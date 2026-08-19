# Contributing

Thanks for helping. This project has a few hard rules that keep it safe to
use on real personal data; read this once before your first change.

## Ground rules

- **Python stdlib only.** The scripts must run on a bare Python 3 install.
  No new dependencies, no `pip install`. The only external binaries are
  Ghostscript (`ps2pdf`) and Poppler utilities, and both are optional.
- **The vault is personal data.** `vault/` is gitignored and must stay out of
  history. Never commit real names, employers, compensation, or contact
  details — test fixtures use obviously fictional data.
- **Skills stay host-neutral.** Everything under `.agents/skills/` must work
  for any AI agent: no provider names, slash-command syntax, or
  provider-specific frontmatter in canonical files. Host adapters (like the
  `.claude/skills/` symlinks) live outside that tree.
- **Controlled vocabularies live once**, in
  `.agents/skills/career-evidence/scripts/schema.py`. After changing them,
  regenerate the field reference:
  `python3 export_index.py --write-field-reference`.
- **Structural vault changes land in four places together:** the scripts,
  `references/vault-schema.md`, `assets/vault-template/`, and (for your own
  testing) a live vault.

## Before you open a PR

From `.agents/skills/career-evidence/scripts/`:

```sh
python3 test_safety.py    # safety-boundary tests, must pass
python3 audit_vault.py    # must exit 0 against a vault built by init_vault.py
```

If you touched the dashboard UI, sanity-check the JavaScript still parses
(`node --check` on the extracted script block works) and confirm the server
still binds `127.0.0.1` only and still requires the per-session token for
writes. Those two properties are non-negotiable.

## Style

- Match the surrounding code. Minimal comments — explain the non-obvious
  constraint, not the line.
- Markdown that ships inside the vault template uses one line per paragraph
  (Obsidian renders every newline as a line break). Repo docs like this one
  hard-wrap normally.
- No em dashes in anything that could reach an employer (templates, sample
  copy, rendered artifacts).

## Issues and roadmap

Direction lives in [ROADMAP.md](ROADMAP.md); concrete work lives in GitHub
issues. Open an issue before a large PR so the approach can be agreed first.
Bug reports and feature requests each have an issue template.

## Releases

Releases are tagged `X.Y.Z` and built by `.github/workflows/release.yml`,
which runs the safety tests, packages the skill zip, and attaches it to the
GitHub release. Update `CHANGELOG.md` in the same PR as a user-visible change.
