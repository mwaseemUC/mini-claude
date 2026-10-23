from pathlib import Path

from mini_claude.agent import Agent
from mini_claude.tools import Toolbox
from tests.fakes import FakeClient, reply, text, tool_use


def make_agent(tmp_path: Path, client: FakeClient, **kw) -> Agent:
    (tmp_path / "app.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    return Agent(client=client, toolbox=Toolbox(tmp_path, lambda *_: True), **kw)


def test_plain_answer_ends_the_loop(tmp_path: Path) -> None:
    client = FakeClient(reply(text("Hello!")))
    agent = make_agent(tmp_path, client, model="claude-haiku-5-5")
    assert agent.run("hi") == "Hello!"
    assert agent.usage.llm_calls == 1
    assert [m["role"] for m in agent.messages] == ["user", "assistant"]


def test_tool_call_is_run_and_result_sent_back(tmp_path: Path) -> None:
    client = FakeClient(
        reply(tool_use("t1", "read_file", path="app.py"), stop="tool_use"),
        reply(text("It subtracts instead of adding.")),
    )
    agent = make_agent(tmp_path, client, model="claude-haiku-5-5")
    assert agent.run("what's wrong?") == "It subtracts instead of adding."
    second_request = client.requests[1]["messages"]
    result = second_request[-1]["content"][0]
    assert second_request[-1]["role"] == "user"
    assert result["type"] == "tool_result" and result["tool_use_id"] == "t1"
    assert "return a - b" in result["content"] and result["is_error"] is False


def test_parallel_tool_calls_return_in_one_message(tmp_path: Path) -> None:
    client = FakeClient(
        reply(
            tool_use("a", "list_dir"),
            tool_use("b", "grep", pattern="def"),
            stop="tool_use",
        ),
        reply(text("done")),
    )
    agent = make_agent(tmp_path, client, model="claude-haiku-5-5")
    agent.run("look around")
    results = client.requests[1]["messages"][-1]["content"]
    assert [r["tool_use_id"] for r in results] == ["a", "b"]
    assert agent.usage.tool_calls == 2


def test_tool_errors_go_back_to_the_model(tmp_path: Path) -> None:
    client = FakeClient(
        reply(tool_use("t1", "read_file", path="../../etc/passwd"), stop="tool_use"),
        reply(text("I can't read outside the project.")),
    )
    agent = make_agent(tmp_path, client, model="claude-haiku-5-5")
    agent.run("read passwd")
    result = client.requests[1]["messages"][-1]["content"][0]
    assert result["is_error"] is True and "outside the workspace" in result["content"]


def test_history_is_append_only_and_keeps_full_content(tmp_path: Path) -> None:
    first = reply(tool_use("t1", "list_dir"), stop="tool_use")
    client = FakeClient(first, reply(text("ok")))
    agent = make_agent(tmp_path, client, model="claude-haiku-5-5")
    agent.run("go")
    assert agent.messages[1]["content"] is first.content  # unchanged object, not just its text


def test_max_turns_stops_a_runaway_loop(tmp_path: Path) -> None:
    looping = [reply(tool_use(f"t{i}", "list_dir"), stop="tool_use") for i in range(3)]
    agent = make_agent(tmp_path, FakeClient(*looping), model="claude-haiku-5-5", max_turns=3)
    assert "stopped after 3 model calls" in agent.run("loop forever")


def test_max_tokens_and_refusal_are_reported(tmp_path: Path) -> None:
    agent = make_agent(tmp_path, FakeClient(reply(text("partial"), stop="max_tokens")))
    assert "output token limit" in agent.run("write a novel")
    agent = make_agent(tmp_path, FakeClient(reply(stop="refusal")))
    assert "declined" in agent.run("something")


def test_request_shape_and_fallback_routing(tmp_path: Path) -> None:
    client = FakeClient(reply(text("a")), reply(text("b")))
    make_agent(tmp_path, client, model="claude-sonnet-5-5").run("x")
    make_agent(tmp_path, client, model="claude-haiku-5-5").run("y")
    sonnet, haiku = client.requests
    assert sonnet["fallbacks"] == "default"
    assert sonnet["betas"] == ["context-management-2025-06-27", "server-side-fallback-2026-07-01"]
    assert "fallbacks" not in haiku
    assert haiku["betas"] == ["context-management-2025-06-27"]
    for req in (sonnet, haiku):
        edit = req["context_management"]["edits"][0]
        assert edit["type"] == "clear_tool_uses_20250919"
        assert edit["trigger"] == {"type": "input_tokens", "value": 60_000}
        assert req["cache_control"] == {"type": "ephemeral"}
        assert req["output_config"] == {"effort": "medium"}
        assert "temperature" not in req and "thinking" not in req
        assert {t["name"] for t in req["tools"]} >= {"read_file", "run_command"}


def test_cost_includes_cache_pricing(tmp_path: Path) -> None:
    r = reply(text("hi"))
    r.usage.input_tokens = 1_000
    r.usage.cache_creation_input_tokens = 2_000
    r.usage.cache_read_input_tokens = 10_000
    r.usage.output_tokens = 500
    agent = make_agent(tmp_path, FakeClient(r), model="claude-sonnet-5-5")
    agent.run("x")
    expected = (1_000 * 2 + 2_000 * 2 * 1.25 + 10_000 * 2 * 0.1 + 500 * 10) / 1_000_000
    assert abs(agent.usage.cost_usd - expected) < 1e-12
    assert agent.usage.last_input_tokens == 13_000
