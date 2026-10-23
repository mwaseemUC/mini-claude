import os
from pathlib import Path

import pytest

from mini_claude.tools import TOOL_SCHEMAS, Toolbox, cap


def yes(*_: str) -> bool:
    return True


def no(*_: str) -> bool:
    return False


@pytest.fixture
def ws(tmp_path: Path) -> Path:
    (tmp_path / "app.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "util.py").write_text("TODO = 1\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("TODO secret\n", encoding="utf-8")
    return tmp_path


def test_schemas_cover_every_handler() -> None:
    names = {s["name"] for s in TOOL_SCHEMAS}
    assert names == {"read_file", "write_file", "list_dir", "grep", "run_command"}
    for name in names:
        assert hasattr(Toolbox, f"_{name}")


def test_read_file_numbers_lines(ws: Path) -> None:
    text, err = Toolbox(ws, yes).run("read_file", {"path": "app.py"})
    assert not err
    assert "   2 |     return a - b" in text


# Backslash is a path separator only on Windows; on Linux "..\\..\\x" is a plain filename.
ESCAPES = ["../outside.txt", "/etc/passwd", "pkg/../../x"] + (
    ["..\\..\\x"] if os.name == "nt" else []
)


@pytest.mark.parametrize("path", ESCAPES)
def test_paths_outside_workspace_are_refused(ws: Path, path: str) -> None:
    for tool, args in [
        ("read_file", {"path": path}),
        ("write_file", {"path": path, "content": "x"}),
    ]:
        text, err = Toolbox(ws, yes).run(tool, args)
        assert err, f"{tool}({path!r}) was allowed: {text}"
        assert "outside the workspace" in text


def test_write_file_shows_diff_and_writes_when_approved(ws: Path) -> None:
    seen: list[tuple[str, str]] = []

    def approve(title: str, preview: str) -> bool:
        seen.append((title, preview))
        return True

    text, err = Toolbox(ws, approve).run(
        "write_file", {"path": "app.py", "content": "def add(a, b):\n    return a + b\n"}
    )
    assert not err and "wrote app.py" in text
    assert "-    return a - b" in seen[0][1] and "+    return a + b" in seen[0][1]
    assert "a + b" in (ws / "app.py").read_text(encoding="utf-8")


def test_write_file_declined_leaves_file_untouched(ws: Path) -> None:
    text, err = Toolbox(ws, no).run("write_file", {"path": "app.py", "content": "boom\n"})
    assert err and "declined" in text
    assert "a - b" in (ws / "app.py").read_text(encoding="utf-8")


def test_write_file_creates_parent_dirs_and_skips_noop(ws: Path) -> None:
    box = Toolbox(ws, yes)
    assert not box.run("write_file", {"path": "new/dir/f.txt", "content": "hi\n"})[1]
    assert (ws / "new/dir/f.txt").read_text(encoding="utf-8") == "hi\n"
    assert box.run("write_file", {"path": "new/dir/f.txt", "content": "hi\n"})[0].startswith(
        "no changes"
    )


def test_list_dir_skips_git_and_marks_dirs(ws: Path) -> None:
    text, _ = Toolbox(ws, yes).run("list_dir", {})
    assert text.splitlines() == ["pkg/", "app.py"]


def test_grep_finds_matches_but_not_in_skipped_dirs(ws: Path) -> None:
    text, err = Toolbox(ws, yes).run("grep", {"pattern": "TODO"})
    assert not err
    assert text == "pkg/util.py:1: TODO = 1"


def test_grep_bad_regex_is_an_error(ws: Path) -> None:
    text, err = Toolbox(ws, yes).run("grep", {"pattern": "("})
    assert err and "bad regex" in text


def test_run_command_needs_approval(ws: Path) -> None:
    text, err = Toolbox(ws, no).run("run_command", {"command": "echo hi"})
    assert err and "declined" in text


def test_run_command_returns_exit_code_and_output(ws: Path) -> None:
    text, err = Toolbox(ws, yes).run("run_command", {"command": 'python -c "print(42)"'})
    assert not err
    assert text.startswith("exit code 0") and "42" in text


def test_run_command_timeout(ws: Path) -> None:
    box = Toolbox(ws, yes, command_timeout=0.5)
    text, err = box.run("run_command", {"command": 'python -c "import time; time.sleep(5)"'})
    assert err and "timed out" in text


def test_unknown_tool_and_bad_args(ws: Path) -> None:
    box = Toolbox(ws, yes)
    assert box.run("delete_everything", {}) == ("unknown tool: delete_everything", True)
    text, err = box.run("read_file", {"nope": 1})
    assert err and "bad arguments" in text


def test_cap_truncates_long_output() -> None:
    out = cap("x" * 50, limit=10)
    assert out.startswith("x" * 10) and "truncated 40 characters" in out
