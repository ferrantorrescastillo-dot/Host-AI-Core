from __future__ import annotations

from typing import Any


API_VERSION = "1.0"


def build_error_payload(*, request_id: str, status_code: int, code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "version": API_VERSION,
        "api_version": API_VERSION,
        "request_id": str(request_id or ""),
        "modo_seguro": True,
        "datos_reales_modificados": False,
        "error": {
            "status": int(status_code),
            "code": str(code or "api_error"),
            "message": str(message or "No se pudo procesar la solicitud."),
        },
    }


def normalize_success_payload(*, request_id: str, status_code: int, payload: dict[str, Any] | None) -> dict[str, Any]:
    data = dict(payload or {})
    if "ok" not in data:
        data["ok"] = status_code < 400
    if "version" not in data:
        data["version"] = API_VERSION
    if "modo_seguro" not in data:
        data["modo_seguro"] = True
    if "datos_reales_modificados" not in data:
        data["datos_reales_modificados"] = False
    data["api_version"] = API_VERSION
    data["request_id"] = str(request_id or "")
    return data
