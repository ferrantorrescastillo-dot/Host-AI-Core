from __future__ import annotations

from API.contracts.http_models import ApiRequest
from API.endpoints import chat as chat_endpoint


class _FacadeStub:
    def chat(self, body):
        return {
            "ok": True,
            "respuesta": str(body.get("mensaje") or ""),
            "datos_reales_modificados": False,
        }


def _request(body):
    return ApiRequest(
        method="POST",
        path="/api/v1/chat",
        request_id="REQ-6B",
        body=body,
    )


def test_chat_input_normal_aceptado():
    response = chat_endpoint.handle(
        _request({"mensaje": "hola", "contexto": {"session_id": "session-1"}}),
        _FacadeStub(),
    )
    assert response.status_code == 200
    assert response.payload.get("ok") is True


def test_chat_input_excesivo_rechazado():
    response = chat_endpoint.handle(
        _request({"mensaje": "x" * 4001, "contexto": {}}),
        _FacadeStub(),
    )
    assert response.status_code == 413
    assert response.payload.get("error", {}).get("reason") == "mensaje_too_large"


def test_chat_estructura_invalida_rechazada():
    response = chat_endpoint.handle(
        _request({"mensaje": "hola", "contexto": ["no", "dict"]}),
        _FacadeStub(),
    )
    assert response.status_code == 400
    assert response.payload.get("error", {}).get("reason") == "invalid_contexto"


def test_chat_campos_extra_rechazados():
    response = chat_endpoint.handle(
        _request({"mensaje": "hola", "contexto": {}, "extra": 1}),
        _FacadeStub(),
    )
    assert response.status_code == 400
    assert response.payload.get("error", {}).get("reason") == "unknown_fields"


def test_chat_session_id_excesivo_rechazado():
    response = chat_endpoint.handle(
        _request({"mensaje": "hola", "contexto": {"session_id": "s" * 65}}),
        _FacadeStub(),
    )
    assert response.status_code == 413
    assert response.payload.get("error", {}).get("reason") == "session_id_too_large"
