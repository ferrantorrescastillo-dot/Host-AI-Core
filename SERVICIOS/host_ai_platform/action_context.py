from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets
from threading import RLock
from typing import Any, Callable


class ActionContextError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass
class _StoredAction:
    action_id: str
    session_id: str
    internal_payload: dict[str, Any]
    created_at: datetime
    expires_at: datetime
    fingerprint: str | None
    consumed: bool = False


class ActionContextStore:
    def __init__(self, now_provider: Callable[[], datetime] | None = None) -> None:
        self._now = now_provider or (lambda: datetime.now(timezone.utc))
        self._items: dict[str, _StoredAction] = {}
        self._lock = RLock()

    def create(self, action_id: str, session_id: str, internal_payload: dict[str, Any], ttl_seconds: int, fingerprint: str | None = None) -> dict[str, str]:
        if not str(action_id or "").strip() or not str(session_id or "").strip():
            raise ActionContextError("invalid_action_context")
        if ttl_seconds <= 0:
            raise ActionContextError("invalid_ttl")
        now = self._now()
        context_id = secrets.token_hex(16)
        with self._lock:
            self._items[context_id] = _StoredAction(str(action_id), str(session_id), deepcopy(internal_payload), now, now + timedelta(seconds=ttl_seconds), fingerprint)
        return {"action_id": str(action_id), "action_context_id": context_id}

    def resolve(self, context_id: str, action_id: str, session_id: str, fingerprint: str | None = None) -> dict[str, Any]:
        with self._lock:
            item = self._get(context_id)
            self._validate(item, action_id, session_id, fingerprint)
            return deepcopy(item.internal_payload)

    def consume(self, context_id: str, action_id: str, session_id: str, fingerprint: str | None = None) -> dict[str, Any]:
        with self._lock:
            item = self._get(context_id)
            self._validate(item, action_id, session_id, fingerprint)
            item.consumed = True
            return deepcopy(item.internal_payload)

    def _get(self, context_id: str) -> _StoredAction:
        item = self._items.get(str(context_id or ""))
        if item is None:
            raise ActionContextError("action_context_not_found")
        return item

    def _validate(self, item: _StoredAction, action_id: str, session_id: str, fingerprint: str | None) -> None:
        if item.consumed:
            raise ActionContextError("action_context_replayed")
        if self._now() >= item.expires_at:
            raise ActionContextError("action_context_expired")
        if item.action_id != str(action_id):
            raise ActionContextError("action_id_mismatch")
        if item.session_id != str(session_id):
            raise ActionContextError("session_mismatch")
        if item.fingerprint is not None and item.fingerprint != fingerprint:
            raise ActionContextError("stale_action_context")
