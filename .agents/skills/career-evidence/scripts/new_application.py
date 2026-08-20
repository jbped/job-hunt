#!/usr/bin/env python3
"""Scaffold an application folder from the skill's templates.

Deterministic on purpose: the CLI and the web UI both call this, so an
application created either way has identical structure and prefilled fields.

Usage:
    python new_application.py "Acme Corp." "Software Developer III" \
        [--url URL] [--discovery formal-referral] [--detail "Contact name"] \
        [--source "Referral"] [--vault PATH]
"""

from __future__ import annotations

from pathlib import Path
import argparse
import datetime
import json
import sys

import schema
import vaultlib as v

# Template -> destination. Draft - Resume and Draft - Cover Letter are created up front so
# the folder shape is predictable, even before there is anything to write in them.
FILES = {
    "Application Brief.md": "Application Brief.md",
    "Analysis.md": "Analysis.md",
    "Job Description.md": "Job Description.md",
    "Contacts.md": "Contacts.md",
    "Interviews.md": "Interviews.md",
    "Draft - Resume.md": "Draft - Resume.md",
    "Draft - Cover Letter.md": "Draft - Cover Letter.md",
    "Submission Notes.md": "Submission Notes.md",
}


# Names Windows refuses as files or folders regardless of extension.
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL",
                    *(f"COM{n}" for n in range(1, 10)),
                    *(f"LPT{n}" for n in range(1, 10))}


def safe_name(value: str) -> str:
    """Keep folder names close to what the user typed but legal on disk."""
    cleaned = value.strip().rstrip(".")
    for char in '/\\:*?"<>|':
        cleaned = cleaned.replace(char, "-")
    cleaned = " ".join(cleaned.split())
    if cleaned.split(".")[0].upper() in WINDOWS_RESERVED:
        cleaned += "-"
    return cleaned


def create(vault: Path, company: str, position: str, *, url: str = "",
           discovery: str = "", detail: str = "", source: str = "",
           today: str | None = None) -> Path:
    templates = v.TEMPLATES_DIR
    company_dir, position_dir = safe_name(company), safe_name(position)
    if not company_dir or not position_dir:
        raise SystemExit(
            f"'{company}' / '{position}' sanitize to an empty folder name.\n"
            "The index only sees Applications/<Company>/<Role>/ — pick real names."
        )
    folder = vault / "Applications" / company_dir / position_dir
    if folder.exists():
        raise SystemExit(f"Already exists: {folder.relative_to(vault)}\nNothing was changed.")

    if discovery and discovery not in schema.DISCOVERY_METHOD:
        raise SystemExit(
            f"Unknown discovery method '{discovery}'.\n"
            f"Use one of: {', '.join(schema.DISCOVERY_METHOD)}"
        )

    missing = [n for n in FILES if not (templates / n).exists()]
    if missing:
        raise SystemExit(f"Missing templates: {', '.join(missing)}")

    today = today or datetime.date.today().isoformat()
    heading = f"{company} | {position}"

    folder.mkdir(parents=True)
    (folder / "Artifacts").mkdir()

    for template_name, out_name in FILES.items():
        text = (templates / template_name).read_text(encoding="utf-8")
        if text.startswith("---"):
            for key, value in (("company", company), ("position", position)):
                try:
                    text = v.set_frontmatter_field(text, key, value)
                except ValueError:
                    pass
        # Templates head their body with a generic "Company | Position" line.
        text = text.replace("# Company | Position", f"# {heading}", 1)
        text = text.replace("# Name", f"# {heading}", 1)
        (folder / out_name).write_text(text, encoding="utf-8")

    brief = folder / "Application Brief.md"
    text = brief.read_text(encoding="utf-8")
    for key, value in (
        ("status", "discovered"),
        ("date_found", today),
        ("job_url", url),
        ("discovery_method", discovery),
        ("discovery_detail", detail),
        ("posting_source", source),
    ):
        if value:
            text = v.set_frontmatter_field(text, key, value)
    brief.write_text(text, encoding="utf-8")

    jd = folder / "Job Description.md"
    jd_text = jd.read_text(encoding="utf-8")
    jd_text = v.set_frontmatter_field(jd_text, "captured_at", today)
    if url:
        jd_text = v.set_frontmatter_field(jd_text, "source_url", url)
    jd.write_text(jd_text, encoding="utf-8")

    return folder


def _wikilink_name(value: str) -> str:
    """The display name inside a `[[...]]` link, or the value unchanged."""
    value = str(value or "").strip()
    if value.startswith("[[") and value.endswith("]]"):
        inner = value[2:-2].split("|")[-1]
        return inner.rsplit("/", 1)[-1].strip()
    return value


def promote_lead(vault: Path, lead_rel: str, *, today: str | None = None) -> Path:
    """Scaffold the application a lead points at, and mark the lead promoted.

    The lead's source contact becomes discovery_detail only — how the interest
    arrived is a fact, but the discovery method is the user's call, never
    inferred from a wikilink.
    """
    lead_path = (vault / lead_rel).resolve()
    try:
        lead_path.relative_to(vault.resolve())
    except ValueError:
        raise SystemExit(f"'{lead_rel}' is outside the vault.")
    if not lead_path.is_file():
        raise SystemExit(f"No such lead: {lead_rel}")

    fm, text = v.read_note(lead_path)
    if fm.get("type") != "lead":
        raise SystemExit(f"{lead_rel} is not a lead note (type: {fm.get('type')}).")
    if fm.get("status") == "promoted":
        raise SystemExit(f"{lead_rel} is already promoted"
                         f" (application: {fm.get('application') or 'unrecorded'}).")
    company = str(fm.get("company") or "").strip()
    role = str(fm.get("role") or "").strip()
    if not company:
        raise SystemExit(f"{lead_rel} has no company recorded.")
    if not role or role.lower() == "unknown":
        raise SystemExit(f"{lead_rel} still has role Unknown — record the actual "
                         "role on the lead before promoting it.")

    fingerprint = v.fingerprint(lead_path)
    folder = create(vault, company, role,
                    url=str(fm.get("url") or "").strip(),
                    detail=_wikilink_name(fm.get("source")),
                    today=today)

    app_rel = folder.relative_to(vault)
    text = v.set_frontmatter_field(text, "status", "promoted")
    text = v.set_frontmatter_field(
        text, "application", f"[[{app_rel.as_posix()}/Application Brief]]")
    v.atomic_write(lead_path, text, expect=fingerprint, vault=vault)
    return folder


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("company", nargs="?", default="")
    ap.add_argument("position", nargs="?", default="")
    ap.add_argument("--from-lead", default="", dest="from_lead",
                    help="vault-relative path of a lead note to promote")
    ap.add_argument("--url", default="")
    ap.add_argument("--discovery", default="", choices=schema.DISCOVERY_METHOD + [""])
    ap.add_argument("--detail", default="", help="referrer name, board, or site")
    ap.add_argument("--source", default="", help="where the posting lives")
    ap.add_argument("--vault")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    vault = v.require_vault(args.vault)
    if args.from_lead:
        folder = promote_lead(vault, args.from_lead)
    elif args.company and args.position:
        folder = create(vault, args.company, args.position, url=args.url,
                        discovery=args.discovery, detail=args.detail, source=args.source)
    else:
        ap.error("give a company and position, or --from-lead <path>")
    rel = folder.relative_to(vault)

    if args.json:
        print(json.dumps({"path": str(rel), "absolute": str(folder)}))
    else:
        print(f"Created {rel}")
        print("\nNext:")
        print(f"  1. Capture the posting:  python capture_jd.py --app '{rel}' --file posting.txt")
        print( "  2. Fill Application Brief.md (URL, compensation, next action)")
        print( "  3. Ask the agent to write Analysis.md from the posting and your evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
