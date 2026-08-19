# Changelog

Notable, user-visible changes. Follows [Keep a Changelog](https://keepachangelog.com)
loosely; versions are git tags.

## Unreleased

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
