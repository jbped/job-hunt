# Company Questions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A per-company bank of application questions with the answers actually submitted, surfaced in the webapp's Applications view whenever an application targets that company.

**Architecture:** One new note type (`company-questions`, `Applications/<Company>/Company Questions.md`) using the vault's entry pattern extended with a prose body per entry. One new POST endpoint (`/api/question`) that scaffolds the note on first use and upserts entries by question. The index projection gains a `company_questions` collection; the React Applications view gains a QuestionsPanel. Answers are user-authored; agents read only.

**Tech Stack:** Python stdlib server, React/TS frontend — no new dependencies anywhere.

**Spec:** `docs/superpowers/specs/2026-09-02-company-questions-design.md`

## Global Constraints

- `python3 server/test_safety.py` passes unweakened before every commit; new behavior gets new tests there.
- `npm run typecheck` and `npm test` (in `ui/`) green before every commit; rebuild the bundle (`npm run build`) in the final task so the CI drift gate passes.
- Answers are user-authored: no endpoint may generate or transform answer text; the server stores what it is sent, verbatim.
- Existing `/api/entry` and its Contacts/person gate stay untouched.
- Branch `feat-company-questions` (already checked out in your worktree); commit per task; never push or merge.
- `python3 server/audit_vault.py` must exit 0 against the demo vault after seeding (run against demo via `CAREER_EVIDENCE_VAULT` or `--vault` if supported — check the script's args; never run destructive experiments against any non-demo vault).

## Ground truth (from the 2026-09-02 code inventory; verify line numbers as you go)

- Entry writes: `append_entry` (`server/serve.py:293-335`) — gate at `:308-310` (Contacts.md / `type: person` only), `##`/`###` heading logic `:312`, bullets-only body `:313-318` (`- Label: value`, label = key with `_`→space, first letter capitalized, empty → `Unknown`), placeholder drop `:191-203`, insertion before `## Entry format` via `_append_before_reference` `:206-214`, `v.atomic_write(..., expect=fingerprint, vault=vault)`.
- Entry reads: `export_index._entries` (`server/export_index.py:39-81`), `BULLET = re.compile(r"^\s*-\s+([^:]+):\s*(.*)$")`, `IGNORED_HEADINGS`, placeholder regex `^(YYYY|<|\{\{)`. **Prose between/after bullets is currently dropped — you will extend this.**
- Scaffold exemplar: `server/new_lead.py:36-72` (template load from `v.TEMPLATES_DIR`, `safe_name` from `new_application.py:43-51`, no-overwrite guard, `set_frontmatter_field` fills, write). Company folder may already exist: `mkdir(parents=True, exist_ok=True)` on the folder, no-overwrite guard on the **file**.
- Projection: `export_index.build` (`:116-290`); model a new company-level glob on `_archived()` (`:84-113`); apps glob is `Applications/*/*/Application Brief.md` (`:140`) — the bank sits one level up: `Applications/*/Company Questions.md`.
- Audit: type-dispatch chain at `audit_vault.py:292-300`; `report.warn`/`report.error` (`:69-78`); exit 1 only on errors. `TEMPLATES` list `:46-60` must gain the new template file. `check_enums` runs free for any type registered in `schema.NOTE_TYPES`.
- Schema: `NOTE_TYPES` (`schema.py:185-312`), `UI_EDITABLE` (`:317-368`), `UI_READONLY_FILES` (`:453`) — the new note is writable (Application-Brief-like contract), so NOT readonly.
- React: `ApplicationsView.tsx` owns the `.split` layout; `Rail.tsx` render controls `:219-227`, Details `:232+`. `useModal()` → `(fields: ModalField[], opts: ModalOptions) => Promise<Record<string,string> | null>`, `ModalField = {key, label, choices?, options?, multiline?, type?, placeholder?, value?}` — the add-question form uses this (like `useAddContact`, `ui/src/lib/actions.ts`), NOT `useFormModal`. `NoteOverlay` opens any note for fingerprint-guarded editing.
- Demo: `demo/build_demo.py:128-` seeds via direct handler calls; three apps are three distinct companies today — you will add a second application to one company so reuse is demonstrable.

---

### Task 1: Entry body support + the Company Questions note type + `/api/question`

**Files:**
- Create: `server/assets/templates/Company Questions.md`
- Modify: `server/serve.py` (new handler + HANDLERS entry), `server/export_index.py` (`_entries` body capture), `server/schema.py` (`NOTE_TYPES`)
- Test: `server/test_safety.py` (new tests, nothing weakened)

**Interfaces:**
- Produces: POST `/api/question` — payload `{company: str, question: str, answer: str, asked_on: str (application folder path), char_limit?: int|str, fingerprint?: str}`; response `{"changed": true, "path": "Applications/<Company>/Company Questions.md", "fingerprint": <new>}`. Upsert semantics: an existing entry with the same question heading gains the new `asked_on` wikilink (appended, deduplicated) and an updated date, and keeps its answer **unless** a non-empty `answer` is sent, which replaces it (the user resubmitting an edited answer). `_entries` items gain a `"body": str` key (prose after the bullet block, up to the next heading, stripped; `""` when absent).

- [ ] **Step 1: Write the template.** `server/assets/templates/Company Questions.md`: frontmatter `type: company-questions`, `company:` (filled at scaffold), body `# {company} | Questions`-style heading matching the template conventions of `Contacts.md` (read it first and mirror its placeholder + `## Entry format` documentation-footer structure). The Entry format example shows one question entry: `## <Question text>` + `- Asked on: [[Applications/<Company>/<Role>]]` + `- Date: YYYY-MM-DD` + `- Char limit: 300` + a prose paragraph as the sample answer.
- [ ] **Step 2: Failing tests first.** Add to `test_safety.py`: (a) `/api/question` to a new company scaffolds the note from the template with `type: company-questions` and refuses path escapes in `company`; (b) posting the same question twice yields one entry whose `Asked on` bullet carries both application links; (c) the answer body round-trips through `export_index._entries` (i.e. `_entries` returns the prose as `body`); (d) `/api/question` without the session token is 403 (it inherits the standard POST gate — assert it's registered in HANDLERS); (e) the scaffold refuses to overwrite an existing `Company Questions.md` structure (upsert appends, never rewrites unrelated content). Run: all new tests fail.
- [ ] **Step 3: Extend `_entries`.** After the bullet loop, capture subsequent non-bullet, non-heading lines as the entry's `body` (joined, stripped). Existing consumers (contacts, people) see `body: ""` — assert no behavior change by running the full suite.
- [ ] **Step 4: Implement the handler.** New `create_or_update_question(vault, payload)` in `serve.py` following `append_entry`'s structure: sanitize `company` with `safe_name`, scaffold from the template when the note is missing (folder `mkdir(parents=True, exist_ok=True)`, file no-overwrite — scaffold only when absent), then upsert the entry (heading = question text run through the same escaping the note's other headings get; bullets `Asked on` (wikilinks, comma-or-repeated-bullet — match the entry format you defined), `Date` (today), `Char limit` only when provided; body = answer verbatim). Fingerprint-guarded `atomic_write`. Register as `"/api/question"` in HANDLERS. Add `"company-questions"` to `schema.NOTE_TYPES` (`required: ["type", "company"]`, file `Company Questions.md`).
- [ ] **Step 5: Green.** `python3 server/test_safety.py` — everything passes. Commit: `Add the company questions note type and /api/question`.

### Task 2: Projection and audit

**Files:**
- Modify: `server/export_index.py` (`build`), `server/audit_vault.py`
- Test: `server/test_safety.py`

**Interfaces:**
- Produces: `/api/index` gains top-level `company_questions: [{company: str, path: str, question: str, fields: {...}, answer: str}]` (one item per entry, flattened, company from the folder name).

- [ ] **Step 1: Failing test.** `export_index.build` on a vault with a seeded bank exposes the entry under `company_questions` with company, question, and answer.
- [ ] **Step 2: Projection.** New block in `build` globbing `Applications/*/Company Questions.md`, parsing with `_entries`, flattening as specified.
- [ ] **Step 3: Audit.** `check_company_questions(report, note, vault, fm, text)` in the dispatch chain: warn when an `Asked on` wikilink doesn't resolve; warn when `Char limit` is non-numeric; never error (missing optional fields are fine). Add `"Company Questions.md"` to the `TEMPLATES` existence list. Test: an unresolvable `Asked on` produces a warning and exit code stays 0.
- [ ] **Step 4: Green + commit:** `Project and audit company question banks`.

### Task 3: QuestionsPanel in the Applications view

**Files:**
- Create: `ui/src/views/applications/QuestionsPanel.tsx`, `ui/src/views/applications/__tests__/QuestionsPanel.test.tsx`
- Modify: `ui/src/views/ApplicationsView.tsx` (mount the panel), `ui/src/api/types.ts` (`CompanyQuestion`, index key, `QuestionCreate` request), `ui/src/lib/actions.ts` (a `useAddQuestion` following `useAddContact`'s pattern)

**Interfaces:**
- Consumes: `index.company_questions`, `useModal`, `NoteOverlay` (`useNoteOverlay`), `invalidateAfterWrite`, toast.
- Produces: `<QuestionsPanel company={...} appPath={...} />` — a `.card` in the rail below Details.

- [ ] **Step 1: Failing tests.** RTL: (a) with an index fixture holding two questions for "Globex Corporation", selecting a Globex application renders both with their answers and a copy affordance; (b) the add-question modal submits `{company, question, answer, char_limit?, asked_on: appPath}` to `/api/question` and invalidates the index; (c) a company with no bank shows the panel's empty state with the add action.
- [ ] **Step 2: Implement.** Panel lists the selected application's company bank (question as heading, answer body, `Asked on` badges, char-limit pill when present); "Copy answer" (`navigator.clipboard.writeText`, toast on success); "Add question" via `useModal` (question text, answer `multiline: true`, optional char limit); "Mark asked here" on entries not yet linked to this application (posts the upsert with empty answer); "Edit in note" opens `Applications/<Company>/Company Questions.md` in the NoteOverlay for full fingerprint-guarded editing. Reuse existing class names (`.card .title .muted .pill .stack .kv`) — no new CSS.
- [ ] **Step 3: Green:** `npm run typecheck`, `npm test`, `python3 server/test_safety.py`. Commit: `Surface company question banks in the Applications view`.

### Task 4: Skills, docs, demo, verification

**Files:**
- Modify: `.agents/skills/career-evidence/SKILL.md`, `.agents/skills/career-evidence/references/vault-schema.md`, `demo/build_demo.py`
- Test: full gates + rebuild bundle

- [ ] **Step 1: Docs.** `vault-schema.md`: document the note type, its entry shape (bullets + prose answer body), and ownership. `SKILL.md`: one short rule in the ownership section — Company Questions answers are the user's submission record; agents may read them for context and must never write or draft them. Host-neutral wording (the neutrality test enforces it). Note in `vault-schema.md` that the four-places rule is satisfied with no `vault-template/` change: banks are created on demand, no company folders exist in a fresh vault.
- [ ] **Step 2: Demo seed.** In `build_demo.py`: add a second Globex Corporation application (reuse the existing app-seeding pattern), then seed a bank via the new handler (direct call, `serve.create_or_update_question(vault, {...})`) with two questions answered on the first Globex application. Rebuild: `python3 demo/build_demo.py --force`.
- [ ] **Step 3: Full verification.** `python3 server/test_safety.py`; `python3 server/audit_vault.py` against the demo vault exits 0; `cd ui && npm run typecheck && npm test && npm run build` (commit the rebuilt bundle — drift gate); manual API smoke against the demo vault: serve, fetch `/api/index`, confirm `company_questions` present; POST `/api/question` for the second Globex app and confirm the upsert added the link without duplicating the entry.
- [ ] **Step 4: Commit** `Document, seed, and verify company questions`, and write a short verification section at the bottom of this plan file (what ran, results). Stop — no push, no merge.

## Task 4 verification

Run by the implementing agent:

- Updated the host-neutral ownership and schema documentation for Company Questions.
- Rebuilt the demo vault with a second Globex Corporation application and two questions seeded through `serve.create_or_update_question`.
- `cd ui && npm run typecheck` — passed.
- `cd ui && npm test` — passed: 8 test files, 26 tests.
- `cd ui && npm run build` — passed; rebuilt bundle committed under `server/assets/ui/`.
- `git diff --check` — passed.

Run by the orchestrator from an unsandboxed shell in the same worktree:

- `python3 server/test_safety.py` — passed: 41 tests, `OK`.
- API smoke against `demo/vault` with `serve.py --port 8768` — `GET /api/index` exposed two seeded Globex `company_questions` entries with `asked_on` links. Posting `/api/question` with the exact seeded title `Why do you want to work at Globex?`, an empty answer, and `asked_on: Applications/Globex Corporation/Platform Engineer` kept the exact-title entry count at one, appended the second application link, and preserved the existing answer.
- Rebuilt with `python3 demo/build_demo.py --force`.
- `python3 server/audit_vault.py --vault demo/vault` — passed: 0 errors, 0 warnings.
