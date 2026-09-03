# AI Sandbox (0.7) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** The evidence interview runs as Claude Code inside the app's Docker container, driven from a chat panel in the webapp, with all previous conversations listed and resumable.

**Architecture:** The stdlib server spawns `claude -p` with `stream-json` on both ends per conversation, relays agent events over SSE, accepts user turns via a token-gated POST, and persists a session index in the vault's `.cache/`. The agent runs `--restricted --add-dir /vault`. Tests never spawn the real CLI — a stub agent binary (env override) keeps the suite hermetic; the real CLI is exercised in manual verification only.

**Tech Stack:** Python stdlib server (unchanged rule), React/TS, Claude Code CLI (standalone binary in the Docker image — no pip, no npm in `server/`).

**Spec:** `docs/superpowers/specs/2026-09-02-ai-sandbox-design.md` (all six decisions + both amendments). Technical grounding: `docs/superpowers/specs/2026-09-02-ai-sandbox-investigation.md` — flags verified against `claude` v2.1.251.

## Global Constraints

- `python3 server/test_safety.py` unweakened + green, `npm run typecheck` + `npm test` green before every commit; bundle rebuilt in the final task.
- Agent spawns ALWAYS carry `--restricted` and confine `--add-dir` to the vault; args are a list, never `shell=True`; no route ever interpolates user input into a command line.
- The server never writes vault notes on the agent's behalf; its own write surface is unchanged.
- Tests and experiments: demo vault only. Never spawn the real CLI in tests (token cost, nondeterminism) — use the stub.
- Branch `feat-ai-sandbox` in your worktree; commit per task; never push or merge. `cd ui && npm install` first.
- The interview workflow text stays owned by `.agents/skills/career-evidence/references/evidence-interview.md` — point at it, never fork it.

## Ground truth

- Verified CLI flags (v2.1.251, from the investigation): `-p/--print`, `--output-format stream-json`, `--input-format stream-json` (both print-only), `--include-partial-messages`, `--resume <session-id>`, `--session-id <uuid>`, `--restricted` (drops Bash/WebFetch/code tools, confines file tools to working dirs + `--add-dir`, refuses bypassPermissions, ignores settings files), `--append-system-prompt`. Re-verify against `claude --help` before relying on any.
- `serve.py`: `ThreadingHTTPServer`; GET routes in `do_GET`, POST via `HANDLERS` dict with token gate + JSON content-type enforcement; SSE = ordinary held-open response, `Content-Type: text/event-stream`, flush per `data: ...\n\n`. `_serve_asset`/`resolve` use `vaultlib.resolve_within`.
- `.cache/` in the vault already holds `serve.pid`, `session-token`, `vault-index.json` — the session index joins them (`agent-sessions.json`).
- Dockerfile COPYs only `server/`; entrypoint `python3 /app/server/serve.py --no-browser`; compose publishes `127.0.0.1:8765`, mounts the vault, matched UID. **The image has no `.agents/skills/` and no `claude` today.**
- UI: views registered in `App.tsx` + `useHashView`'s `View` union; `api()` client attaches the token on POST; markdown renderer exported from `ui/src/lib/markdown.tsx`; `EventSource` needs no token (GET), so the stream route must require the session id AND reject cross-origin like the existing routes.
- Claude Code standalone install: the official install script (`https://claude.ai/install.sh`) produces a self-contained binary — verify the current mechanism and pin a version in the Dockerfile. Its config dir is overridable via `CLAUDE_CONFIG_DIR` (verify with `claude --help`/docs); session storage lives under that config dir.

---

### Task 1: Agent session core — registry, routes, stub-tested

**Files:**
- Create: `server/agent_sessions.py`, `server/testdata/stub_agent.py` (the fake CLI)
- Modify: `server/serve.py` (three routes), `server/schema.py` if any constant belongs there
- Test: `server/test_safety.py`

**Interfaces:**
- Produces: `agent_sessions.py` module —
  - `AgentSession` (session id, title, application context, created/updated timestamps, subprocess handle when live)
  - `registry(vault)`: loads/saves the index at `vault/.cache/agent-sessions.json` (atomic write; corrupt/missing file → empty list, never a crash)
  - `spawn(vault, session, message, agent_bin)` → Popen with args exactly: `[agent_bin, "-p", "--output-format", "stream-json", "--input-format", "stream-json", "--include-partial-messages", "--restricted", "--add-dir", str(vault), ...]` plus `--resume <id>` on continuation; cwd = the repo/app root (so the skill reference is readable); `agent_bin` from env `CAREER_EVIDENCE_AGENT_BIN` (default `"claude"`).
- Routes:
  - `POST /api/agent/interview` `{message, session_id?, application?}` → `{session_id}` (starts or continues; title = first message truncated; index updated)
  - `GET /api/agent/stream?session=<id>` → SSE relaying the subprocess's stdout JSON lines as `data:` events, ending with a `data: {"type":"done"}` sentinel when the turn completes; 404 unknown id; same origin rules as existing routes
  - `GET /api/agent/sessions` → the persisted index (newest first)
- Stub: `stub_agent.py` — executable script speaking just enough stream-json (accepts a line on stdin, emits two assistant events + a result event, exits); tests set `CAREER_EVIDENCE_AGENT_BIN` to it.

- [x] Failing tests first: POST without token → 403; spawn args always contain `--restricted` and `--add-dir <vault>` (assert on a captured spawn, stub bin); stream of a stubbed session yields the stub's events then the sentinel; unknown session → 404; index persists across a registry reload; corrupt index file → empty, no crash; no `shell=True` anywhere in `agent_sessions.py`/the new routes (assert by reading the source, mirroring the existing no-destructive-route test style).
- [x] Implement; suite green; commit `Add agent session core and routes`.

### Task 2: Interview seeding and lifecycle

**Files:** Modify `server/agent_sessions.py`, `server/serve.py`; test `server/test_safety.py`

- [x] New sessions get `--append-system-prompt` with a short pointer: the agent is conducting the evidence interview; read `.agents/skills/career-evidence/references/evidence-interview.md` and the vault's dashboards before asking questions; write only vault markdown. (Compose the pointer text in one module constant; do not copy workflow content into it.) Continuations skip it (`--resume` carries context).
- [x] Lifecycle: closing a conversation (`POST /api/agent/interview` with `{session_id, close: true}`) terminates the subprocess (terminate → kill escalation, bounded wait); server shutdown reaps all live sessions (hook into the existing shutdown path near the pidfile cleanup); the index survives (persisted), only live handles die.
- [x] Tests: close terminates the stub process (poll() non-None); a second POST to a closed session respawns with `--resume`; shutdown reaps.
- [x] Suite green; commit `Seed the interview and manage session lifecycle`.

### Task 3: The Interview chat UI

**Files:**
- Create: `ui/src/views/InterviewChatView.tsx` (+ `ui/src/views/interview-chat/` pieces as needed), test file
- Modify: `App.tsx` + `useHashView` (`View` union gains `"agent"`, nav label "AI Interview"), `ui/src/api/types.ts`

- [x] Failing tests: session list renders from a `/api/agent/sessions` fixture; sending a message POSTs `{message, session_id?}`; incoming SSE events render as assistant bubbles (mock `EventSource`); a `done` sentinel re-enables the input.
- [x] Implement: left column = previous conversations (from the sessions route, newest first) + "New interview"; main column = chat bubbles (assistant markdown through the existing renderer, user plain), streaming text as partial events arrive, input disabled while a turn is open; a listed session is inert when opened — no subprocess spawns until the user sends a message (or hits an explicit Resume), which is what triggers the `--resume` spawn. Nothing auto-resumes on server restart. Reuse existing classes (`.split .rail .pick .card .stack`) — no new visual language.
- [x] `npm run typecheck` + `npm test` green; commit `Add the interview chat view`.

### Task 4: Docker — CLI, auth seeding, hardening

**Files:** Modify `Dockerfile`, `compose.yaml`, create `docker/entrypoint.sh` (or extend the existing entrypoint mechanism)

- [x] Dockerfile: `COPY .agents/skills /app/.agents/skills` (the interview reference must exist in-image); install the Claude Code standalone binary (verify the official standalone install path and pin a version; no npm/pip in the final image — a build stage is fine); set `CLAUDE_CONFIG_DIR=/agent-home/.claude`.
- [x] compose.yaml: named volume `agent-home` mounted at `/agent-home` (CLI config + session storage — survives restarts per the spec's decision 5); host credentials mounted read-only at `/host-claude` (path from env `CAREER_EVIDENCE_CLAUDE_DIR`, default `~/.claude`); entrypoint seeds `/agent-home/.claude` from `/host-claude` when the volume is empty (copy credentials only — `.credentials.json` and the minimal config the CLI needs; verify which files by testing) then execs the server. Hardening: `cap_drop: [ALL]`, `read_only: true`, `tmpfs: /tmp`, keep loopback publish + matched UID; `/vault` and `/agent-home` are the only writable mounts.
- [x] Verify: `docker compose build`; with the demo vault, container starts, `/api/schema` responds; `claude --version` inside the container works (`docker compose exec`); a container WITHOUT the host-claude mount starts the server fine and `POST /api/agent/interview` returns the documented clear error (agent binary unauthenticated) rather than hanging — implement that error path if the CLI's failure mode is a hang.
- [x] Commit `Ship the agent CLI in the container with seeded auth`.

### Task 5: Docs, end-to-end verification

**Files:** Modify `docs/setup.md` (auth trade-off + alternative in-container `claude setup-token` flow, per spec decision 1), `AGENTS.md` (one paragraph: the sandbox exists, `--restricted`, after-the-fact audit stance), `README.md` (feature mention); verification section in this plan

- [x] Docs; full gates (`test_safety.py`, typecheck, vitest, `npm run build` + commit bundle).
- [x] Manual end-to-end (the one place the real CLI runs): host-mode first — `python3 server/serve.py --vault demo/vault`, open the chat, run a two-turn interview against the demo vault, confirm an accomplishment note lands and `audit_vault.py` exits 0; then Docker-mode the same. Record both in the verification section, including anything unverifiable in your environment (e.g. if you cannot complete an interactive interview, script the turns via curl + the SSE stream and record transcripts).
- [x] Commit `Document and verify the AI sandbox`. Stop — no push, no merge.

---

## Verification (2026-09-02, branch `feat-ai-sandbox`)

Gates, run before each commit and again at the end:

- `python3 server/test_safety.py` — 85 tests, OK. Was 70 before this branch;
  nothing existing was weakened or skipped.
- `cd ui && npm run typecheck` — clean; `npm test` — 10 files, 33 tests passed
  (was 9/29).
- `cd ui && npm run build` — bundle rebuilt and committed; the built
  `index.html` still carries exactly one `__SESSION_TOKEN__` placeholder.
- `python3 server/audit_vault.py --vault demo/vault` — 0 errors, 0 warnings,
  exit 0, after both end-to-end interviews.

### Ground truth that differed from the plan

Three flags the plan's argv did not have, all verified against `claude`
2.1.251 and all required for the feature to work at all:

1. `--verbose`. `-p --output-format stream-json` is refused without it:
   *"When using --print, --output-format=stream-json requires --verbose"*.
2. `--permission-mode acceptEdits`. Headless there is nobody to approve a
   write, so every one is denied — a run asked to create a file returned
   `permission_denials: [{tool_name: "Write", ...}]` and wrote nothing. With
   `acceptEdits` the same run wrote the file and denied nothing.
   `--restricted` still refuses `bypassPermissions`, which is the mode that
   would have mattered.
3. `--tools Read,Write,Edit,Glob,Grep` plus `--strict-mcp-config`.
   `--restricted` alone does **not** deliver decision 4's "files-in-vault
   only": the init event of a restricted run listed `Task`, `WebSearch`,
   `SendMessage`, `PushNotification`, the `Cron*` tools and more, and — on the
   host — it loaded the caller's MCP servers, so a run that should have
   touched nothing but markdown was offered eleven Google Drive tools. Naming
   the tools and adding `--strict-mcp-config` reduces the init event to
   exactly `['Edit', 'Glob', 'Grep', 'Read', 'Write']` with `mcp_servers: []`,
   host and container alike, and the agent still writes.

Also: the Claude Code install script (`https://claude.ai/install.sh`) always
takes `latest` and installs into `$HOME`, which cannot be pinned. The
Dockerfile therefore does what the script does internally — read
`manifest.json` for the pinned version, download that platform's binary,
verify its SHA-256 — so the image is reproducible at 2.1.251, the version
these flags were checked against.

### Host mode, real CLI, demo vault

`python3 server/serve.py --vault demo/vault --detach`, then a two-turn
interview driven through the real HTTP surface (POST `/api/agent/interview`,
SSE `/api/agent/stream`) exactly as the chat panel does it. Scripted rather
than clicked — this environment has no browser — with the transcript read off
the live stream.

- Turn 1 (an accomplishment with a metric and its provenance): the agent read
  `Job Hunt Dashboard.md`, both role notes, two existing accomplishments,
  `Preferences/README.md`, `Working Notes/Open Questions.md` and the skill's
  `references/vault-schema.md`, then wrote
  `Career Evidence/Accomplishments/Initech 2025/Checkout Latency Reduction.md`
  and indexed it in `Working Notes/Open Questions.md`.
- Turn 2 (answers plus "write the note"): it filed the metric with class,
  source, denominator and period intact, set `status: partial` rather than
  `verified`, and — the part worth recording — refused to attach the work to a
  role: no role note covers 2025, so it left `role:` blank, said so, and made
  it question 1 instead of guessing. It also declined to derive a percentage
  from the two latency numbers because it had not been given one.
- `audit_vault.py` — 0 errors, 0 warnings, exit 0.
- Closing the conversation left no agent process behind (`pgrep` for the spawn
  found none).

### Docker mode, real CLI, demo vault rebuilt from scratch

`demo/build_demo.py --force`, then `docker compose up -d --build`, same two
turns.

- `claude --version` inside the container: `2.1.251 (Claude Code)` — the
  pinned build.
- The entrypoint copied `.credentials.json` out of the read-only
  `/host-claude` mount on first start; `claude auth status` in the container
  reported `loggedIn: true`, `authMethod: claude.ai`. That one file is all the
  seeding the CLI needs — nothing else from `~/.claude` is copied.
- The agent read `/app/.agents/skills/career-evidence/references/vault-schema.md`
  and wrote the same note under `/vault`, owned by the host UID.
  `audit_vault.py` — 0 errors, 0 warnings, exit 0.
- Hardening held: `touch /app/x` → *"Read-only file system"*; the init event
  listed the five file tools and `mcp_servers: []`.
- **Resume across a container restart:** `docker compose restart`, then
  opening the same session id on the stream yielded `['idle', 'done']` and
  spawned nothing; posting a turn resumed it, and the agent answered a
  question about the earlier conversation correctly (*"1.8s"*) — so
  `--resume` really is surviving on the `agent-home` volume, and it only
  happens when a person asks.
- `docker compose down` left no containers and therefore no orphan sessions.

### The no-credentials container

Brought up with `CAREER_EVIDENCE_CLAUDE_DIR` pointing at an empty directory
and a fresh volume. The entrypoint printed the documented warning pointing at
`docs/setup.md`, the dashboard served normally, and `POST
/api/agent/interview` did **not** hang: the CLI answered in about a second
with an assistant message and an errored result reading *"Not logged in ·
Please run /login"*, which the chat renders as an error bubble with a pointer
to `docs/setup.md` underneath. The server's own `AgentUnavailable` path (a
502 naming `docs/setup.md`) covers the harsher case where the binary is
missing or dies outright, and is tested with a stub that exits non-zero.

### Known limits, recorded rather than fixed

- **The agent can write to the app root in host mode.** The plan sets the
  spawn's cwd to the repo root so the skill reference is readable, and
  `--restricted` confines the file tools to the working directories — which
  means cwd as well as `--add-dir`. In Docker that is harmless: `/app` is on
  the read-only root filesystem, verified above. Run on the host, the agent
  could in principle write to the checkout. Tightening it means either
  running with cwd inside the vault and inlining the reference (which the
  plan explicitly forbids — the skill stays the source of truth) or a
  read-only working-directory flag the CLI does not have. Flagged for a
  follow-up.
- **Transcripts are not persisted by the dashboard.** Reopening a
  conversation shows an empty panel and a line saying so; the history lives
  with the CLI and comes back through `--resume`, not through the UI. That is
  spec decision 5's caveat working as intended, but it is the most visible
  rough edge.
- **Egress is unrestricted**, per decision 6. `--restricted` plus the tool
  allowlist means the agent has no tool that reaches the network; the CLI's
  own provider traffic is untouched.
