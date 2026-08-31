from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from API.contracts.http_models import ApiRequest
from API.endpoints import chat as chat_endpoint
from API.facade.core_public_api02 import CorePublicApi02Facade
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentRunResult, AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class _Engine:
    def __init__(self, turns):
        self.turns = list(turns)
        self.requests = []

    def ejecutar_turn_agente(self, request):
        self.requests.append(request)
        return self.turns.pop(0)


class _Executor:
    def __init__(self):
        self.calls = []
        self.state = {"stock": "intacto", "compras": "intactas", "produccion": "intacta"}

    def execute_agent_read(self, tool_id, params):
        self.calls.append((tool_id, dict(params)))
        return SimpleNamespace(
            estado="OK",
            datos={"solo_lectura": True, "datos_reales_modificados": False, "resultados": []},
        )


def _agent(turns, executor=None):
    engine = _Engine(turns)
    agent = HostAIAgent(
        engine,
        executor or _Executor(),
        HostAIToolCatalog(build_default_tool_registry()),
    )
    return agent, engine


def test_respuesta_natural_llega_exactamente_sin_plantilla_python():
    text = (
        "Yo empezaria por desbloquear la tarea de produccion. Despues revisaria el "
        "pedido pendiente de patata, porque tienes material por recibir."
    )
    agent, _ = _agent([AgentTurnResult(FINAL_RESPONSE, text=text)])

    result = agent.run("Que harias primero?")

    assert result.text == text
    assert all(value not in result.text for value in ("Resumen rapido", "Conclusion", "Acciones recomendadas"))


def test_respuesta_general_directa_no_usa_tools_y_conserva_texto():
    text = "Confitar cocina lentamente en grasa; pochar cocina suavemente, normalmente sin dorar."
    executor = _Executor()
    agent, _ = _agent([AgentTurnResult(FINAL_RESPONSE, text=text)], executor)

    result = agent.run("Que diferencia hay entre confitar y pochar?")

    assert result.ok is True
    assert result.text == text
    assert result.executed_tools == []
    assert executor.calls == []


def test_follow_up_conserva_orden_roles_y_no_duplica_mensaje_actual():
    agent, engine = _agent([AgentTurnResult(FINAL_RESPONSE, text="Yo empezaria por el bloqueo.")])
    history = [
        {"role": "user", "content": "Mira mi produccion, stock y compras y dime como voy."},
        {"role": "assistant", "content": "Hay una tarea bloqueada y un pedido pendiente."},
    ]

    result = agent.run(
        "Vale, y tu que harias primero?",
        conversation_context={"conversation_history": history},
    )

    assert result.ok is True
    assert engine.requests[0].messages == [
        *history,
        {"role": "user", "content": "Vale, y tu que harias primero?"},
    ]


def test_follow_up_puede_reconsultar_una_tool_sin_reconsultarlas_todas():
    executor = _Executor()
    agent, engine = _agent(
        [
            AgentTurnResult(
                TOOL_CALL,
                tool_calls=[ToolCall("consultar_produccion", {"consulta": "bloqueadas"}, "call-1")],
            ),
            AgentTurnResult(FINAL_RESPONSE, text="Primero resolveria la tarea bloqueada."),
        ],
        executor,
    )

    result = agent.run(
        "Vale, y tu que harias primero?",
        conversation_context={
            "conversation_history": [
                {"role": "user", "content": "Mira mi produccion, stock y compras."},
                {"role": "assistant", "content": "Hay varios asuntos abiertos."},
            ]
        },
    )

    assert result.ok is True
    assert result.executed_tools == ["consultar_produccion"]
    assert executor.calls == [("consultar_produccion", {"consulta": "bloqueadas"})]
    assert engine.requests[1].messages[-1]["type"] == "TOOL_DATA"


def test_catalogo_no_publica_write_y_peticion_write_no_modifica_estado():
    executor = _Executor()
    before = deepcopy(executor.state)
    text = "Todavia no puedo recepcionar pedidos; esa operacion no esta habilitada."
    agent, engine = _agent([AgentTurnResult(FINAL_RESPONSE, text=text)], executor)

    result = agent.run("Recepciona ese pedido.")

    assert result.text == text
    assert executor.state == before
    assert executor.calls == []
    assert result.datos_reales_modificados is False
    assert all(tool["type"] in {"READ", "UI_ACTION"} for tool in engine.requests[0].allowed_tools)
    assert all(tool["type"] != "WRITE" for tool in engine.requests[0].allowed_tools)
    assert all(not tool["tool_id"].startswith(("crear_", "confirmar_", "recepcionar_")) for tool in engine.requests[0].allowed_tools)


def test_http_conserva_historial_entre_dos_mensajes(monkeypatch, tmp_path):
    captured = []

    def fake_run(self, message, conversation_context=None):
        captured.append((message, deepcopy(conversation_context or {})))
        text = "Analisis inicial." if len(captured) == 1 else "Yo empezaria por el bloqueo."
        return AgentRunResult(True, text, f"HAA-{len(captured)}", "FAKE", "fake-model", 1, [])

    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    monkeypatch.setattr(HostAIAgent, "run", fake_run)
    chat_service = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()))
    chat_service.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    facade = CorePublicApi02Facade(base_dir=tmp_path)
    facade._chat_service = chat_service

    first = chat_endpoint.handle(ApiRequest(method="POST", path="/api/v1/chat", body={"mensaje": "Mira mi produccion, stock y compras y dime como voy.", "contexto": {}}, request_id="HTTP-1"), facade)
    second = chat_endpoint.handle(ApiRequest(method="POST", path="/api/v1/chat", body={"mensaje": "Vale, y tu que harias primero?", "contexto": {}}, request_id="HTTP-2"), facade)

    assert first.status_code == second.status_code == 200
    assert len(captured) == 2
    history = captured[1][1]["conversation_history"]
    assert history == [
        {"role": "user", "content": "Mira mi produccion, stock y compras y dime como voy."},
        {"role": "assistant", "content": "Analisis inicial."},
    ]
    assert all("TOOL_DATA" not in item["content"] for item in history)
