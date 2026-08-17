#!/usr/bin/env python3
"""Answer 'where am I, what's coming up, what do I need to do' in the terminal.

Same questions the web dashboard answers, available without Obsidian or a
browser — useful over SSH, and as a quick check that the index reflects reality.

Usage:
    python status.py [--vault PATH] [--all] [--days 14]
"""

from __future__ import annotations

from pathlib import Path
import argparse
import datetime

import export_index
import schema
import vaultlib as v

# Applications sitting in these states with no movement are the ones that
# quietly go stale; applied/screening/interviewing all imply someone owes a reply.
STALE_AFTER_DAYS = 14


def parse_date(value) -> datetime.date | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m"):
        try:
            return datetime.datetime.strptime(text[:len(fmt) + 2].strip(), fmt).date()
        except ValueError:
            continue
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault")
    ap.add_argument("--all", action="store_true", help="include closed applications")
    ap.add_argument("--days", type=int, default=STALE_AFTER_DAYS)
    args = ap.parse_args()

    vault = v.require_vault(args.vault)
    data = export_index.build(vault)
    today = datetime.date.today()

    apps = data["applications"]
    shown = apps if args.all else [a for a in apps if a["active"]]

    print(f"Vault: {vault}")
    print(f"Date:  {today.isoformat()}\n")

    # Where am I
    print("WHERE AM I")
    if not shown:
        print("  No active applications.")
    for status in schema.APPLICATION_STATUS:
        group = [a for a in shown if a["status"] == status]
        if not group:
            continue
        print(f"  {status}")
        for a in group:
            applied = parse_date(a.get("date_applied"))
            age = f"  ({(today - applied).days}d since applied)" if applied else ""
            print(f"    - {a['company']} | {a['position']}{age}")

    # What's coming up
    print("\nWHAT'S COMING UP")
    upcoming = []
    for iv in data["interviews"]:
        if not iv["upcoming"]:
            continue
        when = parse_date(iv.get("date"))
        upcoming.append((when or datetime.date.max, iv))
    for when, iv in sorted(upcoming, key=lambda p: p[0]):
        label = iv["when"] or "date unknown"
        print(f"  {label}  {iv['company']} | {iv['stage'] or 'interview'}")

    due = []
    for a in shown:
        when = parse_date(a.get("next_action_date"))
        if when and a.get("next_action"):
            due.append((when, a))
    for when, a in sorted(due, key=lambda p: p[0]):
        if when <= today + datetime.timedelta(days=args.days):
            flag = "OVERDUE" if when < today else "due"
            print(f"  {when.isoformat()}  [{flag}] {a['company']}: {a['next_action']}")

    if not upcoming and not due:
        print("  Nothing scheduled.")

    # What do I need to do
    print("\nWHAT DO I NEED TO DO")
    todo = []
    for a in shown:
        if not a.get("next_action"):
            todo.append(f"{a['company']} | {a['position']}: no next action recorded")
            continue
        if not a.get("next_action_date"):
            todo.append(f"{a['company']}: '{a['next_action']}' has no due date")
        applied = parse_date(a.get("date_applied"))
        if applied and a["status"] in ("applied", "screening") and (today - applied).days > args.days:
            todo.append(
                f"{a['company']}: {(today - applied).days} days since applying with no status change"
            )

    unconfirmed = [p for p in data["people"]
                   if p["reference_status"] and p["reference_status"] != "confirmed"]
    if unconfirmed:
        todo.append(f"{len(unconfirmed)} professional reference(s) not yet confirmed")

    questions = vault / "Working Notes" / "Open Questions.md"
    if questions.exists():
        count = sum(1 for line in questions.read_text(encoding="utf-8").split("\n")
                    if line.strip().startswith("- ") and line.strip().endswith("?"))
        if count:
            todo.append(f"{count} open question(s) in Working Notes/Open Questions.md")

    for item in todo:
        print(f"  - {item}")
    if not todo:
        print("  Nothing outstanding.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
