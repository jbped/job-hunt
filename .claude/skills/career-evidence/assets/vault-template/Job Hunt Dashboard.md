---
type: dashboard
tags:
  - job-hunt
---

# Job Hunt Dashboard

## Active applications

![[Applications.base#Active]]

## Next actions due

![[Applications.base#Next actions due]]

## Career evidence

No roles recorded yet. Ask your agent to interview you about your most recent job,
or create a note from [[Templates/Accomplishment]].

- [[Career Evidence.base]]

## Personal information

- [[Personal Information/Contact]]
- [[Personal Information/About Me]]
- [[Personal Information/Education]]
- [[Personal Information/Interview Queue]]

## People

- [[People.base]]

## Working notes

- [[Working Notes/Open Questions]]
- [[Working Notes/Field Reference]]
- [[Start Here]]

## How this vault works

Two ideas carry most of the weight:

**Evidence is separate from applications.** `Career Evidence/` holds what is true
about your career, written once. An application selects from it. A resume never
introduces a claim that is not already in evidence — which is what makes it safe
to generate quickly.

**Facts are separate from interpretation.** In each application folder,
`Application Brief.md` is yours: status, URL, compensation, next action. `Analysis.md`
is the agent's: what the posting wants, how your evidence maps to it, what not to
claim. Rewriting the analysis is always safe; it is derived, not recorded.

## Application workflow

1. `new_application.py "<Company>" "<Role>"` scaffolds the folder.
2. `capture_jd.py` stores the posting verbatim and stamps its checksum.
3. Ask the agent to write `Analysis.md` from the posting and your evidence.
4. Draft `Resume Copy.md` and `Cover Letter.md` from linked evidence only.
5. `render_pdf.py` produces validated PDFs into `Artifacts/`.
6. Record what was sent in `Submission Notes.md` and update the status.

Run `status.py` for the same picture in a terminal, or `serve.py` for the local
dashboard. `audit_vault.py` checks the vault after any structural change.

## Evidence rules

- Role and accomplishment notes are the source of truth.
- Keep exact, estimated, and qualitative impact distinguishable.
- Never invent a metric to satisfy a job description.
- Match a keyword only when the underlying experience supports it.
- Prefer concrete ownership, scale, decisions, and outcomes over generic claims.
