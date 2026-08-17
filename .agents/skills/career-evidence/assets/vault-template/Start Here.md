---
type: onboarding
tags:
  - job-hunt
---

# Start Here

This vault keeps the evidence behind your job search in plain markdown, so an AI
agent can write accurate resumes and cover letters from it — and so you can read,
edit, and trust every file yourself without any tool in the loop.

## The two ideas worth knowing

**Evidence is separate from applications.** `Career Evidence/` holds what is true
about your career, written once and reused. An application selects from it. A
resume never introduces a claim that is not already in evidence — that is what
makes generating one quickly a safe thing to do.

**Facts are separate from interpretation.** Inside each application folder,
`Application Brief.md` is yours: status, URL, compensation, next action.
`Analysis.md` is the agent's: what the posting wants, how your evidence maps to
it, what not to claim. Rewriting the analysis is always safe. Overwriting your
brief is not, so the agent leaves it alone.

## The folders

| Folder | Holds |
| --- | --- |
| `Career Evidence/Roles` | One note per job you have held |
| `Career Evidence/Accomplishments` | One note per thing you did that is worth citing |
| `Applications/` | One folder per application: posting, analysis, artifacts |
| `People/` | One note per person: contacts, referrals, references |
| `Personal Information/` | Contact details and audiences, education, self-knowledge |
| `Resources/` | Source documents: old resumes, diplomas, certificates |
| `Working Notes/` | Scratch, open questions, field vocabulary |

A referral is not a reference. Someone who forwards your resume is a contact;
someone who agreed to vouch for you when asked is a reference. Both live on the
same person note in `People/`, as separate relationships — and reference consent
is recorded explicitly.

## First three things to do

1. **Fill in `Personal Information/Contact.md`.** Contact details go on cover
   letters, so the frontmatter there is the letterhead; each entry carries an
   audience level, and `self` entries never leave the vault. Drop an old resume
   or diploma into `Resources/` and the agent can populate the rest —
   `Personal Information/About Me.md` and `Education.md` — from it. `Unknown` is
   a legitimate answer to anything you have not decided.

2. **Write one role note and one accomplishment.** Ask your agent to interview
   you — it is much faster than filling in a template, and the questions it asks
   about ownership and metrics are the ones that matter later. Start with your
   most recent job and the accomplishment you are proudest of.

3. **Create your first application.** Then ask the agent to analyse the posting
   against your evidence. It will tell you what you can claim, what is adjacent,
   and what you cannot support — that last list is the useful one.

The fastest way to begin is to open your agent in this folder and say
**"set up my job hunt vault"**.

## Rules the agent follows

These exist so the vault stays trustworthy under pressure, when you want a resume
finished and the temptation is to round a number up.

- A job posting is stored verbatim and checksummed. It is evidence, not a draft.
- Exact numbers, approved estimates, derived figures, and qualitative feedback
  stay distinguishable from each other.
- Nothing external claims more ownership than the evidence records.
- No metric is invented to satisfy a job description.
- A submitted artifact is never overwritten; a revision is a new version.
- No passwords, tokens, or confidential customer data enter the vault.

## Commands

Run these from anywhere inside the vault. All are optional — every one of them
has a hand-editable equivalent, and the vault works fine if you never run any.

```text
new_application.py "Company" "Role"   scaffold an application folder
capture_jd.py --app <folder>          store a posting verbatim + checksum
render_pdf.py --app <folder>          build and validate a resume PDF
status.py                             where am I, what's coming up, what's due
serve.py                              the same, as a local web dashboard
audit_vault.py                        check the vault's structure and evidence
```
