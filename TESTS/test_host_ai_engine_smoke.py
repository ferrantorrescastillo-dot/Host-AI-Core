from __future__ import annotations

import json
from pathlib import Path

from CORE.orquestador import OrquestadorHostAI, SolicitudHostAI
from SERVICIOS.host_ai_engine import HostAIEngine
from SERVICIOS.host_ai_engine.models import HostAIEngineRequest
from SERVICIOS.host_ai_engine.openai_provider import OpenAIProvider
from SERVICIOS.host_ai_agent_models import AgentTurnRequest, FINAL_RESPONSE, TOOL_CALL


class _DummyMemoria:
    def registrar_respuesta_orquestador(self, intencion: str, respuesta: dict) -> None:
        _ = (intencion, respuesta)

    def limpiar_memoria(self) -> None:
        return


class _DummyDirector:
    def ejecutar_pipeline(self, pipeline: str, accion: str, params: dict):
        raise RuntimeError(f"No deberia llamarse en este smoke test: {pipeline}:{accion}")


class _DummyRegistroPipelines:
    def listar(self):
        return []


class _DummyCore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.memoria = _DummyMemoria()
        self.director = _DummyDirector()
        self.registro_pipelines = _DummyRegistroPipelines()


def test_host_ai_engine_simulado_y_logs_sanitizados(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "CLAVE_ENTORNO_FICTICIA")
    engine = HostAIEngine(tmp_path)

    resultado = engine.consultar(
        origen="Eventos",
        modulo="eventos",
        tipo_peticion="responder_pregunta",
        datos_enviados={
            "pregunta": "Que menu recomiendas CLAVE_ENTORNO_FICTICIA",
            "password": "SECRETO",
            "OPENAI_API_KEY": "OTRO_SECRETO",
        },
        proveedor_preferido="SIMULADO",
        formato_entrada="texto",
    )

    assert str(resultado.get("estado") or "") == "OK_SIMULADO"
    assert str(resultado.get("proveedor") or "") == "SIMULADO"
    assert isinstance(resultado.get("respuesta"), dict)

    log_path = tmp_path / "DATOS" / "logs" / "host_ai_engine_calls.jsonl"
    assert log_path.exists()
    contenido = log_path.read_text(encoding="utf-8")
    assert "SECRETO" not in contenido
    assert "OTRO_SECRETO" not in contenido
    assert "CLAVE_ENTORNO_FICTICIA" not in contenido
    assert "***REDACTED***" in contenido


def test_host_ai_engine_multi_provider_preparado(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("HOST_AI_AI_PROVIDER", raising=False)
    engine = HostAIEngine(tmp_path)
    providers = engine.providers_disponibles()
    ids = {str(p.get("id") or "") for p in providers}

    assert {"SIMULADO", "OPENAI", "AZURE_OPENAI", "CLAUDE", "GEMINI", "LOCAL"}.issubset(ids)

    respuesta_nc = engine.consultar(
        origen="Compras",
        modulo="compras",
        tipo_peticion="proponer_proveedor",
        datos_enviados={"producto": "Aceite"},
        proveedor_preferido="OPENAI",
    )
    assert str(respuesta_nc.get("estado") or "") == "ERROR"
    assert "no conectado" in " ".join(respuesta_nc.get("errores") or []).lower()


class _FakeResponses:
    def __init__(self, output_text: str = "Respuesta real simulada"):
        self.output_text = output_text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return type("FakeResponse", (), {"output_text": self.output_text})()


class _FakeOpenAIClient:
    def __init__(self, responses: _FakeResponses):
        self.responses = responses


def _request() -> HostAIEngineRequest:
    return HostAIEngineRequest(
        origen="CHAT",
        modulo="chat_host_ai",
        tipo_peticion="consulta_general",
        datos_enviados={"pregunta": "Hola, ¿qué puedes hacer?"},
        proveedor_preferido="OPENAI",
    )


def test_openai_provider_usa_responses_api_y_modelo_configurable(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia-de-test")
    monkeypatch.setenv("OPENAI_MODEL", "modelo-ficticio-de-test")
    responses = _FakeResponses()
    factory_calls = []

    def factory(**kwargs):
        factory_calls.append({"has_key": bool(kwargs.get("api_key")), "timeout": kwargs.get("timeout")})
        return _FakeOpenAIClient(responses)

    provider = OpenAIProvider(client_factory=factory)
    result = provider.ejecutar(_request())

    assert result.ok is True
    assert result.modelo == "modelo-ficticio-de-test"
    assert result.salida == {"mensaje": "Respuesta real simulada"}
    assert factory_calls == [{"has_key": True, "timeout": 30.0}]
    assert responses.calls[0]["model"] == "modelo-ficticio-de-test"
    assert responses.calls[0]["input"] == "Hola, ¿qué puedes hacer?"
    assert "tools" not in responses.calls[0]


def test_openai_provider_traduce_tool_call_al_contrato_neutral(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia-de-test")
    item = type("Item", (), {"type": "function_call", "name": "consultar_estado_stock", "arguments": '{"consulta":"resumen"}', "call_id": "call-1"})()

    class Responses:
        def __init__(self): self.calls = []
        def create(self, **kwargs):
            self.calls.append(kwargs)
            return type("Response", (), {"output": [item], "output_text": "", "usage": None})()

    responses = Responses()
    provider = OpenAIProvider(client_factory=lambda **_kwargs: _FakeOpenAIClient(responses))
    request = AgentTurnRequest(
        messages=[{"role": "user", "content": "Revisa stock"}],
        allowed_tools=[{"tool_id": "consultar_estado_stock", "description": "Consulta stock", "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}}],
        request_id="REQ-1", system_instructions="INSTRUCCIONES NEUTRALES",
    )
    result = provider.ejecutar_turn_agente(request)
    assert result.kind == TOOL_CALL and result.tool_calls[0].tool_id == "consultar_estado_stock"
    assert result.tool_calls[0].arguments == {"consulta": "resumen"}
    assert responses.calls[0]["tools"][0]["name"] == "consultar_estado_stock"
    assert responses.calls[0]["instructions"] == "INSTRUCCIONES NEUTRALES"
    assert responses.calls[0]["tool_choice"] == "auto"
    assert responses.calls[0]["tools"][0]["parameters"]["additionalProperties"] is False
    assert responses.calls[0]["timeout"] == 30.0
    assert responses.calls[0]["text"]["format"]["schema"]["required"] == ["grounding_requirement", "answer"]
    assert responses.calls[0]["text"]["format"]["schema"]["additionalProperties"] is False


def test_openai_provider_aplica_tool_choice_required_en_grounding_retry(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia-de-test")
    item = type("Item", (), {"type": "function_call", "name": "consultar_estado_stock", "arguments": '{}', "call_id": "required-1"})()

    class Responses:
        def __init__(self): self.calls = []
        def create(self, **kwargs):
            self.calls.append(kwargs)
            return type("Response", (), {"output": [item], "output_text": "", "usage": None})()

    responses = Responses()
    provider = OpenAIProvider(client_factory=lambda **_kwargs: _FakeOpenAIClient(responses))
    request = AgentTurnRequest(
        messages=[{"role": "user", "content": "Consulta interna"}],
        allowed_tools=[{"tool_id": "consultar_estado_stock", "description": "Consulta stock", "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}}],
        request_id="REQ-REQUIRED", tool_choice_mode="required",
    )
    assert provider.ejecutar_turn_agente(request).kind == TOOL_CALL
    assert responses.calls[0]["tool_choice"] == "required"


def test_openai_provider_traduce_respuesta_final_y_tool_data(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia-de-test")
    responses = _FakeResponses('{"grounding_requirement":"NONE","answer":"Respuesta conversacional"}')
    provider = OpenAIProvider(client_factory=lambda **_kwargs: _FakeOpenAIClient(responses))
    request = AgentTurnRequest(
        messages=[
            {"role": "user", "content": "Revisa"},
            {"role": "assistant", "type": "tool_call", "tool_id": "consultar_estado_stock", "call_id": "c1", "arguments": {}},
            {"role": "tool", "type": "TOOL_DATA", "tool_id": "consultar_estado_stock", "call_id": "c1", "content": {"cantidad": None}, "untrusted_data": True},
        ],
        allowed_tools=[], request_id="REQ-2",
    )
    result = provider.ejecutar_turn_agente(request)
    assert result.kind == FINAL_RESPONSE and result.text == "Respuesta conversacional"
    assert responses.calls[0]["input"][-1]["type"] == "function_call_output"
    assert "UNTRUSTED_DATA" in responses.calls[0]["input"][-1]["output"]


def test_openai_provider_payload_contiene_catalogo_read_completo(monkeypatch) -> None:
    from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
    from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia-de-test")
    responses = _FakeResponses('{"grounding_requirement":"NONE","answer":"Hola"}')
    provider = OpenAIProvider(client_factory=lambda **_kwargs: _FakeOpenAIClient(responses))
    request = AgentTurnRequest(messages=[{"role": "user", "content": "Hola"}], allowed_tools=HostAIToolCatalog(build_default_tool_registry()).effective_tools(), request_id="REQ-CATALOGO")
    result = provider.ejecutar_turn_agente(request)
    assert result.kind == FINAL_RESPONSE
    payload = responses.calls[0]
    assert payload["tool_choice"] == "auto"
    assert {tool["name"] for tool in payload["tools"]} == {"consultar_produccion", "consultar_estado_stock", "consultar_compras_pendientes"}
    assert all(tool["type"] == "function" and tool["parameters"]["additionalProperties"] is False for tool in payload["tools"])
    assert "credencial-ficticia-de-test" not in json.dumps(payload)


def test_openai_provider_aplica_timeout_efectivo_por_turno(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia-de-test")
    responses = _FakeResponses('{"grounding_requirement":"NONE","answer":"ok"}')
    provider = OpenAIProvider(client_factory=lambda **_kwargs: _FakeOpenAIClient(responses))
    request = AgentTurnRequest(messages=[{"role": "user", "content": "hola"}], allowed_tools=[], request_id="REQ-TIMEOUT", provider_timeout_seconds=47.5)
    assert provider.ejecutar_turn_agente(request).kind == FINAL_RESPONSE
    assert responses.calls[0]["timeout"] == 47.5


def test_openai_provider_clasifica_timeout_sin_exponer_excepcion(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia-de-test")
    class Responses:
        def create(self, **_kwargs): raise type("APITimeoutError", (Exception,), {})("SECRETO")
    provider = OpenAIProvider(client_factory=lambda **_kwargs: _FakeOpenAIClient(Responses()))
    result = provider.ejecutar_turn_agente(AgentTurnRequest(messages=[], allowed_tools=[], request_id="REQ-TIMEOUT"))
    assert result.safe_error == "api_timeout"
    assert "SECRETO" not in json.dumps(result.__dict__)


def test_openai_provider_sin_clave_falla_sin_crear_cliente(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = OpenAIProvider(client_factory=lambda **_kwargs: (_ for _ in ()).throw(AssertionError("no llamar")))

    result = provider.ejecutar(_request())

    assert result.ok is False
    assert "OPENAI_API_KEY" in " ".join(result.errores)


def test_openai_provider_traduce_errores_sin_filtrar_secretos(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia-de-test")

    cases = [
        (type("AuthenticationError", (Exception,), {"status_code": 401}), "credencial"),
        (type("QuotaError", (Exception,), {"status_code": 429, "code": "insufficient_quota"}), "cuota"),
        (type("RateLimitError", (Exception,), {"status_code": 429}), "limitado"),
        (type("APITimeoutError", (Exception,), {}), "tiempo"),
        (type("APIConnectionError", (Exception,), {}), "conectar"),
    ]
    for error_type, expected in cases:
        class FailingResponses:
            def create(self, **_kwargs):
                raise error_type("mensaje potencialmente sensible")

        provider = OpenAIProvider(client_factory=lambda **_kwargs: _FakeOpenAIClient(FailingResponses()))
        result = provider.ejecutar(_request())
        serialized = json.dumps(result.to_dict(), ensure_ascii=False)
        assert result.ok is False
        assert expected in serialized.lower()
        assert "mensaje potencialmente sensible" not in serialized
        assert "credencial-ficticia-de-test" not in serialized


def test_orquestador_exponer_host_ai_engine(tmp_path: Path) -> None:
    core = _DummyCore(tmp_path)
    orquestador = OrquestadorHostAI(core)

    health = orquestador.resolver(SolicitudHostAI("host_ai_engine_health", {})).to_dict()
    assert health["ok"] is True
    assert str((health.get("datos") or {}).get("servicio") or "") == "HOST AI ENGINE"

    consulta = orquestador.resolver(
        SolicitudHostAI(
            "host_ai_engine_consulta",
            {
                "origen": "Escandallos",
                "modulo": "escandallos",
                "tipo_peticion": "detectar_duplicados",
                "datos_enviados": {"lineas": ["A", "B"]},
                "proveedor_preferido": "SIMULADO",
                "formato_entrada": "excel",
            },
        )
    ).to_dict()

    assert consulta["ok"] is True
    motor = ((consulta.get("datos") or {}).get("host_ai_engine") or {})
    assert str(motor.get("estado") or "") == "OK_SIMULADO"
    assert str(motor.get("modulo") or "") == "escandallos"
