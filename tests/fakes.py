"""A scripted stand-in for the Anthropic client, so tests never call the API."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any


def text(t: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=t)


def tool_use(id_: str, name: str, **input_: Any) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=input_)


def reply(*blocks: SimpleNamespace, stop: str = "end_turn", tokens: int = 100) -> SimpleNamespace:
    usage = SimpleNamespace(
        input_tokens=tokens,
        output_tokens=10,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=0,
    )
    return SimpleNamespace(content=list(blocks), stop_reason=stop, usage=usage)


class FakeClient:
    """Returns the scripted replies in order and records every request."""

    def __init__(self, *replies: SimpleNamespace) -> None:
        self.replies = list(replies)
        self.requests: list[dict[str, Any]] = []
        self.messages = SimpleNamespace(create=self._create)
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **params: Any) -> SimpleNamespace:
        self.requests.append({**params, "messages": list(params["messages"])})
        return self.replies.pop(0)
