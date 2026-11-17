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


FONT_SIZE = 15
FONT_CANDIDATES = (
    Path("/System/Library/Fonts/Menlo.ttc"),
    Path("/Library/Fonts/Menlo.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
)


class FontError(RuntimeError):
    """No usable monospace font was found."""


@dataclass(frozen=True)
class Fonts:
    regular: object
    bold: object
    cell_width: float
    line_height: int


def load_fonts(path: Path | None = None) -> Fonts:
    """A regular and a bold monospace font, and the size of one character cell."""
    from PIL import ImageFont

    for candidate in [path] if path else list(FONT_CANDIDATES):
        if candidate is None or not candidate.exists():
            continue
        regular = ImageFont.truetype(str(candidate), FONT_SIZE, index=0)
        bold = (
            ImageFont.truetype(str(candidate), FONT_SIZE, index=1)
            if candidate.suffix == ".ttc"
            else regular
        )
        return Fonts(regular, bold, regular.getlength("M"), int(FONT_SIZE * 1.4))
    raise FontError("no monospace font found; pass --font with a .ttf or .ttc file")


def render_frame(rows: list[list[Cell]], fonts: Fonts, columns: int, height: int, cursor: bool):
    """Draw ``rows`` on a dark terminal background. ``cursor`` adds a block after the last row."""
    from PIL import Image, ImageDraw

    width = int(columns * fonts.cell_width) + 2 * PADDING
    image = Image.new("RGB", (width, height * fonts.line_height + 2 * PADDING), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for y, row in enumerate(rows[:height]):
        top = PADDING + y * fonts.line_height
        start = 0
        while start < len(row):  # draw runs of one style as a single string
            style = (row[start].color, row[start].bold)
            end = start
            while end < len(row) and (row[end].color, row[end].bold) == style:
                end += 1
            text = "".join(cell.char for cell in row[start:end])
            font = fonts.bold if style[1] else fonts.regular
            draw.text((PADDING + start * fonts.cell_width, top), text, font=font, fill=style[0])
            start = end
    if cursor and rows:
        row = rows[min(len(rows), height) - 1]
        x = PADDING + len(row) * fonts.cell_width
        top = PADDING + (min(len(rows), height) - 1) * fonts.line_height
        draw.rectangle(
            (x, top + 2, x + fonts.cell_width - 1, top + fonts.line_height - 2), fill=FOREGROUND
        )
    return image


@dataclass(frozen=True)
class Scene:
    """One command and the output it printed (with colour codes)."""

    command: str
    output: str


def scene_steps(
    scene: Scene, *, typing: int = 2, chunk: int = 3
) -> list[tuple[list[list[Cell]], int, bool]]:
    """(rows, milliseconds, cursor) for a command being typed, then its output appearing."""
    prompt = [Cell("$", PROMPT, True), Cell(" ")]
    steps: list[tuple[list[list[Cell]], int, bool]] = [([prompt], 500, True)]
    for end in range(typing, len(scene.command) + typing, typing):
        typed = [Cell(c) for c in scene.command[:end]]
        steps.append(([[*prompt, *typed]], 60, True))
    command_row = [*prompt, *[Cell(c) for c in scene.command]]
    steps.append(([command_row], 350, False))
    output = parse_ansi(scene.output)
    for end in range(chunk, len(output) + chunk, chunk):
        steps.append(([command_row, *output[:end]], 90, False))
    steps[-1] = (steps[-1][0], 2600, False)
    return steps


def build_gif(
    scenes: list[Scene], out: Path, fonts: Fonts, *, columns: int = 100, height: int = 20
) -> int:
    """Write the GIF and return its frame count. Each scene starts on a cleared screen."""
    frames = []
    durations: list[int] = []
    for scene in scenes:
        for rows, milliseconds, cursor in scene_steps(scene):
            image = render_frame(rows, fonts, columns, height, cursor)
            frames.append(image.convert("P", palette=1, colors=48))  # 1 = adaptive palette
            durations.append(milliseconds)
    out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    return len(frames)


COMMANDS = (
    ["run", "examples/regression/baseline.yaml"],
    ["run", "examples/regression/candidate.yaml"],
    ["compare", "previous", "latest"],
    ["report", "latest", "--baseline", "previous"],
)


def capture_scenes(columns: int = 100) -> list[Scene]:
    """Run the commands for real in a scratch directory and keep what they printed."""
    import os
    import subprocess
    import sys
    import tempfile

    scenes: list[Scene] = []
    with tempfile.TemporaryDirectory() as scratch:
        work = Path(scratch)
        (work / "examples").symlink_to(ROOT / "examples")
        env = {
            **{k: v for k, v in os.environ.items() if k not in ("NO_COLOR", "AGENTGAUGE_DB")},
            "COLUMNS": str(columns),
            "TERM": "xterm-256color",
            "FORCE_COLOR": "1",
        }
        for args in COMMANDS:
            done = subprocess.run(
                [sys.executable, "-m", "agentgauge", *args],
                cwd=work,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            output = done.stdout + done.stderr
            if done.returncode:
                output += f"\x1b[2m# exit code {done.returncode}\x1b[0m\n"
            scenes.append(Scene("agentgauge " + " ".join(args), output))
    return scenes


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "assets" / "demo.gif")
    parser.add_argument("--font", type=Path, default=None)
    args = parser.parse_args()
    fonts = load_fonts(args.font)
    scenes = capture_scenes()
    count = build_gif(scenes, args.out, fonts)
    print(f"wrote {args.out}: {count} frames, {args.out.stat().st_size // 1024} KiB")


if __name__ == "__main__":
    main()
