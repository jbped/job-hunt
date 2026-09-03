#!/usr/bin/env python3
"""Render a resume or cover letter from its markdown working copy to a validated PDF.

Replaces the manual PostScript reflow the old generation guide described. The
visual identity — colours, fonts, icons, the blue rule — comes from the existing
skill's `assets/templates/PDF/*.ps` prologue unchanged. What this script computes is the part a
human should never have to: measuring each line against the real font metrics,
wrapping it, and stacking the vertical positions.

The important behaviour is what happens when the content does not fit. Rather
than clipping (which produces a PDF that looks fine until someone reads the
bottom), it reports exactly how much is over and refuses. `--pages 2` opts into
a deliberate two-page resume.

Usage:
    python render_pdf.py --app "Applications/Co/Role" --kind resume
    python render_pdf.py --app "Applications/Co/Role" --kind cover-letter --pages 2
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from pathlib import Path
import argparse
import datetime
import re
import shutil
import subprocess
import sys

import metrics
import vaultlib as v

class Density:
    """A set of type sizes and spacings to try when fitting to the page.

    Fitting by shrinking type is preferable to fitting by silently dropping
    content, but only within a range that stays readable and ATS-parsable —
    hence a short explicit ladder rather than a continuous scale.
    """

    def __init__(self, body: float, leading: float, gap_bullet: float,
                 gap_role: float, gap_section: float, after_section: float,
                 role_offset: float = 0.7, section_offset: float = 2.5,
                 education_offset: float = -0.1):
        self.body = body
        self.leading = leading
        self.gap_bullet = gap_bullet
        self.gap_role = gap_role
        self.gap_section = gap_section
        self.after_section = after_section
        self.role = body + role_offset
        self.section = body + section_offset
        self.education = body + education_offset


RESUME_DENSITIES = (
    Density(8.0, 10.0, 2.0, 7.0, 20.0, 18.0),
    Density(7.8, 9.6, 1.6, 6.0, 17.0, 16.0),
    Density(7.6, 9.2, 1.2, 5.0, 15.0, 14.0),
    Density(7.4, 8.9, 1.0, 4.0, 13.0, 13.0),
)

LETTER_DENSITIES = (
    Density(9.2, 13.0, 0.0, 0.0, 13.0, 13.0),
    Density(9.0, 12.4, 0.0, 0.0, 12.0, 12.0),
    Density(8.6, 11.6, 0.0, 0.0, 11.0, 11.0),
)

# The sections the resume engine knows how to draw, in the order a template
# gets to reorder. Anything outside this set is a template bug, not a feature.
SECTIONS = ("summary", "experience", "additional", "education", "skills")
SECTION_LABELS = {
    "experience": "Experience",
    "additional": "Additional Experience",
    "education": "Education",
    "skills": "Technical Skills",
}


@dataclass(frozen=True)
class Params:
    """Every layout number the engine used to hardcode.

    The defaults are the values this repo has always rendered with, so a
    template that declares nothing renders byte-identically to before. A
    template declares overrides in its prologue as `% ce-param: <key> <value>`
    lines; the engine's logic stays here in Python, and only these numbers move.
    """

    # Text column and page box.
    left: float = 38.0
    right: float = 570.0
    bullet_x: float = 50.0
    top_rule_y: float = 703.0
    bottom_margin: float = 54.0
    page_top: float = 756.0

    # Fonts, which must be ones the metrics tables can measure.
    body_font: str = "Helvetica"
    bold_font: str = "Helvetica-Bold"

    # The letterhead wordmark and contact column.
    name_size: float = 18.5
    name_second_y: float = 735.0
    title_size: float = 8.6
    title_y: float = 718.0
    contact_size: float = 7.8
    contact_right: float = 548.0
    contact_icon_x: float = 556.0
    contact_icon_drop: float = 4.0
    contact_step: float = 14.0
    rule_width: float = 0.9

    # Drawing details the emitted procedures use.
    bullet_dot_x: float = 43.0
    bullet_dot_rise: float = 2.0
    bullet_dot_radius: float = 1.15
    section_rule_gap: float = 8.0
    section_rule_rise: float = 3.0
    section_rule_width: float = 0.35

    # Where the body starts below the rule, per kind.
    resume_start_drop: float = 15.0
    letter_start_drop: float = 22.0

    # Cover-letter spacing, as multiples of the leading.
    re_size_offset: float = 0.8
    re_gap: float = 1.6
    salutation_gap: float = 0.4
    paragraph_gap: float = 0.6
    closing_gap: float = 0.4

    # Type-size offsets from the body size, applied to every density.
    role_size_offset: float = 0.7
    section_size_offset: float = 2.5
    education_size_offset: float = -0.1

    section_order: tuple[str, ...] = SECTIONS

    def densities(self, kind: str) -> tuple[Density, ...]:
        """The density ladder, rebuilt at this template's size offsets."""
        ladder = RESUME_DENSITIES if kind == "resume" else LETTER_DENSITIES
        return tuple(
            Density(d.body, d.leading, d.gap_bullet, d.gap_role, d.gap_section,
                    d.after_section, self.role_size_offset,
                    self.section_size_offset, self.education_size_offset)
            for d in ladder
        )


PARAM_KEYS = tuple(f.name for f in fields(Params))


def parse_params(prologue_text: str) -> Params:
    """Read a template's `% ce-param:` block. Refuse anything we cannot honour.

    Silently ignoring an unknown key would let a template declare a layout it
    does not get, and the user would only find out by comparing PDFs.
    """
    values: dict[str, object] = {}
    for line in prologue_text.split("\n"):
        match = re.match(r"^%\s*ce-param:\s*(\S+)\s+(.+?)\s*$", line.strip())
        if not match:
            continue
        key, raw = match.group(1), match.group(2)
        if key not in PARAM_KEYS:
            raise SystemExit(
                f"Unknown template parameter '{key}'.\nValid keys: "
                + ", ".join(PARAM_KEYS)
            )
        values[key] = _coerce(key, raw)
    return replace(Params(), **values)


def _coerce(key: str, raw: str):
    if key == "section_order":
        wanted = tuple(part for part in re.split(r"[,\s]+", raw) if part)
        unknown = [s for s in wanted if s not in SECTIONS]
        if unknown or not wanted:
            raise SystemExit(
                f"Bad value for template parameter 'section_order': {raw!r}.\n"
                "Valid sections: " + ", ".join(SECTIONS)
            )
        return wanted
    if key in ("body_font", "bold_font"):
        if raw not in metrics.WIDTHS:
            raise SystemExit(
                f"Bad value for template parameter '{key}': {raw!r}.\n"
                "Only fonts with metrics tables can be laid out: "
                + ", ".join(sorted(metrics.WIDTHS))
            )
        return raw
    try:
        return float(raw)
    except ValueError:
        raise SystemExit(
            f"Bad value for template parameter '{key}': {raw!r} is not a number."
        )


# --------------------------------------------------------------------------
# Markdown parsing
# --------------------------------------------------------------------------

def _clean(text: str) -> str:
    """Strip the markdown emphasis and links that must not reach the PDF."""
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()


def parse_sections(text: str) -> dict[str, list[str]]:
    """Split a working copy into `## Heading` -> raw lines."""
    _, body = v.split_frontmatter(text)
    sections: dict[str, list[str]] = {}
    current = None
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            current = stripped[3:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return sections


def parse_resume(text: str) -> dict:
    """Turn a resume working copy into the structure the layout engine consumes."""
    sections = parse_sections(text)

    def joined(name: str) -> str:
        return " ".join(_clean(l) for l in sections.get(name, []) if l.strip())

    header_lines = [_clean(l) for l in sections.get("Header", []) if l.strip()]
    if len(header_lines) < 3:
        raise SystemExit(
            "The '## Header' section needs three lines: name, professional title, "
            "and a contact line separated by '·'."
        )
    name, title, contact = header_lines[0], header_lines[1], header_lines[2]

    experience = []
    for line in sections.get("Experience", []):
        stripped = line.strip()
        if stripped.startswith("### "):
            parts = [p.strip() for p in _clean(stripped[4:]).split("|")]
            experience.append({
                "title": " | ".join(parts[:-1]) if len(parts) > 1 else parts[0],
                "dates": parts[-1] if len(parts) > 1 else "",
                "bullets": [],
            })
        elif stripped.startswith("- ") and experience:
            experience[-1]["bullets"].append(_clean(stripped[2:]))

    additional = []
    for line in sections.get("Additional Experience", []):
        stripped = line.strip()
        if not stripped:
            continue
        head, sep, rest = stripped.partition("—")
        if not sep:
            head, sep, rest = stripped.partition(" - ")
        parts = [p.strip() for p in _clean(head).split("|")]
        additional.append({
            "title": " | ".join(parts[:-1]) if len(parts) > 1 else parts[0],
            "dates": parts[-1] if len(parts) > 1 else "",
            "bullets": [_clean(rest)] if rest.strip() else [],
        })

    education = []
    for line in sections.get("Education", []):
        stripped = line.strip()
        if stripped.startswith("- "):
            parts = [p.strip() for p in _clean(stripped[2:]).split("|")]
            education.append({
                "title": " | ".join(parts[:-1]) if len(parts) > 1 else parts[0],
                "dates": parts[-1] if len(parts) > 1 else "",
            })

    return {
        "name": name,
        "title": title,
        "contact": [c.strip() for c in contact.split("·") if c.strip()],
        "summary": joined("Summary"),
        "experience": experience,
        "additional": additional,
        "education": education,
        "skills": joined("Technical Skills"),
    }


SIGNOFF = ("sincerely", "regards", "best", "thank you", "respectfully", "cordially")


def letterhead(vault: Path) -> dict:
    """Build the name/title/contact block from Personal Information/Contact.md.

    A cover letter should read as a letter, not as a form with a duplicated
    contact block. Pulling the letterhead from the profile also means updating a
    phone number in one place updates every future artifact.
    """
    profile = vault / "Personal Information" / "Contact.md"
    if not profile.exists():
        raise SystemExit(
            "Personal Information/Contact.md is missing, and it supplies the letterhead.\n"
            "Add a '## Header' section to the working copy instead, or restore the contact note."
        )
    fm, text = v.read_note(profile)

    title = ""
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.lower().startswith("- current resume title:"):
            title = _clean(stripped.split(":", 1)[1]).rstrip(".")
            break

    # Each contacts entry is {value, audience}. Application artifacts may carry
    # only `application` and `public` details — `recruiter` is for conversation,
    # not for a cover letter, and `self` never leaves the vault.
    entries = fm.get("contacts") or {}
    contact = []
    # The letterhead design has exactly four contact slots.
    for key in ("location", "phone", "email", "linkedin"):
        entry = entries.get(key)
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if value and entry.get("audience") in ("application", "public"):
            contact.append(str(value).replace("https://www.", "")
                           .replace("https://", "").rstrip("/"))

    name = fm.get("preferred_name") or fm.get("full_name") or "Unknown"
    if fm.get("full_name") and fm.get("preferred_name"):
        surname = str(fm["full_name"]).split()[-1]
        name = f"{fm['preferred_name']} {surname}"

    return {"name": name, "title": title, "contact": contact}


def parse_letter(text: str, vault: Path) -> dict:
    """Parse a cover letter written as prose, not as a filled-in form.

    Everything before the first `## ` heading is the letter itself; trailing
    sections such as 'Evidence used' are working notes and never rendered.
    """
    _, body = v.split_frontmatter(text)
    lines = []
    for line in body.split("\n"):
        if line.strip().startswith("## "):
            break
        if line.strip().startswith("# "):
            continue
        lines.append(line)

    blocks: list[list[str]] = []
    buffer: list[str] = []
    for line in lines:
        if line.strip():
            buffer.append(_clean(line))
        elif buffer:
            blocks.append(buffer)
            buffer = []
    if buffer:
        blocks.append(buffer)

    if not blocks:
        raise SystemExit("The cover letter has no content above its first '## ' heading.")

    date, recipient, salutation = "", [], ""
    paragraphs, closing = [], []

    index = 0
    # A short leading block containing a year is the date line.
    if len(blocks[0]) == 1 and re.search(r"\b(19|20)\d{2}\b", blocks[0][0]):
        date = blocks[0][0]
        index = 1
    # The next multi-line block, before any salutation, addresses the recipient.
    if index < len(blocks) and not blocks[index][0].lower().startswith("dear") \
            and len(blocks[index]) > 1:
        recipient = blocks[index]
        index += 1
    if index < len(blocks) and blocks[index][0].lower().startswith("dear"):
        salutation = blocks[index][0]
        index += 1

    for block in blocks[index:]:
        first = block[0].lower().rstrip(",").strip()
        if any(first.startswith(word) for word in SIGNOFF):
            closing = block
            continue
        if closing:
            closing.extend(block)
            continue
        paragraphs.append(" ".join(block))

    head = letterhead(vault)
    sections = parse_sections(text)
    if sections.get("Header"):
        header_lines = [_clean(l) for l in sections["Header"] if l.strip()]
        if len(header_lines) >= 3:
            head = {
                "name": header_lines[0],
                "title": header_lines[1],
                "contact": [c.strip() for c in header_lines[2].split("·") if c.strip()],
            }

    return {
        **head,
        "date": date,
        "recipient": recipient,
        "salutation": salutation,
        "paragraphs": paragraphs,
        "closing": closing,
    }


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

class Overflow(Exception):
    """Raised only after a full layout pass, so `lines` is the true excess.

    Stopping at the first element that did not fit would report how far that one
    element overran, not how much content is actually over — which is useless
    advice when the answer is 'cut about this much'.
    """

    def __init__(self, short_by: float, leading: float):
        self.short_by = short_by
        self.lines = max(1, round(short_by / leading))
        super().__init__(f"content exceeds the page by {short_by:.0f}pt")


class Page:
    """Accumulates PostScript operations and tracks the current baseline."""

    def __init__(self, density: Density, start_y: float, pages: int,
                 params: Params | None = None):
        self.d = density
        self.p = params or Params()
        self.y = start_y
        self.ops: list[str] = []
        self.page_breaks: list[int] = []
        self.pages_allowed = pages
        self.page = 1
        self.overflowed = False
        # Lines that exceed the text column. Wrapping cannot fix these — they are
        # single tokens (a URL, a long hyphenless compound) wider than the column,
        # and they would silently run off the right edge.
        self.overwide: list[str] = []

    def _check_width(self, content: str, x: float, size: float,
                     font: str | None = None) -> None:
        font = font or self.p.body_font
        if metrics.width(content, font, size) > (self.p.right - x) + 0.5:
            self.overwide.append(content)

    def _ensure(self, needed: float) -> None:
        if self.y - needed >= self.p.bottom_margin:
            return
        if self.page >= self.pages_allowed:
            # Keep laying out past the bottom so the finished pass can report the
            # total excess. Nothing is emitted to a PDF in this state.
            self.overflowed = True
            return
        self.page_breaks.append(len(self.ops))
        self.page += 1
        self.y = self.p.page_top

    def shortfall(self) -> float:
        """Points by which the content overran the page budget; 0 if it fits."""
        return max(0.0, self.p.bottom_margin - self.y) if self.overflowed else 0.0

    def text(self, content: str, x: float, size: float, font: str | None = None) -> None:
        self._ensure(size)
        self._check_width(content, x, size, font)
        self.ops.append(f"{self.y:.1f} {x:.0f} ({metrics.escape(content)}) bodyline")
        self.y -= self.d.leading

    def paragraph(self, content: str, x: float, max_x: float | None = None) -> None:
        max_x = self.p.right if max_x is None else max_x
        for line in metrics.wrap(content, self.p.body_font, self.d.body, max_x - x):
            self.text(line, x, self.d.body)

    def bullet(self, content: str) -> None:
        lines = metrics.wrap(content, self.p.body_font, self.d.body,
                             self.p.right - self.p.bullet_x)
        for i, line in enumerate(lines):
            self._ensure(self.d.body)
            self._check_width(line, self.p.bullet_x, self.d.body)
            op = "bullet" if i == 0 else "bodyline"
            prefix = (f"{self.y:.1f}" if i == 0
                      else f"{self.y:.1f} {self.p.bullet_x:.0f}")
            self.ops.append(f"{prefix} ({metrics.escape(line)}) {op}")
            self.y -= self.d.leading
        self.y -= self.d.gap_bullet

    def section(self, label: str) -> None:
        self.y -= self.d.gap_section
        self._ensure(self.d.section)
        self.ops.append(f"({metrics.escape(label.upper())}) {self.y:.1f} section")
        self.y -= self.d.after_section

    def role(self, title: str, dates: str, education: bool = False) -> None:
        self._ensure(self.d.role)
        # Title is left-aligned and dates right-aligned on the same baseline, so
        # the failure here is a collision in the middle rather than an overrun.
        size = self.d.education if education else self.d.role
        title_w = metrics.width(title, self.p.bold_font, size)
        dates_w = metrics.width(dates, self.p.body_font,
                                self.d.education if education else self.d.body)
        if title_w + dates_w + 12 > self.p.right - self.p.left:
            self.overwide.append(f"{title} / {dates} (title and dates collide)")
        op = "education" if education else "role"
        self.ops.append(
            f"{self.y:.1f} ({metrics.escape(title)}) ({metrics.escape(dates)}) {op}"
        )
        self.y -= self.d.leading + 1


def layout_resume(data: dict, density: Density, pages: int,
                  params: Params | None = None) -> Page:
    p = params or Params()
    page = Page(density, p.top_rule_y - p.resume_start_drop, pages, p)

    for name in p.section_order:
        if not data[name]:
            continue
        if name == "summary":
            page.paragraph(data["summary"], p.left)
        elif name in ("experience", "additional"):
            page.section(SECTION_LABELS[name])
            for i, role in enumerate(data[name]):
                if i:
                    page.y -= density.gap_role
                page.role(role["title"], role["dates"])
                for bullet in role["bullets"]:
                    page.bullet(bullet)
        elif name == "education":
            page.section(SECTION_LABELS[name])
            for entry in data["education"]:
                page.role(entry["title"], entry["dates"], education=True)
        elif name == "skills":
            page.section(SECTION_LABELS[name])
            page.paragraph(data["skills"], p.left)

    return page


def fit(data: dict, kind: str, pages: int = 1, position: str = "",
        params: Params | None = None, source_name: str | None = None) -> Page:
    """Lay the content out at the loosest density that still fits the budget."""
    p = params or Params()
    tightest = None
    for density in p.densities(kind):
        attempt = (layout_resume(data, density, pages, p) if kind == "resume"
                   else layout_letter(data, density, pages, p, position))
        tightest = attempt
        if not attempt.overflowed:
            return attempt

    excess = tightest.shortfall()
    lines = max(1, round(excess / tightest.d.leading))
    source_name = source_name or (
        "Draft - Resume.md" if kind == "resume" else "Draft - Cover Letter.md")
    raise SystemExit(
        f"Content does not fit on {pages} page(s), even at the tightest spacing —\n"
        f"about {lines} line(s) ({excess:.0f}pt) too long.\n"
        f"Cut roughly that much from {source_name}, or pass --pages {pages + 1} "
        "to render a deliberate multi-page document."
    )


def layout_letter(data: dict, density: Density, pages: int,
                  params: Params | None = None, position: str = "") -> Page:
    p = params or Params()
    page = Page(density, p.top_rule_y - p.letter_start_drop, pages, p)

    if data["date"]:
        page.text(data["date"], p.left, density.body)
        page.y -= density.leading

    for line in data["recipient"]:
        page.text(line, p.left, density.body)
    if data["recipient"]:
        page.y -= density.leading

    if position:
        page._ensure(density.section)
        page.ops.append(
            f"HB {density.body + p.re_size_offset:.1f} scalefont setfont brand "
            f"{p.left:.0f} {page.y:.1f} "
            f"moveto (RE: {metrics.escape(position.upper())}) show"
        )
        page.y -= density.leading * p.re_gap

    if data["salutation"]:
        page.text(data["salutation"], p.left, density.body)
        page.y -= density.leading * p.salutation_gap

    for paragraph in data["paragraphs"]:
        page.paragraph(paragraph, p.left)
        page.y -= density.leading * p.paragraph_gap

    if data["closing"]:
        page.y -= density.leading * p.closing_gap
        for line in data["closing"]:
            page.text(line, p.left, density.body)

    return page


# --------------------------------------------------------------------------
# PostScript emission
# --------------------------------------------------------------------------

def overrides(d: Density, params: Params | None = None) -> str:
    """Redefine the drawing procedures at the chosen density's sizes.

    The shipped templates hardcode 8pt inside `bodyline`, `role`, and friends.
    That is why the old workflow required manual reflow: the size the layout
    assumed and the size actually drawn were independent. Emitting them here,
    from the same Density used for measurement, keeps wrapping and rendering in
    agreement. Colours, icons, and the rule geometry stay as the template
    defines them, so the design is unchanged.
    """
    p = params or Params()
    return f"""
/BODY {d.body:.2f} def
/bodyline {{
  /txt exch def /x exch def /y exch def
  HR BODY scalefont setfont ink x y moveto txt show
}} def
/bullet {{
  /txt exch def /y exch def
  brand newpath {p.bullet_dot_x:g} y {p.bullet_dot_rise:g} add {p.bullet_dot_radius:g} 0 360 arc fill
  y {p.bullet_x:.0f} txt bodyline
}} def
/role {{
  /date exch def /title exch def /y exch def
  HB {d.role:.2f} scalefont setfont ink {p.left:.0f} y moveto title show
  HR BODY scalefont setfont muted {p.right:.0f} y moveto date Rshow
}} def
/education {{
  /date exch def /title exch def /y exch def
  HB {d.education:.2f} scalefont setfont ink {p.left:.0f} y moveto title show
  HR {d.education:.2f} scalefont setfont muted {p.right:.0f} y moveto date Rshow
}} def
/section {{
  /y exch def /label exch def
  HB {d.section:.2f} scalefont setfont brand {p.left:.0f} y moveto label show
  label stringwidth pop {p.left:.0f} add {p.section_rule_gap:g} add y {p.section_rule_rise:g} add moveto
  {p.right:.0f} y {p.section_rule_rise:g} add lineto {p.section_rule_width:g} setlinewidth stroke
}} def
/contact {{
  /txt exch def /y exch def
  HR {p.contact_size:g} scalefont setfont muted {p.contact_right:g} y moveto txt Rshow
}} def
"""


def prologue(template: Path) -> str:
    """Everything up to the first drawing command: fonts, colours, procedures, icons."""
    text = template.read_text(encoding="utf-8")
    marker = "\nbrand\nHB"
    index = text.find(marker)
    if index == -1:
        raise SystemExit(
            f"{template.name} does not have the expected procedure prologue.\n"
            "It should end its definitions with a line 'brand' followed by 'HB ... scalefont'."
        )
    return text[:index]


# --------------------------------------------------------------------------
# The template registry
# --------------------------------------------------------------------------

# What a template of each kind must carry, beyond the prologue marker. These
# are the tokens `build_postscript` substitutes; a template missing one would
# ship a PDF whose metadata names the wrong person or role.
REQUIRED_TOKENS = ("{{FULL_NAME}}", "{{POSITION}}", "{{COMPANY}}")

KINDS = ("resume", "cover-letter")

DEFAULT_TEMPLATES = {
    "resume": "Resume - Figma Inspired",
    "cover-letter": "Cover Letter - Figma Inspired",
}

VAULT_TEMPLATES = ("Resources", "Templates")


def _declared_kind(text: str) -> str | None:
    match = re.search(r"^%\s*ce-kind:\s*(\S+)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def registry(vault: Path) -> dict[str, list[dict]]:
    """Every template the user may pick, per kind.

    Two roots and no others: the built-ins this repo ships, and `.ps` files the
    user drops in their vault. Names are namespaced so the two can never
    collide and a vault template can never shadow a built-in.
    """
    found: dict[str, list[dict]] = {kind: [] for kind in KINDS}

    built_in = v.TEMPLATES_DIR / "PDF"
    for kind, stem in DEFAULT_TEMPLATES.items():
        found[kind].append({"name": f"built-in:{stem}",
                            "path": built_in / f"{stem}.ps"})
    for path in sorted(built_in.glob("*.ps")):
        if path.stem in DEFAULT_TEMPLATES.values():
            continue
        kind = _declared_kind(path.read_text(encoding="utf-8", errors="replace"))
        if kind in KINDS:
            found[kind].append({"name": f"built-in:{path.stem}", "path": path})

    root = vault / VAULT_TEMPLATES[0] / VAULT_TEMPLATES[1]
    if root.is_dir():
        for path in sorted(root.glob("*.ps")):
            try:
                # A symlink out of the vault is not a template the user put
                # there; refuse it rather than reading whatever it points at.
                resolved = v.resolve_within(vault, str(path.relative_to(vault)))
            except ValueError:
                print(f"note: ignoring {path.name}, which points outside the vault",
                      file=sys.stderr)
                continue
            kind = _declared_kind(resolved.read_text(encoding="utf-8", errors="replace"))
            if kind not in KINDS:
                print(f"note: ignoring {path.name}, which declares no "
                      "'% ce-kind: resume' or '% ce-kind: cover-letter' line",
                      file=sys.stderr)
                continue
            found[kind].append({"name": f"vault:{path.stem}", "path": resolved})

    return found


def resolve_template(vault: Path, kind: str, name: str | None) -> Path:
    """Turn a registry name into a path. No name means today's default."""
    entries = registry(vault)[kind]
    if not name:
        return v.TEMPLATES_DIR / "PDF" / f"{DEFAULT_TEMPLATES[kind]}.ps"
    for entry in entries:
        if entry["name"] == name:
            return entry["path"]
    raise SystemExit(
        f"No {kind} template named '{name}'.\nAvailable: "
        + ", ".join(entry["name"] for entry in entries)
    )


TEMPLATE_FIELD = {"resume": "resume_template",
                  "cover-letter": "cover_letter_template"}


def template_for(vault: Path, folder: Path, kind: str,
                 override: str | None = None) -> tuple[Path, Params]:
    """The template this application renders with, and the layout it declares.

    An explicit `--template` wins over the brief, and an unset brief field
    means the default this repo has always used.
    """
    brief = folder / "Application Brief.md"
    fm, _ = v.read_note(brief) if brief.exists() else ({}, "")
    chosen = override or (fm.get(TEMPLATE_FIELD[kind]) or None)
    path = resolve_template(vault, kind, chosen)
    return path, check_template(path, kind)


def check_template(path: Path, kind: str) -> Params:
    """Prove a template can be rendered before anything is rendered with it.

    A template is never transformed to make it fit — it is refused, with the
    thing that is missing named, so the person who wrote it can fix it.
    """
    if not path.is_file():
        raise SystemExit(f"Missing template: {path}")

    # Only the prologue is ever used, so that is where the tokens have to be:
    # a token past the marker would be discarded unread and the PDF would
    # quietly carry the wrong metadata.
    head = prologue(path)
    missing = [token for token in REQUIRED_TOKENS if token not in head]
    if missing:
        raise SystemExit(
            f"{path.name} is missing the required token(s) {', '.join(missing)}.\n"
            "A template must carry all of " + ", ".join(REQUIRED_TOKENS)
            + " in the PDF metadata block of its prologue."
        )
    return parse_params(head)


def contact_icon(value: str) -> str:
    """Match the icon to what the value actually is.

    The contact line is written in whatever order reads best, so pairing icons
    by position would eventually put a phone glyph beside a city name.
    """
    lowered = value.lower()
    if "@" in value and " " not in value.strip():
        return "mailIcon"
    if "linkedin" in lowered or "github" in lowered or lowered.startswith(("http", "www.")):
        return "linkedinIcon"
    if sum(char.isdigit() for char in value) >= 7:
        return "phoneIcon"
    return "pinIcon"


def header_ops(data: dict, params: Params | None = None) -> list[str]:
    """The name block, contact column, icons, and rule — fixed by the design."""
    p = params or Params()
    words = data["name"].split()
    if len(words) >= 2:
        line1, line2 = words[0], " ".join(words[1:])
    else:
        line1, line2 = data["name"], ""

    # Uppercase to match the section labels; the name block is set as a wordmark
    # in this design, not as running text.
    ops = [
        "brand",
        f"HB {p.name_size:g} scalefont setfont {p.left:.0f} {p.page_top:g} moveto "
        f"({metrics.escape(line1.upper())}) show",
    ]
    if line2:
        ops.append(f"{p.left:.0f} {p.name_second_y:g} moveto "
                   f"({metrics.escape(line2.upper())}) show")
    ops.append(
        f"HR {p.title_size:g} scalefont setfont muted {p.left:.0f} {p.title_y:g} moveto "
        f"({metrics.escape(data['title'])}) show"
    )

    for i, item in enumerate(data["contact"][:4]):
        ops.append(f"{p.page_top - i * p.contact_step:g} ({metrics.escape(item)}) contact")
        ops.append(f"{p.contact_icon_x:g} "
                   f"{p.page_top - p.contact_icon_drop - i * p.contact_step:g} "
                   f"{contact_icon(item)}")

    ops.append(
        f"brand {p.left:.0f} {p.top_rule_y:.0f} moveto "
        f"{p.right:.0f} {p.top_rule_y:.0f} lineto "
        f"{p.rule_width:g} setlinewidth stroke"
    )
    return ops


def build_postscript(template: Path, data: dict, page: Page, doc_title: str,
                     author: str, subject: str,
                     params: Params | None = None) -> str:
    p = params or page.p
    head = prologue(template)
    head = (head
            .replace("{{FULL_NAME}}", metrics.escape(author))
            .replace("{{POSITION}}", metrics.escape(doc_title))
            .replace("{{COMPANY}}", metrics.escape(subject)))

    body = header_ops(data, p)
    ops = list(page.ops)
    for index in reversed(page.page_breaks):
        ops.insert(index, "showpage\n" + "\n".join(header_ops(data, p)))

    head = head.replace("%%Pages: 1", f"%%Pages: {page.page}")
    return (head + overrides(page.d, p) + "\n"
            + "\n".join(body + ops) + "\nshowpage\n%%EOF\n")


# --------------------------------------------------------------------------
# Render and validate
# --------------------------------------------------------------------------

def next_version(artifacts: Path, stem: str) -> int:
    """Never reuse a version number — submitted artifacts must stay addressable."""
    highest = 0
    for existing in artifacts.glob(f"{stem} v*"):
        match = re.match(rf"{re.escape(stem)} v(\d+)", existing.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def validate(pdf: Path, expected_pages: int, sample: str) -> tuple[list[str], list[str]]:
    """Prove the artifact is what it claims before anyone attaches it to an email."""
    problems, notes = [], []

    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
    pages = 0
    for line in info.stdout.split("\n"):
        if line.startswith("Pages:"):
            pages = int(line.split(":")[1].strip())
        if line.startswith("Page size:"):
            notes.append(line.strip())
    notes.append(f"Pages: {pages}")
    if pages != expected_pages:
        problems.append(f"expected {expected_pages} page(s), produced {pages}")

    fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True)
    font_lines = [l for l in fonts.stdout.split("\n")[2:] if l.strip()]
    embedded = [l for l in font_lines if " yes " in l or l.split()[2:3] == ["yes"]]
    notes.append(f"Fonts: {len(font_lines)} used, {len(embedded)} embedded")
    if font_lines and not embedded:
        problems.append("no fonts are embedded; the PDF may render differently elsewhere")

    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                          capture_output=True, text=True).stdout
    if not text.strip():
        problems.append("no extractable text; the PDF is not ATS-readable")
    else:
        notes.append(f"Extractable text: {len(text.split())} words")
        probe = " ".join(sample.split()[:6])
        if probe and probe.lower() not in " ".join(text.split()).lower():
            problems.append(f"expected text not found in extraction: '{probe}'")

    if "{{" in text:
        problems.append("unreplaced {{PLACEHOLDER}} found in the rendered text")

    return problems, notes


def ghostscript() -> str | None:
    """The Ghostscript executable, wherever this OS puts it.

    ps2pdf is a wrapper script that Windows installs do not ship; invoking gs
    directly with the equivalent flags works identically on every platform.
    """
    for name in ("gs", "gswin64c", "gswin32c"):
        if shutil.which(name):
            return name
    return None


def render(vault: Path, folder: Path, kind: str, pages: int = 1,
           preview: bool = True, template_name: str | None = None) -> dict:
    source_name = "Draft - Resume.md" if kind == "resume" else "Draft - Cover Letter.md"
    stem = "Resume" if kind == "resume" else "Cover Letter"

    source = folder / source_name
    if not source.exists():
        raise SystemExit(f"No {source_name} in {folder.relative_to(vault)}")
    template, params = template_for(vault, folder, kind, template_name)

    gs = ghostscript()
    missing = [t for t in ("pdfinfo", "pdftotext", "pdffonts") if shutil.which(t) is None]
    if gs is None or missing:
        need = (["Ghostscript"] if gs is None else []) + \
               (["Poppler utilities"] if missing else [])
        raise SystemExit(
            f"{' and '.join(need)} not found. Install:\n"
            "  Arch:    sudo pacman -S ghostscript poppler\n"
            "  Debian:  sudo apt install ghostscript poppler-utils\n"
            "  macOS:   brew install ghostscript poppler\n"
            "  Windows: winget install ArtifexSoftware.Ghostscript, and put the\n"
            "           Poppler binaries (e.g. the poppler-windows release) on PATH"
        )

    brief = folder / "Application Brief.md"
    fm, _ = v.read_note(brief) if brief.exists() else ({}, "")
    company = fm.get("company") or folder.parent.name
    position = fm.get("position") or folder.name

    text = source.read_text(encoding="utf-8")
    data = parse_resume(text) if kind == "resume" else parse_letter(text, vault)
    page = fit(data, kind, pages, position, params, source_name=source_name)

    ps_text = build_postscript(template, data, page, position, data["name"],
                               company, params)

    artifacts = folder / "Artifacts"
    artifacts.mkdir(exist_ok=True)
    version = next_version(artifacts, stem)
    today = datetime.date.today().isoformat()
    base = f"{stem} v{version} {today}"

    ps_path = artifacts / f"{base}.ps"
    pdf_path = artifacts / f"{base}.pdf"
    ps_path.write_text(ps_text, encoding="utf-8")

    result = subprocess.run(
        [gs, "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite",
         "-dPDFSETTINGS=/prepress", f"-sOutputFile={pdf_path}", str(ps_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not pdf_path.exists():
        ps_path.unlink(missing_ok=True)
        raise SystemExit(f"Ghostscript failed:\n{result.stderr.strip()}")

    probe = data["summary"] if kind == "resume" else (data["paragraphs"] or [""])[0]
    problems, notes = validate(pdf_path, page.page, probe)
    for line in page.overwide:
        problems.append(f"line exceeds the text column: {line[:80]}")

    # Proof images are a rendering by-product, not an artifact — keep only the
    # newest for this document so the folder does not fill with near-identical PNGs.
    for stale in artifacts.glob(f".preview-{stem} v*.png"):
        stale.unlink(missing_ok=True)

    preview_path = None
    if preview and shutil.which("pdftoppm"):
        preview_path = artifacts / f".preview-{base}"
        subprocess.run(
            ["pdftoppm", "-png", "-r", "110", "-singlefile", str(pdf_path), str(preview_path)],
            capture_output=True,
        )
        preview_path = preview_path.with_suffix(".png")

    return {
        "pdf": pdf_path,
        "ps": ps_path,
        "preview": preview_path if preview_path and preview_path.exists() else None,
        "version": version,
        "pages": page.page,
        "problems": problems,
        "notes": notes,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app", required=True, help="application folder, relative to the vault")
    ap.add_argument("--kind", choices=["resume", "cover-letter"], default="resume")
    ap.add_argument("--pages", type=int, default=1, help="page budget; 1 unless deliberate")
    ap.add_argument("--template",
                    help="registry name, e.g. 'vault:My Design'; "
                         "overrides the brief's field for this render")
    ap.add_argument("--no-preview", action="store_true")
    ap.add_argument("--vault")
    args = ap.parse_args()

    vault = v.require_vault(args.vault)
    folder = Path(args.app).expanduser()
    if not folder.is_absolute():
        folder = vault / args.app
    folder = folder.resolve()
    try:
        folder.relative_to(vault.resolve())
    except ValueError:
        raise SystemExit(f"Not inside the vault: {folder}")
    if not folder.is_dir():
        raise SystemExit(f"Not a folder: {folder}")

    out = render(vault, folder, args.kind, args.pages,
                 preview=not args.no_preview, template_name=args.template)

    def show(path: Path) -> str:
        try:
            return str(path.relative_to(vault))
        except ValueError:
            return str(path)

    print(f"Rendered {show(out['pdf'])}")
    for note in out["notes"]:
        print(f"  {note}")
    if out["preview"]:
        print(f"  Proof image: {show(out['preview'])}")

    if out["problems"]:
        print("\nValidation problems:")
        for problem in out["problems"]:
            print(f"  - {problem}")
        print("\nThe PDF was written but should not be submitted until these are resolved.")
        return 1

    print("\nValidation passed. Inspect the proof image before submitting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
