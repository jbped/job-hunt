#!/usr/bin/env python3
"""Write a job posting into Job Description.md verbatim and stamp its checksum.

The checksum is the point. It turns "preserve the posting exactly" from a rule
someone has to remember into something the vault audit can verify — so if a
posting is ever edited, reflowed, or spell-corrected after capture, it shows up
as an error instead of silently becoming the evidence for a resume claim.

The posting text is preserved after newline normalization only — CRLF becomes
LF and trailing newlines are trimmed. No words, spelling, punctuation, or
ordering are ever changed.

Usage:
    python capture_jd.py --app "Applications/Co/Role" --file posting.txt
    pbpaste | python capture_jd.py --app "Applications/Co/Role"
"""

from __future__ import annotations

from pathlib import Path
import argparse
import datetime
import hashlib
import re
import sys

import vaultlib as v

MARKED_BLOCK = re.compile(
    r"(## Verbatim posting\s*\n\s*<!-- verbatim-start -->\n)(.*?)(\n<!-- verbatim-end -->)",
    re.DOTALL,
)
# Pre-2026-08 captures fenced the posting in a ```text block; still readable.
FENCED_BLOCK = re.compile(r"(## Verbatim posting\s*\n\s*```text\n)(.*?)(\n```)", re.DOTALL)


def find_posting(text: str) -> re.Match | None:
    return MARKED_BLOCK.search(text) or FENCED_BLOCK.search(text)


def checksum(posting: str) -> str:
    return hashlib.sha256(posting.encode("utf-8")).hexdigest()


def capture(note: Path, posting: str, *, source_url: str = "", source_kind: str = "",
            today: str | None = None, force: bool = False) -> str:
    """Replace the marked block and stamp verbatim_sha256. Returns the checksum."""
    text = note.read_text(encoding="utf-8")
    match = find_posting(text)
    if match is None:
        raise SystemExit(
            f"{note.name} has no '## Verbatim posting' block delimited by "
            "<!-- verbatim-start --> and <!-- verbatim-end -->.\n"
            "Recreate it from the skill's assets/templates/Job Description.md."
        )

    existing = match.group(2)
    placeholder = "PASTE THE COMPLETE JOB DESCRIPTION" in existing
    if existing.strip() and not placeholder and not force:
        raise SystemExit(
            f"{note.name} already holds a captured posting.\n"
            "A changed posting is a new dated capture, not an edit — that is what the\n"
            "checksum protects. Use --force only to fix a botched initial capture."
        )

    posting = posting.replace("\r\n", "\n").rstrip("\n")
    if not posting.strip():
        raise SystemExit("Refusing to capture an empty posting.")
    closer = "```" if match.group(3).lstrip() == "```" else "<!-- verbatim-end -->"
    if closer in posting:
        raise SystemExit(
            f"The posting contains '{closer}', which would break the block.\n"
            "Paste it into the note by hand and compute the checksum with --recompute."
        )

    digest = checksum(posting)
    text = text[:match.start(2)] + posting + text[match.end(2):]
    text = v.set_frontmatter_field(text, "verbatim_sha256", digest)
    text = v.set_frontmatter_field(text, "capture_status", "verbatim")
    text = v.set_frontmatter_field(text, "captured_at", today or datetime.date.today().isoformat())
    if source_url:
        text = v.set_frontmatter_field(text, "source_url", source_url)
    if source_kind:
        text = v.set_frontmatter_field(text, "source_kind", source_kind)

    note.write_text(text, encoding="utf-8")
    return digest


def recompute(note: Path) -> tuple[str, bool]:
    """Restamp the checksum from the current block. Returns (digest, changed)."""
    text = note.read_text(encoding="utf-8")
    match = find_posting(text)
    if match is None:
        raise SystemExit(f"{note.name} has no verbatim posting block.")
    digest = checksum(match.group(2))
    updated = v.set_frontmatter_field(text, "verbatim_sha256", digest)
    changed = updated != text
    if changed:
        note.write_text(updated, encoding="utf-8")
    return digest, changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app", help="application folder, relative to the vault or absolute")
    ap.add_argument("--note", help="path to a Job Description.md directly")
    ap.add_argument("--file", help="read the posting from a file instead of stdin")
    ap.add_argument("--url", default="")
    ap.add_argument("--kind", default="", choices=["pasted", "webpage", "recruiter", ""])
    ap.add_argument("--force", action="store_true", help="overwrite an existing capture")
    ap.add_argument("--recompute", action="store_true",
                    help="restamp the checksum from the block already in the note")
    ap.add_argument("--vault")
    args = ap.parse_args()

    vault = v.require_vault(args.vault)

    if args.note:
        note = Path(args.note).expanduser()
    elif args.app:
        folder = Path(args.app).expanduser()
        if not folder.is_absolute():
            folder = vault / args.app
        note = folder / "Job Description.md"
    else:
        raise SystemExit("Pass --app <application folder> or --note <Job Description.md>")

    if not note.exists():
        raise SystemExit(f"Not found: {note}")

    if args.recompute:
        digest, changed = recompute(note)
        print(f"{'updated' if changed else 'unchanged'} verbatim_sha256: {digest}")
        return 0

    posting = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    digest = capture(note, posting, source_url=args.url, source_kind=args.kind, force=args.force)
    shown = note.relative_to(vault) if note.resolve().is_relative_to(vault) else note
    print(f"Captured {len(posting.splitlines())} lines into {shown}")
    print(f"verbatim_sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
