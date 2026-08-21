from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionContext:
    session_id: str
    active_entity: dict[str, Any] = field(default_factory=dict)
    _domain_state: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("session_id_required")

    @property
    def domain_state(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self._domain_state)

    def get_domain_state(self, name: str) -> dict[str, Any]:
        return deepcopy(self._domain_state.get(self._name(name), {}))

    def set_domain_state(self, name: str, value: dict[str, Any]) -> None:
        if not isinstance(value, dict):
            raise TypeError("domain_state_must_be_mapping")
        self._domain_state[self._name(name)] = deepcopy(value)

    def clear_domain_state(self, name: str) -> None:
        self._domain_state.pop(self._name(name), None)

    @staticmethod
    def _name(name: str) -> str:
        value = str(name or "").strip()
        if not value:
            raise ValueError("domain_name_required")
        return value
