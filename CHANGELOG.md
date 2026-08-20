# Changelog

Notable, user-visible changes. Follows [Keep a Changelog](https://keepachangelog.com)
loosely; versions are git tags.

## Unreleased

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
