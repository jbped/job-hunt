# Webapp-first: repository restructure and React frontend

Date: 2026-09-02. Status: approved direction, pending spec review.

## Why

The repo has been skills-first: the product was a portable skill set, and the
dashboard grew inside it. The direction is now **webapp-first**: the product
is a local web application over the markdown vault, supplemented by local CLI
AI agents (Claude Code, Codex, Gemini, and any AGENTS.md-reading tool). The
webapp carries the everyday experience; the skills become the integration
layer that lets an agent work the same vault through the same surface.

Unchanged principles: markdown is the database; deterministic wherever
repeatable; agents use the human surface; the server stays Python stdlib-only;
the dashboard binds loopback by default and requires the per-vault token.

Two milestones, in order, each independently verifiable:

1. **0.5 — Webapp-first restructure** (layout only, zero behavior change)
2. **0.6 — React frontend** (feature parity, same design)

The AI-sandbox investigation (agent running *inside* the container,
interacted with through the webapp) stays after both, as 0.7 — the
restructure is deliberately its enabler, not its vehicle.

## Milestone 0.5 — Webapp-first restructure

### Target layout

```
server/                     # the Python application — engine + API + CLI
  serve.py  vaultlib.py  schema.py  audit_vault.py  export_index.py
  capture_jd.py  render_pdf.py  new_application.py  new_person.py
  new_role.py  new_accomplishment.py  new_interview.py  new_lead.py
  init_vault.py  status.py  metrics.py  package_app.py  test_safety.py
  assets/
    templates/              # note + PDF templates, moved as-is
    ui/                     # the served frontend (index.html now; Vite output in 0.6)
ui/                         # created in 0.6 — React source
extension/                  # unchanged
.agents/skills/             # thin skills: SKILL.md + references, no scripts
.claude/skills/             # symlinks into .agents/skills/, unchanged mechanism
demo/  docs/  Dockerfile  compose.yaml
```

### Rules of the move

- `git mv` the flat modules; imports between them do not change. Only the
  root constants move: `SKILL_ROOT` becomes `SERVER_ROOT`
  (`Path(__file__).parent`), templates and UI dirs resolve under
  `server/assets/`. `.env`/repo-root discovery (walk up for `.git`/`.env`)
  is depth-independent and needs no change.
- **Zero behavior change.** Endpoints, token handling, binds, pidfile,
  vault resolution, audit rules — all identical. `test_safety.py` moves to
  `server/` and must pass without weakening; that is the restructure's proof.
- Skills keep their workflows and rules but invoke `server/<script>.py`
  (repo-relative) instead of shipping `scripts/`. They stay host-neutral —
  the neutrality test keeps running over `.agents/skills/`.
- `package_skill.py` becomes `server/package_app.py`: the release zip is the
  application — `server/`, `.agents/skills/`, `extension/`, `docs/`,
  `Dockerfile`, `compose.yaml`, README/CHANGELOG — never `vault/` or any
  `.cache`. The release workflow and archive-portability test update to the
  app-zip contract (no provider-named paths, no vault, runnable from the
  unzipped root).
- Docker: `COPY server/ /app/server`, entrypoint
  `python3 /app/server/serve.py --no-browser`. Same env contract
  (`CAREER_EVIDENCE_VAULT=/vault`, `CAREER_EVIDENCE_BIND` opt-in), same
  loopback-only publish in compose.
- Docs sweep: README, AGENTS.md, docs/setup.md, docs/host-adapters.md,
  references/vault-schema.md, and the generated Field Reference footer all
  point at `server/`. AGENTS.md reframes the repo description webapp-first.
- `demo/build_demo.py` and anything else importing the scripts adjusts its
  `sys.path` to `server/`.

### Verification (0.5)

1. `python3 server/test_safety.py` passes; `python3 server/audit_vault.py`
   exits 0 against the live vault.
2. The dashboard serves and writes exactly as before (manual smoke: create a
   lead, archive, restore, render a demo PDF).
3. `docker compose up --build` works with the new layout.
4. The app zip unpacks and runs (`python3 server/serve.py`) from the
   unzipped root; it contains no vault data and no provider-named paths.
5. A skill invoked in-checkout (e.g. new-application) still walks its
   workflow using `server/` paths.

## Milestone 0.6 — React frontend

Scope: **feature parity with the current page, same visual design.**
Redesigns come afterwards as normal feature work.

- **Stack:** Vite + React 18 + TypeScript strict, in top-level `ui/`.
  No component library; the existing CSS ports wholesale as a global
  stylesheet and components reuse its class names.
- **Data:** TanStack Query over the existing API. The `/api/state`
  fingerprint poll (focus/visibility-driven, as today) invalidates queries.
  Payload types are hand-written in `ui/src/api/types.ts` — UI/server drift
  becomes a compile error.
- **Structure:** one component per view — Now, Leads, Applications (rail +
  viewer), Board, Interviews, People, Evidence, Archived — plus shared
  pieces: note viewer/editor (fingerprint contract intact), schema-driven
  form modal built from `/api/schema` `forms`, inline field editors, toast,
  wikilink navigation. Hash-based view routing via a small hook; no router.
- **Token:** the built `index.html` keeps the `__SESSION_TOKEN__`
  placeholder in an inline script; `serve.py` keeps the same string
  replacement and additionally serves the hashed asset files beside it.
- **Distribution:** the built bundle is committed to `server/assets/ui/`.
  Users never need Node. Contributors run `npm run dev` (Vite proxying
  `/api` to the Python server). CI rebuilds the bundle and fails on drift
  against the committed output.
- **Tests:** vitest + React Testing Library for form generation, fingerprint
  conflict handling, and archive/restore flows; `test_safety.py` continues to
  own the API contract.
- **Exit:** a side-by-side parity walk against the old page, then the
  vanilla `index.html` is deleted. One frontend, one truth.

## Roadmap rewrite (draft for ROADMAP.md)

Framing change: "A local-first job-hunt **webapp** where markdown is the
database — a dashboard you run yourself, supplemented by local CLI AI agents
that work the same vault through the same surface."

- **0.5 — Webapp-first restructure**: the layout above; release artifact
  becomes the app zip.
- **0.6 — React frontend**: parity port, committed bundle, old page retired.
- **0.7 — AI sandbox (investigate)**: agent in a container, interacted with
  through the webapp. Open questions unchanged: subscription auth
  passthrough; preserving conversational back-and-forth (evidence interviews
  are interactive — streaming chat through the webapp is the likely shape).
- **Later**: insights views, interview-prep workflow, submission integrity
  report, LinkedIn importer, multi-profile — now framed as React feature
  work over the same API.
- **Non-goals unchanged**: no cloud service, no accounts, no telemetry, no
  auto-apply, no AI in deterministic steps.

## Decisions log

- Webapp-first supersedes skills-first; skills remain as the AI integration
  layer (user, 2026-09-02).
- Release zip becomes the whole app, not a standalone skill set.
- Sequencing: restructure first, then React; sandbox stays 0.7.
- React runtime needs no Node for users: build-time only, bundle committed.
- TypeScript strict; parity-first scope; `ui/` and `server/` as separate
  top-level directories.
