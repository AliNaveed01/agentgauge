"""The demo GIF script: its ANSI parsing, with no commands run and no GIF drawn yet."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "make_demo_gif", ROOT / "scripts" / "make_demo_gif.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look the module up by name
    spec.loader.exec_module(module)
    return module


def test_plain_text_becomes_rows_of_default_coloured_cells() -> None:
    script = load_script()
    rows = script.parse_ansi("ab\ncd\n")
    assert [[c.char for c in row] for row in rows] == [["a", "b"], ["c", "d"]]
    assert all(c.color == script.FOREGROUND and not c.bold for row in rows for c in row)


def test_colours_bold_and_reset_apply_to_the_text_between_codes() -> None:
    script = load_script()
    (row,) = script.parse_ansi("x\x1b[1;31mred\x1b[0my\x1b[32mg\x1b[39mz")
    cells = {c.char: c for c in row}
    assert cells["x"].color == script.FOREGROUND
    assert cells["r"].color == script.ANSI16[1] and cells["r"].bold
    assert cells["y"].color == script.FOREGROUND and not cells["y"].bold
    assert cells["g"].color == script.ANSI16[2]
    assert cells["z"].color == script.FOREGROUND


def test_256_colour_and_truecolour_codes() -> None:
    script = load_script()
    (row,) = script.parse_ansi("\x1b[38;5;196ma\x1b[38;2;1;2;3mb\x1b[38;5;244mc\x1b[38;5;9md")
    colours = [c.color for c in row]
    assert colours == [(255, 0, 0), (1, 2, 3), (128, 128, 128), script.ANSI16[9]]


def test_dim_darkens_and_other_escape_sequences_are_dropped() -> None:
    script = load_script()
    (row,) = script.parse_ansi("\x1b[?25l\x1b[2mdim\x1b[22mfull\x1b[2K")
    assert "".join(c.char for c in row) == "dimfull"
    assert row[0].color == tuple(v * 6 // 10 for v in script.FOREGROUND)
    assert row[3].color == script.FOREGROUND


def test_trailing_blank_lines_are_trimmed_and_carriage_returns_ignored() -> None:
    script = load_script()
    assert len(script.parse_ansi("a\r\nb\r\n\r\n\r\n")) == 2
    assert script.parse_ansi("") == []


def fonts_or_skip(script: Any) -> Any:
    try:
        return script.load_fonts()
    except script.FontError:
        pytest.skip("no monospace font on this machine")


def test_a_missing_font_file_is_reported_clearly(tmp_path: Path) -> None:
    script = load_script()
    with pytest.raises(script.FontError, match="--font"):
        script.load_fonts(tmp_path / "nope.ttf")


def test_a_command_is_typed_then_its_output_appears_in_chunks() -> None:
    script = load_script()
    scene = script.Scene("echo hi", "\x1b[32mone\x1b[0m\ntwo\nthree\nfour\n")
    steps = script.scene_steps(scene, typing=2, chunk=3)

    def text(row: list[Any]) -> str:
        return "".join(cell.char for cell in row)

    assert text(steps[0][0][0]) == "$ "  # the prompt alone, with a cursor
    assert text(steps[1][0][0]) == "$ ec"  # two characters typed
    assert text(steps[-1][0][0]) == "$ echo hi"  # the command stays on the first row
    cursors = [cursor for _, _, cursor in steps]
    assert cursors[0] is True and cursors[-1] is False
    assert [len(r) for r, _, _ in steps][-2:] == [4, 5]  # three, then all four output lines
    assert steps[-1][1] == 2600, "the final frame is held so the output can be read"


def test_a_frame_has_the_size_of_its_grid_and_shows_the_text() -> None:
    script = load_script()
    fonts = fonts_or_skip(script)
    rows = script.parse_ansi("\x1b[31mred\x1b[0m plain\n")
    image = script.render_frame(rows, fonts, columns=40, height=5, cursor=False)
    assert image.size == (
        int(40 * fonts.cell_width) + 2 * script.PADDING,
        5 * fonts.line_height + 2 * script.PADDING,
    )
    assert len({image.getpixel((x, y)) for x in range(0, image.width, 3) for y in range(0, 40)}) > 2


def test_the_gif_is_built_with_many_frames_and_stays_small(tmp_path: Path) -> None:
    script = load_script()
    fonts = fonts_or_skip(script)
    scenes = [
        script.Scene("agentgauge run suite.yaml", "\x1b[1mRun\x1b[0m done\n3/4 passed\n"),
        script.Scene("agentgauge compare previous latest", "\x1b[31mREGRESSION\x1b[0m\n"),
    ]
    out = tmp_path / "assets" / "demo.gif"
    count = script.build_gif(scenes, out, fonts, columns=60, height=6)
    data = out.read_bytes()
    assert data[:6] == b"GIF89a" and count > 20 and len(data) < 300_000
