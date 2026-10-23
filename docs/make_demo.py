"""Record a real mini-claude session building a small app, and save it as docs/demo.svg.

Runs in a throwaway folder with the benchmark's sandbox settings (this venv's Python first on PATH,
pip downloads blocked), auto-approving each step but showing every diff and command it approves.
The finished app is copied to examples/todo-app/ so readers can check the result.

    python docs/make_demo.py [--model claude-sonnet-5-5]
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from rich.console import Console
from rich.terminal_theme import MONOKAI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from bench.run_bench import sandbox_env  # noqa: E402
from mini_claude.cli import main as cli_main  # noqa: E402

REQUEST = (
    "Build a small command-line todo app in todo.py: `add <text>`, `list`, `done <id>` and "
    "`remove <id>`, stored in todos.json next to the script. Use only the standard library. "
    "Write pytest tests in test_todo.py that use a temporary file, then run them and fix any "
    "failures."
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="claude-sonnet-5-5")
    args = p.parse_args()
    sandbox_env()
    console = Console(record=True, width=110, force_terminal=True)
    with tempfile.TemporaryDirectory(prefix="mc-demo-") as tmp:
        console.print(f"[bold]$ mini-claude --model {args.model} --yes[/]")
        console.print(f"[bold green]> [/]{REQUEST}")
        cli_main([REQUEST, "--dir", tmp, "--model", args.model, "--yes"], console=console)
        out = ROOT / "examples" / "todo-app"
        shutil.rmtree(out, ignore_errors=True)
        shutil.copytree(
            tmp, out, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "todos.json")
        )
    (ROOT / "docs").mkdir(exist_ok=True)
    console.save_svg(str(ROOT / "docs" / "demo.svg"), title="mini-claude", theme=MONOKAI)
    print(f"saved docs/demo.svg and {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
