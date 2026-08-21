# Changelog

Notable, user-visible changes. Follows [Keep a Changelog](https://keepachangelog.com)
loosely; versions are git tags.

## Unreleased

- Browser extension MVP (#17): `extension/` holds a plain no-build MV3
  Chrome/Firefox add-on — click it on a posting, name the company and role,
  and the page's visible text (or your selection) is POSTed to the local
  dashboard as an application capture or a lead. No site detection by
  design. The server answers CORS preflights for extension origins only, on
  POST routes only, so no extension can read the vault.
- Capture endpoint (#18): `POST /api/capture` scaffolds an application and
  stores the checksummed verbatim posting in one call, through the same
  `new_application` + `capture_jd` path the CLI uses; `mode: lead` files a
  lightweight lead instead and stores no posting text. A failed capture rolls
  the scaffold back. `source_kind` gains an `extension` value and its
  vocabulary moves into `schema.py`; the JD template now ships the field
  empty instead of a placeholder the audit would flag.
- Extension pairing (#18): browser-extension origins may POST when they carry
  the per-session token; the dashboard nav gains a "Pair extension" button
  that shows and copies the token. The server keeps binding `127.0.0.1` only.
- Resume standards rebuilt around collected professional advice (three
  writer/recruiter guides, distilled into the vault's Resources): the
  result test on every bullet, Action + How + Impact structure, the
  top-three-goals selection lens and eight impact areas, three levels of
  impact mapped onto ownership classes, four quantification lenses bounded
  by the claim classes, tense rules, per-role context, the recruiter
  find-it-fast test, and gap/title/self-rating rules. The `cross-check`
  skill gains a four-persona review panel: resume and cover letter pro,
  recruiter, hiring manager, and coach.
- Resume directions tightened: each rule now lives in exactly one file, the
  header is copied verbatim from `Contact.md` (no more per-application name
  and location drift), the summary opens with title and computed years, one
  claim per bullet at two rendered lines max, a `·`-separated skills line
  capped near 15 posting-relevant entries, and an explicit cut order when a
  draft runs over a page.
- Follow-up queue (#5): "What's coming up" now unifies application next
  actions, person and contact follow-ups, and lead follow-ups into one
  soonest-first queue with overdue flagged, in both `status.py` and the
  dashboard.
- Pipeline board (#6): applications as columns by status with drag-and-drop
  status changes (select fallback on each card) and a show-terminal toggle.
- Introduction chains (#7): the People view renders `via` chains
  (target ← via ← connector) and lists dangling chains as missing connector
  notes.
- `cross-check` skill (#16): validates the drafted resume and cover letter
  as a pair against the posting, the analysis, and the evidence — coverage,
  redundancy, claim tracing, voice, contradictions — appending findings to
  `Analysis.md` as a dated Draft review section. Reports, never edits.
- Demo vault (#1): `demo/build_demo.py` builds a fictional, audit-clean
  example vault with the real scripts; the README gains a "See it first"
  walkthrough with screenshots (#2). Dashboard views are now deep-linkable
  via `#view` hashes.
- Leads (#15): a pre-application pipeline stage. One small note per lead in
  `Leads/` (company alone is enough), created from the dashboard's new Leads
  view or `new_lead.py`, with an Obsidian Base table view. Promotion
  (`new_application.py --from-lead` or the Promote button) scaffolds the
  application and links back; passed leads keep their reason as funnel data.
- New `compensation_requested` field on the application brief: what you
  actually asked for, when, and where, so an interview never has to
  reconstruct it from memory.
- Schema-driven scaffold forms (#13): dashboard forms are now generated from
  `FORMS` in `schema.py` via `/api/schema`, and two new scaffolds join the
  API and CLI — `new_role.py` and `new_accomplishment.py` create evidence
  notes with open Questions sections, so forms create structure and
  interviews create facts.
- Edit flows for person fields (#14): `company_context`, `via`,
  `next_follow_up`, and `last_contact` are editable from a person card.
  The person-level follow-up dates carry the relationship's own cadence,
  distinct from per-application contact follow-ups.
- The application Details card now includes the stated experience level.
- Product scaffolding: roadmap, contributing guide, changelog, issue and PR
  templates.
- Release workflow now triggers on plain `X.Y.Z` tags (previous tags never
  matched the old `v*` pattern, so no release was built for them).

## 0.1.2 — 2026-08-19

- `People/` is now organized into warmth-based subfolders: `Network/`,
  `Recruiters/`, and `Job Hunt/`. Folders encode how well you know someone;
  frontmatter keeps the full multi-role truth.
- New vocabulary for introduction chains: `networking-target` and `connector`
  relationships, plus an optional `via` field pointing at the person the
  introduction runs through.
- The dashboard groups people by folder and lets you pick one when adding.
- Cover-letter writing standards rewritten around a plainspoken, direct
  voice: pain-point targeting, banned template openings/closers, a one-or-two
  numbers rule, and a mandatory read-aloud pass in the draft workflow.

## 0.1.1 — 2026-08-18

- Skills made portable across agents: canonical copies under
  `.agents/skills/`, host adapters as symlinks.
- Workflows split into individual command skills.
- `init_vault.py` made non-destructive.
- Em dashes banned in employer-facing copy.
- README overhauled around getting started.

## 0.1.0 — 2026-08-17

- Initial alpha: the career-evidence vault system, core skill and workflow
  skills, stdlib-only scripts (init, capture, render, audit, status, serve),
  vault template, and the local dashboard.
