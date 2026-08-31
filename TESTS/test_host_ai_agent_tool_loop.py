from __future__ import annotations

from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class _Engine:
    def __init__(self, turn): self.turn = turn
    def ejecutar_turn_agente(self, _request): return self.turn


class _TurnsEngine:
    def __init__(self, *turns): self.turns = list(turns); self.requests = []
    def ejecutar_turn_agente(self, request): self.requests.append(request); return self.turns.pop(0)


class _Executor:
    def __init__(self, ok=True): self.ok = ok
    def execute_agent_read(self, *_args): return SimpleNamespace(estado="OK" if self.ok else "ERROR", datos={"resultados": list(range(20))})


class _Telemetry:
    def __init__(self): self.events = []
    def emit(self, event_type, **metadata): self.events.append({"event_type": event_type, **metadata})


def _run(turn, executor=None):
    return HostAIAgent(_Engine(turn), executor or _Executor(), HostAIToolCatalog(build_default_tool_registry())).run("consulta")


def test_loop_rechaza_tool_inventada_navigation_write_y_argumentos_extra():
    for tool, args in [("inventada", {}), ("abrir_stock", {}), ("crear_receta", {}), ("consultar_estado_stock", {"metodo": "__getattr__"})]:
        result = _run(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(tool, args, "c")]))
        assert result.ok is False and not result.executed_tools


def test_loop_corta_repeticion_calls_provider_error_y_tool_error():
    call = ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "c")
    repeated = HostAIAgent(
        _TurnsEngine(
            AgentTurnResult(TOOL_CALL, tool_calls=[call]),
            AgentTurnResult(TOOL_CALL, tool_calls=[call]),
            AgentTurnResult(TOOL_CALL, tool_calls=[call]),
            AgentTurnResult(FINAL_RESPONSE, text="Loop bloqueado."),
        ),
        _Executor(), HostAIToolCatalog(build_default_tool_registry()),
    ).run("consulta")
    assert repeated.ok and repeated.research_completion_reason == "REPEATED_CACHED_READ" and len(repeated.executed_tools) == 1
    assert _run(AgentTurnResult(kind="", safe_error="provider_error")).safe_error == "provider_error"
    assert _run(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_estado_stock", {}, "c")]), _Executor(False)).safe_error == "tool_error"


def test_loop_respeta_maximo_de_calls_y_proyecta_diez():
    calls = [ToolCall("consultar_estado_stock", {"consulta": mode}, f"c{i}") for i, mode in enumerate(["resumen", "alertas", "articulo", "resumen", "alertas"], 1)]
    result = _run(AgentTurnResult(TOOL_CALL, tool_calls=calls))
    assert result.ok is False and result.safe_error == "max_agent_steps_exceeded"


def test_same_tool_mismos_args_dedup_y_args_distintos_hacen_progreso():
    executor = _Executor()
    agent = HostAIAgent(
        _TurnsEngine(
            AgentTurnResult(TOOL_CALL, tool_calls=[
                ToolCall("consultar_estado_stock", {"terminos": ["ART-A"]}, "a1"),
                ToolCall("consultar_estado_stock", {"terminos": ["ART-A"]}, "a2"),
                ToolCall("consultar_estado_stock", {"terminos": ["ART-B"]}, "b"),
            ]),
            AgentTurnResult(FINAL_RESPONSE, text="Consulta completa."),
        ), executor, HostAIToolCatalog(build_default_tool_registry()),
    )
    result = agent.run("Comprueba A y B")
    assert result.ok and result.executed_tools == ["consultar_estado_stock", "consultar_estado_stock"]


def test_loop_real_misma_firma_en_turno_posterior_sigue_bloqueado():
    call = ToolCall("consultar_estado_stock", {"terminos": ["ART-A"]}, "a")
    result = HostAIAgent(
        _TurnsEngine(AgentTurnResult(TOOL_CALL, tool_calls=[call]), AgentTurnResult(TOOL_CALL, tool_calls=[call]), AgentTurnResult(FINAL_RESPONSE, text="Loop bloqueado.")),
        _Executor(), HostAIToolCatalog(build_default_tool_registry()),
    ).run("Consulta")
    assert result.ok is True
    assert result.executed_tools == ["consultar_estado_stock"]


def test_repeticion_cacheada_compacta_y_fuerza_sintesis_model_sin_consumir_budget():
    call = ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "stock")
    telemetry = _Telemetry()
    engine = _TurnsEngine(
        AgentTurnResult(TOOL_CALL, tool_calls=[call]),
        AgentTurnResult(TOOL_CALL, tool_calls=[call]),
        AgentTurnResult(TOOL_CALL, tool_calls=[call]),
        AgentTurnResult(FINAL_RESPONSE, text="Sintesis final con la evidencia disponible."),
    )

    class LargeExecutor:
        def __init__(self): self.calls = 0
        def execute_agent_read(self, *_args):
            self.calls += 1
            return SimpleNamespace(estado="OK", datos={"items": [{"detalle": "x" * 2000}]})

    executor = LargeExecutor()
    result = HostAIAgent(
        engine, executor, HostAIToolCatalog(build_default_tool_registry()),
    ).run("Analiza necesidades", {"telemetry": telemetry})

    assert result.ok and executor.calls == 1
    assert result.executed_tools == ["consultar_estado_stock"]
    assert result.research_completion_reason == "REPEATED_CACHED_READ"
    assert result.final_answer_source == "PROVIDER_FINAL_RESPONSE"
    assert engine.requests[-1].allowed_tools == []
    assert engine.requests[-1].limits["max_tool_calls"] == 4
    cached_payloads = [
        message["content"]
        for request in engine.requests[2:]
        for message in request.messages
        if message.get("type") == "TOOL_DATA"
        and message.get("content", {}).get("status") == "CACHED_RESULT_AVAILABLE"
    ]
    assert cached_payloads and all("items" not in payload for payload in cached_payloads)
    cached_events = [event for event in telemetry.events if event.get("tool_call_disposition") == "CACHED"]
    assert [event["consecutive_cache_hits"] for event in cached_events] == [1, 2]
    assert all(event["repeated_without_new_evidence"] is True for event in cached_events)
    assert all(event["remaining_tool_budget"] == 3 for event in cached_events)


def test_cache_a_b_a_no_activa_corte_por_repeticion_consecutiva():
    call_a = ToolCall("consultar_estado_stock", {"terminos": ["ART-A"]}, "a")
    call_b = ToolCall("consultar_estado_stock", {"terminos": ["ART-B"]}, "b")
    engine = _TurnsEngine(
        AgentTurnResult(TOOL_CALL, tool_calls=[call_a]),
        AgentTurnResult(TOOL_CALL, tool_calls=[call_b]),
        AgentTurnResult(TOOL_CALL, tool_calls=[call_a]),
        AgentTurnResult(FINAL_RESPONSE, text="Final con A y B."),
    )
    result = HostAIAgent(
        engine, _Executor(), HostAIToolCatalog(build_default_tool_registry()),
    ).run("Compara A y B")

    assert result.ok and result.executed_tools == ["consultar_estado_stock", "consultar_estado_stock"]
    assert result.research_completion_reason != "REPEATED_CACHED_READ"
    assert engine.requests[-1].allowed_tools


def test_recipe_completion_batch_articulos_llega_a_stock_y_compras_con_budget_cuatro():
    terms = [f"Ingrediente {index}" for index in range(10)]
    article_ids = [f"ART-{index}" for index in range(10)]
    engine = _TurnsEngine(
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("buscar_articulos", {"terminos": terms}, "articles")]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_estado_stock", {"terminos": article_ids}, "stock")]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_compras_pendientes", {}, "purchases")]),
        AgentTurnResult(FINAL_RESPONSE, text="Receta contrastada con articulos, stock y compras."),
    )

    class RecipeExecutor:
        def __init__(self): self.calls = []
        def execute_agent_read(self, tool_id, arguments):
            self.calls.append((tool_id, dict(arguments)))
            if tool_id == "buscar_articulos":
                data = {"resultados": [
                    {"termino": term, "estado": "OK", "article_id": article_id}
                    for term, article_id in zip(terms, article_ids)
                ], "batch_size": 10}
            elif tool_id == "consultar_estado_stock":
                data = {"items": [{"termino": article_id, "estado": "OK"} for article_id in article_ids], "batch_size": 10}
            else:
                data = {"pedidos": []}
            return SimpleNamespace(estado="OK", datos={**data, "datos_reales_modificados": False})

    telemetry = _Telemetry()
    executor = RecipeExecutor()
    result = HostAIAgent(
        engine, executor, HostAIToolCatalog.for_general_agent(build_default_tool_registry()),
    ).run(
        "Propón una receta y contrasta ingredientes, stock y compras",
        {"workflow": {"workflow_type": "recipe_completion"}, "telemetry": telemetry},
    )

    assert result.ok and result.executed_tools == [
        "buscar_articulos", "consultar_estado_stock", "consultar_compras_pendientes",
    ]
    assert [tool_id for tool_id, _arguments in executor.calls] == result.executed_tools
    assert executor.calls[0][1]["terminos"] == terms
    assert executor.calls[1][1]["terminos"] == article_ids
    assert engine.requests[-1].limits["max_tool_calls"] == 4
    attempt = next(event for event in telemetry.events if event["event_type"] == "general_agent_attempt")
    assert attempt["initial_tool_budget"] == 4


def test_receta_ocho_ingredientes_concluye_en_un_turno_con_batch_y_telemetria():
    terms = [f"ART-{index}" for index in range(8)]
    telemetry = _Telemetry()
    engine = _TurnsEngine(
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_escandallos", {"consulta": "detalle", "termino": "Ensaladilla de gamba"}, "recipe")]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_estado_stock", {"terminos": terms}, "stock")]),
        AgentTurnResult(FINAL_RESPONSE, text="Hay stock suficiente para las 10 raciones; se comprobaron los 8 ingredientes."),
    )

    class Executor:
        def execute_agent_read(self, tool_id, arguments):
            if tool_id == "consultar_escandallos":
                return SimpleNamespace(estado="OK", datos={"ingredientes": terms, "rendimiento": 10})
            return SimpleNamespace(estado="OK", datos={"items": [{"termino": term, "estado": "OK"} for term in terms], "batch_size": 8, "resultados_parciales": False, "datos_reales_modificados": False})

    result = HostAIAgent(engine, Executor(), HostAIToolCatalog.for_general_agent(build_default_tool_registry())).run(
        "Con el stock actual, ¿podemos preparar 10 raciones?", {"telemetry": telemetry},
    )
    assert result.ok and result.steps == 3
    assert result.executed_tools == ["consultar_escandallos", "consultar_estado_stock"]
    assert "8 ingredientes" in result.text and "límite" not in result.text
    attempt = next(event for event in telemetry.events if event["event_type"] == "general_agent_attempt")
    batch = next(event for event in telemetry.events if event["event_type"] == "agent_tool_result" and event["tool_id"] == "consultar_estado_stock")
    assert attempt["initial_tool_budget"] == 4 and attempt["remaining_tool_budget"] == 4
    assert batch["batch_size"] == 8 and batch["partial_results"] is False and batch["remaining_tool_budget"] == 2


def test_pedido_cuatro_articulos_concluye_en_un_turno_con_batch():
    terms = [f"ART-PED-{index}" for index in range(4)]
    engine = _TurnsEngine(
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_compras_pendientes", {"consulta": "pedido", "proveedor": "SARDA"}, "purchase")]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_estado_stock", {"terminos": terms}, "stock")]),
        AgentTurnResult(FINAL_RESPONSE, text="Comprobados los 4 artículos; uno tiene poco stock."),
    )

    class Executor:
        def execute_agent_read(self, tool_id, _arguments):
            data = {"pedidos": [{"lineas": [{"articulo_id": term} for term in terms]}]} if tool_id == "consultar_compras_pendientes" else {"items": [{"termino": term, "estado": "OK"} for term in terms], "batch_size": 4}
            return SimpleNamespace(estado="OK", datos={**data, "datos_reales_modificados": False})

    result = HostAIAgent(engine, Executor(), HostAIToolCatalog.for_general_agent(build_default_tool_registry())).run("¿Alguno tiene poco stock?")
    assert result.ok and result.executed_tools == ["consultar_compras_pendientes", "consultar_estado_stock"]
    assert "4 artículos" in result.text and "pendiente" not in result.text.lower()
