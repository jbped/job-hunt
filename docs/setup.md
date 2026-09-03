# Setup

Everything runs from a plain checkout: the scripts are Python 3 standard
library only, and the dashboard is a single local server. The optional pieces
are Ghostscript + poppler (PDF rendering), Obsidian (reading the vault as a
vault), and Docker (running the dashboard without installing anything else).

| Requirement | Needed for | Notes |
| --- | --- | --- |
| Python 3.11+ | everything | stdlib only, no pip installs |
| git | getting the code | Windows: see the symlink note below |
| Ghostscript + poppler | PDF rendering only | optional; the Docker image bundles them |
| Obsidian | browsing the vault | optional; the notes are plain markdown |
| Docker | the packaged dashboard | optional; local packaging, not a service |

## Linux and macOS

```sh
git clone https://github.com/jbped/job-hunt.git
cd job-hunt
cp .env.example .env      # set CAREER_EVIDENCE_VAULT to where your vault should live
python3 server/init_vault.py   # first time only
python3 server/serve.py        # opens the dashboard on http://127.0.0.1:8765
```

PDF tooling:

- macOS: `brew install ghostscript poppler`
- Debian/Ubuntu: `sudo apt install ghostscript poppler-utils`
- Arch: `sudo pacman -S ghostscript poppler`

Nothing else on macOS needs special handling — no shipped binaries, so
Gatekeeper has nothing to quarantine; python3 comes from the Xcode command
line tools or Homebrew.

## Windows

Three things differ, and the Docker route below sidesteps all of them:

1. **Symlinks.** `.claude/skills/` holds symlinks into `.agents/skills/`.
   Git only recreates them with Developer Mode enabled **and**
   `git config --global core.symlinks true` set **before** cloning (re-clone
   if it was off). Without them the scripts and dashboard still work fully;
   only the Claude Code skill discovery in this checkout is affected — WSL or
   the release zip (real files) are alternatives.
2. **PDF tooling.** The Ghostscript installer ships `gswin64c`, not the
   `ps2pdf` wrapper — the render script probes for it, so a standard install
   works once Ghostscript's `bin` is on `PATH`. Install poppler via
   `winget install poppler` (or chocolatey, or the poppler-windows release)
   and verify with `where pdftotext`.
3. **Token file mode.** The write token at `<vault>\.cache\session-token`
   is created with owner-only permissions where the OS supports it; on NTFS
   that mode is advisory.

The commands above translate directly to PowerShell (`python` instead of
`python3` if that is how Python is on `PATH`; `copy .env.example .env`).

## Docker (any OS)

The image packages the dashboard server with Ghostscript and poppler; your
vault stays on the host as plain markdown, mounted read-write, and Obsidian
keeps working on the same files while the container runs.

```sh
# fish
set -gx CAREER_EVIDENCE_VAULT_HOST /absolute/path/to/your/vault
# bash/zsh: export CAREER_EVIDENCE_VAULT_HOST=/absolute/path/to/your/vault

docker compose up --build
```

The dashboard answers on `http://127.0.0.1:8765`, and compose publishes the
port on the host's loopback only — nothing is reachable from the network.
Inside the container the server binds its own interface via the
`CAREER_EVIDENCE_BIND` opt-in the image sets; run bare, it binds `127.0.0.1`
and nothing else. `compose.yaml` maps the container user to UID/GID 1000 by
default so vault files keep your ownership; set `UID`/`GID` if yours differ.

The write token lives at `<vault>/.cache/session-token` and survives
restarts, so the browser extension pairs once. Re-roll it by running
`serve.py --new-token`, or delete the file — `.cache/` is derived and
disposable. The token is also printed nowhere; copy it from the dashboard's
**Pair extension** button or the file itself.

## The AI interview (Docker)

The image also carries the Claude Code CLI, and the dashboard's **AI
Interview** tab runs the evidence interview through it. The agent works your
vault directly — it reads and writes markdown under `/vault` and has nothing
else: no shell, no web access, no MCP servers, and a read-only container
filesystem outside the vault. What it writes is checked the same way anything
hand-written is, by `python3 server/audit_vault.py` and the audit banner.

It needs credentials, and there are two ways to give it some. Pick one
deliberately — the difference is real:

1. **Mount your host credentials (the default).** `compose.yaml` mounts
   `~/.claude` read-only at `/host-claude`, and the entrypoint copies one
   file — `.credentials.json` — into the container's own volume the first
   time it starts. Convenient, and it survives rebuilds. The trade-off:
   a live, long-lived credential for your Claude subscription now exists
   inside the container. The controls above are what keep it there, and
   Anthropic's own dev-container guidance says the same thing — don't mount
   other secrets (SSH keys, cloud credentials) beside it. Point
   `CAREER_EVIDENCE_CLAUDE_DIR` at a different directory if your config
   lives elsewhere.
2. **Log in inside the container instead.** Point
   `CAREER_EVIDENCE_CLAUDE_DIR` at an empty directory so nothing is copied,
   then run `docker compose exec dashboard claude setup-token` and follow
   the prompts. No host credential ever enters the container; the token it
   creates lives on the `agent-home` volume and survives restarts, but you
   repeat this if you remove the volume.

Either way the agent's config and its conversation storage live on the
`agent-home` volume, which is why a conversation you closed yesterday is
still there today. Nothing resumes by itself: the dashboard lists past
conversations, and opening one starts no process — sending a message is what
resumes it.

Without credentials the dashboard still runs; the AI Interview reports that
the agent could not start and points back here.

## Custom PDF templates

You can drop your own PostScript templates in `Resources/Templates/` in your vault; they appear in the dashboard's template pickers per application. A `.ps` file is a program, and rendering runs it in Ghostscript on your machine — so treat a template you were given the same way you would treat any other program someone sent you. The contract a template must honour is in the skill's `references/document-generation.md`, and `Resources/Templates/README.md` in your vault summarises it.

## Verify the install

From the repo root:

1. `python3 server/test_safety.py` — the safety suite must pass.
2. `python3 server/audit_vault.py` — must report 0 errors against your vault.
3. Open the dashboard, create a lead, archive it from its card, restore it
   from the Archived tab.
4. If PDF tooling is installed: open an application and render a resume
   preview (`demo/build_demo.py` builds a fictional vault to try this on).
