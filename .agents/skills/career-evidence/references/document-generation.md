# Resume and cover-letter generation

## Source order

1. The exact job description
2. `Analysis.md` — the position breakdown and evidence alignment
3. Canonical role and accomplishment notes
4. `Personal Information/` — `Contact.md` (respecting each entry's audience
   level), `About Me.md`, and `Education.md`
5. Contacts and referral status

Never treat a previously generated artifact as proof of a claim. If an old resume
and the evidence notes disagree, the evidence notes win and the old resume is the
thing to investigate — that disagreement is usually where an inflated claim first
crept in.

## Working copies

- Draft into `Draft - Resume.md` and `Draft - Cover Letter.md` in the application folder.
- Link the evidence used, and record what was excluded and why. The exclusions
  are what make the next tailoring pass fast.
- Once a version is submitted, it is history. Revisions become new versions.

## Validation before rendering

Each draft workflow carries its own pass (the resume's keyword pass, the
cover letter's read-aloud voice pass). Once both drafts exist, the
`cross-check` workflow skill is the unified final gate: it checks the pair
against the posting, the analysis, and the evidence — coverage, redundancy,
claim tracing, voice, and cross-document contradictions — and appends its
findings to `Analysis.md` as a dated Draft review section. It reports; it
never edits a draft.

## Rendering

`render_pdf.py --app <folder> --kind resume|cover-letter` reads the markdown,
measures every line against the real font metrics, computes wrapping and vertical
positions, renders through `ps2pdf`, and validates the result. Output is versioned
into `Artifacts/`.

It checks page count, font embedding, text extraction, column overflow, title/date
collisions, and unreplaced placeholders. If content does not fit, it reports how
many lines are over and refuses rather than clipping — a clipped PDF looks correct
until someone reads the bottom of it. Cut copy; reach for `--pages 2` only when a
two-page document is intended.

It also writes a proof PNG. Look at it. The automated checks catch structural
faults, not ugly ones.

### Source format

The resume working copy needs `## Header`, `## Summary`, and `## Experience`
with `### Title | Company | Dates` headings and `-` bullets.
`## Additional Experience`, `## Education`, and `## Technical Skills` are
optional; when present, Technical Skills is a single `·`-separated line.

The header's three lines come verbatim from `Personal Information/Contact.md`:
`full_name`, the recorded current resume title, then a `·`-separated contact
line of the `application` and `public` entries in their frontmatter order.
Never retype them from memory or copy them from an earlier draft — that is how
one application says `Jake, Lehi, Utah` and the next says `Jacob, Lehi, UT`.

A cover letter is written as a letter — date, recipient block, salutation,
paragraphs, sign-off. Everything above its first `## ` heading is rendered, and the
letterhead comes from `Personal Information/Contact.md`, so contact details live
in one place; only entries whose audience is `application` or `public` are
printed — `recruiter` details are for conversation, never for artifacts.

To change the visual design, edit the definitions at the top of
the skill's `assets/templates/PDF/*.ps`. Avoid adding fixed-position drawing commands after them;
hardcoded coordinates are what made the old manual reflow necessary.

## Resume selection

- Rank evidence by relevance, strength, recency, ownership, and metric quality.
- Prefer a focused one-page resume; use two when strong relevant evidence would
  otherwise become unreadable.
- Do not satisfy a keyword with an unsupported technology or inflated tenure.
- Selection is the tailoring. Including everything is the same as choosing nothing.
- Over a page? Cut in this order: bullets from the oldest role, then
  Additional Experience detail, then the tail of the skills line. Recent-role
  accomplishment bullets go last. Never pad in the other direction to fill a
  short page.

## Cover-letter selection

- Two or three verified narratives, not prose that restates the resume.
- State formal referrals accurately, and name contacts only when verified.
- Explain equivalent experience directly when the posting allows it, rather than
  implying the technology the employer asked for.
- Ground motivation in the captured posting or verified research — not in praise
  that could apply to any company.
