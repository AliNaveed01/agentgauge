"""examples/real-agent: the suite is valid, and a model that follows the policy passes it."""

import asyncio
import re
from pathlib import Path
from typing import Any

from agentgauge.core import ToolCall, load_suite
from agentgauge.providers import FakeProvider, FakeResponse
from agentgauge.runner import run_suite

SUITE = Path(__file__).resolve().parents[2] / "examples" / "real-agent" / "suite.yaml"


def order_ids(text: str) -> list[str]:
    return re.findall(r"\b[A-D]\d{3}\b", text)


def call(name: str, **arguments: Any) -> FakeResponse:
    import json

    return FakeResponse(tool_calls=(ToolCall(id="c", name=name, arguments=json.dumps(arguments)),))


def following_the_policy() -> FakeProvider:
    """One scripted reply list per case, built from the case's own expected route."""
    responses: dict[str, Any] = {}
    for case in load_suite(SUITE).cases:
        user = case.input[-1].content
        ids = order_ids(user)
        steps: list[str | FakeResponse] = []
        lookups = iter(ids)
        for expected in case.metadata["expected_trajectory"]:
            if expected["name"] == "lookup_order":
                steps.append(call("lookup_order", order_id=next(lookups)))
            else:
                steps.append(call("refund_order", order_id=ids[0], reason="customer request"))
        steps.append("Done.")
        responses[user] = steps
    return FakeProvider(responses, name="policy-follower")


def test_the_suite_is_consistent() -> None:
    suite = load_suite(SUITE)
    tools = {t.name for t in suite.tools}
    assert tools == {"lookup_order", "refund_order"}
    assert len(suite.cases) == 10 and len({c.id for c in suite.cases}) == 10
    assert suite.agent is not None and suite.agent.max_steps == 6
    assert [s.name for s in suite.scorers] == ["trajectory_match", "trajectory_budget"]
    for case in suite.cases:
        assert case.input[0].role == "system" and case.input[-1].role == "user"
        for expected in case.metadata["expected_trajectory"]:
            assert expected["name"] in tools
    mocked = {m.arguments["order_id"] for m in suite.tool_mocks if m.arguments}
    wanted = {i for c in suite.cases for i in order_ids(c.input[-1].content)}
    assert wanted <= mocked, "every order a case mentions has a scripted lookup result"


def test_every_case_uses_the_same_system_prompt() -> None:
    prompts = {case.input[0].content for case in load_suite(SUITE).cases}
    assert len(prompts) == 1 and "lookup_order" in next(iter(prompts))


def test_a_model_that_follows_the_policy_passes_every_case() -> None:
    run = asyncio.run(run_suite(load_suite(SUITE), following_the_policy(), concurrency=1))
    failed = [r.case_id for r in run.results if not r.passed]
    assert failed == [] and len(run.results) == 10


def test_refunding_without_looking_up_fails_that_case() -> None:
    suite = load_suite(SUITE)
    provider = FakeProvider(
        {
            case.input[-1].content: [call("refund_order", order_id="A100", reason="x"), "ok"]
            for case in suite.cases
        },
        name="careless",
    )
    run = asyncio.run(run_suite(suite, provider, concurrency=1))
    by_id = {r.case_id: r.passed for r in run.results}
    assert by_id["refund-delivered"] is False and by_id["refund-shipped-refused"] is False
    assert not any(by_id.values())
