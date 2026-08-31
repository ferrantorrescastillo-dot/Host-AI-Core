from __future__ import annotations

from types import SimpleNamespace

from API.contracts.http_models import ApiRequest
from API.endpoints import chat as chat_endpoint
from API.facade.core_public_api02 import CorePublicApi02Facade
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_agent_models import AgentRunResult


def test_general_agent_ignora_override_de_active_entity_desde_contexto(monkeypatch) -> None:
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()))
    shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    shell._session.contexto_activo = "MENU"
    shell._session.menu_activo = {"id": "MENU-OK", "nombre": "Menu seguro", "tipo": "MENU"}

    captured: dict[str, object] = {}

    def fake_run(_message: str, conversation_context=None):
        captured.update(dict(conversation_context or {}))
        return AgentRunResult(True, "ok", "RID", "FAKE", "fake", 1, [])

    shell.general_agent = SimpleNamespace(engine=object(), run=fake_run)
    shell._try_general_agent(
        "hola",
        {
            "active_entity": {"id": "EVIL-ID", "tipo": "COMPRA"},
            "conversation_history": [{"role": "user", "content": "EVIL"}],
            "_host_ai_request_id": "REQ-1",
        },
    )

    assert captured["active_entity"] == {"id": "MENU-OK", "nombre": "Menu seguro", "tipo": "MENU"}
    assert isinstance(captured.get("conversation_history"), list)
    assert captured.get("user_context") == {}


def test_chat_sanea_error_interno_en_respuesta() -> None:
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()))
    shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    shell.general_agent = SimpleNamespace(
        engine=object(),
        run=lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("DB fail C:/secret/token-XYZ")),
    )

    result = shell.enviar("forzar error")

    assert result["ok"] is False
    assert "token-XYZ" not in str(result["mensaje"])
    assert "DB fail" not in str(result["mensaje"])
    assert result["datos"].get("safe_error_code") == "internal_error"
    assert result["datos"].get("datos_reales_modificados") is False


def test_http_chat_aisla_contexto_por_session_id(monkeypatch, tmp_path) -> None:
    created_services: list[object] = []

    class _FakeChatService:
        def __init__(self):
            self.menu_activo: dict[str, str] = {}

        def enviar(self, texto: str, contexto=None):
            if "abre" in str(texto).lower():
                self.menu_activo = {"id": "MENU-A", "nombre": "Menu A"}
                return {"ok": True, "mensaje": "abierto", "datos": {"datos_reales_modificados": False}}
            return {"ok": True, "mensaje": "seguimiento", "datos": {"datos_reales_modificados": False}}

        def estado_sesion(self):
            return {
                "contexto_activo": "MENU" if self.menu_activo else "HOME",
                "menu_activo": dict(self.menu_activo),
            }

    def build_chat_service(self):
        service = _FakeChatService()
        created_services.append(service)
        return service

    facade = CorePublicApi02Facade(base_dir=tmp_path)
    monkeypatch.setattr(CorePublicApi02Facade, "_build_chat_service", build_chat_service)

    first = chat_endpoint.handle(
        ApiRequest(
            method="POST",
            path="/api/v1/chat",
            request_id="A-1",
            body={"mensaje": "abre menu a", "contexto": {"session_id": "session-A"}},
        ),
        facade,
    )
    second = chat_endpoint.handle(
        ApiRequest(
            method="POST",
            path="/api/v1/chat",
            request_id="B-1",
            body={"mensaje": "y cual es la mas cara?", "contexto": {"session_id": "session-B"}},
        ),
        facade,
    )

    assert first.status_code == 200 and second.status_code == 200
    assert first.payload.get("session_id") == "session-A"
    assert second.payload.get("session_id") == "session-B"
    assert first.payload.get("contexto", {}).get("menu_activo", {}).get("id") == "MENU-A"
    assert second.payload.get("contexto", {}).get("menu_activo") == {}
    assert len(created_services) == 2
