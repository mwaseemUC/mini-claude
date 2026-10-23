"""The five tools the model can ask for, and the checks around them.

The model never touches the machine. It returns a tool name plus JSON input; `Toolbox.run`
decides whether to do it, does it inside the workspace, and returns text for the model.
"""

from __future__ import annotations

import difflib
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

OUTPUT_CAP = 20_000  # max characters of any tool result sent back to the model
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", ".ruff_cache"}

# approve(title, preview) -> True to go ahead. The CLI asks the user; --yes always says True.
Approver = Callable[[str, str], bool]


class ToolError(Exception):
    """A refused or failed tool call. Its message is sent back to the model as an error result."""


TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read a text file in the workspace. Returns numbered lines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to the workspace"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file with the full new content. "
        "The user sees a diff and "
        "must approve it. Always send the complete file, not a fragment.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_dir",
        "description": "List files and folders (folders end with /). Skips .git, venvs and caches.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "default": "."}},
        },
    },
    {
        "name": "grep",
        "description": "Search file contents with a Python regex. Returns path:line: text matches.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "default": "."},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "run_command",
        "description": "Run a shell command in the workspace (e.g. tests). "
        "The user must approve it. "
        "Returns the exit code and output.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
]


def cap(text: str, limit: int = OUTPUT_CAP) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated {len(text) - limit} characters]"


class Toolbox:
    def __init__(self, root: Path, approve: Approver, command_timeout: float = 60.0) -> None:
        self.root = root.resolve()
        self.approve = approve
        self.command_timeout = command_timeout

    def run(self, name: str, args: dict) -> tuple[str, bool]:
        """Execute one tool call. Returns (text for the model, is_error)."""
        handler = getattr(self, f"_{name}", None)
        if name not in {s["name"] for s in TOOL_SCHEMAS} or handler is None:
            return f"unknown tool: {name}", True
        try:
            return cap(handler(**args)), False
        except ToolError as exc:
            return str(exc), True
        except TypeError as exc:
            return f"bad arguments for {name}: {exc}", True

    def resolve(self, path: str) -> Path:
        """Map a model-supplied path to a real path, refusing anything outside the workspace."""
        target = (self.root / path).resolve()
        if not target.is_relative_to(self.root):
            raise ToolError(f"refused: {path!r} is outside the workspace")
        return target

    def _read_file(self, path: str) -> str:
        target = self.resolve(path)
        if not target.is_file():
            raise ToolError(f"not a file: {path}")
        try:
            lines = target.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise ToolError(f"not a UTF-8 text file: {path}") from exc
        return "\n".join(f"{i:>4} | {line}" for i, line in enumerate(lines, 1)) or "(empty file)"

    def _write_file(self, path: str, content: str) -> str:
        target = self.resolve(path)
        old = target.read_text(encoding="utf-8") if target.is_file() else ""
        if old == content:
            return f"no changes to {path}"
        diff = "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
        )
        if not self.approve(f"write {path}", diff):
            raise ToolError(f"user declined the write to {path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"wrote {path} ({len(content)} chars)"

    def _list_dir(self, path: str = ".") -> str:
        target = self.resolve(path)
        if not target.is_dir():
            raise ToolError(f"not a directory: {path}")
        entries = sorted(
            (p for p in target.iterdir() if p.name not in SKIP_DIRS),
            key=lambda p: (p.is_file(), p.name.lower()),
        )
        return "\n".join(p.name + ("/" if p.is_dir() else "") for p in entries) or "(empty)"

    def _grep(self, pattern: str, path: str = ".") -> str:
        try:
            regex = re.compile(pattern)
        except re.error as exc:
            raise ToolError(f"bad regex: {exc}") from exc
        base = self.resolve(path)
        files = [base] if base.is_file() else sorted(base.rglob("*"))
        hits: list[str] = []
        for file in files:
            if not file.is_file() or SKIP_DIRS & set(file.relative_to(self.root).parts):
                continue
            try:
                lines = file.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            rel = file.relative_to(self.root).as_posix()
            hits += [f"{rel}:{n}: {line}" for n, line in enumerate(lines, 1) if regex.search(line)]
            if len(hits) >= 200:
                break
        return "\n".join(hits[:200]) or "no matches"

    def _run_command(self, command: str) -> str:
        if not self.approve("run command", command):
            raise ToolError("user declined to run the command")
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=self.root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.command_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise ToolError(f"command timed out after {self.command_timeout:g}s") from exc
        return (
            f"exit code {proc.returncode}\n"
            f"--- stdout ---\n{proc.stdout}\n"
            f"--- stderr ---\n{proc.stderr}"
        )
