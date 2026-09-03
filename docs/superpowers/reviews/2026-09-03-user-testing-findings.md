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

## Chrome/Firefox/sandbox status

- Chrome extension: works (finding 1 & 2 aside).
- Firefox extension: not yet reported.
- AI sandbox, webapp walk, zip, PDFs, Obsidian view, live vault: not yet
  reported.
