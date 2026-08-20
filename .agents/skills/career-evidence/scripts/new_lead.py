#!/usr/bin/env python3
"""Record a lead: a company or role worth looking into, before any application.

A lead is deliberately small — company alone is enough, and role and URL may
stay Unknown. Promotion (`new_application.py --from-lead`) scaffolds the real
application and links back; a passed lead keeps its reason as funnel data.

Usage:
    python new_lead.py "Acme Corp." [--role "Platform Engineer"] \
        [--url URL] [--source "[[People/Network/Full Name]]"] \
        [--follow-up 2026-09-01] [--vault PATH]
"""

from __future__ import annotations

from pathlib import Path
import argparse
import datetime
import json
import sys

import vaultlib as v
from new_application import safe_name

TEMPLATE = "Lead.md"


def source_wikilink(value: str) -> str:
    """Normalise a source contact to a wikilink; a bare name gets brackets."""
    value = value.strip()
    if not value or value.startswith("[["):
        return value
    return f"[[{value}]]"


def create(vault: Path, company: str, *, role: str = "", url: str = "",
           source: str = "", follow_up: str = "", today: str | None = None) -> Path:
    template = v.TEMPLATES_DIR / TEMPLATE
    if not template.exists():
        raise SystemExit(f"Missing template: {template}")
    company_name = safe_name(company)
    if not company_name:
        raise SystemExit(f"'{company}' sanitizes to an empty file name — pick a real name.")

    role = role.strip()
    known_role = role and role.lower() != "unknown"
    name = f"{company_name} - {safe_name(role)}" if known_role else company_name
    folder = vault / "Leads"
    target = folder / f"{name}.md"
    if target.exists():
        raise SystemExit(f"Already exists: {target.relative_to(vault)}\n"
                         "Nothing was changed. Update the existing lead instead.")

    today = today or datetime.date.today().isoformat()
    heading = f"{company} | {role}" if known_role else company

    text = template.read_text(encoding="utf-8")
    for key, value in (
        ("company", company),
        ("role", role if known_role else "Unknown"),
        ("url", url.strip()),
        ("source", source_wikilink(source)),
        ("date_added", today),
        ("next_follow_up", follow_up.strip()),
    ):
        if value:
            text = v.set_frontmatter_field(text, key, value)
    text = text.replace("# Company | Role", f"# {heading}", 1)

    folder.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("company")
    ap.add_argument("--role", default="", help="leave blank while unknown")
    ap.add_argument("--url", default="")
    ap.add_argument("--source", default="",
                    help="the person the interest came through, as a name or wikilink")
    ap.add_argument("--follow-up", default="", dest="follow_up", help="YYYY-MM-DD")
    ap.add_argument("--vault")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    vault = v.require_vault(args.vault)
    target = create(vault, args.company, role=args.role, url=args.url,
                    source=args.source, follow_up=args.follow_up)
    rel = target.relative_to(vault)

    if args.json:
        print(json.dumps({"path": str(rel), "absolute": str(target)}))
    else:
        print(f"Created {rel}")
        print("\nWhen it becomes real:")
        print(f"  python new_application.py --from-lead '{rel}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
