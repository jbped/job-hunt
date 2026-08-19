# Roadmap

A local-first job-hunt system where **markdown is the database**. Obsidian,
git, scripts, dashboards, extensions, and AI agents are all clients of the
same vault of plain files. The goal: trustworthy enough to run your own
search on, simple enough to hand to a friend.

This file is direction; concrete work lives in
[GitHub issues](https://github.com/jbped/job-hunt/issues) by milestone.
Version numbers are intent, not promises.

## Principles

These shape every phase and outrank any feature:

- **Markdown is the database.** Every frontend reads and writes the vault on
  disk. Moving truth into a real database would be a different product and
  will only ever happen as a deliberate decision, not drift.
- **Deterministic wherever repeatable.** If a step can be a script or a form,
  it is never an AI behavior. AI touchpoints narrow to generation (drafts,
  analysis) and validation (voice, claim tracing, comparing descriptions
  against resumes and letters).
- **Agents use the human surface.** Anything an AI does goes through the same
  scripts and API a person uses, so swapping where the agent runs never
  changes what it can touch.
- **Humans can build data by hand.** The structure is schema-driven and
  audited, so hand-populating a note can never silently break automation —
  `audit_vault.py` catches it instead.

## 0.2 — Structure without an agent

Every scaffold becomes something a human can do through a form, no agent and
no schema knowledge required.

- Schema-driven dashboard forms for the remaining scaffolds: new
  application, new role, new accomplishment (people already exist). Forms
  generate from `schema.py` so vocabulary lives once.
- Leads: a pre-application stage for companies and roles worth looking into.
  One small note per lead (company is enough; role and link can be
  `Unknown`), with source contact, status (`new`, `pursuing`, `promoted`,
  `passed`), and an Obsidian Base table view. Promotion scaffolds the
  application and links back; passed leads keep their reason.
- Edit flows for the fields humans maintain (status, dates, follow-ups,
  compensation) through the token-guarded API.
- Follow-up queue: every next-follow-up date across applications and people,
  soonest first, overdue flagged — in `status.py` and the dashboard.
- Pipeline board view: applications as columns by status.
- People network view: render `via`/connector introduction chains.
- Cross-analysis validation pass (the flagship AI-as-validator touchpoint):
  a workflow that takes a drafted resume and cover letter as a pair and
  checks them against the posting, the analysis, and the evidence — keyword
  coverage and unsupported terms, letter-restates-resume redundancy, claim
  tracing with metric class and ownership intact, voice and banned patterns,
  and contradictions between the documents. It reports findings; it never
  silently edits a draft.
- Demo vault with fictional data, and a README walkthrough with screenshots,
  so the system can be evaluated before trusting it with real history.

## 0.3 — Capture from the browser

A Chrome/Firefox extension: one click on a job posting collects the URL and
description and POSTs them to the dashboard, which scaffolds the application
and stores the checksummed capture.

- New capture endpoint on the dashboard API (the extension is a client of
  it, per the principles).
- One-time token pairing between extension and dashboard; the server keeps
  binding `127.0.0.1` only.
- Verbatim capture with the extraction method recorded — the evidence rule
  is "untouched", never "clean".
- Site detection is explicitly not MVP; the button can be dumb.
- Low-commitment mode: file a lead instead of a full application when the
  posting is merely interesting.
- Scopes the stdlib-only rule to the vault scripts; the extension is its own
  build surface in its own directory.

## 0.4 — Packaged app

The dashboard grows into the full read/write frontend and ships as an
optional Docker image with the vault as a mounted volume. Packaging, not a
storage change: Obsidian keeps working on the same files throughout.

- Docker image for the dashboard server; compose file; vault volume.
- Delete/archive flows to complete CRUD, with the same audit guarantees.
- Verified setup on macOS and Windows (with or without Docker).
- Host adapter guide for non-Claude agents.

## 0.5 — AI sandbox (investigate)

A containerized agent runtime: log in with a Claude or Codex subscription
and the app dispatches analysis, drafting, and validation work to a headless
agent in a Docker sandbox. Because agents already use the human API, this
changes where the agent runs, not what it can do.

Open questions to answer before committing: subscription auth passthrough,
and preserving conversational back-and-forth (evidence interviews are
inherently interactive; agent SDKs support streaming chat, which may be
enough).

## Later

- Insights, as dashboard views over the index: funnel analytics by discovery
  method and referral, keyword gap report, evidence coverage report.
- Interview-prep workflow skill.
- Submission integrity report (which artifact versions went where, and
  whether working copies drifted since).
- LinkedIn data-export importer.
- Multi-profile support (one checkout, several vaults).

## Non-goals

- No cloud service, no accounts, no telemetry. Docker is local packaging.
- No auto-apply or bulk-application features. Volume is not the strategy.
- No AI in deterministic steps, and no loosening the evidence rules. If a
  claim can't be traced, it doesn't ship.
