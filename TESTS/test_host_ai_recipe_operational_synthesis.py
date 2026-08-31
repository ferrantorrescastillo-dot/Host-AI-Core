from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_operational_synthesis import HostAIOperationalSynthesis
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


def _evidence(*, relation="RESUELTO", required=2, need_unit="kg", stock=1, stock_unit="kg", confirmed=0, draft=0):
    article_id = "ART-1" if relation == "RESUELTO" else None
    orders = []
    if confirmed:
        orders.append({"estado": "confirmado", "lineas": [{"articulo_id": "ART-1", "unidad": need_unit, "pendiente": confirmed}]})
    if draft:
        orders.append({"estado": "borrador", "lineas": [{"articulo_id": "ART-1", "unidad": need_unit, "pendiente": draft}]})
    search = {"termino": "Ingrediente", "estado": relation, "article_id": article_id, "nombre": "Artículo"}
    return [
        {"propuesta_ingredientes": [{"ingrediente": "Ingrediente", "cantidad": required, "unidad": need_unit}]},
        {"resultados": [search]},
        {"existencias": [] if stock is None else [{"articulo_id": "ART-1", "cantidad": stock, "unidad": stock_unit}]},
        {"pedidos": orders},
    ]


@pytest.mark.parametrize(("kwargs", "state", "net"), [
    ({"required": 1, "stock": 2}, "CUBIERTO", 0.0),
    ({"required": 2, "stock": 1}, "COMPRAR", 1.0),
    ({"required": 2, "stock": 1, "confirmed": 1}, "CUBIERTO", 0.0),
    ({"required": 2, "stock": 1, "draft": 1}, "COMPRAR", 1.0),
])
def test_clasificacion_determinista_compra_cobertura_y_borradores(kwargs, state, net):
    row = HostAIOperationalSynthesis.ingredient_states(_evidence(**kwargs))[0]
    assert row["estado_operativo"] == state
    assert row["necesidad_neta"] == net


def test_stock_desconocido_ambiguo_y_no_encontrado_son_estados_seguros():
    unknown = HostAIOperationalSynthesis.ingredient_states(_evidence(stock=None))[0]
    ambiguous = HostAIOperationalSynthesis.ingredient_states(_evidence(relation="AMBIGUO"))[0]
    missing = HostAIOperationalSynthesis.ingredient_states(_evidence(relation="NO_ENCONTRADO"))[0]
    assert unknown["estado_operativo"] == "VERIFICAR_STOCK"
    assert ambiguous["estado_operativo"] == "CONFIRMAR_ARTICULO"
    assert missing["estado_operativo"] == "SIN_ARTICULO"
    assert ambiguous["necesidad_neta"] is missing["necesidad_neta"] is None


def test_busqueda_resuelta_sin_necesidad_estructurada_no_inventa_compra_ni_cobertura():
    summary = HostAIOperationalSynthesis.summarize([{
        "resultados": [{"termino": "Leche", "estado": "RESUELTO", "article_id": "ART-1"}],
    }, {
        "existencias": [{"articulo_id": "ART-1", "cantidad": 5, "unidad": "kg"}],
    }, {"pedidos": []}])
    row = summary["ingredient_states"][0]
    assert row["estado_operativo"] == "VERIFICAR_STOCK"
    assert row["necesidad_neta"] is None


def test_leche_litros_y_stock_kilos_sin_conversion_es_unidad_incompatible():
    row = HostAIOperationalSynthesis.ingredient_states(
        _evidence(required=1.25, need_unit="l", stock=5, stock_unit="kg")
    )[0]
    assert row["estado_operativo"] == "UNIDAD_INCOMPATIBLE"
    assert row["unidades_compatibles"] is False
    assert row["necesidad_neta"] is None


def test_conversion_metrica_canonica_existente_se_reutiliza():
    row = HostAIOperationalSynthesis.ingredient_states(
        _evidence(required=1, need_unit="kg", stock=1000, stock_unit="g")
    )[0]
    assert row["estado_operativo"] == "CUBIERTO"
    assert row["stock_utilizable"] == 1.0


def test_forced_budget_synthesis_entrega_estados_canonicos_al_provider():
    states = [
        ("A", "AMBIGUO", None), ("B", "NO_ENCONTRADO", None),
        ("C", "RESUELTO", "ART-C"), ("D", "RESUELTO", "ART-D"),
        ("E", "RESUELTO", "ART-E"), ("F", "RESUELTO", "ART-F"),
    ]

    class Engine:
        def __init__(self):
            self.requests = []
            self.turns = [
                AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("buscar_articulos", {"termino": f"paso-{index}"}, f"c{index}")])
                for index in range(4)
            ] + [AgentTurnResult(FINAL_RESPONSE, text="Síntesis final controlada.")]

        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            return self.turns.pop(0)

    class Executor:
        def __init__(self): self.index = 0
        def execute_agent_read(self, _tool_id, _arguments):
            self.index += 1
            if self.index > 1:
                return SimpleNamespace(estado="OK", datos={"estado": "OK", "datos_reales_modificados": False}, contexto_actualizado={}, duracion_ms=0)
            return SimpleNamespace(estado="OK", datos={
                "propuesta_ingredientes": [
                    {"ingrediente": name, "cantidad": 1, "unidad": "l" if name == "D" else "kg"}
                    for name, _state, _article_id in states
                ],
                "resultados": [
                    {"termino": name, "estado": state, "article_id": article_id}
                    for name, state, article_id in states
                ],
                "existencias": [
                    {"articulo_id": "ART-D", "cantidad": 5, "unidad": "kg"},
                    {"articulo_id": "ART-E", "cantidad": 2, "unidad": "kg"},
                    {"articulo_id": "ART-F", "cantidad": 0.5, "unidad": "kg"},
                ],
                "pedidos": [],
                "datos_reales_modificados": False,
            }, contexto_actualizado={}, duracion_ms=0)

    engine = Engine()
    result = HostAIAgent(
        engine, Executor(), HostAIToolCatalog.for_general_agent(build_default_tool_registry()),
    ).run("Proponer una receta con IA y comprobar artículos, stock y compras", {
        "workflow": {"workflow_type": "recipe_completion", "objective": "Completar propuesta"},
    })

    assert result.final_answer_source == "FORCED_BUDGET_SYNTHESIS"
    assert engine.requests[-1].allowed_tools == []
    summary_message = next(item for item in engine.requests[-1].messages if item.get("operational_summary") is True)
    assert "estado_operativo es un HECHO CANONICO" in summary_message["content"]
    payload = json.loads(summary_message["content"].rsplit(". ", 1)[1])
    assert payload["state_counts"] == {
        "COMPRAR": 1, "CUBIERTO": 1, "VERIFICAR_STOCK": 1,
        "CONFIRMAR_ARTICULO": 1, "SIN_ARTICULO": 1, "UNIDAD_INCOMPATIBLE": 1,
    }
    assert [item["estado_operativo"] for item in result.context_updates["operational_ingredient_states"]] == [
        "CONFIRMAR_ARTICULO", "SIN_ARTICULO", "VERIFICAR_STOCK",
        "UNIDAD_INCOMPATIBLE", "CUBIERTO", "COMPRAR",
    ]
