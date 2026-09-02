# Host adapters: using the skills from any agent

The canonical skills live in `.agents/skills/` and are host-neutral by
contract: no provider names, no slash-command syntax, no provider-specific
frontmatter, and they reference each other only by skill name and relative
path (`../career-evidence/`), so the whole set ships together. Two safety
tests enforce the wall — `test_skill_sources_are_host_neutral` and
`test_release_archive_has_portable_skill_roots` in
`server/test_safety.py` — so a canonical file
that mentions a provider fails the suite.

An **adapter** is anything outside `.agents/skills/` that maps the canonical
skills into one host's discovery mechanism. Adapters may be as host-specific
as they like; canonical files may not. Nothing about the skills changes per
host — every agent reads the same SKILL.md files, runs the same scripts, and
goes through the same dashboard API a person uses.

## Worked example A: Claude Code (ships with this repo)

`.claude/skills/` contains one symlink per canonical skill:

```text
.claude/skills/career-evidence -> ../../.agents/skills/career-evidence
.claude/skills/new-application -> ../../.agents/skills/new-application
…
```

Claude Code discovers skills in `.claude/skills/`, so the workflows appear as
project-scoped skills in this checkout with zero duplication. On Windows the
symlinks need Developer Mode plus `git config core.symlinks true` before
cloning — see [setup.md](setup.md) — or use the release zip, which contains
real files.

## Worked example B: Codex (or any AGENTS.md-reading agent)

Codex reads `AGENTS.md` natively, so the adapter is a pointer section — no
canonical file changes, no copies. Paste this into the repo's `AGENTS.md`
(or `~/.codex/AGENTS.md` for a global setup) if it is not already covered:

```markdown
## Job-hunt skills

Before any job-hunt work, read
`.agents/skills/career-evidence/SKILL.md` — it defines note ownership,
the truth and privacy rules, and points to the workflow skills that sit
beside it (`new-application`, `draft-resume`, …), each with its own
`SKILL.md`. Always work through `server/` and the
dashboard API; never edit vault notes beyond what SKILL.md allows.
```

This repo's own `AGENTS.md` already serves that role for agents that read
it, so a Codex user needs nothing extra in this checkout.

## Checklist for any other host

1. **Entry point**: expose `career-evidence/SKILL.md` however the host
   discovers instructions (a skills directory, a rules file, a pointer in its
   config). The core skill routes to everything else.
2. **Preserve relative paths**: link or copy the *whole* `.agents/skills/`
   tree — the workflow skills reference `../career-evidence/` and break if
   separated. `server/package_app.py` builds the application zip, which
   carries exactly this shape.
3. **Never fork the rules**: an adapter points at the canonical files; it
   does not restate or amend them. Shared rules belong in the core skill.
4. **Verify**: from the repo root, run
   `python3 server/test_safety.py` — it must pass, and it will catch a provider
   marker accidentally added to a canonical file.
