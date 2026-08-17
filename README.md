# job-hunt

The `career-evidence` skill: an Obsidian vault of verified career evidence, plus
the scripts that turn it into tailored resumes, cover letters, and an application
tracker.

**The vault is not in this repo.** This repo is the tooling; the vault is your
personal data and lives wherever you keep your Obsidian vaults. `.env` connects
the two.

## Layout

```
.claude/skills/career-evidence/
  SKILL.md            what the agent reads
  scripts/            the deterministic parts (Python 3 stdlib only)
  references/         schema, tracking rules, writing standards
  assets/
    vault-template/   an empty vault to start from
    ui/               the local dashboard
.env                  points at your vault (gitignored)
```

Because the skill sits at `.claude/skills/`, opening this repo in Claude Code
loads it automatically. Nothing needs installing and nothing is symlinked.

## Setup

```fish
cp .env.example .env
```

Then edit `.env` so `CAREER_EVIDENCE_VAULT` points at your vault. If you do not
have one yet:

```fish
python .claude/skills/career-evidence/scripts/init_vault.py ~/Documents/Obsidian/job-hunt
```

There are no dependencies to install. `render_pdf.py` needs `ps2pdf`
(Ghostscript) and the `poppler` utilities for validation; everything else is
stdlib.

## Scripts

Run from anywhere — they read `.env` for the vault path, and `--vault PATH`
overrides it.

```fish
set -l s .claude/skills/career-evidence/scripts

python $s/serve.py                          # the dashboard, on 127.0.0.1
python $s/status.py                         # same picture, in the terminal
python $s/new_application.py "Company" "Role"
python $s/capture_jd.py --app <folder> --file posting.txt
python $s/render_pdf.py --app <folder> --kind resume
python $s/audit_vault.py                    # must exit 0
python $s/export_index.py                   # rebuild .cache/vault-index.json
```

## Rules that are not negotiable

- The markdown notes are the only source of truth. `.cache/vault-index.json` is
  generated; deleting it loses nothing.
- `Application Brief.md` is yours, `Analysis.md` is the agent's, and
  `Job Description.md` is evidence — verbatim, checksummed, never edited.
- Every script has a hand-editable fallback. Copy a template and the whole
  workflow still works.
- The dashboard binds `127.0.0.1` only. It can write to personal data and has no
  authentication.
