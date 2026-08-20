---
name: draft-resume
description: Tailor a resume draft for a specific application from the verified evidence in the job-hunt vault. Use whenever the user wants to write, tailor, rework, or update a resume or CV for a role. This produces the markdown working copy; the resume-pdf skill renders it afterwards.
---

# Draft a resume

Read [the core rules](../career-evidence/SKILL.md) first if the career-evidence
skill is not already loaded — it defines how the vault is found, the truth and
privacy rules, and who owns which note. Then read
[document-generation.md](../career-evidence/references/document-generation.md)
for the source order, selection rules, and the source format `render_pdf.py`
expects, and the resume sections of
[writing-standards.md](../career-evidence/references/writing-standards.md) —
they are the content rules, not suggestions.

1. Read the sources in the order document-generation.md lists them.
2. Select evidence by its Resume selection rules. Selection is the tailoring.
3. Draft into `Draft - Resume.md` in the source format: header copied verbatim
   from `Contact.md`, then summary, bullets, and skills line per
   writing-standards.md.
4. Fill `## Evidence used` and `## Claims excluded` with why — the exclusions
   are what make the next tailoring pass fast.

When the draft is settled, run the [`cross-check`](../cross-check/SKILL.md)
pass over the resume and letter as a pair, then render and validate with the
[`resume-pdf`](../resume-pdf/SKILL.md) workflow.
