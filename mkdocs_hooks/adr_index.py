"""MkDocs hook: list every decision record on the decisions page, so the list never goes stale."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DECISIONS_PAGE = "decisions.md"


def adr_titles(adr_dir: Path) -> list[tuple[str, str]]:
    """(file name, title) of each numbered record, in order. The title is the first heading."""
    titles: list[tuple[str, str]] = []
    for path in sorted(adr_dir.glob("[0-9]*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        heading = lines[0] if lines else path.stem
        titles.append((path.name, re.sub(r"^#\s*", "", heading).strip()))
    return titles


def render_index(adr_dir: Path) -> str:
    """A markdown bullet list linking each record."""
    return "\n".join(f"- [{title}](adr/{name})" for name, title in adr_titles(adr_dir)) + "\n"


def on_page_markdown(markdown: str, page: Any, config: Any, files: Any) -> str:
    """Append the list of records to the decisions page."""
    if page.file.src_path != DECISIONS_PAGE:
        return markdown
    return markdown.rstrip() + "\n\n" + render_index(Path(config["docs_dir"]) / "adr")
