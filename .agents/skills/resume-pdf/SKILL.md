---
name: resume-pdf
description: Render and validate the resume PDF for a job application from its Draft - Resume.md working copy. Use whenever the user asks to generate, render, export, or re-render a resume PDF, or to produce the final resume artifact for a submission.
argument-hint: <company or application folder>
---

# Generate the resume PDF

Read [the core rules](../career-evidence/SKILL.md) first if the career-evidence
skill is not already loaded. The rendering details are in the Rendering section
of [document-generation.md](../career-evidence/references/document-generation.md).

1. The source is the application's `Draft - Resume.md`. If it is missing or
   stale, draft it first with `/draft-resume` — this command renders, it does
   not write copy.
2. Run `render_pdf.py --app <folder> --kind resume` from
   `../career-evidence/scripts/`. It measures the content against real font
   metrics, renders through `ps2pdf`, validates the result, and versions the
   output into `Artifacts/` — a submitted artifact is never overwritten.
3. If it reports the content is too long, cut copy in the draft — do not reach
   for `--pages 2` unless a two-page resume is what the user wants. It refuses
   rather than clipping because a clipped PDF looks correct until someone reads
   the bottom of it.
4. Look at the proof PNG before calling it done. The automated checks catch
   structural faults, not ugly ones.
