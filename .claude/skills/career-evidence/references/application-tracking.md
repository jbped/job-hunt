# Application tracking

The accepted values for every field below live in `scripts/schema.py`, are
mirrored into `Working Notes/Field Reference.md` for reading in Obsidian, and are
enforced by `audit_vault.py`. Read them from there rather than from memory — this
file explains what the fields *mean*, not what values they take.

## Status

The flow runs `discovered → researching → preparing → applied → screening →
interviewing → offer`, with `rejected`, `withdrawn`, and `closed` as terminal
states. Record `next_action` and `next_action_date` whenever an application is
active; an active application with no next action is the most common way one
quietly dies.

## Discovery

Use one primary `discovery_method` and put the person's name, board, or site in
`discovery_detail`. Do not collapse a referral into a generic source — how a role
reached you shapes both the cover letter and the follow-up, and recording
`job-board` loses the fact that a specific person vouched for you.

## Job URL and posting source

- Store the direct job URL when available.
- If no URL was supplied, use `unknown`; do not substitute the company homepage.
- Store the posting source separately from how the candidate heard about it.
- Preserve the exact posting in `Job Description.md`.
- Record its SHA-256 checksum after capture and verify it during vault audits.

## Experience-level synthesis

Keep three distinct ideas:

1. Title or level stated by the employer.
2. Explicit tenure requirement.
3. Synthesized scope based on autonomy, architecture, project ownership, mentorship, and management expectations.

Use conventional labels such as junior, mid-level, senior individual contributor, staff-like scope, technical lead, or people manager. Explain the reasoning and do not convert adjacent experience into unsupported tenure.

## Compensation

Capture:

- Currency
- Minimum and maximum
- Period: hourly, monthly, or annual
- Base, bonus, commission, equity, signing, and benefits separately
- Whether the range came from the posting, recruiter, referral, or interview

Use `not-listed-in-captured-posting` or `unknown` instead of guessing. Keep candidate expectations in About Me, not in the employer's compensation fields.

## Contacts and referrals

Distinguish:

- Formal referral
- Informal referral
- Internal contact
- Recruiter
- Hiring manager
- Interviewer
- Scheduling contact

Record follow-up dates and contact methods. Do not infer that a formal referral is also a professional reference.

## Interview entries

Use local date, explicit time zone, and method. Preserve meeting links only when the vault's privacy policy permits; never put passwords, access tokens, or private keys in the vault.

For completed interviews, record evidence rather than only a positive/negative label:

- Questions and topics
- Candidate sentiment
- Interviewer signals
- Strong answers and weak answers
- New role information
- Commitments and follow-ups
- Preparation changes for the next stage

## Position synthesis

Keep the TL;DR concise. Break the position into outcomes, responsibilities, technologies/domain, team/collaboration, and logistics. Synthesis may paraphrase; the verbatim job-description note may not.
