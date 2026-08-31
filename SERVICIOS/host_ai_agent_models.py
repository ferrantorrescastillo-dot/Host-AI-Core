from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


FINAL_RESPONSE = "FINAL_RESPONSE"
TOOL_CALL = "TOOL_CALL"
GROUNDING_NONE = "NONE"
GROUNDING_INTERNAL_DATA_REQUIRED = "INTERNAL_DATA_REQUIRED"


def default_final_response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "grounding_requirement": {"type": "string", "enum": [GROUNDING_NONE, GROUNDING_INTERNAL_DATA_REQUIRED]},
            "answer": {"type": "string"},
        },
        "required": ["grounding_requirement", "answer"],
        "additionalProperties": False,
    }


@dataclass(frozen=True)
class ToolCall:
    tool_id: str
    arguments: dict[str, Any] = field(default_factory=dict)
    call_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentTurnRequest:
    messages: list[dict[str, Any]]
    allowed_tools: list[dict[str, Any]]
    request_id: str
    response_mode: str = "AUTO"
    limits: dict[str, Any] = field(default_factory=dict)
    conversation_context: dict[str, Any] = field(default_factory=dict)
    system_instructions: str = ""
    response_schema: dict[str, Any] = field(default_factory=default_final_response_schema)
    telemetry: Any = None
    agent_step: int = 0
    provider_timeout_seconds: float = 0.0
    agent_timeout_seconds: float = 0.0
    elapsed_ms: float = 0.0
    remaining_ms: float = 0.0
    tool_choice_mode: str = "auto"


@dataclass
class AgentTurnResult:
    kind: str
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    safe_error: str = ""
    grounding_requirement: str = GROUNDING_NONE


@dataclass
class AgentRunResult:
    ok: bool
    text: str = ""
    request_id: str = ""
    provider: str = ""
    model: str = ""
    steps: int = 0
    executed_tools: list[str] = field(default_factory=list)
    safe_error: str = ""
    datos_reales_modificados: bool = False
    grounding_requirement: str = GROUNDING_NONE
    grounding_retry: bool = False
    termination_reason: str = ""
    research_completion_reason: str = ""
    final_answer_source: str = ""
    ui_actions: list[dict[str, Any]] = field(default_factory=list)
    context_updates: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "FINAL_RESPONSE", "TOOL_CALL", "ToolCall", "AgentTurnRequest",
    "AgentTurnResult", "AgentRunResult", "GROUNDING_NONE",
    "GROUNDING_INTERNAL_DATA_REQUIRED",
    "default_final_response_schema",
]
