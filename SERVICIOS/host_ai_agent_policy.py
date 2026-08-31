from __future__ import annotations

import os
from typing import Any

from SERVICIOS.host_ai_tool_schemas import validate_arguments
from SERVICIOS.host_ai_authorized_execution_context import TOOL_READ_SCOPES, AuthorizedExecutionContext


class HostAIAgentPolicy:
    MAX_AGENT_STEPS = 6
    MAX_TOOL_CALLS = 4
    PRODUCTION_PLANNING_TOOL_CALLS = 9
    MAX_TOOL_CALLS_HARD = 10
    PRODUCTION_PLANNING_MAX_AGENT_STEPS = 10
    MAX_SAME_TOOL_CALLS = 2
    MAX_RESULT_ITEMS = 10
    MAX_CONTEXT_SIZE = 32_000
    TOTAL_TIMEOUT_SECONDS = 90.0
    TOOL_TIMEOUT_SECONDS = 5.0
    PROVIDER_TIMEOUT_SECONDS = 60.0
    MIN_PROVIDER_TIMEOUT_SECONDS = 5.0
    MAX_PROVIDER_TIMEOUT_SECONDS = 120.0
    MIN_TOTAL_TIMEOUT_SECONDS = 10.0
    MAX_TOTAL_TIMEOUT_SECONDS = 180.0
    MIN_AGENT_STEPS = 2
    MAX_AGENT_STEPS_ALLOWED = 12

    def tool_budget(
        self,
        workflow_type: str = "",
        routing_reason: str = "",
        multi_source_read: bool = False,
    ) -> int:
        requested = (
            self.PRODUCTION_PLANNING_TOOL_CALLS
            if (
                str(workflow_type or "") == "production_planning"
                or (
                    str(routing_reason or "") == "multi_factor_operational_analysis"
                    and multi_source_read
                )
            )
            else self.MAX_TOOL_CALLS
        )
        return min(int(requested), int(self.MAX_TOOL_CALLS_HARD))

    def agent_steps(
        self,
        workflow_type: str = "",
        routing_reason: str = "",
        multi_source_read: bool = False,
    ) -> int:
        if (
            str(workflow_type or "") == "production_planning"
            or (
                str(routing_reason or "") == "multi_factor_operational_analysis"
                and multi_source_read
            )
        ):
            return min(self.PRODUCTION_PLANNING_MAX_AGENT_STEPS, self.MAX_AGENT_STEPS_ALLOWED)
        return self.MAX_AGENT_STEPS

    def __init__(self) -> None:
        self.MAX_AGENT_STEPS = self._env_int(
            "HOST_AI_AGENT_MAX_ROUNDS", self.MAX_AGENT_STEPS,
            self.MIN_AGENT_STEPS, self.MAX_AGENT_STEPS_ALLOWED,
        )
        self.PROVIDER_TIMEOUT_SECONDS = self._env_seconds(
            "HOST_AI_AGENT_PROVIDER_TIMEOUT_SECONDS", self.PROVIDER_TIMEOUT_SECONDS,
            self.MIN_PROVIDER_TIMEOUT_SECONDS, self.MAX_PROVIDER_TIMEOUT_SECONDS,
        )
        self.TOTAL_TIMEOUT_SECONDS = self._env_seconds(
            "HOST_AI_AGENT_TOTAL_TIMEOUT_SECONDS", self.TOTAL_TIMEOUT_SECONDS,
            self.MIN_TOTAL_TIMEOUT_SECONDS, self.MAX_TOTAL_TIMEOUT_SECONDS,
        )

    @staticmethod
    def _env_seconds(name: str, default: float, minimum: float, maximum: float) -> float:
        raw = str(os.getenv(name) or "").strip()
        if not raw:
            return float(default)
        try:
            value = float(raw)
        except ValueError:
            return float(default)
        if value < minimum or value > maximum:
            return float(default)
        return value

    @staticmethod
    def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
        try:
            value = int(str(os.getenv(name) or "").strip())
        except ValueError:
            return int(default)
        return value if minimum <= value <= maximum else int(default)

    def authorize(self, tool_id: str, arguments: Any, catalog: list[dict[str, Any]]) -> tuple[bool, str]:
        contract = next((item for item in catalog if item.get("tool_id") == tool_id), None)
        if not contract:
            return False, "tool_not_allowed"
        expected_policy = "EXPLICIT_HUMAN" if contract.get("type") in {"PREVIEW", "CONFIRM"} else "NONE"
        if contract.get("type") not in {"READ", "ANALYSIS", "UI_ACTION", "PREVIEW", "CONFIRM"} or contract.get("confirmation_policy") != expected_policy or not contract.get("enabled"):
            return False, "tool_type_not_allowed"
        return validate_arguments(dict(contract.get("input_schema") or {}), arguments)

    def authorize_context(self, tool_id: str, context: AuthorizedExecutionContext | None) -> tuple[bool, str]:
        if context is None:
            return False, "missing_identity"
        valid, reason = context.validate()
        if not valid:
            return False, reason
        required_scope = TOOL_READ_SCOPES.get(str(tool_id or ""))
        if not required_scope:
            return False, "tool_not_allowed"
        if required_scope not in context.scopes:
            return False, "missing_scope"
        return True, ""


__all__ = ["HostAIAgentPolicy"]
