# User testing findings — 2026-09-03

Status: **collecting**. These are Jacob's raw findings from the epic test
pass. Nothing here is started, prioritized, or specced — the list gets
reviewed together first, then items graduate to specs/plans.

## 1. Extension: captured metadata is drastically limited

Chrome capture works end to end, but the metadata that comes out is thin.
Explore whether the extension can prompt/extract more from the page at
capture time (fields worth considering at review: title, location, comp
range, work model, posted date, req id, source URL context — TBD with
Jacob). Constraint to respect: `Job Description.md` stays verbatim
checksummed evidence; richer metadata belongs in the Analysis/Brief
fields, not in the capture body.

## 2. Extension: no pairing check on open

Reproduced UX failure: submitting a capture while unpaired redirects and
only then reports "not paired". The extension popup should verify on open
that it can reach a job-hunt instance and that it is paired, and show
state + a pair action up front — before any capture is attempted.

## 3. Webapp: settings menu

Add a settings surface to the UI. "Pair extension" should live there,
not as its own header button. (Other future settings candidates land
here as they appear.)

## 4. Webapp: UI iteration

Jacob's impression: the React port reads as the old page with new things
bolted on, not a rethought UI. Context for the review discussion: 0.6
was scoped parity-first by the spec ("feature parity with the current
page, same visual design"), with redesign deferred to feature work — so
the sameness is by design, and the two new panels + chat view were added
in the old visual language. The deferred redesign is now due: plan a
deliberate UI iteration pass (information architecture, header/nav
cleanup, visual design), reviewed as its own initiative.

## 5. Firefox extension is missing

There is no Firefox build of the extension. Needs to exist (packaging
and any API differences from the Chrome build to be scoped at review).

## 6. Obsidian ↔ webapp piping works; in-app editing is clunky

Positive: edits made in Obsidian show up immediately in the webapp, and
webapp edits land in the vault — the fingerprint/poll buffer system is
doing its job. Negative: editing inside the webapp is clunky as a user.
Enhancement idea: a WYSIWYG-to-markdown editing experience (must keep
markdown as the stored truth and the fingerprint contract intact).

## 7. Company questions: no editing after entry in the UI

The panel supports entry at submission time, but answers/questions can't
be edited afterwards within the UI — editing works via Obsidian (and
reflects immediately). Review: whether the intended "Edit in note"
affordance is missing, hidden, or insufficient, and what in-panel editing
should look like.

## 8. Fundamental flow gap: no "what next / where am I working" layer

The biggest finding. The UI presents applications and notes well, but has
no top-level action flow: this is an application, this is where it
stands, this is the next action — the kanban-board-style stance and a
"what do we do next" entry point are absent as a first-class experience.
This is a data/flow-structure question, not a styling one, and needs
ideation with Jacob before any UI iteration (finding 4) is designed —
the UI iteration should be built around whatever this produces.

## Status

- Chrome extension: works (findings 1 & 2).
- Firefox extension: missing (finding 5).
- Obsidian ↔ webapp round-trip: works (finding 6).
- Company questions: entry works, post-entry edit gap (finding 7).
- AI sandbox, zip, PDFs, live vault: not yet reported.
