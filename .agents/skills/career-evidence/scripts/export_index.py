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
# the example would index as a phantom contact or interview.
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

    Contacts, interviews, and reference logs all share this shape, so one
    parser covers them. Returns [] for the placeholder text the templates ship
    with ("No upcoming interviews recorded.").
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
                current = {"title": title, "fields": {}}
                out.append(current)
                continue
            if depth < level:
                current = None
            continue
        match = BULLET.match(line)
        if match and current is not None:
            key = match.group(1).strip().lower().replace(" ", "_")
            current["fields"][key] = match.group(2).strip()
    return [e for e in out if e["fields"]]


def _interview(entry: dict, app: dict, upcoming: bool) -> dict:
    """Split a `YYYY-MM-DD HH:mm TZ | Stage` heading into date and stage."""
    title = entry["title"]
    date, stage = (title.split("|", 1) + [""])[:2] if "|" in title else (title, "")
    date = date.strip()
    return {
        "company": app["company"],
        "position": app["position"],
        "application": app["path"],
        "when": date,
        "date": date.split(" ")[0] if date else "",
        "stage": stage.strip(),
        "upcoming": upcoming,
        **entry["fields"],
    }


def build(vault: Path) -> dict:
    applications, contacts, interviews, people, evidence = [], [], [], [], []

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
                     "Interviews.md", "Draft - Resume.md", "Draft - Cover Letter.md",
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

        interviews_note = folder / "Interviews.md"
        if interviews_note.exists():
            _, itext = v.read_note(interviews_note)
            for entry in _entries(itext, "## Upcoming"):
                interviews.append(_interview(entry, app, True))
            for entry in _entries(itext, "## Previous"):
                interviews.append(_interview(entry, app, False))

        applications.append(app)

    people_dir = vault / "People"
    if people_dir.is_dir():
        for note in sorted(people_dir.glob("*.md")):
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
                "relationships": fm.get("relationships") or [],
                "company_context": fm.get("company_context"),
                "reference_status": fm.get("reference_status"),
                "email": fm.get("email"),
                "phone": fm.get("phone"),
                "preferred_contact_method": fm.get("preferred_contact_method"),
                "permission_confirmed": fm.get("permission_confirmed"),
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
        "Generated from `skills:` frontmatter across `Career Evidence/` — do not\n",
        "edit by hand; regenerate with `python scripts/export_index.py --write-skill-matrix`.\n\n",
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
