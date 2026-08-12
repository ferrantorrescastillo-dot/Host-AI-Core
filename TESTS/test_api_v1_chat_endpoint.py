from __future__ import annotations

import json
from pathlib import Path

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest


def test_post_api_v1_chat_devuelve_http_200_y_json_valido(monkeypatch, tmp_path: Path) -> None:
    from API.facade.core_public_api02 import CorePublicApi02Facade

    class FakeChatService:
        def enviar(self, texto: str, contexto=None):
            return {
                "ok": True,
                "tipo_mensaje": "RESULTADO",
                "mensaje": f"eco: {texto}",
                "rol": "host_ai",
                "timestamp": "2026-07-29T10:00:00",
                "datos": {"contexto": dict(contexto or {})},
            }

        def estado_sesion(self):
            return {"contexto_activo": "HOME"}

    monkeypatch.setattr(CorePublicApi02Facade, "_build_chat_service", lambda self: FakeChatService())

    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(
        ApiRequest(
            method="POST",
            path="/api/v1/chat",
            body={"mensaje": "hola host", "contexto": {"evento_id": "EV-1"}},
        )
    )

    assert response.status_code == 200
    payload = response.payload
    assert payload.get("ok") is True
    assert payload.get("version") == "1.0"
    assert payload.get("modo_seguro") is True
    assert payload.get("datos_reales_modificados") is False
    assert payload.get("respuesta") == "eco: hola host"
    assert isinstance(payload.get("chat"), dict)
    assert isinstance(payload.get("contexto"), dict)
    json.dumps(payload)


def test_post_api_v1_chat_delega_en_servicio_conversacional_existente(monkeypatch, tmp_path: Path) -> None:
    from API.facade import core_public_api02 as module

    called = {"chat_ctor": 0, "enviar": 0}

    class FakeCore:
        def __init__(self, base_dir):
            self.base_dir = base_dir
            self.orquestador = object()

    class FakeHomeRead:
        def __init__(self, core):
            self.core = core

    class FakeChatService:
        def __init__(self, orquestador, home_read_service=None):
            called["chat_ctor"] += 1

        def enviar(self, texto: str, contexto=None):
            called["enviar"] += 1
            return {
                "ok": True,
                "tipo_mensaje": "RESULTADO",
                "mensaje": "respuesta certificada",
                "rol": "host_ai",
                "timestamp": "2026-07-29T10:00:00",
                "datos": {"raw": True},
            }

        def estado_sesion(self):
            return {"contexto_activo": "HOME"}

    monkeypatch.setattr(module, "HostAICore", FakeCore)
    monkeypatch.setattr(module, "HostAIHomeReadService", FakeHomeRead)
    monkeypatch.setattr(module, "ServicioChatHostAIShell", FakeChatService)

    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(
        ApiRequest(
            method="POST",
            path="/api/v1/chat",
            body={"mensaje": "consulta", "contexto": {"k": "v"}},
        )
    )

    assert response.status_code == 200
    assert called["chat_ctor"] == 1
    assert called["enviar"] == 1
    payload = response.payload
    assert payload.get("ok") is True
    assert payload.get("datos_reales_modificados") is False
    assert payload.get("chat", {}).get("mensaje") == "respuesta certificada"


def test_post_api_v1_chat_error_homogeneo_sin_traceback(monkeypatch, tmp_path: Path) -> None:
    from API.facade.core_public_api02 import CorePublicApi02Facade

    class FailingChatService:
        def enviar(self, texto: str, contexto=None):
            raise RuntimeError("Fallo interno C:\\ruta\\privada")

        def estado_sesion(self):
            return {}

    monkeypatch.setattr(CorePublicApi02Facade, "_build_chat_service", lambda self: FailingChatService())

    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(ApiRequest(method="POST", path="/api/v1/chat", body={"mensaje": "hola"}))

    assert response.status_code == 200
    payload = response.payload
    assert payload.get("ok") is False
    assert payload.get("version") == "1.0"
    assert payload.get("modo_seguro") is True
    assert payload.get("datos_reales_modificados") is False
    assert payload.get("error", {}).get("code") == "chat_unavailable"
    serialized = json.dumps(payload)
    assert "Traceback" not in serialized
    assert "C:\\\\" not in serialized


def test_post_api_v1_chat_devuelve_respuesta_openai_falsa_por_ruta_real(monkeypatch, tmp_path: Path) -> None:
    from SERVICIOS.host_ai_engine.openai_provider import OpenAIProvider

    class FakeResponses:
        def create(self, **kwargs):
            assert kwargs["model"] == "gpt-5-mini"
            assert kwargs["input"] == "Conversemos sobre organización de cocina"
            return type("FakeResponse", (), {"output_text": "Respuesta OpenAI controlada"})()

    class FakeClient:
        responses = FakeResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia-de-test")
    monkeypatch.setenv("HOST_AI_AI_PROVIDER", "OPENAI")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setattr(OpenAIProvider, "_sdk_available", staticmethod(lambda: True))
    monkeypatch.setattr(OpenAIProvider, "_get_client", lambda self: FakeClient())

    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(
        ApiRequest(
            method="POST",
            path="/api/v1/chat",
            body={"mensaje": "Conversemos sobre organización de cocina", "contexto": {}},
        )
    )

    assert response.status_code == 200
    assert response.payload["ok"] is True
    assert response.payload["respuesta"] == "Respuesta OpenAI controlada"
    assert response.payload["chat"]["datos"]["engine"]["proveedor"] == "OPENAI"
    assert response.payload["datos_reales_modificados"] is False
