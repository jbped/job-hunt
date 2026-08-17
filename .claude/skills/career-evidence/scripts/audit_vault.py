#!/usr/bin/env python3
"""Check the vault's structure, frontmatter vocabulary, and evidence integrity.

Errors are things that are wrong: a broken structure, an illegal status value, a
posting whose checksum no longer matches. Warnings are things that are merely
missing — an unknown job URL is a real state of the world, not a defect, so the
right response to a warning is to find the information, never to invent it.

Usage:
    python audit_vault.py [VAULT_PATH] [--json]
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import sys

import schema
import vaultlib as v
from capture_jd import POSTING_BLOCK, checksum

REQUIRED_ROOT = [
    "Job Hunt Dashboard.md",
    "About Me",
    "Career Evidence",
    "Applications",
    "References",
    "Working Notes",
    "Templates",
]

APPLICATION_FILES = [
    "Application Brief.md",
    "Analysis.md",
    "Job Description.md",
    "Contacts.md",
    "Interviews.md",
    "Submission Notes.md",
]

TEMPLATES = [
    "Application Brief.md",
    "Analysis.md",
    "Job Description.md",
    "Contacts.md",
    "Interviews.md",
    "Reference.md",
    "About Me Profile.md",
    "Resume Copy.md",
    "Cover Letter.md",
    "Submission Notes.md",
    "PDF/Resume - Figma Inspired.ps",
    "PDF/Cover Letter - Figma Inspired.ps",
    "PDF/Generation Guide.md",
]

# Folders under Applications/ that are not real applications and are exempt from
# the full file set.
EXEMPT_COMPANIES = {"General"}

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def check_enums(report: Report, note: Path, vault: Path, fm: dict) -> None:
    note_type = fm.get("type")
    if not note_type:
        return
    rel = note.relative_to(vault)

    status = fm.get("status")
    allowed = schema.STATUS_BY_TYPE.get(note_type)
    if allowed and status and status not in allowed:
        report.error(f"{rel}: status '{status}' is not one of {', '.join(allowed)}")

    for field, values in schema.ENUMS.items():
        value = fm.get(field)
        if value and value not in values:
            report.error(f"{rel}: {field} '{value}' is not one of {', '.join(values)}")

    spec = schema.NOTE_TYPES.get(note_type)
    if spec:
        for field in spec["required"]:
            if not fm.get(field):
                report.warn(f"{rel}: missing required field '{field}'")


def check_job_description(report: Report, note: Path, vault: Path, fm: dict, text: str) -> None:
    rel = note.relative_to(vault)
    match = POSTING_BLOCK.search(text)
    if match is None:
        report.error(f"{rel}: no '## Verbatim posting' fenced text block")
        return

    posting = match.group(2)
    if not posting.strip() or "PASTE THE COMPLETE JOB DESCRIPTION" in posting:
        report.warn(f"{rel}: posting not captured yet")
        return

    stamped = fm.get("verbatim_sha256")
    if not stamped:
        report.warn(f"{rel}: missing verbatim_sha256 (run capture_jd.py --recompute)")
        return

    actual = checksum(posting)
    if stamped != actual:
        report.error(
            f"{rel}: verbatim_sha256 does not match the posting — it has been edited "
            "since capture. Restore it, or record the new text as a separate dated capture."
        )


def check_links(report: Report, note: Path, vault: Path, text: str) -> None:
    """Flag wikilinks that resolve to nothing, since Obsidian shows them as normal text."""
    stems = {p.stem for p in vault.rglob("*.md")}
    names = {p.name for p in vault.rglob("*") if p.is_file()}
    for target in WIKILINK.findall(text):
        target = target.strip()
        if not target:
            continue
        leaf = target.rsplit("/", 1)[-1]
        if leaf in stems or leaf in names or f"{leaf}.md" in names:
            continue
        if (vault / target).exists() or (vault / f"{target}.md").exists():
            continue
        report.warn(f"{note.relative_to(vault)}: unresolved link [[{target}]]")


def audit(vault: Path, check_wikilinks: bool = True) -> Report:
    report = Report()

    for relative in REQUIRED_ROOT:
        if not (vault / relative).exists():
            report.error(f"missing root item: {relative}")

    for relative in TEMPLATES:
        if not (vault / "Templates" / relative).exists():
            report.error(f"missing template: Templates/{relative}")

    applications = vault / "Applications"
    if applications.is_dir():
        for brief in sorted(applications.glob("*/*/Application Brief.md")):
            folder = brief.parent
            rel = folder.relative_to(vault)
            exempt = folder.relative_to(applications).parts[0] in EXEMPT_COMPANIES

            if not exempt:
                for name in APPLICATION_FILES:
                    if not (folder / name).exists():
                        report.warn(f"{rel}: missing {name}")
                if not (folder / "Artifacts").is_dir():
                    report.warn(f"{rel}: missing Artifacts/ folder for rendered PDFs")

            fm, _ = v.read_note(brief)
            if not exempt:
                for field in ("job_url", "discovery_method", "compensation_status"):
                    if not fm.get(field):
                        report.warn(f"{rel}/Application Brief.md: {field} not recorded")

    for note in sorted(vault.rglob("*.md")):
        if ".cache" in note.parts or "Templates" in note.parts:
            continue
        fm, text = v.read_note(note)
        check_enums(report, note, vault, fm)
        if fm.get("type") == "job-description":
            check_job_description(report, note, vault, fm, text)
        if check_wikilinks:
            check_links(report, note, vault, text)

    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("vault", nargs="?", default=None)
    ap.add_argument("--vault", dest="vault_flag", help="same as the positional argument")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-links", action="store_true", help="skip wikilink resolution")
    args = ap.parse_args()

    vault = v.require_vault(args.vault_flag or args.vault)
    report = audit(vault, check_wikilinks=not args.no_links)

    if args.json:
        print(json.dumps({
            "vault": str(vault),
            "errors": report.errors,
            "warnings": report.warnings,
        }, indent=2))
        return 1 if report.errors else 0

    print(f"Vault: {vault}")
    for warning in report.warnings:
        print(f"WARNING {warning}")
    for error in report.errors:
        print(f"ERROR   {error}")
    print(f"Result: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    if report.warnings and not report.errors:
        print("Warnings are missing information. Find the value or leave it Unknown; never invent it.")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
