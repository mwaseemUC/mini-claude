from pathlib import Path
from types import SimpleNamespace

from mini_claude.agent import Agent
from mini_claude.context import ContextPolicy, applied_edits, fullness
from mini_claude.tools import Toolbox
from tests.fakes import FakeClient, reply, text, tool_use


def test_policy_builds_the_documented_edit() -> None:
    edit = ContextPolicy(trigger_tokens=30_000, keep_tool_uses=3, clear_at_least=5_000).edits()
    assert edit == {
        "edits": [
            {
                "type": "clear_tool_uses_20250919",
                "trigger": {"type": "input_tokens", "value": 30_000},
                "keep": {"type": "tool_uses", "value": 3},
                "clear_at_least": {"type": "input_tokens", "value": 5_000},
            }
        ]
    }


def test_applied_edits_reads_the_response_field() -> None:
    response = SimpleNamespace(
        context_management=SimpleNamespace(
            applied_edits=[SimpleNamespace(cleared_tool_uses=8, cleared_input_tokens=50_000)]
        )
    )
    assert applied_edits(response) == [{"cleared_tool_uses": 8, "cleared_input_tokens": 50_000}]
    assert applied_edits(SimpleNamespace()) == []
    assert applied_edits(SimpleNamespace(context_management=None)) == []


def test_fullness() -> None:
    assert fullness(250_000) == 0.25


def test_agent_reports_clearing_and_never_edits_history(tmp_path: Path) -> None:
    first = reply(tool_use("t1", "list_dir"), stop="tool_use")
    second = reply(text("done"))
    second.context_management = SimpleNamespace(
        applied_edits=[SimpleNamespace(cleared_tool_uses=4, cleared_input_tokens=20_000)]
    )
    events: list[tuple[str, dict]] = []
    agent = Agent(
        client=FakeClient(first, second),
        toolbox=Toolbox(tmp_path, lambda *_: True),
        model="claude-haiku-5-5",
        on_event=lambda kind, payload: events.append((kind, payload)),
    )
    agent.run("go")
    assert ("context_cleared", {"cleared_tool_uses": 4, "cleared_input_tokens": 20_000}) in events
    assert agent.usage.cleared_tool_uses == 4
    # Our copy of the history still holds the original tool result: clearing happens server-side.
    assert agent.messages[2]["content"][0]["type"] == "tool_result"
    assert agent.messages[2]["content"][0]["content"]
