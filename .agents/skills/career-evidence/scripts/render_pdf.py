#!/usr/bin/env python3
"""Render a resume or cover letter from its markdown working copy to a validated PDF.

Replaces the manual PostScript reflow the old generation guide described. The
visual identity — colours, fonts, icons, the blue rule — comes from the existing
`Templates/PDF/*.ps` prologue unchanged. What this script computes is the part a
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

from pathlib import Path
import argparse
import datetime
import re
import shutil
import subprocess
import sys

import metrics
import vaultlib as v

# Geometry, taken from the existing template so rendered output stays consistent
# with the PDFs already submitted.
LEFT = 38.0
RIGHT = 570.0
BULLET_X = 50.0
TOP_RULE_Y = 703.0
BOTTOM_MARGIN = 54.0

BODY_FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"


class Density:
    """A set of type sizes and spacings to try when fitting to the page.

    Fitting by shrinking type is preferable to fitting by silently dropping
    content, but only within a range that stays readable and ATS-parsable —
    hence a short explicit ladder rather than a continuous scale.
    """

    def __init__(self, body: float, leading: float, gap_bullet: float,
                 gap_role: float, gap_section: float, after_section: float):
        self.body = body
        self.leading = leading
        self.gap_bullet = gap_bullet
        self.gap_role = gap_role
        self.gap_section = gap_section
        self.after_section = after_section
        self.role = body + 0.7
        self.section = body + 2.5
        self.education = body - 0.1


RESUME_DENSITIES = [
    Density(8.0, 10.0, 2.0, 7.0, 20.0, 18.0),
    Density(7.8, 9.6, 1.6, 6.0, 17.0, 16.0),
    Density(7.6, 9.2, 1.2, 5.0, 15.0, 14.0),
    Density(7.4, 8.9, 1.0, 4.0, 13.0, 13.0),
]

LETTER_DENSITIES = [
    Density(9.2, 13.0, 0.0, 0.0, 13.0, 13.0),
    Density(9.0, 12.4, 0.0, 0.0, 12.0, 12.0),
    Density(8.6, 11.6, 0.0, 0.0, 11.0, 11.0),
]


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

    def __init__(self, density: Density, start_y: float, pages: int):
        self.d = density
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

    def _check_width(self, content: str, x: float, size: float, font: str = BODY_FONT) -> None:
        if metrics.width(content, font, size) > (RIGHT - x) + 0.5:
            self.overwide.append(content)

    def _ensure(self, needed: float) -> None:
        if self.y - needed >= BOTTOM_MARGIN:
            return
        if self.page >= self.pages_allowed:
            # Keep laying out past the bottom so the finished pass can report the
            # total excess. Nothing is emitted to a PDF in this state.
            self.overflowed = True
            return
        self.page_breaks.append(len(self.ops))
        self.page += 1
        self.y = 756.0

    def shortfall(self) -> float:
        """Points by which the content overran the page budget; 0 if it fits."""
        return max(0.0, BOTTOM_MARGIN - self.y) if self.overflowed else 0.0

    def text(self, content: str, x: float, size: float, font: str = BODY_FONT) -> None:
        self._ensure(size)
        self._check_width(content, x, size, font)
        self.ops.append(f"{self.y:.1f} {x:.0f} ({metrics.escape(content)}) bodyline")
        self.y -= self.d.leading

    def paragraph(self, content: str, x: float, max_x: float = RIGHT) -> None:
        for line in metrics.wrap(content, BODY_FONT, self.d.body, max_x - x):
            self.text(line, x, self.d.body)

    def bullet(self, content: str) -> None:
        lines = metrics.wrap(content, BODY_FONT, self.d.body, RIGHT - BULLET_X)
        for i, line in enumerate(lines):
            self._ensure(self.d.body)
            self._check_width(line, BULLET_X, self.d.body)
            op = "bullet" if i == 0 else "bodyline"
            prefix = f"{self.y:.1f}" if i == 0 else f"{self.y:.1f} {BULLET_X:.0f}"
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
        title_w = metrics.width(title, BOLD_FONT, size)
        dates_w = metrics.width(dates, BODY_FONT, self.d.education if education else self.d.body)
        if title_w + dates_w + 12 > RIGHT - LEFT:
            self.overwide.append(f"{title} / {dates} (title and dates collide)")
        op = "education" if education else "role"
        self.ops.append(
            f"{self.y:.1f} ({metrics.escape(title)}) ({metrics.escape(dates)}) {op}"
        )
        self.y -= self.d.leading + 1


def layout_resume(data: dict, density: Density, pages: int) -> Page:
    page = Page(density, TOP_RULE_Y - 15, pages)

    if data["summary"]:
        page.paragraph(data["summary"], LEFT)

    if data["experience"]:
        page.section("Experience")
        for i, role in enumerate(data["experience"]):
            if i:
                page.y -= density.gap_role
            page.role(role["title"], role["dates"])
            for bullet in role["bullets"]:
                page.bullet(bullet)

    if data["additional"]:
        page.section("Additional Experience")
        for i, role in enumerate(data["additional"]):
            if i:
                page.y -= density.gap_role
            page.role(role["title"], role["dates"])
            for bullet in role["bullets"]:
                page.bullet(bullet)

    if data["education"]:
        page.section("Education")
        for entry in data["education"]:
            page.role(entry["title"], entry["dates"], education=True)

    if data["skills"]:
        page.section("Technical Skills")
        page.paragraph(data["skills"], LEFT)

    return page


def layout_letter(data: dict, density: Density, pages: int, position: str = "") -> Page:
    page = Page(density, TOP_RULE_Y - 22, pages)

    if data["date"]:
        page.text(data["date"], LEFT, density.body)
        page.y -= density.leading

    for line in data["recipient"]:
        page.text(line, LEFT, density.body)
    if data["recipient"]:
        page.y -= density.leading

    if position:
        page._ensure(density.section)
        page.ops.append(
            f"HB {density.body + 0.8:.1f} scalefont setfont brand {LEFT:.0f} {page.y:.1f} "
            f"moveto (RE: {metrics.escape(position.upper())}) show"
        )
        page.y -= density.leading * 1.6

    if data["salutation"]:
        page.text(data["salutation"], LEFT, density.body)
        page.y -= density.leading * 0.4

    for paragraph in data["paragraphs"]:
        page.paragraph(paragraph, LEFT)
        page.y -= density.leading * 0.6

    if data["closing"]:
        page.y -= density.leading * 0.4
        for line in data["closing"]:
            page.text(line, LEFT, density.body)

    return page


# --------------------------------------------------------------------------
# PostScript emission
# --------------------------------------------------------------------------

def overrides(d: Density) -> str:
    """Redefine the drawing procedures at the chosen density's sizes.

    The shipped templates hardcode 8pt inside `bodyline`, `role`, and friends.
    That is why the old workflow required manual reflow: the size the layout
    assumed and the size actually drawn were independent. Emitting them here,
    from the same Density used for measurement, keeps wrapping and rendering in
    agreement. Colours, icons, and the rule geometry stay as the template
    defines them, so the design is unchanged.
    """
    return f"""
/BODY {d.body:.2f} def
/bodyline {{
  /txt exch def /x exch def /y exch def
  HR BODY scalefont setfont ink x y moveto txt show
}} def
/bullet {{
  /txt exch def /y exch def
  brand newpath 43 y 2 add 1.15 0 360 arc fill
  y {BULLET_X:.0f} txt bodyline
}} def
/role {{
  /date exch def /title exch def /y exch def
  HB {d.role:.2f} scalefont setfont ink {LEFT:.0f} y moveto title show
  HR BODY scalefont setfont muted {RIGHT:.0f} y moveto date Rshow
}} def
/education {{
  /date exch def /title exch def /y exch def
  HB {d.education:.2f} scalefont setfont ink {LEFT:.0f} y moveto title show
  HR {d.education:.2f} scalefont setfont muted {RIGHT:.0f} y moveto date Rshow
}} def
/section {{
  /y exch def /label exch def
  HB {d.section:.2f} scalefont setfont brand {LEFT:.0f} y moveto label show
  label stringwidth pop {LEFT:.0f} add 8 add y 3 add moveto
  {RIGHT:.0f} y 3 add lineto 0.35 setlinewidth stroke
}} def
/contact {{
  /txt exch def /y exch def
  HR 7.8 scalefont setfont muted 548 y moveto txt Rshow
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


def header_ops(data: dict) -> list[str]:
    """The name block, contact column, icons, and rule — fixed by the design."""
    words = data["name"].split()
    if len(words) >= 2:
        line1, line2 = words[0], " ".join(words[1:])
    else:
        line1, line2 = data["name"], ""

    # Uppercase to match the section labels; the name block is set as a wordmark
    # in this design, not as running text.
    ops = [
        "brand",
        f"HB 18.5 scalefont setfont {LEFT:.0f} 756 moveto ({metrics.escape(line1.upper())}) show",
    ]
    if line2:
        ops.append(f"{LEFT:.0f} 735 moveto ({metrics.escape(line2.upper())}) show")
    ops.append(
        f"HR 8.6 scalefont setfont muted {LEFT:.0f} 718 moveto "
        f"({metrics.escape(data['title'])}) show"
    )

    for i, item in enumerate(data["contact"][:4]):
        ops.append(f"{756 - i * 14} ({metrics.escape(item)}) contact")
        ops.append(f"556 {752 - i * 14} {contact_icon(item)}")

    ops.append(
        f"brand {LEFT:.0f} {TOP_RULE_Y:.0f} moveto {RIGHT:.0f} {TOP_RULE_Y:.0f} lineto "
        "0.9 setlinewidth stroke"
    )
    return ops


def build_postscript(template: Path, data: dict, page: Page, doc_title: str,
                     author: str, subject: str) -> str:
    head = prologue(template)
    head = (head
            .replace("{{FULL_NAME}}", metrics.escape(author))
            .replace("{{POSITION}}", metrics.escape(doc_title))
            .replace("{{COMPANY}}", metrics.escape(subject)))

    body = header_ops(data)
    ops = list(page.ops)
    for index in reversed(page.page_breaks):
        ops.insert(index, "showpage\n" + "\n".join(header_ops(data)))

    head = head.replace("%%Pages: 1", f"%%Pages: {page.page}")
    return head + overrides(page.d) + "\n" + "\n".join(body + ops) + "\nshowpage\n%%EOF\n"


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


def render(vault: Path, folder: Path, kind: str, pages: int = 1,
           preview: bool = True) -> dict:
    source_name = "Resume Content.md" if kind == "resume" else "Cover Letter.md"
    template_name = ("PDF/Resume - Figma Inspired.ps" if kind == "resume"
                     else "PDF/Cover Letter - Figma Inspired.ps")
    stem = "Resume" if kind == "resume" else "Cover Letter"

    source = folder / source_name
    if not source.exists():
        raise SystemExit(f"No {source_name} in {folder.relative_to(vault)}")
    template = vault / "Templates" / template_name
    if not template.exists():
        raise SystemExit(f"Missing template: Templates/{template_name}")

    for tool in ("ps2pdf", "pdfinfo", "pdftotext", "pdffonts"):
        if shutil.which(tool) is None:
            raise SystemExit(
                f"'{tool}' is not installed. On Arch/CachyOS: "
                "sudo pacman -S ghostscript poppler"
            )

    brief = folder / "Application Brief.md"
    fm, _ = v.read_note(brief) if brief.exists() else ({}, "")
    company = fm.get("company") or folder.parent.name
    position = fm.get("position") or folder.name

    text = source.read_text(encoding="utf-8")
    data = parse_resume(text) if kind == "resume" else parse_letter(text, vault)
    densities = RESUME_DENSITIES if kind == "resume" else LETTER_DENSITIES

    page, tightest = None, None
    for density in densities:
        attempt = (layout_resume(data, density, pages) if kind == "resume"
                   else layout_letter(data, density, pages, position))
        tightest = attempt
        if not attempt.overflowed:
            page = attempt
            break
    if page is None:
        excess = tightest.shortfall()
        lines = max(1, round(excess / tightest.d.leading))
        raise SystemExit(
            f"Content does not fit on {pages} page(s), even at the tightest spacing —\n"
            f"about {lines} line(s) ({excess:.0f}pt) too long.\n"
            f"Cut roughly that much from {source_name}, or pass --pages {pages + 1} "
            "to render a deliberate multi-page document."
        )

    ps_text = build_postscript(template, data, page, position, data["name"], company)

    artifacts = folder / "Artifacts"
    artifacts.mkdir(exist_ok=True)
    version = next_version(artifacts, stem)
    today = datetime.date.today().isoformat()
    base = f"{stem} v{version} {today}"

    ps_path = artifacts / f"{base}.ps"
    pdf_path = artifacts / f"{base}.pdf"
    ps_path.write_text(ps_text, encoding="utf-8")

    result = subprocess.run(
        ["ps2pdf", "-dPDFSETTINGS=/prepress", str(ps_path), str(pdf_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not pdf_path.exists():
        ps_path.unlink(missing_ok=True)
        raise SystemExit(f"ps2pdf failed:\n{result.stderr.strip()}")

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

    out = render(vault, folder, args.kind, args.pages, preview=not args.no_preview)

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
