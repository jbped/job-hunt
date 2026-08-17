# Vault schema

## Structure

```text
VAULT_ROOT/
├── Job Hunt Dashboard.md
├── Start Here.md                  (new vaults; onboarding)
├── Applications.base              (live tables, Obsidian Bases)
├── References.base
├── About Me/
│   ├── Profile.md                 (also the cover-letter letterhead)
│   └── Interview Queue.md
├── Career Evidence/
│   ├── Roles/
│   └── Accomplishments/
├── Applications/
│   └── <Company>/
│       └── <Role>/
│           ├── Application Brief.md    <- the user's
│           ├── Analysis.md             <- the agent's
│           ├── Job Description.md      <- evidence, checksummed
│           ├── Contacts.md
│           ├── Interviews.md
│           ├── Resume Copy.md
│           ├── Cover Letter.md
│           ├── Submission Notes.md
│           └── Artifacts/              <- rendered PDFs, versioned
├── References/
│   └── Reference Index.md
├── Working Notes/
│   ├── Open Questions.md
│   └── Field Reference.md         (generated from scripts/schema.py)
├── Templates/
│   └── PDF/
└── .cache/                        (derived; safe to delete)
```

`References/` holds people who agreed to serve as a professional reference.
`Working Notes/` holds scratch and open questions. They are different things, and
the near-identical names they once had caused real confusion — keep them distinct.

## Ownership boundaries

- Career facts live in `Career Evidence/`. Everything else interprets them.
- Personal contact details, preferences, and publication boundaries live in
  `About Me/`. `Profile.md` frontmatter supplies the PDF letterhead.
- One employer's posting, analysis, contacts, interviews, and artifacts live in
  that application's folder.
- `Application Brief.md` is hand-maintained: update fields, never restructure.
- `Analysis.md` is agent-generated: rewrite it freely.
- Templates are scaffolds, never the only copy of a submitted artifact.
- `.cache/` is derived. `export_index.py` rebuilds it and nothing reads it as truth.

## Frontmatter

Vocabularies are defined once in `scripts/schema.py` and enforced by
`audit_vault.py`. Do not restate the lists elsewhere; read them from there.

### Role

```yaml
type: role
company:
title:
start:
end:
status: needs-interview | source-verified | documented
team:
tags: []
```

`source-verified` means the facts came from a prior artifact such as an old resume
rather than from the user — usable, but weaker than `documented`, and worth
re-confirming before it carries a claim.

### Accomplishment

```yaml
type: accomplishment
company:
role:
status: draft | partial | verified
ownership:
team:
technologies: []
themes: []
tags: [accomplishment]
```

Keep summary, problem, contribution, technical decisions, ownership, impact,
metric provenance, resume angles, cover-letter narrative, and open questions.

### Application

```yaml
type: application
company:
position:
status: discovered | researching | preparing | applied | screening |
        interviewing | offer | rejected | withdrawn | closed
job_url:
posting_source:
discovery_method:
discovery_detail:
date_found:
date_applied:
location:
work_model:
compensation_status:
compensation_currency / _min / _max / _period:
experience_level_stated:
next_action:
next_action_date:
```

This frontmatter drives the Bases dashboard and the web UI, so keeping it current
is what makes those views true.

### Analysis

```yaml
type: application-analysis
company:
position:
experience_level_synthesized:
```

The synthesised level lives here rather than on the brief because it is a
judgement, not something the employer stated.

### Job description

```yaml
type: job-description
captured_at:
source_url:
source_kind: pasted | webpage | recruiter
capture_status: verbatim
verbatim_sha256:
```

The fenced `## Verbatim posting` block is immutable source evidence. Preserve
exact words, spelling, bullet characters, order, and compensation text — including
mistakes. `capture_jd.py` writes it and computes the checksum; `audit_vault.py`
verifies the two still agree. A changed posting is a new dated capture, never an
edit in place.

### Contacts and interviews

These are sections within a note, not separate notes: `## Full Name` blocks in
`Contacts.md`, and `### YYYY-MM-DD HH:mm TZ | Stage` blocks under `## Upcoming`
or `## Previous` in `Interviews.md`, each followed by `- Field: value` bullets.

Both notes end with an `## Entry format` section documenting their own shape. The
tools skip it, and new entries are inserted above it.

Move a completed interview from Upcoming to Previous and add its outcome. Do not
create a second entry — one conversation should read as one entry.

### Professional reference

```yaml
type: professional-reference
name:
status: confirmed | requested | prospective | declined
relationship:
email / phone / preferred_contact_method:
permission_confirmed:
permission_confirmed_at:
```

`confirmed` only after explicit consent.

## Artifacts

Rendered files go in the application's `Artifacts/` as
`Resume v<N> <YYYY-MM-DD>.pdf`. `render_pdf.py` increments the version, so a
submitted artifact is never overwritten and can always be reconstructed.

## Link rules

- Link every accomplishment from its role note.
- Link an application to its posting, analysis, contacts, interviews, artifacts,
  and submission record.
- Link references to every associated application.
- Keep `Working Notes/Open Questions.md` an index, not a second evidence store.
- Inspect before editing; update the canonical note rather than creating a
  near-duplicate beside it.
