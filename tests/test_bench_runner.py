"""Runner tests on a tiny synthetic task, with fake clients (no API calls)."""

import json
from pathlib import Path

import pytest

from bench import run_bench
from tests.fakes import FakeClient, reply, text, tool_use


@pytest.fixture
def tasks_dir(tmp_path: Path) -> Path:
    task = tmp_path / "tasks" / "t99-double"
    (task / "workspace").mkdir(parents=True)
    (task / "hidden").mkdir()
    (task / "solution").mkdir()
    (task / "workspace" / "mathx.py").write_text("def double(x):\n    return x\n", encoding="utf-8")
    (task / "solution" / "mathx.py").write_text(
        "def double(x):\n    return 2 * x\n", encoding="utf-8"
    )
    (task / "hidden" / "test_hidden.py").write_text(
        "from mathx import double\n\ndef test_double():\n    assert double(4) == 8\n",
        encoding="utf-8",
    )
    (task / "setup.py").write_text(
        "def setup(workspace, task_dir):\n"
        "    (workspace / 'made_by_setup.txt').write_text('ok', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (task / "task.json").write_text(
        json.dumps(
            {
                "id": "t99-double",
                "title": "double",
                "prompt": "Fix double() in mathx.py so it doubles its input.",
                "difficulty": "easy",
                "needs_execution": False,
                "why": "trivial",
            }
        ),
        encoding="utf-8",
    )
    return tmp_path / "tasks"


def test_dry_run_oracle_passes_and_untouched_fails(tasks_dir: Path, tmp_path: Path) -> None:
    code = run_bench.main(
        ["--dry-run", "--tasks-dir", str(tasks_dir), "--out", str(tmp_path / "o")]
    )
    assert code == 0
    records = json.loads((tmp_path / "o" / "dry_run.json").read_text())["records"]
    assert {(r["system"], r["passed"]) for r in records} == {("oracle", True), ("untouched", False)}


def test_setup_runs_and_hidden_check_is_not_visible_to_the_system(tasks_dir: Path) -> None:
    task = run_bench.load_tasks(tasks_dir)[0]
    seen: dict[str, str] = {}

    class Spy(FakeClient):
        def _create(self, **params):
            seen["prompt"] = params["messages"][0]["content"]
            return super()._create(**params)

    files = json.dumps(
        {"files": [{"path": "mathx.py", "content": "def double(x):\n    return 2 * x\n"}]}
    )
    record = run_bench.run_job(Spy(reply(text(files))), task, "single-shot", "claude-haiku-5-5")
    assert record["passed"] is True and record["llm_calls"] == 1
    assert "made_by_setup.txt" in seen["prompt"]
    assert "test_hidden" not in seen["prompt"] and "_hidden_check" not in seen["prompt"]


def test_agent_job_is_scored_by_the_hidden_check(tasks_dir: Path) -> None:
    task = run_bench.load_tasks(tasks_dir)[0]
    client = FakeClient(
        reply(
            tool_use(
                "w", "write_file", path="mathx.py", content="def double(x):\n    return 2 * x\n"
            ),
            stop="tool_use",
        ),
        reply(text("fixed")),
    )
    record = run_bench.run_job(client, task, "agent", "claude-haiku-5-5")
    assert record["passed"] is True and record["tool_calls"] == 1 and record["llm_calls"] == 2


def test_wrong_fix_fails_and_crashes_are_recorded(tasks_dir: Path) -> None:
    task = run_bench.load_tasks(tasks_dir)[0]
    wrong = json.dumps(
        {"files": [{"path": "mathx.py", "content": "def double(x):\n    return x + 1\n"}]}
    )
    assert (
        run_bench.run_job(FakeClient(reply(text(wrong))), task, "single-shot", "m")["passed"]
        is False
    )
    crashed = run_bench.run_job(FakeClient(reply(text("not json"))), task, "single-shot", "m")
    assert crashed["passed"] is False and "JSONDecodeError" in crashed["error"]


def test_single_shot_cannot_escape_the_workspace(tasks_dir: Path, tmp_path: Path) -> None:
    task = run_bench.load_tasks(tasks_dir)[0]
    evil = json.dumps({"files": [{"path": "../../escaped.txt", "content": "x"}]})
    record = run_bench.run_job(FakeClient(reply(text(evil))), task, "single-shot", "m")
    assert "outside the workspace" in record["error"]
    assert not (tmp_path / "escaped.txt").exists()


def test_summary_and_markdown(tasks_dir: Path) -> None:
    recs = [
        {"task": "a", "system": "agent", "model": "m", "passed": True, "needs_execution": True,
         "llm_calls": 4, "tool_calls": 3, "cost_usd": 0.01, "latency_s": 5.0},
        {"task": "b", "system": "agent", "model": "m", "passed": False, "needs_execution": False,
         "llm_calls": 2, "tool_calls": 1, "cost_usd": 0.03, "latency_s": 7.0},
    ]  # fmt: skip
    row = run_bench.summarize(recs)[0]
    assert (row["passed"], row["passed_exec"], row["n_exec"], row["passed_plain"]) == (1, 1, 1, 0)
    assert row["cost_per_task"] == pytest.approx(0.02) and row["p50_latency_s"] == 6.0
    md = run_bench.render_markdown([row], recs)
    assert "| agent | m | 1/2 | 1/1 | 0/1 |" in md and "| a | pass |" in md


def test_sandbox_env_puts_venv_first_and_blocks_downloads(monkeypatch) -> None:
    monkeypatch.setenv("PATH", "C:/elsewhere")
    run_bench.sandbox_env()
    import os
    import sys

    assert os.environ["PATH"].startswith(str(Path(sys.executable).parent))
    assert os.environ["PIP_NO_INDEX"] == "1"
