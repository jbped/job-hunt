# 0.7 — AI sandbox: investigation findings

Date: 2026-09-02. Status: investigation complete, no code changes proposed here.

This is the milestone described in `2026-09-02-webapp-first-design.md` and
`ROADMAP.md`'s 0.7 entry: an AI CLI agent (Claude Code, Codex, Gemini CLI, or
any AGENTS.md-reading tool) running *inside* the app's Docker container,
working the user's vault through the same server surface, interacted with
through the webapp. Non-goals hold throughout: no cloud service, no
accounts, no telemetry.

## 1. Subscription auth passthrough

Researched via web search (cited below); no credential files were opened or
their contents read — paths and mechanisms only.

### Claude Code

- **Mechanism:** browser OAuth (device/browser flow, session persists ~90
  days); `claude setup-token` generates a long-lived OAuth token
  non-interactively for CI/headless use. A separate `ANTHROPIC_API_KEY` env
  var exists but is metered API billing, not the subscription, and silently
  overrides OAuth if set.
- **Host path:** macOS Keychain; on Linux, plaintext `~/.claude/.credentials.json`
  plus `~/.claude.json` for onboarding/config state.
- **Container guidance:** Anthropic's own devcontainer docs and community
  guides document bind-mounting `~/.claude` (+ `~/.claude.json`) into a
  container to reuse host auth, but explicitly warn that with
  `--dangerously-skip-permissions` a malicious project in that container
  could exfiltrate the mounted credentials, and recommend against mounting
  other host secrets (SSH keys, cloud creds) alongside it.
  Sources: [CLI authentication](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/authentication),
  [Authentication](https://code.claude.com/docs/en/authentication),
  [Development containers](https://code.claude.com/docs/en/devcontainer),
  [credential persistence in devcontainers](https://github.com/tfvchow/field-notes-public/issues/10),
  [Using Claude Code Safely with Dev Containers](https://nakamasato.medium.com/using-claude-code-safely-with-dev-containers-b46b8fedbca9).

Locally verified (this host, `claude --version` → `2.1.251`): `--restricted`
mode "confines the file tools to the working directories... refuses
bypassPermissions"; `--bare` mode forces `ANTHROPIC_API_KEY`/`apiKeyHelper`
only and never reads OAuth or keychain — both are directly relevant to a
sandboxed container run and are covered in §3.

### OpenAI Codex CLI

- **Mechanism:** "Sign in with ChatGPT" browser OAuth tied to a ChatGPT
  Plus/Pro subscription (distinct from API-key billing); tokens auto-refresh.
  A device-code flow is documented as the standard pattern specifically for
  containerized/headless environments.
- **Host path:** `~/.codex/auth.json` (plaintext access/refresh tokens);
  OpenAI's docs caution to treat it like a password.
- **Container guidance:** because a device-code flow is vendor-documented for
  containers, a fresh in-container login is the sanctioned path, not
  bind-mounting `auth.json`.
  Sources: [OpenAI authentication docs](https://developers.openai.com/codex/auth.md),
  [Codex CLI Authentication: OAuth, Device Code, API Keys](https://codex.danielvaughan.com/2026/04/01/codex-cli-authentication-flows-credential-management/).

### Google Gemini CLI

- **Mechanism:** "Login with Google" OAuth (`gemini auth login --oauth`),
  recommended for Google AI Pro/Ultra subscribers. Some setups need
  `GOOGLE_CLOUD_PROJECT` even for personal accounts; users report needing to
  re-login every new terminal session on some platforms.
- **Host path:** `~/.gemini/oauth_creds.json` (access/refresh tokens).
- **Container guidance:** no official container-mount docs found (unlike
  Claude Code's devcontainer guide); same file shape as Claude's
  credentials, so the trade-off is the same category, but it is unproven and
  has known session-persistence bugs.
  Sources: [Gemini CLI Authentication Setup](https://google-gemini.github.io/gemini-cli/docs/get-started/authentication.html),
  [re-login every new terminal session, issue #8096](https://github.com/google-gemini/gemini-cli/issues/8096).

### Cross-cutting: the three injection strategies

| Strategy | Trade-off |
|---|---|
| **(a) Bind-mount host config dir, read-only** | Exposes a live, long-lived, high-privilege token to every process the container runs — Anthropic's own docs flag exfiltration risk. Simplest, zero extra friction. Host revocation kills container access too. |
| **(b) Env var injection at container start** | Visible via `docker inspect`, `/proc/*/environ`, `ps -eww`, daemon logs — worse exposure surface than a file with restrictive perms. Not recommended for OAuth-class tokens. |
| **(c) Fresh device-code/browser login inside the container** | No host credential ever enters the container — best isolation, matches this project's no-added-attack-surface stance. Needs outbound network to the auth provider and repeats login on every rebuild. Codex documents this as its container pattern; Claude Code supports it via `setup-token`; Gemini's OAuth is less battle-tested for repeated headless use. |

**Recommendation:** (c) as the default — it is the only option that never
plants a copy of the user's subscription credential inside the sandboxed
container — with (a) as an explicit, clearly-labeled opt-in for people who
accept the trade-off for convenience across rebuilds. (b) is not
recommended for OAuth-class tokens.

## 2. Conversational back-and-forth through the webapp

The evidence interview (`.agents/skills/career-evidence/references/evidence-interview.md`)
is the representative workflow: multi-turn, needs the agent to read notes,
ask batches of questions, and write answers back — a long-lived agent
process, not a single request/response.

### (a) PTY bridge

Python stdlib's `pty` module (Unix-only — fine, the container is Linux) can
spawn a subprocess attached to a pseudo-terminal, giving it real TTY
semantics. But relaying that I/O to a browser needs a bidirectional
low-latency channel, and **`http.server`/`socketserver` have no WebSocket
support at all** — WebSocket is a distinct framed protocol layered on an
HTTP Upgrade handshake (RFC 6455: `Sec-WebSocket-Accept` = base64(SHA1(key +
magic GUID)), then binary frame parsing) that stdlib does not implement.
Getting this without a dependency means hand-rolling the handshake and frame
codec — a few hundred lines of protocol code to own and maintain — or
socket-hijacking through `BaseHTTPRequestHandler`'s underlying connection.
It also implies rendering a real terminal in the browser (an `xterm.js`-class
dependency in `ui/`, which is fine there — `ui/` already takes npm
dependencies — but doesn't fit a conversational "interview" UI as naturally
as chat bubbles do.

### (b) Headless / JSON stream-json modes

Verified directly against the installed CLI (`claude --help`, v2.1.251) —
not guessed:

- `--print`/`-p`: non-interactive, print-and-exit.
- `--output-format stream-json` (only with `--print`): real-time streaming
  JSON output; `--input-format stream-json` (only with `--print`): real-time
  streaming JSON input, "text" is the default for both.
- `--include-partial-messages`: stream partial message chunks as they arrive
  (print + stream-json only).
- `--replay-user-messages`: re-emits user messages from stdin back on stdout
  for acknowledgment (requires stream-json in both directions).
- Session continuity: `-r`/`--resume [session-id]`, `-c`/`--continue`,
  `--session-id <uuid>`, `--fork-session` (new session id on resume),
  `--no-session-persistence` (disable saving, print-mode only).
- Access control for a sandboxed run: `--permission-mode` (`acceptEdits`,
  `auto`, `bypassPermissions`, `manual`, `dontAsk`, `plan`),
  `--allowedTools`/`--disallowedTools`, and **`--restricted`** — removes
  Bash/PowerShell/REPL/code-running tools and `WebFetch` unless explicitly
  named, confines file tools to the working directories (`--add-dir`),
  refuses `bypassPermissions`, and ignores user/project/local settings files.
- Background/session management commands also exist: `--bg`/`--background`,
  `claude attach <id>`, `claude logs <id>`, `claude stop|kill <id>` — a
  session can outlive the calling process, which is relevant to "the user
  closes the tab mid-interview and comes back."

This maps directly onto stdlib capability: spawn `claude -p --output-format
stream-json --input-format stream-json ...` via `subprocess.Popen` (stdlib),
write one JSON object per line to stdin, read one per line from stdout.
**SSE requires no special stdlib support either** — it's an ordinary HTTP
response with `Content-Type: text/event-stream`, held open, with `data:
...\n\n` written and flushed per event; `ThreadingHTTPServer` (already used
in `serve.py`) can hold one thread per open SSE connection without trouble
at this app's scale (one user, a handful of concurrent tabs at most). The
browser's native `EventSource` (or a manual `fetch` + `ReadableStream`)
consumes it with zero new frontend dependencies.

### (c) Claude Agent SDK inside the container

Confirmed via web search (2026-09-02): `pip install claude-agent-sdk`
(Python 3.10–3.13), current release `0.2.152`. It **bundles the Claude Code
CLI itself** and by default authenticates via `ANTHROPIC_API_KEY` — i.e. it
targets the metered API path, not the OAuth subscription flow that
`claude`'s own CLI login uses. It is a pip dependency, which conflicts with
`AGENTS.md`'s stdlib-only constraint for `server/`. It could only live as a
separate process in its own venv inside the Docker image — not part of
`server/` — with the stdlib server proxying to it over a local socket/pipe.
That's two Python runtimes to maintain for a capability (`--output-format
stream-json`) the compiled CLI already exposes via flags.
Sources: [claude-agent-sdk · PyPI](https://pypi.org/project/claude-agent-sdk/),
[Agent SDK reference — Python](https://code.claude.com/docs/en/agent-sdk/python).

### Recommendation

**(b): headless `stream-json`, relayed over SSE-out + POST-in.** It needs no
new stdlib capability (subprocess + a held-open HTTP response are both
already trivial in `http.server`), no hand-rolled WebSocket protocol, no new
frontend dependency, and no pip dependency in `server/`. It also produces
chat-bubble-shaped output naturally, which fits "evidence interview"
conversation better than a raw terminal would. The PTY route (a) is the
right shape only if a truly general terminal (arbitrary interactive
commands, not one workflow) becomes the goal; the Agent SDK (c) buys nothing
over the CLI's own flags for this project's scope and costs a dependency
boundary the CLI in headless mode already avoids.

## 3. Sandbox boundary

What already governs this repo's trust model, from `serve.py` and
`test_safety.py`: the dashboard's own write surface is a *closed* set of
guarded operations (`resolve()` refuses vault escapes, `UI_READONLY_FILES`
blocks `Job Description.md`/`Submission Notes.md`, fingerprints prevent
clobbering concurrent edits) — but an AI CLI agent working the vault
directly (as `AGENTS.md` already assumes on the host, outside Docker) has
raw filesystem access to `/vault`, which is *more* privileged than the
HTTP API. Containerizing the agent doesn't need to narrow that below what a
host-run CLI already has — the vault is the agent's legitimate workspace
either way, and `audit_vault.py` is the existing after-the-fact check on
hand-shaped or agent-shaped notes alike. The new surface a container adds is
everything *beyond* the vault: the container's own filesystem, and network.

**What the agent can already reach today (Dockerfile + compose.yaml):**
runs as `${UID:-1000}:${GID:-1000}` (good — matches host vault ownership),
binds `0.0.0.0:8765` inside the container but compose publishes only on
`127.0.0.1` on the host — no bind-mount beyond `/vault` exists yet, and
there is no `network: none` or egress restriction, so the container has
ordinary outbound internet access by default (bridge network). That's
necessary for the CLI to reach the auth provider and the model API at all,
but it also means a full agentic coding CLI's tool surface — Bash, WebFetch
— would have both filesystem and network reach if left at defaults. A job
posting captured verbatim into the vault is attacker-controlled text
(anyone can write a job description); once an agent reads it as context,
that's a live prompt-injection surface if the agent also has Bash/WebFetch
available.

**Recommended Docker-level controls for 0.7:**

- Keep the existing loopback-only publish and matched-UID user (already in
  place, don't regress).
- `--restricted --add-dir /vault` on the agent invocation: drops
  Bash/PowerShell/REPL/code-running tools and `WebFetch` unless named,
  confines file tools to `/vault`. For an evidence interview specifically —
  pure Q&A that writes markdown — no code execution is needed, so ship with
  Bash and WebFetch both off by default.
- `--cap-drop=ALL` and a read-only root filesystem for the container, with
  `/vault` as the one writable mount (plus a small `tmpfs` for scratch if
  the agent needs one) — nothing the agent does should be able to persist
  outside the vault or the container's ephemeral layer.
- No other host directories mounted alongside whatever auth mechanism is
  chosen (echoing Anthropic's own devcontainer warning against mounting SSH
  keys/cloud creds next to `~/.claude`).
- Network: full egress allowlisting (only the model/auth provider's
  endpoints) is the tightest control but needs a proxy or iptables rules in
  the image — worth flagging as an open question (§4) rather than assuming
  it's in scope for a first slice, since `--restricted` already removes the
  agent's own means of making arbitrary outbound requests; the only traffic
  left is the CLI-to-provider channel the feature requires to function at
  all.

## 4. Proposed 0.7 scope cut

**Smallest end-to-end slice:** one CLI (Claude Code — already installed,
flags verified above), one workflow (the evidence interview), one streaming
surface.

- Docker image adds the `claude` CLI binary (no `pip install`, keeps
  `server/` stdlib-only).
- Auth: fresh in-container login (§1 option c) as the shipped default;
  `claude setup-token` or a documented bind-mount as an explicit opt-in
  later, not in the first slice.
- Server adds one new POST route (start/continue a turn, JSON body,
  token-gated exactly like every existing write route) and one SSE GET
  route, spawning `claude -p --output-format stream-json --input-format
  stream-json --restricted --add-dir /vault --permission-mode <mode>
  --resume <session-id>` per conversation and relaying JSON-line events to
  the open SSE connection.
- Frontend: a chat view reusing the existing token/POST plumbing plus one
  `EventSource` consumer — no new npm dependency needed for the minimal
  slice.
- Test only against the demo vault (`python3 demo/build_demo.py --force`)
  end to end before ever pointing at a live vault.

**Open questions for the user, unresolved by this investigation:**

1. Ship the in-container-login default (safer, more friction on every
   rebuild) or the host-credential bind-mount default (convenient, exposes
   a long-lived token to the container) — or make it a choice the user sees
   at setup time?
2. Scope 0.7 to Claude Code only, or does the first slice need to prove the
   pattern is portable to Codex/Gemini too (their flags/streaming modes
   were not verified against a locally installed binary the way Claude
   Code's were)?
3. Chat bubbles (recommended, §2) vs. a real terminal-in-browser — confirm
   the conversational-interview framing is the right one before any PTY
   work is considered.
4. Should the sandboxed agent ever get Bash/WebFetch for *some* future
   workflow (e.g. an insights or submission-integrity workflow that needs
   to fetch a posting URL), or should those stay off by policy across all
   0.7-and-later agent workflows, not just the evidence interview?
5. Session lifecycle: one subprocess per open browser tab, torn down on
   disconnect, or a longer-lived background session (`claude --bg` /
   `attach` / `--resume`) that survives a closed tab so an interview can be
   picked back up later?
6. Is network egress allowlisting (beyond `--restricted`) in scope for 0.7,
   or explicitly deferred hardening for a later milestone?
