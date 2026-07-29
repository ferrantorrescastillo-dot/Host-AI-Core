from __future__ import annotations

import json
from pathlib import Path

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest


REQUIRED_FIELDS = {
    "ok",
    "version",
    "api_version",
    "request_id",
    "modo_seguro",
    "datos_reales_modificados",
}


def _assert_common_contract(payload: dict) -> None:
    assert REQUIRED_FIELDS.issubset(set(payload.keys()))
    assert isinstance(payload.get("ok"), bool)
    assert isinstance(payload.get("version"), str)
    assert isinstance(payload.get("api_version"), str)
    assert isinstance(payload.get("request_id"), str)
    assert payload.get("request_id")
    assert isinstance(payload.get("modo_seguro"), bool)
    assert isinstance(payload.get("datos_reales_modificados"), bool)
    json.dumps(payload)


def test_contract_get_api_v1_health(tmp_path: Path) -> None:
    api = HostAIPlatformAPI(base_dir=tmp_path)
    r = api.handle(ApiRequest(method="GET", path="/api/v1/health"))
    assert r.status_code == 200
    _assert_common_contract(r.payload)
    assert isinstance(r.payload.get("health"), dict)


def test_contract_get_api_v1_version(tmp_path: Path) -> None:
    api = HostAIPlatformAPI(base_dir=tmp_path)
    r = api.handle(ApiRequest(method="GET", path="/api/v1/version"))
    assert r.status_code == 200
    _assert_common_contract(r.payload)
    assert isinstance(r.payload.get("version_info"), dict)


def test_contract_get_api_v1_executive(tmp_path: Path) -> None:
    api = HostAIPlatformAPI(base_dir=tmp_path)
    r = api.handle(ApiRequest(method="GET", path="/api/v1/executive"))
    assert r.status_code == 200
    _assert_common_contract(r.payload)
    assert isinstance(r.payload.get("executive"), dict)


def test_contract_get_api_v1_dashboard(tmp_path: Path) -> None:
    api = HostAIPlatformAPI(base_dir=tmp_path)
    r = api.handle(ApiRequest(method="GET", path="/api/v1/dashboard"))
    assert r.status_code == 200
    _assert_common_contract(r.payload)
    assert isinstance(r.payload.get("dashboard"), dict)


def test_contract_post_api_v1_chat(monkeypatch, tmp_path: Path) -> None:
    from API.facade.core_public_api02 import CorePublicApi02Facade

    class FakeChatService:
        def enviar(self, texto: str, contexto=None):
            return {
                "ok": True,
                "tipo_mensaje": "RESULTADO",
                "mensaje": f"eco: {texto}",
                "rol": "host_ai",
                "timestamp": "2026-07-29T13:00:00",
                "datos": {"contexto": dict(contexto or {})},
            }

        def estado_sesion(self):
            return {"contexto_activo": "HOME"}

    monkeypatch.setattr(CorePublicApi02Facade, "_build_chat_service", lambda self: FakeChatService())

    api = HostAIPlatformAPI(base_dir=tmp_path)
    r = api.handle(ApiRequest(method="POST", path="/api/v1/chat", body={"mensaje": "hola", "contexto": {}}))
    assert r.status_code == 200
    _assert_common_contract(r.payload)
    assert isinstance(r.payload.get("chat"), dict)


def test_contract_error_http_not_found(tmp_path: Path) -> None:
    api = HostAIPlatformAPI(base_dir=tmp_path)
    r = api.handle(ApiRequest(method="GET", path="/api/v1/no-existe"))
    assert r.status_code == 404
    _assert_common_contract(r.payload)
    error = dict(r.payload.get("error") or {})
    assert error.get("status") == 404
    assert error.get("code") == "not_found"
    assert isinstance(error.get("message"), str)
