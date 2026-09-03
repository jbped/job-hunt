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

The layout is single-column by design and stays that way: ATS parsers read
top-to-bottom, and multi-column or graphic-heavy templates are how qualified
resumes get dropped before a human sees them.

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

## Templates

A template is one `.ps` file. Templates come from two places and nowhere else: the built-ins the application ships in `server/assets/templates/PDF/`, and `.ps` files the user puts in their vault's `Resources/Templates/`. Registry names are namespaced — `built-in:Resume - Figma Inspired`, `vault:My Design` — so the two can never collide and a vault template can never shadow a built-in.

Which one an application renders with is `resume_template` / `cover_letter_template` on its `Application Brief.md`, chosen in the dashboard beside the render buttons or set with `render_pdf.py --template <name>` for one render. An unset field means the built-in default, so a vault that has never heard of templates renders exactly as it always has.

A template is never rewritten to make it work. If it does not honour the contract below it is refused, with the missing piece named.

### The prologue contract

Only the *prologue* is used — everything up to a line `brand` followed by a line starting `HB`. Everything after that marker is discarded unread, which is why the shipped templates' own drawing commands never execute: the layout engine emits its own at the density it measured with.

The prologue must:

- carry the three tokens `{{FULL_NAME}}`, `{{POSITION}}`, and `{{COMPANY}}` in its `/DOCINFO pdfmark` metadata block;
- keep the literal `%%Pages: 1` line, which the renderer rewrites for a multi-page document;
- define the fonts `/HB` and `/HR`, the colours `/brand`, `/ink`, and `/muted`, the helper `/Rshow`, and the four contact icons `/phoneIcon`, `/pinIcon`, `/mailIcon`, `/linkedinIcon`;
- end with the marker: a line `brand`, then a line starting `HB`.

Defining `/bodyline`, `/bullet`, `/role`, `/education`, `/section`, or `/contact` is harmless but pointless — the engine redefines all six after the prologue.

### `% ce-kind:`

A vault template declares which document it is for:

```postscript
% ce-kind: resume
```

`resume` or `cover-letter`. A vault template without this line is skipped with a note on stderr rather than guessed at.

### `% ce-param:`

All layout — margins, column positions, section order, sizes, spacing — is computed in Python, not drawn by the template. A template declares the numbers that computation uses:

```postscript
% ce-param: left 54
% ce-param: right 558
% ce-param: section_order summary, skills, experience, education
```

One `key value` per line, anywhere in the prologue. Undeclared keys keep their default, an unknown key is refused with the valid list, and an unusable value is refused rather than rounded to something workable.

Every key, with the default that is also today's rendered output:

| Key | Default | What it sets |
| --- | --- | --- |
| `left` | 38 | Left edge of the text column |
| `right` | 570 | Right edge of the text column |
| `bullet_x` | 50 | Left edge of bullet text |
| `top_rule_y` | 703 | The brand rule under the letterhead |
| `bottom_margin` | 54 | Lowest baseline before the page is full |
| `page_top` | 756 | First baseline on a continuation page, and the wordmark's |
| `body_font` | Helvetica | Body face; must have a metrics table |
| `bold_font` | Helvetica-Bold | Bold face; must have a metrics table |
| `name_size` | 18.5 | Wordmark size |
| `name_second_y` | 735 | Baseline of the wordmark's second line |
| `title_size` | 8.6 | Professional title under the wordmark |
| `title_y` | 718 | Its baseline |
| `contact_size` | 7.8 | Contact column type size |
| `contact_right` | 548 | Right edge the contact column aligns to |
| `contact_icon_x` | 556 | Icon column |
| `contact_icon_drop` | 4 | Icon offset below its text baseline |
| `contact_step` | 14 | Distance between contact lines |
| `rule_width` | 0.9 | Brand rule stroke width |
| `bullet_dot_x` | 43 | Bullet dot centre |
| `bullet_dot_rise` | 2 | Its rise above the baseline |
| `bullet_dot_radius` | 1.15 | Its radius |
| `section_rule_gap` | 8 | Gap between a section label and its rule |
| `section_rule_rise` | 3 | The rule's rise above the baseline |
| `section_rule_width` | 0.35 | Its stroke width |
| `resume_start_drop` | 15 | First resume baseline below the brand rule |
| `letter_start_drop` | 22 | First letter baseline below the brand rule |
| `re_size_offset` | 0.8 | The `RE:` line's size, relative to body |
| `re_gap` | 1.6 | Space after it, in leadings |
| `salutation_gap` | 0.4 | Space after the salutation, in leadings |
| `paragraph_gap` | 0.6 | Space between paragraphs, in leadings |
| `closing_gap` | 0.4 | Space before the sign-off, in leadings |
| `role_size_offset` | 0.7 | Role title size, relative to body |
| `section_size_offset` | 2.5 | Section label size, relative to body |
| `education_size_offset` | -0.1 | Education line size, relative to body |
| `section_order` | summary, experience, additional, education, skills | Which resume sections are drawn, and in what order |

`section_order` takes any ordering of those five identifiers; naming fewer omits the rest. Everything else is a number.

The density ladder itself — the sizes the fitter steps down through when content is tight — stays in Python: it is a fitting strategy, not a design choice, and a template that could disable it could silently produce an unreadable resume.

To change a built-in's visual design, edit the definitions at the top of `server/assets/templates/PDF/*.ps`. Avoid adding fixed-position drawing commands after the marker; hardcoded coordinates are what made the old manual reflow necessary.

## Resume selection

- Identify the top three goals the role is graded on, from the posting's
  what-you-will-do section and the analysis, and select the evidence that
  moves those goals. The impact areas employers buy: revenue, cost reduction,
  process efficiency, customer acquisition and retention, company growth,
  team health, market awareness.
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
