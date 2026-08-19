#!/usr/bin/env python3
"""Create an empty job-hunt vault from the bundled template.

Deliberately deterministic: two people running this get byte-identical vaults,
so a friend's structure matches the one the skill's instructions describe. It
creates the scaffolding and nothing else — filling in a profile and the first
role note is a conversation with the agent, because that is where judgement is
needed and a prompt does better than a form.

Usage:
    python init_vault.py [~/Documents/Obsidian/job-hunt]

Without a path it creates the repo's own gitignored `vault/`.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import shutil
import sys

from vaultlib import DEFAULT_VAULT

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_ROOT / "assets" / "vault-template"

# The note Obsidian seeds into every brand-new vault. Removed only on an exact
# (whitespace-normalized) match — an edited or translated note is user content.
OBSIDIAN_WELCOME = """\
This is your new *vault*.

Make a note of something, [[create a link]], or try [the Importer](https://help.obsidian.md/Plugins/Importer)!

When you're ready, delete this note and make the vault your own.
"""


def is_stock_welcome(path: Path) -> bool:
    if path.name != "Welcome.md" or not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return " ".join(text.split()) == " ".join(OBSIDIAN_WELCOME.split())


# Directories that must exist even though the template ships them empty; git and
# zip archives both drop empty directories.
DIRECTORIES = [
    "Personal Information",
    "Applications",
    "Career Evidence/Roles",
    "Career Evidence/Accomplishments",
    "People/Network",
    "People/Recruiters",
    "People/Job Hunt",
    "Preferences",
    "Resources",
    "Working Notes",
]


def create(target: Path, force: bool = False) -> Path:
    if not TEMPLATE.is_dir():
        raise SystemExit(f"The skill's vault template is missing: {TEMPLATE}")

    if target.exists():
        welcome = target / "Welcome.md"
        if is_stock_welcome(welcome):
            welcome.unlink()
        existing = [p for p in target.iterdir() if not p.name.startswith(".")]
        if existing and not force:
            raise SystemExit(
                f"{target} is not empty ({len(existing)} item(s)).\n"
                "Choose an empty directory, or pass --force to add the template alongside\n"
                "what is already there. Nothing was changed."
            )
    target.mkdir(parents=True, exist_ok=True)

    # Never overwrite: a template file whose destination already exists is
    # skipped, so even --force cannot clobber a populated vault.
    skipped: list[Path] = []
    for src in sorted(TEMPLATE.rglob("*")):
        dst = target / src.relative_to(TEMPLATE)
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        elif dst.exists():
            skipped.append(dst.relative_to(target))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    for relative in DIRECTORIES:
        (target / relative).mkdir(parents=True, exist_ok=True)

    return target, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default=None,
                    help="where to create the vault "
                         "(default: the repo's gitignored vault/)")
    ap.add_argument("--force", action="store_true",
                    help="add missing template files to a directory that already "
                         "has content; existing files are never overwritten")
    args = ap.parse_args()

    target = (Path(args.path).expanduser().resolve() if args.path
              else DEFAULT_VAULT)
    _, skipped = create(target, args.force)
    if skipped:
        print(f"Left {len(skipped)} existing note(s) untouched:")
        for rel in skipped:
            print(f"  {rel}")

    notes = sum(1 for _ in target.rglob("*.md"))
    print(f"Created a job-hunt vault at {target}")
    print(f"  {notes} notes, {len(DIRECTORIES)} directories\n")
    print("Next:")
    print(f"  1. In Obsidian, choose \"Open folder as vault\" and select {target}.")
    print( "     (Not \"Create new vault\" — that would nest a new folder inside.)")
    print( "  2. Read 'Start Here.md'.")
    print( "  3. Ask your agent: \"set up my job hunt vault\" — it will interview you")
    print( "     for your profile and first role, which is the part worth doing carefully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
