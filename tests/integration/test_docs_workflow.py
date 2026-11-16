"""The docs workflow builds strictly, and deploys only when Pages has been switched on."""

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW: dict[str, Any] = yaml.safe_load((ROOT / ".github" / "workflows" / "docs.yml").read_text())


def steps(job: str) -> str:
    return "\n".join(str(s.get("run", s.get("uses", ""))) for s in WORKFLOW["jobs"][job]["steps"])


def test_the_site_is_built_strictly_from_the_docs_group_only() -> None:
    text = steps("build")
    assert "mkdocs build --strict" in text and "--only-group docs" in text


def test_it_runs_on_docs_changes_for_pull_requests_and_main() -> None:
    triggers: dict[str, Any] = WORKFLOW.get("on") or WORKFLOW[True]  # type: ignore[index]  # YAML 1.1 reads `on` as True
    assert triggers["pull_request"]["paths"] == triggers["push"]["paths"]
    assert "docs/**" in triggers["push"]["paths"] and "mkdocs.yml" in triggers["push"]["paths"]
    assert triggers["push"]["branches"] == ["main"]
