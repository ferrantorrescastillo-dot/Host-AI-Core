from __future__ import annotations

from typing import Any

from .contracts import AuthorizedExecutionContext, ToolResult
from .policy import PlatformPolicy
from .tool_registry import ToolRegistry, UnknownToolError


class ToolExecutor:
    def __init__(self, registry: ToolRegistry, policy: PlatformPolicy | None = None) -> None:
        self.registry = registry
        self.policy = policy or PlatformPolicy()

    def execute(
        self, tool_id: str, params: dict[str, Any] | None,
        execution_context: AuthorizedExecutionContext,
    ) -> ToolResult:
        try:
            registered = self.registry.get(tool_id)
        except UnknownToolError:
            return ToolResult("ERROR", "Tool not registered.", error_code="unknown_tool", tool_id=str(tool_id or ""))
        allowed, reason = self.policy.authorize(registered.definition, execution_context)
        if not allowed:
            return ToolResult("ERROR", "Tool execution is not authorized.", error_code=reason, tool_id=registered.definition.tool_id)
        try:
            result = registered.handler(dict(params or {}), execution_context)
        except Exception:
            return ToolResult("ERROR", "Tool execution failed safely.", error_code="handler_error", tool_id=registered.definition.tool_id)
        if not isinstance(result, ToolResult):
            return ToolResult("ERROR", "Invalid tool result.", error_code="invalid_tool_result", tool_id=registered.definition.tool_id)
        result.tool_id = registered.definition.tool_id
        return result
