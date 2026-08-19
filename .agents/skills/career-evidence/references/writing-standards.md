# Application writing standards

## Evidence quality

Use these claim classes:

- **Exact:** confirmed number or contractual amount. State directly.
- **Approved estimate:** calculated or approved by a credible business owner. Use `estimated`, `approximately`, or equivalent.
- **Derived:** calculated from confirmed inputs. Preserve the derivation in the evidence note.
- **Qualitative:** user feedback or observed benefit without measurement. Do not convert it into a number or causal performance claim.
- **Unknown:** omit externally or ask the user when material.

Record the denominator and period for percentages. A percentage without its population or timeframe is incomplete evidence.

## Punctuation

**NO EM DASHES** in employer-facing copy — none in resumes, cover letters, or
any rendered artifact. Where one is tempting, restructure: a separate sentence,
a comma, a colon, or parentheses. Hyphens and en dashes remain fine for date
and number ranges (`Aug 2025–Aug 2026`, `70–80 agents`). This is a user
directive, not a style preference to weigh.

## Resume summary

Every resume gets a 3-4 sentence `Summary`, structured as: who you are (title
and years), what you do professionally, who or what you support with that
expertise, and optionally one standout highlight. First person is fine and
reads warmer than third. Never an objective statement — the application already
says what role is sought. Ban filler self-praise (`results-oriented`,
`hardworking`, `proven track record`); every adjective should reveal working
style, and every noun should be an evidence-backed keyword.

## Resume bullets

Prefer this flexible structure:

```text
Action and ownership + product or technical scope + verified result + relevant mechanism
```

Do not force every bullet into the same order. Put the strongest differentiator first.

Keep bullets independently understandable. Avoid pronouns, dense feature inventories, internal acronyms without context, and claims such as `significantly improved` without supporting evidence.

Discipline per role: 5-7 bullets for recent relevant roles, each 1-2 rendered
lines, the majority accomplishments rather than duties. Older or less relevant
roles get fewer bullets, a single line, or a bare listing with no bullets —
dropping a role entirely is fine unless it creates an unexplained gap.

Vary the opening verbs — a column of `Led… Led… Built… Built…` reads as
padding. Choose the verb by ownership class first, then for variety. The bank
below is profession-neutral; pull equivalents from the user's own field when
their vocabulary is stronger:

- Sole or primary: led, owned, designed, established, founded, directed,
  overhauled, authored
- Meaningful hands-on within a team: built, developed, implemented, created,
  produced, standardized, modernized, launched
- Shared: co-led, delivered (with team size), collaborated, coordinated
- Supporting: contributed, supported, assisted
- Analysis and discovery: diagnosed, identified, investigated, evaluated,
  audited, researched
- People and communication: mentored, trained, coached, negotiated, presented,
  recruited, facilitated
- Outcomes: reduced, increased, eliminated, consolidated, streamlined, saved,
  grew

Software-engineering additions: architected, engineered, automated, migrated,
optimized, refactored, instrumented, shipped.

Never let a stronger verb upgrade the ownership class — verb variety is
presentation, attribution is evidence.

Include awards, honors, and formal recognition when the evidence notes record
them; they are verification someone else already did. Omit references and the
phrase `References available upon request` — references are provided when
asked, per their own consent records. Hobbies earn space only when distinctive
and approved in `About Me.md`.

## ATS readability

- Use conventional section names such as `Summary`, `Experience`, `Education`, and `Technical Skills`.
- Use official job titles unless a parenthetical clarification is necessary and accurate.
- Include exact technology and domain terms naturally when supported.
- Prefer normal bullets and chronological role structure.
- Avoid keyword stuffing, hidden text, fabricated synonyms, and skill lists unsupported by evidence.
- Keep essential information in text rather than relying only on icons or visual grouping.
- Tailor selection and emphasis per application; do not maintain one supposedly universal resume.
- Hard skills carry the resume; soft skills are subjective and get at most one
  or two words in the Summary — their real home is the cover letter, where an
  example can back them.
- Name tools and technologies exactly (`Angular`, `Snowflake`) — recruiters
  search keywords, not descriptions like `modern frontend frameworks`.
- Final keyword pass: before rendering, re-read the posting's material terms
  against `Analysis.md`'s fit-by-term classification. Every directly supported
  term the draft omits is a finding; every unsupported term the draft contains
  is a defect.

## Cover letters

A cover letter is a clear, honest conversation with the hiring manager: here
is your problem, here is my evidence I can help with it. Its job is motivating
them to read the resume, not restating it. One page, three to five paragraphs,
skimmable — a recruiter may give it seconds. Clarity beats cleverness.

**Voice: plainspoken and direct** (user directive). Short sentences, concrete
verbs, no ceremony. Read the draft aloud before calling it done: any sentence
that would sound stiff spoken across a table gets rewritten in words the user
would actually say.

**Aim at their pain points.** The top tasks in the posting's "what you'll do"
section are the problems the team actually has. Choose the two or three
evidence-backed stories that speak to those problems, frame each as a short
story (situation, what the user did, why it mattered to them), and prefer the
posting's own vocabulary where the evidence supports the term — that is
speaking their dialect, not keyword stuffing.

**Context over inventory.** The resume carries the numbers. The letter keeps
at most one or two, chosen because they land, with the story around them. A
paragraph that stacks metrics is a resume restated; cut it or narrate one.

**Structure that works:** an opener that says who the user is and why this
role, in one credible statement rather than a boilerplate announcement; the
two or three matched stories; one "why this company" grounded in something
verified and genuinely resonant (having used and liked the product is gold; a
value or initiative confirmed from their own material works too); a short,
confident close with a plain ask.

Banned patterns — the tics that make a letter read machine-written:

- Template openings (`I am writing to express my interest in...`, `I am
  applying for the [title] position...`) and stock closers (`I would welcome
  the opportunity to discuss how...`).
- Self-narrating topic sentences (`Reliability is the thread through my
  work`, `I want to be direct about one thing`). Just make the point.
- Uniform paragraph shape. Vary length and density; one short paragraph that
  makes a single point is a feature.
- Generic praise (`Your company is a leader in the industry`) and unverified
  claims about the company.

Handle a stated requirement the user lacks honestly and as trajectory: name
the gap plainly, then the nearest verified equivalent and how the user has
crossed comparable gaps before. Meeting well over half the must-haves is a
reason to apply, not to apologize; showing an understanding of the job counts
for more than a checklist match.

- State a verified referral early, phrased exactly as the evidence supports.
- Add reasoning or narrative not already obvious from the resume.
- Address a verified named contact when one is recorded; otherwise a role
  address (`Dear Hiring Team`, `Dear Head of Engineering`). Never guess a name,
  and never `To Whom It May Concern` — warm and specific beats robotic-formal.
- Include the posting's reference number when the capture records one.
- Voice never loosens evidence: every claim keeps its class and attribution.

## Attribution

- `Built` is acceptable for meaningful hands-on delivery within a team when the sentence does not imply sole ownership.
- Use `led`, `owned`, or `independently` only when the evidence supports it.
- Use `co-led`, `shared delivery`, or explicit team size when collaboration is a differentiator.
- Do not hide a supporting contribution behind language that implies primary ownership.

## Privacy and publication

- Respect public-name constraints recorded in evidence notes.
- Do not store secrets, customer data, private source code, or confidential operational details.
- Generalize sensitive incidents while retaining the engineering decision and outcome.

