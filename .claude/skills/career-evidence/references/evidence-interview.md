# Evidence interviews

How career evidence gets from memory into notes that survive scrutiny. The
interview is a conversation, not a form — but its output has one shape, so
every role and accomplishment gets the same treatment.

## The seven dimensions

Every question belongs to one dimension. They get conflated in the telling —
"we shipped X and saved $Y" mixes four of them — and untangling later is hard,
so the interview separates them deliberately:

1. **Context** — what was true before; what problem existed and for whom.
2. **Contribution** — what this person actually did, distinct from the team.
3. **Collaboration** — team size, shape, and who owned what.
4. **Decisions** — choices made, alternatives rejected, tradeoffs accepted.
5. **Adoption** — who used it, how many, and what reach claims are honest.
6. **Impact** — outcomes, with each metric's class, source, denominator, and period.
7. **Learning** — setbacks, failed hypotheses, and what changed afterward. The
   best interview material, and the first thing memory discards.

## The Questions section

Open questions live in the note they belong to, under `## Questions`, grouped
by dimension:

```markdown
## Questions

### Ownership and collaboration

- What did "led development" mean: technical lead, primary engineer, or owner?

### Metrics and impact

- What is the denominator and period for "50% of enrollments"?
```

Use the dimension names as `###` headings, merging where natural (Context and
scope; Ownership and collaboration; Decisions and tradeoffs; Adoption and
reach; Metrics and impact; Setbacks and learning; Publication and naming).
Only headings with open questions appear. `Publication and naming` is the
eighth, practical grouping: what may be said publicly — product names, vendor
names, cultural details — is a question about permission, not fact.

`Working Notes/Open Questions.md` stays an index: it links to these sections
rather than restating them.

## Running an interview

1. Read the role note and every linked accomplishment first. Never ask for
   what the vault already records.
2. Pick one note per session. Depth on one accomplishment beats breadth over
   five.
3. Ask in batches of three to five, highest resume leverage first — usually
   Metrics and impact, then Ownership. A long questionnaire gets abandoned.
4. Follow up on every metric until it carries: value, claim class (exact,
   approved-estimate, derived, qualitative, unknown), source or approver,
   denominator, and period. A percentage without its population is not yet
   evidence.
5. Follow up on every ownership word. "Led", "built", and "helped" each get
   one clarifying question: sole, shared evenly, primary with support, or
   supporting?
6. Accept `unknown` immediately and move on. Record it where the fact would
   live — a recorded unknown stops the next draft from guessing.
7. Ask for the failure. Every accomplishment has a setback, a missed
   projection, or a rejected approach; it is the most credible thing in an
   interview answer and it vanishes if not captured now.

## Filing answers

An answered question moves; it is never answered inline:

- The fact goes into the note body under the section where it belongs, or into
  frontmatter (`skills`, `team`, `ownership`).
- Metric provenance is recorded with the metric, not in the question.
- The question is deleted from `## Questions`. A partially answered question is
  rewritten to only what remains open.
- If the answer opens new questions, they are added under their dimension.

When a note's Questions section empties, promote its status: a role interviewed
end-to-end is `documented`; an accomplishment whose metrics all carry
provenance is `verified`. Status describes the evidence, so it changes only
when the evidence does — never to tidy a list.
