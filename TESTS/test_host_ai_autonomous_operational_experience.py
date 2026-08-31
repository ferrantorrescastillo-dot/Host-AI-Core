from __future__ import annotations

from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_conversation_brain import HostAIConversationBrain
from SERVICIOS.host_ai_operational_synthesis import HostAIOperationalSynthesis, MISSING_RECIPE_OPTIONS
from SERVICIOS.host_ai_operational_needs_read_service import HostAIOperationalNeedsReadService
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.menu_necesidades_service import MenuNecesidadesService


def _evidence(required=10, available=10, *, confirmed=0, draft=0, stock_unit="kg"):
    orders = []
    if confirmed:
        orders.append({"estado": "confirmado", "lineas": [{"articulo_id": "ART-1", "unidad": "kg", "pendiente": confirmed}]})
    if draft:
        orders.append({"estado": "borrador", "lineas": [{"articulo_id": "ART-1", "unidad": "kg", "pendiente": draft}]})
    return [
        {"necesidades": {"lines": [{"articulo_id": "ART-1", "articulo_nombre": "Patata", "cantidad_necesaria": required, "unidad_necesaria": "kg"}]}},
        {"existencias": [{"articulo_id": "ART-1", "disponible": available, "unidad": stock_unit}]},
        {"pedidos": orders},
    ]


def test_menu_cubierto_no_genera_compra():
    result = HostAIOperationalSynthesis.summarize(_evidence(required=5, available=5))
    assert result["covered_count"] == 1
    assert result["purchase_required"] == []


def test_menu_con_faltante_genera_solo_necesidad_neta():
    result = HostAIOperationalSynthesis.summarize(_evidence(required=10, available=4, confirmed=3))
    assert result["purchase_required"] == [{
        "articulo_id": "ART-1", "nombre": "Patata", "necesidad": 10.0,
        "stock_utilizable": 4.0, "compra_confirmada_pendiente": 3.0,
        "necesidad_neta": 3.0, "unidad": "kg",
    }]


def test_borrador_no_cuenta_como_cobertura_confirmada():
    result = HostAIOperationalSynthesis.summarize(_evidence(required=10, available=4, draft=3))
    assert result["purchase_required"][0]["necesidad_neta"] == 6.0
    assert result["draft_orders_not_coverage"] == [{"articulo_id": "ART-1", "unidad": "kg", "cantidad": 3.0}]


def test_compra_neta_se_agrupa_por_proveedor_y_resuelve_accion_segun_pedido():
    needs = {"menu_id": "MENU-1", "lines": [
        {"articulo_id": "A1", "articulo_nombre": "Azúcar", "cantidad_necesaria": 1, "necesidad_neta": 1, "unidad_necesaria": "kg", "proveedor_preferente": "SARDA"},
        {"articulo_id": "A2", "articulo_nombre": "Maizena", "cantidad_necesaria": 2, "necesidad_neta": 2, "unidad_necesaria": "kg", "proveedor_preferente": "SARDA"},
        {"articulo_id": "A3", "articulo_nombre": "Huevos", "cantidad_necesaria": 12, "necesidad_neta": 12, "unidad_necesaria": "u", "proveedor_preferente": "PAU GAVALDA"},
        {"articulo_id": "A4", "articulo_nombre": "Sal", "cantidad_necesaria": 1, "necesidad_neta": 1, "unidad_necesaria": "kg"},
    ]}
    orders = [
        {"pedido_id": "PED-1", "proveedor_nombre": "SARDA", "estado": "preparado", "lineas": [{"articulo_id": "A1"}]},
        {"pedido_id": "PED-2", "proveedor_nombre": "PAU GAVALDA", "estado": "borrador", "lineas": [{"articulo_id": "A3", "pendiente": 12, "unidad": "u"}]},
        {"pedido_id": "PED-IRRELEVANTE", "proveedor_nombre": "MAKRO", "estado": "borrador", "lineas": [{"articulo_id": "OTRO", "pendiente": 20, "unidad": "kg"}]},
    ]
    result = HostAIOperationalSynthesis.summarize([{"necesidades": needs}, {"pedidos": orders}])

    groups = {item["proveedor"]: item for item in result["purchase_groups"]}
    assert len(groups["SARDA"]["articulos"]) == 2
    assert groups["SARDA"]["action"] == {"type": "OPEN_ORDER", "label": "Abrir pedido", "pedido_id": "PED-1"}
    assert groups["PAU GAVALDA"]["action"] == {"type": "OPEN_ORDER", "label": "Abrir borrador", "pedido_id": "PED-2"}
    assert groups["PAU GAVALDA"]["pedido_relacionado"]["lineas_relevantes"] == [{"articulo_id": "A3", "nombre": "Huevos", "cantidad_prevista": 12.0, "unidad": "u", "cubriria_necesidad": True}]
    assert "MAKRO" not in groups
    assert groups["Sin proveedor asignado"]["action"] is None
    assert result["draft_orders_not_coverage"] == [{"articulo_id": "A3", "unidad": "u", "cantidad": 12.0}]


def test_tres_proveedores_sin_pedido_ofrecen_preview_del_menu_sin_write():
    lines = [{"articulo_id": f"A{index}", "nombre": f"Artículo {index}", "cantidad_necesaria": index, "necesidad_neta": index, "unidad_necesaria": "kg", "proveedor_preferente": provider} for index, provider in enumerate(("P1", "P2", "P3"), 1)]
    result = HostAIOperationalSynthesis.summarize([{"necesidades": {"menu_id": "MENU-2", "lines": lines}}, {"pedidos": []}])

    assert len(result["purchase_groups"]) == 3
    assert all(group["action"] == {"type": "PREPARE_ORDER", "label": "Preparar pedido", "menu_id": "MENU-2"} for group in result["purchase_groups"])
    assert result["datos_reales_modificados"] is False


def test_unidades_incompatibles_no_se_convierten_ni_generan_compra_falsa():
    result = HostAIOperationalSynthesis.summarize(_evidence(required=10, available=20, stock_unit="l"))
    assert result["purchase_required"] == []
    assert result["incidents"] == [{"articulo_id": "ART-1", "reason": "STOCK_NOT_COMPARABLE", "unidad": "kg"}]


def test_stock_desconocido_no_genera_compra_y_borrador_no_lo_convierte_en_cubierto():
    evidence = _evidence(required=10, available=10, draft=3)
    evidence[1] = {"existencias": [{"articulo_id": "ART-1", "disponible": None, "unidad": "kg"}]}
    result = HostAIOperationalSynthesis.summarize(evidence)

    assert result["purchase_required"] == []
    assert result["covered_count"] == 0
    assert result["incidents"] == [{"articulo_id": "ART-1", "reason": "STOCK_NOT_COMPARABLE", "unidad": "kg"}]
    assert result["draft_orders_not_coverage"] == []


def test_receta_inexistente_ofrece_cinco_opciones_y_ambigua_no_autoselecciona():
    missing = HostAIOperationalSynthesis.missing_recipe_resolution("NO_ENCONTRADO")
    ambiguous = HostAIOperationalSynthesis.missing_recipe_resolution("AMBIGUO", [{"id": "R1"}, {"id": "R2"}])
    assert missing["options"] == MISSING_RECIPE_OPTIONS
    assert "Proponer una receta con IA" in missing["options"]
    assert ambiguous == {"state": "AMBIGUO", "candidates": [{"id": "R1"}, {"id": "R2"}], "auto_selected": False}


def test_objetivo_operativo_continua_en_turnos_siguientes():
    brain = HostAIConversationBrain()
    _route, first = brain.prepare_turn("Investiga el evento, producción, recetas y stock")
    _route, followup = brain.prepare_turn("Crear la receta conmigo", first.to_dict())
    assert first.workflow_type == "operational_research"
    assert followup.workflow_type == "operational_research"
    assert followup.objective == first.objective


def test_write_sigue_exigiendo_confirmacion_explicita():
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    confirm = next(item for item in tools if item["tool_id"] == "confirmar_cambio_articulo")
    preview = next(item for item in tools if item["tool_id"] == "preparar_formato_articulo")
    assert confirm["confirmation_policy"] == preview["confirmation_policy"] == "EXPLICIT_HUMAN"


def test_agente_entrega_opciones_de_hueco_y_presentacion_operativa_al_provider():
    class Engine:
        def __init__(self):
            self.requests = []
            self.turns = [
                AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_escandallos", {"consulta": "buscar", "termino": "receta ausente"}, "c1")]),
                AgentTurnResult(FINAL_RESPONSE, text="Necesito que elijas cómo resolver la receta."),
            ]
        def ejecutar_turn_agente(self, request):
            self.requests.append(request); return self.turns.pop(0)

    class Executor:
        def execute_agent_read(self, _tool_id, _arguments):
            return SimpleNamespace(estado="OK", datos={"estado": "NO_ENCONTRADO", "candidatos": [], "datos_reales_modificados": False}, contexto_actualizado={}, duracion_ms=0)

    engine = Engine()
    result = HostAIAgent(engine, Executor(), HostAIToolCatalog.for_general_agent(build_default_tool_registry())).run(
        "Investiga la receta y revisa producción",
        {"workflow": {"workflow_type": "operational_research", "objective": "Analizar el menú completo"}},
    )
    tool_data = next(item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    assert result.ok
    assert tool_data["content"]["missing_recipe_resolution"]["options"] == MISSING_RECIPE_OPTIONS
    assert tool_data["content"]["root_goal"] == "MENU_ANALYSIS"
    assert tool_data["content"]["pending_issue"] == "MISSING_RECIPE"
    assert result.context_updates["root_goal"] == "MENU_ANALYSIS"
    assert "faltantes reales" in engine.requests[0].system_instructions
    assert "borradores" in engine.requests[0].system_instructions


def test_necesidades_read_resta_solo_compras_confirmadas(tmp_path):
    class Needs:
        def necesidades(self, _menu_id):
            return {"ok": True, "necesidades": {"lines": [{
                "articulo_id": "ART-1", "articulo_nombre": "Patata", "unidad_necesaria": "kg",
                "cantidad_necesaria": 10, "stock_disponible": 4, "cantidad_faltante": 6,
                "formato_compra": "bolsa", "cantidad_formato": 1, "proveedor_preferente": "Proveedor",
                "precio_estimado": .82, "unidad_precio": "kg",
            }], "summary": {"articulos": 1}}}

    class Purchases:
        def consultar_pedidos(self, **_kwargs):
            return {"pedidos": [
                {"estado": "preparado", "lineas": [{"articulo_id": "ART-1", "unidad": "kg", "pendiente": 2}]},
                {"estado": "borrador", "lineas": [{"articulo_id": "ART-1", "unidad": "kg", "pendiente": 3}]},
            ]}

    result = HostAIOperationalNeedsReadService(tmp_path, needs=Needs(), purchases=Purchases()).consultar_menu("MENU-1")
    line = result["necesidades"]["lines"][0]
    assert line["necesidad_neta"] == 4
    assert line["borradores_pendientes"] == 3
    assert line["precio_unitario"] == .82
    assert line["coste_neto"] == 3.28
    assert result["borradores_cuentan_como_cobertura"] is False
    assert result["datos_reales_modificados"] is False


def test_coste_neto_preciso_y_unidad_incompatible_no_inventa_coste(tmp_path):
    class Needs:
        def __init__(self, price_unit): self.price_unit = price_unit
        def necesidades(self, _menu_id):
            return {"ok": True, "necesidades": {"menu_id": "MENU-PBD", "lines": [{
                "articulo_id": "ART-AZUCAR", "articulo_nombre": "Azúcar", "unidad_necesaria": "kg",
                "cantidad_necesaria": .1, "stock_disponible": 0, "cantidad_faltante": .1,
                "proveedor_preferente": "SARDA", "precio_estimado": .82, "unidad_precio": self.price_unit,
            }], "summary": {"articulos": 1}}}
    class Purchases:
        def consultar_pedidos(self, **_kwargs): return {"pedidos": []}

    compatible = HostAIOperationalNeedsReadService(tmp_path, needs=Needs("kg"), purchases=Purchases()).consultar_menu("MENU-PBD")["necesidades"]["lines"][0]
    incompatible = HostAIOperationalNeedsReadService(tmp_path, needs=Needs("u"), purchases=Purchases()).consultar_menu("MENU-PBD")["necesidades"]["lines"][0]
    assert compatible["coste_neto"] == .082
    assert incompatible["coste_neto"] is None


def test_necesidades_read_conserva_borrador_relevante_para_accion_sin_restarlo(tmp_path):
    class Needs:
        def necesidades(self, _menu_id):
            return {"ok": True, "necesidades": {"menu_id": "MENU-PBD", "lines": [{
                "articulo_id": "ART-AZUCAR", "articulo_nombre": "Azúcar", "unidad_necesaria": "kg",
                "cantidad_necesaria": .1, "stock_disponible": 0, "cantidad_faltante": .1,
                "proveedor_preferente": "SARDA", "precio_estimado": .82, "unidad_precio": "kg",
            }]}}

    class Purchases:
        def consultar_pedidos(self, **_kwargs):
            return {"pedidos": [{
                "pedido_id": "PED-0AD463508C", "proveedor_nombre": "SARDA", "estado": "borrador",
                "lineas": [{"articulo_id": "ART-AZUCAR", "nombre": "Azúcar", "unidad": "kg", "pendiente": .2}],
            }]}

    read = HostAIOperationalNeedsReadService(tmp_path, needs=Needs(), purchases=Purchases()).consultar_menu("MENU-PBD")
    summary = HostAIOperationalSynthesis.summarize([read])

    line = read["necesidades"]["lines"][0]
    group = summary["purchase_groups"][0]
    assert line["necesidad_neta"] == .1
    assert line["borradores_pendientes"] == .2
    assert group["action"] == {"type": "OPEN_ORDER", "label": "Abrir borrador", "pedido_id": "PED-0AD463508C"}
    assert group["pedido_relacionado"]["lineas_relevantes"][0]["cubriria_necesidad"] is True
    assert group["articulos"][0]["formato"] is None


def test_unidad_de_medida_no_se_presenta_como_formato_comercial():
    assert MenuNecesidadesService._commercial_format("kg") is None
    assert MenuNecesidadesService._commercial_format("bolsa 1 kg") == "bolsa 1 kg"


def test_necesidades_operativas_expuesta_como_read():
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    tool = next(item for item in tools if item["tool_id"] == "consultar_necesidades_operativas")
    assert tool["type"] == "READ" and tool["confirmation_policy"] == "NONE"


def test_propuesta_ia_cruza_articulo_y_finaliza_en_modelo_sin_write():
    class Engine:
        def __init__(self):
            self.requests = []
            self.turns = [
                AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("buscar_articulos", {"termino": "cebolla"}, "a1")]),
                AgentTurnResult(FINAL_RESPONSE, text="PROPUESTA GENERADA POR IA, no registrada. Cebolla: RESUELTO."),
            ]
        def ejecutar_turn_agente(self, request):
            self.requests.append(request); return self.turns.pop(0)

    class Executor:
        def execute_agent_read(self, _tool_id, _arguments):
            return SimpleNamespace(estado="OK", datos={"estado": "EXACT", "articulos": [{"article_id": "ART-1", "nombre": "Cebolla"}]}, contexto_actualizado={}, duracion_ms=0)

    result = HostAIAgent(Engine(), Executor(), HostAIToolCatalog.for_general_agent(build_default_tool_registry())).run(
        "Proponer una receta con IA para una crema de cebolla",
        {"workflow": {"workflow_type": "recipe_completion", "objective": "Preparar propuesta IA"}},
    )
    assert result.executed_tools == ["buscar_articulos"]
    assert result.final_answer_source == "PROVIDER_FINAL_RESPONSE"
    assert "no registrada" in result.text and result.datos_reales_modificados is False


def test_guia_editorial_prioriza_accion_y_oculta_ruido_tecnico():
    class Engine:
        def __init__(self): self.requests = []
        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            return AgentTurnResult(FINAL_RESPONSE, text="## Comprar\nUn faltante.\n\n## Detalle\nEl resto está cubierto.")

    engine = Engine()
    result = HostAIAgent(engine, SimpleNamespace(), HostAIToolCatalog.for_general_agent(build_default_tool_registry())).run(
        "Analiza el menú completo, revisa stock y compras",
        {"workflow": {"workflow_type": "operational_research", "objective": "Analizar menú"}},
    )
    guidance = engine.requests[0].system_instructions.casefold()
    concepts = {
        "purchase_before_detail": guidance.index("compra antes") < guidance.index("detalle descriptivo"),
        "covered_as_summary": "elementos cubiertos en una cifra" in guidance,
        "group_incidents": "agrupa incidencias repetidas" in guidance,
        "hide_identifiers": "oculta por defecto ids" in guidance,
        "canonical_pack_only": "formato canonico" in guidance and "no aparece en los datos" in guidance,
    }
    assert all(concepts.values())
    assert result.final_answer_source == "PROVIDER_FINAL_RESPONSE"
    assert result.text.index("Comprar") < result.text.index("Detalle")


def test_guia_editorial_de_propuesta_separa_compra_stock_relacion_sin_articulo_y_cubierto():
    class Engine:
        def __init__(self): self.request = None
        def ejecutar_turn_agente(self, request):
            self.request = request
            return AgentTurnResult(FINAL_RESPONSE, text="Propuesta clasificada sin compras no demostradas.")

    engine = Engine()
    result = HostAIAgent(
        engine, SimpleNamespace(), HostAIToolCatalog.for_general_agent(build_default_tool_registry()),
    ).run(
        "Proponer una receta con IA y revisar articulos, stock y compras",
        {"workflow": {"workflow_type": "recipe_completion", "objective": "Preparar propuesta IA"}},
    )
    guidance = engine.request.system_instructions.casefold()

    assert result.ok and result.datos_reales_modificados is False
    assert "comprar exige una necesidad neta positiva demostrada" in guidance
    assert "verificar stock antes de comprar" in guidance
    assert "confirmar articulo" in guidance and "candidato posible" in guidance
    assert "sin articulo localizado" in guidance
    assert "pertenece a cubierto" in guidance
    assert "nunca afirmes que uno 'es la opcion adecuada'" in guidance
    assert "no convierten stock desconocido en cubierto" in guidance
    assert "no las conviertas en una plantilla rigida" in guidance


def test_consulta_simple_conserva_respuesta_breve_del_modelo():
    class Engine:
        def __init__(self):
            self.request = None
            self.turns = [
                AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "s1")]),
                AgentTurnResult(FINAL_RESPONSE, text="Tienes 2 kg disponibles."),
            ]
        def ejecutar_turn_agente(self, request):
            self.request = request
            return self.turns.pop(0)

    class Executor:
        def execute_agent_read(self, _tool_id, _arguments):
            return SimpleNamespace(estado="OK", datos={"existencias": [{"cantidad": 2, "unidad": "kg"}]}, contexto_actualizado={}, duracion_ms=0)

    engine = Engine()
    result = HostAIAgent(engine, Executor(), HostAIToolCatalog.for_general_agent(build_default_tool_registry())).run(
        "¿Cuánto stock tengo?",
    )
    assert result.text.count("\n") == 0
    assert "consulta simple" in engine.request.system_instructions.casefold()
