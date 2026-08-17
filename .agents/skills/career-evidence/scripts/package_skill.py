#!/usr/bin/env python3
"""Build a distributable zip of the skill for people who don't want the repo.

The zip unpacks to a single `career-evidence/` folder, ready to drop into
`~/.claude/skills/` (or any agent's skills directory). Only the skill's own
files go in — never the vault, caches, or anything gitignored.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from vaultlib import SKILL_ROOT, REPO_ROOT

EXCLUDED_DIRS = {"__pycache__", ".cache", ".git"}
EXCLUDED_FILES = {".DS_Store", ".env"}


def skill_files() -> list[Path]:
    files = []
    for path in sorted(SKILL_ROOT.rglob("*")):
        if not path.is_file():
            continue
        parts = path.relative_to(SKILL_ROOT).parts
        if any(part in EXCLUDED_DIRS for part in parts):
            continue
        if path.name in EXCLUDED_FILES or path.suffix == ".pyc":
            continue
        files.append(path)
    return files


def build(output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in skill_files():
            arcname = Path("career-evidence") / path.relative_to(SKILL_ROOT)
            zf.write(path, arcname.as_posix())
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "dist" / "career-evidence-skill.zip",
    )
    args = parser.parse_args()
    target = build(args.output.expanduser().resolve())
    count = len(skill_files())
    size_kb = target.stat().st_size / 1024
    print(f"Wrote {target} ({count} files, {size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
