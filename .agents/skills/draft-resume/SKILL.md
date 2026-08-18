---
name: draft-resume
description: Tailor a resume draft for a specific application from the verified evidence in the job-hunt vault. Use whenever the user wants to write, tailor, rework, or update a resume or CV for a role. This produces the markdown working copy; rendering the PDF afterwards is /resume-pdf.
argument-hint: <company or application folder>
---

# Draft a resume

Read [the core rules](../career-evidence/SKILL.md) first if the career-evidence
skill is not already loaded — it defines how the vault is found, the truth and
privacy rules, and who owns which note. Then read
[document-generation.md](../career-evidence/references/document-generation.md)
for the source order, selection rules, and the source format `render_pdf.py`
expects, and [writing-standards.md](../career-evidence/references/writing-standards.md)
for any copy that will reach an employer.

1. Read the posting, the analysis, the Personal Information notes, and the
   evidence. Never treat an old resume as proof of a claim — when it disagrees
   with the evidence notes, the evidence wins and the old resume is the thing
   to investigate.
2. Rank evidence by relevance, strength, recency, ownership, and metric quality.
3. Select a focused subset. Cramming every accomplishment in weakens all of
   them — selection is the tailoring.
4. Draft into `Draft - Resume.md` with conventional headings and official
   titles, in the source format from document-generation.md.
5. Preserve supported technologies, tenure, metric language, and ownership. A
   skill absent from the vault's Skill Matrix has no evidence behind it and
   does not belong on the resume.
6. Link the evidence used and record what was excluded and why — the exclusions
   are what make the next tailoring pass fast.

When the draft is settled, render and validate it with `/resume-pdf`.
