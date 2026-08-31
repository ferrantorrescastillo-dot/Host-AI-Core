from __future__ import annotations

from API.contracts.http_models import ApiRequest, ApiResponse, validate_chat_payload
from API.facade.core_public_facade import CorePublicFacade


def handle(request: ApiRequest, facade: CorePublicFacade) -> ApiResponse:
    body = dict(request.body or {})
    valid, reason = validate_chat_payload(body)
    if not valid:
        status = 413 if reason in {"mensaje_too_large", "contexto_too_large", "session_id_too_large"} else 400
        return ApiResponse(
            status_code=status,
            payload={
                "ok": False,
                "error": {
                    "code": "invalid_chat_request",
                    "reason": reason,
                },
                "datos_reales_modificados": False,
            },
        )
    context = dict(body.get("contexto") or {})
    context["_host_ai_request_id"] = str(request.request_id or "")
    body["contexto"] = context
    return ApiResponse(status_code=200, payload=facade.chat(body))
