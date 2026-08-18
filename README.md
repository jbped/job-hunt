# career-evidence

A job-hunt system built on plain markdown: an Obsidian vault of verified career
evidence, plus portable AI-agent skills and scripts that turn it into tailored
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

The vault is personal data and never belongs in git history. It can live outside
the checkout, connected through `.env`, or in the repo's gitignored `vault/`
directory for zero-config setup.

## Layout

```
.agents/skills/career-evidence/
  SKILL.md            what the agent reads
  scripts/            the deterministic parts (Python 3 stdlib only)
  references/         schema, tracking rules, writing standards
  assets/
    vault-template/   an empty vault to start from
    templates/        the note scaffolds the scripts create from
    ui/               the local dashboard
.env                  points at your vault (gitignored; see .env.example)
```

The vault a new user gets:

```
Personal Information/   contact details with audience levels, education, about-me
Career Evidence/        one note per role, one per accomplishment — the source of truth
Applications/           one folder per application: posting, analysis, artifacts
People/                 one note per person: contacts, referrals, references
Preferences/            standing instructions for any agent working in the vault
Resources/              ingested source documents (old resumes, diplomas)
Working Notes/          open questions, generated skill matrix and field reference
```

The canonical skills live at `.agents/skills/`: the `career-evidence` core plus
seven sibling workflows. They use only portable `SKILL.md` frontmatter, relative
links, plain-language instructions, and executable scripts. They do not name a
model provider, assume a command prefix, or depend on proprietary agent tools.

Host-specific discovery and invocation stay outside the canonical package. For
Claude Code, each entry in `.claude/skills/` is a symlink to a canonical skill,
so the commands load automatically in this checkout and stay scoped to it;
other hosts can discover `.agents/skills/` directly, point their recognized
skill directory at it, or load `career-evidence/SKILL.md` explicitly. Command
names and prefixes may differ by host; the stable workflow identifiers are the
folder names such as `new-application`, `draft-resume`, and `resume-pdf`.

The checkout adapter uses symlinks. On Windows, git recreates symlinks only
when Developer Mode (or an elevated shell) and `git config core.symlinks true`
are enabled before cloning. This does not affect the canonical skills or the
release archive, which contains real files.

## Getting it

Two ways in, with the same provider-neutral skills either way:

- **Clone the repo** (recommended). Configure your agent to discover
  `.agents/skills/`, or tell it to read
  `.agents/skills/career-evidence/SKILL.md`. You also get git history and easy
  updates.
- **Download the zip** from the [Releases page](../../releases) — extract all
  sibling skill folders into a skill directory recognized by your agent. Keep
  them side by side because workflow skills link to the core by relative path.
  The archive carries the scripts, references, vault template, and dashboard.

The zip is built by `scripts/package_skill.py`, so you can also produce one
yourself from a checkout. Consult the host's documentation for its discovery
directory and invocation syntax; neither is baked into the archive.

## Setup

The zero-config path — create the vault inside the checkout, where it is
gitignored and found automatically:

```sh
python .agents/skills/career-evidence/scripts/init_vault.py
```

Then in Obsidian choose **Open folder as vault** and select the created
folder. (Not *Create new vault* — that would nest a fresh, empty vault inside
it.)

To keep the vault elsewhere instead (say, alongside your other Obsidian
vaults), pass `init_vault.py` that path and point the tooling at it:

```fish
cp .env.example .env
```

Then edit `.env` so `CAREER_EVIDENCE_VAULT` points at your vault. (Zip install:
create the `.env` inside the unzipped `career-evidence/` folder, next to
`SKILL.md` — the scripts look there first.)

Everything runs on stock Python 3 — Windows, macOS, or Linux, no packages to
install. Only `render_pdf.py` needs external tools, Ghostscript and the Poppler
utilities: `pacman -S ghostscript poppler` (Arch), `apt install ghostscript
poppler-utils` (Debian/Ubuntu), `brew install ghostscript poppler` (macOS), or
on Windows the Ghostscript installer plus Poppler binaries on `PATH`.

## Scripts

Run from anywhere — they read `.env` for the vault path, and `--vault PATH`
overrides it. From the repo root, with `scripts/` being
`.agents/skills/career-evidence/scripts/`:

```sh
python scripts/serve.py                    # the dashboard, on 127.0.0.1
python scripts/serve.py --detach           # same, in the background (--stop ends it)
python scripts/status.py                   # same picture, in the terminal
python scripts/new_application.py "Company" "Role"
python scripts/capture_jd.py --app <folder> --file posting.txt
python scripts/render_pdf.py --app <folder> --kind resume
python scripts/audit_vault.py              # must exit 0
python scripts/export_index.py             # rebuild .cache/vault-index.json
python scripts/export_index.py --write-skill-matrix   # skills -> evidence map
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
- Every script has a hand-editable fallback. Copy a note from
  `assets/templates/` and the whole
  workflow still works.
- The dashboard binds `127.0.0.1` only, and writes additionally require the
  per-session token the served page carries — a browser tab on another site
  cannot reach the write API.

## License

[MIT](LICENSE)
