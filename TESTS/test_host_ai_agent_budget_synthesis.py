from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class _Engine:
    def __init__(self):
        self.requests = []
        self.turns = [
            AgentTurnResult(TOOL_CALL, tool_calls=[
                ToolCall("consultar_eventos", {"consulta": "proximos"}, "e"),
                ToolCall("consultar_produccion", {"consulta": "pendientes"}, "p"),
                ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "s"),
                ToolCall("consultar_compras_pendientes", {"consulta": "listado"}, "c"),
            ]),
            AgentTurnResult(FINAL_RESPONSE, text="He reunido la información disponible y resumo las prioridades."),
        ]

    def ejecutar_turn_agente(self, request):
        self.requests.append(request)
        return self.turns.pop(0)


class _Executor:
    def execute_agent_read(self, tool_id, _arguments):
        return SimpleNamespace(estado="OK", datos={"tool": tool_id, "solo_lectura": True, "datos_reales_modificados": False})


def test_agente_fuerza_sintesis_sin_tools_al_agotar_presupuesto():
    engine = _Engine()
    result = HostAIAgent(
        engine, _Executor(), HostAIToolCatalog.for_general_agent(build_default_tool_registry()),
    ).run("Investiga la operación completa.")

    assert result.ok is True
    assert len(engine.requests) == 2
    assert len(engine.requests[1].allowed_tools) == 0
    assert "prioridades" in result.text