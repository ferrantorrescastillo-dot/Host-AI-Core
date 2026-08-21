from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class OperationClass(str, Enum):
    READ = "READ"
    PURE_CALC = "PURE_CALC"
    PREVIEW = "PREVIEW"
    CONFIRM = "CONFIRM"
    UI_ACTION = "UI_ACTION"


def _frozen_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True)
class ToolDefinition:
    tool_id: str
    description: str
    operation_class: OperationClass
    input_schema: Mapping[str, Any] = field(default_factory=dict)
    required_scopes: frozenset[str] = field(default_factory=frozenset)
    grounding_requirement: str = "NONE"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tool_id.strip():
            raise ValueError("tool_id_required")
        object.__setattr__(self, "input_schema", _frozen_mapping(self.input_schema))
        object.__setattr__(self, "required_scopes", frozenset(self.required_scopes))
        object.__setattr__(self, "metadata", _frozen_mapping(self.metadata))

    def capability(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "description": self.description,
            "operation_class": self.operation_class.value,
            "input_schema": dict(self.input_schema),
            "required_scopes": sorted(self.required_scopes),
            "grounding_requirement": self.grounding_requirement,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class AuthorizedExecutionContext:
    request_id: str
    user_id: str
    tenant_id: str
    roles: frozenset[str] = field(default_factory=frozenset)
    scopes: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(self, "roles", frozenset(self.roles))
        object.__setattr__(self, "scopes", frozenset(self.scopes))

    def validate(self) -> tuple[bool, str]:
        if not self.request_id.strip():
            return False, "request_id_required"
        if not self.user_id.strip():
            return False, "user_id_required"
        if not self.tenant_id.strip():
            return False, "tenant_id_required"
        return True, ""


@dataclass
class ToolResult:
    status: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    context_updates: dict[str, Any] = field(default_factory=dict)
    error_code: str = ""
    tool_id: str = ""


@dataclass(frozen=True)
class UIAction:
    target: str
    view: str
    entity_id: str = ""
    label: str = ""
    type: str = "OPEN_VIEW"

    def to_public_dict(self) -> dict[str, str]:
        return {
            "type": self.type, "target": self.target, "id": self.entity_id,
            "view": self.view, "label": self.label,
        }


@dataclass(frozen=True)
class AgentAction:
    action_id: str
    label: str
    action_context_id: str = ""
    ui_action: UIAction | None = None

    def to_public_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"action_id": self.action_id, "label": self.label}
        if self.action_context_id:
            result["action_context_id"] = self.action_context_id
        if self.ui_action is not None:
            result["ui_action"] = self.ui_action.to_public_dict()
        return result
