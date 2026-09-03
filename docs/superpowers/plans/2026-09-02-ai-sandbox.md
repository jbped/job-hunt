# AI Sandbox (0.7) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

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

- [ ] Failing tests first: POST without token → 403; spawn args always contain `--restricted` and `--add-dir <vault>` (assert on a captured spawn, stub bin); stream of a stubbed session yields the stub's events then the sentinel; unknown session → 404; index persists across a registry reload; corrupt index file → empty, no crash; no `shell=True` anywhere in `agent_sessions.py`/the new routes (assert by reading the source, mirroring the existing no-destructive-route test style).
- [ ] Implement; suite green; commit `Add agent session core and routes`.

### Task 2: Interview seeding and lifecycle

**Files:** Modify `server/agent_sessions.py`, `server/serve.py`; test `server/test_safety.py`

- [ ] New sessions get `--append-system-prompt` with a short pointer: the agent is conducting the evidence interview; read `.agents/skills/career-evidence/references/evidence-interview.md` and the vault's dashboards before asking questions; write only vault markdown. (Compose the pointer text in one module constant; do not copy workflow content into it.) Continuations skip it (`--resume` carries context).
- [ ] Lifecycle: closing a conversation (`POST /api/agent/interview` with `{session_id, close: true}`) terminates the subprocess (terminate → kill escalation, bounded wait); server shutdown reaps all live sessions (hook into the existing shutdown path near the pidfile cleanup); the index survives (persisted), only live handles die.
- [ ] Tests: close terminates the stub process (poll() non-None); a second POST to a closed session respawns with `--resume`; shutdown reaps.
- [ ] Suite green; commit `Seed the interview and manage session lifecycle`.

### Task 3: The Interview chat UI

**Files:**
- Create: `ui/src/views/InterviewChatView.tsx` (+ `ui/src/views/interview-chat/` pieces as needed), test file
- Modify: `App.tsx` + `useHashView` (`View` union gains `"agent"`, nav label "AI Interview"), `ui/src/api/types.ts`

- [ ] Failing tests: session list renders from a `/api/agent/sessions` fixture; sending a message POSTs `{message, session_id?}`; incoming SSE events render as assistant bubbles (mock `EventSource`); a `done` sentinel re-enables the input.
- [ ] Implement: left column = previous conversations (from the sessions route, newest first) + "New interview"; main column = chat bubbles (assistant markdown through the existing renderer, user plain), streaming text as partial events arrive, input disabled while a turn is open; reopening a listed session resumes it. Reuse existing classes (`.split .rail .pick .card .stack`) — no new visual language.
- [ ] `npm run typecheck` + `npm test` green; commit `Add the interview chat view`.

### Task 4: Docker — CLI, auth seeding, hardening

**Files:** Modify `Dockerfile`, `compose.yaml`, create `docker/entrypoint.sh` (or extend the existing entrypoint mechanism)

- [ ] Dockerfile: `COPY .agents/skills /app/.agents/skills` (the interview reference must exist in-image); install the Claude Code standalone binary (verify the official standalone install path and pin a version; no npm/pip in the final image — a build stage is fine); set `CLAUDE_CONFIG_DIR=/agent-home/.claude`.
- [ ] compose.yaml: named volume `agent-home` mounted at `/agent-home` (CLI config + session storage — survives restarts per the spec's decision 5); host credentials mounted read-only at `/host-claude` (path from env `CAREER_EVIDENCE_CLAUDE_DIR`, default `~/.claude`); entrypoint seeds `/agent-home/.claude` from `/host-claude` when the volume is empty (copy credentials only — `.credentials.json` and the minimal config the CLI needs; verify which files by testing) then execs the server. Hardening: `cap_drop: [ALL]`, `read_only: true`, `tmpfs: /tmp`, keep loopback publish + matched UID; `/vault` and `/agent-home` are the only writable mounts.
- [ ] Verify: `docker compose build`; with the demo vault, container starts, `/api/schema` responds; `claude --version` inside the container works (`docker compose exec`); a container WITHOUT the host-claude mount starts the server fine and `POST /api/agent/interview` returns the documented clear error (agent binary unauthenticated) rather than hanging — implement that error path if the CLI's failure mode is a hang.
- [ ] Commit `Ship the agent CLI in the container with seeded auth`.

### Task 5: Docs, end-to-end verification

**Files:** Modify `docs/setup.md` (auth trade-off + alternative in-container `claude setup-token` flow, per spec decision 1), `AGENTS.md` (one paragraph: the sandbox exists, `--restricted`, after-the-fact audit stance), `README.md` (feature mention); verification section in this plan

- [ ] Docs; full gates (`test_safety.py`, typecheck, vitest, `npm run build` + commit bundle).
- [ ] Manual end-to-end (the one place the real CLI runs): host-mode first — `python3 server/serve.py --vault demo/vault`, open the chat, run a two-turn interview against the demo vault, confirm an accomplishment note lands and `audit_vault.py` exits 0; then Docker-mode the same. Record both in the verification section, including anything unverifiable in your environment (e.g. if you cannot complete an interactive interview, script the turns via curl + the SSE stream and record transcripts).
- [ ] Commit `Document and verify the AI sandbox`. Stop — no push, no merge.
