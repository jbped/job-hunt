# Webapp-First Restructure (Milestone 0.5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the Python application out of the career-evidence skill into a top-level `server/` directory with zero behavior change, and retarget packaging, Docker, CI, skills, and docs to the new layout.

**Architecture:** Pure relocation: `git mv` the flat module directory and the app assets (note/PDF templates, served UI, vault template) to `server/`; only root-resolution constants change (`SKILL_ROOT` → `SERVER_ROOT`). The skills stay in `.agents/skills/` as thin workflow documents that invoke `server/<script>.py`. The release zip becomes the whole application.

**Tech Stack:** Python 3 stdlib only (unchanged rule). External binaries stay optional (Ghostscript `ps2pdf`, poppler). No new dependencies of any kind.

**Spec:** `docs/superpowers/specs/2026-09-02-webapp-first-design.md` (§ Milestone 0.5)

## Global Constraints

- **Zero behavior change**: endpoints, token handling, binds, pidfile, vault resolution, audit rules all identical.
- `server/test_safety.py` must pass **without weakening**. The only permitted test edits are the two packaging tests (`test_skill_sources_are_host_neutral` stays as-is; `test_release_archive_has_portable_skill_roots` moves to the app-zip contract) and the `import package_skill` → `import package_app` rename.
- Python stdlib only; no new dependencies.
- Skills stay host-neutral: no provider names, no `.claude/` paths, no slash-command syntax inside `.agents/skills/` (enforced by `test_skill_sources_are_host_neutral`).
- Never commit vault data; `vault/` and `demo/vault/` stay out of git and out of the zip.
- Dashboard binds `127.0.0.1` by default; per-vault token required for writes. Do not touch that code.
- All work on branch `webapp-first-0.5`, commits per task, no push unless asked.
- Run every verification command from the **repo root** (`python3 server/test_safety.py` works from anywhere because Python puts the script's own directory on `sys.path`).

## Current → target map (from the repo inventory, 2026-09-02)

| Today | After |
|---|---|
| `.agents/skills/career-evidence/scripts/*.py` (17 files) | `server/*.py` |
| `.agents/skills/career-evidence/scripts/package_skill.py` | `server/package_app.py` (renamed, new contract) |
| `.agents/skills/career-evidence/assets/templates/` | `server/assets/templates/` |
| `.agents/skills/career-evidence/assets/ui/index.html` | `server/assets/ui/index.html` |
| `.agents/skills/career-evidence/assets/vault-template/` | `server/assets/vault-template/` |
| `.agents/skills/career-evidence/{SKILL.md,references/}` | unchanged location, contents retargeted to `server/` |
| `dist/career-evidence-skill.zip` (stale artifact) | deleted; new artifact `dist/career-evidence-app.zip` |

`.claude/skills/` symlinks (`<name> -> ../../.agents/skills/<name>`) are untouched — they point at skill directories, which keep their names and SKILL.md files.

---

### Task 1: Move the code and assets; retarget the root constants

**Files:**
- Move (git mv): `.agents/skills/career-evidence/scripts/` → `server/`; `.agents/skills/career-evidence/assets/templates/` → `server/assets/templates/`; `.agents/skills/career-evidence/assets/ui/` → `server/assets/ui/`; `.agents/skills/career-evidence/assets/vault-template/` → `server/assets/vault-template/`
- Modify: `server/vaultlib.py:33-34`, `server/init_vault.py:25-26`, `server/serve.py:61`
- Test: `server/test_safety.py` (moves with the directory; not edited in this task)

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `vaultlib.SERVER_ROOT: Path` (the `server/` directory), `vaultlib.TEMPLATES_DIR: Path`, `vaultlib.REPO_ROOT: Path` (unchanged name/behavior). Every later task assumes scripts run as `python3 server/<script>.py` from the repo root.

- [x] **Step 1: Create the branch**

```bash
git checkout -b webapp-first-0.5
```

- [x] **Step 2: git mv the script directory and assets**

```bash
git mv .agents/skills/career-evidence/scripts server
mkdir -p server/assets
git mv .agents/skills/career-evidence/assets/templates server/assets/templates
git mv .agents/skills/career-evidence/assets/ui server/assets/ui
git mv .agents/skills/career-evidence/assets/vault-template server/assets/vault-template
rmdir .agents/skills/career-evidence/assets
```

If a stray `server/__pycache__/` came along, delete it (`rm -rf server/__pycache__`).

- [x] **Step 3: Retarget the root constants**

In `server/vaultlib.py`, replace lines 33-34:

```python
SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "assets" / "templates"
```

with:

```python
SERVER_ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = SERVER_ROOT / "assets" / "templates"
```

Then update the two remaining `SKILL_ROOT` uses in the same file (lines 45 and 48, the repo-root discovery walk) to `SERVER_ROOT`. Grep to catch them all:

```bash
grep -rn "SKILL_ROOT" server/
```

In `server/init_vault.py`, replace lines 25-26:

```python
SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_ROOT / "assets" / "vault-template"
```

with:

```python
SERVER_ROOT = Path(__file__).resolve().parent
TEMPLATE = SERVER_ROOT / "assets" / "vault-template"
```

In `server/serve.py`, replace line 61:

```python
UI_DIR = Path(__file__).resolve().parent.parent / "assets" / "ui"
```

with:

```python
UI_DIR = Path(__file__).resolve().parent / "assets" / "ui"
```

In `server/package_skill.py` (renamed in Task 2), update line 17's import for now so the module still loads:

```python
from vaultlib import SERVER_ROOT, REPO_ROOT
```

and line 19:

```python
SKILLS_ROOT = REPO_ROOT / ".agents" / "skills"
```

(The old `SKILL_ROOT.parent` derivation no longer points at the skills dir.)

After the edits, `grep -rn "SKILL_ROOT" server/` must return nothing.

- [x] **Step 4: Run the safety tests**

```bash
python3 server/test_safety.py
```

Expected: `test_release_archive_has_portable_skill_roots` may FAIL (the zip contract changes in Task 2 — old assertions expect `career-evidence/SKILL.md` at the archive root). Every other test must PASS. If anything else fails, fix the constant retargeting — do not touch the tests.

- [x] **Step 5: Smoke the vault audit**

```bash
python3 server/audit_vault.py; echo "exit=$?"
```

Expected: `exit=0` against the live vault.

- [x] **Step 6: Commit**

```bash
git add -A
git commit -m "Move the Python app and its assets to server/"
```

---

### Task 2: package_skill.py → package_app.py with the app-zip contract

**Files:**
- Move: `server/package_skill.py` → `server/package_app.py`
- Modify: `server/package_app.py`, `server/test_safety.py` (import + the archive test only)

**Interfaces:**
- Consumes: `vaultlib.REPO_ROOT` from Task 1.
- Produces: `package_app.build(output: Path) -> Path` writing `dist/career-evidence-app.zip`; module constants `APP_TOP_LEVEL: list[str]`, `CANONICAL_SKILLS: set[str]` (unchanged members), `EXCLUDED_DIRS: set[str]`, `EXCLUDED_FILES: set[str]`. Task 5 (CI) invokes `python3 server/package_app.py`.

- [x] **Step 1: Rename the module**

```bash
git mv server/package_skill.py server/package_app.py
```

- [x] **Step 2: Rewrite the packaging logic**

Keep `CANONICAL_SKILLS`, `EXCLUDED_DIRS`, `EXCLUDED_FILES` and the CLI shape; replace the file selection and archive layout. The zip is the application, rooted at the repo layout, runnable from the unzipped root:

```python
EXCLUDED_DIRS = {"__pycache__", ".cache", ".git", "vault", "superpowers"}
EXCLUDED_FILES = {".DS_Store", ".env"}

APP_TOP_LEVEL = [
    "server",
    "extension",
    "docs",
    "Dockerfile",
    "compose.yaml",
    ".dockerignore",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
]


def app_files():
    files = []
    for top in APP_TOP_LEVEL:
        path = REPO_ROOT / top
        if path.is_file():
            files.append(path)
            continue
        for candidate in sorted(path.rglob("*")):
            if not candidate.is_file():
                continue
            parts = candidate.relative_to(REPO_ROOT).parts
            if any(part in EXCLUDED_DIRS for part in parts):
                continue
            if candidate.name in EXCLUDED_FILES or candidate.suffix == ".pyc":
                continue
            files.append(candidate)
    skills_root = REPO_ROOT / ".agents" / "skills"
    for skill in sorted(CANONICAL_SKILLS):
        for candidate in sorted((skills_root / skill).rglob("*")):
            if not candidate.is_file():
                continue
            parts = candidate.relative_to(skills_root).parts
            if any(part in EXCLUDED_DIRS for part in parts):
                continue
            if candidate.name in EXCLUDED_FILES or candidate.suffix == ".pyc":
                continue
            files.append(candidate)
    return files


def build(output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in app_files():
            zf.write(path, path.relative_to(REPO_ROOT).as_posix())
    return output
```

Archive names are therefore repo-relative: `server/serve.py`, `.agents/skills/career-evidence/SKILL.md`, `Dockerfile`, … Default output becomes `REPO_ROOT / "dist" / "career-evidence-app.zip"`. `docs/superpowers/` (personal process docs) is excluded via `EXCLUDED_DIRS`. Adapt surrounding code (docstring, `main()`, argparse help) to say "app", and keep the module stdlib-only.

- [x] **Step 3: Update the two packaging references in test_safety.py**

In `server/test_safety.py`: change `import package_skill` to `import package_app` (and every `package_skill.` reference — grep for it). Leave `test_skill_sources_are_host_neutral` (line 199) logically unchanged: it walks `CANONICAL_SKILLS` under `.agents/skills/`, now via `package_app.CANONICAL_SKILLS`; its `scripts/*.py` glob simply matches nothing once skills carry no scripts, which is correct.

Rewrite `test_release_archive_has_portable_skill_roots` (line 218) to the app-zip contract, preserving its strictness:

```python
def test_release_archive_has_portable_skill_roots(self):
    self.assertIn("vault", package_app.EXCLUDED_DIRS)
    with tempfile.TemporaryDirectory() as tmp:
        archive = package_app.build(Path(tmp) / "app.zip")
        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
    for required in (
        "server/serve.py",
        "server/test_safety.py",
        "server/assets/ui/index.html",
        ".agents/skills/career-evidence/SKILL.md",
        ".agents/skills/new-application/SKILL.md",
        "Dockerfile",
        "compose.yaml",
    ):
        self.assertIn(required, names)
    forbidden_segments = {"anthropic", "claude", "codex", "cursor", "gemini", "openai", ".claude", ".claude-plugin", "vault", ".cache", "__pycache__"}
    for name in names:
        parts = name.split("/")
        self.assertFalse(set(parts) & forbidden_segments, f"forbidden path segment in {name}")
        self.assertFalse(name.startswith("job-hunt/"), name)
```

Match the existing test file's assertion style and helpers when writing the final version — this block shows the required assertions, not necessarily the file's idiom.

- [x] **Step 4: Run the safety tests**

```bash
python3 server/test_safety.py
```

Expected: all tests PASS, including both packaging tests.

- [x] **Step 5: Build the zip and verify it runs from the unzipped root**

```bash
rm -f dist/career-evidence-skill.zip
python3 server/package_app.py
cd "$(mktemp -d)" && unzip -q /home/jbped/dev/job-hunt/dist/career-evidence-app.zip
python3 server/serve.py --help
```

Expected: unzip succeeds, `--help` prints usage (proves the app is runnable in place). Then `cd` back to the repo. If `dist/` entries are untracked (check `git status dist/`), nothing to commit for the artifacts; if the stale zip was tracked, `git rm` it.

- [x] **Step 6: Commit**

```bash
git add -A
git commit -m "Package the application zip instead of the skill set"
```

---

### Task 3: Docker and demo builder

**Files:**
- Modify: `Dockerfile`, `.dockerignore`, `demo/build_demo.py`
- Unchanged (verify only): `compose.yaml`

**Interfaces:**
- Consumes: `server/` layout from Task 1.
- Produces: image entrypoint `python3 /app/server/serve.py --no-browser`; `demo/build_demo.py` imports via `sys.path.insert(0, str(REPO / "server"))`.

- [x] **Step 1: Retarget the Dockerfile**

Replace:

```dockerfile
COPY .agents/skills/career-evidence /app/career-evidence
```

with:

```dockerfile
COPY server/ /app/server
```

and the entrypoint:

```dockerfile
ENTRYPOINT ["python3", "/app/server/serve.py", "--no-browser"]
```

Env (`CAREER_EVIDENCE_VAULT=/vault`, `CAREER_EVIDENCE_BIND=0.0.0.0`), `EXPOSE 8765`, and the healthcheck stay exactly as they are. `compose.yaml` needs no change (build context `.`, loopback-only publish `127.0.0.1:8765:8765`) — verify, don't edit.

- [x] **Step 2: Retarget .dockerignore**

Replace its contents:

```
*
!server
server/__pycache__
```

- [x] **Step 3: Retarget demo/build_demo.py**

Replace:

```python
SCRIPTS = REPO / ".agents" / "skills" / "career-evidence" / "scripts"
sys.path.insert(0, str(SCRIPTS))
```

with:

```python
SERVER = REPO / "server"
sys.path.insert(0, str(SERVER))
```

- [x] **Step 4: Verify the demo build and the Docker image**

```bash
python3 demo/build_demo.py
docker compose build
CAREER_EVIDENCE_VAULT_HOST=/home/jbped/dev/job-hunt/demo/vault docker compose up -d
sleep 2
curl -fsS http://127.0.0.1:8765/api/schema >/dev/null && echo "docker OK"
docker compose down
```

Expected: demo build completes, image builds, `docker OK` prints. (Docker daemon starts on demand via the socket; no sudo needed.)

- [x] **Step 5: Run the safety tests**

```bash
python3 server/test_safety.py
```

Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add -A
git commit -m "Point Docker and the demo builder at server/"
```

---

### Task 4: Retarget the skills to server/ paths

**Files:**
- Modify: `.agents/skills/career-evidence/SKILL.md` (lines 28, 32-44, 108, 198, 207), `.agents/skills/init-vault/SKILL.md:17`, `.agents/skills/new-application/SKILL.md` (lines 11, 13-14, 30), `.agents/skills/new-person/SKILL.md:32`, `.agents/skills/draft-resume/SKILL.md:12`, `.agents/skills/resume-pdf/SKILL.md:15-16`, `.agents/skills/cover-letter-pdf/SKILL.md:15-16`, `.agents/skills/career-evidence/references/vault-schema.md` (lines 50, 120)

**Interfaces:**
- Consumes: `server/<script>.py` invocation form from Task 1.
- Produces: skills that describe scripts as living in the repo's `server/` directory, still host-neutral.

- [x] **Step 1: Rewrite the script-location wording**

The convention across all skills: scripts are invoked repo-relative as `python3 server/<script>.py`, run from the repository root (the directory that contains both `server/` and `.agents/`). Concretely:

- `career-evidence/SKILL.md:28` — change "Scripts live in this skill's `scripts/`…" to "Scripts live in the repository's `server/` directory; run them from the repository root as `python3 server/<script>.py`." Lines 32-44 keep the bare script names; line 108 `scripts/schema.py` → `server/schema.py`; lines 198 and 207 stay bare names (verify context reads correctly).
- `init-vault/SKILL.md:17` — `` `init_vault.py` (in `../career-evidence/scripts/`) `` → `` `server/init_vault.py` (at the repository root) ``.
- `new-application/SKILL.md:11` — `../career-evidence/scripts/` → `server/` at the repository root; lines 13-14 become `python3 server/new_application.py "<Company>" "<Role>"` and `python3 server/capture_jd.py --app <folder>`; line 30 `scripts/schema.py` → `server/schema.py`.
- `new-person/SKILL.md:32` — `scripts/schema.py` → `server/schema.py`.
- `draft-resume/SKILL.md:12` — retarget the `render_pdf.py` source-format pointer to `server/render_pdf.py`.
- `resume-pdf/SKILL.md:15-16` and `cover-letter-pdf/SKILL.md:15-16` — `python3 server/render_pdf.py --app <folder> --kind resume` (resp. `cover-letter`), dropping the "from `../career-evidence/scripts/`" phrasing.
- `career-evidence/references/vault-schema.md:50` — "(generated from `scripts/schema.py`)" → "(generated from `server/schema.py`)"; line 120 — "defined once in `scripts/schema.py`" → "defined once in `server/schema.py`".

Also sweep for stragglers:

```bash
grep -rn "scripts/" .agents/skills/ --include="*.md"
```

Expected after edits: no hits referring to the old script location (hits about unrelated words are fine — read each).

- [x] **Step 2: Run the safety tests (neutrality gate)**

```bash
python3 server/test_safety.py
```

Expected: PASS — in particular `test_skill_sources_are_host_neutral` (the edits must introduce no provider names).

- [x] **Step 3: Walk one skill against the new paths**

Read `.agents/skills/new-application/SKILL.md` end-to-end and dry-check every command it names resolves: `ls server/new_application.py server/capture_jd.py server/schema.py`. Expected: all exist.

- [x] **Step 4: Commit**

```bash
git add -A
git commit -m "Retarget skills to invoke server/ scripts"
```

---

### Task 5: Docs, generated footers, and CI

**Files:**
- Modify: `README.md` (lines 33, 63, 102-109), `AGENTS.md` (intro reframing + lines 35, 41), `docs/setup.md` (lines 22, 88), `docs/host-adapters.md` (lines 9, 47, 61, 65), `server/schema.py:475`, `server/export_index.py:321`, `extension/README.md:27`, `.github/workflows/release.yml`
- Regenerate: the live vault's `Working Notes/Field Reference.md`

**Interfaces:**
- Consumes: `python3 server/<script>.py` form; `package_app.py` from Task 2.
- Produces: docs that describe the webapp-first layout; CI that tests and packages from `server/`.

- [x] **Step 1: README**

Line 33 → `python server/serve.py --vault demo/vault`; line 63 → `python server/init_vault.py`; delete line 102's "With `scripts/` meaning …" preamble (no longer needed) and rewrite 105-109 as `python server/status.py`, `python server/serve.py`, `python server/new_application.py "Company" "Role"`, `python server/render_pdf.py --app <folder> --kind resume`, `python server/audit_vault.py`.

- [x] **Step 2: AGENTS.md**

Reframe the opening paragraph webapp-first. Replace the current first paragraph with:

```markdown
This repo is a local-first job-hunt webapp where markdown is the database:
a dashboard you run yourself over an Obsidian vault, supplemented by local
CLI AI agents that work the same vault through the same surface. The vault
is located via `.env` (`CAREER_EVIDENCE_VAULT`), by walking upward from the
working directory, or falling back to the gitignored `vault/` at the repo
root. Never commit personal data here — `vault/` stays ignored.
```

Add a short "The server" section before "The skill" noting: the application lives in `server/` (Python stdlib only), serves the dashboard, and owns all deterministic vault operations; the skills in `.agents/skills/` are the AI integration layer and invoke `server/<script>.py`. Update line 35 → "in `server/schema.py`", the regen command → `python3 server/export_index.py --write-field-reference`, and line 41's "run from `scripts/`:" → "run from the repo root:" with `python3 server/test_safety.py` and `python3 server/audit_vault.py`. Update the "skills ship together — `package_skill.py` zips the whole set" sentence to "the release zip is the whole application — `server/package_app.py` builds it".

- [x] **Step 3: docs/setup.md, docs/host-adapters.md, extension/README.md**

- `docs/setup.md:22` — `cd .agents/skills/career-evidence/scripts` → run from the repo root, `python3 server/…`; line 88 — "From `.agents/skills/career-evidence/scripts/`:" → "From the repo root:" (adjust the commands beneath to `server/` paths).
- `docs/host-adapters.md:9` — `.agents/skills/career-evidence/scripts/test_safety.py` → `server/test_safety.py`; line 47 — "work through `career-evidence/scripts/`" → "work through `server/`"; line 61 — "`scripts/package_skill.py` builds a portable zip" → "`server/package_app.py` builds the application zip"; line 65 — "from `.agents/skills/career-evidence/scripts/`, run `python3 test_safety.py`" → "from the repo root, run `python3 server/test_safety.py`".
- `extension/README.md:27` — "Start the dashboard: `python serve.py` (from the skill's `scripts/`)." → "Start the dashboard: `python3 server/serve.py` (from the repo root)."

Then sweep the whole repo for leftovers:

```bash
grep -rn "career-evidence/scripts" --include="*.md" --include="*.yml" --include="*.py" . | grep -v docs/superpowers
```

Expected: no hits (docs/superpowers specs/plans are historical records and stay as written).

- [x] **Step 4: Generated footers + regenerate Field Reference**

- `server/schema.py:475` — footer text → ``regenerate with `python server/export_index.py --write-field-reference`.``
- `server/export_index.py:321` — Skill Matrix footer → ``regenerate with `python server/export_index.py --write-skill-matrix`.`` (the live Skill Matrix updates whenever the user next regenerates it; do not regenerate it now — it belongs to the user's evidence flow).
- Regenerate the vault's Field Reference (sanctioned by AGENTS.md after schema.py changes):

```bash
python3 server/export_index.py --write-field-reference
python3 server/audit_vault.py; echo "exit=$?"
```

Expected: Field Reference rewritten with the new footer; audit `exit=0`.

- [x] **Step 5: ROADMAP.md**

Apply the spec's "Roadmap rewrite" section verbatim in spirit: reframe the product line to "A local-first job-hunt **webapp** where markdown is the database — a dashboard you run yourself, supplemented by local CLI AI agents that work the same vault through the same surface." Mark 0.4 as shipped if the file tracks status, then list: **0.5 — Webapp-first restructure** (this milestone; release artifact becomes the app zip), **0.6 — React frontend** (parity port, committed bundle, old page retired), **0.7 — AI sandbox (investigate)** (open questions copied unchanged from the spec), **Later** items reframed as React feature work over the same API, and the unchanged non-goals. Preserve the file's existing structure and voice — this is a retargeting, not a rewrite from scratch.

- [x] **Step 6: CI workflow**

In `.github/workflows/release.yml`, both steps currently use `working-directory: .agents/skills/career-evidence/scripts`. Change to run from the checkout root:

```yaml
      - name: Safety tests
        run: python3 server/test_safety.py
      - name: Package app
        run: python3 server/package_app.py
```

and retarget the artifact/release attachment from `dist/career-evidence-skill.zip` to `dist/career-evidence-app.zip` (keep the tag-vs-dispatch conditional structure exactly as it is).

- [x] **Step 7: Run the safety tests**

```bash
python3 server/test_safety.py
```

Expected: PASS.

- [x] **Step 8: Commit**

```bash
git add -A
git commit -m "Sweep docs, roadmap, generated footers, and CI to the server/ layout"
```

---

### Task 6: End-to-end verification (spec § Verification 0.5)

**Files:**
- No edits. Fix regressions only if a check fails, each fix committed with a reason.

**Interfaces:**
- Consumes: everything above.
- Produces: the verification evidence for the milestone.

- [x] **Step 1: Tests and audit**

```bash
python3 server/test_safety.py
python3 server/audit_vault.py; echo "exit=$?"
```

Expected: all tests PASS; `exit=0`.

- [x] **Step 2: Dashboard smoke against the demo vault (create lead → archive → restore → PDF)**

```bash
python3 demo/build_demo.py
python3 server/serve.py --vault demo/vault --no-browser &
sleep 2
TOKEN=$(cat demo/vault/.cache/session-token)
curl -fsS http://127.0.0.1:8765/api/state | head -c 200; echo
curl -fsS -X POST http://127.0.0.1:8765/api/leads -H "X-Session-Token: $TOKEN" -H "Content-Type: application/json" -d '{"company":"Smoke Test Co","role":"Restructure Check"}'
```

Before running: read `server/serve.py`'s route table for the exact lead-create, archive, and restore endpoints and payloads (do not guess field names — mirror what `server/assets/ui/index.html` sends). Then: create the lead, archive it, restore it, confirm each via the API or the vault files, and kill the background server (`kill %1`). If port 8765 is busy, pass `--port 8766` consistently.

```bash
command -v ps2pdf >/dev/null && python3 server/render_pdf.py --app <a demo application folder> --kind resume || echo "ps2pdf absent — note in report, skip"
```

Expected: lead lifecycle works; PDF renders if Ghostscript is installed.

- [x] **Step 3: Docker**

```bash
docker compose up --build -d
curl -fsS http://127.0.0.1:8765/api/schema >/dev/null && echo "docker OK"
docker compose down
```

(Requires `CAREER_EVIDENCE_VAULT_HOST` — use the demo vault path as in Task 3.) Expected: `docker OK`.

- [x] **Step 4: App zip from a clean unzip**

```bash
python3 server/package_app.py
ZIPDIR=$(mktemp -d) && unzip -q dist/career-evidence-app.zip -d "$ZIPDIR"
cd "$ZIPDIR" && python3 server/test_safety.py; cd -
```

Expected: safety tests pass inside the unzipped tree (proves runnable-from-unzipped-root; the archive test inside the zip re-verifies no vault data / no provider-named paths).

- [x] **Step 5: Final commit if verification required fixes; report**

Write a short verification report (what ran, what passed, anything skipped and why) to `docs/superpowers/plans/2026-09-02-webapp-first-restructure-verification.md`, commit:

```bash
git add -A
git commit -m "Record milestone 0.5 verification results"
```

Do **not** merge to main and do **not** push — stop and report back.
