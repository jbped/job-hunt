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
`Job Hunt Dashboard.md` and `Career Evidence/`. That is `VAULT_ROOT`.

The vault is deliberately outside this repo — it is personal data, and the repo
is shareable tooling. If neither the `.env` nor the upward search finds a vault,
ask before creating one; never silently make a second vault.

Scripts live in this skill's `scripts/` and resolve the vault the same way, so
they work from any directory. `--vault PATH` overrides. Stdlib-only Python 3.

```text
init_vault.py <path>              create an empty vault
new_application.py "Co" "Role"    scaffold an application folder
capture_jd.py --app <folder>      store a posting verbatim + checksum
render_pdf.py --app <folder>      build and validate a PDF
status.py                         where am I / coming up / to do
serve.py                          the same as a local web dashboard
export_index.py                   rebuild .cache/vault-index.json
audit_vault.py                    check structure, vocabulary, evidence
```

Prefer these over doing the same work by hand: they produce identical results
every time, and `audit_vault.py` is written against what they produce.

## Who owns which note

This split is the thing to get right. Inside an application folder:

- **`Application Brief.md` is the user's.** Status, URL, compensation, dates,
  next action. Update a field when asked; do not restructure it, reorder it, or
  move their prose into a shape you prefer. Someone reads this file by hand.
- **`Analysis.md` is yours.** Position breakdown, evidence alignment, resume and
  cover-letter strategy, claims to verify. Rewrite it freely — it is derived, and
  regenerating it costs nothing.
- **`Job Description.md` is neither.** It is evidence, checksummed. Never edit a
  captured posting; a changed posting is a new dated capture.

The same idea holds vault-wide: `Career Evidence/` records what happened,
everything else interprets it.

## Read further when the task calls for it

- [vault-schema.md](references/vault-schema.md) — creating, moving, or
  reorganising notes; frontmatter shapes.
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

## First-time setup

If `Personal Information/Contact.md` is missing or still has empty contact
fields, the user is starting out. Offer to walk them through it rather than
filling forms silently.

1. Run `init_vault.py <path>` if there is no vault yet.
2. Ask for an existing resume, diploma, or certificate to drop into `Resources/`
   — source documents there are the fastest way to seed the vault, and
   provenance lines can point back at them.
3. Fill `Personal Information/` — `Contact.md` (contact details with per-entry
   audience levels; the frontmatter is the cover-letter letterhead),
   `About Me.md` (target roles, work model, compensation thinking), and
   `Education.md`. `unknown` is a fine answer and better than a guess.
4. Capture one role and its strongest accomplishment by interview (below). One
   good accomplishment note is worth more than five thin ones, and it shows the
   user what the vault is for.
5. Create their first application and analyse it against that evidence.

Ask in small batches. A long questionnaire gets abandoned.

## Capture career evidence

1. Read the role note and any linked accomplishments first.
2. Separate context, contribution, collaboration, decisions, adoption, impact,
   and learning — these get conflated, and untangling them later is hard.
3. Ask a small batch of high-value questions. Accept `unknown`.
4. Record each metric's type and source, including the denominator and period.
   A percentage without its population is incomplete evidence.
5. Record ownership precisely: sole, shared, supporting, team size, cross-team.
6. Preserve limitations, failed hypotheses, and setbacks. They are the best
   interview material and they vanish if not written down early.
7. Update one canonical accomplishment note; link it from the role.
8. Index anything still unresolved in `Working Notes/Open Questions.md`.

## Create or update an application

1. `new_application.py "<Company>" "<Role>"` — scaffolds the folder and Artifacts/.
2. `capture_jd.py` — stores the posting verbatim and stamps `verbatim_sha256`.
   Capture before analysing, so the analysis cannot quietly reshape the source.
3. Write `Analysis.md`: TL;DR, outcomes, responsibilities, technologies,
   collaboration model, logistics, and synthesised level with reasoning.
4. Classify every job term as directly supported, adjacent or partial, or
   unsupported. The unsupported list is the most useful thing in the note.
5. Record compensation components exactly and identify their source. Never guess.
6. Keep contacts, referrals, and interviews in their own notes.
7. Keep `next_action` and `next_action_date` current while the application lives.

## Tailor a resume

1. Read the posting, the analysis, the Personal Information notes, and the evidence.
2. Rank evidence by relevance, strength, recency, ownership, and metric quality.
3. Select a focused subset. Cramming every accomplishment in weakens all of them.
4. Draft into `Resume Copy.md` with conventional headings and official titles.
5. Preserve supported technologies, tenure, metric language, and ownership.
6. `render_pdf.py --kind resume` renders and validates. If it reports the content
   is too long, cut copy — do not reach for `--pages 2` unless a two-page resume
   is what the user wants.
7. Look at the proof image before calling it done.

## Draft a cover letter

1. Read the posting, analysis, referral status, and the selected evidence.
2. Write it as a letter in `Cover Letter.md`; the letterhead comes from
   `Personal Information/Contact.md`, filtered by audience.
3. Open with the role and a credible fit statement. State a verified formal
   referral when there is one, phrased exactly as the evidence supports.
4. Connect two or three evidence-backed narratives to the employer's stated needs,
   and say why each matters to them.
5. Add reasoning that is not already obvious from the resume bullets.
6. Explain equivalent experience directly rather than claiming the technology.
7. `render_pdf.py --kind cover-letter`, then check the proof.

## Track contacts, interviews, and references

- Record a person's organisation, title, role in this application, relationship,
  contact details, preferred method, referral status, last contact, and next
  follow-up. Never imply an endorsement beyond what the user confirmed.
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
