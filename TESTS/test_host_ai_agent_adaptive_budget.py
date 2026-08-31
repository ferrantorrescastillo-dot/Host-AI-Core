from __future__ import annotations

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
        return SimpleNamespace(
            estado="OK", datos={"tool": tool_id, "datos_reales_modificados": False},
            contexto_actualizado={}, duracion_ms=0,
        )


def _agent(engine, executor=None):
    return HostAIAgent(
        engine,
        executor or _Executor(),
        HostAIToolCatalog.for_general_agent(build_default_tool_registry()),
    )


def _production_context(telemetry=None):
    context = {"workflow": {"workflow_type": "production_planning"}}
    if telemetry is not None:
        context["telemetry"] = telemetry
    return context


def _multi_factor_context(telemetry=None):
    context = {
        "intelligence_route": {
            "reason": "multi_factor_operational_analysis",
            "workflow_type": "",
        }
    }
    if telemetry is not None:
        context["telemetry"] = telemetry
    return context


def test_consulta_stock_simple_conserva_budget_reducido():
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "s")]),
        AgentTurnResult(FINAL_RESPONSE, text="Stock revisado"),
    ])

    result = _agent(engine).run("Revisa el stock")

    assert result.ok
    assert engine.requests[0].limits["max_tool_calls"] == 4


def test_production_planning_expone_catalogo_ampliado_y_budget_adaptativo():
    engine = _Engine([AgentTurnResult(FINAL_RESPONSE, text="Sin cambios")])

    result = _agent(engine).run("Organiza la producción", _production_context())

    exposed = {item["tool_id"] for item in engine.requests[0].allowed_tools}
    assert result.ok
    assert engine.requests[0].limits["max_tool_calls"] == 9
    assert {"buscar_articulos", "consultar_articulo_detalle"} <= exposed
    assert {
        "consultar_eventos", "consultar_evento_detalle", "consultar_escandallos",
        "consultar_estado_stock", "consultar_compras_pendientes", "consultar_produccion",
    } <= exposed
    assert all(item["type"] == "READ" for item in engine.requests[0].allowed_tools)


def test_multi_factor_multifuente_recibe_budget_adaptativo_pero_simple_no():
    complex_engine = _Engine([AgentTurnResult(FINAL_RESPONSE, text="Análisis")])
    simple_engine = _Engine([AgentTurnResult(FINAL_RESPONSE, text="Stock")])

    _agent(complex_engine).run(
        "Analiza el menú completo, investiga recetas, ingredientes, stock y compras.",
        _multi_factor_context(),
    )
    _agent(simple_engine).run(
        "¿Cuánto stock tengo de patata?",
        _multi_factor_context(),
    )

    assert complex_engine.requests[0].limits["max_tool_calls"] == 9
    assert simple_engine.requests[0].limits["max_tool_calls"] == 4


def test_multi_factor_menu_escandallos_stock_y_compras_supera_cuatro_reads():
    calls = [
        ("consultar_menu", {"consulta": "detalle", "termino": "menu"}),
        ("consultar_escandallos", {"consulta": "detalle", "escandallo_id": "REC-1"}),
        ("consultar_escandallos", {"consulta": "detalle", "escandallo_id": "REC-2"}),
        ("consultar_escandallos", {"consulta": "detalle", "escandallo_id": "REC-3"}),
        ("consultar_estado_stock", {"consulta": "articulo", "terminos": ["ART-1", "ART-2"]}),
        ("consultar_compras_pendientes", {"consulta": "listado", "article_id": "ART-1"}),
    ]
    turns = [
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(tool_id, arguments, f"m{index}")])
        for index, (tool_id, arguments) in enumerate(calls)
    ] + [AgentTurnResult(FINAL_RESPONSE, text="Análisis completo")]
    engine, executor = _Engine(turns), _Executor()

    result = _agent(engine, executor).run(
        "Analiza el menú completo, investiga recetas, ingredientes, stock y compras.",
        _multi_factor_context(),
    )

    assert result.ok
    assert engine.requests[0].limits["max_tool_calls"] == 9
    assert [tool_id for tool_id, _arguments in executor.calls] == [item[0] for item in calls]
    assert len(executor.calls) == 6
    assert result.research_completion_reason == "ENOUGH_EVIDENCE"


def test_production_planning_completa_siete_reads_encadenadas():
    chain = [
        ("consultar_eventos", {"consulta": "proximos"}),
        ("consultar_evento_detalle", {"consulta": "detalle", "evento_id": "EV-1"}),
        ("consultar_escandallos", {"consulta": "buscar", "nombre_referencia": "Carrillera de ternera"}),
        ("buscar_articulos", {"termino": "Carrillera de ternera"}),
        ("consultar_articulo_detalle", {"article_id": "ART-1"}),
        ("consultar_estado_stock", {"consulta": "articulo", "termino": "ART-1"}),
        ("consultar_compras_pendientes", {"consulta": "listado", "article_id": "ART-1"}),
        ("consultar_produccion", {"consulta": "pendientes"}),
    ]
    turns = [
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(tool_id, arguments, f"c{index}")])
        for index, (tool_id, arguments) in enumerate(chain)
    ] + [AgentTurnResult(FINAL_RESPONSE, text="Investigación completa")]
    engine, executor = _Engine(turns), _Executor()

    result = _agent(engine, executor).run("Organiza la producción", _production_context())

    assert result.ok
    assert [tool_id for tool_id, _arguments in executor.calls] == [item[0] for item in chain]
    assert len(executor.calls) == 8
    assert result.research_completion_reason == "ENOUGH_EVIDENCE"


def test_hard_limit_marca_reads_pendientes_y_fuerza_sintesis_segura():
    requested = [
        ToolCall("consultar_eventos", {"consulta": "proximos"}, "1"),
        ToolCall("consultar_evento_detalle", {"consulta": "detalle", "evento_id": "EV-1"}, "2"),
        ToolCall("consultar_escandallos", {"consulta": "buscar", "termino": "Carrillera"}, "3"),
        ToolCall("buscar_articulos", {"termino": "Carrillera"}, "4"),
        ToolCall("consultar_articulo_detalle", {"article_id": "ART-1"}, "5"),
        ToolCall("consultar_estado_stock", {"consulta": "articulo", "termino": "ART-1"}, "6"),
        ToolCall("consultar_compras_pendientes", {"consulta": "listado", "article_id": "ART-1"}, "7"),
        ToolCall("consultar_produccion", {"consulta": "pendientes"}, "8"),
        ToolCall("consultar_uso_elaboracion", {"escandallo_id": "REC-1"}, "9"),
        ToolCall("consultar_menu", {"consulta": "detalle", "menu_id": "MENU-1"}, "10"),
    ]
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=requested),
        AgentTurnResult(FINAL_RESPONSE, text="Síntesis acotada"),
    ])
    events = []
    telemetry = SimpleNamespace(emit=lambda event_type, **metadata: events.append({"event_type": event_type, **metadata}))

    result = _agent(engine).run("Investiga toda la producción", _production_context(telemetry))

    assert result.ok
    assert len(result.executed_tools) == 9
    assert engine.requests[0].limits["max_tool_calls"] == 9
    assert len(engine.requests[1].allowed_tools) == 0
    assert result.research_completion_reason == "BUDGET_EXHAUSTED"
    assert result.final_answer_source == "FORCED_BUDGET_SYNTHESIS"
    final = next(item for item in events if item["event_type"] == "agent_final")
    assert final["research_completion_reason"] == "BUDGET_EXHAUSTED"
    assert final["final_answer_source"] == "FORCED_BUDGET_SYNTHESIS"
    assert _agent(_Engine([])).policy.PRODUCTION_PLANNING_TOOL_CALLS <= _agent(_Engine([])).policy.MAX_TOOL_CALLS_HARD
