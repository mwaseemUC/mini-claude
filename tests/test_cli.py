from pathlib import Path

from rich.console import Console

from mini_claude.agent import Agent
from mini_claude.cli import Terminal, footer, main
from mini_claude.tools import Toolbox
from tests.fakes import FakeClient, reply, text, tool_use


def recording_console() -> Console:
    return Console(record=True, width=120, force_terminal=False)


def test_one_shot_request_prints_answer_tools_and_footer(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello\n", encoding="utf-8")
    client = FakeClient(
        reply(tool_use("t1", "read_file", path="a.txt"), stop="tool_use"),
        reply(text("The file says **hello**.")),
    )
    console = recording_console()
    code = main(
        ["what does a.txt say", "--dir", str(tmp_path), "--model", "claude-haiku-5-5"],
        client=client,
        console=console,
    )
    out = console.export_text()
    assert code == 0
    assert "> read_file" in out and "The file says hello." in out
    assert "claude-haiku-5-5 | context" in out and "2 calls, 1 tools" in out


def test_yes_flag_auto_approves_and_shows_the_diff(tmp_path: Path) -> None:
    client = FakeClient(
        reply(tool_use("t1", "write_file", path="new.py", content="x = 1\n"), stop="tool_use"),
        reply(text("created")),
    )
    console = recording_console()
    main(["make new.py", "--dir", str(tmp_path), "--yes"], client=client, console=console)
    out = console.export_text()
    assert "+x = 1" in out and "auto-approved" in out
    assert (tmp_path / "new.py").read_text(encoding="utf-8") == "x = 1\n"


def test_declined_write_is_reported_to_the_model(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("mini_claude.cli.Confirm.ask", lambda *a, **k: False)
    client = FakeClient(
        reply(tool_use("t1", "write_file", path="x.py", content="boom\n"), stop="tool_use"),
        reply(text("ok, not writing")),
    )
    main(["write x", "--dir", str(tmp_path)], client=client, console=recording_console())
    assert not (tmp_path / "x.py").exists()
    result = client.requests[1]["messages"][-1]["content"][0]
    assert result["is_error"] and "declined" in result["content"]


def test_interrupt_closes_dangling_tool_calls(tmp_path: Path) -> None:
    agent = Agent(client=FakeClient(), toolbox=Toolbox(tmp_path, lambda *_: True))
    agent.messages = [
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": [tool_use("t9", "list_dir")]},
    ]
    agent.close_interrupted_turn()
    closing = agent.messages[-1]
    assert closing["role"] == "user"
    assert closing["content"][0]["tool_use_id"] == "t9" and closing["content"][0]["is_error"]
    agent.close_interrupted_turn()  # idempotent: last message is now a user message
    assert len(agent.messages) == 3


def test_footer_format(tmp_path: Path) -> None:
    agent = Agent(client=FakeClient(), toolbox=Toolbox(tmp_path, lambda *_: True))
    agent.usage.last_input_tokens = 50_000
    agent.usage.cost_usd = 0.0123
    assert "context 5.0% (50,000 tokens)" in footer(agent) and "$0.0123" in footer(agent)


def test_terminal_reports_tool_errors_and_clearing() -> None:
    console = recording_console()
    term = Terminal(console)
    term.on_event("tool_result", {"name": "read_file", "output": "refused: x", "error": True})
    term.on_event("context_cleared", {"cleared_tool_uses": 4, "cleared_input_tokens": 9})
    out = console.export_text()
    assert "! refused: x" in out and "4 old tool results cleared" in out
