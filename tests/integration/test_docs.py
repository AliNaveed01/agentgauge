"""The docs cannot drift from the code: every command is documented, every link resolves."""

import re
from pathlib import Path
from typing import Any

import typer.main

from agentgauge.cli import app

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
LINK = re.compile(r"\]\(([^)\s]+)\)")


def leaf_commands() -> dict[str, Any]:
    """Every command that does something, by its full name (``runs show``)."""
    found: dict[str, Any] = {}

    def walk(group: Any, prefix: str) -> None:
        for name, command in group.commands.items():
            if hasattr(command, "commands"):
                walk(command, f"{prefix}{name} ")
            else:
                found[f"{prefix}{name}"] = command

    walk(typer.main.get_command(app), "")
    return found


def test_the_command_reference_names_every_command_and_option() -> None:
    text = (DOCS / "cli.md").read_text()
    commands = leaf_commands()
    assert {
        "run",
        "runs list",
        "runs show",
        "calibrate",
        "import-otel",
        "compare",
        "report",
    } <= set(commands)
    for name, command in commands.items():
        assert f"agentgauge {name}" in text, f"cli.md does not document `agentgauge {name}`"
        for param in command.params:
            for opt in param.opts:
                if opt.startswith("--"):
                    assert f"`{opt}`" in text, f"cli.md misses {opt} of `agentgauge {name}`"


def markdown_files() -> list[Path]:
    return sorted([*DOCS.rglob("*.md"), ROOT / "README.md"])


def test_every_relative_link_in_the_docs_and_readme_resolves() -> None:
    broken: list[str] = []
    for page in markdown_files():
        for target in LINK.findall(page.read_text()):
            if re.match(r"([a-z][a-z0-9+.-]*:|#)", target):
                continue  # a URL or an in-page anchor
            path = target.split("#", 1)[0]
            if path and not (page.parent / path).exists():
                broken.append(f"{page.relative_to(ROOT)} -> {target}")
    assert not broken, "broken links:\n" + "\n".join(broken)


def test_every_page_in_the_site_navigation_exists_and_every_guide_is_in_it() -> None:
    nav = (ROOT / "mkdocs.yml").read_text()
    listed = set(re.findall(r":\s+([\w/.-]+\.md)\s*$", nav, flags=re.MULTILINE))
    assert listed, "no pages found in the nav"
    for page in listed:
        assert (DOCS / page).exists(), f"nav lists {page}, which does not exist"
    for guide in DOCS.glob("*.md"):
        assert guide.name in listed, f"docs/{guide.name} is not in the site navigation"
