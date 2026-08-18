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
import json
import os
import tempfile
import threading
import unittest
import urllib.request
import zipfile

import capture_jd
import init_vault
import new_application
import package_skill
import render_pdf
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

    def test_interview_completion_only_touches_interviews(self):
        brief = str((self.app / "Application Brief.md").relative_to(self.vault))
        with self.assertRaises(serve.RequestError):
            serve.complete_interview(self.vault, {"path": brief, "title": "x"})

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
        for pattern in ("SKILL.md", "references/*.md", "scripts/*.py"):
            checked.extend(package_skill.SKILLS_ROOT.rglob(pattern))
        for path in sorted(set(checked)):
            if path.resolve() == Path(__file__).resolve():
                continue
            text = path.read_text(encoding="utf-8").lower()
            for marker in forbidden:
                self.assertNotIn(marker, text, f"{path}: host-specific marker {marker}")

    def test_release_archive_has_portable_skill_roots(self):
        self.assertIn("vault", package_skill.EXCLUDED_DIRS)
        output = Path(self._tmp.name) / "skills.zip"
        package_skill.build(output)
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
        self.assertIn("career-evidence/SKILL.md", names)
        self.assertIn("new-application/SKILL.md", names)
        self.assertFalse(any(".claude-plugin" in name for name in names))
        self.assertFalse(any(name.startswith("job-hunt/") for name in names))
        self.assertFalse(any("vault" in Path(name).parts for name in names))
        provider_names = {"anthropic", "claude", "codex", "cursor", "gemini", "openai"}
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
        result = serve.create_person(self.vault, {"name": "Sam Test",
                                                  "relationship": "recruiter"})
        self.assertEqual(result["path"], "People/Sam Test.md")
        with self.assertRaises(serve.RequestError):  # one note per person
            serve.create_person(self.vault, {"name": "Sam Test"})
        fm, _ = v.read_note(self.vault / "People" / "Sam Test.md")
        self.assertEqual(fm.get("type"), "person")
        self.assertEqual(fm.get("relationships"), ["recruiter"])

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
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
