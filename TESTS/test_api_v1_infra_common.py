from __future__ import annotations

import json
from pathlib import Path

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest


def test_get_api_v1_health_respuesta_estandar(tmp_path: Path) -> None:
    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(ApiRequest(method="GET", path="/api/v1/health"))

    assert response.status_code == 200
    payload = response.payload
    assert payload.get("ok") is True
    assert payload.get("api_version") == "1.0"
    assert isinstance(payload.get("request_id"), str)
    assert payload.get("request_id")
    json.dumps(payload)


def test_get_api_v1_version_respuesta_estandar(tmp_path: Path) -> None:
    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(ApiRequest(method="GET", path="/api/v1/version"))

    assert response.status_code == 200
    payload = response.payload
    assert payload.get("ok") is True
    assert payload.get("api_version") == "1.0"
    assert isinstance(payload.get("request_id"), str)
    assert payload.get("request_id")
    json.dumps(payload)


def test_request_id_es_unico_por_peticion(tmp_path: Path) -> None:
    api = HostAIPlatformAPI(base_dir=tmp_path)
    r1 = api.handle(ApiRequest(method="GET", path="/api/v1/health"))
    r2 = api.handle(ApiRequest(method="GET", path="/api/v1/health"))

    assert r1.payload.get("request_id")
    assert r2.payload.get("request_id")
    assert r1.payload.get("request_id") != r2.payload.get("request_id")


def test_compatibilidad_formato_executive_dashboard_chat(monkeypatch, tmp_path: Path) -> None:
    from API.facade.core_public_api02 import CorePublicApi02Facade

    class FakeChatService:
        def enviar(self, texto: str, contexto=None):
            return {
                "ok": True,
                "tipo_mensaje": "RESULTADO",
                "mensaje": "respuesta certificada",
                "rol": "host_ai",
                "timestamp": "2026-07-29T12:00:00",
                "datos": {"echo": texto, "contexto": dict(contexto or {})},
            }

        def estado_sesion(self):
            return {"contexto_activo": "HOME"}

    monkeypatch.setattr(CorePublicApi02Facade, "_build_chat_service", lambda self: FakeChatService())

    api = HostAIPlatformAPI(base_dir=tmp_path)

    res_exec = api.handle(ApiRequest(method="GET", path="/api/v1/executive"))
    res_dash = api.handle(ApiRequest(method="GET", path="/api/v1/dashboard"))
    res_chat = api.handle(ApiRequest(method="POST", path="/api/v1/chat", body={"mensaje": "hola", "contexto": {}}))

    for res in [res_exec, res_dash, res_chat]:
        assert res.status_code == 200
        payload = res.payload
        assert payload.get("api_version") == "1.0"
        assert isinstance(payload.get("request_id"), str)
        assert payload.get("request_id")
        assert payload.get("datos_reales_modificados") is False

    assert isinstance(res_exec.payload.get("executive"), dict)
    assert isinstance(res_dash.payload.get("dashboard"), dict)
    assert isinstance(res_chat.payload.get("chat"), dict)
