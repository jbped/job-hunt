# AI sandbox (milestone 0.7): the evidence interview through the webapp

Date: 2026-09-02. Status: approved direction, pending spec review.
Parent: `webapp-first-epic`. Grounding:
`2026-09-02-ai-sandbox-investigation.md` (all technical claims there were
verified against the installed CLI or cited current docs; this spec only
decides among the options it laid out).

## What ships

The smallest end-to-end slice: **Claude Code, running inside the app's
Docker container, conducting the evidence interview through a chat panel
in the webapp.** One CLI, one workflow, one streaming surface. Portability
to Codex/Gemini is a later milestone once the pattern is proven.

Decisions (user, 2026-09-02), resolving the investigation's open
questions:

1. **Auth: bind-mount the host's Claude config** (read-only where the CLI
   tolerates it) as the shipped default; a fresh in-container
   `setup-token` login is the documented alternative for users who want
   zero host-credential exposure. The investigation's exfiltration
   caution is mitigated by the rest of this spec: `--restricted` (no
   Bash, no WebFetch), `--cap-drop=ALL`, read-only rootfs, nothing else
   mounted beside the vault and the auth path, and `docs/setup.md`
   stating the trade-off plainly.
2. **Scope: Claude Code only** for 0.7.
3. **UI: chat bubbles**, not a terminal. No PTY work.
4. **Tools: files-in-vault only** — `--restricted --add-dir /vault`,
   Bash and WebFetch off. This is policy for all 0.7-era agent
   workflows, not just the interview; any future workflow wanting more
   must argue for it in its own spec.
5. **Lifecycle: per-conversation** — a session starts when the interview
   chat opens and its subprocess ends when the conversation is closed
   (or the server stops); the CLI's `--resume <session-id>` makes a
   closed interview resumable within the CLI's retention window. No
   always-on daemon.
6. **Egress: deferred hardening.** The container keeps ordinary outbound
   access (the CLI must reach its provider); `--restricted` already
   removes the agent's own ability to make arbitrary requests.
   Endpoint allowlisting is a later-milestone hardening task, recorded
   as a non-goal here.

## Architecture

- **Container:** the existing image gains the `claude` CLI binary (no
  pip installs — `server/` stays stdlib-only). Compose adds the
  read-only auth mount and hardening: `cap_drop: [ALL]`, `read_only:
  true` rootfs with `/vault` writable and a small tmpfs for scratch,
  matched UID, loopback-only publish — all per the investigation §3.
- **Server (stdlib only):** two new routes.
  - `POST /api/agent/interview` — token-gated like every write route.
    Starts or continues a conversation: spawns
    `claude -p --output-format stream-json --input-format stream-json
    --restricted --add-dir /vault` (with `--resume <session-id>` on
    continuation) via `subprocess.Popen`, writes the user turn as a
    JSON line to stdin. Body: `{message, session_id?}`; response:
    `{session_id}`.
  - `GET /api/agent/stream?session=<id>` — SSE (`text/event-stream`,
    held-open response on the existing `ThreadingHTTPServer`), relaying
    the subprocess's JSON-line events as SSE `data:` events until the
    turn completes. No WebSocket, no new server dependency.
  - Session registry: in-memory map session-id → subprocess handle,
    per-conversation lifecycle, cleaned up on close/exit. Vault writes
    happen only by the agent through its file tools inside `/vault`;
    the server's own write surface is unchanged.
- **Interview prompt:** the conversation is seeded with the
  evidence-interview workflow from the career-evidence skill (the skill
  stays the source of truth; the server passes a pointer/system prompt,
  it does not fork the workflow text).
- **Frontend:** a new Interview chat panel — streamed assistant turns
  rendered as chat bubbles (reusing the existing markdown renderer),
  a user input box, session resume on reopen. Native `EventSource` +
  the existing POST plumbing; no new npm dependency.
- **Safety tests:** `test_safety.py` gains: the agent routes are
  token-gated; the spawn arguments always include `--restricted` and
  confine `--add-dir` to the vault; the stream route refuses unknown
  session ids; no route ever passes user input into a shell (args list,
  never `shell=True`).

## Trust model (explicit)

The vault is the agent's legitimate workspace — a host-run CLI already
has more access than this container will. The new, deliberately narrow
surface is: the mounted auth credential (mitigated per decision 1) and
provider egress (decision 6). Job postings in the vault are
attacker-controlled text; `--restricted` with no Bash/WebFetch is the
standing mitigation that a prompt-injected agent has no tools to act on
beyond writing vault markdown, which `audit_vault.py` already checks
after the fact.

## Verification

- Demo vault only, end to end, before any live-vault use: build demo,
  `docker compose up`, open the interview, complete a short interview
  that writes an accomplishment note, confirm the note and audit exit 0.
- Kill-switch behavior: closing the conversation terminates the
  subprocess; `docker compose down` leaves no orphan sessions.
- `test_safety.py` additions pass; existing suite unweakened.
- A container without the auth mount fails with a clear, documented
  error pointing at `docs/setup.md`.

## Non-goals (0.7)

- Codex/Gemini support; egress allowlisting; terminal-in-browser; any
  agent workflow beyond the evidence interview; the Agent SDK; running
  the agent against a live vault as part of this milestone's testing.
