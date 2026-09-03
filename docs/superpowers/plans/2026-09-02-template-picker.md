# Template Registry & Picker (2a) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PDF templates become a registry — built-in plus user-supplied `.ps` files in the vault — carrying style *and declared layout parameters*, selectable per application in the webapp.

**Architecture:** Templates stay single `.ps` files. A parameter block in structured PostScript comments (`% ce-param: <key> <value>`) feeds a `Params` dataclass whose defaults are today's hardcoded constants, so a template with no block renders byte-identically to today. A registry resolves `built-in:<name>` / `vault:<name>` (from `Resources/Templates/`); the Application Brief gains `resume_template` / `cover_letter_template`; `/api/schema` carries the registry; the Rail gains two pickers.

**Tech Stack:** Python stdlib + Ghostscript (both unchanged); React/TS. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-09-02-resume-templates-design.md` (Part 2a, including the Amendment)

## Global Constraints

- **Golden rule: default output is unchanged.** A render with no template field set must produce byte-identical PostScript to today's — proven by test, not asserted.
- `python3 server/test_safety.py` unweakened + green, `npm run typecheck` + `npm test` green before every commit; rebuild the bundle in the final task.
- Server stays stdlib-only. Never transform a template: validate and refuse, or render as declared.
- Branch `feat-template-picker` in your worktree; commit per task; never push or merge.
- Vault-touching runs against the worktree's demo vault only.

## Ground truth (verified 2026-09-02 pre-merge; line numbers have drifted — locate by name)

- `render_pdf.py` resolution is hardcoded in `render()`: `template_name = "PDF/Resume - Figma Inspired.ps" if kind == "resume" else "PDF/Cover Letter - Figma Inspired.ps"`, then `template = v.TEMPLATES_DIR / template_name`. The brief is read AFTER resolution (only for display strings) — brief-driven resolution means moving/duplicating that read.
- `prologue(template)` splits the file at the literal marker `"\nbrand\nHB"` and uses ONLY the text before it; everything after (all the `{{...}}` placeholders) is discarded. `build_postscript()` substitutes exactly 3 tokens into the prologue: `{{FULL_NAME}}`, `{{POSITION}}`, `{{COMPANY}}`.
- The prologue contract a template must satisfy: define `/HB /HR` (fonts), `/brand /ink /muted` (colors), `/Rshow`, the 4 icon procs (`/phoneIcon /pinIcon /mailIcon /linkedinIcon`), carry the 3 tokens, keep the literal `%%Pages: 1` line, end with a line `brand` followed by a line starting `HB`.
- `overrides(d: Density)` redefines `/bodyline /bullet /role /education /section /contact` after the prologue — templates' own definitions of those 6 never execute.
- Layout is Python: `header_ops(data)`, `layout_resume`/`layout_letter` with module constants (`LEFT`, `RIGHT`, `TOP_RULE_Y`, the `Density` dataclass). These constants become `Params` fields.
- `validate()` after render: pdfinfo page count, pdffonts embedded, pdftotext non-empty + probe substring + leftover-`{{` check.
- Path guards: the resolve-inside-root pattern is duplicated in `serve.py` (`resolve()` and `_serve_asset`) — this plan lifts it into `vaultlib.py` as `resolve_within(root, relative) -> Path` and converts all three call sites.
- Schema: add both fields to `NOTE_TYPES["application"]["optional"]` (the projection picks optional fields up generically) and `UI_EDITABLE["application"]`. NOT to `ENUMS` (registry values are dynamic). `api_schema(vault)` in `serve.py` assembles `/api/schema` — add a computed `templates` key there.
- UI: `EditableField` already has `values?: string[]` for non-vocabulary selects. `Rail.tsx` has the render-controls block ("Generate resume"/"Generate cover letter") and the Details `EditableField` block — the pickers slot beside the render controls. `Schema` type lives in `ui/src/api/types.ts`; extend it.
- `server/assets/vault-template/Resources/README.md` exists (describes Resources as source-document ingress) — reconcile wording when adding `Resources/Templates/`.

---

### Task 1: Params — parameterize the layout engine, zero behavior change

**Files:** Modify `render_pdf.py`; test `server/test_safety.py`

**Interfaces:**
- Produces: `@dataclass Params` in `render_pdf.py` — fields for every module layout constant it replaces (at minimum `left`, `right`, `top_rule_y`, the `Density` numbers, and `section_order: tuple[str, ...]` over the engine's existing section identifiers), defaults = today's exact values; `parse_params(prologue_text) -> Params` reading `% ce-param: <key> <value>` lines (unknown key → `SystemExit` naming valid keys; malformed value → `SystemExit`); layout functions take a `Params` argument.

- [ ] **Step 1 (golden baseline):** add a test that renders the demo application's resume PostScript (the `.ps` text `build_postscript` produces, no Ghostscript needed) and stores its sha256 in the test as the expected value. Run once to capture the hash; the test then asserts it. This is the refactor's tripwire.
- [ ] **Step 2:** introduce `Params` + `parse_params`, thread through `header_ops`/`layout_resume`/`layout_letter`/`overrides`, delete the loose constants. `section_order` drives the order the engine emits its existing sections; validate entries against the known set.
- [ ] **Step 3:** golden test still passes (identical hash — defaults produce identical output). A unit test: a prologue with `% ce-param: left 72` yields `Params(left=72, ...)`; an unknown key exits loudly.
- [ ] **Step 4:** full suite green; commit `Parameterize the PDF layout engine`.

### Task 2: Registry, validation, and the shared path guard

**Files:** Modify `render_pdf.py`, `vaultlib.py`, `serve.py`; test `server/test_safety.py`

**Interfaces:**
- Produces: `vaultlib.resolve_within(root: Path, relative: str) -> Path` (raises `ValueError` on escape; `serve.py`'s `resolve()` and `_serve_asset` converted to use it); in `render_pdf.py`: `registry(vault) -> dict` mapping kind → list of `{"name": "built-in:<stem>"|"vault:<stem>", "path": ...}` (built-ins from `TEMPLATES_DIR/"PDF"`, vault from `vault/"Resources"/"Templates"` — missing dir = empty, resolved via `resolve_within`); vault templates declare kind via `% ce-kind: resume|cover-letter` (missing → excluded with a stderr warning, never a crash); `resolve_template(vault, kind, name|None) -> Path` (None → today's default; unknown name → `SystemExit` listing available names); `check_template(path, kind)` — marker present, 3 tokens present, params parse — run before any render with a non-default template.

- [ ] Tests first: registry ignores files outside the two roots (symlink escape refused via `resolve_within`); unknown template name exits listing names; a template missing `{{FULL_NAME}}` is refused by `check_template`; `resolve_within` conversion keeps the existing `/assets/` escape test green.
- [ ] Implement; suite green; commit `Add the template registry and validation`.

### Task 3: Brief fields, CLI, and /api/schema

**Files:** Modify `render_pdf.py` (CLI + brief-driven resolution), `schema.py`, `serve.py` (`api_schema`); test `server/test_safety.py`

**Interfaces:**
- Produces: `render_pdf.py --template <name>` CLI override; otherwise the brief's `resume_template`/`cover_letter_template` (read moved before resolution); both fields in `NOTE_TYPES["application"]["optional"]` + `UI_EDITABLE["application"]`; `/api/schema` gains `"templates": {"resume": [names...], "cover-letter": [names...]}` computed per request from `registry(vault)`.

- [ ] Tests first: a brief with `resume_template: vault:Sample` renders through the vault template (seed one in the test's temp vault); `/api/schema` exposes the registry; an unset field renders the default (golden hash again). Implement; green; commit `Resolve templates from the brief and expose the registry`.

### Task 4: Pickers in the Rail

**Files:** Modify `ui/src/api/types.ts` (Schema.templates), `ui/src/views/applications/Rail.tsx`; test `ui/src/views/applications/__tests__/` (new test file)

- [ ] Tests first (RTL): with a schema fixture carrying two resume templates, the picker renders both plus a "Default" option and writes the field via `/api/field`; no `templates` key in schema (older server) → pickers absent, nothing crashes. Implement two `EditableField`-based selects (`values` prop from `schema.templates[kind]`, empty value = default) beside the render controls. `npm run typecheck` + `npm test` green; commit `Add per-application template pickers`.

### Task 5: Docs, vault template, demo, verification

**Files:** Modify `.agents/skills/career-evidence/references/document-generation.md` (token + `ce-param`/`ce-kind` contract, full key list), `references/vault-schema.md` (`Resources/Templates/`), `docs/setup.md` (one-sentence trust note: a `.ps` template executes in Ghostscript — treat third-party templates like any program you'd run), `server/assets/vault-template/Resources/Templates/README.md` (new; reconcile with the existing Resources README wording), `demo/build_demo.py` (seed one sample vault template exercising a couple of `ce-param` keys and set it on one demo application)

- [ ] Docs + template + demo seed; rebuild demo; audit exits 0; full gates (`test_safety.py`, typecheck, vitest, `npm run build` + commit bundle); render the demo app's PDF once via the vault template if Ghostscript is present (note if absent). Append a verification section to this plan. Commit `Document and seed the template registry`. Stop — no push, no merge.
