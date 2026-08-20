#!/usr/bin/env python3
"""Build a runnable demo vault with obviously fictional data.

Every note is produced by the same scripts the real workflows use, so the
demo can never drift from the schema — if a script changes shape, this
build changes with it, and the audit at the end still has to pass.

Usage:
    python demo/build_demo.py [--force]

Output lands in demo/vault/ (gitignored). --force deletes and rebuilds it.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import shutil
import sys

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / ".agents" / "skills" / "career-evidence" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import audit_vault          # noqa: E402
import capture_jd           # noqa: E402
import export_index         # noqa: E402
import init_vault           # noqa: E402
import new_accomplishment   # noqa: E402
import new_application      # noqa: E402
import new_lead             # noqa: E402
import new_role             # noqa: E402
import serve                # noqa: E402
import vaultlib as v        # noqa: E402

TARGET = REPO / "demo" / "vault"

# Every name, employer, and number below is deliberately fictional and round.
CONTACT = """---
type: contact-profile
full_name: Avery Demoson
preferred_name: Avery
contacts:
  location: {value: "Springfield, USA", audience: application}
  email: {value: "avery@example.com", audience: public}
  phone: {value: "555-0134", audience: recruiter}
  website: {value: "example.com/avery", audience: self}
---

# Contact

## Header

- Current resume title: Software Engineer
"""

POSTING = """Globex Corporation is hiring a Software Engineer II.

What you will do:
- Build and maintain our customer portal (TypeScript, Node)
- Own features end to end with a five-person product team
- Improve reliability of our order pipeline

What we look for:
- 3+ years building web applications
- Comfort with SQL and REST APIs
- Experience with containerized deployments is a plus

Salary range: $100,000 - $120,000 (annual)
"""

RESUME = """---
type: submission
company: Globex Corporation
position: Software Engineer II
status: draft
---

# Globex Corporation | Software Engineer II

## Header

Avery Demoson
Software Engineer
Springfield, USA · avery@example.com

## Summary

Software engineer with four years building web applications and the data pipelines behind them, including a dashboard rewrite serving 40 client teams.

## Experience

### Software Engineer | Acme Analytics | Mar 2022 - Jun 2024

- Rewrote the legacy reporting dashboard as a TypeScript single-page app, cutting median page load from 6 seconds to 2 seconds across 40 client teams.
- Added alerting to the order pipeline, cutting mean time to detect failures from hours to under 10 minutes.
- Reduced dashboard support tickets by 50% quarter over quarter.

### Junior Developer | Initech Labs | Jan 2020 - Feb 2022

- Maintained internal reporting scripts and stabilized the nightly data import that previously failed about once a week.

## Technical Skills

TypeScript, Node, Python, SQL, Docker
"""


def set_fields(path: Path, **fields: str) -> None:
    text = path.read_text(encoding="utf-8")
    for key, value in fields.items():
        text = v.set_frontmatter_field(text, key, value)
    path.write_text(text, encoding="utf-8")


def fill(path: Path, heading: str, *lines: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = v.append_section_entry(text, heading, "\n".join(lines))
    path.write_text(text, encoding="utf-8")


def set_skills(path: Path, skills: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("skills: []", f"skills: [{', '.join(skills)}]", 1),
                    encoding="utf-8")


def build(force: bool = False) -> Path:
    if TARGET.exists():
        if not force:
            raise SystemExit(f"{TARGET} already exists. Pass --force to rebuild it.")
        shutil.rmtree(TARGET)

    init_vault.create(TARGET)
    vault = TARGET
    (vault / "Personal Information" / "Contact.md").write_text(CONTACT, encoding="utf-8")

    # Evidence: two roles, three accomplishments, all round numbers.
    role1 = new_role.create(vault, "Acme Analytics", "Software Engineer",
                            start="2022-03", end="2024-06", team="Dashboards")
    set_fields(role1, status="documented")
    set_skills(role1, ["TypeScript", "Node", "SQL", "Docker"])
    fill(role1, "## Summary",
         "Built and maintained the reporting dashboard used by 40 client teams.")

    role2 = new_role.create(vault, "Initech Labs", "Junior Developer",
                            start="2020-01", end="2022-02", team="Platform")
    set_fields(role2, status="documented")
    set_skills(role2, ["Python", "SQL"])
    fill(role2, "## Summary",
         "Maintained internal reporting scripts and the nightly data import.")

    acc1 = new_accomplishment.create(vault, "Acme Analytics", "Dashboard Rewrite",
                                     role="Software Engineer",
                                     folder="Acme Analytics 2022-2024")
    set_fields(acc1, status="verified", ownership="primary, on a team of five")
    set_skills(acc1, ["TypeScript", "Node"])
    fill(acc1, "## Summary",
         "Rewrote the legacy reporting dashboard as a TypeScript single-page app.")
    fill(acc1, "## Impact",
         "- Cut median page load from 6 seconds to 2 seconds (measured across all 40 client teams, Q3 2023).",
         "- Reduced dashboard support tickets by 50% quarter over quarter (derived from the ticket tracker).")

    acc2 = new_accomplishment.create(vault, "Acme Analytics", "Order Pipeline Alerts",
                                     role="Software Engineer",
                                     folder="Acme Analytics 2022-2024")
    set_fields(acc2, status="verified", ownership="sole")
    set_skills(acc2, ["Node", "Docker"])
    fill(acc2, "## Summary",
         "Added alerting to the order pipeline so failures paged before customers noticed.")
    fill(acc2, "## Impact",
         "- Cut mean time to detect pipeline failures from hours to under 10 minutes (exact, from incident logs, 2023).")

    acc3 = new_accomplishment.create(vault, "Initech Labs", "Nightly Import Stabilization",
                                     role="Junior Developer",
                                     folder="Initech Labs 2020-2022")
    set_fields(acc3, status="partial", ownership="shared with one senior developer")
    set_skills(acc3, ["Python", "SQL"])
    fill(acc3, "## Summary",
         "Stabilized the nightly data import that previously failed about once a week.")

    # People: one referrer, one recruiter.
    serve.create_person(vault, {
        "name": "Jordan Exemplar", "professional_relationship": "former-coworker",
        "relationship": "informal-referral", "company_context": "Acme Analytics",
        "email": "jordan@example.com"})
    serve.create_person(vault, {
        "name": "Riley Placeholder", "relationship": "recruiter",
        "company_context": "Globex Corporation"})

    # Applications in three different states.
    app1 = new_application.create(vault, "Globex Corporation", "Software Engineer II",
                                  url="https://example.com/globex/se2",
                                  discovery="informal-referral",
                                  detail="Jordan Exemplar")
    capture_jd.capture(app1 / "Job Description.md", POSTING)
    set_fields(app1 / "Application Brief.md",
               status="applied", date_applied="2026-08-10",
               compensation_status="listed-in-posting",
               compensation_min="100000", compensation_max="120000",
               compensation_period="annual", work_model="hybrid",
               location="Springfield, USA",
               next_action="Follow up with the recruiter",
               next_action_date="2026-08-24")

    app2 = new_application.create(vault, "Hooli Systems", "Frontend Engineer",
                                  url="https://example.com/hooli/frontend",
                                  discovery="job-board", detail="Example job board")
    capture_jd.capture(app2 / "Job Description.md",
                       "Hooli Systems seeks a Frontend Engineer.\n\n"
                       "- Build internal tools in React\n"
                       "- Partner with design on the component library\n\n"
                       "Compensation is discussed during the process.")
    set_fields(app2 / "Application Brief.md", status="researching",
               compensation_status="not-listed-in-captured-posting")

    app3 = new_application.create(vault, "Umbrella Logistics", "Platform Engineer",
                                  url="https://example.com/umbrella/platform",
                                  discovery="recruiter-outreach", detail="Riley Placeholder")
    capture_jd.capture(app3 / "Job Description.md",
                       "Umbrella Logistics is hiring a Platform Engineer.\n\n"
                       "- Operate our container platform\n"
                       "- On-call rotation, one week in six\n\n"
                       "Compensation depends on experience.")
    set_fields(app3 / "Application Brief.md", status="rejected",
               date_applied="2026-07-01",
               compensation_status="unknown")

    # One rendered artifact, when Ghostscript is around; the vault is complete
    # without it, so a machine missing ps2pdf still gets a working demo.
    (app1 / "Draft - Resume.md").write_text(RESUME, encoding="utf-8")
    try:
        import render_pdf
        render_pdf.render(vault, app1, "resume", 1, preview=True)
    except SystemExit as error:
        print(f"note: skipped the rendered artifact ({error})", file=sys.stderr)

    # A lead that has not become an application yet.
    new_lead.create(vault, "Vandelay Industries", role="Backend Engineer",
                    source="[[People/Network/Jordan Exemplar]]",
                    url="https://example.com/vandelay/careers")

    export_index.write(vault)
    report = audit_vault.audit(vault)
    if report.errors:
        for error in report.errors:
            print(f"ERROR   {error}", file=sys.stderr)
        raise SystemExit("The demo vault failed its own audit — the build is wrong.")
    return vault


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="delete and rebuild demo/vault")
    args = ap.parse_args()
    vault = build(force=args.force)
    notes = sum(1 for _ in vault.rglob("*.md"))
    print(f"Built the demo vault at {vault} ({notes} notes; audit clean).")
    print("\nExplore it:")
    print(f"  python {SCRIPTS.relative_to(REPO)}/serve.py --vault demo/vault")
    print( "  or open demo/vault as a vault in Obsidian")
    return 0


if __name__ == "__main__":
    sys.exit(main())
