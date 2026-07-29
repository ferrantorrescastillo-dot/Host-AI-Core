from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ApiRequest:
    method: str
    path: str
    request_id: str = ""
    query: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] = field(default_factory=dict)


@dataclass
class ApiResponse:
    status_code: int
    payload: dict[str, Any]
