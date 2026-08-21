"""Neutral, additive contracts for the future General Agent runtime."""

from .action_context import ActionContextError, ActionContextStore
from .contracts import (
    AgentAction,
    AuthorizedExecutionContext,
    OperationClass,
    ToolDefinition,
    ToolResult,
    UIAction,
)
from .policy import PlatformPolicy
from .session_context import SessionContext
from .tool_executor import ToolExecutor
from .tool_registry import DuplicateToolError, ToolRegistry, UnknownToolError

__all__ = [
    "ActionContextError", "ActionContextStore", "AgentAction",
    "AuthorizedExecutionContext", "DuplicateToolError", "OperationClass",
    "PlatformPolicy", "SessionContext", "ToolDefinition", "ToolExecutor",
    "ToolRegistry", "ToolResult", "UIAction", "UnknownToolError",
]
