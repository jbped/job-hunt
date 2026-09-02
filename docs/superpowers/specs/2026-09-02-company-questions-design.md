# Company Questions

Date: 2026-09-02. Status: approved direction, pending spec review.
Parent: `webapp-first-epic`.

## Why

Users applying to several roles at the same entity are asked the same
short-form questions on every application (reported: three identical
questions across three applications to one government employer). Today
those answers are rewritten from scratch or hunted out of old submission
notes. The vault should keep a per-company bank of questions with the
answers actually submitted, and the webapp should surface that bank the
moment another application targets the same company.

Decisions made in brainstorming (user, 2026-09-02):

- Purpose is **answer reuse**: each entry is a question plus the answer
  the user gave.
- Scope is **per-company only** — no shared pool, no tags. Cross-company
  reuse is manual copy.
- Workflow is **company note + application surfacing** in the webapp.
- Answers are **user-authored only**. Agents may read them for context;
  they never draft or edit them. AI-assisted answer drafting, if ever
  wanted, is a separate future feature with its own spec.

## Data model

One new note per company folder, created on first use:

```
Applications/<Company>/Company Questions.md
```

- Ownership: the user's, with the same contract as `Application Brief.md`
  — tools may append entries and update fields, never restructure, and
  agents never author answer prose.
- Shape: frontmatter identifying the note type; one entry per question in
  the vault's established entry pattern (heading = the question text;
  entry fields + free body). Entry fields:
  - `asked_on` — application folder(s) the question appeared in
    (wikilink), appendable as it recurs
  - `date` — when last asked
  - `char_limit` — optional; short-form portals commonly cap length
  - body — the answer as submitted, verbatim
- Markdown remains the database: the note reads cleanly in Obsidian with
  no tooling.

Per the four-places rule, the structure lands together in: the server
scripts, `references/vault-schema.md`, `server/assets/vault-template/`
(template file), and the user's live vault.

## Server

Smallest possible surface, reusing what exists:

- Scaffold: creating the note from its template when a company has none.
  Follow the existing scaffold conventions (bounded writes, sanitized
  names, no overwrite of an existing note).
- Append/update: the existing entry-append and note/field endpoints
  already fit the entry shape; extend only if the plan-time inventory
  finds a real gap.
- Projection: `/api/index` exposes each company's question bank so the
  UI needs no extra fetches.
- Audit: `audit_vault.py` learns the note type — valid structure,
  `asked_on` links resolve, and (if kept) `char_limit` is numeric.
  Warnings, not errors, for missing optional fields.
- `test_safety.py` additions: scaffold boundedness for the new note and
  the no-restructure boundary (same class of tests the other note types
  have).

## Webapp

- The Applications viewer gains a **Company questions** panel, visible on
  every application whose company has (or could have) a bank:
  - existing entries listed question-first with the submitted answer
    ready to copy;
  - add-question form (question, optional char limit, answer textarea);
  - answers edited through the existing fingerprint-guarded note flow;
  - each entry shows where it was asked via its `asked_on` links.
- Creating a new application for a company with a bank surfaces the
  panel immediately — the reuse moment this feature exists for.
- No new view; this is a panel within the Applications split view.

## Skills

`career-evidence` SKILL.md and `references/vault-schema.md` document the
note's ownership and the agents-read-only rule for answers. No new
command skill: there is no agent workflow here beyond reading.

## Non-goals

- No shared/global question pool, no tagging, no cross-company search.
- No AI drafting of answers.
- No import of questions from postings or portals.

## Verification

- `test_safety.py` passes with the new boundedness/ownership tests.
- `audit_vault.py` exits 0 on a vault containing banks (demo vault gains
  one).
- Webapp: add a question on application A of a company, open application
  B of the same company, see the entry with its answer; edit the answer
  via the note flow; `asked_on` gains B when marked asked there.
- A vault with no banks behaves exactly as today.
