from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
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

    def execute_agent_read(self, tool_id, arguments):
        self.calls.append((tool_id, dict(arguments)))
        return SimpleNamespace(estado="OK", datos={"estado": "OK", "tool": tool_id, "datos_reales_modificados": False})


def test_objetivo_amplio_mantiene_reads_hasta_minimo_de_evidencia():
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_eventos", {"consulta": "proximos"}, "1")]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_evento_detalle", {"evento_id": "EVT-1"}, "2")]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_produccion", {"consulta": "pendientes"}, "3")]),
        AgentTurnResult(FINAL_RESPONSE, text="Plan estructurado con evidencia disponible."),
    ])
    executor = _Executor()
    agent = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(build_default_tool_registry()))

    result = agent.run(
        "Hazme la producción del próximo evento. Investiga todos los datos y organízamela de forma profesional.",
        {"workflow": {"workflow_type": "production_planning"}},
    )

    assert result.ok is True
    assert [call[0] for call in executor.calls] == ["consultar_eventos", "consultar_evento_detalle", "consultar_produccion"]
    assert [request.tool_choice_mode for request in engine.requests[:3]] == ["required", "required", "required"]
    assert engine.requests[3].tool_choice_mode == "auto"


def test_consulta_simple_no_fuerza_investigacion_adicional():
    engine = _Engine([AgentTurnResult(FINAL_RESPONSE, text="Tienes 5 kg.")])
    agent = HostAIAgent(engine, _Executor(), HostAIToolCatalog.for_general_agent(build_default_tool_registry()))

    result = agent.run("¿Cuánta Patata Monalisa tengo?")

    assert result.ok is True
    assert engine.requests[0].tool_choice_mode == "auto"