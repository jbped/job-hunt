# Vault schema

## Structure

```text
VAULT_ROOT/
├── Job Hunt Dashboard.md
├── Start Here.md                  (new vaults; onboarding)
├── Applications.base              (live tables, Obsidian Bases)
├── People.base
├── Career Evidence.base
├── Leads.base
├── Personal Information/
│   ├── Contact.md                 (audience-tagged; also the letterhead)
│   ├── About Me.md                (preferences, identity, cultural notes)
│   ├── Education.md
│   └── Interview Queue.md
├── Career Evidence/
│   ├── Roles/
│   └── Accomplishments/
├── Leads/
│   └── <Company> - <Role>.md      (pre-application interest; company alone is enough)
├── Applications/
│   └── <Company>/
│       └── <Role>/
│           ├── Application Brief.md    <- the user's
│           ├── Analysis.md             <- the agent's
│           ├── Job Description.md      <- evidence, checksummed
│           ├── Contacts.md
│           ├── Interviews/             (one note per interview)
│           ├── Draft - Resume.md
│           ├── Draft - Cover Letter.md
│           ├── Submission Notes.md
│           └── Artifacts/              <- rendered PDFs, versioned
├── People/
│   ├── Network/                   (people the user has a real relationship with)
│   │   └── <Full Name>.md         (one note per person, in exactly one folder)
│   ├── Recruiters/                (agency and in-house recruiters)
│   └── Job Hunt/                  (targets, interviewers, company contacts)
├── Preferences/
│   └── README.md                  (+ the user's standing instructions)
├── Resources/
│   └── README.md                  (+ ingested source documents)
├── Working Notes/
│   ├── Open Questions.md
│   └── Field Reference.md         (generated from scripts/schema.py)
└── .cache/                        (derived; safe to delete)
```

`People/` holds one note per person, filed in exactly one subfolder by
relationship warmth: `Network/` for people the user has a real relationship
with (coworkers past and present, managers, mentors, friends, family),
`Recruiters/` for agency and in-house recruiters, and `Job Hunt/` for everyone
who exists in the vault because of the search — networking targets,
interviewers, hiring managers, company contacts. The folder answers "how well
do I know them"; everything finer-grained stays in frontmatter, so a note moves
folders only when the relationship itself changes (a cold contact becoming a
real connection moves to `Network/`). `professional_relationships` records how
they worked with the user; `relationships` records vault-wide job-search roles
(including `networking-target` for someone the user is trying to reach and
`connector` for someone bridging an introduction); `via` links the person who
provides the introduction path; application entries record roles specific to
one application. Being a former manager, a referral, and a reference can all be
true on the same note. `Working Notes/` holds scratch and open questions; keep
the two distinct.

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
compensation_requested:            # what you asked for, when, and in which conversation
experience_level_stated:
next_action:
next_action_date:
```

This frontmatter drives the Bases dashboard and the web UI, so keeping it current
is what makes those views true.

### Lead

```yaml
type: lead
company:
role: Unknown
url:
source: "[[People/<Folder>/Full Name]]"   # who the interest came through
date_added:
status: new | pursuing | promoted | passed
next_follow_up:
passed_reason:                     # required in spirit once passed
application: "[[Applications/<Company>/<Role>/Application Brief]]"   # set on promotion
```

A lead is pre-application interest, one small note in `Leads/`. Company alone
is a valid lead; the file is `<Company>.md` until the role is known, then
`<Company> - <Role>.md`. `new_application.py --from-lead <path>` promotes it:
the application is scaffolded with the lead's URL, the source contact becomes
`discovery_detail` (the discovery method itself is never inferred), and the
lead is marked `promoted` with the `application` link back. A passed lead
keeps its `passed_reason` — that is funnel data, not garbage.

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
source_kind: pasted | webpage | recruiter | extension
capture_status: verbatim
verbatim_sha256:
```

The `## Verbatim posting` section, between `<!-- verbatim-start -->` and
`<!-- verbatim-end -->`, is immutable source evidence. Preserve
exact words, spelling, bullet characters, order, and compensation text — including
mistakes. `capture_jd.py` writes it and computes the checksum; `audit_vault.py`
verifies the two still agree. A changed posting is a new dated capture, never an
edit in place.

### Contacts

Contacts are sections within `Contacts.md`, not separate notes:
`## [[People/<Folder>/Full Name]]` blocks holding only application-specific
facts (the person's own details live on their `People/` note), each followed by
`- Field: value` bullets. The note ends with an `## Entry format` section
documenting its own shape; the tools skip it and insert new entries above it.

### Interview

One note per interview, in the application's `Interviews/` folder, named
`<YYYY-MM-DD> <HHmm> <Stage>.md`:

```yaml
type: interview
company:
position:
status: scheduled | completed | cancelled
when:                              # date-leading, e.g. 2026-09-02 14:00 MDT
stage:                             # interview stage vocabulary
method: phone | video | onsite | async | unknown
location_or_link:
point_of_contact:
interviewers:
thank_you_sent:
next_step:
```

The body holds `## Preparation` and `## Outcome` as prose. Completing or
cancelling an interview is a status change, never a move and never a second
note — one conversation reads as one note, and its history stays in git.

### Person

```yaml
type: person
name:
professional_relationships: []     # how they worked with the user
relationships: []                  # job-search roles, vault-wide
company_context:
via: "[[People/<Folder>/Full Name]]"   # who the introduction path runs through
email / phone / preferred_contact_method:
next_follow_up:                    # relationship cadence, independent of applications
last_contact:
reference_status: confirmed | requested | prospective | declined
permission_confirmed:
permission_confirmed_at:
```

Professional relationships are directional relative to the user: `manager`
means the person managed the user, while `direct-report` means the user managed
the person. Current/former is explicit where it matters for outreach. The
reference fields exist only once the person is being considered as a professional
reference; `confirmed` only after explicit consent. `via` is optional and holds
a wikilink to the person's note whose introduction makes this contact reachable
— set it on the target, not the connector. `next_follow_up` and `last_contact`
are the person's own cadence — when to reach out next and when contact last
happened — distinct from the per-application follow-up bullets on a
`Contacts.md` entry. Per-application involvement
lives in the body's `## Applications` section as
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
