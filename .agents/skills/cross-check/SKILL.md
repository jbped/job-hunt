---
name: cross-check
description: Validate a drafted resume and cover letter as a pair against the captured posting, the analysis, and the evidence notes before rendering, through five check families and a four-persona review panel (writer, recruiter, hiring manager, coach). Use whenever the user wants drafts checked, reviewed, validated, or audited, and as the final gate after both drafts exist and before the PDF workflows. Reports findings; never edits a draft.
---

# Cross-check the drafts

Read [the core rules](../career-evidence/SKILL.md) first if the career-evidence
skill is not already loaded. Then read
[writing-standards.md](../career-evidence/references/writing-standards.md) and
[document-generation.md](../career-evidence/references/document-generation.md)
— this pass enforces them; it does not replace reading them.

This is a validation pass, not an editing pass. It reads
`Draft - Resume.md` and `Draft - Cover Letter.md` as a pair and checks them
against `Job Description.md` (the verbatim capture), `Analysis.md`
(fit-by-term), and the evidence notes. It never changes a draft: fixes go
back through the [`draft-resume`](../draft-resume/SKILL.md) and
[`draft-cover-letter`](../draft-cover-letter/SKILL.md) workflows, where the
evidence and read-aloud rules still apply.

## The five check families

Work through all five, even when the first one finds problems. Tag every
finding as a **blocker** (do not render until resolved), a **warning**
(defensible but worth a decision), or a **note** (observation, no action
required).

1. **Keyword coverage and unsupported terms.** List the posting's material
   terms from the verbatim capture and the analysis. Flag terms absent from
   both documents that the evidence could support (coverage gaps), and terms
   present in either document with no Skill Matrix evidence behind them
   (unsupported claims — always blockers).
2. **Redundancy.** Flag cover-letter paragraphs that restate resume bullets
   instead of adding reasoning the resume cannot carry. The letter earns its
   page by explaining fit, equivalence, and motivation, not by repeating.
3. **Claim tracing.** For every metric and ownership word in either document,
   trace back to its evidence note. A metric that upgraded its class (an
   estimate presented as exact, a percentage that lost its denominator) or an
   ownership word that inflated (shared work reading as sole) is a blocker.
4. **Voice and banned patterns.** Check both documents against
   writing-standards.md: banned openings and closers, template praise, keyword
   stuffing, and the em-dash ban in employer-facing copy.
5. **Cross-document contradictions.** Compare the two documents to each other:
   dates, titles, tenure, metrics, and framing must agree. The letter may say
   less than the resume; it must never say something different.

## The review panel

After the five families, review the pair through four personas. Run them as
parallel subagents when the host supports delegation; otherwise make four
separate passes, one lens at a time — the value is in the distinct
perspectives, so never blend them into a single read.

- **Resume and cover letter pro.** Craft: does every bullet pass the result
  test, does the summary work as a 60-100 word pitch, do both documents
  follow writing-standards.md to the letter. Would a professional writer put
  their name on these.
- **Recruiter.** The skim and the search: give the pair ten seconds, then
  time how fast each posting requirement can be found. Flag buried
  differentiators, language that does not match the posting's own terms, and
  anything an ATS parse would mangle.
- **Hiring manager.** Credibility and impact: reading only what is on the
  page, would they book the interview. Flag bullets that state duties instead
  of results, claims that would crumble under one probing question, and the
  strongest evidence when it is not doing the deciding.
- **Coach.** The one lens pointing the other way: where is the candidate
  underselling. Flag verified evidence stronger than the draft's phrasing,
  vault accomplishments that outmatch what was selected, and hedges where the
  evidence supports confidence. The coach argues for the candidate, but only
  from evidence.

Panel findings use the same blocker/warning/note tags, attributed to their
persona, and land in the same dated section as the family findings.

## Recording the findings

Append the findings to `Analysis.md` as a dated section — it is the agent's
synthesis note, so passes accumulate there as history:

```markdown
## Draft review - YYYY-MM-DD

- **Blocker** (claim tracing): ...
- **Warning** (recruiter): ...
- **Note** (coach): ...
```

Summarise the findings for the user, blockers first. When there are no
blockers, say so plainly and point to the
[`resume-pdf`](../resume-pdf/SKILL.md) and
[`cover-letter-pdf`](../cover-letter-pdf/SKILL.md) workflows as the next
step. Never fix a finding silently, and never soften one: an unsupported
claim is reported as unsupported, not reworded until it sounds supported.
