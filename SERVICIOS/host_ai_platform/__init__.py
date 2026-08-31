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
from .economy import ECONOMY_DOMAIN, EconomyDomain, EconomyPort, HostAIEconomyPort, register_economy_domain
from .reservations import RESERVATIONS_DOMAIN, HostAIReservationsPort, ReservationsDomain, ReservationsPort, register_reservations_domain
from .runtime_bridge import DOMAIN_NAMES, GeneralAgentPlatformRuntime

__all__ = [
    "ActionContextError", "ActionContextStore", "AgentAction",
    "AuthorizedExecutionContext", "DuplicateToolError", "OperationClass",
    "PlatformPolicy", "SessionContext", "ToolDefinition", "ToolExecutor",
    "ToolRegistry", "ToolResult", "UIAction", "UnknownToolError",
    "ECONOMY_DOMAIN", "EconomyDomain", "EconomyPort", "HostAIEconomyPort", "register_economy_domain",
    "RESERVATIONS_DOMAIN", "HostAIReservationsPort", "ReservationsDomain", "ReservationsPort", "register_reservations_domain",
    "DOMAIN_NAMES", "GeneralAgentPlatformRuntime",
]
