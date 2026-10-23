"""The `mini-claude` command: a REPL around the agent loop, rendered with rich."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax

from mini_claude.agent import DEFAULT_MODEL, Agent
from mini_claude.context import fullness
from mini_claude.tools import Toolbox


class Terminal:
    """Turns agent events into terminal output and asks the user to approve risky actions."""

    def __init__(self, console: Console, auto_approve: bool = False) -> None:
        self.console = console
        self.auto_approve = auto_approve
        self.status = console.status("[dim]thinking...", spinner="dots")

    def approve(self, title: str, preview: str) -> bool:
        if title.startswith("write"):
            body: Any = Syntax(preview or "(no diff)", "diff", theme="ansi_dark")
        else:
            body = Syntax(preview, "bash", theme="ansi_dark")
        self.console.print(Panel(body, title=f"[bold yellow]{title}", expand=False))
        if self.auto_approve:
            self.console.print("[dim]auto-approved (--yes)")
            return True
        self.status.stop()
        try:
            return Confirm.ask("Allow?", console=self.console, default=False)
        finally:
            self.status.start()

    def on_event(self, kind: str, payload: dict[str, Any]) -> None:
        if kind == "text":
            self.console.print(Markdown(payload["text"]))
        elif kind == "tool_call":
            args = ", ".join(f"{k}={str(v)[:60]!r}" for k, v in payload["input"].items())
            self.console.print(f"[cyan]> {payload['name']}[/]([dim]{args}[/])")
        elif kind == "tool_result" and payload["error"]:
            self.console.print(f"[red]  ! {payload['output'][:200]}")
        elif kind == "context_cleared":
            n = payload["cleared_tool_uses"]
            self.console.print(f"[yellow]  context: {n} old tool results cleared")


def footer(agent: Agent) -> str:
    u = agent.usage
    return (
        f"{agent.model} | context {fullness(u.last_input_tokens):.1%} "
        f"({u.last_input_tokens:,} tokens) | {u.llm_calls} calls, {u.tool_calls} tools "
        f"| ${u.cost_usd:.4f} this session"
    )


def run_once(agent: Agent, term: Terminal, request: str) -> str:
    term.status.start()
    try:
        answer = agent.run(request)
    except KeyboardInterrupt:
        agent.close_interrupted_turn()
        answer = "[interrupted]"
    finally:
        term.status.stop()
    term.console.print(f"[dim]{footer(agent)}")
    return answer


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="mini-claude", description="A minimal coding agent.")
    p.add_argument("request", nargs="*", help="run one request and exit (omit for a REPL)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    p.add_argument("--dir", type=Path, default=Path.cwd(), help="workspace (default: current dir)")
    p.add_argument("--yes", action="store_true", help="approve every write and command (unsafe)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None, client: Any = None, console: Console | None = None) -> int:
    args = parse_args(argv)
    console = console or Console()
    if client is None:
        import anthropic

        load_dotenv(find_dotenv(usecwd=True))  # a .env in or above the workspace
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")  # or this repo's .env
        client = anthropic.Anthropic()
    term = Terminal(console, auto_approve=args.yes)
    agent = Agent(
        client=client,
        toolbox=Toolbox(args.dir, term.approve),
        model=args.model,
        effort=args.effort,
        on_event=term.on_event,
    )
    if args.request:
        run_once(agent, term, " ".join(args.request))
        return 0

    console.print(
        f"[bold]mini-claude[/] in {args.dir.resolve()}  [dim](exit with Ctrl+D or 'exit')"
    )
    while True:
        try:
            request = console.input("[bold green]> [/]").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if request in {"exit", "quit"}:
            break
        if request:
            run_once(agent, term, request)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
