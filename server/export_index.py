#!/usr/bin/env python3
"""Project the vault into a single JSON file for tools that should not re-parse it.

The index is derived, never authoritative. It is rebuilt from the notes on
demand and nothing ever writes back to it — if it disagrees with the markdown,
the markdown is right and the index is stale. Deleting `.cache/` loses nothing.

Usage:
    python export_index.py [--vault PATH] [--stdout] [--write-field-reference]
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import re

import schema
import vaultlib as v

BULLET = re.compile(r"^\s*-\s+([^:]+):\s*(.*)$")

# Headings that document the note's own format rather than holding data. The
# templates keep a worked example so a hand-editor knows the shape; without this
# the example would index as a phantom contact.
IGNORED_HEADINGS = {"entry format", "name", "full name", "company | position"}
PLACEHOLDER = re.compile(r"^(YYYY|<|\{\{)", re.IGNORECASE)


def _display_name(title: str) -> str:
    """Strip wikilink syntax from an entry heading: `[[People/Ed]]` -> `Ed`."""
    match = re.fullmatch(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]", title.strip())
    if match:
        return match.group(1).rsplit("/", 1)[-1].strip()
    return title


def _entries(text: str, under: str | None = None) -> list[dict]:
    """Parse `## Name` / `### Name` blocks of `- Field: value` bullets.

    Contacts and reference logs share this shape, so one parser covers them.
    Prose written under an entry's bullets is kept as its `body` — the company
    question banks answer in prose, and an answer is the point of the entry.
    Returns [] for the placeholder text the templates ship with
    ("No contacts recorded.").
    """
    lines = text.split("\n")
    start, level = 0, 2
    if under is not None:
        for i, line in enumerate(lines):
            if line.strip().lower() == under.strip().lower():
                start, level = i + 1, 3
                break
        else:
            return []

    out: list[dict] = []
    current: dict | None = None
    for line in lines[start:]:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            depth = len(stripped) - len(stripped.lstrip("#"))
            if under is not None and depth < level:
                break
            title = stripped.lstrip("#").strip()
            if under is None and depth == 2 and title.lower() in IGNORED_HEADINGS:
                break
            if depth == level:
                if title.lower() in IGNORED_HEADINGS or PLACEHOLDER.match(title):
                    current = None
                    continue
                current = {"title": title, "fields": {}, "body": []}
                out.append(current)
                continue
            if depth < level:
                current = None
            continue
        if current is None:
            continue
        match = BULLET.match(line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_")
            current["fields"][key] = match.group(2).strip()
            continue
        current["body"].append(line)
    for entry in out:
        entry["body"] = "\n".join(entry["body"]).strip()
    return [e for e in out if e["fields"]]


def _archived(vault: Path) -> list[dict]:
    """Anchor notes under Archive/, mirrored from the live layout.

    Archived units drop out of every live section because those globs only
    scan the live folders; this section keeps them countable and restorable
    instead of invisible.
    """
    out = []
    archive = vault / "Archive"
    anchors = [
        *((p, "application") for p in
          sorted((archive / "Applications").glob("*/*/Application Brief.md"))),
        *((p, "lead") for p in sorted((archive / "Leads").glob("*.md"))),
    ] if archive.is_dir() else []
    for note, kind in anchors:
        fm, _ = v.read_note(note)
        unit = note.parent if kind == "application" else note
        out.append({
            "kind": kind,
            "company": fm.get("company"),
            "position": fm.get("position") or fm.get("role"),
            "status": fm.get("status"),
            "archived": fm.get("archived"),
            "archive_reason": fm.get("archive_reason"),
            "archived_from": fm.get("archived_from"),
            "path": str(unit.relative_to(vault)),
            "brief": str(note.relative_to(vault)),
            "fingerprint": v.fingerprint(note),
        })
    return out


def build(vault: Path) -> dict:
    applications, contacts, interviews, people, evidence = [], [], [], [], []
    leads, company_questions = [], []

    leads_dir = vault / "Leads"
    if leads_dir.is_dir():
        for note in sorted(leads_dir.glob("*.md")):
            fm, _ = v.read_note(note)
            if fm.get("type") != "lead":
                continue
            leads.append({
                "company": fm.get("company"),
                "role": fm.get("role"),
                "url": fm.get("url"),
                "source": fm.get("source"),
                "date_added": fm.get("date_added"),
                "status": fm.get("status"),
                "next_follow_up": fm.get("next_follow_up"),
                "passed_reason": fm.get("passed_reason"),
                "application": fm.get("application"),
                "path": str(note.relative_to(vault)),
                "fingerprint": v.fingerprint(note),
            })

    # One bank per company folder — a level above the applications themselves,
    # which is the whole point: the answers outlive any one application.
    for bank in sorted((vault / "Applications").glob("*/Company Questions.md")):
        company = bank.parent.name
        rel = str(bank.relative_to(vault))
        _, btext = v.read_note(bank)
        for entry in _entries(btext):
            company_questions.append({
                "company": company,
                "path": rel,
                "question": entry["title"],
                "fields": entry["fields"],
                "answer": entry["body"],
            })

    for brief in sorted((vault / "Applications").glob("*/*/Application Brief.md")):
        folder = brief.parent
        fm, _ = v.read_note(brief)
        rel = str(folder.relative_to(vault))

        app = {
            "company": fm.get("company") or folder.parent.name,
            "position": fm.get("position") or folder.name,
            "status": fm.get("status") or "discovered",
            "active": schema.is_active(fm.get("status") or "discovered"),
            "path": rel,
            "brief": str(brief.relative_to(vault)),
            "fingerprint": v.fingerprint(brief),
            "artifacts": [],
            "notes": {},
        }
        for key in schema.NOTE_TYPES["application"]["optional"]:
            if key != "tags":
                app[key] = fm.get(key)
        app["tags"] = fm.get("tags") or []

        for name in ("Analysis.md", "Job Description.md", "Contacts.md",
                     "Draft - Resume.md", "Draft - Cover Letter.md",
                     "Submission Notes.md"):
            if (folder / name).exists():
                app["notes"][name[:-3]] = str((folder / name).relative_to(vault))

        analysis = folder / "Analysis.md"
        if analysis.exists():
            afm, _ = v.read_note(analysis)
            app["experience_level_synthesized"] = afm.get("experience_level_synthesized")

        artifacts = folder / "Artifacts"
        if artifacts.is_dir():
            for f in sorted(artifacts.iterdir()):
                if f.is_file() and not f.name.startswith("."):
                    app["artifacts"].append({
                        "name": f.name,
                        "path": str(f.relative_to(vault)),
                        "bytes": f.stat().st_size,
                    })

        contacts_note = folder / "Contacts.md"
        if contacts_note.exists():
            _, ctext = v.read_note(contacts_note)
            for entry in _entries(ctext):
                contacts.append({
                    # Entries may head with a [[People/Name]] link; index the name.
                    "name": _display_name(entry["title"]),
                    "company": app["company"],
                    "position": app["position"],
                    "application": rel,
                    "note": str(contacts_note.relative_to(vault)),
                    **entry["fields"],
                })

        interviews_dir = folder / "Interviews"
        if interviews_dir.is_dir():
            for note in sorted(interviews_dir.glob("*.md")):
                ifm, _ = v.read_note(note)
                if ifm.get("type") != "interview":
                    continue
                when = str(ifm.get("when") or "")
                status = ifm.get("status") or "scheduled"
                interview = {
                    "company": app["company"],
                    "position": app["position"],
                    "application": rel,
                    "path": str(note.relative_to(vault)),
                    "fingerprint": v.fingerprint(note),
                    "when": when,
                    "date": when.split(" ")[0] if when else "",
                    "status": status,
                    # Kept for every consumer that asks "is this still ahead
                    # of me": only a scheduled interview is.
                    "upcoming": status == "scheduled",
                }
                for key in schema.NOTE_TYPES["interview"]["optional"]:
                    if key != "tags":
                        interview[key] = ifm.get(key)
                interviews.append(interview)

        applications.append(app)

    people_dir = vault / "People"
    if people_dir.is_dir():
        for note in sorted(people_dir.rglob("*.md")):
            fm, text = v.read_note(note)
            if fm.get("type") != "person":
                continue
            involvements = []
            for entry in _entries(text, "## Applications"):
                roles = [r.strip() for r in
                         re.split(r"[,;]", entry["fields"].get("roles", "")) if r.strip()]
                involvements.append({
                    "application": entry["title"],
                    "roles": roles,
                    **{k: val for k, val in entry["fields"].items() if k != "roles"},
                })
            people.append({
                "name": fm.get("name") or note.stem,
                "folder": (note.parent.relative_to(people_dir).as_posix()
                           if note.parent != people_dir else None),
                "via": fm.get("via"),
                "relationships": fm.get("relationships") or [],
                "professional_relationships": fm.get("professional_relationships") or [],
                "company_context": fm.get("company_context"),
                "reference_status": fm.get("reference_status"),
                "email": fm.get("email"),
                "phone": fm.get("phone"),
                "preferred_contact_method": fm.get("preferred_contact_method"),
                "next_follow_up": fm.get("next_follow_up"),
                "last_contact": fm.get("last_contact"),
                "permission_confirmed": fm.get("permission_confirmed"),
                "permission_confirmed_at": fm.get("permission_confirmed_at"),
                "applications": involvements,
                "path": str(note.relative_to(vault)),
                "fingerprint": v.fingerprint(note),
            })

    ev_dir = vault / "Career Evidence"
    if ev_dir.is_dir():
        for note in sorted(ev_dir.rglob("*.md")):
            fm, _ = v.read_note(note)
            kind = fm.get("type")
            if kind not in ("role", "accomplishment"):
                continue
            evidence.append({
                "kind": kind,
                "title": note.stem,
                "company": fm.get("company"),
                "role": fm.get("role") or fm.get("title"),
                "status": fm.get("status"),
                "skills": fm.get("skills") or fm.get("technologies") or [],
                "themes": fm.get("themes") or [],
                "path": str(note.relative_to(vault)),
            })

    return {
        "vault": str(vault),
        "vault_name": vault.name,
        "generated_note": "Derived from the markdown notes. Never edit; regenerate with export_index.py.",
        "applications": applications,
        "leads": leads,
        "archived": _archived(vault),
        "company_questions": company_questions,
        "contacts": contacts,
        "interviews": interviews,
        "people": people,
        "evidence": evidence,
        "skills": _skills(evidence),
    }


def _skills(evidence: list[dict]) -> dict:
    """Associate each skill with the evidence notes that support it.

    Derived entirely from `skills:` frontmatter, so a skill with no entry
    here has no evidence behind it — which is exactly what a resume audit
    needs to know. Casing differences collapse to the first spelling seen
    so 'GitHub' and 'Github' cannot fork into two skills.
    """
    canonical: dict[str, str] = {}
    out: dict[str, list[dict]] = {}
    for entry in evidence:
        for tech in entry["skills"]:
            name = canonical.setdefault(str(tech).strip().lower(), str(tech).strip())
            out.setdefault(name, []).append({
                "kind": entry["kind"],
                "title": entry["title"],
                "company": entry["company"],
                "path": entry["path"],
            })
    return dict(sorted(out.items(), key=lambda kv: kv[0].lower()))


def skill_matrix_markdown(vault: Path) -> str:
    """Render the skill -> evidence association as an Obsidian note."""
    skills = _skills(build(vault)["evidence"])
    out = [
        "# Skill Matrix\n\n",
        "Generated from `skills:` frontmatter across `Career Evidence/` — do not ",
        "edit by hand; regenerate with `python server/export_index.py --write-skill-matrix`.\n\n",
        "A skill listed on a resume but absent here has no evidence behind it.\n\n",
    ]
    for name, entries in skills.items():
        out.append(f"## {name}\n\n")
        for e in entries:
            label = "role" if e["kind"] == "role" else e["company"] or "accomplishment"
            out.append(f"- [[{e['path'][:-3]}|{e['title']}]] ({label})\n")
        out.append("\n")
    return "".join(out)


def write(vault: Path) -> Path:
    target = vault / ".cache" / "vault-index.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build(vault), indent=2) + "\n", encoding="utf-8")
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault")
    ap.add_argument("--stdout", action="store_true", help="print instead of writing .cache/")
    ap.add_argument("--write-field-reference", action="store_true",
                    help="regenerate Working Notes/Field Reference.md from schema.py")
    ap.add_argument("--write-skill-matrix", action="store_true",
                    help="regenerate Working Notes/Skill Matrix.md from evidence frontmatter")
    args = ap.parse_args()

    vault = v.require_vault(args.vault)

    if args.write_field_reference:
        target = vault / "Working Notes" / "Field Reference.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(schema.field_reference_markdown().rstrip("\n") + "\n",
                      encoding="utf-8")
        print(f"wrote {target.relative_to(vault)}")

    if args.write_skill_matrix:
        target = vault / "Working Notes" / "Skill Matrix.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(skill_matrix_markdown(vault).rstrip("\n") + "\n",
                      encoding="utf-8")
        print(f"wrote {target.relative_to(vault)}")

    if args.stdout:
        print(json.dumps(build(vault), indent=2))
    else:
        target = write(vault)
        data = json.loads(target.read_text(encoding="utf-8"))
        print(
            f"wrote {target.relative_to(vault)}: "
            f"{len(data['applications'])} applications, {len(data['contacts'])} contacts, "
            f"{len(data['interviews'])} interviews, {len(data['people'])} people, "
            f"{len(data['evidence'])} evidence notes"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
