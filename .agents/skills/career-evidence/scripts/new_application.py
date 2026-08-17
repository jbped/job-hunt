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

# Template -> destination. Resume Content and Cover Letter are created up front so
# the folder shape is predictable, even before there is anything to write in them.
FILES = {
    "Application Brief.md": "Application Brief.md",
    "Analysis.md": "Analysis.md",
    "Job Description.md": "Job Description.md",
    "Contacts.md": "Contacts.md",
    "Interviews.md": "Interviews.md",
    "Resume Content.md": "Resume Content.md",
    "Cover Letter.md": "Cover Letter.md",
    "Submission Notes.md": "Submission Notes.md",
}


def safe_name(value: str) -> str:
    """Keep folder names close to what the user typed but legal on disk."""
    cleaned = value.strip().rstrip(".")
    for char in '/\\:*?"<>|':
        cleaned = cleaned.replace(char, "-")
    return " ".join(cleaned.split())


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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("company")
    ap.add_argument("position")
    ap.add_argument("--url", default="")
    ap.add_argument("--discovery", default="", choices=schema.DISCOVERY_METHOD + [""])
    ap.add_argument("--detail", default="", help="referrer name, board, or site")
    ap.add_argument("--source", default="", help="where the posting lives")
    ap.add_argument("--vault")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    vault = v.require_vault(args.vault)
    folder = create(vault, args.company, args.position, url=args.url,
                    discovery=args.discovery, detail=args.detail, source=args.source)
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
