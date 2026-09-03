# Agent guidance

This repo is a local-first job-hunt webapp where markdown is the database:
a dashboard you run yourself over an Obsidian vault, supplemented by local
CLI AI agents that work the same vault through the same surface. The vault
is located via `.env` (`CAREER_EVIDENCE_VAULT`), by walking upward from the
working directory, or falling back to the gitignored `vault/` at the repo
root. Never commit personal data here — `vault/` stays ignored.

## The server

The application lives in `server/` — Python 3 stdlib only. It serves the
dashboard from `server/assets/ui/` and owns every deterministic vault
operation: scaffolding notes, capturing postings, rendering PDFs, indexing,
and the audit. Run its scripts from the repository root as
`python3 server/<script>.py`.

## The frontend

The dashboard is a React 18 + TypeScript app; its source is `ui/` and its
built bundle is committed to `server/assets/ui/`, which is what the server
serves. Never hand-edit the bundle — change `ui/` and rebuild with
`cd ui && npm run build`, committing the output alongside the source. Users
need no Node; contributors run `npm run dev`, which proxies `/api` and
`/file` to the Python server. The built `index.html` keeps the
`__SESSION_TOKEN__` placeholder that `serve.py` substitutes on every `GET /`
— every occurrence of that literal is replaced, so nothing else in the page
may spell it.

## The skill

The `career-evidence` skill is the heart of the repo and lives at
`.agents/skills/career-evidence/` — always edit the canonical copies under
`.agents/skills/`. Read its `SKILL.md` before doing any job-hunt work: it
defines who owns which note, the truth and privacy rules, and points to the
workflow command skills. Deeper references live beside it in `references/`.

The step-by-step workflows are thin sibling skills: `init-vault`,
`new-application`, `new-person`, `draft-resume`, `draft-cover-letter`,
`resume-pdf`, and `cover-letter-pdf`. They reference the core skill's rules
and references by relative path (`../career-evidence/`), and invoke the
server's scripts as `python3 server/<script>.py`. They are the AI integration
layer over the same surface the webapp uses; the release zip is the whole
application — `server/package_app.py` builds it. Shared rules belong in the
core skill; a command skill holds only its own workflow.

Keep everything under `.agents/skills/` host-neutral. Canonical skill files may
refer to sibling workflows by skill name and relative link, but must not assume
a provider, model, command prefix, slash-command syntax, proprietary tool name,
or provider-specific frontmatter. Host adapters belong outside `.agents/skills/`;
for example, each entry in `.claude/skills/` is a symlink to a canonical skill,
which keeps the commands scoped to this project checkout in Claude Code.
`docs/host-adapters.md` is the written guide, with a worked non-Claude example.

## The AI sandbox

The dashboard can run the evidence interview itself, by spawning the Claude
Code CLI per conversation and relaying its `stream-json` events to a chat
panel over SSE (`server/agent_sessions.py`). The agent is confined on purpose:
`--restricted --strict-mcp-config --tools Read,Write,Edit,Glob,Grep` with a
single `--add-dir` pointing at the vault, so it can read and write vault
markdown and do nothing else — no shell, no web, no MCP. Arguments are always
a list handed to `Popen`; a captured job posting is text an attacker wrote,
and it must never be able to reach a command line. The stance on what the
agent writes is after the fact, not up front: there is no approval step,
`audit_vault.py` is the check, exactly as it is for notes written by hand.
Nothing resumes on its own — a listed conversation is inert until someone
sends it a turn.

## Working on the tooling

- Scripts are Python 3 **stdlib only** — no new dependencies. External
  binaries allowed: Ghostscript (`ps2pdf`) and poppler utils, both optional.
- Controlled vocabularies live once, in `server/schema.py`. After changing
  them, regenerate the vault's `Working Notes/Field Reference.md` with
  `python3 server/export_index.py --write-field-reference`.
- Structural changes to the vault layout must land in four places together:
  the server scripts, `references/vault-schema.md`,
  `server/assets/vault-template/`, and the user's live vault.
- After any change, run from the repo root:
  - `python3 server/test_safety.py` — safety-boundary tests, must pass
  - `python3 server/audit_vault.py` — must exit 0 against the live vault

## Rules that are not negotiable

- Markdown notes are the only source of truth; `.cache/` is derived and
  disposable.
- `Job Description.md` captures are checksummed evidence — never edited.
- `Application Brief.md` belongs to the user — update fields, never
  restructure.
- A skill absent from the vault's Skill Matrix has no evidence behind it and
  does not belong on a resume.
- Contact details carry audience levels; `self` never leaves the vault, and
  rendered artifacts may carry only `application` and `public`.
- The dashboard binds `127.0.0.1` by default and requires its per-vault token
  (`.cache/session-token`) for writes — keep it that way. The only sanctioned
  widening is the explicit `CAREER_EVIDENCE_BIND`/`--bind` opt-in the Docker
  image uses, and there `compose.yaml` publishes the port on the host's
  loopback only.
