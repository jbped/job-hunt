#!/usr/bin/env python3
"""Create an empty job-hunt vault from the bundled template.

Deliberately deterministic: two people running this get byte-identical vaults,
so a friend's structure matches the one the skill's instructions describe. It
creates the scaffolding and nothing else — filling in a profile and the first
role note is a conversation with the agent, because that is where judgement is
needed and a prompt does better than a form.

Usage:
    python init_vault.py ~/Documents/Obsidian/job-hunt
"""

from __future__ import annotations

from pathlib import Path
import argparse
import shutil
import sys

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_ROOT / "assets" / "vault-template"

# Directories that must exist even though the template ships them empty; git and
# zip archives both drop empty directories.
DIRECTORIES = [
    "About Me",
    "Applications",
    "Career Evidence/Roles",
    "Career Evidence/Accomplishments",
    "References",
    "Templates/PDF",
    "Working Notes",
]


def create(target: Path, force: bool = False) -> Path:
    if not TEMPLATE.is_dir():
        raise SystemExit(f"The skill's vault template is missing: {TEMPLATE}")

    if target.exists():
        existing = [p for p in target.iterdir() if not p.name.startswith(".")]
        if existing and not force:
            raise SystemExit(
                f"{target} is not empty ({len(existing)} item(s)).\n"
                "Choose an empty directory, or pass --force to add the template alongside\n"
                "what is already there. Nothing was changed."
            )
    target.mkdir(parents=True, exist_ok=True)

    shutil.copytree(TEMPLATE, target, dirs_exist_ok=True)
    for relative in DIRECTORIES:
        (target / relative).mkdir(parents=True, exist_ok=True)

    return target


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", help="where to create the vault")
    ap.add_argument("--force", action="store_true",
                    help="write into a directory that already has content")
    args = ap.parse_args()

    target = Path(args.path).expanduser().resolve()
    create(target, args.force)

    notes = sum(1 for _ in target.rglob("*.md"))
    print(f"Created a job-hunt vault at {target}")
    print(f"  {notes} notes, {len(DIRECTORIES)} directories\n")
    print("Next:")
    print(f"  1. Open {target.name} as a vault in Obsidian.")
    print( "  2. Read 'Start Here.md'.")
    print( "  3. Ask your agent: \"set up my job hunt vault\" — it will interview you")
    print( "     for your profile and first role, which is the part worth doing carefully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
