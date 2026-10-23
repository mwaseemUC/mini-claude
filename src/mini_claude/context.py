"""Keeping the conversation from growing without bound.

The agent re-sends the whole history on every call, so cost and latency grow with every tool result,
and old file dumps and test logs crowd out what matters. We bound each result before it is ever sent
(tools.OUTPUT_CAP) and let the API clear old tool results server-side once the prompt gets large.

Why not delete old results ourselves? Current models check that earlier turns come back unchanged
(they carry the model's thinking); trimming them client-side is a history edit that invalidates that
thinking, and on newer accounts it is rejected. Server-side clearing is applied after that check.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CONTEXT_BETA = "context-management-2025-06-27"
CONTEXT_WINDOW = 1_000_000  # Haiku 5.5, Sonnet 5.5 and Opus 5.5 all have a 1M-token window


@dataclass(frozen=True)
class ContextPolicy:
    trigger_tokens: int = 60_000  # start clearing once a request is this big
    keep_tool_uses: int = 6  # always keep the most recent tool calls and their results
    # Clearing breaks the prompt cache, so only clear when it saves at least this much.
    clear_at_least: int = 10_000

    def edits(self) -> dict[str, Any]:
        return {
            "edits": [
                {
                    "type": "clear_tool_uses_20250919",
                    "trigger": {"type": "input_tokens", "value": self.trigger_tokens},
                    "keep": {"type": "tool_uses", "value": self.keep_tool_uses},
                    "clear_at_least": {"type": "input_tokens", "value": self.clear_at_least},
                }
            ]
        }


def applied_edits(response: Any) -> list[dict[str, int]]:
    """What the API cleared on this call: [{"cleared_tool_uses": n, "cleared_input_tokens": n}]."""
    management = getattr(response, "context_management", None)
    edits = getattr(management, "applied_edits", None) or []
    return [
        {
            "cleared_tool_uses": getattr(e, "cleared_tool_uses", 0) or 0,
            "cleared_input_tokens": getattr(e, "cleared_input_tokens", 0) or 0,
        }
        for e in edits
    ]


def fullness(last_input_tokens: int) -> float:
    """Share of the context window the most recent request used (0.0 to 1.0)."""
    return last_input_tokens / CONTEXT_WINDOW
