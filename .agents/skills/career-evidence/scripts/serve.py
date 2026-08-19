#!/usr/bin/env python3
"""A local dashboard for the vault: where am I, what's coming up, what's due.

Reads through `export_index.py` and writes straight back into the markdown notes.
The index is never written to — after any successful save it is rebuilt from
disk, so the notes remain the only source of truth and a stale cache can never
become the thing you are editing.

Four write operations are allowed, and no others:

  1. Edit a frontmatter field the schema marks UI-editable (one line rewritten)
  2. Append a structured entry built from a template (contact, interview, reference)
  3. Create an application, by calling the same script the CLI calls
  4. Create a person note (one per person, never overwriting)

Everything else — prose, analysis, the verbatim posting — is read-only here and
links out to Obsidian. That boundary is what keeps the notes hand-editable
rather than UI-managed.

Usage:
    python serve.py [--vault PATH] [--port 8765] [--no-browser]
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import hashlib
import json
import mimetypes
import os
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
import traceback
import urllib.parse
import urllib.request
import uuid
import webbrowser

import audit_vault
import export_index
import new_application
import schema
import vaultlib as v

UI_DIR = Path(__file__).resolve().parent.parent / "assets" / "ui"

# Background render jobs, keyed by id. Bounded by how many times someone can
# click a button, so a plain dict is fine.
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()


class RequestError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(message)


# --------------------------------------------------------------------------
# Write guards
# --------------------------------------------------------------------------

def resolve(vault: Path, relative: str) -> Path:
    """Resolve a vault-relative path, refusing anything that escapes the vault."""
    if not relative:
        raise RequestError(400, "no path given")
    target = (vault / relative).resolve()
    try:
        target.relative_to(vault.resolve())
    except ValueError:
        raise RequestError(403, "path is outside the vault")
    if not target.exists():
        raise RequestError(404, f"not found: {relative}")
    if target.name in schema.UI_READONLY_FILES:
        raise RequestError(
            403,
            f"{target.name} is read-only here. The verbatim posting and the submission "
            "record are evidence — edit them in Obsidian if you genuinely must.",
        )
    return target


def check_field(note_type: str, field: str, value: str) -> None:
    editable = schema.UI_EDITABLE.get(note_type)
    if not editable:
        raise RequestError(403, f"notes of type '{note_type}' are not editable here")
    if field not in editable:
        raise RequestError(
            403,
            f"'{field}' is not editable from the dashboard. "
            f"Editable fields: {', '.join(editable)}",
        )
    allowed = schema.allowed_values(note_type, field)
    if allowed and value and value not in allowed:
        raise RequestError(400, f"'{value}' is not one of: {', '.join(allowed)}")


def set_field(vault: Path, payload: dict) -> dict:
    target = resolve(vault, payload.get("path", ""))
    field = str(payload.get("field", ""))
    value = payload.get("value")
    value = "" if value is None else str(value).strip()

    expect = payload.get("fingerprint") or v.fingerprint(target)
    fm, text = v.read_note(target)
    check_field(fm.get("type", ""), field, value)

    updated = v.set_frontmatter_field(text, field, value)
    if updated == text:
        return {"changed": False, "fingerprint": v.fingerprint(target)}

    try:
        fingerprint = v.atomic_write(target, updated, expect=expect, vault=vault)
    except v.ConflictError as error:
        raise RequestError(409, str(error))
    return {"changed": True, "fingerprint": fingerprint}


# The empty-state sentence each template ships, per section. Removing the wrong
# one leaves a sibling section looking broken, so they are matched by heading.
PLACEHOLDERS = {
    "## upcoming": "No upcoming interviews recorded.",
    "## previous": "No previous interviews recorded.",
    "": "No contacts recorded.",
}

REFERENCE_HEADING = "## Entry format"


def _drop_placeholder(text: str, heading: str) -> str:
    """Remove only the empty-state line belonging to the section being written."""
    sentence = PLACEHOLDERS.get(heading.strip().lower())
    if not sentence:
        return text
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == sentence:
            del lines[i]
            if i < len(lines) and not lines[i].strip() and i and not lines[i - 1].strip():
                del lines[i]
            return "\n".join(lines)
    return text


def _append_before_reference(text: str, entry: str) -> str:
    """Insert an entry above the note's `## Entry format` section, if it has one."""
    lines = text.split("\n")
    stop = next((i for i, l in enumerate(lines)
                 if l.strip().lower() == REFERENCE_HEADING.lower()), len(lines))
    while stop > 0 and not lines[stop - 1].strip():
        stop -= 1
    lines[stop:stop] = ["", *entry.rstrip("\n").split("\n")]
    return "\n".join(lines)


def vault_state(vault: Path) -> str:
    """A cheap digest of which notes exist and when they last changed.

    Stat-only — no file is read — so the page can poll it every few seconds and
    refetch the real index only when something on disk actually moved.
    """
    digest = hashlib.sha256()
    for path in sorted(vault.rglob("*.md")):
        if ".cache" in path.parts or ".obsidian" in path.parts:
            continue
        try:
            digest.update(f"{path}:{path.stat().st_mtime_ns}\n".encode())
        except OSError:
            continue  # deleted between listing and stat — the next poll settles it
    return digest.hexdigest()[:16]


def read_note(vault: Path, relative: str) -> dict:
    """Return a note's raw markdown for display.

    Reading is deliberately broader than writing: every note in the vault can be
    read here, including the ones no write path may touch. Being able to see the
    verbatim posting or a submission record without leaving the dashboard is the
    whole point; being able to change them from here is not.
    """
    if not relative:
        raise RequestError(400, "no path given")
    target = (vault / relative).resolve()
    try:
        target.relative_to(vault.resolve())
    except ValueError:
        raise RequestError(403, "path is outside the vault")
    if target.suffix.lower() != ".md":
        raise RequestError(403, "only markdown notes can be read")
    if not target.is_file():
        raise RequestError(404, f"not found: {relative}")

    return {
        "path": relative,
        "name": target.stem,
        "text": target.read_text(encoding="utf-8"),
        "fingerprint": v.fingerprint(target),
        # Notes the dashboard will never write to, so the viewer can say so
        # rather than leaving the reader to wonder why there is no edit affordance.
        "readonly": target.name in schema.UI_READONLY_FILES,
    }


def _section_has_entries(text: str, heading: str) -> bool:
    """Whether a section still holds at least one `###` entry."""
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines)
                  if l.strip().lower() == heading.strip().lower()), None)
    if start is None:
        return False
    for line in lines[start + 1:]:
        stripped = line.strip()
        if stripped.startswith("## "):
            return False
        if stripped.startswith("### "):
            return True
    return False


def append_entry(vault: Path, payload: dict) -> dict:
    """Append a contact or interview block, composed the same way a person would."""
    target = resolve(vault, payload.get("path", ""))
    heading = str(payload.get("heading", "")).strip()
    title = str(payload.get("title", "")).strip()
    fields = payload.get("fields") or {}

    if not title:
        raise RequestError(400, "an entry needs a title")
    if not isinstance(fields, dict):
        raise RequestError(400, "fields must be an object")

    fm, text = v.read_note(target)
    # Entries belong in entry-shaped notes. Anything else — the brief, an
    # evidence note — is hand-structured and not this API's to grow.
    if target.name not in ("Contacts.md", "Interviews.md") and fm.get("type") != "person":
        raise RequestError(403, "entries may be appended only to Contacts.md, "
                                "Interviews.md, or a person note")
    expect = payload.get("fingerprint") or v.fingerprint(target)
    level = "###" if heading else "##"
    lines = [f"{level} {title}"]
    for key, value in fields.items():
        label = str(key).replace("_", " ").strip()
        label = label[:1].upper() + label[1:]
        lines.append(f"- {label}: {str(value).strip() or 'Unknown'}")
    entry = "\n".join(lines)

    # Notes that document their own format keep that reference last; a new entry
    # belongs with the data above it, not appended after the instructions.
    text = _drop_placeholder(text, heading)
    try:
        if heading:
            updated = v.append_section_entry(text, heading, entry)
        else:
            updated = _append_before_reference(text, entry)
    except ValueError as error:
        raise RequestError(400, str(error))

    try:
        fingerprint = v.atomic_write(target, updated, expect=expect, vault=vault)
    except v.ConflictError as error:
        raise RequestError(409, str(error))
    return {"changed": True, "fingerprint": fingerprint}


def complete_interview(vault: Path, payload: dict) -> dict:
    """Move an interview from Upcoming to Previous and append its outcome.

    Defined as a structural move rather than an edit: the entry is relocated
    verbatim and the outcome fields are added beneath it. Nothing around it is
    reflowed, so a hand-written note survives the operation unchanged.
    """
    target = resolve(vault, payload.get("path", ""))
    title = str(payload.get("title", "")).strip()
    outcome = payload.get("fields") or {}

    if target.name != "Interviews.md":
        raise RequestError(403, "interview completion applies only to Interviews.md")
    expect = payload.get("fingerprint") or v.fingerprint(target)
    _, text = v.read_note(target)
    lines = text.split("\n")

    start = next((i for i, l in enumerate(lines)
                  if l.strip().startswith("### ") and l.strip()[4:].strip() == title), None)
    if start is None:
        raise RequestError(404, f"no upcoming interview titled '{title}'")

    end = len(lines)
    for i in range(start + 1, len(lines)):
        stripped = lines[i].lstrip()
        if stripped.startswith("#") and len(stripped) - len(stripped.lstrip("#")) <= 3:
            end = i
            break
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1

    block = lines[start:end]
    for key, value in outcome.items():
        label = str(key).replace("_", " ").strip()
        label = label[:1].upper() + label[1:]
        block.append(f"- {label}: {str(value).strip() or 'Unknown'}")

    del lines[start:end]
    while start < len(lines) and not lines[start].strip() and \
            (start == 0 or not lines[start - 1].strip()):
        del lines[start]

    remaining = _drop_placeholder("\n".join(lines), "## Previous")
    try:
        updated = v.append_section_entry(remaining, "## Previous", "\n".join(block))
    except ValueError as error:
        raise RequestError(400, str(error))

    # If that was the last upcoming interview, put the empty-state sentence back
    # so the section reads as deliberately empty rather than truncated.
    if not _section_has_entries(updated, "## Upcoming"):
        updated = v.append_section_entry(updated, "## Upcoming",
                                         PLACEHOLDERS["## upcoming"])

    try:
        fingerprint = v.atomic_write(target, updated, expect=expect, vault=vault)
    except v.ConflictError as error:
        raise RequestError(409, str(error))
    return {"changed": True, "fingerprint": fingerprint}


def create_application(vault: Path, payload: dict) -> dict:
    company = str(payload.get("company", "")).strip()
    position = str(payload.get("position", "")).strip()
    if not company or not position:
        raise RequestError(400, "company and role are both required")
    try:
        folder = new_application.create(
            vault, company, position,
            url=str(payload.get("url", "")).strip(),
            discovery=str(payload.get("discovery", "")).strip(),
            detail=str(payload.get("detail", "")).strip(),
            source=str(payload.get("source", "")).strip(),
        )
    except SystemExit as error:
        raise RequestError(400, str(error))
    return {"path": str(folder.relative_to(vault))}


def create_person(vault: Path, payload: dict) -> dict:
    """Create a People/<Folder>/<Name>.md note — the one-note-per-person entry point.

    Deliberately minimal: it names the person, their job-search role, and how
    they know the user professionally. Everything deeper — application
    involvements, reference consent — is either an editable field or belongs in
    Obsidian.
    """
    name = str(payload.get("name", "")).strip()
    if not name:
        raise RequestError(400, "a name is required")
    safe = new_application.safe_name(name)
    if not safe:
        raise RequestError(400, f"'{name}' does not reduce to a usable file name")

    relationship = str(payload.get("relationship", "")).strip()
    if relationship and relationship not in schema.CONTACT_RELATIONSHIP:
        raise RequestError(
            400, f"'{relationship}' is not one of: {', '.join(schema.CONTACT_RELATIONSHIP)}")

    professional_relationship = str(payload.get("professional_relationship", "")).strip()
    if (professional_relationship and
            professional_relationship not in schema.PROFESSIONAL_RELATIONSHIP):
        raise RequestError(
            400, f"'{professional_relationship}' is not one of: "
                 f"{', '.join(schema.PROFESSIONAL_RELATIONSHIP)}")

    group = str(payload.get("folder", "")).strip()
    if group and group not in schema.PEOPLE_FOLDERS:
        raise RequestError(
            400, f"'{group}' is not one of: {', '.join(schema.PEOPLE_FOLDERS)}")
    if not group:
        # Warmth is the folder axis: a known professional relationship means
        # Network even for a recruiter, everyone else exists because of the
        # search.
        if professional_relationship:
            group = "Network"
        elif relationship == "recruiter":
            group = "Recruiters"
        else:
            group = "Job Hunt"

    people_dir = vault / "People"
    existing = next(people_dir.rglob(f"{safe}.md"), None) if people_dir.is_dir() else None
    if existing is not None:
        raise RequestError(409, f"{existing.relative_to(vault)} already exists — one note "
                                "per person; add to it instead of creating a second")
    folder = people_dir / group
    folder.mkdir(parents=True, exist_ok=True)
    target = (folder / f"{safe}.md").resolve()
    try:
        target.relative_to(vault.resolve())
    except ValueError:
        raise RequestError(403, "path is outside the vault")

    lines = ["---", "type: person", f"name: {name}"]
    if relationship:
        lines += ["relationships:", f"  - {relationship}"]
    if professional_relationship:
        lines += ["professional_relationships:", f"  - {professional_relationship}"]
    for key in ("company_context", "email", "phone"):
        value = str(payload.get(key, "")).strip()
        if value:
            lines.append(f"{key}: {value}")
    lines += ["---", "", f"# {name}", "", "## Applications", "", "## Notes", ""]

    v.atomic_write(target, "\n".join(lines))
    return {"path": str(target.relative_to(vault))}


def start_render(vault: Path, payload: dict) -> dict:
    """Kick off a PDF render on a worker thread and return a job id to poll.

    Rendering shells out to Ghostscript and takes seconds; doing it inline would
    block the whole server, so the page polls instead.
    """
    folder = resolve(vault, str(payload.get("path", "")))
    kind = str(payload.get("kind", "resume"))
    pages = int(payload.get("pages", 1) or 1)
    if kind not in ("resume", "cover-letter"):
        raise RequestError(400, "kind must be 'resume' or 'cover-letter'")
    if not folder.is_dir():
        raise RequestError(404, "application folder not found")

    job_id = uuid.uuid4().hex[:12]
    with JOBS_LOCK:
        JOBS[job_id] = {"state": "running", "kind": kind}

    def run() -> None:
        try:
            import render_pdf
            out = render_pdf.render(vault, folder, kind, pages, preview=True)
            result = {
                "state": "done",
                "kind": kind,
                "pdf": str(out["pdf"].relative_to(vault)),
                "preview": str(out["preview"].relative_to(vault)) if out["preview"] else None,
                "pages": out["pages"],
                "notes": out["notes"],
                "problems": out["problems"],
            }
        except SystemExit as error:
            result = {"state": "failed", "kind": kind, "error": str(error)}
        except Exception:
            result = {"state": "failed", "kind": kind, "error": traceback.format_exc(limit=3)}
        with JOBS_LOCK:
            JOBS[job_id] = result

    threading.Thread(target=run, daemon=True).start()
    return {"job": job_id}


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    vault: Path = Path(".")
    server_version = "career-evidence"

    def log_message(self, fmt: str, *args) -> None:
        if "?" in self.path or self.command != "GET":
            sys.stderr.write(f"  {self.command} {self.path}\n")

    # -- helpers -----------------------------------------------------------

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status: int = 200) -> None:
        self._send(status, json.dumps(data).encode("utf-8"), "application/json")

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            raise RequestError(400, "request body was not valid JSON")

    # -- routes ------------------------------------------------------------

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path
        try:
            if route == "/":
                page = UI_DIR / "index.html"
                if not page.exists():
                    raise RequestError(500, f"UI template missing: {page}")
                html = page.read_text(encoding="utf-8").replace(
                    "__SESSION_TOKEN__", self.token)
                self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
            elif route == "/api/index":
                self._json(export_index.build(self.vault))
            elif route == "/api/state":
                self._json({"state": vault_state(self.vault)})
            elif route == "/api/schema":
                self._json({
                    "status": schema.APPLICATION_STATUS,
                    "terminal": sorted(schema.TERMINAL_STATUS),
                    "discovery_method": schema.DISCOVERY_METHOD,
                    "compensation_status": schema.COMPENSATION_STATUS,
                    "compensation_period": schema.COMPENSATION_PERIOD,
                    "work_model": schema.WORK_MODEL,
                    "stage": schema.INTERVIEW_STAGE,
                    "method": schema.INTERVIEW_METHOD,
                    "contact_relationship": schema.CONTACT_RELATIONSHIP,
                    "professional_relationship": schema.PROFESSIONAL_RELATIONSHIP,
                    "people_folders": schema.PEOPLE_FOLDERS,
                    "reference_permission": schema.REFERENCE_PERMISSION,
                    "contact_audience": schema.CONTACT_AUDIENCE,
                    "editable": schema.UI_EDITABLE,
                    "vault_name": self.vault.name,
                })
            elif route == "/api/note":
                query = urllib.parse.parse_qs(parsed.query)
                self._json(read_note(self.vault, (query.get("path") or [""])[0]))
            elif route == "/api/audit":
                report = audit_vault.audit(self.vault)
                self._json({"errors": report.errors, "warnings": report.warnings})
            elif route.startswith("/api/job/"):
                with JOBS_LOCK:
                    job = JOBS.get(route.rsplit("/", 1)[-1])
                if job is None:
                    raise RequestError(404, "unknown job")
                self._json(job)
            elif route.startswith("/file/"):
                self._serve_file(urllib.parse.unquote(route[len("/file/"):]))
            else:
                raise RequestError(404, "no such route")
        except RequestError as error:
            self._json({"error": str(error)}, error.status)
        except Exception:
            traceback.print_exc()
            self._json({"error": "internal error; see the terminal"}, 500)

    def _serve_file(self, relative: str) -> None:
        """Serve a preview image or PDF from inside the vault, read-only."""
        target = (self.vault / relative).resolve()
        try:
            target.relative_to(self.vault.resolve())
        except ValueError:
            raise RequestError(403, "outside the vault")
        if not target.is_file():
            raise RequestError(404, "not found")
        if target.suffix.lower() not in (".png", ".pdf", ".jpg", ".jpeg"):
            raise RequestError(403, "only images and PDFs are served")
        kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self._send(200, target.read_bytes(), kind)

    def do_POST(self) -> None:
        route = urllib.parse.urlparse(self.path).path
        # 127.0.0.1 keeps the network out, but not a browser tab: any webpage
        # can fire POSTs at localhost. Writes therefore require the per-session
        # token the served page carries, a JSON content type, and — when a
        # browser sends one — a local Origin.
        origin = self.headers.get("Origin")
        if origin and urllib.parse.urlparse(origin).hostname not in ("127.0.0.1", "localhost"):
            self._json({"error": "cross-origin writes are not allowed"}, 403)
            return
        content_type = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if content_type != "application/json":
            self._json({"error": "writes must be application/json"}, 403)
            return
        if not secrets.compare_digest(self.headers.get("X-Session-Token", ""), self.token):
            self._json({"error": "missing or invalid session token; reload the page"}, 403)
            return
        handlers = {
            "/api/field": set_field,
            "/api/entry": append_entry,
            "/api/interview/complete": complete_interview,
            "/api/application": create_application,
            "/api/person": create_person,
            "/api/render": start_render,
        }
        try:
            handler = handlers.get(route)
            if handler is None:
                raise RequestError(404, "no such route")
            payload = self._body()
            result = handler(self.vault, payload)
            # Any write invalidates the projection; rebuild it from the notes so
            # the index can never drift from what is on disk.
            if route != "/api/render" and result.get("changed", True):
                export_index.write(self.vault)
            self._json(result)
        except RequestError as error:
            self._json({"error": str(error)}, error.status)
        except Exception:
            traceback.print_exc()
            self._json({"error": "internal error; see the terminal"}, 500)


# --------------------------------------------------------------------------
# Single instance
# --------------------------------------------------------------------------
# A dashboard left running with old code answers with old rules, which reads as
# vault corruption. Each server records itself in the vault's .cache; the next
# start stops the previous one before taking over.

def _pidfile(vault: Path) -> Path:
    return vault / ".cache" / "serve.pid"


def _is_dashboard(port: int) -> bool:
    """Whether something on this local port identifies as this dashboard."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/schema",
                                    timeout=1) as response:
            return response.headers.get("Server", "").startswith(Handler.server_version)
    except OSError:
        return False


def stop_previous(vault: Path) -> bool:
    """Stop the dashboard the pidfile names, if it is still one of ours.

    The PID alone is not trusted — PIDs get recycled, and killing whatever now
    holds the number would be worse than the stale server. The process is only
    signalled after the port it recorded answers as a career-evidence dashboard.
    Returns whether a running dashboard was actually stopped.
    """
    pidfile = _pidfile(vault)
    if not pidfile.is_file():
        return False
    try:
        info = json.loads(pidfile.read_text(encoding="utf-8"))
        pid, port = int(info["pid"]), int(info["port"])
    except (ValueError, KeyError, json.JSONDecodeError):
        pidfile.unlink(missing_ok=True)
        return False

    stopped = False
    if pid != os.getpid() and _is_dashboard(port):
        stopped = True
        print(f"Stopping the previous dashboard (pid {pid}, port {port})…")
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        else:
            for _ in range(30):
                if not _is_dashboard(port):
                    break
                time.sleep(0.1)
    pidfile.unlink(missing_ok=True)
    return stopped


def write_pidfile(vault: Path, port: int) -> None:
    pidfile = _pidfile(vault)
    pidfile.parent.mkdir(parents=True, exist_ok=True)
    pidfile.write_text(json.dumps({"pid": os.getpid(), "port": port}),
                       encoding="utf-8")


def default_port() -> int:
    raw = os.environ.get("CAREER_EVIDENCE_PORT") or v.load_env().get("CAREER_EVIDENCE_PORT")
    try:
        return int(raw) if raw else 8765
    except ValueError:
        return 8765


def detach(vault: Path, args) -> int:
    """Relaunch the server as its own session and return once it answers.

    For agent harnesses and scripts that kill their child process group when a
    command finishes — the detached server escapes that group, so `--detach`
    returns immediately while the dashboard keeps running.
    """
    log = vault / ".cache" / "serve.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(Path(__file__).resolve()),
           "--port", str(args.port), "--no-browser"]
    if args.vault:
        cmd += ["--vault", args.vault]
    kwargs: dict = {}
    if os.name == "nt":
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        kwargs["creationflags"] = 0x00000008 | 0x00000200
    else:
        kwargs["start_new_session"] = True
    with open(log, "ab") as handle:
        subprocess.Popen(cmd, stdout=handle, stderr=handle,
                         stdin=subprocess.DEVNULL, **kwargs)

    for _ in range(50):
        if _is_dashboard(args.port):
            break
        time.sleep(0.1)
    else:
        raise SystemExit(f"The dashboard did not come up; see {log}")

    url = f"http://127.0.0.1:{args.port}/"
    print(f"Dashboard: {url} (running in the background)")
    print(f"Log:       {log}")
    print("Stop it with: python serve.py --stop")
    if not args.no_browser:
        webbrowser.open(url)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault")
    ap.add_argument("--port", type=int, default=default_port())
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--detach", action="store_true",
                    help="start in the background and return immediately")
    ap.add_argument("--stop", action="store_true",
                    help="stop the running dashboard and exit")
    args = ap.parse_args()

    vault = v.require_vault(args.vault)
    if args.stop:
        print("Stopped." if stop_previous(vault) else "No dashboard was running.")
        return 0
    if args.detach:
        return detach(vault, args)

    Handler.vault = vault
    Handler.token = secrets.token_hex(16)
    stop_previous(vault)
    export_index.write(vault)

    # 127.0.0.1 rather than 0.0.0.0: this server can write to personal data, so
    # it must not be reachable from the network. Writes additionally require the
    # per-session token injected into the served page.
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError as error:
        raise SystemExit(
            f"Could not bind 127.0.0.1:{args.port} ({error.strerror}).\n"
            "Something else holds the port — an untracked older dashboard, or "
            "another program. Stop it, or pass --port to use a different one."
        )
    write_pidfile(vault, args.port)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Vault:     {vault}")
    print(f"Dashboard: {url}")
    print("Editing happens in Obsidian; this writes only structured fields and entries.")
    print("Ctrl+C to stop.\n")

    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        pidfile = _pidfile(vault)
        try:
            if json.loads(pidfile.read_text(encoding="utf-8")).get("pid") == os.getpid():
                pidfile.unlink()
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
