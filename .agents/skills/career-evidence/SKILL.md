---
name: career-evidence
description: Maintain an Obsidian job-hunt vault holding verified career evidence, verbatim job postings, application tracking, referrals and contacts, interview history, professional references, and generated resumes and cover letters. Use this whenever the user mentions their job search, an application, a job posting, a resume or CV, a cover letter, an interview, a recruiter, a referral, or a professional reference — and also when they want to record an accomplishment, tailor or audit application materials, prepare interview stories, check where their applications stand, or set up a new job-hunt vault from scratch. Works with a vault containing Job Hunt Dashboard.md and Career Evidence/, and can create one.
---

# Career Evidence

The vault is the source of truth. Resumes, cover letters, and PDFs are generated
artifacts — always reconstructible, never the place a fact first appears.

The rules below exist because job-hunt writing is done under pressure, and the
pressure always points the same way: toward rounding a number up, toward implying
sole ownership, toward claiming the technology the posting asks for. Evidence that
survives that pressure is what makes fast generation safe.

## Find the vault

`CAREER_EVIDENCE_VAULT` in the repo's `.env` names the vault. Failing that, walk
upward from the working directory for a folder containing both
`Job Hunt Dashboard.md` and `Career Evidence/`; failing that too, the repo's
own `vault/` if it exists. That is `VAULT_ROOT`.

The vault is personal data and the repo is shareable tooling, so the vault
lives either outside the repo or in the gitignored `vault/` at the repo root —
never in history. If none of the three lookups finds a vault, ask before
creating one; never silently make a second vault.

Scripts live in this skill's `scripts/` and resolve the vault the same way, so
they work from any directory. `--vault PATH` overrides. Stdlib-only Python 3.

```text
init_vault.py <path>              create an empty vault
new_application.py "Co" "Role"    scaffold an application folder
new_application.py --from-lead P  promote a lead into an application
new_lead.py "Co" [--role R]       record pre-application interest in Leads/
new_role.py "Co" "Title"          scaffold a role note in Career Evidence
new_accomplishment.py "Co" "Name" scaffold an accomplishment note
capture_jd.py --app <folder>      store a posting verbatim + checksum
render_pdf.py --app <folder>      build and validate a PDF
status.py                         where am I / coming up / to do
serve.py                          the same as a local web dashboard
serve.py --detach | --stop        run it in the background / stop it
export_index.py                   rebuild .cache/vault-index.json
audit_vault.py                    check structure, vocabulary, evidence
```

Prefer these over doing the same work by hand: they produce identical results
every time, and `audit_vault.py` is written against what they produce.

## Workflow skills

The step-by-step workflows live in sibling skills. Load and follow the matching
skill when doing that work; how a user or host invokes it varies by agent. This
note holds the rules they all share.

- [`init-vault`](../init-vault/SKILL.md) — first-time setup of a new
  vault
- [`new-application`](../new-application/SKILL.md) — scaffold the
  folder, capture the posting verbatim, write the analysis
- [`new-person`](../new-person/SKILL.md) — one `People/` note per professional
  connection, including coworkers, leaders, contacts, recruiters, and references
- [`draft-resume`](../draft-resume/SKILL.md) and
  [`draft-cover-letter`](../draft-cover-letter/SKILL.md) — tailor the
  working copies from verified evidence
- [`resume-pdf`](../resume-pdf/SKILL.md) and
  [`cover-letter-pdf`](../cover-letter-pdf/SKILL.md) — render and
  validate the artifacts

## Who owns which note

This split is the thing to get right. Inside an application folder:

- **`Application Brief.md` is the user's.** Status, URL, compensation, dates,
  next action. Update a field when asked; do not restructure it, reorder it, or
  move their prose into a shape you prefer. Someone reads this file by hand.
- **`Analysis.md` is yours.** Compatibility confidence, fit-by-term evidence
  alignment, resume and cover-letter strategy, claims to verify. Synthesis only —
  never a restated posting; quote a term only where it is being judged. Rewrite
  it freely — it is derived, and regenerating it costs nothing.
- **`Job Description.md` is neither.** It is evidence, checksummed. Never edit a
  captured posting; a changed posting is a new dated capture.

The same idea holds vault-wide: `Career Evidence/` records what happened,
everything else interprets it.

When writing any vault note, put each paragraph on one line — Obsidian renders
every newline as a line break, so hard-wrapped prose displays broken
mid-sentence.

## Read further when the task calls for it

- [vault-schema.md](references/vault-schema.md) — creating, moving, or
  reorganising notes; frontmatter shapes.
- [evidence-interview.md](references/evidence-interview.md) — capturing career
  evidence by interview: the question dimensions, batch protocol, and how
  answers are filed.
- [application-tracking.md](references/application-tracking.md) — applications,
  discovery, compensation, contacts, interviews, level synthesis.
- [writing-standards.md](references/writing-standards.md) — any copy that will
  reach an employer.
- [document-generation.md](references/document-generation.md) — resumes, cover
  letters, PDF rendering and validation.

The controlled vocabularies (statuses, discovery methods, stages) are defined in
`scripts/schema.py` and mirrored into `Working Notes/Field Reference.md`.
`audit_vault.py` enforces them, so use a listed value or add one deliberately.

## Truth and privacy

- Preserve exact facts, ownership, dates, metrics, provenance, and uncertainty.
- Use `Unknown` when a value is unavailable. Do not infer URLs, compensation,
  contact details, interview logistics, or titles. A gap is information.
- Keep exact, approved-estimate, derived, qualitative, and unknown claims
  distinguishable from each other, all the way to the resume bullet.
- Do not turn overlapping roles into additive tenure.
- Never store passwords, meeting passwords, tokens, private keys, or confidential
  customer data.
- Referrals, contacts, interviewers, and professional references are different
  roles. Someone willing to forward a resume has not agreed to take a call.
- Add a person to confirmed references only after explicit consent.
- Do not publish personal or cultural details until the user confirms both the
  facts and the channel.

## Preferences

`Preferences/` in the vault holds the user's standing instructions — tone,
formatting tastes, workflow defaults. Read every note there before starting
any workflow and follow them as if the user had just said them. They tune how
the work is done; they cannot override the truth and privacy rules above or
the note-ownership boundaries. When the user states a preference meant to
outlast the session, offer to record it there.

## First-time setup

If `Personal Information/Contact.md` is missing or still has empty contact
fields, the user is starting out — switch to
the [`init-vault`](../init-vault/SKILL.md) workflow and walk them through setup
rather than filling forms silently.

## Capture career evidence

Evidence is captured by structured interview — the full protocol is
[evidence-interview.md](references/evidence-interview.md). The shape of it:

1. Read the role note and any linked accomplishments first.
2. Keep open questions in the note's `## Questions` section, grouped by the
   interview dimensions (context, contribution, collaboration, decisions,
   adoption, impact, learning, publication).
3. Ask in batches of three to five, highest resume leverage first. Accept
   `unknown` and record it where the fact would live.
4. Chase every metric to its class, source, denominator, and period, and every
   ownership word to sole, shared, primary, or supporting.
5. File answers into the note body or frontmatter and delete the question;
   never answer inline. Promote status only when the evidence supports it.
6. Update one canonical accomplishment note; link it from the role.
7. Index anything still unresolved in `Working Notes/Open Questions.md` by
   linking the note's Questions section, not restating it.

## Applications, resumes, and cover letters

Creating an application, drafting a resume or cover letter, and rendering the
PDFs are the workflow skills above. The shared rule: capture and analysis
come before drafting, drafting comes before rendering, and every external claim
traces to evidence at each step.

## Track contacts, interviews, and references

- Record both how the person worked with the user (`professional_relationships`)
  and any job-search role they hold (`relationships` or an application entry),
  plus organisation, title, contact details, preferred method, referral status,
  last contact, and next follow-up. Never imply an endorsement beyond what the
  user confirmed.
- For upcoming interviews capture date, time, time zone, stage, contacts,
  interviewers, method, link or location, duration, and preparation priorities.
- Afterwards, move the entry from Upcoming to Previous — do not create a second
  one — and add sentiment, interviewer signals, what went well, concerns,
  takeaways, questions asked, commitments, thank-you status, and next step.
  Record evidence, not just a good/bad verdict; the details drive the next stage.
- One note per professional reference, with what they can credibly discuss and
  explicit consent. Log each request so nobody is surprised or overused.

## Prepare for interviews

Select narratives for the competencies likely to be assessed and expand each into
context, problem, decisions, contribution, tradeoffs, result, and learning. Keep
team attribution, uncertainty, adoption limits, and setbacks intact — a story
that admits a tradeoff is more convincing than one that does not, and it is the
only version that survives follow-up questions.

## Submit and preserve

Record the exact resume, cover letter, job-description capture, channel,
timestamp, and confirmation in `Submission Notes.md`. Update status, date applied,
next action, and follow-up date. Never overwrite a submitted artifact —
`render_pdf.py` versions automatically. Notify a referral only when asked.

## Audit

Trace every material external claim back to canonical evidence. Flag unsupported
numbers, ownership inflation, percentages without a denominator, confidential
names, stale contact data, invented URLs, inferred compensation, and keywords
with no evidence behind them.

Run `audit_vault.py` after structural changes. Fix errors. Report warnings as
missing information and ask for the value — never invent one to clear a warning.

## Before calling it done

- The verbatim posting is unchanged and its checksum still validates.
- Source, discovery method, compensation, level, contacts, interviews, and next
  action are recorded, with `Unknown` where genuinely unknown.
- External claims retain provenance, metric class, and ownership.
- Personal Information details used are within their audience level for that
  channel; reference consent explicit.
- Artifacts are linked, versioned, and validated.
- The user's `Application Brief.md` was updated, not restructured.
- Updated files and unresolved gaps are summarised for the user.
