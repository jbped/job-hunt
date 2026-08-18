# Vault schema

## Structure

```text
VAULT_ROOT/
├── Job Hunt Dashboard.md
├── Start Here.md                  (new vaults; onboarding)
├── Applications.base              (live tables, Obsidian Bases)
├── People.base
├── Career Evidence.base
├── Personal Information/
│   ├── Contact.md                 (audience-tagged; also the letterhead)
│   ├── About Me.md                (preferences, identity, cultural notes)
│   ├── Education.md
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
│           ├── Draft - Resume.md
│           ├── Draft - Cover Letter.md
│           ├── Submission Notes.md
│           └── Artifacts/              <- rendered PDFs, versioned
├── People/
│   └── <Full Name>.md             (one note per person)
├── Preferences/
│   └── README.md                  (+ the user's standing instructions)
├── Resources/
│   └── README.md                  (+ ingested source documents)
├── Working Notes/
│   ├── Open Questions.md
│   └── Field Reference.md         (generated from scripts/schema.py)
└── .cache/                        (derived; safe to delete)
```

`People/` holds one note per person, whatever their roles — contact, referral,
reference. Being a referral on one application and a reference for another are
relationships recorded on that one note, never a second file. `Working Notes/`
holds scratch and open questions; keep the two distinct.

`Preferences/` holds the user's standing instructions for how the agent works
this vault — tone, formatting tastes, workflow defaults. Plain markdown notes,
written by the user (or by the agent when asked to record a preference). They
tune how work is done and cannot override the truth and privacy rules or the
ownership boundaries below.

`Resources/` is the ingress point for source documents — old resumes, diplomas,
certificates. A file there is a source, not evidence: extract facts into notes
whose provenance lines point back at it, and never edit an ingested document.

## Formatting

Vault notes are read in Obsidian, which renders every newline as a visible
line break: write each paragraph (and each list item) as one long line, never
hard-wrapped at a column width. Repo files — skill docs, references, code —
stay conventionally wrapped; this rule is only for markdown that lands in the
vault.

## Ownership boundaries

- Career facts live in `Career Evidence/`. Everything else interprets them.
- Personal contact details, preferences, and publication boundaries live in
  `Personal Information/`. `Contact.md` frontmatter supplies the PDF letterhead,
  and each entry's `audience` (`self | application | recruiter | public`)
  controls where it may appear; `self` never leaves the vault.
- One employer's posting, analysis, contacts, interviews, and artifacts live in
  that application's folder.
- `Application Brief.md` is hand-maintained: update fields, never restructure.
- `Analysis.md` is agent-generated: rewrite it freely.
- Templates ship with the skill (`assets/templates/`), not the vault; a
  submitted artifact is never a template's only copy.
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
skills: []
tags: []
```

`skills` associates the role with the skills and tools its evidence supports
(`technologies` is the older spelling and is still read).
`export_index.py` aggregates it (with accomplishments' lists) into a skills map
and `--write-skill-matrix` renders it as `Working Notes/Skill Matrix.md` — a
skill absent from that matrix has no evidence behind it and must not appear
on a resume.

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
skills: []
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

The `## Verbatim posting` section, between `<!-- verbatim-start -->` and
`<!-- verbatim-end -->`, is immutable source evidence. Preserve
exact words, spelling, bullet characters, order, and compensation text — including
mistakes. `capture_jd.py` writes it and computes the checksum; `audit_vault.py`
verifies the two still agree. A changed posting is a new dated capture, never an
edit in place.

### Contacts and interviews

These are sections within a note, not separate notes: `## [[People/Full Name]]`
blocks in `Contacts.md` holding only application-specific facts (the person's
own details live on their `People/` note), and `### YYYY-MM-DD HH:mm TZ | Stage`
blocks under `## Upcoming` or `## Previous` in `Interviews.md`, each followed by
`- Field: value` bullets.

Both notes end with an `## Entry format` section documenting their own shape. The
tools skip it, and new entries are inserted above it.

Move a completed interview from Upcoming to Previous and add its outcome. Do not
create a second entry — one conversation should read as one entry.

### Person

```yaml
type: person
name:
relationships: []                  # contact-relationship values, vault-wide
company_context:
email / phone / preferred_contact_method:
reference_status: confirmed | requested | prospective | declined
permission_confirmed:
permission_confirmed_at:
```

The reference fields exist only once the person is being considered as a
professional reference; `confirmed` only after explicit consent. Per-application
involvement lives in the body's `## Applications` section as
`### Company | Position` blocks with `- Roles:` and follow-up bullets — that is
what the index reads to associate people with applications.

### Contact profile

```yaml
type: contact-profile
full_name:
preferred_name:
contacts:
  email: {value: "...", audience: self | application | recruiter | public}
```

One inline-map entry per contact detail. This is the only sanctioned nested
frontmatter in the vault; the tools read it but only ever write flat fields.

## Artifacts

Rendered files go in the application's `Artifacts/` as
`Resume v<N> <YYYY-MM-DD>.pdf`. `render_pdf.py` increments the version, so a
submitted artifact is never overwritten and can always be reconstructed.

## Link rules

- Link every accomplishment from its role note.
- Link an application to its posting, analysis, contacts, interviews, artifacts,
  and submission record.
- Link each application `Contacts.md` entry to its `People/` note, and list the
  application under that person's `## Applications` section.
- Keep `Working Notes/Open Questions.md` an index, not a second evidence store.
- Inspect before editing; update the canonical note rather than creating a
  near-duplicate beside it.
