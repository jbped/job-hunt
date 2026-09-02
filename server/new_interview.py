#!/usr/bin/env python3
"""Scaffold an interview note inside an application's Interviews/ folder.

One note per interview. The structured facts (when, stage, method, people)
live in frontmatter so the dashboard can edit them in place; Preparation and
Outcome are prose sections. Completion is a status change, not a move.

Usage:
    python new_interview.py "Applications/Co/Role" "2026-09-02 14:00 MDT" \
        [--stage hiring-manager] [--method video] [--contact "Name"] \
        [--interviewers "Names"] [--location URL] [--vault PATH]
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import sys

import schema
import vaultlib as v
from new_application import safe_name

DATE_LEADING = re.compile(r"^\d{4}-\d{2}-\d{2}(\s|$)")


def create(vault: Path, app_rel: str, when: str, *, stage: str = "",
           method: str = "", location: str = "", contact: str = "",
           interviewers: str = "") -> Path:
    folder = (vault / app_rel).resolve()
    try:
        folder.relative_to(vault.resolve())
    except ValueError:
        raise SystemExit(f"'{app_rel}' is outside the vault.")
    brief = folder / "Application Brief.md"
    if not brief.is_file():
        raise SystemExit(f"{app_rel} is not an application folder "
                         "(no Application Brief.md).")

    when = " ".join(when.split())
    if not DATE_LEADING.match(when):
        raise SystemExit(f"'{when}' must start with the date as YYYY-MM-DD "
                         "(e.g. '2026-09-02 14:00 MDT') so interviews sort.")
    if stage and stage not in schema.INTERVIEW_STAGE:
        raise SystemExit(f"Unknown stage '{stage}'. "
                         f"Use one of: {', '.join(schema.INTERVIEW_STAGE)}")
    if method and method not in schema.INTERVIEW_METHOD:
        raise SystemExit(f"Unknown method '{method}'. "
                         f"Use one of: {', '.join(schema.INTERVIEW_METHOD)}")

    fm, _ = v.read_note(brief)
    company = str(fm.get("company") or folder.parent.name)
    position = str(fm.get("position") or folder.name)

    # Date, compact time, stage: "2026-09-02 1400 Hiring-manager.md" — readable,
    # sortable, and legal on every filesystem.
    parts = when.split()
    time = parts[1].replace(":", "") if len(parts) > 1 else ""
    name = safe_name(" ".join(p for p in (parts[0], time, stage or "Interview") if p))
    target = folder / "Interviews" / f"{name}.md"
    if target.exists():
        raise SystemExit(f"Already exists: {target.relative_to(vault)}\n"
                         "One note per interview — edit it, or vary the stage.")

    text = (v.TEMPLATES_DIR / "Interview.md").read_text(encoding="utf-8")
    for key, value in (("company", company), ("position", position),
                       ("when", when), ("stage", stage), ("method", method),
                       ("location_or_link", location),
                       ("point_of_contact", contact),
                       ("interviewers", interviewers)):
        if value:
            text = v.set_frontmatter_field(text, key, value)
    text = text.replace("# Company | Position", f"# {company} | {position}", 1)

    target.parent.mkdir(exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("app", help="application folder, relative to the vault")
    ap.add_argument("when", help="date-leading, e.g. '2026-09-02 14:00 MDT'")
    ap.add_argument("--stage", default="", choices=schema.INTERVIEW_STAGE + [""])
    ap.add_argument("--method", default="", choices=schema.INTERVIEW_METHOD + [""])
    ap.add_argument("--location", default="", help="location or meeting link")
    ap.add_argument("--contact", default="", help="point of contact")
    ap.add_argument("--interviewers", default="")
    ap.add_argument("--vault")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    vault = v.require_vault(args.vault)
    target = create(vault, args.app, args.when, stage=args.stage,
                    method=args.method, location=args.location,
                    contact=args.contact, interviewers=args.interviewers)
    rel = target.relative_to(vault)
    if args.json:
        print(json.dumps({"path": str(rel), "absolute": str(target)}))
    else:
        print(f"Created {rel}")
        print("Preparation and Outcome live in the note; completion is "
              "status: completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
