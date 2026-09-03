#!/usr/bin/env python3
"""Conversations with a local AI CLI, relayed between the browser and stdin/stdout.

One conversation is one `claude -p` subprocess speaking stream-json in both
directions: a user turn goes in as a JSON line on stdin, the agent's events
come back as JSON lines on stdout and are handed to whichever SSE connection is
watching. The agent works the vault through its own file tools; this module
never writes a note on its behalf.

Two boundaries are not negotiable and are pinned by test_safety.py:

  * every spawn carries `--restricted` (no Bash, no WebFetch, file tools
    confined to the working directories) and the only `--add-dir` is the vault
  * arguments are always a list handed to Popen — no shell, ever, so nothing a
    user or a job posting types can become a command

Only the session index is persisted, in the vault's `.cache/`: ids, titles,
timestamps. Transcripts are the CLI's own business and `.cache/` is derived and
disposable — losing it loses the chat list, never career data.
"""

from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import threading
import time
import uuid

APP_ROOT = Path(__file__).resolve().parent.parent
INDEX_NAME = "agent-sessions.json"
DEFAULT_AGENT_BIN = "claude"

# Everything the evidence interview needs and nothing more: read the vault and
# the skill, write notes back. No Bash, no WebFetch, no WebSearch, no
# subagents, no MCP — see build_args for why each of those needs saying.
TOOLS = ("Read", "Write", "Edit", "Glob", "Grep")

# One conversation's worth of events is small; this only stops a runaway agent
# from growing the buffer without bound.
MAX_BUFFERED_EVENTS = 20000

# How long a fresh spawn gets to prove it is alive before the POST answers. A
# healthy CLI emits its init event well inside this; an unauthenticated or
# missing one exits, and the caller gets a clear error instead of a hang.
START_GRACE_SECONDS = 20.0

# What a new conversation is told, and nothing more. The workflow itself lives
# in the career-evidence skill and is read from disk by the agent — forking its
# text into this constant would give the vault two sources of truth for how an
# interview is run, which is exactly what the skill exists to prevent.
INTERVIEW_SKILL = ".agents/skills/career-evidence/references/evidence-interview.md"

INTERVIEW_PROMPT = (
    "You are conducting an evidence interview for this job-hunt vault, through "
    "a chat panel in the dashboard. Before asking anything, read "
    f"{INTERVIEW_SKILL} and the skill it belongs to "
    "(.agents/skills/career-evidence/SKILL.md), then orient yourself in the "
    "vault: its Job Hunt Dashboard and the Career Evidence notes the interview "
    "concerns. Follow that workflow exactly; it, not this prompt, is the source "
    "of truth for how an interview is run. Write only markdown notes inside the "
    "vault, and never invent an accomplishment, a metric, or a date the person "
    "did not give you."
)

AGENT_UNAVAILABLE = (
    "The AI agent could not start. Check that the `claude` CLI is installed and "
    "signed in — in Docker that means the credential mount described in "
    "docs/setup.md."
)


def agent_bin() -> str:
    return os.environ.get("CAREER_EVIDENCE_AGENT_BIN") or DEFAULT_AGENT_BIN


# --------------------------------------------------------------------------
# The persisted index
# --------------------------------------------------------------------------

def index_path(vault: Path) -> Path:
    return vault / ".cache" / INDEX_NAME


def load_index(vault: Path) -> list[dict]:
    """Every past conversation, newest first.

    A missing or corrupt file is an empty list, never an exception: this is a
    disposable cache and a broken one must not stop the dashboard from serving.
    """
    try:
        data = json.loads(index_path(vault).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    entries = data.get("sessions") if isinstance(data, dict) else data
    if not isinstance(entries, list):
        return []
    clean = [e for e in entries if isinstance(e, dict) and e.get("id")]
    return sorted(clean, key=lambda e: str(e.get("updated") or ""), reverse=True)


def save_index(vault: Path, entries: list[dict]) -> None:
    target = index_path(vault)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".json.tmp")
    temp.write_text(json.dumps({"sessions": entries}, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, target)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def title_from(message: str, limit: int = 60) -> str:
    text = " ".join(str(message or "").split())
    if not text:
        return "Untitled interview"
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def record_turn(vault: Path, session_id: str, message: str,
                application: str | None = None) -> dict:
    """Create or touch this conversation's index entry and return it."""
    entries = load_index(vault)
    for entry in entries:
        if entry.get("id") == session_id:
            entry["updated"] = _now()
            if application:
                entry["application"] = application
            break
    else:
        entry = {"id": session_id, "title": title_from(message),
                 "application": application or "",
                 "created": _now(), "updated": _now()}
        entries.append(entry)
    save_index(vault, entries)
    return entry


def known(vault: Path, session_id: str) -> bool:
    return any(e.get("id") == session_id for e in load_index(vault))


# --------------------------------------------------------------------------
# Spawning
# --------------------------------------------------------------------------

def build_args(vault: Path, session_id: str, *, resume: bool,
               binary: str | None = None,
               system_prompt: str | None = None) -> list[str]:
    """The exact argv for one conversation.

    `--verbose` is not decoration: the CLI refuses `--print` with
    `--output-format stream-json` without it. `--permission-mode acceptEdits`
    is likewise required — headless, with nobody to answer a prompt, every
    write the agent attempts is otherwise denied. Neither loosens
    `--restricted`, which still refuses bypassPermissions and keeps the file
    tools inside the working directories.

    `--restricted` alone was not enough for "files in the vault and nothing
    else", checked against claude 2.1.251: it drops Bash and WebFetch but
    leaves WebSearch and the rest of the built-in set, and it still loads the
    user's MCP servers. So the tools are named explicitly and
    `--strict-mcp-config` shuts the MCP door. A captured job posting is text
    an attacker wrote; this is what makes a prompt-injected agent unable to do
    anything with it but edit markdown the audit then checks.
    """
    args = [binary or agent_bin(),
            "-p",
            "--verbose",
            "--output-format", "stream-json",
            "--input-format", "stream-json",
            "--include-partial-messages",
            "--restricted",
            "--strict-mcp-config",
            "--tools", ",".join(TOOLS),
            "--permission-mode", "acceptEdits",
            "--add-dir", str(vault)]
    if resume:
        args += ["--resume", session_id]
    else:
        args += ["--session-id", session_id]
    if system_prompt:
        args += ["--append-system-prompt", system_prompt]
    return args


class LiveSession:
    """One running agent process and the events it has produced so far.

    Events are buffered rather than queued so a reconnecting EventSource can
    replay from where it left off, and so a POST can tell a healthy start from
    a dead one before it answers.
    """

    def __init__(self, vault: Path, session_id: str, proc: subprocess.Popen):
        self.vault = vault
        self.id = session_id
        self.proc = proc
        self.events: list[dict] = []
        # Counted separately from `events`: a process that only ever wrote to
        # stderr has not started, it has complained.
        self.spoke = 0
        self.closed = False
        self._lock = threading.Condition()
        self._readers = [
            threading.Thread(target=self._pump_stdout, daemon=True),
            threading.Thread(target=self._pump_stderr, daemon=True),
        ]
        for thread in self._readers:
            thread.start()

    # -- event plumbing ------------------------------------------------

    def _append(self, event: dict) -> None:
        with self._lock:
            if len(self.events) < MAX_BUFFERED_EVENTS:
                self.events.append(event)
            self._lock.notify_all()

    def _pump_stdout(self) -> None:
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                event = {"type": "agent_output", "text": line}
            self.spoke += 1
            self._append(event)
            if isinstance(event, dict) and event.get("type") == "result":
                self._append({"type": "done"})
        self._append({"type": "exit", "code": self.proc.wait()})
        self._append({"type": "done"})

    def _pump_stderr(self) -> None:
        for line in self.proc.stderr:
            line = line.strip()
            if line:
                self._append({"type": "agent_error", "text": line})

    def follow(self, start: int = 0, timeout: float = 30.0):
        """Yield buffered events from `start` onwards, blocking for new ones."""
        index = start
        while True:
            with self._lock:
                if index >= len(self.events):
                    if self.closed and self.proc.poll() is not None:
                        return
                    self._lock.wait(timeout)
                if index >= len(self.events):
                    yield None  # a keepalive, so a dead socket is noticed
                    continue
                event = self.events[index]
            index += 1
            yield event

    def wait_for_start(self, timeout: float = START_GRACE_SECONDS) -> None:
        """Block until the process has said something, or raise if it died."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.spoke:
                return
            if self.proc.poll() is not None:
                raise AgentUnavailable(self._death_note())
            time.sleep(0.05)

    def _death_note(self) -> str:
        detail = " ".join(e.get("text", "") for e in self.events
                          if e.get("type") == "agent_error")[:400]
        return f"{AGENT_UNAVAILABLE} ({detail.strip()})" if detail else AGENT_UNAVAILABLE

    # -- turns and teardown --------------------------------------------

    def submit(self, message: str) -> None:
        line = json.dumps({
            "type": "user",
            "message": {"role": "user", "content": [{"type": "text", "text": message}]},
        })
        try:
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError, OSError):
            raise AgentUnavailable(self._death_note())

    def close(self) -> None:
        self.closed = True
        for stream in (self.proc.stdin,):
            try:
                stream.close()
            except (OSError, ValueError):
                pass
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)
        for stream in (self.proc.stdout, self.proc.stderr):
            try:
                stream.close()
            except (OSError, ValueError):
                pass
        with self._lock:
            self._lock.notify_all()


class AgentUnavailable(Exception):
    """The agent process could not be started or has died."""


_LIVE: dict[str, LiveSession] = {}
_LIVE_LOCK = threading.Lock()


def live(session_id: str) -> LiveSession | None:
    with _LIVE_LOCK:
        session = _LIVE.get(session_id)
    if session and session.proc.poll() is not None and session.closed:
        return None
    return session


def spawn(vault: Path, session_id: str, *, resume: bool,
          system_prompt: str | None = None) -> LiveSession:
    """Start the agent for this conversation. Never uses a shell.

    A fresh conversation is seeded with the interview pointer; a resumed one is
    not — `--resume` carries the original system prompt along with the history.
    """
    if system_prompt is None and not resume:
        system_prompt = INTERVIEW_PROMPT
    args = build_args(vault, session_id, resume=resume, system_prompt=system_prompt)
    try:
        proc = subprocess.Popen(
            args,
            cwd=str(APP_ROOT),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
        )
    except OSError as error:
        raise AgentUnavailable(f"{AGENT_UNAVAILABLE} ({error.strerror})")
    session = LiveSession(vault, session_id, proc)
    with _LIVE_LOCK:
        previous = _LIVE.get(session_id)
        _LIVE[session_id] = session
    if previous is not None:
        previous.close()
    return session


def new_id() -> str:
    return str(uuid.uuid4())


def close(session_id: str) -> bool:
    with _LIVE_LOCK:
        session = _LIVE.pop(session_id, None)
    if session is None:
        return False
    session.close()
    return True


def close_all() -> None:
    """Reap every live conversation — called when the server stops."""
    with _LIVE_LOCK:
        sessions = list(_LIVE.values())
        _LIVE.clear()
    for session in sessions:
        session.close()
