# PDF generation

Use `render_pdf.py`. It reads the markdown working copy, measures every line
against the real font metrics, computes the wrapping and vertical positions, then
renders and validates the result:

```text
python render_pdf.py --app "Applications/<Company>/<Role>" --kind resume
python render_pdf.py --app "Applications/<Company>/<Role>" --kind cover-letter
```

Output lands in the application's `Artifacts/` folder as `Resume v<N> <date>.pdf`,
with the version auto-incremented so a submitted artifact is never overwritten.

## What it checks before you send anything

- Page count matches the budget (one page unless you pass `--pages 2`)
- Fonts are embedded, so it renders the same on someone else's machine
- Text is extractable, which is what makes it ATS-readable
- No line exceeds the text column, and no role title collides with its dates
- No unreplaced `{{PLACEHOLDER}}` survived into the output

If the content does not fit, it reports how many lines are over and refuses to
render rather than clipping — a clipped PDF looks correct until someone reads the
bottom of it. Cut that much copy, or opt into two pages deliberately.

It also writes a proof PNG beside the PDF. Look at it before submitting; the
automated checks catch structural faults, not ugly ones.

## The design

`Resume - Figma Inspired.ps` and `Cover Letter - Figma Inspired.ps` define the
visual identity: the blue stacked-name header, the right-aligned contact block
with vector icons, the section rules, US Letter size, and the colour palette. The
renderer uses their definitions unchanged and generates only the content stream.

To change the look, edit the definitions at the top of those files — colours
(`brand`, `ink`, `muted`), the icon paths, the name size. Avoid adding
fixed-position drawing commands after the definitions; hardcoded coordinates are
exactly what made the earlier manual reflow workflow necessary.

## Layout rules the renderer preserves

- Essential information stays text. Icons are decorative and carry no content.
- Body copy runs the full column width; bullets indent from it.
- Education and experience dates align to the same right edge.
- Blue is used for the name, section labels, rules, bullets, and icons only.
- Dates and contact text stay muted grey; body copy stays near-black.
- Exact versus estimated language from the evidence notes is carried through
  unchanged — the renderer never rewords anything.

## Source format

The renderer reads the structure of `Resume Copy.md`: a `## Header` section with
name, professional title, and a `·`-separated contact line; `## Summary`;
`## Experience` with `### Title | Company | Dates` and `-` bullets; then
optionally `## Additional Experience`, `## Education`, and `## Technical Skills`.

A cover letter needs no special structure — write it as a letter. Everything above
its first `## ` heading is rendered, and the letterhead comes from
`Personal Information/Contact.md`, so contact details live in exactly one
place; only entries whose audience is `application` or `public` appear on it.
