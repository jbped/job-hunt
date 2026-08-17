# Agent guidance

This repo is tooling for a job-hunt system; the user's data lives in an
Obsidian vault **outside** the repo, located via `.env`
(`CAREER_EVIDENCE_VAULT`) or by walking upward from the working directory.
Never commit personal data here.

## The skill

The `career-evidence` skill is the heart of the repo and lives at
`.agents/skills/career-evidence/` (`.claude/skills/career-evidence` is a
compatibility symlink to it — edit the canonical copy). Read its `SKILL.md`
before doing any job-hunt work: it defines who owns which note, the truth and
privacy rules, and the workflows. Deeper references live beside it in
`references/`.

## Working on the tooling

- Scripts are Python 3 **stdlib only** — no new dependencies. External
  binaries allowed: Ghostscript (`ps2pdf`) and poppler utils, both optional.
- Controlled vocabularies live once, in `scripts/schema.py`. After changing
  them, regenerate the vault's `Working Notes/Field Reference.md` with
  `export_index.py --write-field-reference`.
- Structural changes to the vault layout must land in four places together:
  the scripts, `references/vault-schema.md`, `assets/vault-template/`, and the
  user's live vault.
- After any change, run from `scripts/`:
  - `python3 test_safety.py` — safety-boundary tests, must pass
  - `python3 audit_vault.py` — must exit 0 against the live vault

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
- The dashboard binds `127.0.0.1` and requires its per-session token for
  writes — keep it that way.
