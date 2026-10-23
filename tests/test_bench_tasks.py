"""Validate benchmark fixtures: schema, and hidden tests fail before / pass after the oracle fix."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TASKS_DIR = Path(__file__).resolve().parent.parent / "bench" / "tasks"
TASK_DIRS = sorted(p for p in TASKS_DIR.iterdir() if p.is_dir() and (p / "task.json").exists())
EXECUTION_TASKS = {"t07", "t08", "t09", "t10"}


def load_task(task_dir: Path) -> dict:
    return json.loads((task_dir / "task.json").read_text(encoding="utf-8"))


def prepare(task_dir: Path, dest: Path) -> Path:
    shutil.copytree(task_dir / "workspace", dest)
    setup_file = task_dir / "setup.py"
    if setup_file.exists():
        spec = importlib.util.spec_from_file_location(f"_setup_{task_dir.name}", setup_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.setup(dest, task_dir)
    return dest


def run_hidden(task_dir: Path, workspace: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(workspace), "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            str(task_dir / "hidden"),
            "-p",
            "no:cacheprovider",
            f"--rootdir={workspace}",
        ],
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_ten_tasks_with_unique_ids():
    assert len(TASK_DIRS) == 10
    ids = [load_task(d)["id"] for d in TASK_DIRS]
    assert len(set(ids)) == 10
    assert [d.name for d in TASK_DIRS] == ids
    assert [i[:3] for i in ids] == [f"t{n:02d}" for n in range(1, 11)]


@pytest.mark.parametrize("task_dir", TASK_DIRS, ids=lambda d: d.name)
def test_task_schema(task_dir):
    t = load_task(task_dir)
    assert set(t) == {"id", "title", "prompt", "difficulty", "needs_execution", "why"}
    assert t["difficulty"] in {"easy", "medium", "hard"}
    assert isinstance(t["needs_execution"], bool)
    assert t["needs_execution"] == (task_dir.name[:3] in EXECUTION_TASKS)
    assert all(isinstance(t[k], str) and t[k].strip() for k in ("title", "prompt", "why"))
    assert "hidden" not in t["prompt"].lower()
    assert (task_dir / "hidden" / "test_hidden.py").is_file()
    assert (task_dir / "workspace").is_dir()
    assert any((task_dir / "solution").rglob("*"))
    for f in (task_dir / "workspace").rglob("*.py"):
        assert len(f.read_text(encoding="utf-8").splitlines()) < 150, f
    assert not (task_dir / "workspace" / "hidden").exists()
    assert not (task_dir / "workspace" / "private").exists()


@pytest.mark.parametrize("task_dir", TASK_DIRS, ids=lambda d: d.name)
def test_hidden_fails_on_start_and_passes_with_solution(task_dir, tmp_path):
    start = prepare(task_dir, tmp_path / "start")
    before = run_hidden(task_dir, start)
    assert before.returncode != 0, "hidden tests pass on the unsolved workspace:\n" + before.stdout

    solved = prepare(task_dir, tmp_path / "solved")
    shutil.copytree(task_dir / "solution", solved, dirs_exist_ok=True)
    after = run_hidden(task_dir, solved)
    assert after.returncode == 0, after.stdout + after.stderr


def test_setup_is_deterministic(tmp_path):
    for task_dir in TASK_DIRS:
        if not (task_dir / "setup.py").exists():
            continue
        a = prepare(task_dir, tmp_path / f"{task_dir.name}-a")
        b = prepare(task_dir, tmp_path / f"{task_dir.name}-b")
        files_a = {p.relative_to(a): p.read_bytes() for p in a.rglob("*") if p.is_file()}
        files_b = {p.relative_to(b): p.read_bytes() for p in b.rglob("*") if p.is_file()}
        assert files_a == files_b, task_dir.name
