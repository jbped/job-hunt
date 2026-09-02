# UI parity inventory — source of truth for the milestone 0.6 port

Produced 2026-09-02 against main @ 35925e3 (0.5 merged). Every claim carries
the line number in `server/assets/ui/index.html` (1809 lines: CSS 7–252,
HTML 254–369, JS 370–1807) or `server/serve.py`. Executors: treat this as
the map, but verify against the live file — line numbers drift.

## Views

Nav `button[data-view]` (259–266), `section[data-view]` (275–362).

| Nav label | data-view / hash | Section containers |
|---|---|---|
| Now | `now` | `#upcoming` `#todo` `#pipeline` |
| Leads | `leads` | `#leadsOpen` `#leadsPromoted` `#leadsPassed` |
| Applications | `applications` | `.split` → `#rail` (aside) + `#viewer` |
| Board | `board` | `#board` |
| Interviews | `calendar` | `#calendarUpcoming` `#calendarPrevious` |
| People | `people` | `#people` `#network` `#contacts` |
| Evidence | `evidence` | `#evidence` |
| Archived | `archived` | `#archived` |

**Decision (0.6):** the hash token for Interviews stays `calendar` — parity
preserves existing deep-links.

## View switching (the routing contract to replicate exactly)

`show(view)` (1725): sets module VIEW, `history.replaceState(null, "", "#"+view)`
(never pushState — no back/forward stack), toggles `data-active` on sections,
`aria-current` on nav buttons, calls `render()` (1735, a switch to 8
`render*()` functions). No `hashchange` listener: the hash is read once on
load (1751–1752) and only if it names a known view. Nav clicks drive
everything. **Decision (0.6):** replicate exactly; live-hashchange support is
post-parity feature work.

## CSS

Custom properties on `:root` (8–14): `--bg --panel --line --ink --muted
--brand --brand-soft --warn --warn-soft --bad --bad-soft --good --good-soft
--radius`; redefined wholesale under `@media (prefers-color-scheme: dark)`
(15–22). OS-preference only, no `[data-theme]` toggle. Only reset:
`* { box-sizing: border-box; }`. Class families (global, nothing scoped —
ports wholesale): layout `header nav main section[data-active]`; primitives
`.card .row .grow .title .muted .pill(.warn/.bad/.good) .grid
.banner(.warn/.bad) .empty .stack .kv`; forms `label input select textarea
.field-row .saved`, `dialog`/`::backdrop`, `#toast[data-show][data-kind]`;
board `.board .col(.drop) .bcard`; split view `.split .rail .pick(.sub/.dot)
.pick-list .pick-filter .group-label .actionbar .viewer .viewer-head
.viewer-doc .rail-actions`; notes `.note-edit`, `details.note > summary`,
`.note-body` (nested h2–h6, p, ul/ol, li, code, pre.verbatim, blockquote,
hr, `.wikilink`), `.note-foot`; inline editor `details.editor`.

## Session token

Server: `serve.py:810-811` string-replaces literal `__SESSION_TOKEN__` in
index.html on every `GET /`. Client: `const SESSION_TOKEN = "__SESSION_TOKEN__";`
(400), sent as `X-Session-Token` header on every POST inside `api()`
(402–410). The built bundle's index.html must keep the literal placeholder
in an inline script.

## API surface (serve.py)

GET (do_GET, 802–838):

| Path | Behavior | Response |
|---|---|---|
| `/` | index.html, token replaced | text/html |
| `/api/index` | `export_index.build(vault)` | full vault projection (client `DATA`) |
| `/api/state` | `vault_state(vault)` | `{"state": "<16-hex sha256 prefix>"}` |
| `/api/schema` | `api_schema(vault)` | see below |
| `/api/note?path=` | `read_note` | `{"path","name","text","fingerprint","readonly"}` |
| `/api/resolve?link=` | `resolve_wikilink` | `{"path"}` |
| `/api/audit` | `audit_vault.audit` | `{"errors":[…],"warnings":[…]}` |
| `/api/job/<id>` | `JOBS[id]` | `{"state":"running"\|"done"\|"failed", …}` |
| `/file/<rel>` | vault file, .png/.pdf/.jpg/.jpeg only, escape-guarded | bytes |
| else | 404 | `{"error":"no such route"}` |

Errors: `RequestError(status,msg)` → `{"error": msg}`; other exceptions →
500 `{"error":"internal error; see the terminal"}`.

POST — `HANDLERS` dict (717–731), `do_POST` (883–921). Every POST requires
`Content-Type: application/json` + `X-Session-Token` (constant-time compare)
else 403; cross-origin blocked unless 127.0.0.1/localhost/extension scheme.
After success, `export_index.write(vault)` runs unless route is `/api/render`
or `result["changed"] is False` — i.e. **every non-render mutation
invalidates the `/api/index` projection**.

| Path | Handler (line) | Payload | Response |
|---|---|---|---|
| `/api/field` | `set_field` (114) | `path, field, value, fingerprint?` | `{"changed","fingerprint"}` / 409 |
| `/api/note/save` | `save_note` (154) | `path, text, fingerprint` (required) | `{"changed":true,"fingerprint","warnings":[…]}` / 400 / 409 |
| `/api/entry` | `append_entry` (293) | `path, heading?, title, fields{}` | `{"changed":true,"fingerprint"}` |
| `/api/interview` | `create_interview` (338) | `application, when, stage?, method?, location_or_link?, point_of_contact?, interviewers?` | `{"path"}` |
| `/api/application` | `create_application` (359) | `lead?` (promotion) OR `company, position, url?, discovery?, detail?, source?` | `{"path"}` |
| `/api/person` | `create_person` (405) | `name, folder?, professional_relationship?, relationship?, company_context?, email?, phone?` | `{"path"}` |
| `/api/role` | `create_role` (475) | `company, title, start?, end?, team?` | `{"path"}` |
| `/api/accomplishment` | `create_accomplishment` (492) | `company, title, role?, folder?` | `{"path"}` |
| `/api/lead` | `create_lead` (388) | `company, role?, url?, source?, next_follow_up?` | `{"path"}` |
| `/api/capture` | `create_capture` (508) | `mode, company, url?, position?, text?, source?` | lead: `{"path","mode","stored_posting":false}`; application: `{"path","mode","sha256"}` |
| `/api/archive` | `archive_unit` (600) | `kind, path, reason?, fingerprint?` | `{"changed":true,"archived","from"}` |
| `/api/unarchive` | `unarchive_unit` (643) | `path, fingerprint?` | `{"changed":true,"restored"}` |
| `/api/render` | `start_render` (673) | `path, kind, pages?` | `{"job":"<12-hex>"}`, poll `/api/job/<id>` |

## /api/state semantics and the poll

`vault_state()` (217–231): sha256 over `path:mtime_ns` of every vault `*.md`
(excluding `.cache`/`.obsidian`), truncated to 16 hex. Stat-only. Client:
`checkVaultState()` (1786–1796) on `setInterval(…, 3000)` (1798) plus
visibilitychange→visible (1799–1800) and window focus (1801); no-op while
`document.hidden` or `editingNow()` (1780–1784: an input/select/textarea
focused, or the modal dialog open). On change: `refresh()` = parallel
re-fetch `/api/index` + `/api/schema`, then render, then `/api/audit`
separately (non-blocking). First poll only baselines. **0.6 shape:** keep a
raw interval/focus/visibility trigger that *invalidates* the TanStack Query
keys — not `refetchInterval` — because the skip-while-editing gate must
inspect focus state each tick.

## /api/schema

Top-level keys (734–757): `status, terminal, lead_status, interview_status,
discovery_method, compensation_status, compensation_period, work_model,
stage, method, contact_relationship, professional_relationship,
people_folders, reference_permission, contact_audience, editable,
archivable, forms, vault_name`. All but the last four are flat string-list
vocabularies used as `<select>` options.

`forms` (schema.py FORMS, 374–449): keys `application, person, role,
accomplishment, lead`; each `{"title","submit","endpoint","fields":
[{"name","label","required"?,"placeholder"?,"widget"?:"select"|"date",
"enum"?:"<schema key>"}]}`. Interview scheduling (`addInterview()`, 1658),
capture, and note/field/archive/entry flows are hand-built, not
schema-driven — same split survives in 0.6.

## Fingerprint conflict contract

Read `GET /api/note` returns opaque `fingerprint`. `/api/field`:
fingerprint optional (omitted = last-write-wins); mismatch → 409, body
`{"error": "...changed on disk..."}` — client toasts, and on the
"changed on disk" substring calls `refresh()` (697–700). `/api/note/save`:
fingerprint required (400: "the editor must send the fingerprint it loaded
with"), empty text refused (400), 409 same contract; success `warnings` are
non-fatal vocabulary notes shown as error-toasts while the save stands.

## Behaviors to preserve (function → line)

- `api()` 402 — fetch wrapper, token on POST only.
- `save()` 412, `editable()` 679 — inline field editor: save on change, **no
  re-render on success** (focus preservation; the poller redraws later).
- `toast()` 391 — `data-kind` ok/error, 2.5s / 6s auto-dismiss.
- `markdown()` 467, `inline()` 445 — deliberate tiny renderer: escape all
  HTML, then re-introduce code, wikilinks, bold, italic, autolinks,
  `[text](url)`. Port as-is; do not swap in a real markdown library.
- `noteViewer()` 529 — `<details>` lazy-fetches `/api/note` on first open.
- `noteEditor()` 559, `noteFoot()` 590 — textarea swap, re-fetch fresh
  fingerprint before opening the editor.
- `openWikilink()` 613 + delegated click on `a[data-wikilink]` (663–668) —
  `/api/resolve`; image/PDF → new tab; application-owned note → switch to
  Applications split view; else lightbox overlay.
- `openNoteOverlay()` 640 — overlay reusing the note edit flow.
- `obsidian()` 670 — `obsidian://open?vault=…&file=…` deep link.
- Applications split view: `buildRail()` 870, `pickButton()` 856,
  `fillPickList()` 1000, `docButton()` 1012, `syncDocSelection()` 1025,
  `renderViewer()` 1030.
- Board: `renderBoard()` 1116, `boardCard()` 1095, `moveCard()` 1083 —
  drag-and-drop AND `<select>` fallback, both via `save(..., "status", …)`.
- `promoteLead()` 1143 — POST `/api/application` with `lead`.
- `archiveUnit()` 1527 (reason modal → `/api/archive`), `restoreUnit()` 1540.
- `modal()` 1576 (generic dialog: archive/addContact/addInterview),
  `formModal(key)` 1613 (schema-driven), `newApplication()` 1633,
  `addPerson()` 1473, `addContact()` 1637, `addInterview()` 1658.
- `renderPdf()` 1687 — POST `/api/render`, poll `/api/job/<id>` every 700ms
  until `state !== "running"`.
- `OPEN_EDITORS` Set (378) — background refresh must not collapse an open
  person-editor accordion.
- `renderAudit()` 711 — audit banners, fetched outside the main refresh.

## Tooling / CI ground truth

- node v22.23.2, npm 12.0.2 installed. `ui/` does not exist yet.
- `.gitignore` has no `ui/` entries — 0.6 adds `ui/node_modules/` (build
  output goes straight to `server/assets/ui/`, which is committed).
- `.github/workflows/release.yml`: checkout → `python3 server/test_safety.py`
  → `python3 server/package_app.py` → tag: release upload, else artifact
  upload of `dist/career-evidence-app.zip`. No Node step yet; 0.6 adds
  setup-node (pin 22), `npm ci` + build in `ui/`, and a bundle-drift gate
  (`git diff --exit-code server/assets/ui/` after rebuild) before the Python
  steps.
