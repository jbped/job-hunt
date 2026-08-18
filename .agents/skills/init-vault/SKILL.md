---
name: init-vault
description: Create and seed a new job-hunt vault — first-time setup of Personal Information, a first role and accomplishment, and a first application. Use when the user wants to set up the job-hunt system from scratch, has no vault yet, or the vault's Contact.md is missing or still has empty contact fields.
---

# Initialise the vault

Read [the core rules](../career-evidence/SKILL.md) first — it defines how an
existing vault is found, and the truth and privacy rules that apply from the
first note. Never silently make a second vault: if the `.env` or the upward
search finds one, ask before creating another.

If `Personal Information/Contact.md` is missing or still has empty contact
fields, the user is starting out. Walk them through it rather than filling
forms silently:

1. Run `init_vault.py` (in `../career-evidence/scripts/`) if there is no vault
   yet — without a path it creates the repo's own gitignored `vault/`; pass a
   path to put it elsewhere. Tell the user to use Obsidian's "Open folder as
   vault" on the created folder, not "Create new vault", which would nest a
   fresh empty vault inside it. It works in a vault Obsidian just created too: it clears the
   stock `Welcome.md` Obsidian seeds, but only on an exact content match — a
   `Welcome.md` that was edited (or is in another language) is user content, so
   ask before deleting it.
2. Ask for an existing resume, diploma, or certificate to drop into
   `Resources/` — source documents there are the fastest way to seed the vault,
   and provenance lines can point back at them.
3. Fill `Personal Information/` — `Contact.md` (contact details with per-entry
   audience levels; the frontmatter is the cover-letter letterhead),
   `About Me.md` (target roles, work model, compensation thinking), and
   `Education.md`. `unknown` is a fine answer and better than a guess.
4. Capture one role and its strongest accomplishment by interview — the
   protocol is [evidence-interview.md](../career-evidence/references/evidence-interview.md).
   One good accomplishment note is worth more than five thin ones, and it shows
   the user what the vault is for.
5. Follow the [`new-application`](../new-application/SKILL.md) workflow to create
   their first application and analyse it against that evidence.

Ask in small batches. A long questionnaire gets abandoned.
