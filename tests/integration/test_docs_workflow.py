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


def test_deploying_needs_a_push_to_main_and_an_explicit_opt_in() -> None:
    deploy = WORKFLOW["jobs"]["deploy"]
    assert "github.event_name == 'push'" in deploy["if"]
    assert "vars.DOCS_DEPLOY == 'true'" in deploy["if"]
    assert deploy["needs"] == "build"
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}
    assert "actions/deploy-pages" in steps("deploy")


def test_the_site_is_packaged_only_when_it_will_be_deployed() -> None:
    (package,) = [
        s
        for s in WORKFLOW["jobs"]["build"]["steps"]
        if "upload-pages-artifact" in s.get("uses", "")
    ]
    assert "vars.DOCS_DEPLOY == 'true'" in package["if"] and package["with"]["path"] == "site"
