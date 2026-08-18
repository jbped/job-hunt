---
name: new-application
description: Start tracking a new job application in the job-hunt vault — scaffold the folder, capture the posting verbatim, and write the analysis. Use whenever the user has found a job posting, wants to apply somewhere, pastes a posting for a role they are considering, or asks to add, track, or analyse a job or application.
---

# New application

Read [the core rules](../career-evidence/SKILL.md) first if the career-evidence
skill is not already loaded — it defines how the vault is found, who owns which
note, and the truth and privacy rules. Scripts live in
`../career-evidence/scripts/` and locate the vault themselves.

1. `new_application.py "<Company>" "<Role>"` — scaffolds the folder and Artifacts/.
2. `capture_jd.py --app <folder>` — stores the posting verbatim and stamps
   `verbatim_sha256`. Capture before analysing, so the analysis cannot quietly
   reshape the source.
3. Write `Analysis.md`, insight first: a three-sentence TL;DR, a compatibility
   confidence verdict with its drivers, and the synthesised level with
   reasoning. Do not restate the posting — it sits verbatim one file away.
4. Classify every material job term as directly supported, adjacent or partial,
   or unsupported, each with the evidence note that backs the verdict. The
   unsupported list is the most useful thing in the note.
5. Record compensation components exactly and identify their source. Never guess.
6. Keep contacts, referrals, and interviews in their own notes. Create person
   notes with the [`new-person`](../new-person/SKILL.md) workflow.
7. Keep `next_action` and `next_action_date` current while the application lives.

What the fields mean — status flow, discovery, compensation, level synthesis —
is in [application-tracking.md](../career-evidence/references/application-tracking.md).
Accepted values live in `scripts/schema.py`, mirrored into the vault's
`Working Notes/Field Reference.md`; use a listed value or add one deliberately.
