# career-evidence

A job-hunt system built on plain markdown: an Obsidian vault of verified career
evidence, plus the scripts and Claude Code skill that turn it into tailored
resumes, cover letters, and an application tracker.

The premise: resume writing under pressure always drifts the same way — numbers
round up, shared work becomes sole work, and job-posting keywords get claimed
without backing. This system makes fast generation safe by keeping evidence
separate from artifacts. Every claim on a resume traces to an evidence note;
every skill traces to the role where it was used; every job posting is stored
verbatim and checksummed so analysis can't quietly reshape it.

It is profession-agnostic — the examples lean software engineering because that
is the author's field, but the vocabulary lives in one file
(`scripts/schema.py`) and the vault holds roles, accomplishments, skills, and
people, not code.

**The vault is not in this repo.** This repo is the tooling; the vault is your
personal data and lives wherever you keep your Obsidian vaults. `.env` connects
the two, and nothing personal is ever committed here.

## Layout

```
.agents/skills/career-evidence/
  SKILL.md            what the agent reads
  scripts/            the deterministic parts (Python 3 stdlib only)
  references/         schema, tracking rules, writing standards
  assets/
    vault-template/   an empty vault to start from
    ui/               the local dashboard
.env                  points at your vault (gitignored; see .env.example)
```

The vault a new user gets:

```
Personal Information/   contact details with audience levels, education, about-me
Career Evidence/        one note per role, one per accomplishment — the source of truth
Applications/           one folder per application: posting, analysis, artifacts
People/                 one note per person: contacts, referrals, references
Resources/              ingested source documents (old resumes, diplomas)
Working Notes/          open questions, generated skill matrix and field reference
Templates/              the scaffolds everything is created from
```

The skill lives at `.agents/skills/` (the cross-agent standard location);
`.claude/skills/career-evidence` is a symlink to it, so opening this repo in
Claude Code loads it automatically. Nothing needs installing.

## Setup

```fish
cp .env.example .env
```

Then edit `.env` so `CAREER_EVIDENCE_VAULT` points at your vault. If you do not
have one yet:

```fish
python .agents/skills/career-evidence/scripts/init_vault.py ~/Documents/Obsidian/job-hunt
```

There are no dependencies to install. `render_pdf.py` needs `ps2pdf`
(Ghostscript) and the `poppler` utilities for validation; everything else is
stdlib.

## Scripts

Run from anywhere — they read `.env` for the vault path, and `--vault PATH`
overrides it.

```fish
set -l s .agents/skills/career-evidence/scripts

python $s/serve.py                          # the dashboard, on 127.0.0.1
python $s/status.py                         # same picture, in the terminal
python $s/new_application.py "Company" "Role"
python $s/capture_jd.py --app <folder> --file posting.txt
python $s/render_pdf.py --app <folder> --kind resume
python $s/audit_vault.py                    # must exit 0
python $s/export_index.py                   # rebuild .cache/vault-index.json
python $s/export_index.py --write-skill-matrix   # skills -> evidence map
```

## Rules that are not negotiable

- The markdown notes are the only source of truth. `.cache/vault-index.json` is
  generated; deleting it loses nothing.
- `Application Brief.md` is yours, `Analysis.md` is the agent's, and
  `Job Description.md` is evidence — verbatim, checksummed, never edited.
- A skill absent from the skill matrix has no evidence behind it and does not
  belong on a resume.
- Contact details carry an audience level (`self | application | recruiter |
  public`); anything marked `self` never leaves the vault.
- Every script has a hand-editable fallback. Copy a template and the whole
  workflow still works.
- The dashboard binds `127.0.0.1` only, and writes additionally require the
  per-session token the served page carries — a browser tab on another site
  cannot reach the write API.

## License

[MIT](LICENSE)
