from __future__ import annotations

from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class Engine:
    def __init__(self, turns): self.turns = list(turns); self.requests = []
    def ejecutar_turn_agente(self, request): self.requests.append(request); return self.turns.pop(0)


class Executor:
    def __init__(self): self.calls = []
    def execute_agent_read(self, tool_id, arguments):
        self.calls.append((tool_id, arguments))
        return SimpleNamespace(estado="OK", datos={"tool": tool_id, "args": arguments})


def run(calls):
    engine = Engine([AgentTurnResult(TOOL_CALL, tool_calls=calls), AgentTurnResult(FINAL_RESPONSE, text="Final libre")])
    executor = Executor()
    result = HostAIAgent(engine, executor, HostAIToolCatalog(build_default_tool_registry())).run("consulta")
    return result, engine, executor


def test_tres_calls_validas_se_envian_juntas_y_finalizan():
    calls = [ToolCall("consultar_produccion", {"consulta": "pendientes"}, "p"), ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "s"), ToolCall("consultar_compras_pendientes", {}, "c")]
    result, engine, executor = run(calls)
    assert result.ok and len(executor.calls) == 3
    second = engine.requests[1].messages
    assert [item["call_id"] for item in second if item.get("type") == "tool_call"] == ["p", "s", "c"]
    assert [item["call_id"] for item in second if item.get("type") == "TOOL_DATA"] == ["p", "s", "c"]


def test_ocho_identicas_solo_ejecutan_una_y_todas_reciben_output():
    result, engine, executor = run([ToolCall("consultar_estado_stock", {"consulta": "resumen"}, f"c{i}") for i in range(8)])
    assert result.ok and len(executor.calls) == 1
    assert len([item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA"]) == 8


def test_cinco_distintas_ejecutan_cuatro_y_continuan_sin_resultado_falso():
    calls = [ToolCall("consultar_produccion", {"consulta": value}, f"c{i}") for i, value in enumerate(["pendientes", "bloqueadas", "hoy", "en_curso", "terminadas"])]
    result, engine, executor = run(calls)
    assert result.ok and len(executor.calls) == 2  # limite de dos ejecuciones no equivalentes por tool
    outputs = [item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA"]
    rejected = [item for item in outputs if item["content"].get("status") == "NOT_EXECUTED"]
    assert len(rejected) == 3 and all(item["content"]["reason"] == "max_same_tool_calls_policy" for item in rejected)


def test_cinco_tools_distintas_por_firma_respetan_budget_cuatro():
    calls = [
        ToolCall("consultar_produccion", {"consulta": "pendientes"}, "1"),
        ToolCall("consultar_produccion", {"consulta": "bloqueadas"}, "2"),
        ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "3"),
        ToolCall("consultar_estado_stock", {"consulta": "alertas"}, "4"),
        ToolCall("consultar_compras_pendientes", {}, "5"),
    ]
    result, engine, executor = run(calls)
    assert result.ok and len(executor.calls) == 4
    assert [item[0] for item in executor.calls] == [
        "consultar_produccion",
        "consultar_estado_stock",
        "consultar_compras_pendientes",
        "consultar_produccion",
    ]
    outputs = [item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA"]
    assert outputs[3]["content"] == {"status": "NOT_EXECUTED", "reason": "max_tool_calls_policy", "datos_reales_modificados": False}


def test_patron_real_reserva_cobertura_y_deja_cuarto_slot_a_segunda_variante():
    calls = [
        ToolCall("consultar_produccion", {"consulta": value}, f"p{i}")
        for i, value in enumerate(["pendientes", "bloqueadas", "hoy", "en_curso"], 1)
    ] + [
        ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "s1"),
        ToolCall("consultar_estado_stock", {"consulta": "alertas"}, "s2"),
        ToolCall("consultar_compras_pendientes", {}, "c1"),
    ]

    result, engine, executor = run(calls)

    assert result.ok is True
    assert [item[0] for item in executor.calls] == [
        "consultar_produccion",
        "consultar_estado_stock",
        "consultar_compras_pendientes",
        "consultar_produccion",
    ]
    outputs = {item["call_id"]: item["content"] for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA"}
    assert outputs["c1"]["tool"] == "consultar_compras_pendientes"
    assert outputs["p3"]["status"] == outputs["p4"]["status"] == "NOT_EXECUTED"
    assert outputs["s2"]["status"] == "NOT_EXECUTED"


def test_observabilidad_expone_fase_rango_y_seleccion_sin_argumentos():
    calls = [
        ToolCall("consultar_produccion", {"consulta": "pendientes"}, "p1"),
        ToolCall("consultar_produccion", {"consulta": "bloqueadas"}, "p2"),
        ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "s1"),
        ToolCall("consultar_compras_pendientes", {}, "c1"),
    ]
    engine = Engine([AgentTurnResult(TOOL_CALL, tool_calls=calls), AgentTurnResult(FINAL_RESPONSE, text="Final")])
    events = []
    telemetry = SimpleNamespace(emit=lambda event_type, **metadata: events.append({"event_type": event_type, **metadata}))
    result = HostAIAgent(engine, Executor(), HostAIToolCatalog(build_default_tool_registry())).run(
        "consulta",
        conversation_context={"telemetry": telemetry},
    )

    assert result.ok
    planned = [item for item in events if item["event_type"] == "agent_tool_call"]
    assert [item["planning_phase"] for item in planned] == [
        "UNIQUE_TOOL_COVERAGE", "SECOND_PASS", "UNIQUE_TOOL_COVERAGE", "UNIQUE_TOOL_COVERAGE"
    ]
    assert [item["selection_rank"] for item in planned] == [1, 4, 2, 3]
    assert all(item["selected_for_execution"] is True for item in planned)
    assert all("arguments" not in item for item in planned)


def test_budget_tres_prioriza_a1_b1_c1_sobre_a2():
    agent = HostAIAgent(Engine([]), Executor(), HostAIToolCatalog(build_default_tool_registry()))
    agent.policy.MAX_TOOL_CALLS = 3
    planned, _ = agent._plan_tool_batch([
        ToolCall("consultar_produccion", {"consulta": "pendientes"}, "a1"),
        ToolCall("consultar_produccion", {"consulta": "bloqueadas"}, "a2"),
        ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "b1"),
        ToolCall("consultar_compras_pendientes", {}, "c1"),
    ], agent.catalog.effective_tools(), 0, {})
    assert [item["call"].call_id for item in planned if item["disposition"] == "EXECUTED"] == ["a1", "b1", "c1"]
    assert [item["planning_phase"] for item in planned if item["disposition"] == "EXECUTED"] == ["UNIQUE_TOOL_COVERAGE"] * 3


def test_duplicada_no_consume_budget_y_reutiliza_resultado():
    calls = [
        ToolCall("consultar_produccion", {"consulta": "pendientes"}, "a1"),
        ToolCall("consultar_produccion", {"consulta": "pendientes"}, "a1-dup"),
        ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "b1"),
        ToolCall("consultar_compras_pendientes", {}, "c1"),
    ]
    result, engine, executor = run(calls)
    assert result.ok and len(executor.calls) == 3
    outputs = {item["call_id"]: item["content"] for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA"}
    assert outputs["a1-dup"] == outputs["a1"]


def test_invalida_temprana_no_impide_cobertura_valida():
    result, _engine, executor = run([
        ToolCall("inventada", {}, "bad"),
        ToolCall("consultar_produccion", {"consulta": "pendientes"}, "a2"),
        ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "b1"),
    ])
    assert result.ok and [item[0] for item in executor.calls] == ["consultar_produccion", "consultar_estado_stock"]


def test_una_sola_tool_con_cinco_variantes_ejecuta_maximo_dos():
    result, _engine, executor = run([
        ToolCall("consultar_produccion", {"consulta": value}, str(index))
        for index, value in enumerate(["pendientes", "bloqueadas", "hoy", "en_curso", "terminadas"], 1)
    ])
    assert result.ok and len(executor.calls) == 2


def test_invalida_mezclada_no_rompe_validas_y_todas_invalidas_fallan():
    result, _engine, executor = run([ToolCall("inventada", {}, "x"), ToolCall("consultar_estado_stock", {}, "s"), ToolCall("consultar_compras_pendientes", {}, "c")])
    assert result.ok and len(executor.calls) == 2
    engine = Engine([AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("inventada", {}, "x")])])
    failed = HostAIAgent(engine, Executor(), HostAIToolCatalog(build_default_tool_registry())).run("consulta")
    assert not failed.ok and failed.safe_error == "invalid_tool"
