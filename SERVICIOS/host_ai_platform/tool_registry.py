from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .contracts import AuthorizedExecutionContext, ToolDefinition, ToolResult

ToolHandler = Callable[[dict[str, Any], AuthorizedExecutionContext], ToolResult]


class DuplicateToolError(ValueError):
    pass


class UnknownToolError(LookupError):
    pass


@dataclass(frozen=True)
class RegisteredTool:
    definition: ToolDefinition
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._items: dict[str, RegisteredTool] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        if definition.tool_id in self._items:
            raise DuplicateToolError("duplicate_tool_id")
        if not callable(handler):
            raise TypeError("tool_handler_must_be_callable")
        self._items[definition.tool_id] = RegisteredTool(definition, handler)

    def has(self, tool_id: str) -> bool:
        return str(tool_id or "") in self._items

    def get(self, tool_id: str) -> RegisteredTool:
        try:
            return self._items[str(tool_id or "")]
        except KeyError as exc:
            raise UnknownToolError("unknown_tool") from exc

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return tuple(item.definition for item in self._items.values())

    def capabilities(self) -> list[dict[str, Any]]:
        return [definition.capability() for definition in self.definitions()]
