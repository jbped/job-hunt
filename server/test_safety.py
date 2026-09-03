#!/usr/bin/env python3
"""Tests for the safety boundaries the scripts promise.

Each test pins a rule that protects personal data or evidence integrity:
audience filtering on the letterhead, the vault write boundary, which notes
the dashboard may append to, the concurrency guard, and CSRF protection on
the local server. Run with:

    python test_safety.py
"""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
import http.client
import json
import os
import tempfile
import threading
import unittest
import urllib.request
import zipfile

import audit_vault
import capture_jd
import export_index
import init_vault
import new_application
import package_app
import render_pdf
import schema
import serve
import vaultlib as v


CONTACT = """---
type: contact-profile
full_name: Test Person
preferred_name: Test
contacts:
  location: {value: "Testville", audience: application}
  phone: {value: "555-0100", audience: recruiter}
  email: {value: "test@example.com", audience: public}
  linkedin: {value: "linkedin.com/in/test", audience: self}
---

# Contact

## Header

- Current resume title: Tester
"""


class SafetyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.vault = Path(cls._tmp.name) / "vault"
        init_vault.create(cls.vault)
        (cls.vault / "Personal Information" / "Contact.md").write_text(
            CONTACT, encoding="utf-8")
        cls.app = new_application.create(cls.vault, "Testco", "Tester")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_letterhead_prints_only_application_and_public(self):
        contact = render_pdf.letterhead(self.vault)["contact"]
        self.assertEqual(contact, ["Testville", "test@example.com"])

    def test_init_clears_only_the_stock_obsidian_welcome(self):
        fresh = Path(self._tmp.name) / "obsidian-fresh"
        fresh.mkdir()
        (fresh / "Welcome.md").write_text(
            init_vault.OBSIDIAN_WELCOME, encoding="utf-8")
        init_vault.create(fresh)
        self.assertFalse((fresh / "Welcome.md").exists())

        edited = Path(self._tmp.name) / "obsidian-edited"
        edited.mkdir()
        (edited / "Welcome.md").write_text(
            init_vault.OBSIDIAN_WELCOME + "\nMy own note.\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            init_vault.create(edited)
        self.assertTrue((edited / "Welcome.md").exists())

    def test_init_force_never_overwrites_a_populated_vault(self):
        vault = Path(self._tmp.name) / "populated"
        init_vault.create(vault)
        contact = vault / "Personal Information" / "Contact.md"
        contact.write_text("precious user data", encoding="utf-8")
        _, skipped = init_vault.create(vault, force=True)
        self.assertEqual(contact.read_text(encoding="utf-8"),
                         "precious user data")
        self.assertIn(Path("Personal Information/Contact.md"), skipped)

    def test_default_vault_is_gitignored(self):
        ignore = (v.REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/vault/", ignore.split())

    def test_find_vault_falls_back_to_repo_default(self):
        original = v.DEFAULT_VAULT
        v.DEFAULT_VAULT = self.vault
        os.environ[v.ENV_VAR] = str(Path(self._tmp.name) / "not-a-vault")
        try:
            self.assertEqual(v.find_vault(), self.vault)
        finally:
            v.DEFAULT_VAULT = original
            del os.environ[v.ENV_VAR]

    def test_resolve_rejects_paths_outside_the_vault(self):
        with self.assertRaises(serve.RequestError):
            serve.resolve(self.vault, "../outside.md")

    def test_render_rejects_paths_outside_the_vault(self):
        outside = Path(self._tmp.name) / "elsewhere"
        outside.mkdir(exist_ok=True)
        with self.assertRaises(serve.RequestError):
            serve.start_render(self.vault, {"path": "../elsewhere", "kind": "resume"})

    def test_append_entry_only_touches_entry_notes(self):
        brief = str((self.app / "Application Brief.md").relative_to(self.vault))
        with self.assertRaises(serve.RequestError):
            serve.append_entry(self.vault, {"path": brief, "title": "Sneaky",
                                            "fields": {"note": "x"}})
        contacts = str((self.app / "Contacts.md").relative_to(self.vault))
        result = serve.append_entry(self.vault, {"path": contacts, "title": "Jo Doe",
                                                 "fields": {"role": "recruiter"}})
        self.assertTrue(result["changed"])

    def test_create_interview_is_bounded(self):
        app = "Applications/Testco/Tester"
        with self.assertRaises(serve.RequestError):  # a date is required
            serve.create_interview(self.vault, {"application": app})
        with self.assertRaises(serve.RequestError):  # and it must lead the value
            serve.create_interview(self.vault, {"application": app,
                                                "when": "next Tuesday"})
        with self.assertRaises(serve.RequestError):  # stage vocabulary enforced
            serve.create_interview(self.vault, {"application": app,
                                                "when": "2026-09-02 14:00 MDT",
                                                "stage": "vibe-check"})
        with self.assertRaises(serve.RequestError):  # only application folders
            serve.create_interview(self.vault, {"application": "People",
                                                "when": "2026-09-02"})
        result = serve.create_interview(self.vault, {
            "application": app, "when": "2026-09-02 14:00 MDT",
            "stage": "hiring-manager", "method": "video",
            "interviewers": "Pat Example"})
        self.assertEqual(result["path"],
                         f"{app}/Interviews/2026-09-02 1400 hiring-manager.md")
        fm, text = v.read_note(self.vault / result["path"])
        self.assertEqual(fm.get("type"), "interview")
        self.assertEqual(fm.get("status"), "scheduled")
        self.assertEqual(fm.get("when"), "2026-09-02 14:00 MDT")
        self.assertIn("## Outcome", text)
        with self.assertRaises(serve.RequestError):  # one note per interview
            serve.create_interview(self.vault, {
                "application": app, "when": "2026-09-02 14:00 MDT",
                "stage": "hiring-manager"})
        # Status is a plain field edit — completion needs no special endpoint.
        serve.set_field(self.vault, {"path": result["path"], "field": "status",
                                     "value": "completed"})
        fm, _ = v.read_note(self.vault / result["path"])
        self.assertEqual(fm.get("status"), "completed")
        report = audit_vault.audit(self.vault)
        self.assertEqual([e for e in report.errors if "Interviews" in e], [])

    def test_stale_fingerprint_is_refused(self):
        contacts = self.app / "Contacts.md"
        rel = str(contacts.relative_to(self.vault))
        stale = v.fingerprint(contacts)
        contacts.write_text(contacts.read_text(encoding="utf-8") + "\n<!-- obsidian -->\n",
                            encoding="utf-8")
        with self.assertRaises(serve.RequestError):
            serve.append_entry(self.vault, {"path": rel, "title": "Raced Entry",
                                            "fields": {"role": "other"},
                                            "fingerprint": stale})

    def test_empty_sanitized_names_are_rejected(self):
        with self.assertRaises(SystemExit):
            new_application.create(self.vault, ".", "Role")

    def test_windows_reserved_names_are_defused(self):
        self.assertEqual(new_application.safe_name("Nul"), "Nul-")
        self.assertEqual(new_application.safe_name("com1.io"), "com1.io-")
        self.assertEqual(new_application.safe_name("Console Corp"), "Console Corp")

    def test_new_application_accepts_verbatim_capture(self):
        folder = new_application.create(self.vault, "Capture Test", "Role")
        note = folder / "Job Description.md"
        digest = capture_jd.capture(note, "First line\nSecond line", today="2026-01-02")
        fm, body = v.read_note(note)
        self.assertEqual(fm["verbatim_sha256"], digest)
        self.assertEqual(capture_jd.find_posting(body).group(2),
                         "First line\nSecond line")

    def test_skill_sources_are_host_neutral(self):
        forbidden = (
            "anthropic", "chatgpt", "claude", "codex", "cursor", "gemini", "openai",
            ".claude/", ".codex/", ".cursor/", ".gemini/", "/job-hunt:",
            "argument-hint:",
        )
        checked = []
        for skill in package_app.CANONICAL_SKILLS:
            root = package_app.SKILLS_ROOT / skill
            for pattern in ("SKILL.md", "references/*.md", "scripts/*.py"):
                checked.extend(root.rglob(pattern))
        self.assertTrue(checked, "no canonical skill files found to check")
        for path in sorted(set(checked)):
            if path.resolve() == Path(__file__).resolve():
                continue
            text = path.read_text(encoding="utf-8").lower()
            for marker in forbidden:
                self.assertNotIn(marker, text, f"{path}: host-specific marker {marker}")

    def test_release_archive_has_portable_skill_roots(self):
        self.assertIn("vault", package_app.EXCLUDED_DIRS)
        output = Path(self._tmp.name) / "app.zip"
        package_app.build(output)
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
        for required in ("server/serve.py",
                         "server/test_safety.py",
                         "server/assets/ui/index.html",
                         ".agents/skills/career-evidence/SKILL.md",
                         ".agents/skills/new-application/SKILL.md",
                         "Dockerfile",
                         "compose.yaml"):
            self.assertIn(required, names)
        self.assertFalse(any(".claude-plugin" in name for name in names))
        self.assertFalse(any(name.startswith("job-hunt/") for name in names))
        self.assertFalse(any("vault" in Path(name).parts for name in names))
        self.assertFalse(any(".cache" in Path(name).parts for name in names))
        self.assertFalse(any("__pycache__" in Path(name).parts for name in names))
        provider_names = {"anthropic", "claude", "codex", "cursor", "gemini", "openai",
                          ".claude"}
        for name in names:
            parts = {part.lower() for part in Path(name).parts}
            self.assertTrue(parts.isdisjoint(provider_names),
                            f"provider-specific archive path: {name}")

    def test_create_person_is_bounded(self):
        with self.assertRaises(serve.RequestError):
            serve.create_person(self.vault, {"name": ""})
        with self.assertRaises(serve.RequestError):
            serve.create_person(self.vault, {"name": "."})
        with self.assertRaises(serve.RequestError):
            serve.create_person(self.vault, {"name": "X", "relationship": "bogus"})
        with self.assertRaises(serve.RequestError):
            serve.create_person(self.vault, {
                "name": "X", "professional_relationship": "old-boss"})
        with self.assertRaises(serve.RequestError):
            serve.create_person(self.vault, {"name": "X", "folder": "Friends"})
        result = serve.create_person(self.vault, {"name": "Sam Test",
                                                  "relationship": "recruiter",
                                                  "professional_relationship":
                                                      "former-manager"})
        # A known professional relationship outranks the recruiter role.
        self.assertEqual(result["path"], "People/Network/Sam Test.md")
        with self.assertRaises(serve.RequestError):  # one note per person, vault-wide
            serve.create_person(self.vault, {"name": "Sam Test", "folder": "Job Hunt"})
        fm, _ = v.read_note(self.vault / "People" / "Network" / "Sam Test.md")
        self.assertEqual(fm.get("type"), "person")
        self.assertEqual(fm.get("relationships"), ["recruiter"])
        self.assertEqual(fm.get("professional_relationships"), ["former-manager"])
        result = serve.create_person(self.vault, {"name": "Rae Recruiter",
                                                  "relationship": "recruiter"})
        self.assertEqual(result["path"], "People/Recruiters/Rae Recruiter.md")
        result = serve.create_person(self.vault, {"name": "Tia Target",
                                                  "relationship": "networking-target"})
        self.assertEqual(result["path"], "People/Job Hunt/Tia Target.md")

    def test_create_role_is_bounded(self):
        with self.assertRaises(serve.RequestError):
            serve.create_role(self.vault, {"company": "", "title": "X"})
        with self.assertRaises(serve.RequestError):
            serve.create_role(self.vault, {"company": "X", "title": ""})
        result = serve.create_role(self.vault, {
            "company": "Testco", "title": "Tester", "start": "2024-01"})
        self.assertEqual(result["path"], "Career Evidence/Roles/Testco - Tester.md")
        fm, text = v.read_note(self.vault / result["path"])
        self.assertEqual(fm.get("type"), "role")
        self.assertEqual(fm.get("status"), "needs-interview")
        self.assertEqual(fm.get("company"), "Testco")
        self.assertEqual(fm.get("start"), "2024-01")
        self.assertIn("# Testco | Tester", text)
        self.assertIn("## Questions", text)
        with self.assertRaises(serve.RequestError):  # one canonical note per role
            serve.create_role(self.vault, {"company": "Testco", "title": "Tester"})

    def test_create_accomplishment_is_bounded(self):
        with self.assertRaises(serve.RequestError):
            serve.create_accomplishment(self.vault, {"company": "X", "title": ""})
        result = serve.create_accomplishment(self.vault, {
            "company": "Testco", "title": "Big Win", "folder": "Testco 2024"})
        self.assertEqual(result["path"],
                         "Career Evidence/Accomplishments/Testco 2024/Big Win.md")
        fm, text = v.read_note(self.vault / result["path"])
        self.assertEqual(fm.get("type"), "accomplishment")
        self.assertEqual(fm.get("status"), "draft")
        self.assertIn("# Big Win", text)
        self.assertIn("## Questions", text)
        # One canonical note vault-wide, even from a different subfolder.
        with self.assertRaises(serve.RequestError):
            serve.create_accomplishment(self.vault, {"company": "Testco",
                                                     "title": "Big Win"})
        report = audit_vault.audit(self.vault)
        scaffold_errors = [e for e in report.errors if "Career Evidence" in e]
        self.assertEqual(scaffold_errors, [])

    def test_scaffold_forms_match_schema_and_routes(self):
        payload = serve.api_schema(self.vault)
        for name, spec in schema.FORMS.items():
            self.assertIn(spec["endpoint"], serve.HANDLERS,
                          f"form '{name}' posts to an unregistered route")
            for field in spec["fields"]:
                enum = field.get("enum")
                if enum:
                    self.assertIn(enum, payload,
                                  f"form '{name}.{field['name']}' names a missing enum")

    def test_create_lead_is_bounded(self):
        with self.assertRaises(serve.RequestError):
            serve.create_lead(self.vault, {"company": ""})
        result = serve.create_lead(self.vault, {"company": "Leadco",
                                                "source": "Sam Test"})
        self.assertEqual(result["path"], "Leads/Leadco.md")
        fm, _ = v.read_note(self.vault / result["path"])
        self.assertEqual(fm.get("type"), "lead")
        self.assertEqual(fm.get("status"), "new")
        self.assertEqual(fm.get("role"), "Unknown")
        self.assertEqual(fm.get("source"), "[[Sam Test]]")
        with self.assertRaises(serve.RequestError):  # one note per lead
            serve.create_lead(self.vault, {"company": "Leadco"})

    def test_lead_promotion_needs_a_real_role_and_links_back(self):
        serve.create_lead(self.vault, {"company": "Promoco"})
        with self.assertRaises(serve.RequestError):  # Unknown role cannot promote
            serve.create_application(self.vault, {"lead": "Leads/Promoco.md"})
        serve.set_field(self.vault, {"path": "Leads/Promoco.md",
                                     "field": "role", "value": "Tester"})
        result = serve.create_application(self.vault, {"lead": "Leads/Promoco.md"})
        self.assertEqual(result["path"], "Applications/Promoco/Tester")
        fm, _ = v.read_note(self.vault / "Leads/Promoco.md")
        self.assertEqual(fm.get("status"), "promoted")
        self.assertIn("Applications/Promoco/Tester", fm.get("application") or "")
        with self.assertRaises(serve.RequestError):  # promoting twice is refused
            serve.create_application(self.vault, {"lead": "Leads/Promoco.md"})
        with self.assertRaises(serve.RequestError):  # only lead notes promote
            serve.create_application(
                self.vault, {"lead": "Applications/Promoco/Tester/Analysis.md"})

    def test_wikilink_resolution_is_bounded(self):
        with self.assertRaises(serve.RequestError):  # escape attempts refused
            serve.resolve_wikilink(self.vault, "../outside")
        with self.assertRaises(serve.RequestError):  # empty after stripping
            serve.resolve_wikilink(self.vault, "#section")
        with self.assertRaises(serve.RequestError):
            serve.resolve_wikilink(self.vault, "No Such Note Anywhere")
        # Full vault-relative path, with alias and anchor stripped.
        result = serve.resolve_wikilink(
            self.vault, "Applications/Testco/Tester/Analysis#Fit|the analysis")
        self.assertEqual(result["path"], "Applications/Testco/Tester/Analysis.md")
        # Bare-name fallback, the way Obsidian resolves short links.
        result = serve.resolve_wikilink(self.vault, "Sam Test")
        self.assertEqual(result["path"], "People/Network/Sam Test.md")

    def test_note_save_is_guarded(self):
        analysis = self.app / "Analysis.md"
        rel = str(analysis.relative_to(self.vault))
        fp = v.fingerprint(analysis)
        with self.assertRaises(serve.RequestError):  # evidence stays read-only
            serve.save_note(self.vault, {
                "path": str((self.app / "Job Description.md").relative_to(self.vault)),
                "text": "x", "fingerprint": "y"})
        with self.assertRaises(serve.RequestError):  # emptying is not deleting
            serve.save_note(self.vault, {"path": rel, "text": "  ",
                                         "fingerprint": fp})
        with self.assertRaises(serve.RequestError):  # the loaded fingerprint is required
            serve.save_note(self.vault, {"path": rel, "text": "x"})
        with self.assertRaises(serve.RequestError):  # a stale one is refused
            serve.save_note(self.vault, {"path": rel, "text": "x",
                                         "fingerprint": "stale"})

        result = serve.save_note(self.vault, {
            "path": rel, "fingerprint": fp,
            "text": "---\ntype: application-analysis\ncompany: Testco\n"
                    "position: Tester\n---\n\n# New analysis"})
        self.assertTrue(result["changed"])
        self.assertEqual(result["warnings"], [])
        fm, body = v.read_note(analysis)
        self.assertEqual(fm.get("type"), "application-analysis")
        self.assertIn("# New analysis", body)

        # Structural damage saves — the buffer is the user's — but warns loudly.
        result = serve.save_note(self.vault, {
            "path": rel, "fingerprint": result["fingerprint"],
            "text": "---\ntype: application\nstatus: bogus\n---\nbody\n"})
        self.assertTrue(any("type changed" in w for w in result["warnings"]))
        self.assertTrue(any("'bogus'" in w for w in result["warnings"]))
        serve.save_note(self.vault, {  # leave the shared fixture note valid
            "path": rel, "fingerprint": result["fingerprint"],
            "text": "---\ntype: application-analysis\ncompany: Testco\n"
                    "position: Tester\n---\n\n# Restored\n"})

    def test_capture_endpoint_scaffolds_and_checksums(self):
        with self.assertRaises(serve.RequestError):  # position is required
            serve.create_capture(self.vault, {"company": "Capco", "text": "x"})
        with self.assertRaises(serve.RequestError):  # so is actual posting text
            serve.create_capture(self.vault, {"company": "Capco",
                                              "position": "Dev", "text": "  "})
        result = serve.create_capture(self.vault, {
            "company": "Capco", "position": "Dev",
            "url": "https://jobs.example.com/dev",
            "text": "Line one\nLine two"})
        self.assertEqual(result["path"], "Applications/Capco/Dev")
        fm, body = v.read_note(self.vault / result["path"] / "Job Description.md")
        self.assertEqual(fm.get("verbatim_sha256"), result["sha256"])
        self.assertEqual(fm.get("source_kind"), "extension")
        self.assertEqual(capture_jd.find_posting(body).group(2),
                         "Line one\nLine two")
        brief, _ = v.read_note(self.vault / result["path"] / "Application Brief.md")
        self.assertEqual(brief.get("posting_source"), "jobs.example.com")
        # How the user found the job is their fact — never inferred by a capture.
        self.assertFalse(brief.get("discovery_method"))
        with self.assertRaises(serve.RequestError):  # duplicate refused
            serve.create_capture(self.vault, {"company": "Capco",
                                              "position": "Dev", "text": "again"})

    def test_capture_rolls_back_the_scaffold_when_capture_fails(self):
        with self.assertRaises(serve.RequestError):
            serve.create_capture(self.vault, {
                "company": "Rollco", "position": "Dev",
                "text": "broken <!-- verbatim-end --> marker"})
        self.assertFalse((self.vault / "Applications" / "Rollco").exists())

    def test_capture_lead_mode_stores_no_posting_text(self):
        result = serve.create_capture(self.vault, {
            "mode": "lead", "company": "Leadcapco", "position": "Dev",
            "url": "https://x.example/job", "text": "secret posting text"})
        self.assertEqual(result["path"], "Leads/Leadcapco - Dev.md")
        fm, body = v.read_note(self.vault / result["path"])
        self.assertEqual(fm.get("type"), "lead")
        self.assertNotIn("secret posting text", body)

    def test_person_follow_up_fields_are_editable_but_name_is_not(self):
        result = serve.create_person(self.vault, {"name": "Cadence Check"})
        path = result["path"]
        serve.set_field(self.vault, {"path": path, "field": "next_follow_up",
                                     "value": "2026-09-01"})
        serve.set_field(self.vault, {"path": path, "field": "last_contact",
                                     "value": "2026-08-15"})
        fm, _ = v.read_note(self.vault / path)
        self.assertEqual(fm.get("next_follow_up"), "2026-09-01")
        self.assertEqual(fm.get("last_contact"), "2026-08-15")
        with self.assertRaises(serve.RequestError):  # identity is not UI-editable
            serve.set_field(self.vault, {"path": path, "field": "name",
                                         "value": "Someone Else"})

    def test_audit_rejects_unknown_professional_relationship(self):
        note = self.vault / "People" / "Invalid Relationship.md"
        note.write_text(
            "---\ntype: person\nname: Invalid Relationship\n"
            "professional_relationships:\n  - old-boss\n---\n",
            encoding="utf-8",
        )
        try:
            report = audit_vault.audit(self.vault)
            self.assertTrue(any("professional relationship 'old-boss'" in error
                                for error in report.errors))
        finally:
            note.unlink()

    def test_stop_previous_never_kills_unverified_pids(self):
        # PIDs get recycled: a stale pidfile may name an innocent process. It
        # must be signalled only if its recorded port answers as our dashboard.
        import json as jsonlib
        import subprocess
        import sys
        bystander = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            pidfile = self.vault / ".cache" / "serve.pid"
            pidfile.parent.mkdir(exist_ok=True)
            pidfile.write_text(jsonlib.dumps({"pid": bystander.pid, "port": 1}))
            serve.stop_previous(self.vault)
            self.assertIsNone(bystander.poll())  # still alive
            self.assertFalse(pidfile.exists())   # stale record cleaned up
        finally:
            bystander.kill()
            bystander.wait()

    def test_archive_moves_the_whole_unit_and_is_reversible(self):
        result = serve.create_capture(self.vault, {
            "company": "Archco", "position": "Dev",
            "url": "https://jobs.example.com/a", "text": "Posting body"})
        rel = result["path"]
        jd_before = (self.vault / rel / "Job Description.md").read_bytes()

        archived = serve.archive_unit(self.vault, {
            "kind": "application", "path": rel, "reason": "position filled"})
        self.assertFalse((self.vault / rel).exists())
        moved = self.vault / archived["archived"]
        self.assertEqual(archived["archived"], f"Archive/{rel}")
        # The checksummed capture moved with its folder, byte-identical.
        self.assertEqual((moved / "Job Description.md").read_bytes(), jd_before)
        fm, _ = v.read_note(moved / "Application Brief.md")
        self.assertEqual(fm.get("archived_from"), rel)
        self.assertEqual(fm.get("archive_reason"), "position filled")
        self.assertTrue(fm.get("archived"))

        index = export_index.build(self.vault)
        self.assertNotIn(rel, [a["path"] for a in index["applications"]])
        entry = next(e for e in index["archived"] if e["archived_from"] == rel)
        self.assertEqual(entry["kind"], "application")

        report = audit_vault.audit(self.vault)
        self.assertEqual([e for e in report.errors if "Archive" in e], [])
        # A name-only wikilink to an archived note still resolves.
        serve.create_lead(self.vault, {"company": "Linkco"})
        serve.archive_unit(self.vault, {"kind": "lead", "path": "Leads/Linkco.md"})
        resolved = serve.resolve_wikilink(self.vault, "Linkco")
        self.assertEqual(resolved["path"], "Archive/Leads/Linkco.md")

        restored = serve.unarchive_unit(self.vault,
                                        {"path": archived["archived"]})
        self.assertEqual(restored["restored"], rel)
        self.assertTrue((self.vault / rel / "Application Brief.md").exists())
        fm, _ = v.read_note(self.vault / rel / "Application Brief.md")
        for field in schema.ARCHIVE_FIELDS:
            self.assertIsNone(fm.get(field), field)

    def test_archive_restores_refuse_an_occupied_destination(self):
        serve.create_lead(self.vault, {"company": "Occupyco"})
        archived = serve.archive_unit(self.vault, {
            "kind": "lead", "path": "Leads/Occupyco.md"})
        serve.create_lead(self.vault, {"company": "Occupyco"})
        with self.assertRaises(serve.RequestError):
            serve.unarchive_unit(self.vault, {"path": archived["archived"]})

    def test_archive_refuses_evidence_and_bad_targets(self):
        with self.assertRaises(serve.RequestError):  # unknown kind
            serve.archive_unit(self.vault, {"kind": "person",
                                            "path": "People/Network/Sam Test.md"})
        with self.assertRaises(serve.RequestError):  # evidence is not a unit
            serve.archive_unit(self.vault, {
                "kind": "lead",
                "path": "Applications/Testco/Tester/Job Description.md"})
        with self.assertRaises(serve.RequestError):  # a single file inside an app
            serve.archive_unit(self.vault, {
                "kind": "application",
                "path": "Applications/Testco/Tester/Analysis.md"})
        with self.assertRaises(serve.RequestError):  # escape attempt
            serve.archive_unit(self.vault, {"kind": "lead", "path": "../x.md"})
        with self.assertRaises(serve.RequestError):  # restores stay inside Archive/
            serve.unarchive_unit(self.vault, {"path": "Leads"})

    def test_bind_defaults_to_loopback(self):
        # Widening the bind must be an explicit act; with no environment set,
        # the server can only ever listen on loopback.
        saved = {key: os.environ.pop(key, None)
                 for key in ("CAREER_EVIDENCE_BIND",)}
        original_load_env = v.load_env
        v.load_env = lambda path=None: {}
        try:
            self.assertEqual(serve.default_bind(), "127.0.0.1")
            os.environ["CAREER_EVIDENCE_BIND"] = "0.0.0.0"
            self.assertEqual(serve.default_bind(), "0.0.0.0")
        finally:
            v.load_env = original_load_env
            os.environ.pop("CAREER_EVIDENCE_BIND", None)
            for key, value in saved.items():
                if value is not None:
                    os.environ[key] = value

    def test_session_token_persists_and_is_private(self):
        first = serve.load_or_create_token(self.vault)
        token_file = self.vault / ".cache" / "session-token"
        self.assertTrue(token_file.is_file())
        if os.name != "nt":
            self.assertEqual(token_file.stat().st_mode & 0o777, 0o600)
        # The same token comes back on the next start — pairing survives.
        self.assertEqual(serve.load_or_create_token(self.vault), first)
        # An emptied file (the --new-token path) re-rolls it.
        token_file.write_text("", encoding="utf-8")
        self.assertNotEqual(serve.load_or_create_token(self.vault), first)

    def test_question_bank_scaffolds_and_upserts(self):
        app = "Applications/Testco/Tester"
        second = new_application.create(self.vault, "Testco", "Senior Tester")
        second_rel = str(second.relative_to(self.vault))

        with self.assertRaises(serve.RequestError):  # a bank needs a company
            serve.create_or_update_question(self.vault, {"company": " ",
                                                         "question": "Why us?"})
        with self.assertRaises(serve.RequestError):  # one that survives sanitising
            serve.create_or_update_question(self.vault, {"company": ".",
                                                         "question": "Why us?"})
        with self.assertRaises(serve.RequestError):  # and a question needs text
            serve.create_or_update_question(self.vault, {"company": "Testco",
                                                         "question": "  "})
        with self.assertRaises(serve.RequestError) as rejected:
            serve.create_or_update_question(self.vault, {
                "company": "Testco", "question": "Why us?",
                "answer": "First paragraph.\n## Accidental heading\nLast paragraph."})
        self.assertEqual(rejected.exception.status, 400)
        self.assertIn("headings aren't allowed", str(rejected.exception))
        # A traversal attempt sanitises into a plain folder name; nothing lands
        # outside Applications/.
        escaped = serve.create_or_update_question(self.vault, {
            "company": "../../Escapeco", "question": "Why us?",
            "answer": "Because.", "asked_on": app})
        self.assertTrue(escaped["path"].startswith("Applications/"), escaped["path"])
        self.assertTrue((self.vault / escaped["path"]).is_file())
        self.assertFalse((self.vault.parent / "Escapeco").exists())

        result = serve.create_or_update_question(self.vault, {
            "company": "Testco", "question": "Why do you want to work here?",
            "answer": "Because the work is real.", "asked_on": app,
            "char_limit": 300})
        self.assertEqual(result["path"], "Applications/Testco/Company Questions.md")
        note = self.vault / result["path"]
        fm, text = v.read_note(note)
        self.assertEqual(fm.get("type"), "company-questions")
        self.assertEqual(fm.get("company"), "Testco")
        self.assertNotIn("No questions recorded.", text)
        self.assertIn("## Entry format", text)

        # The same question asked again on another application appends the link
        # rather than forking a second entry, and the answer already given stands.
        serve.create_or_update_question(self.vault, {
            "company": "Testco", "question": "Why do you want to work here?",
            "answer": "", "asked_on": second_rel})
        _, text = v.read_note(note)
        self.assertEqual(text.count("## Why do you want to work here?"), 1)
        entries = export_index._entries(text)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertIn(f"[[{app}]]", entry["fields"]["asked_on"])
        self.assertIn(f"[[{second_rel}]]", entry["fields"]["asked_on"])
        self.assertEqual(entry["fields"]["char_limit"], "300")
        # The answer round-trips as the entry body, verbatim and unedited.
        self.assertEqual(entry["body"], "Because the work is real.")

        # A resubmitted answer replaces the old one, and the link set stays
        # deduplicated when a question recurs where it was already asked.
        serve.create_or_update_question(self.vault, {
            "company": "Testco", "question": "Why do you want to work here?",
            "answer": "Because the work is real, and the team is too.",
            "asked_on": app})
        entry = export_index._entries(v.read_note(note)[1])[0]
        self.assertEqual(entry["body"],
                         "Because the work is real, and the team is too.")
        self.assertEqual(entry["fields"]["asked_on"].count("[["), 2)

    def test_question_upsert_never_rewrites_the_note(self):
        company = "Handwritten Co"
        serve.create_or_update_question(self.vault, {
            "company": company, "question": "First question?",
            "answer": "First answer.", "asked_on": "Applications/Testco/Tester"})
        note = self.vault / "Applications" / company / "Company Questions.md"
        note.write_text(
            note.read_text(encoding="utf-8").replace(
                "## Entry format",
                "## My own notes\n\nHand-written prose.\n\n## Entry format"),
            encoding="utf-8")
        serve.create_or_update_question(self.vault, {
            "company": company, "question": "Second question?",
            "answer": "Second answer.", "asked_on": "Applications/Testco/Tester"})
        text = note.read_text(encoding="utf-8")
        self.assertIn("Hand-written prose.", text)
        self.assertIn("## First question?", text)
        self.assertIn("First answer.", text)
        self.assertLess(text.index("## Second question?"), text.index("## Entry format"))
        # Scaffolding happens once: a second call never re-creates the note.
        self.assertEqual(text.count("type: company-questions"), 1)
        # And the write is fingerprint-guarded like every other one.
        with self.assertRaises(serve.RequestError):
            serve.create_or_update_question(self.vault, {
                "company": company, "question": "Third?", "answer": "x",
                "fingerprint": "stale-fingerprint"})

    def test_question_route_is_registered_and_token_gated(self):
        self.assertIs(serve.HANDLERS["/api/question"],
                      serve.create_or_update_question)
        serve.Handler.vault = self.vault
        serve.Handler.token = "test-token-value"
        server = ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/question",
                data=json.dumps({"company": "Testco", "question": "Q",
                                 "answer": "A"}).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
            try:
                status = urllib.request.urlopen(request).status
            except urllib.error.HTTPError as error:
                status = error.code
            self.assertEqual(status, 403)
        finally:
            server.shutdown()
            server.server_close()

    def test_question_banks_are_projected_and_audited(self):
        app = "Applications/Testco/Tester"
        serve.create_or_update_question(self.vault, {
            "company": "Projected Co", "question": "What draws you here?",
            "answer": "The problem, mostly.", "asked_on": app, "char_limit": 250})
        index = export_index.build(self.vault)
        banked = [q for q in index["company_questions"]
                  if q["company"] == "Projected Co"]
        self.assertEqual(len(banked), 1)
        self.assertEqual(banked[0]["question"], "What draws you here?")
        self.assertEqual(banked[0]["answer"], "The problem, mostly.")
        self.assertEqual(banked[0]["path"],
                         "Applications/Projected Co/Company Questions.md")
        self.assertEqual(banked[0]["fields"]["char_limit"], "250")

        # A dangling `Asked on` link and a non-numeric limit are warnings, not
        # errors: a bank is the user's note and must never fail the audit.
        note = self.vault / banked[0]["path"]
        note.write_text(note.read_text(encoding="utf-8")
                        .replace(f"[[{app}]]", "[[Applications/Gone/Nowhere]]")
                        .replace("- Char limit: 250", "- Char limit: about 250"),
                        encoding="utf-8")
        report = audit_vault.audit(self.vault, check_wikilinks=False)
        self.assertEqual(report.errors, [])
        self.assertTrue([w for w in report.warnings
                         if "Company Questions.md" in w and "Applications/Gone" in w])
        self.assertTrue([w for w in report.warnings
                         if "Company Questions.md" in w and "Char limit" in w])

    def test_no_destructive_route_exists(self):
        import inspect
        self.assertEqual([r for r in serve.HANDLERS if "delete" in r], [])
        for handler in (serve.archive_unit, serve.unarchive_unit):
            source = inspect.getsource(handler)
            for call in ("unlink", "rmtree", "rmdir", "remove("):
                self.assertNotIn(call, source, f"{handler.__name__} uses {call}")

    def test_assets_are_served_only_from_the_ui_bundle(self):
        """/assets/ hands out the built frontend and nothing else.

        The handler joins an unsanitised path segment, so the escape guard is
        the only thing between a request and the rest of the disk.
        """
        serve.Handler.vault = self.vault
        serve.Handler.token = "test-token-value"
        ui = Path(self._tmp.name) / "ui-bundle"
        (ui / "assets").mkdir(parents=True, exist_ok=True)
        (ui / "assets" / "index-abc123.js").write_text("export const ok = 1;\n",
                                                       encoding="utf-8")
        (ui / "index.html").write_text("BUNDLE INDEX", encoding="utf-8")
        outside = Path(self._tmp.name) / "outside.txt"
        outside.write_text("PRIVATE", encoding="utf-8")

        original_ui_dir = serve.UI_DIR
        serve.UI_DIR = ui
        server = ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            def get(path):
                # http.client, not urllib: urllib collapses "/a/../b" before it
                # ever reaches the server, which would test nothing.
                connection = http.client.HTTPConnection("127.0.0.1", port)
                connection.request("GET", path)
                response = connection.getresponse()
                body = response.read()
                connection.close()
                return response.status, body

            status, body = get("/assets/index-abc123.js")
            self.assertEqual(status, 200)
            self.assertIn(b"export const ok", body)

            escapes = [
                "/assets/../index.html",
                "/assets/%2e%2e/index.html",
                "/assets/../../outside.txt",
                "/assets/%2e%2e%2f%2e%2e%2foutside.txt",
                f"/assets/{outside}",                      # absolute path
                f"/assets/..%2f..%2f{outside.name}",
            ]
            for path in escapes:
                status, body = get(path)
                self.assertEqual(status, 404, path)
                self.assertNotIn(b"PRIVATE", body, path)
                self.assertNotIn(b"BUNDLE INDEX", body, path)

            self.assertEqual(get("/assets/missing.js")[0], 404)
        finally:
            serve.UI_DIR = original_ui_dir
            server.shutdown()
            server.server_close()

    def test_posts_require_session_token(self):
        serve.Handler.vault = self.vault
        serve.Handler.token = "test-token-value"
        server = ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            def post(headers):
                request = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/field",
                    data=json.dumps({"path": "x"}).encode(),
                    headers=headers, method="POST")
                try:
                    return urllib.request.urlopen(request).status
                except urllib.error.HTTPError as error:
                    return error.code

            json_type = {"Content-Type": "application/json"}
            self.assertEqual(post(json_type), 403)
            self.assertEqual(post({**json_type, "X-Session-Token": "wrong"}), 403)
            self.assertEqual(post({"X-Session-Token": "test-token-value"}), 403)
            self.assertEqual(post({**json_type, "Origin": "http://evil.example",
                                   "X-Session-Token": "test-token-value"}), 403)
            self.assertEqual(post({**json_type, "X-Session-Token": "test-token-value"}),
                             404)  # authenticated; fails on the bogus path, not on auth
            # An extension origin passes the Origin guard but still needs the token.
            self.assertEqual(post({**json_type,
                                   "Origin": "chrome-extension://abcdefgh"}), 403)
            self.assertEqual(post({**json_type, "Origin": "chrome-extension://abcdefgh",
                                   "X-Session-Token": "test-token-value"}), 404)

            def preflight(headers):
                request = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/capture",
                    headers=headers, method="OPTIONS")
                try:
                    return urllib.request.urlopen(request).status
                except urllib.error.HTTPError as error:
                    return error.code

            self.assertEqual(preflight({"Origin": "moz-extension://abcdefgh"}), 204)
            self.assertEqual(preflight({"Origin": "http://evil.example"}), 403)
            self.assertEqual(preflight({}), 403)

            # GETs are not token-gated, so no extension may be allowed to read
            # them cross-origin — the CORS header appears on POST answers only.
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/schema",
                headers={"Origin": "chrome-extension://abcdefgh"})
            with urllib.request.urlopen(request) as response:
                self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
