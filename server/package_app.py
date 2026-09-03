#!/usr/bin/env python3
"""Build a distributable zip of the application for people who don't want the repo.

The zip is the app itself, rooted at the repo layout: unzip it anywhere and
run `python3 server/serve.py` from the unzipped root. The skills ride along
under `.agents/skills/` so an agent host can point at them in place. Only the
project's own files go in — never the vault, caches, or anything gitignored.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from vaultlib import REPO_ROOT

SKILLS_ROOT = REPO_ROOT / ".agents" / "skills"
EXCLUDED_DIRS = {"__pycache__", ".cache", ".git", "vault", "superpowers"}
EXCLUDED_FILES = {".DS_Store", ".env"}

# What the application is made of, repo-relative. Directories are walked;
# files ship as named.
APP_TOP_LEVEL = [
    "server",
    "extension",
    "docs",
    # The image's entrypoint lives here: without it `docker compose build`
    # fails on an unzipped release, which is exactly the path this archive is.
    "docker",
    "Dockerfile",
    "compose.yaml",
    ".dockerignore",
    ".env.example",
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
]

# The skills that ship. Anything else under the skills root is a personal
# install (gitignored) and must never enter the archive.
CANONICAL_SKILLS = {
    "career-evidence",
    "cover-letter-pdf",
    "cross-check",
    "draft-cover-letter",
    "draft-resume",
    "init-vault",
    "new-application",
    "new-person",
    "resume-pdf",
}


def _keep(path: Path, relative_to: Path) -> bool:
    if not path.is_file():
        return False
    if any(part in EXCLUDED_DIRS for part in path.relative_to(relative_to).parts):
        return False
    return path.name not in EXCLUDED_FILES and path.suffix != ".pyc"


def app_files() -> list[Path]:
    files = []
    for top in APP_TOP_LEVEL:
        path = REPO_ROOT / top
        if path.is_file():
            files.append(path)
            continue
        files.extend(p for p in sorted(path.rglob("*")) if _keep(p, REPO_ROOT))
    for skill in sorted(CANONICAL_SKILLS):
        root = SKILLS_ROOT / skill
        files.extend(p for p in sorted(root.rglob("*")) if _keep(p, SKILLS_ROOT))
    return files


def build(output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in app_files():
            zf.write(path, path.relative_to(REPO_ROOT).as_posix())
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "dist" / "career-evidence-app.zip",
    )
    args = parser.parse_args()
    target = build(args.output.expanduser().resolve())
    count = len(app_files())
    size_kb = target.stat().st_size / 1024
    print(f"Wrote {target} ({count} files, {size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
