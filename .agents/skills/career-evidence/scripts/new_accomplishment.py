#!/usr/bin/env python3
"""Scaffold an accomplishment note in Career Evidence/Accomplishments/.

Deterministic on purpose: the CLI and the web UI both call this, so an
accomplishment created either way has identical structure. It creates
structure, not evidence — the note keeps its Questions section so the next
evidence interview fills in the facts.

Usage:
    python new_accomplishment.py "Acme Corp." "Checkout Rewrite" \
        [--role "Software Engineer"] [--folder "Acme 2024-2025"] [--vault PATH]
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

import vaultlib as v
from new_application import safe_name

TEMPLATE = "Accomplishment.md"


def create(vault: Path, company: str, title: str, *, role: str = "",
           folder: str = "") -> Path:
    source = v.TEMPLATES_DIR / TEMPLATE
    if not source.exists():
        raise SystemExit(f"Missing template: {source}")
    title_name = safe_name(title)
    if not safe_name(company) or not title_name:
        raise SystemExit(
            f"'{company}' / '{title}' sanitize to an empty file name — pick real names.")

    root = vault / "Career Evidence" / "Accomplishments"
    # One canonical note per accomplishment, vault-wide — a same-named note in
    # another subfolder is almost certainly the same work.
    existing = next(root.rglob(f"{title_name}.md"), None) if root.is_dir() else None
    if existing is not None:
        raise SystemExit(f"Already exists: {existing.relative_to(vault)}\n"
                         "Nothing was changed. Update the canonical note instead.")

    parent = root
    if folder:
        sub = safe_name(folder)
        if not sub:
            raise SystemExit(f"'{folder}' sanitizes to an empty folder name.")
        parent = root / sub
    target = parent / f"{title_name}.md"

    text = source.read_text(encoding="utf-8")
    for key, value in (("company", company), ("role", role)):
        if value:
            text = v.set_frontmatter_field(text, key, value)
    text = text.replace("# Name", f"# {title}", 1)

    parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("company")
    ap.add_argument("title")
    ap.add_argument("--role", default="", help="the role this work happened in")
    ap.add_argument("--folder", default="",
                    help="optional subfolder, e.g. 'Acme 2024-2025'")
    ap.add_argument("--vault")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    vault = v.require_vault(args.vault)
    target = create(vault, args.company, args.title,
                    role=args.role, folder=args.folder)
    rel = target.relative_to(vault)

    if args.json:
        print(json.dumps({"path": str(rel), "absolute": str(target)}))
    else:
        print(f"Created {rel}")
        print("\nThe note is a scaffold: its Questions section is what an evidence")
        print("interview works through. Link it from its role note.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
