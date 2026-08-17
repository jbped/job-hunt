#!/usr/bin/env python3
"""Adobe Helvetica advance widths, in 1/1000 em, for character codes 32-255.

Extracted from the same Ghostscript font that renders the PDF, so the wrapping
computed here matches what actually lands on the page. Embedded rather than read
from a system AFM at run time — the scripts must work on a friend's machine with
no assumptions about where font metrics live.

Codes above 126 are Adobe StandardEncoding, which is what `/Helvetica findfont`
uses: en dash at 177, em dash at 208, periodcentered at 180, quoteright at 39.
"""

from __future__ import annotations

FIRST_CODE = 32

HELVETICA = (
    278, 278, 355, 556, 556, 889, 667, 222, 333, 333, 389, 584, 278, 333, 278, 278, 556,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556, 1015, 667,
    667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778, 667, 778, 722,
    667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556, 222, 556, 556, 500,
    556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556, 556, 556, 333, 500, 278,
    556, 500, 722, 500, 500, 500, 334, 260, 334, 584, 278, 278, 278, 278, 278, 278, 278,
    278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278,
    278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 333, 556, 556, 278, 556, 556, 556,
    556, 191, 333, 556, 333, 333, 500, 500, 278, 556, 556, 556, 278, 278, 537, 350, 222,
    333, 333, 556, 1000, 1000, 278, 611, 278, 333, 333, 333, 333, 333, 333, 333, 333, 278,
    333, 333, 278, 333, 333, 333, 1000, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278,
    278, 278, 278, 278, 278, 278, 1000, 278, 370, 278, 278, 278, 278, 556, 778, 1000, 365,
    278, 278, 278, 278, 278, 889, 278, 278, 278, 278, 278, 278, 222, 611, 944, 611, 278,
    278, 278, 278,
)

HELVETICA_BOLD = (
    278, 333, 474, 556, 556, 889, 722, 278, 333, 333, 389, 584, 278, 333, 278, 278, 556,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611, 975, 722,
    722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778, 667, 778, 722,
    667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556, 278, 556, 611, 556,
    611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611, 611, 611, 389, 556, 333,
    611, 556, 778, 556, 556, 500, 389, 280, 389, 584, 278, 278, 278, 278, 278, 278, 278,
    278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278,
    278, 278, 278, 278, 278, 278, 278, 278, 278, 278, 333, 556, 556, 278, 556, 556, 556,
    556, 238, 500, 556, 333, 333, 611, 611, 278, 556, 556, 556, 278, 278, 556, 350, 278,
    500, 500, 556, 1000, 1000, 278, 611, 278, 333, 333, 333, 333, 333, 333, 333, 333, 278,
    333, 333, 278, 333, 333, 333, 1000, 278, 278, 278, 278, 278, 278, 278, 278, 278, 278,
    278, 278, 278, 278, 278, 278, 1000, 278, 370, 278, 278, 278, 278, 611, 778, 1000, 365,
    278, 278, 278, 278, 278, 889, 278, 278, 278, 278, 278, 278, 278, 611, 944, 611, 278,
    278, 278, 278,
)

WIDTHS = {"Helvetica": HELVETICA, "Helvetica-Bold": HELVETICA_BOLD}

# Unicode the vault's markdown actually contains -> StandardEncoding code point.
# PostScript string literals take these as octal escapes.
STANDARD_ENCODING = {
    "\u00b7": 180,   # periodcentered, the skills separator
    "\u2013": 177,   # en dash, used in date ranges
    "\u2014": 208,   # em dash
    "\u2018": 96,    # quoteleft
    "\u2019": 39,    # quoteright (StandardEncoding maps ASCII 39 to the curly form)
    "\u201c": 170,   # quotedblleft
    "\u201d": 186,   # quotedblright
    "\u2026": 188,   # ellipsis
    "\u2022": 183,   # bullet
    "\u00a0": 32,    # non-breaking space -> space
    "\u2212": 45,    # minus -> hyphen
}


def encode(text: str) -> str:
    """Map a Python string to PostScript StandardEncoding codes, one per char.

    Characters with no mapping become '?' rather than silently vanishing, so a
    missing glyph is visible in the proof instead of shifting the layout.
    """
    out = []
    for char in text:
        code = ord(char)
        if 32 <= code <= 126:
            out.append(code)
        elif char in STANDARD_ENCODING:
            out.append(STANDARD_ENCODING[char])
        else:
            out.append(63)
    return "".join(chr(c) for c in out)


def width(text: str, font: str, size: float) -> float:
    """Advance width of `text` in points, matching what Ghostscript will render."""
    table = WIDTHS[font]
    total = 0
    for char in encode(text):
        code = ord(char)
        index = code - FIRST_CODE
        total += table[index] if 0 <= index < len(table) else 0
    return total * size / 1000.0


def escape(text: str) -> str:
    """Quote a string for a PostScript literal, with octal escapes for high codes."""
    out = []
    for char in encode(text):
        code = ord(char)
        if char in "()\\":
            out.append("\\" + char)
        elif 32 <= code <= 126:
            out.append(char)
        else:
            out.append(f"\\{code:03o}")
    return "".join(out)


def wrap(text: str, font: str, size: float, max_width: float) -> list[str]:
    """Greedy word wrap on measured width. Never splits a word."""
    words = text.split()
    if not words:
        return []
    lines, current = [], words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if width(candidate, font, size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines
