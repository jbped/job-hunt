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

## High-leverage data points

Field-tested question targets, in rough order of value per question. The
baseline applies to any profession; career-specific addenda follow it. When
interviewing someone in a field without an addendum, translate the baseline
into their vocabulary rather than skipping it.

### Baseline (any career)

- **The mechanism.** "What was hard here, and how did you actually do it?"
  Resume bullets need impact; cover letters and interviews need mechanism. A
  claim with no story under it ("improved efficiency", "reduced errors") dies
  at the first follow-up question. Chase the method, the constraint, and the
  workaround until a stranger could explain why the work was difficult.
- **The approach rationale.** Why this method or tool, and what the rejected
  alternative couldn't do. "Switched from X to Y" is a fact; "Y because X
  couldn't do Z" is evidence of judgment.
- **The origin incident.** What event caused this work to exist — a failure,
  a complaint, a lost contract, a near-miss. Origin incidents causally link
  accomplishment notes to each other, and the chain (incident → response →
  lasting change) is often stronger evidence than any single note in it.
- **Negative-space ownership.** Not just "what did you own" but "who else
  touched this" — the adjacent work by a teammate or another team. Recording
  what the person did *not* do is the only reliable guard against accidental
  claiming later.
- **Seniority signals.** Crises owned and written up afterward, mentoring,
  responsibility for others' work, artifacts or practices adopted beyond the
  person's own team, decisions defended and won. These rarely surface from
  "what did you do" questions and are the difference between mid-level and
  senior on paper — ask for them as their own pass across all roles.
- **Timeline anchors.** Delivery dates and external deadlines ("before the
  busy season", "before the audit") — they turn a duty list into a story with
  stakes.
- **Adoption reality, including failures.** Who used or followed the work,
  who didn't, and why. A note that records poor uptake honestly is both
  credible and a causal link to whatever came next.
- **Familiarity versus authorship.** For every tool or system in a skills
  list: did the person create with it, configure it, or only operate it?
  A skill word that spans all three is a claim waiting to collapse in an
  interview.
- **Exact names, read back.** Spoken interviews mis-capture similar-sounding
  tools, certifications, and methods. Read the name back before it lands in
  frontmatter; a wrong name propagates to the Skill Matrix and then to a
  resume.
- **Domain vocabulary.** Org-specific terms (role names, team types, internal
  product names) get defined once, canonically, in the role note — every
  accomplishment then relies on that definition instead of re-explaining or
  misusing it.
- **Awards and recognition.** Formal awards, honors, internal certifications,
  employee-of-the-period recognition, public shout-outs from leadership.
  People rarely volunteer these — ask directly. Recognition is verification
  someone else already performed, and it earns resume space that a self-claim
  never could.
- **Deliberate ambiguity.** Sometimes the user wants a detail left vague
  (a root cause, a colleague's mistake). Record that the vagueness is
  intentional, so a later session doesn't chase it as a gap.

### Software engineering addendum

- Mechanism means architecture: the data model, the constraint the design
  worked around, the part a new developer would need explained. "Optimized
  expensive queries" is not yet evidence; "collapsed N per-record lookups
  into one join" is.
- Approach rationale usually means stack rationale — why this framework or
  library, and what the previous one's model couldn't support.
- Seniority signals to ask for by name: production incidents owned and
  postmortems written, on-call service, code-review responsibility, tooling
  or libraries published beyond the team, migrations led.
- Familiarity versus authorship shows up sharpest in infrastructure: using a
  CI pipeline daily is not authoring one; deploying to a platform is not
  administering it.
- Name read-backs matter most for lookalike technologies (NGINX / NgRx /
  NGXS, Java / JavaScript) and for internal tools whose public names need a
  publication-boundary check.

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
