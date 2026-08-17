#!/usr/bin/env python3
"""Single definition of the vault's frontmatter vocabulary.

Every script and the web UI import from here so the enum lists exist in exactly
one place. `Working Notes/Field Reference.md` is generated from this module, so
the human-readable documentation cannot drift from what the tools enforce.
"""

from __future__ import annotations

# Status flow. Terminal states end the pipeline; the rest are active.
APPLICATION_STATUS = [
    "discovered",
    "researching",
    "preparing",
    "applied",
    "screening",
    "interviewing",
    "offer",
    "rejected",
    "withdrawn",
    "closed",
]

TERMINAL_STATUS = {"rejected", "withdrawn", "closed"}
ACTIVE_STATUS = [s for s in APPLICATION_STATUS if s not in TERMINAL_STATUS]

# How the candidate learned about the role. Kept distinct from posting_source,
# which records where the posting itself lives.
DISCOVERY_METHOD = [
    "formal-referral",
    "informal-referral",
    "recruiter-outreach",
    "job-board",
    "company-site",
    "professional-network",
    "word-of-mouth",
    "event",
    "other",
    "unknown",
]

COMPENSATION_STATUS = [
    "listed-in-posting",
    "provided-by-recruiter",
    "discussed-in-interview",
    "not-listed-in-captured-posting",
    "unknown",
]

COMPENSATION_PERIOD = ["hourly", "monthly", "annual", "unknown"]

WORK_MODEL = ["onsite", "hybrid", "remote", "unknown"]

# A person can hold several of these at once; they are not mutually exclusive,
# which is why contact notes carry a list rather than a single value.
CONTACT_RELATIONSHIP = [
    "formal-referral",
    "informal-referral",
    "internal-contact",
    "recruiter",
    "hiring-manager",
    "interviewer",
    "scheduler",
    "other",
]

INTERVIEW_STAGE = [
    "recruiter-screen",
    "hiring-manager",
    "technical-screen",
    "take-home",
    "technical-panel",
    "system-design",
    "behavioral",
    "onsite",
    "final",
    "other",
]

INTERVIEW_METHOD = ["phone", "video", "onsite", "async", "unknown"]

REFERENCE_PERMISSION = ["confirmed", "requested", "prospective", "declined"]

# Trust-descending disclosure levels for contact details. `self` never leaves
# the vault; everything else may appear on artifacts for that audience or wider.
CONTACT_AUDIENCE = ["self", "application", "recruiter", "public"]

# Increasing confidence. `source-verified` means the facts were carried over
# from a prior artifact (an old resume, a Figma frame) rather than confirmed by
# the user — usable, but weaker evidence than `documented`.
ROLE_STATUS = ["needs-interview", "source-verified", "documented"]

ACCOMPLISHMENT_STATUS = ["draft", "partial", "verified"]

SUBMISSION_STATUS = ["draft", "ready", "submitted", "confirmed"]

# Claim classes from references/writing-standards.md. Recorded on accomplishment
# metrics so a resume bullet can never silently upgrade an estimate to a fact.
CLAIM_CLASS = ["exact", "approved-estimate", "derived", "qualitative", "unknown"]


# Field name -> allowed values. Anything absent from this map is free text.
ENUMS = {
    "discovery_method": DISCOVERY_METHOD,
    "compensation_status": COMPENSATION_STATUS,
    "compensation_period": COMPENSATION_PERIOD,
    "work_model": WORK_MODEL,
    "stage": INTERVIEW_STAGE,
    "method": INTERVIEW_METHOD,
    "reference_status": REFERENCE_PERMISSION,
}

# `status` means something different per note type, so it is resolved here
# rather than in ENUMS.
STATUS_BY_TYPE = {
    "application": APPLICATION_STATUS,
    "role": ROLE_STATUS,
    "accomplishment": ACCOMPLISHMENT_STATUS,
    "submission": SUBMISSION_STATUS,
}

# Note types, their required fields, and the optional fields the tools know how
# to read. Unknown extra keys are always preserved untouched.
NOTE_TYPES = {
    "application": {
        "file": "Application Brief.md",
        "required": ["type", "company", "position", "status"],
        "optional": [
            "job_url",
            "posting_source",
            "discovery_method",
            "discovery_detail",
            "date_found",
            "date_applied",
            "location",
            "work_model",
            "compensation_status",
            "compensation_currency",
            "compensation_min",
            "compensation_max",
            "compensation_period",
            "experience_level_stated",
            "next_action",
            "next_action_date",
            "tags",
        ],
    },
    "application-analysis": {
        "file": "Analysis.md",
        "required": ["type", "company", "position"],
        "optional": ["experience_level_synthesized", "tags"],
    },
    "role": {
        "required": ["type", "company", "title", "status"],
        "optional": ["start", "end", "team", "skills", "tags"],
    },
    "accomplishment": {
        "required": ["type", "company", "status"],
        "optional": ["role", "ownership", "team", "skills", "themes", "tags"],
    },
    # One note per person. Referral and reference are relationships this person
    # holds, not separate note types; `applications` records their involvement
    # per application so the index can build the associative view.
    "person": {
        "required": ["type", "name"],
        "optional": [
            "relationships",
            "company_context",
            "email",
            "phone",
            "preferred_contact_method",
            "reference_status",
            "permission_confirmed",
            "permission_confirmed_at",
            "applications",
            "tags",
        ],
    },
    "contact-profile": {
        "file": "Contact.md",
        "required": ["type", "full_name"],
        "optional": ["preferred_name", "contacts", "tags"],
    },
    "about-me": {
        "file": "About Me.md",
        "required": ["type"],
        "optional": ["tags"],
    },
    "education": {
        "file": "Education.md",
        "required": ["type"],
        "optional": ["tags"],
    },
    "submission": {
        "required": ["type", "company", "position"],
        "optional": ["submitted_at", "channel", "status", "tags"],
    },
    "job-description": {
        "file": "Job Description.md",
        "required": ["type", "company", "position", "capture_status"],
        "optional": ["captured_at", "source_url", "source_kind", "verbatim_sha256", "tags"],
    },
    "application-contacts": {
        "file": "Contacts.md",
        "required": ["type", "company", "position"],
        "optional": ["tags"],
    },
    "application-interviews": {
        "file": "Interviews.md",
        "required": ["type", "company", "position"],
        "optional": ["tags"],
    },
}

# Fields the web UI may edit in place, per note type. Everything else is
# read-only to the UI and must be edited in Obsidian. Keeping this list here
# rather than in serve.py means the write surface is auditable in one glance.
UI_EDITABLE = {
    "application": [
        "status",
        "next_action",
        "next_action_date",
        "date_applied",
        "job_url",
        "posting_source",
        "discovery_method",
        "discovery_detail",
        "location",
        "work_model",
        "compensation_status",
        "compensation_currency",
        "compensation_min",
        "compensation_max",
        "compensation_period",
        "experience_level_stated",
    ],
    "person": [
        "reference_status",
        "email",
        "phone",
        "preferred_contact_method",
        "permission_confirmed",
        "permission_confirmed_at",
    ],
}

# Notes the UI must never write to, at any path. The verbatim posting and its
# checksum are evidence; submitted artifacts are historical record.
UI_READONLY_FILES = ["Job Description.md", "Submission Notes.md"]


def allowed_values(note_type: str, field: str) -> list[str] | None:
    """Return the legal values for a field, or None if it is free text."""
    if field == "status":
        return STATUS_BY_TYPE.get(note_type)
    return ENUMS.get(field)


def is_active(status: str) -> bool:
    return status not in TERMINAL_STATUS


def field_reference_markdown() -> str:
    """Render the vocabulary as an Obsidian note so it is visible in the vault."""
    def block(title: str, values: list[str]) -> str:
        return f"### {title}\n\n" + "\n".join(f"- `{v}`" for v in values) + "\n\n"

    out = [
        "# Field Reference\n\n",
        "Generated from the skill's `scripts/schema.py` — do not edit by hand; ",
        "regenerate with `python scripts/export_index.py --write-field-reference`.\n\n",
        "These are the values the tools accept in note frontmatter. ",
        "Anything outside these lists is flagged by the vault audit.\n\n",
        "## Application\n\n",
        block("status", APPLICATION_STATUS),
        block("discovery_method", DISCOVERY_METHOD),
        block("compensation_status", COMPENSATION_STATUS),
        block("compensation_period", COMPENSATION_PERIOD),
        block("work_model", WORK_MODEL),
        "## People\n\n",
        block("contact relationship", CONTACT_RELATIONSHIP),
        block("reference permission (`reference_status`)", REFERENCE_PERMISSION),
        block("contact audience", CONTACT_AUDIENCE),
        "## Interviews\n\n",
        block("stage", INTERVIEW_STAGE),
        block("method", INTERVIEW_METHOD),
        "## Evidence\n\n",
        block("role status", ROLE_STATUS),
        block("accomplishment status", ACCOMPLISHMENT_STATUS),
        block("claim class", CLAIM_CLASS),
        "## Submission\n\n",
        block("submission status", SUBMISSION_STATUS),
    ]
    return "".join(out)


if __name__ == "__main__":
    print(field_reference_markdown())
