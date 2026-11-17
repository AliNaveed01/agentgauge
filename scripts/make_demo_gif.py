"""Render the terminal demo GIF from the real output of agentgauge commands.

Nothing is recorded and no recording tool is needed: the script runs the commands, captures
their colour output, and draws it with Pillow (which comes with matplotlib, in the dev group)
as a typed command followed by its output appearing line by line. Run it from the repository:

    uv run python scripts/make_demo_gif.py            # writes docs/assets/demo.gif

It needs a monospace font with box-drawing characters; it uses Menlo on macOS. Pass --font to
use another file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BACKGROUND = (24, 24, 27)
FOREGROUND = (228, 228, 231)
PROMPT = (74, 222, 128)
PADDING = 18

# The sixteen ANSI colours, tuned for a dark background.
ANSI16 = [
    (24, 24, 27), (248, 113, 113), (74, 222, 128), (250, 204, 21),
    (96, 165, 250), (192, 132, 252), (34, 211, 238), (212, 212, 216),
    (113, 113, 122), (252, 165, 165), (134, 239, 172), (253, 224, 71),
    (147, 197, 253), (216, 180, 254), (103, 232, 249), (250, 250, 250),
]  # fmt: skip

Color = tuple[int, int, int]
SGR = re.compile(r"\x1b\[([0-9;]*)m")
OTHER_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[A-Za-ln-z]")


@dataclass(frozen=True)
class Cell:
    char: str
    color: Color = FOREGROUND
    bold: bool = False


def color_256(n: int) -> Color:
    """The xterm 256-colour palette: 16 base colours, a 6x6x6 cube, then 24 greys."""
    if n < 16:
        return ANSI16[n]
    if n < 232:
        n -= 16
        steps = [0, 95, 135, 175, 215, 255]
        return steps[n // 36], steps[(n // 6) % 6], steps[n % 6]
    level = 8 + (n - 232) * 10
    return level, level, level


def parse_ansi(text: str) -> list[list[Cell]]:
    """Turn text with SGR colour codes into rows of coloured cells. Other escapes are dropped."""
    text = OTHER_ESCAPE.sub("", text.replace("\r\n", "\n"))
    rows: list[list[Cell]] = [[]]
    color: Color = FOREGROUND
    bold = False
    dim = False
    position = 0
    for match in SGR.finditer(text):
        for char in text[position : match.start()]:
            rows.append([]) if char == "\n" else rows[-1].append(
                Cell(char, _shade(color, dim), bold)
            )
        position = match.end()
        codes = [int(c) if c else 0 for c in match.group(1).split(";")]
        i = 0
        while i < len(codes):
            code = codes[i]
            if code == 0:
                color, bold, dim = FOREGROUND, False, False
            elif code == 1:
                bold = True
            elif code == 2:
                dim = True
            elif code in (22,):
                bold = dim = False
            elif 30 <= code <= 37:
                color = ANSI16[code - 30]
            elif 90 <= code <= 97:
                color = ANSI16[code - 90 + 8]
            elif code == 39:
                color = FOREGROUND
            elif code == 38 and i + 1 < len(codes):
                if codes[i + 1] == 5 and i + 2 < len(codes):
                    color = color_256(codes[i + 2])
                    i += 2
                elif codes[i + 1] == 2 and i + 4 < len(codes):
                    color = (codes[i + 2], codes[i + 3], codes[i + 4])
                    i += 4
            i += 1
    for char in text[position:]:
        rows.append([]) if char == "\n" else rows[-1].append(Cell(char, _shade(color, dim), bold))
    while rows and not rows[-1]:
        rows.pop()
    return rows


def _shade(color: Color, dim: bool) -> Color:
    return (color[0] * 6 // 10, color[1] * 6 // 10, color[2] * 6 // 10) if dim else color
