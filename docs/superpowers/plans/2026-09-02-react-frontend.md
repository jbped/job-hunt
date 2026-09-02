# React Frontend (Milestone 0.6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for your assigned phase. Steps use checkbox (`- [ ]`) syntax. You will be told which phase (A, B1, B2, B3, or C) is yours — execute only that phase.

**Goal:** Replace the vanilla `server/assets/ui/index.html` with a Vite + React 18 + TypeScript-strict frontend at feature parity and identical visual design; users still never need Node.

**Architecture:** Top-level `ui/` holds the React source; the built bundle is committed to `server/assets/ui/` (Vite builds straight there). The existing CSS ports wholesale as a global stylesheet; components reuse its class names. TanStack Query over the existing API with the fingerprint poll invalidating queries. Phase A builds the shared foundation (shell, API layer, note components, modals); phases B1–B3 port the eight views in parallel worktrees over disjoint files; phase C integrates, adds the CI drift gate, runs the parity walk, and retires the old page.

**Tech Stack:** Vite 6, React 18, TypeScript strict, @tanstack/react-query v5, vitest + @testing-library/react. Node 22 (build-time only; this machine has v22.23.2). The Python server stays stdlib-only.

**Spec:** `docs/superpowers/specs/2026-09-02-webapp-first-design.md` (§ Milestone 0.6)
**Parity source of truth:** `docs/superpowers/plans/2026-09-02-ui-parity-inventory.md` — read it before your phase; it maps every behavior to `index.html` line numbers. The live `server/assets/ui/index.html` (until phase C, the vanilla page) is the reference implementation: when this plan and that file disagree, the file wins and you report the discrepancy.

## Global Constraints

- Feature parity, same visual design. No redesigns, no new features, no UX "improvements" — oddities of the current page are the contract (replaceState-only routing, hash token `calendar` for Interviews, no re-render after inline field save).
- TypeScript `strict: true`; no `any` except where a third-party type forces it (comment why).
- No component library. No CSS-in-JS. No markdown library — port the deliberate tiny renderer.
- The server keeps Python stdlib only; `server/test_safety.py` passes unweakened at every commit.
- Token: the built `index.html` carries the literal `__SESSION_TOKEN__` in an inline script; `serve.py` keeps the same `.replace()`.
- Users never need Node: the bundle in `server/assets/ui/` is committed; CI fails on drift.
- Branch discipline: phase A on `react-frontend-0.6`; B1/B2/B3 on worktree branches `0.6-views-apps`, `0.6-views-board-leads`, `0.6-views-rest` cut from A's tip; C back on `react-frontend-0.6` after merging B*. No pushes.
- Commit per task. Run `python3 server/test_safety.py` before every commit (it owns the API contract you're consuming).

---

## Phase A — Foundation (one worker, sequential)

### Task A1: Scaffold ui/ with Vite + React + TS strict

**Files:**
- Create: `ui/package.json`, `ui/vite.config.ts`, `ui/tsconfig.json`, `ui/index.html`, `ui/src/main.tsx`, `ui/src/App.tsx`, `ui/.gitignore`
- Modify: `.gitignore` (repo root)

**Interfaces:**
- Produces: `npm run dev` (Vite, proxies `/api` and `/file` to `http://127.0.0.1:8765`), `npm run build` (outputs to `../server/assets/ui`), `npm test` (vitest). All later tasks assume these.

- [x] **Step 1: Scaffold**

```bash
cd ui 2>/dev/null || mkdir ui && cd ui
npm create vite@latest . -- --template react-ts
npm install
npm install react@18 react-dom@18
npm install -D @types/react@18 @types/react-dom@18
# (the Vite template ships React 19; the spec pins 18 — confirm package.json shows ^18 after)
npm install @tanstack/react-query
npm install -D vitest @testing-library/react @testing-library/user-event jsdom @testing-library/jest-dom
```

- [x] **Step 2: vite.config.ts**

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: { outDir: "../server/assets/ui", emptyOutDir: true },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8765",
      "/file": "http://127.0.0.1:8765",
    },
  },
  test: { environment: "jsdom", setupFiles: "./src/test-setup.ts", globals: true },
});
```

(vitest config inline via `vite.config.ts` needs `/// <reference types="vitest/config" />` at top or `defineConfig` from `vitest/config` — use `vitest/config`.)

- [x] **Step 3: tsconfig strict; index.html token bootstrap**

Ensure `"strict": true` in `ui/tsconfig.json` (the template default — verify). Replace `ui/index.html` body with:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Job Hunt</title>
    <script>window.__SESSION_TOKEN__ = "__SESSION_TOKEN__";</script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

The inline script survives the Vite build verbatim — that is the placeholder `serve.py` replaces. Delete the Vite template boilerplate (logos, App.css, demo counter).

- [x] **Step 4: .gitignore entries**

`ui/.gitignore`: `node_modules/`. Repo root `.gitignore`: add `ui/node_modules/`. Do NOT ignore `server/assets/ui/` — the bundle is committed.

- [x] **Step 5: package.json scripts** — `"dev": "vite"`, `"build": "tsc -b && vite build"`, `"test": "vitest run"`, `"typecheck": "tsc -b"`.

- [x] **Step 6: Verify** — `npm run typecheck` clean; `npm test` runs (0 tests OK); **do not run `npm run build` yet** (it would overwrite the vanilla page — the build first runs in phase C). `python3 ../server/test_safety.py` passes.

- [x] **Step 7: Commit** — `git checkout -b react-frontend-0.6`, commit `Scaffold the React frontend workspace`.

### Task A2: Global stylesheet + API types + client

**Files:**
- Create: `ui/src/styles.css` (wholesale port of index.html lines 7–252), `ui/src/api/types.ts`, `ui/src/api/client.ts`

**Interfaces:**
- Produces (exact, later phases import these):
  - `types.ts`: `VaultIndex`, `Schema`, `SchemaForm`, `SchemaFormField`, `NotePayload { path: string; name: string; text: string; fingerprint: string; readonly: boolean }`, `StateResponse { state: string }`, `AuditReport { errors: string[]; warnings: string[] }`, `JobStatus`, and one request/response pair per POST route (`FieldSave`, `NoteSave`, `EntryAppend`, `InterviewCreate`, `ApplicationCreate`, `PersonCreate`, `RoleCreate`, `AccomplishmentCreate`, `LeadCreate`, `CaptureRequest`, `ArchiveRequest`, `UnarchiveRequest`, `RenderRequest`) — field names exactly per the inventory's route table. Type `VaultIndex` by reading `server/export_index.py`'s `build()` output shape; do not guess.
  - `client.ts`: `api<T>(path: string, opts?: { method?: "GET" | "POST"; body?: unknown }): Promise<T>` — JSON fetch; on POST sets `Content-Type: application/json` and `X-Session-Token`; token = `window.__SESSION_TOKEN__` unless it still equals the literal placeholder, then `import.meta.env.VITE_SESSION_TOKEN` (dev mode). Non-2xx: throw `ApiError` with `.status` and `.message` from the body's `error` key. Export `class ApiError extends Error { status: number }`.

- [x] Port the CSS verbatim (keep the custom-property names and the `prefers-color-scheme` block byte-identical; import from `main.tsx`). Write the types. Write the client. `npm run typecheck` clean; commit `Port the stylesheet and type the API surface`.

### Task A3: Query layer, vault-state poll, hash-view hook, app shell

**Files:**
- Create: `ui/src/api/queries.ts`, `ui/src/hooks/useVaultStatePoll.ts`, `ui/src/hooks/useHashView.ts`, `ui/src/components/Toast.tsx`, `ui/src/views/` (eight stub files), rewrite `ui/src/App.tsx`, `ui/src/main.tsx`

**Interfaces:**
- Produces:
  - `queries.ts`: `useIndexQuery(): UseQueryResult<VaultIndex>` (key `["index"]`, fetch `/api/index`), `useSchemaQuery()` (key `["schema"]`), `useAuditQuery()` (key `["audit"]`), and `invalidateAfterWrite(qc: QueryClient): Promise<void>` — invalidates `["index"]`, `["schema"]`, `["audit"]`. Every mutation in phases B/C calls `invalidateAfterWrite` on success (mirrors the server's write-invalidates-projection contract).
  - `useVaultStatePoll.ts`: 3000ms interval + focus + visibilitychange listeners fetching `/api/state`; skips while `document.hidden` or an input/select/textarea has focus or a dialog is open (port `editingNow()`, index.html:1780–1784); first response only baselines; on change, invalidate `["index"]`/`["schema"]` then `["audit"]`.
  - `useHashView.ts`: `const [view, setView] = useHashView()` — `View` union type `"now" | "leads" | "applications" | "board" | "calendar" | "people" | "evidence" | "archived"`; reads `location.hash` once on mount (unknown → `"now"`); `setView` does `history.replaceState(null, "", "#"+v)`. No hashchange listener (parity).
  - `Toast.tsx`: exports `ToastProvider` + `useToast(): (msg: string, kind?: "ok" | "error") => void`; renders `#toast` with `data-show`/`data-kind`, auto-dismiss 2500ms / 6000ms for errors (parity with `toast()`, index.html:391).
  - `views/`: `NowView.tsx`, `LeadsView.tsx`, `ApplicationsView.tsx`, `BoardView.tsx`, `InterviewsView.tsx`, `PeopleView.tsx`, `EvidenceView.tsx`, `ArchivedView.tsx` — each a stub `export default function XView() { return <section data-view="…" data-active="" /> }` so B workers touch only their own files.
  - `App.tsx`: header + nav (labels and order per the inventory table; button per view with `aria-current` handling), renders the active view component, mounts `useVaultStatePoll`, audit banners from `useAuditQuery` (port `renderAudit()`, index.html:711).

- [x] Implement; `npm run typecheck` + `npm test` clean; write one vitest for `useHashView` (mount with `location.hash = "#board"` → view `board`; `setView("leads")` calls replaceState). Commit `Add the query layer, state poll, hash routing, and app shell`.

### Task A4: Shared note components, markdown renderer, wikilinks, modals, inline editor

**Files:**
- Create: `ui/src/lib/markdown.tsx`, `ui/src/components/NoteViewer.tsx`, `ui/src/components/NoteOverlay.tsx`, `ui/src/components/EditableField.tsx`, `ui/src/components/Modal.tsx`, `ui/src/components/FormModal.tsx`, `ui/src/lib/wikilink.ts`
- Test: `ui/src/components/__tests__/FormModal.test.tsx`, `ui/src/components/__tests__/NoteViewer.test.tsx`

**Interfaces:**
- Produces (B phases consume; port each from the inventory's function map, preserving class names):
  - `markdown.tsx`: `renderMarkdown(text: string): ReactNode` — port `markdown()`/`inline()` (index.html:467/445) exactly: escape everything, then the small subset (code, wikilinks as `<a class="wikilink" data-wikilink>`, bold, italic, autolinks, `[text](url)`, headings, lists, `pre.verbatim`, blockquote, hr). No library.
  - `wikilink.ts`: `openWikilink(link: string, helpers: { showApplication(path: string): void; openOverlay(path: string): void; toast: ToastFn })` — port index.html:613 (resolve via `/api/resolve`; image/PDF → `window.open("/file/"+path)`; application-owned → `showApplication`; else overlay).
  - `NoteViewer.tsx`: props `{ path: string; title?: string }` — `<details class="note">` lazy-fetching `/api/note` on first open; view/edit swap with fresh-fingerprint re-fetch before editing; save via `/api/note/save`; 409 handling: toast the error, and if it contains `"changed on disk"` call `invalidateAfterWrite`; render `warnings` as error toasts on successful save (parity: `noteViewer`/`noteEditor`/`noteFoot`, index.html:529/559/590). Include the "Open in Obsidian" link (`obsidian()`, index.html:670).
  - `NoteOverlay.tsx`: the lightbox (index.html:640); context provider `NoteOverlayProvider` + `useNoteOverlay()` so any view can open it.
  - `EditableField.tsx`: props `{ path: string; field: string; value: string; enumKey?: string }` — input or select from `schema[enumKey]`; POST `/api/field` on change; **on success show `.saved` feedback but do NOT invalidate queries** (parity: no re-render mid-edit; the poll redraws later); on 409 toast + conditional invalidate (index.html:679–703).
  - `Modal.tsx`: `openModal(spec)` equivalent of `modal()` (index.html:1576) as a `<dialog>` component with a promise-based API: `useModal(): (fields: ModalField[], opts: { title: string; submit: string }) => Promise<Record<string, string> | null>`.
  - `FormModal.tsx`: `useFormModal(): (formKey: "application" | "person" | "role" | "accomplishment" | "lead") => Promise<void>` — builds fields from `schema.forms[formKey]` (`widget`/`enum`/`required`/`placeholder` honored), POSTs to the form's `endpoint`, toasts, `invalidateAfterWrite` (index.html:1613).

- [x] Tests (write first, watch them fail, then implement):
  - `FormModal.test.tsx`: given a schema fixture with a `lead` form (one required text, one select with `enum`), the dialog renders those fields, refuses submit with the required field empty, and on submit POSTs the exact payload to the form's `endpoint` (mock `fetch`).
  - `NoteViewer.test.tsx`: mock `/api/note` then a 409 on `/api/note/save` with `{"error":"note changed on disk"}` — asserts the toast fires and the index query is invalidated (fingerprint-conflict contract).
- [x] `npm run typecheck` + `npm test` green; `python3 server/test_safety.py` green; commit `Add shared note, modal, and field-editor components`.

**Phase A exit:** stub app runs under `npm run dev` against a live Python server (manual check: nav switches stubs, audit banner shows, toast works). Report back for phase B dispatch.

---

## Phase B — Views (three workers, parallel worktrees off `react-frontend-0.6`)

Every B worker: read the inventory doc + your views' `render*()` functions in `server/assets/ui/index.html` before writing code. Only touch your own `ui/src/views/*.tsx` files (plus new files under `ui/src/views/<yourview>/`); shared components are frozen — if one is missing a capability you need, report it, don't edit it. Data comes from `useIndexQuery()`; mutations call `invalidateAfterWrite` unless noted. Preserve every class name your reference markup uses. Each worker: `npm run typecheck` + `npm test` green before each commit.

### Task B1 (branch `0.6-views-apps`): Applications split view + PDF rendering

**Files:** `ui/src/views/ApplicationsView.tsx` + `ui/src/views/applications/*` (Rail, Viewer, PickList, ActionBar as separate components)

Port: `buildRail()` (index.html:870, incl. `pickButton` 856 grouping/filter/dots), `fillPickList()` 1000 + `docButton()` 1012 + `syncDocSelection()` 1025, `renderViewer()` 1030 (viewer-head fields via `EditableField`, documents via `NoteViewer`), `renderPdf()` 1687 (POST `/api/render`, 700ms poll of `/api/job/<id>`, toast on done/failed — no query invalidation for render), `newApplication()` 1633 via `useFormModal("application")`, archive action via the shared modal → `/api/archive`. Expose the imperative "show this application" entry the wikilink helper needs (register it through a context or module-level setter defined in `wikilink.ts` — match what phase A produced). Selection state (which application, which document) is component state, not the hash (parity).

### Task B2 (branch `0.6-views-board-leads`): Board + Leads + Archived

**Files:** `ui/src/views/BoardView.tsx`, `ui/src/views/LeadsView.tsx`, `ui/src/views/ArchivedView.tsx` (+ subdirs)

Port: `renderBoard()` 1116 / `boardCard()` 1095 / `moveCard()` 1083 — HTML5 drag-and-drop AND the `<select>` fallback, both POSTing `/api/field` with `field: "status"` then invalidating (board moves DO refresh, unlike inline field edits — check the reference: `moveCard` calls `save` then `refresh`; mirror exactly what the vanilla page does). Leads: the three buckets (`#leadsOpen/#leadsPromoted/#leadsPassed`), `promoteLead()` 1143 (POST `/api/application` `{lead: path}`), lead creation via `useFormModal("lead")`, lead notes via `NoteOverlay`. Archived: `renderArchived` groups + `restoreUnit()` 1540 (POST `/api/unarchive`).

**Test (required):** `ui/src/views/__tests__/archive-restore.test.tsx` — with a mocked index fixture, archiving from the modal POSTs `/api/archive` with `{kind, path, reason}`, restore POSTs `/api/unarchive` with `{path}`, and both invalidate the index query (the spec names archive/restore flows as a required test).

### Task B3 (branch `0.6-views-rest`): Now + Interviews + People + Evidence

**Files:** `ui/src/views/NowView.tsx`, `ui/src/views/InterviewsView.tsx`, `ui/src/views/PeopleView.tsx`, `ui/src/views/EvidenceView.tsx` (+ subdirs)

Port: Now's `#upcoming/#todo/#pipeline` panels; Interviews (`renderCalendar` — upcoming/previous, `addInterview()` 1658 as a hand-built modal via `useModal`, application `<select>` from the index, interview status via `EditableField`); People (`#people/#network/#contacts` incl. `addPerson()` 1473 via `useFormModal("person")`, `addContact()` 1637 via `useModal`, and the open-accordion preservation — component state per person keyed by path replaces the `OPEN_EDITORS` set, index.html:378); Evidence (roles/accomplishments tree, `useFormModal("role")`/`useFormModal("accomplishment")`, notes via `NoteViewer`).

---

## Phase C — Integration, CI, cutover (one worker, on `react-frontend-0.6`)

### Task C1: Merge B branches; serve the hashed bundle

- [x] Merge `0.6-views-apps`, `0.6-views-board-leads`, `0.6-views-rest` (in that order; conflicts should be nil — disjoint files — investigate any that appear). `npm run typecheck`, `npm test`, `python3 server/test_safety.py` all green.
- [x] Extend `server/serve.py` `do_GET`: for paths under `/assets/`, serve the file from `UI_DIR / path` (guard: resolved path must stay inside `UI_DIR`; 404 otherwise; mimetypes via `mimetypes.guess_type`; no token replacement). Keep `/` exactly as-is. Add nothing else. This is the one sanctioned server change in 0.6 — `test_safety.py` must still pass unweakened.
- [x] Commit `Merge the view ports and serve hashed bundle assets`.

### Task C2: Build, parity walk, retire the vanilla page

- [x] `cd ui && npm run build` — this **replaces** `server/assets/ui/index.html` with the built page (and writes `server/assets/ui/assets/*`). The vanilla page is gone from the working tree at this moment; it survives in git history.
- [x] Serve the demo vault (`python3 demo/build_demo.py --force`, then `python3 server/serve.py --vault demo/vault --no-browser --port 8766`) and walk every view against the checklist: each of the 8 views renders its data; create a lead; promote it; board drag (or select fallback) moves status; open + edit + save a note; force a fingerprint conflict (edit the file on disk mid-edit) and see the conflict toast; archive + restore; schedule an interview; add a person + contact; render a PDF; wikilink navigation (application-owned and overlay cases); Obsidian link present; audit banner shows; token gate (POST without token → 403 — automatic via the shared client, verify by curl). Compare against the vanilla page from git (`git show HEAD~1:server/assets/ui/index.html > /tmp/.../old.html` served however convenient, or read it) where a behavior is in doubt.
- [x] Fix findings, rebuild, re-walk until clean. Commit `Ship the React frontend bundle` (the built output is part of this commit).

### Task C3: CI drift gate + docs

- [x] `.github/workflows/release.yml`: before the Python steps add setup-node (`node-version: 22`), `npm ci` + `npm run build` in `ui/`, then `git diff --exit-code server/assets/ui/` (fails the build on a stale committed bundle).
- [x] Docs: README gains a two-line "Developing the UI" note (`cd ui && npm run dev`, Vite proxies to the Python server; users need no Node); CONTRIBUTING.md likewise; AGENTS.md gains one paragraph: `ui/` is the React source, the committed bundle lives in `server/assets/ui/`, never hand-edit the bundle.
- [x] `python3 server/package_app.py` — confirm the zip picks up the new bundle (it lives under `server/`, so no packaging change should be needed; verify `server/assets/ui/assets/` files are in the zip).
- [x] Full gate: `npm run typecheck`, `npm test`, `python3 server/test_safety.py`, `python3 server/audit_vault.py` exit 0. Commit `Gate CI on bundle drift and document the UI workspace`.
- [x] Write `docs/superpowers/plans/2026-09-02-react-frontend-verification.md` recording the parity-walk checklist results and all gate outputs. Commit. Stop — do not merge to main, do not push.
