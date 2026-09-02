# Milestone 0.5 verification — webapp-first restructure

Date: 2026-09-02. Branch: `webapp-first-0.5` (5 implementation commits, not pushed, not merged).
Plan: `2026-09-02-webapp-first-restructure.md`. Spec: `../specs/2026-09-02-webapp-first-design.md` § Verification (0.5).

## 1. Tests and audit

- `python3 server/test_safety.py` — **36 tests, OK**, run after every task. No test was weakened; the only edits were the permitted ones (`import package_skill` → `import package_app`, and `test_release_archive_has_portable_skill_roots` rewritten to the app-zip contract, which gained assertions rather than losing any: `.cache`/`__pycache__` segments and `.claude` are now rejected too).
- `python3 server/audit_vault.py` against the live vault — **exit 0** (0 errors, 3 pre-existing warnings about missing `job_url`, `discovery_method`, and an uncaptured posting; unchanged by this work).

## 2. Dashboard smoke (demo vault)

Server: `python3 server/serve.py --vault demo/vault --no-browser --port 8766` (8765 kept free for the Docker check).

| Check | Result |
|---|---|
| `GET /api/state` | `{"state": "a10c08c99f95f7e2"}` |
| `POST /api/lead` (token) | `{"path": "Leads/Smoke Test Co - Restructure Check.md"}` |
| `POST /api/archive` (`kind: lead`) | moved to `Archive/Leads/…`, file present on disk |
| `POST /api/unarchive` | restored to `Leads/…`, file present on disk |
| `POST /api/lead` **without** the token | HTTP 403 — the write gate is intact |
| `python3 server/render_pdf.py --vault demo/vault --app "Applications/Globex Corporation/Software Engineer II" --kind resume` | rendered `Resume v2 2026-09-02.pdf`, 1 page, 2 fonts embedded, validation passed (Ghostscript present at `/usr/bin/ps2pdf`) |

The demo vault was rebuilt with `python3 demo/build_demo.py --force` afterwards, so the smoke artifacts are gone.

## 3. Docker

`CAREER_EVIDENCE_VAULT_HOST=…/demo/vault docker compose up --build -d` → image built from `COPY server/ /app/server` with entrypoint `python3 /app/server/serve.py --no-browser`; `curl http://127.0.0.1:8765/api/schema` succeeded (**docker OK**); `docker compose down` clean. `compose.yaml` was not edited — the loopback-only publish `127.0.0.1:8765:8765` still stands.

## 4. App zip

`python3 server/package_app.py` → `dist/career-evidence-app.zip`, 79 files, 310 KB. Archive names are repo-relative (`server/serve.py`, `.agents/skills/career-evidence/SKILL.md`, `Dockerfile`, `compose.yaml`, `.dockerignore`, `docs/`, `extension/`, README/CHANGELOG/LICENSE). It contains no vault data, no `.cache`, no `__pycache__`, no provider-named path segments, and no `docs/superpowers/` (excluded via `EXCLUDED_DIRS`). The stale `dist/career-evidence-skill.zip` was deleted; `dist/` is untracked, so no artifact entered git.

Runnable from the unzipped root, verified twice:

- `python3 server/serve.py --help` prints usage from a clean unzip.
- From a clean unzip: `python3 server/init_vault.py myvault`, then `python3 server/serve.py --vault <tmp>/myvault --port 8767` → `GET /api/schema` OK and `GET /` returns the dashboard HTML; `--stop` shut it down.

**Deviation from plan Task 6 Step 4.** The plan expected `python3 server/test_safety.py` to pass *inside the unzipped tree*. It does not: 1 error + 2 failures there, all from one cause — the unzipped tree has no `.git` and no `.env`, so `vaultlib._repo_root()` falls back to `SERVER_ROOT`, making `REPO_ROOT` the `server/` directory. The three affected tests are repo-development checks that assert on files the distribution deliberately does not ship (`test_default_vault_is_gitignored` reads `.gitignore`; `test_skill_sources_are_host_neutral` and `test_release_archive_has_portable_skill_roots` walk `.agents/skills/` relative to `REPO_ROOT`). This is not a regression: the previous skill zip shipped `scripts/test_safety.py` with the same missing `.gitignore` and the same repo-root fallback. Rather than weaken those tests or add repo scaffolding to the distribution, the milestone's real claim — the app runs from the unzipped root — was verified directly, as recorded above. Worth a follow-up decision in 0.6: either ship a repo-root marker in the zip, or split the repo-only tests out of the shipped suite.

## Other notes

- Files touched beyond the plan's explicit list, in the spirit of its "no leftovers" sweep: `CONTRIBUTING.md` (two `.agents/skills/career-evidence/scripts/` references the plan's sweep command surfaced), `README.md`'s `assets/templates/` pointer, `server/assets/vault-template/Working Notes/Field Reference.md` (the shipped copy of the regenerated footer), and the now-stale `_repo_root()` docstring in `server/vaultlib.py`.
- The only write to the live vault was the sanctioned one: `python3 server/export_index.py --write-field-reference` (which also refreshed `.cache/vault-index.json`, derived and disposable). The Skill Matrix was deliberately not regenerated.
- The spec's target-layout listing names `new_person.py`; no such module exists today (person creation lives in `serve.py`/`new-person` skill). Nothing was created — noted only so the listing is not mistaken for a missing file.
