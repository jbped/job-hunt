---
name: cover-letter-pdf
description: Render and validate the cover letter PDF for a job application from its Draft - Cover Letter.md working copy. Use whenever the user asks to generate, render, export, or re-render a cover letter PDF, or to produce the final cover letter artifact for a submission.
---

# Generate the cover letter PDF

Read [the core rules](../career-evidence/SKILL.md) first if the career-evidence
skill is not already loaded. The rendering details are in the Rendering section
of [document-generation.md](../career-evidence/references/document-generation.md).

1. The source is the application's `Draft - Cover Letter.md`. If it is missing
   or stale, follow the [`draft-cover-letter`](../draft-cover-letter/SKILL.md)
   workflow first — this skill renders; it does not write copy.
2. Run `render_pdf.py --app <folder> --kind cover-letter` from
   `../career-evidence/scripts/`. The letterhead comes from
   `Personal Information/Contact.md`; only entries whose audience is
   `application` or `public` are printed — `recruiter` details are for
   conversation, never for artifacts. Output is versioned into `Artifacts/`,
   so a submitted artifact is never overwritten.
3. If it reports the content is too long, cut copy in the draft rather than
   forcing extra pages — it refuses rather than clipping because a clipped PDF
   looks correct until someone reads the bottom of it.
4. Look at the proof PNG before calling it done. The automated checks catch
   structural faults, not ugly ones.
