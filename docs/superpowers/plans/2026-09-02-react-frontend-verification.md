# Milestone 0.6 verification — React frontend

Date: 2026-09-02. Branch `react-frontend-0.6`. Nothing pushed, nothing merged
to `main`. Parity reference throughout: `git show 'main:server/assets/ui/index.html'`
(the vanilla page, retired from the working tree by this milestone).

## How the walk was run

No browser automation was used or offered. The dashboard was exercised two
ways:

1. **curl** against a live server for everything that is an HTTP fact: token
   substitution, the new `/assets/` route and its traversal guard, the write
   gates, asset and artifact content types.
2. **The real React components rendered in jsdom against the live Python
   server** — `fetch` pointed at `http://127.0.0.1:8766`, the session token
   supplied the way the served page supplies it. Every click below is a real
   `userEvent` click on the real component tree, and every assertion about the
   vault is a re-read of `/api/index` afterwards. These walk files were deleted
   after the walk: they need a running server and a freshly built demo vault,
   so they do not belong in `npm test`.

The demo vault was rebuilt (`python3 demo/build_demo.py --force`) and the
server restarted before each full pass; the walk is stateful and a leftover
`Initech` from a previous pass makes the "create a lead" step fail on a
duplicate. Two apparent failures during the walk were exactly this and nothing
else.

## Gates

| Gate | Result |
|---|---|
| `python3 server/test_safety.py` | 36 tests, OK — unweakened, run before every commit |
| `python3 server/audit_vault.py` (live vault) | exit 0 |
| `cd ui && npm run typecheck` | clean (TypeScript strict) |
| `cd ui && npm test` | 6 files, 18 tests, passed |
| `cd ui && npm run build` then `git diff --exit-code server/assets/ui/` | no drift — the committed bundle matches its source |
| `python3 server/package_app.py` | 83 files, 366 KB; contains `server/assets/ui/index.html` + both hashed assets; no vault data |
| Unzipped release run from its own root | `GET /` 200, `GET /assets/index-*.js` 200 |

## Parity checklist

Every row was executed against the demo vault unless the note says otherwise.

| Checklist item | Result |
|---|---|
| Now renders `#upcoming` / `#todo` / `#pipeline` | pass — pipeline counts real statuses |
| Leads renders `#leadsOpen` / `#leadsPromoted` / `#leadsPassed` | pass |
| Applications renders the rail + viewer, viewer defaults to the brief | pass |
| Board renders one column per status | pass |
| Interviews renders `#calendarUpcoming` / `#calendarPrevious`, hash stays `#calendar` | pass |
| People renders `#people` / `#network` / `#contacts` | pass |
| Evidence renders roles, accomplishments and the skills table | pass |
| Archived renders | pass |
| Create a lead (schema-driven form modal, vocabularies from `/api/schema`) | pass — `Created Leads/Initech - Staff Engineer.md` |
| Promote a lead | pass — application created, lead status `promoted` |
| Board move via the `<select>` fallback | pass — `/api/field` write, and the card redraws in its new column (board moves *do* refresh) |
| Board move via drag and drop | pass — synthetic `dragstart`/`dragover`/`drop` with a `dataTransfer` stub; the status write lands |
| Open + edit + save a note | pass — toast `Saved`, text written |
| Force a fingerprint conflict (file written on disk mid-edit) | pass — conflict message inline *and* as an error toast; the edit buffer stays open |
| Archive + restore | pass — `/api/archive` with the reason, entry appears under Archived with its reason, `/api/unarchive` puts it back |
| Schedule an interview (picker modal, active applications first) | pass — appears under Upcoming |
| Add a person | pass |
| Add a contact to an application | pass — appears in the People view's contacts table |
| Render a PDF | pass — `validated · Page size: 612 x 792 pts (letter) · Pages: 1 · Fonts: 2 used, 2 embedded · Extractable text: 125 words`; the artifact takes over the right pane |
| Wikilink → application-owned note | pass — routes into the split view, overlay stays shut |
| Wikilink → note with no view of its own | pass — opens the lightbox with its own foot line and edit flow (see caveat below) |
| "open in Obsidian" present under a rendered note | pass — `obsidian://open?vault=vault&file=…` |
| Audit banner | pass — error banner outranks warnings and reports `(+n more)`; warning banner when there are no errors (both driven by a stubbed `/api/audit`, since the demo vault audits clean) |
| Board "show terminal statuses" toggle | pass — `rejected` column hidden until asked for |
| New application from the header lands on the created application | pass — exercises the fixed pending-request path |
| Token gate | POST with no token 403, wrong token 403, wrong content-type 403, cross-origin `Origin:` 403, correct token 200 |
| `/assets/` route | `.js` `text/javascript` 200, `.css` `text/css` 200, `/assets/../index.html` 404, `%2e%2e` 404, missing file 404 |
| `/file/` artifact | 200 `application/pdf` |

## Findings

1. **Token substitution broke every write (found by the walk, fixed).** The
   Phase A bootstrap was `window.__SESSION_TOKEN__ = "__SESSION_TOKEN__"`, and
   `serve.py` replaces *every* occurrence of that literal — so the property was
   renamed along with its value, the client read `undefined`, and every POST
   was a 403. The vanilla page had only one occurrence, which is why the rule
   never bit before. Fixed in the page, not the server: the global is now
   `__CE_SESSION_TOKEN__`, leaving exactly one placeholder for `serve.py` to
   substitute. `serve.py`'s replacement is untouched.

2. **`requestApplication` left handled requests pending (ledger 1, fixed).**
   Listeners now report whether they claimed the request; only an unclaimed one
   is left pending for a view that was not yet mounted. Covered by
   `ui/src/lib/__tests__/wikilink.test.ts`.

3. **Duplicated helpers lifted (ledger 2–3).** `statusPill`, `referencePill`,
   `fieldRow`, `today`/`days`, `noteLabel`, `peopleFor`/`involvementMatches`
   and the hand-built write modals each existed in two or three view branches;
   they now live once in `ui/src/lib/` and `ui/src/components/`. The interview
   modal is one implementation taking `Application | null`, matching the
   reference's single `addInterview(app)` with its optional picker.

4. **`NoteViewer` summary slot (ledger 4).** Evidence hangs the company and a
   real status pill inside the note `<summary>` again, as `renderEvidence()`
   does, instead of folding them into the title text.

5. **No view opens the note overlay directly — this is correct.** The B2 brief
   expected lead notes to open in the overlay; the reference reaches
   `openNoteOverlay()` only from `openWikilink()` (index.html:634), and
   `noteViewer()` only from Interviews (1249) and Evidence (1485). Leads use
   the inline editor accordion in both implementations. Left as built.

6. **Ledger items 5 and 6 confirmed as built.** No ActionBar in Applications
   (the reference has none); `renderPdf` invalidates after the job settles (the
   reference ends with `refresh()`; the plan's "no invalidation for render" was
   wrong).

## Caveats — what could not be verified by hand

- **No browser was driven.** Everything below the DOM is verified; nothing
  above it is. Not verified: actual pixels, the `prefers-color-scheme` dark
  palette, sticky positioning, the `.rail`/`.board` scroll containers, focus
  outlines, and the `<dialog>`/`::backdrop` rendering. The stylesheet is a
  byte-level port of the vanilla page's CSS and every component reuses its
  class names, so the risk is markup-shaped rather than style-shaped, but it is
  unverified.
- **jsdom implements `<dialog>` without `showModal`/`close`.** The test setup
  polyfills them, so modal and overlay behaviour is verified against a stand-in,
  not the browser's own dialog semantics (top layer, backdrop, Escape).
- **Drag and drop was synthesised.** The handlers and the resulting write are
  verified; the browser's own drag imagery and `dragenter`/`dragleave`
  highlighting (`.col.drop`) are not.
- **The overlay wikilink case had to be planted.** No note in the demo vault
  links outside its own application folder — the one candidate,
  `Contacts.md`'s `[[People/<Folder>/Full Name]]`, is a template placeholder
  that `/api/resolve` returns 404 for. The walk appended a real
  `[[People/Network/Jordan Exemplar]]` link to an Analysis note, exercised the
  route, and restored the file. The router branch is verified; a demo vault
  that ships such a link would verify it end to end.
- **Audit banners were driven from a stubbed `/api/audit`.** The demo vault
  audits clean, so real error/warning payloads were not produced by a real
  vault during this walk.
- **The `<select>` fallback and inline field editors were exercised, but the
  "no re-render on inline field save" property was not asserted directly** —
  only that the write lands and the toast fires.
- **Not walked:** the browser extension pairing round-trip (the dialog and the
  copy fallback are verified; no extension was paired), Docker, and any vault
  other than the demo one.

## Commits

```
9a2aff8  Lift the shared view helpers and fix the pending application request
aafb4ba  Serve the bundle assets beside index.html
7bbd0f4  Ship the React frontend bundle
```
plus the three view-branch merges and this milestone's CI/docs commit.
