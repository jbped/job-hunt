#!/usr/bin/env python3
"""Shared vault I/O: discovery, frontmatter reading, and safe surgical writes.

Two deliberate design choices here, because the vault is hand-edited markdown
and the user's formatting is theirs to keep:

1. Reading and writing are asymmetric. Reading parses frontmatter into a dict.
   Writing never re-emits that dict — it rewrites the single line that changed
   and leaves every other byte alone. A parse/re-emit round trip would quietly
   reorder keys, restyle lists, and strip blank lines the user put there.

2. Writes are atomic and guarded. Obsidian may hold the same file open and
   autosave over us, so callers pass the fingerprint they read the file at and
   the write is refused if the file moved underneath.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import os
import shutil
import tempfile
import time

FRONTMATTER_FENCE = "---"


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "assets" / "templates"
ENV_VAR = "CAREER_EVIDENCE_VAULT"


def _repo_root() -> Path:
    """The checkout this skill lives in — where .env sits.

    The skill nests at <repo>/.agents/skills/career-evidence, so the depth is
    fixed, but search for the marker anyway: someone may vendor the skill at a
    different depth, and a wrong guess would silently ignore their .env.
    """
    for candidate in [SKILL_ROOT, *SKILL_ROOT.parents]:
        if (candidate / ".git").exists() or (candidate / ".env").is_file():
            return candidate
    return SKILL_ROOT


REPO_ROOT = _repo_root()

# The fallback when nothing is configured: a vault inside the checkout itself.
# It is gitignored — personal data stays out of history even when it lives here.
DEFAULT_VAULT = REPO_ROOT / "vault"


def load_env(path: Path | None = None) -> dict[str, str]:
    """Read KEY=VALUE lines from the repo's .env. Real environment variables win."""
    env_file = path or REPO_ROOT / ".env"
    values: dict[str, str] = {}
    if not env_file.is_file():
        return values
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def is_vault(candidate: Path) -> bool:
    return (candidate / "Job Hunt Dashboard.md").exists() and (candidate / "Career Evidence").is_dir()


def configured_vault() -> Path | None:
    """The vault named by the environment or the repo's .env, if it is set."""
    raw = os.environ.get(ENV_VAR) or load_env().get(ENV_VAR)
    return Path(raw).expanduser().resolve() if raw else None


def find_vault(start: Path | str | None = None) -> Path | None:
    """Resolve the vault: explicit path, configuration, upward search, then
    the repo's own gitignored `vault/`.

    Upward search outranks the repo default so the scripts still work when run
    from inside a vault that is not the configured one — a friend's checkout,
    or a second vault used for testing.
    """
    if start:
        candidate = Path(start).expanduser().resolve()
        return candidate if is_vault(candidate) else None

    configured = configured_vault()
    if configured and is_vault(configured):
        return configured

    here = Path.cwd()
    for candidate in [here, *here.parents]:
        if is_vault(candidate):
            return candidate

    if is_vault(DEFAULT_VAULT):
        return DEFAULT_VAULT
    return None


def require_vault(start: Path | str | None = None) -> Path:
    vault = find_vault(start)
    if vault is None:
        configured = configured_vault()
        if start:
            detail = f"'{start}' is not a vault."
        elif configured:
            detail = f"{ENV_VAR} points at '{configured}', which is not a vault."
        else:
            detail = (f"No {ENV_VAR} is set and no vault was found above "
                      f"{Path.cwd()} or at {DEFAULT_VAULT}.")
        raise SystemExit(
            f"{detail}\n"
            "A vault is a directory containing both 'Job Hunt Dashboard.md' and 'Career Evidence/'.\n"
            f"Set {ENV_VAR} in {REPO_ROOT / '.env'}, pass --vault <path>, "
            "or run init_vault.py to create one."
        )
    return vault


# --------------------------------------------------------------------------
# Frontmatter reading
# --------------------------------------------------------------------------

def split_frontmatter(text: str) -> tuple[list[str], str]:
    """Return (frontmatter lines without fences, body). Empty list if none."""
    if not text.startswith(FRONTMATTER_FENCE):
        return [], text
    lines = text.split("\n")
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONTMATTER_FENCE:
            return lines[1:i], "\n".join(lines[i + 1:])
    return [], text


def parse_frontmatter(text: str) -> dict:
    """Parse the near-flat YAML subset this vault uses.

    Handles `key: value`, `key:` with an indented `- item` list, quoted
    scalars, and one read-only nesting level: `key:` followed by indented
    `name: {inline: map}` lines (the contact-profile `contacts` shape).
    Deliberately not a general YAML parser — anything deeper stays out of the
    vault because the surgical writer below could not safely round-trip it.
    """
    fm_lines, _ = split_frontmatter(text)
    data: dict = {}
    key: str | None = None
    for raw in fm_lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith((" ", "\t")):
            stripped = raw.lstrip()
            if stripped.startswith("- "):
                if key is not None:
                    # The parent line was `key:` with no value, so it landed as
                    # None; the first list item reveals it is actually a list.
                    if not isinstance(data.get(key), list):
                        data[key] = []
                    data[key].append(_scalar(stripped[2:].strip()))
            elif ":" in stripped and key is not None:
                if not isinstance(data.get(key), dict):
                    data[key] = {}
                sub, _, value = stripped.partition(":")
                data[key][sub.strip()] = _scalar(value.strip()) if value.strip() else None
            continue
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        key = key.strip()
        value = value.strip()
        data[key] = _scalar(value) if value else None
    return data


def _split_inline(inner: str) -> list[str]:
    """Split an inline `[...]`/`{...}` body on commas outside quotes."""
    parts, buf, quote = [], "", ""
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            buf += ch
        elif ch == ",":
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return parts


def _scalar(value: str):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [_scalar(v.strip()) for v in _split_inline(inner)] if inner else []
    if value.startswith("{") and value.endswith("}"):
        out = {}
        for part in _split_inline(value[1:-1].strip()):
            if ":" not in part:
                continue
            k, _, v = part.partition(":")
            out[k.strip()] = _scalar(v.strip())
        return out
    return value


def read_note(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    return parse_frontmatter(text), text


# --------------------------------------------------------------------------
# Fingerprinting — the concurrency guard
# --------------------------------------------------------------------------

def fingerprint(path: Path) -> str:
    """Cheap identity for a file's current state: mtime plus content hash.

    The hash alone would be enough for correctness; the mtime makes the common
    'nothing changed' case obvious in logs and error messages.
    """
    st = path.stat()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return f"{st.st_mtime_ns}-{digest}"


class ConflictError(Exception):
    """The file changed on disk since the caller read it."""


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------

def backup(path: Path, vault: Path, keep: int = 20) -> Path:
    """Copy a note into .cache/backups before the first write that touches it.

    The vault is not under version control, so this is the only undo available
    when a write turns out to be wrong.
    """
    backups = vault / ".cache" / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    safe = str(path.relative_to(vault)).replace(os.sep, "__")
    target = backups / f"{safe}.{stamp}.bak"
    shutil.copy2(path, target)

    existing = sorted(backups.glob(f"{safe}.*.bak"))
    for old in existing[:-keep]:
        old.unlink()
    return target


def atomic_write(path: Path, content: str, expect: str | None = None,
                 vault: Path | None = None) -> str:
    """Write content, refusing if the file moved since `expect` was taken.

    Returns the new fingerprint. Writes via a temp file in the same directory
    and os.replace(), so an interrupted write cannot leave a truncated note.
    """
    if expect is not None:
        if not path.exists():
            raise ConflictError(f"{path.name} no longer exists")
        current = fingerprint(path)
        if current != expect:
            raise ConflictError(
                f"{path.name} changed on disk since it was loaded "
                "(likely edited in Obsidian). Reload to see the current values."
            )

    if vault is not None and path.exists():
        backup(path, vault)

    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return fingerprint(path)


def set_frontmatter_field(text: str, key: str, value) -> str:
    """Rewrite exactly one frontmatter line, leaving the rest byte-identical.

    Inserts the key before the closing fence if it is absent. Returns the text
    unchanged when the value already matches, so a no-op save writes nothing.
    """
    if not text.startswith(FRONTMATTER_FENCE):
        raise ValueError("note has no frontmatter block")

    lines = text.split("\n")
    close = next(
        (i for i in range(1, len(lines)) if lines[i].strip() == FRONTMATTER_FENCE),
        None,
    )
    if close is None:
        raise ValueError("unterminated frontmatter block")

    rendered = _render_scalar(value)
    new_line = f"{key}: {rendered}".rstrip()

    for i in range(1, close):
        stripped = lines[i]
        if stripped.startswith((" ", "\t")):
            continue
        name, sep, _ = stripped.partition(":")
        if sep and name.strip() == key:
            if lines[i] == new_line:
                return text
            # A key whose value is a block list spans following indented lines;
            # replacing it with a scalar means dropping those continuation lines.
            end = i + 1
            while end < close and lines[end].startswith((" ", "\t")):
                end += 1
            lines[i:end] = [new_line]
            return "\n".join(lines)

    lines.insert(close, new_line)
    return "\n".join(lines)


def _render_scalar(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    # Quote only when the value would otherwise change meaning in YAML.
    if text[0] in "[{&*!|>%@`\"'" or ": " in text or text.endswith(":"):
        escaped = text.replace('"', '\\"')
        return f'"{escaped}"'
    return text


def append_section_entry(text: str, heading: str, entry: str) -> str:
    """Append a block under `heading`, before the next same-or-higher heading.

    Used for adding a contact, interview, or reference. Existing entries are
    never touched — the new block is inserted at the end of that section.
    """
    lines = text.split("\n")
    level = len(heading) - len(heading.lstrip("#"))
    start = next((i for i, l in enumerate(lines) if l.strip() == heading.strip()), None)
    if start is None:
        raise ValueError(f"heading not found: {heading}")

    end = len(lines)
    for i in range(start + 1, len(lines)):
        stripped = lines[i].lstrip()
        if stripped.startswith("#"):
            if len(stripped) - len(stripped.lstrip("#")) <= level:
                end = i
                break

    while end > start + 1 and not lines[end - 1].strip():
        end -= 1

    block = ["", *entry.rstrip("\n").split("\n")]
    lines[end:end] = block
    return "\n".join(lines)
