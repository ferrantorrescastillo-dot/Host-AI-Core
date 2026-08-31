from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnRequest, AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_engine.models import HostAIEngineRequest, HostAIProviderResult
from SERVICIOS.host_ai_engine.openai_provider import OpenAIProvider
from SERVICIOS.host_ai_engine.providers import HostAIProviderBase
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class FakeNeutralProvider(HostAIProviderBase):
    provider_name = "FAKE_NEUTRAL"
    model_name = "neutral-v1"

    def __init__(self, turns):
        self.turns = list(turns)
        self.requests = []

    @property
    def supports_tool_calling(self) -> bool:
        return True

    def ejecutar_turn_agente(self, request: AgentTurnRequest) -> AgentTurnResult:
        self.requests.append(request)
        return self.turns.pop(0)

    def ejecutar(self, request: HostAIEngineRequest) -> HostAIProviderResult:
        return HostAIProviderResult(True, self.provider_name, self.model_name, {"mensaje": "fake"}, [])


class _Executor:
    def __init__(self):
        self.calls = []

    def execute_agent_read(self, tool_id, arguments):
        self.calls.append((tool_id, dict(arguments)))
        return SimpleNamespace(
            estado="OK",
            datos={"fuente": "stock_canonico", "existencias": [], "datos_reales_modificados": False},
        )


def _agent(provider, executor=None):
    return HostAIAgent(
        SimpleNamespace(ejecutar_turn_agente=provider.ejecutar_turn_agente),
        executor or _Executor(),
        HostAIToolCatalog(build_default_tool_registry()),
    )


def test_agent_funciona_con_provider_neutral_sin_importar_openai():
    provider = FakeNeutralProvider([AgentTurnResult(FINAL_RESPONSE, text="Respuesta neutral")])
    result = _agent(provider).run("pregunta general")
    assert result.ok and result.text == "Respuesta neutral"
    assert provider.requests[0].allowed_tools
    assert provider.requests[0].system_instructions


def test_provider_neutral_pide_stock_recibe_resultado_y_finaliza():
    provider = FakeNeutralProvider([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "c1")]),
        AgentTurnResult(FINAL_RESPONSE, text="Stock explicado libremente"),
    ])
    executor = _Executor()
    result = _agent(provider, executor).run("Como esta mi stock?")
    assert result.text == "Stock explicado libremente"
    assert executor.calls == [("consultar_estado_stock", {"consulta": "resumen"})]
    assert provider.requests[1].messages[-1]["type"] == "TOOL_DATA"
    assert provider.requests[1].messages[-1]["content"]["fuente"] == "stock_canonico"


def test_openai_modelo_configurable_no_cambia_contrato_neutral(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia")
    monkeypatch.setenv("OPENAI_MODEL", "modelo-openai-alternativo")
    provider = OpenAIProvider(client_factory=lambda **_kwargs: SimpleNamespace())
    request = AgentTurnRequest(
        messages=[{"role": "user", "content": "consulta"}],
        allowed_tools=[], request_id="neutral-request",
    )
    assert provider.model_name == "modelo-openai-alternativo"
    assert isinstance(request, AgentTurnRequest)
    assert not hasattr(request, "openai_response")
    assert not hasattr(request, "response_id")


def test_provider_sin_tool_calling_devuelve_error_neutral():
    class ProviderWithoutTools(HostAIProviderBase):
        provider_name = "NO_TOOLS"
        model_name = "none"

        def ejecutar(self, request):
            return HostAIProviderResult(False, self.provider_name, self.model_name, {}, ["not supported"])

    result = ProviderWithoutTools().ejecutar_turn_agente(AgentTurnRequest([], [], "request"))
    assert result.safe_error == "provider_tool_calling_not_supported"
    assert result.provider_metadata == {"provider": "NO_TOOLS", "model": "none"}


def test_error_openai_se_normaliza_dentro_del_adapter(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia")

    class Responses:
        def create(self, **_kwargs):
            raise type("RateLimitError", (Exception,), {"status_code": 429})("SECRETO-SDK")

    provider = OpenAIProvider(client_factory=lambda **_kwargs: SimpleNamespace(responses=Responses()))
    result = provider.ejecutar_turn_agente(AgentTurnRequest([], [], "request"))
    assert result.safe_error == "provider_runtime_error"
    assert "SECRETO-SDK" not in result.safe_error


def test_sdk_openai_solo_se_importa_en_adapter():
    root = Path(__file__).resolve().parents[1]
    offenders = []
    for path in (root / "SERVICIOS").rglob("*.py"):
        if path.name == "openai_provider.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(alias.name == "openai" or alias.name.startswith("openai.") for alias in node.names):
                offenders.append(path.relative_to(root).as_posix())
            if isinstance(node, ast.ImportFrom) and (node.module == "openai" or str(node.module or "").startswith("openai.")):
                offenders.append(path.relative_to(root).as_posix())
    assert offenders == []
