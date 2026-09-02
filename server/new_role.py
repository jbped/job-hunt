#!/usr/bin/env python3
"""Scaffold a role note in Career Evidence/Roles/ from the skill's template.

Deterministic on purpose: the CLI and the web UI both call this, so a role
created either way has identical structure. It creates structure, not
evidence — the note keeps its Questions section so the next evidence
interview fills in the facts.

Usage:
    python new_role.py "Acme Corp." "Software Developer III" \
        [--start 2024-02] [--end 2025-08] [--team "Platform"] [--vault PATH]
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

import vaultlib as v
from new_application import safe_name

TEMPLATE = "Role.md"


def create(vault: Path, company: str, title: str, *, start: str = "",
           end: str = "", team: str = "") -> Path:
    source = v.TEMPLATES_DIR / TEMPLATE
    if not source.exists():
        raise SystemExit(f"Missing template: {source}")
    company_name, title_name = safe_name(company), safe_name(title)
    if not company_name or not title_name:
        raise SystemExit(
            f"'{company}' / '{title}' sanitize to an empty file name — pick real names.")

    folder = vault / "Career Evidence" / "Roles"
    target = folder / f"{company_name} - {title_name}.md"
    if target.exists():
        raise SystemExit(f"Already exists: {target.relative_to(vault)}\n"
                         "Nothing was changed. One canonical note per role — add to it.")

    text = source.read_text(encoding="utf-8")
    for key, value in (("company", company), ("title", title),
                       ("start", start), ("end", end), ("team", team)):
        if value:
            text = v.set_frontmatter_field(text, key, value)
    text = text.replace("# Company | Title", f"# {company} | {title}", 1)

    folder.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("company")
    ap.add_argument("title")
    ap.add_argument("--start", default="", help="YYYY-MM")
    ap.add_argument("--end", default="", help="YYYY-MM, blank while current")
    ap.add_argument("--team", default="")
    ap.add_argument("--vault")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    vault = v.require_vault(args.vault)
    target = create(vault, args.company, args.title,
                    start=args.start, end=args.end, team=args.team)
    rel = target.relative_to(vault)

    if args.json:
        print(json.dumps({"path": str(rel), "absolute": str(target)}))
    else:
        print(f"Created {rel}")
        print("\nThe note is a scaffold: its Questions section is what an evidence")
        print("interview works through. Link each accomplishment from this note.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
