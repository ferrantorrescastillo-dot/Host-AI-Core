from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re


CHAT_ALLOWED_KEYS = frozenset({"mensaje", "contexto", "session_id", "action_id", "action_context_id"})
CHAT_ACTION_IDS = frozenset({
    "APPLY_PENDING_RESERVATION", "DISCARD_PENDING_RESERVATION",
    "CONFIRM_RESERVATION", "EDIT_RESERVATION", "CANCEL_RESERVATION",
    "MARK_RESERVATION_NO_SHOW", "COMPLETE_RESERVATION", "OPEN_RESERVATION",
    "RESOLVE_MISSING_PRICE", "RESOLVE_MISSING_CONVERSION",
    "CHECK_ESCANDALLO_COST",
    "APPLY_PENDING_ARTICLE_CHANGE", "DISCARD_PENDING_ARTICLE_CHANGE",
    "PREVIEW_RECIPE_PROCEDURE", "CONFIRM_RECIPE_PROCEDURE",
    "PREVIEW_INGREDIENT_RELATION", "CONFIRM_INGREDIENT_RELATION",
})
CHAT_MAX_MESSAGE_CHARS = 4000
CHAT_MAX_CONTEXT_ITEMS = 32
CHAT_MAX_CONTEXT_VALUE_CHARS = 512
CHAT_MAX_SESSION_ID_CHARS = 64
CHAT_SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
CHAT_ACTION_CONTEXT_PATTERN = re.compile(r"[a-f0-9]{32}")


def validate_chat_payload(body: Any) -> tuple[bool, str]:
    if not isinstance(body, dict):
        return False, "invalid_body"

    extra = set(body.keys()) - set(CHAT_ALLOWED_KEYS)
    if extra:
        return False, "unknown_fields"

    mensaje = body.get("mensaje", "")
    if not isinstance(mensaje, str):
        return False, "invalid_mensaje"
    if len(mensaje) > CHAT_MAX_MESSAGE_CHARS:
        return False, "mensaje_too_large"
    action_id = body.get("action_id")
    if action_id is not None and (not isinstance(action_id, str) or action_id not in CHAT_ACTION_IDS):
        return False, "invalid_action_id"
    action_context_id = body.get("action_context_id")
    if action_context_id is not None and (not isinstance(action_context_id, str) or CHAT_ACTION_CONTEXT_PATTERN.fullmatch(action_context_id) is None):
        return False, "invalid_action_context_id"
    preview_actions = {
        "APPLY_PENDING_RESERVATION", "DISCARD_PENDING_RESERVATION",
        "APPLY_PENDING_ARTICLE_CHANGE", "DISCARD_PENDING_ARTICLE_CHANGE",
        "PREVIEW_RECIPE_PROCEDURE", "CONFIRM_RECIPE_PROCEDURE",
        "PREVIEW_INGREDIENT_RELATION", "CONFIRM_INGREDIENT_RELATION",
    }
    if action_id in preview_actions and action_context_id is not None:
        return False, "unexpected_action_context_id"
    if action_id in CHAT_ACTION_IDS - preview_actions and action_context_id is None:
        return False, "action_context_required"
    if not mensaje.strip() and action_id is None:
        return False, "invalid_mensaje"

    contexto = body.get("contexto", {})
    if contexto is None:
        contexto = {}
    if not isinstance(contexto, dict):
        return False, "invalid_contexto"
    if len(contexto) > CHAT_MAX_CONTEXT_ITEMS:
        return False, "contexto_too_large"

    for key, value in contexto.items():
        if not isinstance(key, str):
            return False, "invalid_contexto"
        if isinstance(value, str):
            if len(value) > CHAT_MAX_CONTEXT_VALUE_CHARS:
                return False, "contexto_too_large"
            continue
        if isinstance(value, (int, float, bool)) or value is None:
            continue
        return False, "invalid_contexto"

    for raw_session_id in (body.get("session_id"), contexto.get("session_id")):
        if raw_session_id is None:
            continue
        if not isinstance(raw_session_id, str):
            return False, "invalid_session_id"
        sid = raw_session_id.strip()
        if len(sid) > CHAT_MAX_SESSION_ID_CHARS:
            return False, "session_id_too_large"
        if sid and CHAT_SESSION_ID_PATTERN.fullmatch(sid) is None:
            return False, "invalid_session_id"

    return True, ""


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
