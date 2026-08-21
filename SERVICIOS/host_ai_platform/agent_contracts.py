from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolCall:
    tool_id: str
    arguments: dict[str, Any] = field(default_factory=dict)
    call_id: str = ""


@dataclass(frozen=True)
class ProviderRequest:
    messages: tuple[dict[str, Any], ...]
    capabilities: tuple[dict[str, Any], ...]
    remaining_tool_budget: int


@dataclass(frozen=True)
class ProviderResponse:
    final_text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()


class AgentProvider(Protocol):
    def execute(self, request: ProviderRequest) -> ProviderResponse: ...
