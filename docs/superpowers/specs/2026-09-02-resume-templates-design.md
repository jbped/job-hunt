# Resume templates: registry, picker, and design cloning

Date: 2026-09-02. Status: approved direction, pending spec review.
Parent: `webapp-first-epic`.

## Why

PDFs render from two checked-in PostScript templates. Users want choice:
in-house alternatives, and — since almost no user can author PostScript —
a way to bring the resume they already have and get a template that
matches its design. The feature splits into a deterministic half that
ships now and an AI-assisted half that becomes the sandbox's second
workflow.

Decisions made in brainstorming (user, 2026-09-02):

- Both in-house templates and user-supplied templates are wanted.
- User-supplied means an **ingress point**: upload an existing resume,
  analyze it, generate a PostScript template that reproduces its design.
- That generation runs as an **agent workflow with a preview loop**
  (analyze → candidate template → sample render → iterate), not one-shot.
- Sequencing is **split**: registry + picker first (2a, deterministic,
  ships independently); upload→clone→preview through the webapp after
  the 0.7 sandbox exists (2b).

## Part 2a — Template registry and picker (ships now)

### Registry

Two template sources, one namespace:

- **Built-in:** the checked-in templates under
  `server/assets/templates/PDF/` (today's two, plus any future in-house
  designs), for both kinds (resume, cover letter).
- **User-supplied:** `.ps` files the user places in
  `Resources/Templates/` in their vault. Any file honoring the token
  contract participates; vault templates shadow nothing — names are
  namespaced (`built-in:…` / `vault:…`) so collisions cannot occur.

The token contract (the placeholders a template must carry, per kind)
gets documented in `references/document-generation.md` — it exists today
only implicitly inside the built-in templates and `render_pdf.py`.

### Selection

- New optional field on the Application Brief: `resume_template` and
  `cover_letter_template` (schema vocabulary is dynamic here — values
  come from the registry, not a fixed list; absent field = the current
  default template, so existing vaults behave exactly as today).
- `render_pdf.py` accepts a template argument / reads the brief field,
  resolving through the registry. Unknown name: fail loudly with the
  available names listed.
- Validation: before rendering with a user-supplied template, verify the
  required tokens for the kind are present; a broken template fails at
  submission-artifact quality gates, never silently produces a wrong
  PDF. Existing render validation (page count, fonts embedded) applies
  unchanged.

### Webapp

- The Applications viewer's render controls gain a template picker per
  kind, listing the registry (built-in and vault templates, labeled).
  Selection writes the brief field through the existing field flow.
- `/api/schema` carries the registry (it already carries the form and
  vocabulary data the pickers build from), so the picker needs no new
  endpoint.

### Safety

- Registry resolution never reads outside the two sanctioned dirs; vault
  paths go through the existing path-escape guards.
- PostScript is a full programming language: user-supplied templates
  execute in Ghostscript at render time, on the user's own machine, over
  their own files — same trust position as today's checked-in templates,
  but `docs/setup.md` gains a sentence saying a template from someone
  else should be treated like any file you'd run.
- `test_safety.py`: registry stays inside its dirs; missing-token
  validation refuses to render; unknown template name refuses loudly.

## Part 2b — Design cloning (after the 0.7 sandbox)

The flagship second workflow for the AI sandbox (see
`2026-09-02-ai-sandbox-investigation.md`):

1. User uploads their existing resume PDF in the webapp.
2. The sandboxed agent analyzes its layout and typography and writes a
   candidate `.ps` template honoring the token contract.
3. The server renders a sample PDF from the candidate (deterministic
   path, demo/sample data — never fabricated user facts).
4. The webapp shows the upload and the sample side by side; the user
   iterates through the chat loop until it matches.
5. On accept, the template lands in `Resources/Templates/` and appears
   in the 2a picker.

Boundaries fixed now, details specced after the 0.7 slice ships:

- Only template *authoring* is AI-assisted; rendering stays
  deterministic. The agent writes templates, never PDFs, and never
  touches evidence notes in this workflow.
- The uploaded resume is design reference only — its *content* is not
  ingested as evidence (importing facts from an old resume would violate
  the evidence rules; if wanted someday, that is its own feature).
- The candidate template passes 2a's token validation before it can be
  previewed or saved.

## Non-goals

- No HTML/CSS or other new template formats; PostScript remains the one
  render path (stdlib + Ghostscript unchanged).
- No template marketplace/sharing mechanism.
- No content import from uploaded resumes.
- 2b ships nothing until the 0.7 evidence-interview slice proves the
  sandbox loop.

## Verification (2a)

- `test_safety.py` passes with the new registry/validation tests.
- A vault template appears in the picker, renders via the brief field,
  and survives the existing PDF validation.
- A template missing a required token is refused with a clear error.
- A vault without `Resources/Templates/` and briefs without the new
  fields behave exactly as today.
