from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentRunResult, AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_escandallos_read_service import HostAIEscandallosReadService
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell


class _SingleFinalEngine:
    def __init__(self, turn): self.turn = turn
    def ejecutar_turn_agente(self, _request): return self.turn


def _fixture(base: Path) -> None:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos_canonicos.json").write_text(json.dumps({
        "schema_version": "1.0",
        "escandallos": [
            {
                "receta": {
                    "codigo": "REC-ARROZ-MELOSO", "nombre": "Arroz meloso", "rendimiento": 10,
                    "unidad_rendimiento": "raciones", "ingredientes": [
                        {"articulo_id": "ART-ARROZ", "nombre": "Arroz", "cantidad": 2, "unidad": "kg"},
                        {"nombre": "Caldo sin precio", "cantidad": 3.5, "unidad": "l"},
                    ],
                },
                "coste_total": None,
            },
            {
                "receta": {
                    "codigo": "REC-ARROZ-MELOSO-VEG", "nombre": "Arroz meloso vegetal",
                    "rendimiento": 8, "unidad_rendimiento": "raciones",
                    "ingredientes": [{"nombre": "Verduras", "cantidad": None, "unidad": "kg"}],
                },
                "coste_total": None,
            },
            {
                "receta": {
                    "codigo": "REC-PADRE-VINAGRETA",
                    "nombre": "CALÇOTADA EN MESA A COMPARTIR ENSALADA VERDE",
                    "rendimiento": 1,
                    "unidad_rendimiento": "u",
                    "ingredientes": [{
                        "articulo_id": "ART-VINAGRETA", "nombre": "Vinagreta clasica",
                        "cantidad": 0.02, "unidad": "kg",
                        "metadata": {"tipo": "ELABORACION", "referencia_elaboracion": "VINAGRETA CLASICA"},
                    }],
                },
                "coste_total": None,
            },
            {
                "receta": {
                    "codigo": "REC-EXCEL-AD9995FDE1", "nombre": "VINAGRETA CLASICA",
                    "rendimiento": 1, "unidad_rendimiento": "kg",
                    "ingredientes": [{"articulo_id": "ART-ACEITE", "nombre": "Aceite", "cantidad": 1, "unidad": "kg"}],
                },
                "coste_total": None,
            },
            {
                "receta": {
                    "codigo": "REC-PADRE-CREMA", "nombre": "Crema Catalana quemada con carquiñoli",
                    "rendimiento": 1, "unidad_rendimiento": "u",
                    "ingredientes": [{
                        "articulo_id": "ART-CREMA", "nombre": "Crema Catalana",
                        "cantidad": 1, "unidad": "kg",
                        "metadata": {"tipo": "ELABORACION", "referencia_elaboracion": "Crema catalana"},
                    }],
                },
                "coste_total": None,
            },
            {
                "receta": {
                    "codigo": "REC-EXCEL-F851AC82AC", "nombre": "Crema catalana",
                    "rendimiento": 1, "unidad_rendimiento": "kg",
                    "ingredientes": [{"nombre": "Leche", "cantidad": 1, "unidad": "l"}],
                },
                "coste_total": None,
            },
            {
                "receta": {
                    "codigo": "REC-GILDA", "nombre": "Vermouth rojo con Gilda MasBoronat",
                    "rendimiento": 1, "unidad_rendimiento": "u",
                    "ingredientes": [{
                        "articulo_id": "ART000348", "nombre": "Gilda MasBoronat",
                        "cantidad": 1, "unidad": "u",
                        "metadata": {"tipo": "ARTICULO", "referencia_elaboracion": None},
                    }],
                },
                "coste_total": None,
            },
        ],
    }, ensure_ascii=False), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "ART-ARROZ", "nombre": "Arroz", "precio": 4.123456, "unidad": "kg"},
        {"codigo": "ART-VINAGRETA", "nombre": "Vinagreta clasica", "precio": 2, "unidad": "kg"},
        {"codigo": "ART-CREMA", "nombre": "Crema Catalana", "precio": 3, "unidad": "kg"},
        {"codigo": "ART000348", "nombre": "Gilda MasBoronat", "precio": 1},
        {"codigo": "ART-ACEITE", "nombre": "Aceite", "precio": 2, "unidad": "kg"},
    ]), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = base / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")


def test_consulta_exacta_preserva_ingredientes_costes_y_null(tmp_path: Path) -> None:
    _fixture(tmp_path)
    before = (tmp_path / "DATOS/db/escandallos_canonicos.json").read_bytes()

    result = HostAIEscandallosReadService(tmp_path).consultar(
        "detalle", termino="Arroz meloso",
    )

    assert result["estado"] == "OK"
    assert result["escandallo"]["id"] == "REC-ARROZ-MELOSO"
    ingredients = result["escandallo"]["ingredientes"]
    assert result["escandallo"]["total_ingredientes"] == 2
    assert result["escandallo"]["ingredientes_limitados"] is False
    assert ingredients[0]["cantidad"] == 2.0 and ingredients[0]["unidad"] == "kg"
    assert ingredients[1]["cantidad"] == 3.5 and ingredients[1]["unidad"] == "l"
    assert ingredients[1]["coste_unitario"] is None
    costs = result["escandallo"]["costes"]
    assert costs["estado_coste"] == "PARCIAL"
    assert costs["coste_total"] is None
    assert costs["coste_total_parcial"] == 8.246912
    assert result["escandallo"]["moneda"] is None
    assert result["datos_reales_modificados"] is False
    assert (tmp_path / "DATOS/db/escandallos_canonicos.json").read_bytes() == before


def test_busqueda_parcial_ambigua_inexistente_y_null_real(tmp_path: Path) -> None:
    _fixture(tmp_path)
    service = HostAIEscandallosReadService(tmp_path)

    ambiguous = service.consultar("detalle", termino="arroz", limite=10)
    assert ambiguous["estado"] == "AMBIGUO"
    assert [item["id"] for item in ambiguous["escandallos"]] == [
        "REC-ARROZ-MELOSO", "REC-ARROZ-MELOSO-VEG",
    ]
    missing = service.consultar("detalle", termino="plato inexistente")
    assert missing["estado"] == "NO_ENCONTRADO" and missing["escandallo"] is None
    vegetable = service.consultar("detalle", escandallo_id="REC-ARROZ-MELOSO-VEG")
    assert vegetable["escandallo"]["ingredientes"][0]["cantidad"] is None


def test_busqueda_general_incluye_receta_sin_escandallo_y_expone_identidad_neutral() -> None:
    class Biblioteca:
        def listar(self, query):
            assert "tiene_escandallo" not in query
            return {"elaboraciones": {"total": 1, "items": [{
                "id": "REC601-000001", "codigo": "REC601-000001",
                "nombre": "SALSA DE CAVA", "estado_coste": "SIN_ESCANDALLO",
                "tiene_receta": True, "tiene_escandallo": False,
            }]}}

        def detalle(self, identity):
            assert identity == "REC601-000001"
            return {"ok": True, "elaboracion": {
                "id": identity, "codigo": identity, "nombre": "SALSA DE CAVA",
                "estado_coste": "SIN_ESCANDALLO", "tiene_receta": True,
                "tiene_escandallo": False, "receta": {}, "escandallo": None,
            }}

    service = HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca())
    listed = service.consultar("buscar", termino="salsa de cava")
    detail = service.consultar("detalle", termino="salsa de cava")

    assert listed["estado"] == "OK"
    assert listed["elaboraciones"][0]["id"] == "REC601-000001"
    assert listed["elaboraciones"][0]["tiene_escandallo"] is False
    assert detail["estado"] == "OK"
    assert detail["elaboracion"]["id"] == "REC601-000001"
    assert detail["elaboracion"]["tiene_escandallo"] is False
    assert detail["datos_reales_modificados"] is False


def test_subelaboraciones_preservan_identidad_y_resuelven_solo_si_es_seguro(tmp_path: Path) -> None:
    _fixture(tmp_path)
    service = HostAIEscandallosReadService(tmp_path)

    vinagreta = service.consultar("detalle", escandallo_id="REC-PADRE-VINAGRETA")["escandallo"]
    line = vinagreta["ingredientes"][0]
    assert line["tipo_componente"] == "ELABORACION"
    assert line["articulo_id"] is None
    assert line["codigo"] is None and line["unidad_base"] is None
    assert line["escandallo_hijo_id"] == "REC-EXCEL-AD9995FDE1"
    assert line["referencia_elaboracion"] == "VINAGRETA CLASICA"
    assert line["coste_linea"] == 0.04
    assert line["estado_coste"] == "COSTE_SUBELABORACION_RESUELTO"
    assert line["trazabilidad_coste"]["fraccion_lote"] == 0.02
    assert "ingredientes" not in line

    crema = service.consultar("detalle", escandallo_id="REC-PADRE-CREMA")["escandallo"]["ingredientes"][0]
    assert crema["tipo_componente"] == "ELABORACION"
    assert crema["articulo_id"] is None
    assert crema["escandallo_hijo_id"] == "REC-EXCEL-F851AC82AC"
    assert crema["referencia_elaboracion"] == "Crema catalana"
    assert crema["coste_linea"] is None


def test_gilda_permanece_articulo_y_conserva_conflicto_u_kg(tmp_path: Path) -> None:
    _fixture(tmp_path)

    detail = HostAIEscandallosReadService(tmp_path).consultar(
        "detalle", escandallo_id="REC-GILDA",
    )["escandallo"]
    line = detail["ingredientes"][0]

    assert line["tipo_componente"] == "ARTICULO"
    assert line["articulo_id"] == "ART000348"
    assert line["escandallo_hijo_id"] is None
    assert line["cantidad"] == 1.0 and line["unidad"] == "u"
    assert line["unidad_base"] == "kg"
    assert line["estado_coste"] == "CONVERSION_NO_DISPONIBLE"


def test_capability_general_agent_es_read_y_no_se_publica_en_catalogo_mcp() -> None:
    registry = build_default_tool_registry()
    internal = HostAIToolCatalog.for_general_agent(registry).effective_tools()
    default = HostAIToolCatalog(registry).effective_tools()
    escandallo = next(item for item in internal if item["tool_id"] == "consultar_escandallos")

    assert escandallo["type"] == "READ"
    assert escandallo["confirmation_policy"] == "NONE"
    assert "consultar_escandallos" not in {item["tool_id"] for item in default}
    assert {
        "consultar_produccion", "consultar_estado_stock", "consultar_compras_pendientes",
        "consultar_escandallos", "consultar_uso_elaboracion", "consultar_menu",
        "abrir_elaboracion", "abrir_articulo", "abrir_menu", "abrir_produccion_ui",
        "abrir_compra",
    } <= {item["tool_id"] for item in internal}
    assert not {"abrir_elaboracion", "abrir_articulo", "abrir_menu", "abrir_produccion_ui", "abrir_compra"} & {
        item["tool_id"] for item in default
    }
    ui_action = next(item for item in internal if item["tool_id"] == "abrir_elaboracion")
    assert ui_action["type"] == "UI_ACTION" and ui_action["confirmation_policy"] == "NONE"
    assert "recalcular_escandallo" not in {item["tool_id"] for item in internal}


def test_argumentos_extra_y_write_se_rechazan() -> None:
    registry = build_default_tool_registry()
    tools = HostAIToolCatalog.for_general_agent(registry).effective_tools()
    policy = HostAIAgentPolicy()
    assert policy.authorize("consultar_escandallos", {"ruta": "DATOS/db/x.json"}, tools) == (
        False, "additional_properties_not_allowed",
    )
    assert policy.authorize("recalcular_escandallo", {}, tools)[0] is False


def test_provider_fake_recibe_dto_como_tool_data_no_confiable(tmp_path: Path) -> None:
    _fixture(tmp_path)
    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(
        registry, escandallos_read_service=HostAIEscandallosReadService(tmp_path),
    )

    class Engine:
        def __init__(self) -> None:
            self.requests = []

        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return AgentTurnResult(TOOL_CALL, tool_calls=[
                    ToolCall("consultar_escandallos", {"consulta": "detalle", "termino": "Arroz meloso"}, "esc-1"),
                ])
            return AgentTurnResult(FINAL_RESPONSE, text="Respuesta libre basada en el escandallo.")

    engine = Engine()
    result = HostAIAgent(
        engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run("¿Cuál es el escandallo de Arroz meloso?")

    assert result.ok and result.executed_tools == ["consultar_escandallos"]
    tool_data = next(item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    assert tool_data["tool_id"] == "consultar_escandallos"
    assert tool_data["untrusted_data"] is True
    assert tool_data["content"]["escandallo"]["id"] == "REC-ARROZ-MELOSO"


def test_follow_up_conserva_respuesta_anterior_sin_forzar_reconsulta() -> None:
    registry = build_default_tool_registry()

    class Engine:
        def __init__(self) -> None:
            self.requests = []

        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            return AgentTurnResult(FINAL_RESPONSE, text="El coste ya estaba en el contexto anterior.")

    engine = Engine()
    result = HostAIAgent(
        engine, SimpleNamespace(), HostAIToolCatalog.for_general_agent(registry),
    ).run("¿Y cuánto me cuesta?", conversation_context={"conversation_history": [
        {"role": "user", "content": "Enséñame el escandallo de Arroz meloso"},
        {"role": "assistant", "content": "El coste parcial registrado es 8,246912; falta un precio."},
    ]})

    assert result.ok and result.executed_tools == []
    assert [item["content"] for item in engine.requests[0].messages] == [
        "Enséñame el escandallo de Arroz meloso",
        "El coste parcial registrado es 8,246912; falta un precio.",
        "¿Y cuánto me cuesta?",
    ]


def test_prompt_real_selecciona_agregacion_global_y_responde_grounded_sin_fallback() -> None:
    class Biblioteca:
        def agregar_costes(self, operation):
            assert operation == "MAX_COSTE_POR_RACION"
            return {
                "ok": True, "agregacion": operation, "estado": "OK",
                "total_evaluadas": 23, "total_validas": 18, "total_excluidas": 5,
                "resultado": [{"receta_id": "REC-CARA", "nombre": "Receta cara", "coste_por_racion": 4.75}],
                "datos_reales_modificados": False,
            }

    class Engine:
        def __init__(self): self.requests = []
        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_escandallos", {"agregacion": "MAX_COSTE_POR_RACION"}, "aggregate")])
            return AgentTurnResult(FINAL_RESPONSE, text="La receta más cara por ración es Receta cara (REC-CARA), con 4,75 por ración.")

    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(registry, escandallos_read_service=HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca()))
    engine = Engine()
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run(
        "¿Cuál es la receta más cara por ración de todas las que tienen coste disponible?",
    )
    assert result.ok and result.executed_tools == ["consultar_escandallos"]
    assert result.safe_error == "" and "REC-CARA" in result.text and "4,75" in result.text
    tool_data = next(item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    assert tool_data["content"]["total_evaluadas"] == 23
    assert tool_data["content"]["resultado"][0]["coste_por_racion"] == 4.75
    assert tool_data["content"]["datos_reales_modificados"] is False


def test_schema_agregacion_es_enum_cerrado_y_listado_sigue_limitado():
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    policy = HostAIAgentPolicy()
    assert policy.authorize("consultar_escandallos", {"agregacion": "MAX_COSTE_POR_RACION"}, tools) == (True, "")
    assert policy.authorize("consultar_escandallos", {"agregacion": "eval(coste)"}, tools) == (False, "invalid_enum:agregacion")
    assert policy.authorize("consultar_escandallos", {"agregacion": "RANK_COSTE_POR_RACION", "orden": "DESC", "posicion": 2}, tools) == (True, "")
    assert policy.authorize("consultar_escandallos", {"agregacion": "RANK_COSTE_POR_RACION", "orden": "SQL", "posicion": 2}, tools) == (False, "invalid_enum:orden")
    assert policy.authorize("consultar_escandallos", {"agregacion": "RANK_COSTE_POR_RACION", "orden": "DESC", "posicion": 0}, tools) == (False, "out_of_range:posicion")
    assert policy.authorize("consultar_escandallos", {"agregacion": "RANK_COSTE_POR_RACION", "orden": "DESC", "posicion": 11}, tools) == (False, "out_of_range:posicion")

    class Biblioteca:
        def listar(self, query):
            assert query["page_size"] == 10
            return {"elaboraciones": {"items": [{"id": f"REC-{index}"} for index in range(10)], "total": 23}}

    listed = HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca()).consultar("listar", limite=10)
    assert len(listed["escandallos"]) == 10 and listed["total_encontrados"] == 23


def test_provider_simulado_resuelve_conteo_incompleto_y_ranking_ordinal() -> None:
    class Biblioteca:
        def agregar_costes(self, operation, **params):
            if operation == "COUNT_COSTE_INCOMPLETO":
                return {
                    "ok": True, "agregacion": operation, "estado": "OK",
                    "total_evaluadas": 27, "total_disponibles": 19,
                    "total_incompletas": 8, "conteo": 8,
                    "desglose": {"PARCIAL": 5, "SIN_COSTE": 3},
                    "datos_reales_modificados": False,
                }
            assert operation == "RANK_COSTE_POR_RACION"
            assert params == {"orden": "DESC", "posicion": 2}
            return {
                "ok": True, "agregacion": operation, "estado": "OK",
                "orden": "DESC", "posicion": 2, "total_evaluadas": 27,
                "total_validas": 19, "total_excluidas": 8, "numero_empates": 1,
                "resultado": [{"receta_id": "REC-SEGUNDA", "nombre": "Segunda", "coste_por_racion": 8.25}],
                "datos_reales_modificados": False,
            }

    class Engine:
        def __init__(self): self.turn = 0
        def ejecutar_turn_agente(self, request):
            self.turn += 1
            if self.turn == 1:
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_escandallos", {"agregacion": "COUNT_COSTE_INCOMPLETO"}, "count")])
            if self.turn == 2:
                return AgentTurnResult(FINAL_RESPONSE, text="Hay 8 recetas con el coste incompleto de 27 evaluadas.")
            if self.turn == 3:
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_escandallos", {"agregacion": "RANK_COSTE_POR_RACION", "orden": "DESC", "posicion": 2}, "rank")])
            return AgentTurnResult(FINAL_RESPONSE, text="La segunda más cara es Segunda (REC-SEGUNDA), a 8,25 por ración.")

    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(registry, escandallos_read_service=HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca()))
    agent = HostAIAgent(Engine(), executor, HostAIToolCatalog.for_general_agent(registry))
    counted = agent.run("¿Cuántas recetas tienen el coste incompleto?")
    ranked = agent.run("¿Cuál es la segunda receta más cara por ración?")
    assert counted.ok and "8 recetas" in counted.text and counted.safe_error == ""
    assert ranked.ok and "REC-SEGUNDA" in ranked.text and ranked.safe_error == ""


def test_follow_up_segunda_conserva_orden_desc_y_asc_en_contexto_del_provider() -> None:
    class Biblioteca:
        def agregar_costes(self, operation, **params):
            assert operation == "RANK_COSTE_POR_RACION" and params["posicion"] == 2
            return {
                "ok": True, "agregacion": operation, "estado": "OK", **params,
                "total_evaluadas": 27, "total_validas": 19, "total_excluidas": 8,
                "numero_empates": 1,
                "resultado": [{"receta_id": f"REC-{params['orden']}", "nombre": params["orden"], "coste_por_racion": 2.0}],
                "datos_reales_modificados": False,
            }

    class Engine:
        def __init__(self, order): self.order, self.requests = order, []
        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                history = " ".join(str(x.get("content") or "") for x in request.messages)
                assert ("más cara" in history) if self.order == "DESC" else ("más barata" in history)
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_escandallos", {"agregacion": "RANK_COSTE_POR_RACION", "orden": self.order, "posicion": 2}, "follow")])
            return AgentTurnResult(FINAL_RESPONSE, text=f"Segundo puesto {self.order} correcto.")

    registry = build_default_tool_registry()
    for order, previous in (("DESC", "La receta más cara es A."), ("ASC", "La receta más barata es B.")):
        engine = Engine(order)
        executor = HostAIToolExecutor(registry, escandallos_read_service=HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca()))
        result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run(
            "¿Y la segunda?", conversation_context={"conversation_history": [
                {"role": "user", "content": "¿Cuál es la más cara?" if order == "DESC" else "¿Cuál es la más barata?"},
                {"role": "assistant", "content": previous},
            ]},
        )
        assert result.ok and order in result.text


def test_schema_listado_economico_filtra_solo_estados_cerrados() -> None:
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    policy = HostAIAgentPolicy()
    valid = {"agregacion": "LIST_COSTE_INCOMPLETO", "estado_coste": "PARCIAL", "pagina": 1, "limite": 10}
    assert policy.authorize("consultar_escandallos", valid, tools) == (True, "")
    invalid = {**valid, "estado_coste": "eval(precio)"}
    assert policy.authorize("consultar_escandallos", invalid, tools) == (False, "invalid_enum:estado_coste")


def test_provider_simulado_count_list_filtros_follow_up_y_detalle_grounded() -> None:
    class Biblioteca:
        def agregar_costes(self, operation):
            assert operation == "COUNT_COSTE_INCOMPLETO"
            return {"ok": True, "agregacion": operation, "total_evaluadas": 27, "total_incompletas": 8, "conteo": 8, "datos_reales_modificados": False}
        def listar_costes_incompletos(self, **params):
            state = params["estado_coste"] or None
            total = 8 if state is None else 4
            return {
                "ok": True, "consulta_economica": "LIST_COSTE_INCOMPLETO", "estado": "OK",
                "filtro_estado_coste": state, "total_evaluadas": 27, "total_coincidencias": total,
                "items_devueltos": total, "truncado": False,
                "resultado": [{"receta_id": f"REC-{state or 'ALL'}", "nombre": "Receta", "estado_coste": state or "PARCIAL", "coste_completo": False}],
                "datos_reales_modificados": False,
            }
        def detalle_coste_incompleto(self, identity):
            assert identity == "REC-PARCIAL"
            return {
                "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO", "estado": "OK",
                "receta_id": identity, "estado_coste": "PARCIAL", "coste_completo": False,
                "explicacion": "El detalle economico expone motivos estructurados.",
                "motivos": [{"tipo": "SIN_PRECIO", "articulo_id": "ART-1", "nombre": "Patata", "detalle": "Sin precio vigente"}],
                "numero_motivos": 1, "datos_reales_modificados": False,
            }

    calls = [
        {"agregacion": "COUNT_COSTE_INCOMPLETO"},
        {"agregacion": "LIST_COSTE_INCOMPLETO"},
        {"agregacion": "LIST_COSTE_INCOMPLETO", "estado_coste": "PARCIAL"},
        {"agregacion": "LIST_COSTE_INCOMPLETO", "estado_coste": "SIN_ESCANDALLO"},
        {"agregacion": "DETAIL_COSTE_INCOMPLETO", "escandallo_id": "REC-PARCIAL"},
    ]
    answers = ["Hay 8.", "Estas son las 8.", "Hay 4 parciales.", "Hay 4 sin escandallo.", "El coste está incompleto por estas causas registradas: SIN_PRECIO — Patata — Sin precio vigente."]

    class Engine:
        def __init__(self): self.index = 0
        def ejecutar_turn_agente(self, _request):
            turn = self.index
            self.index += 1
            if turn % 2 == 0:
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_escandallos", calls[turn // 2], f"call-{turn}")])
            return AgentTurnResult(FINAL_RESPONSE, text=answers[turn // 2])

    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(registry, escandallos_read_service=HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca()))
    agent = HostAIAgent(Engine(), executor, HostAIToolCatalog.for_general_agent(registry))
    prompts = [
        "¿Cuántas recetas tienen el coste incompleto?", "¿Cuáles son?",
        "¿Cuáles están en PARCIAL?", "¿Y cuáles no tienen escandallo?",
        "¿Por qué tiene el coste incompleto REC-PARCIAL?",
    ]
    history = []
    for prompt, expected in zip(prompts, answers):
        result = agent.run(prompt, conversation_context={"conversation_history": history})
        assert result.ok and result.safe_error == "" and result.text == expected
        history.extend([{"role": "user", "content": prompt}, {"role": "assistant", "content": result.text}])


def test_sin_escandallo_impone_respuesta_minima_aunque_provider_e_historial_excedan_grounding() -> None:
    class Biblioteca:
        def detalle_coste_incompleto(self, identity):
            assert identity == "REC601-000001"
            return {
                "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO", "estado": "OK",
                "grounding_scope": "COSTE_INCOMPLETO", "receta_id": identity,
                "nombre": "SALSA DE CAVA", "estado_coste": "SIN_ESCANDALLO",
                "coste_completo": False,
                "causa": {"tipo": "SIN_ESCANDALLO", "mensaje": "No existe un escandallo registrado."},
                "datos_reales_modificados": False,
            }

    class Engine:
        def __init__(self): self.requests = []
        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                    "consultar_escandallos",
                    {"agregacion": "DETAIL_COSTE_INCOMPLETO", "escandallo_id": "REC601-000001"},
                    "detail-cost",
                )])
            return AgentTurnResult(FINAL_RESPONSE, text=(
                "Faltan precios de Patata, articulo_id=null. Puedo buscarla en Stock y preparar un escandallo de ejemplo."
            ))

    registry = build_default_tool_registry()
    engine = Engine()
    executor = HostAIToolExecutor(registry, escandallos_read_service=HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca()))
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run(
        "¿Por qué tiene el coste incompleto esta receta?",
        conversation_context={"conversation_history": [
            {"role": "user", "content": "salsa de cava"},
            {"role": "assistant", "content": "Ingredientes: cava, nata; cantidades pendientes. Puedo preparar un escandallo de ejemplo."},
        ]},
    )
    assert result.ok and result.text == (
        "El coste está incompleto porque esta receta no tiene un escandallo registrado. "
        "Por eso no hay un coste total ni un coste por ración calculable."
    )
    lowered = result.text.lower()
    assert all(term not in lowered for term in (
        "ingrediente", "articulo_id", "precio", "convers", "pendiente", "stock",
        "preparar", "crear", "ejemplo", "recomend",
    ))
    tool_data = next(item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    serialized = json.dumps(tool_data["content"])
    assert all(key not in serialized for key in ("ingredientes", "articulo_id", "precio", "conversion", "pendientes"))


def test_detalle_coste_real_disponible_tiene_prioridad_sobre_motivos_vacios() -> None:
    real_dto = {
        "consulta_economica": "DETAIL_COSTE_INCOMPLETO",
        "coste_completo": True,
        "coste_por_racion": 5.59435,
        "coste_total": 5.59435,
        "coste_total_parcial": None,
        "datos_reales_modificados": False,
        "estado": "OK",
        "estado_coste": "DISPONIBLE",
        "explicacion": "El coste esta completo y disponible.",
        "grounding_scope": "COSTE_INCOMPLETO",
        "motivos": [],
        "nombre": "APERITIVO CALÇOTADA",
        "numero_motivos": 0,
        "ok": True,
        "receta_id": "REC-EXCEL-6B4B251F8E",
    }

    class Biblioteca:
        def detalle_coste_incompleto(self, identity):
            assert identity == "REC-EXCEL-6B4B251F8E"
            return dict(real_dto)

    class Engine:
        def __init__(self): self.turn = 0
        def ejecutar_turn_agente(self, _request):
            self.turn += 1
            if self.turn == 1:
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                    "consultar_escandallos", {
                        "agregacion": "DETAIL_COSTE_INCOMPLETO", "consulta": "detalle",
                        "escandallo_id": "REC-EXCEL-6B4B251F8E",
                    }, "real-detail",
                )])
            return AgentTurnResult(FINAL_RESPONSE, text=(
                "El dominio marca el coste como incompleto, pero no expone una causa."
            ), grounding_requirement="INTERNAL_DATA_REQUIRED")

    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(
        registry,
        escandallos_read_service=HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca()),
    )
    result = HostAIAgent(
        Engine(), executor, HostAIToolCatalog.for_general_agent(registry),
    ).run("¿Por qué tiene el coste incompleto?")

    assert result.ok
    assert result.text == (
        "El coste está completo y disponible. "
        "El coste total es 5,59435 € y el coste por ración es 5,59435 €."
    )
    assert result.context_updates["economic_incidents"] == []
    assert result.datos_reales_modificados is False
    assert "incompleto" not in result.text.lower()


def test_respuesta_coste_prioriza_disponible_y_conserva_regresiones_parciales() -> None:
    def run(dto):
        class Biblioteca:
            def detalle_coste_incompleto(self, _identity): return dict(dto)
        class Engine:
            def __init__(self): self.turn = 0
            def ejecutar_turn_agente(self, _request):
                self.turn += 1
                if self.turn == 1:
                    return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                        "consultar_escandallos", {
                            "agregacion": "DETAIL_COSTE_INCOMPLETO", "escandallo_id": "REC-1",
                        }, "detail",
                    )])
                return AgentTurnResult(FINAL_RESPONSE, text="Respuesta no grounded")
        registry = build_default_tool_registry()
        executor = HostAIToolExecutor(
            registry, escandallos_read_service=HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca()),
        )
        return HostAIAgent(Engine(), executor, HostAIToolCatalog.for_general_agent(registry)).run("coste")

    base = {
        "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO", "estado": "OK",
        "grounding_scope": "COSTE_INCOMPLETO", "receta_id": "REC-1", "nombre": "Receta",
        "datos_reales_modificados": False,
    }
    by_state = run({**base, "coste_completo": False, "estado_coste": "DISPONIBLE", "motivos": []})
    structured = run({**base, "coste_completo": False, "estado_coste": "PARCIAL", "motivos": [{
        "tipo": "SIN_PRECIO", "nombre": "Patata", "detalle": "Sin precio vigente",
    }]})
    unknown = run({**base, "coste_completo": False, "estado_coste": "PARCIAL", "motivos": []})

    assert by_state.text == "El coste está completo y disponible."
    assert "SIN_PRECIO — Patata — Sin precio vigente" in structured.text
    assert unknown.text == (
        "El dominio marca el coste como incompleto, pero el detalle económico actual "
        "no expone una causa concreta."
    )


def test_conversacion_real_listado_seleccion_convierte_detalle_general_en_detalle_economico() -> None:
    class Telemetry:
        def __init__(self): self.events = []
        def emit(self, event_type, **metadata): self.events.append({"event_type": event_type, **metadata})

    class Biblioteca:
        def listar_costes_incompletos(self, **_params):
            return {
                "ok": True, "consulta_economica": "LIST_COSTE_INCOMPLETO", "estado": "OK",
                "total_evaluadas": 27, "total_coincidencias": 8, "items_devueltos": 8,
                "truncado": False, "resultado": [{
                    "receta_id": "REC601-000001", "nombre": "SALSA DE CAVA",
                    "estado_coste": "SIN_ESCANDALLO", "coste_completo": False,
                }], "datos_reales_modificados": False,
            }
        def detalle_coste_incompleto(self, identity):
            assert identity == "REC601-000001"
            return {
                "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO", "estado": "OK",
                "grounding_scope": "COSTE_INCOMPLETO", "receta_id": identity,
                "nombre": "SALSA DE CAVA", "estado_coste": "SIN_ESCANDALLO",
                "coste_completo": False,
                "causa": {"tipo": "SIN_ESCANDALLO", "mensaje": "No existe un escandallo registrado."},
                "datos_reales_modificados": False,
            }

    class Engine:
        def __init__(self): self.requests = []
        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return AgentTurnResult(FINAL_RESPONSE, text="Necesito consultar datos.", grounding_requirement="INTERNAL_DATA_REQUIRED")
            if turn == 2:
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                    "consultar_escandallos", {"agregacion": "LIST_COSTE_INCOMPLETO"}, "list",
                )])
            if turn == 3:
                return AgentTurnResult(FINAL_RESPONSE, text="REC601-000001 — SALSA DE CAVA: Sin escandallo.", grounding_requirement="INTERNAL_DATA_REQUIRED")
            if turn == 4:
                # Reproduce exactamente la selección real reconstruida por hash.
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                    "consultar_escandallos",
                    {"consulta": "detalle", "escandallo_id": "REC601-000001"},
                    "detail",
                )])
            return AgentTurnResult(FINAL_RESPONSE, text=(
                "Chalota, champis, cava y nata están sin_relacionar; articulo_id y coste_unitario son null. "
                "Conviene vincular Stock, introducir precio, revisar conversiones y crear o preparar escandallo."
            ), grounding_requirement="INTERNAL_DATA_REQUIRED")

    telemetry = Telemetry()
    registry = build_default_tool_registry()
    engine = Engine()
    executor = HostAIToolExecutor(registry, escandallos_read_service=HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca()))
    agent = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry))
    first = agent.run(
        "¿Por qué tiene el coste incompleto esta receta?",
        conversation_context={"request_id": "first", "telemetry": telemetry},
    )
    assert first.ok and "SALSA DE CAVA" in first.text
    history = [
        {"role": "user", "content": "¿Por qué tiene el coste incompleto esta receta?"},
        {"role": "assistant", "content": first.text},
    ]
    second = agent.run(
        "la de salsa de cava",
        conversation_context={"request_id": "second", "telemetry": telemetry, "conversation_history": history},
    )
    assert second.ok and second.text == (
        "El coste está incompleto porque esta receta no tiene un escandallo registrado. "
        "Por eso no hay un coste total ni un coste por ración calculable."
    )
    forbidden = (
        "chalota", "champis", "cava ", "nata", "sin_relacionar", "articulo_id",
        "cantidad_texto", "coste_unitario", "conversion", "stock", "vincular",
        "introducir precio", "crear escandallo", "preparar escandallo", "campos pendientes",
    )
    assert all(term not in second.text.lower() for term in forbidden)
    tool_call = next(item for item in engine.requests[4].messages if item.get("type") == "tool_call")
    assert tool_call["arguments"] == {
        "escandallo_id": "REC601-000001", "agregacion": "DETAIL_COSTE_INCOMPLETO",
    }
    result_event = next(
        event for event in telemetry.events
        if event["event_type"] == "agent_tool_result" and event.get("request_id") == "second"
    )
    assert result_event["aggregation"] == "DETAIL_COSTE_INCOMPLETO"
    assert result_event["economic_grounding_scope"] == "COSTE_INCOMPLETO"
    assert result_event["economic_state"] == "SIN_ESCANDALLO"
    final_event = next(
        event for event in telemetry.events
        if event["event_type"] == "agent_final" and event.get("request_id") == "second"
    )
    assert final_event["economic_final_override"] is True
    assert final_event["economic_override_reason"] == "sin_escandallo_minimal_grounding"


def test_continuidad_economica_no_secuestra_peticion_explicita_de_ingredientes() -> None:
    context = {
        "_current_message": "Enséñame los ingredientes de esa receta",
        "conversation_history": [{"role": "assistant", "content": "Recetas con coste incompleto: REC-1"}],
    }
    original = {"consulta": "detalle", "escandallo_id": "REC-1"}
    assert HostAIAgent._enrich_arguments_with_context("consultar_escandallos", original, context) == original


def test_detalle_general_activo_se_normaliza_a_detalle_coste_y_materializa_incidencia() -> None:
    class Biblioteca:
        def detalle_coste_incompleto(self, identity):
            assert identity == "REC-EXCEL-6B4B251F8E"
            return {
                "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO", "estado": "OK",
                "grounding_scope": "COSTE_INCOMPLETO", "receta_id": identity,
                "nombre": "APERITIVO CALÇOTADA", "estado_coste": "PARCIAL",
                "coste_completo": False, "motivos": [{
                    "tipo": "CONVERSION_NO_DISPONIBLE", "articulo_id": "ART000285",
                    "nombre": "Servilleta MPRO", "detalle": "Conversión no disponible",
                    "unidad_origen": "u", "unidad_destino": "kg",
                }], "numero_motivos": 1, "datos_reales_modificados": False,
            }

    class Engine:
        def __init__(self): self.requests = []
        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                    "consultar_escandallos",
                    {"consulta": "detalle", "escandallo_id": "REC-EXCEL-6B4B251F8E"},
                    "real-detail",
                )])
            return AgentTurnResult(FINAL_RESPONSE, text="Añade una conversión genérica.", grounding_requirement="INTERNAL_DATA_REQUIRED")

    registry = build_default_tool_registry(); engine = Engine()
    agent = HostAIAgent(
        engine,
        HostAIToolExecutor(registry, escandallos_read_service=HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca())),
        HostAIToolCatalog.for_general_agent(registry),
    )
    result = agent.run("¿Por qué tiene el coste incompleto?", conversation_context={
        "active_entity": {
            "id": "REC-EXCEL-6B4B251F8E", "nombre": "APERITIVO CALÇOTADA",
            "tipo": "RECETA", "vista": "RECETA",
        },
    })

    executed_call = next(item for item in engine.requests[1].messages if item.get("type") == "tool_call")
    assert executed_call["arguments"] == {
        "agregacion": "DETAIL_COSTE_INCOMPLETO", "escandallo_id": "REC-EXCEL-6B4B251F8E",
    }
    assert result.context_updates["economic_incidents"] == [{
        "receta_id": "REC-EXCEL-6B4B251F8E", "incidencia": "CONVERSION_NO_DISPONIBLE",
        "articulo_id": "ART000285", "nombre": "Servilleta MPRO",
        "unidad_origen": "u", "unidad_destino": "kg",
    }]
    assert result.text == "El coste está incompleto por estas causas registradas: CONVERSION_NO_DISPONIBLE — Servilleta MPRO — Conversión no disponible."
    assert result.datos_reales_modificados is False


def test_detalle_culinario_explicito_no_se_normaliza_a_coste() -> None:
    original = {"consulta": "detalle", "escandallo_id": "REC-EXCEL-6B4B251F8E"}
    for message in (
        "Muéstrame los ingredientes", "Enséñame la receta completa",
        "Quiero ver la ficha", "Muéstrame el procedimiento",
    ):
        context = {"_current_message": message, "active_entity": {
            "id": "REC-EXCEL-6B4B251F8E", "tipo": "RECETA",
        }}
        assert HostAIAgent._enrich_arguments_with_context(
            "consultar_escandallos", original, context,
        ) == original


def test_caso_real_detalle_economico_llega_a_boton_conversion(monkeypatch) -> None:
    class Biblioteca:
        def detalle_coste_incompleto(self, identity):
            return {
                "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO", "estado": "OK",
                "grounding_scope": "COSTE_INCOMPLETO", "receta_id": identity,
                "nombre": "APERITIVO CALÇOTADA", "estado_coste": "PARCIAL", "coste_completo": False,
                "motivos": [{"tipo": "CONVERSION_NO_DISPONIBLE", "articulo_id": "ART000285",
                    "nombre": "Servilleta MPRO", "detalle": "Conversión no disponible",
                    "unidad_origen": "u", "unidad_destino": "kg"}],
                "numero_motivos": 1, "datos_reales_modificados": False,
            }

    class Articles:
        def obtener(self, article_id):
            return {"ok": article_id == "ART000285", "articulo": {
                "id": "ART000285", "nombre": "Servilleta MPRO",
            } if article_id == "ART000285" else None}

    class Engine:
        def __init__(self): self.turn = 0
        def ejecutar_turn_agente(self, _request):
            self.turn += 1
            if self.turn == 1:
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                    "consultar_escandallos", {"consulta": "detalle", "escandallo_id": "REC-EXCEL-6B4B251F8E"}, "real",
                )])
            return AgentTurnResult(FINAL_RESPONSE, text="respuesta libre", grounding_requirement="INTERNAL_DATA_REQUIRED")

    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    engine = Engine()
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=engine), session_id="real-economic-detail")
    shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    monkeypatch.setattr(shell, "_registrar_log", lambda *_args, **_kwargs: None)
    shell.tool_executor.escandallos_read_service = HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca())
    shell.tool_executor.articulos_read_service = Articles()
    shell._session.contexto_activo = "ELABORACION"
    shell._session.receta_activa = {
        "id": "REC-EXCEL-6B4B251F8E", "nombre": "APERITIVO CALÇOTADA", "tipo": "RECETA", "vista": "RECETA",
    }

    response = shell.enviar("¿Por qué tiene el coste incompleto?", contexto={"request_id": "9bd05421-e89d-4621-a6a7-662bff3fd859"})
    assert response["datos"]["datos_reales_modificados"] is False
    assert response["datos"]["economic_actions"] == [
        {"action_id": "RESOLVE_MISSING_CONVERSION", "action_context_id": response["datos"]["economic_actions"][0]["action_context_id"], "label": "Configurar conversión"},
    ]
    assert shell._session.economic_incidents[0]["articulo_id"] == "ART000285"


def test_caso_real_listado_general_se_normaliza_y_selecciona_receta_sin_escandallo() -> None:
    candidates = [{
        "receta_id": "REC601-000001" if index == 0 else f"REC-{index}",
        "nombre": "SALSA DE CAVA" if index == 0 else f"Receta incompleta {index}",
        "estado_coste": "SIN_ESCANDALLO" if index in {0, 3, 5, 7} else "PARCIAL",
        "coste_completo": False,
    } for index in range(8)]

    class Biblioteca:
        def listar_costes_incompletos(self, **_params):
            return {
                "ok": True, "consulta_economica": "LIST_COSTE_INCOMPLETO", "estado": "OK",
                "grounding_scope": "COSTE_INCOMPLETO_LIST", "total_evaluadas": 27,
                "total_coincidencias": 8, "items_devueltos": 8, "truncado": False,
                "resultado": candidates, "datos_reales_modificados": False,
            }
        def detalle_coste_incompleto(self, identity):
            assert identity == "REC601-000001"
            return {
                "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO", "estado": "OK",
                "grounding_scope": "COSTE_INCOMPLETO", "receta_id": identity,
                "nombre": "SALSA DE CAVA", "estado_coste": "SIN_ESCANDALLO",
                "coste_completo": False,
                "causa": {"tipo": "SIN_ESCANDALLO", "mensaje": "No existe un escandallo registrado."},
                "datos_reales_modificados": False,
            }

    class Engine:
        def __init__(self): self.requests = []
        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return AgentTurnResult(FINAL_RESPONSE, text="Necesito datos", grounding_requirement="INTERNAL_DATA_REQUIRED")
            if turn == 2:
                # Reproduce hash real 19ce... antes del enriquecimiento.
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_escandallos", {"consulta": "listar", "limite": 10}, "list")])
            if turn == 3:
                return AgentTurnResult(FINAL_RESPONSE, text="Ejemplos: dos parciales. Introduce precios y revisa conversiones.", grounding_requirement="INTERNAL_DATA_REQUIRED")
            if turn == 4:
                # Reproduce hash real d452... antes de resolver contra contexto económico.
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_escandallos", {"consulta": "buscar", "limite": 10, "termino": "salsa de cava"}, "select")])
            return AgentTurnResult(FINAL_RESPONSE, text="No encuentro un escandallo exacto; prueba a crear uno.")

    registry = build_default_tool_registry(); engine = Engine()
    executor = HostAIToolExecutor(registry, escandallos_read_service=HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca()))
    agent = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry))
    first = agent.run("¿Por qué tiene el coste incompleto esta receta?")
    assert first.ok and first.grounding_retry is True
    assert first.text.count("\n-") == 8
    assert "Introduce precios" not in first.text and "conversiones" not in first.text
    assert len(first.context_updates["economic_recipe_candidates"]) == 8
    first_call = next(item for item in engine.requests[2].messages if item.get("type") == "tool_call")
    assert first_call["arguments"] == {"agregacion": "LIST_COSTE_INCOMPLETO", "limite": 10}

    history = [
        {"role": "user", "content": "¿Por qué tiene el coste incompleto esta receta?"},
        {"role": "assistant", "content": first.text},
    ]
    second = agent.run("la de salsa de cava", conversation_context={
        "conversation_history": history,
        "economic_recipe_candidates": first.context_updates["economic_recipe_candidates"],
    })
    assert second.text == (
        "El coste está incompleto porque esta receta no tiene un escandallo registrado. "
        "Por eso no hay un coste total ni un coste por ración calculable."
    )
    selected_call = next(item for item in engine.requests[4].messages if item.get("type") == "tool_call")
    assert selected_call["arguments"] == {
        "agregacion": "DETAIL_COSTE_INCOMPLETO", "escandallo_id": "REC601-000001",
    }


def test_seleccion_economica_parcial_ambigua_por_id_pronombre_y_aislada_por_sesion() -> None:
    from SERVICIOS.host_ai_session_context import HostAISessionContext

    session_a = HostAISessionContext()
    session_b = HostAISessionContext()
    session_a.economic_recipe_candidates = [{"receta_id": "REC-A", "nombre": "A", "estado_coste": "PARCIAL"}]
    assert session_b.economic_recipe_candidates == []
    session_a.reset()
    assert session_a.economic_recipe_candidates == []

    candidates = [
        {"receta_id": "REC-A", "nombre": "APERITIVO CALÇOTADA", "estado_coste": "PARCIAL"},
        {"receta_id": "REC-B", "nombre": "APERITIVO CALÇOTADA ESPECIAL", "estado_coste": "PARCIAL"},
    ]
    assert HostAIAgent._select_economic_candidate("la de aperitivo", candidates) == (None, True)
    assert HostAIAgent._select_economic_candidate("REC-A", candidates)[0]["receta_id"] == "REC-A"
    assert HostAIAgent._select_economic_candidate("esa", [candidates[0]])[0]["receta_id"] == "REC-A"
    assert HostAIAgent._select_economic_candidate("esa", [])[0] is None

    class Biblioteca:
        def detalle_coste_incompleto(self, identity):
            assert identity == "REC-A"
            return {
                "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO", "estado": "OK",
                "grounding_scope": "COSTE_INCOMPLETO", "receta_id": identity,
                "estado_coste": "PARCIAL", "coste_completo": False,
                "motivos": [{"tipo": "SIN_PRECIO", "nombre": "Calçot", "detalle": "Sin precio vigente"}],
                "numero_motivos": 1, "datos_reales_modificados": False,
            }
    class Engine:
        def __init__(self): self.requests = []
        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_escandallos", {"consulta": "buscar", "termino": "aperitivo calçotada"}, "partial")])
            return AgentTurnResult(FINAL_RESPONSE, text="Añade precios y revisa Stock.")
    registry = build_default_tool_registry(); engine = Engine()
    agent = HostAIAgent(engine, HostAIToolExecutor(registry, escandallos_read_service=HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca())), HostAIToolCatalog.for_general_agent(registry))
    result = agent.run("la de aperitivo calçotada", conversation_context={
        "conversation_history": [{"role": "assistant", "content": "Recetas con coste incompleto"}],
        "economic_recipe_candidates": [candidates[0]],
    })
    assert result.text == "El coste está incompleto por estas causas registradas: SIN_PRECIO — Calçot — Sin precio vigente."
    assert "Stock" not in result.text


def test_nombre_aislado_de_receta_bloquea_final_creativo_y_activa_entidad() -> None:
    request_id = "c3dde48a-03f0-4f82-8113-afb001a3f36f"

    class CanonicalRecipes:
        def consultar(self, consulta="buscar", *, termino="", **_kwargs):
            assert consulta == "detalle"
            assert termino == "APERITIVO CALÇOTADA"
            entity = {
                "id": "REC-EXCEL-6B4B251F8E", "codigo": "REC-EXCEL-6B4B251F8E",
                "nombre": "APERITIVO CALÇOTADA", "tiene_receta": True,
                "tiene_escandallo": True, "estado_coste": "PARCIAL",
            }
            return {
                "estado": "OK", "elaboracion": entity, "elaboraciones": [entity],
                "datos_reales_modificados": False,
            }

    class GenericProvider:
        def __init__(self): self.requests = []
        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            return AgentTurnResult(
                FINAL_RESPONSE,
                text="Para 10 personas prepara calçots, croquetas, cerveza y vino.",
                grounding_requirement="NONE",
                provider_metadata={"provider": "fake", "model": "fake-model"},
            )

    registry = build_default_tool_registry()
    engine = GenericProvider()
    executor = HostAIToolExecutor(registry, escandallos_read_service=CanonicalRecipes())
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run(
        "APERITIVO CALÇOTADA.", conversation_context={"request_id": request_id},
    )

    assert result.ok is True
    assert result.text == "He encontrado APERITIVO CALÇOTADA. ¿Qué quieres revisar?"
    assert "10 personas" not in result.text and "cerveza" not in result.text
    assert result.executed_tools == ["consultar_escandallos"]
    assert result.context_updates["receta_activa"] == {
        "id": "REC-EXCEL-6B4B251F8E", "nombre": "APERITIVO CALÇOTADA",
        "tipo": "RECETA", "vista": "RECETA",
    }
    assert result.context_updates["contexto_activo"] == "ELABORACION"
    assert result.datos_reales_modificados is False
    assert engine.requests[0].conversation_context["request_id"] == request_id


def test_nombre_parcial_inequivoco_ambiguo_y_termino_generico() -> None:
    class Recipes:
        def consultar(self, consulta="buscar", *, termino="", **_kwargs):
            if termino == "CALÇOTADA ESPECIAL":
                entity = {"id": "REC-1", "nombre": "APERITIVO CALÇOTADA ESPECIAL", "estado_coste": "PARCIAL"}
                return {"estado": "OK", "elaboracion": entity, "elaboraciones": [entity], "datos_reales_modificados": False}
            if termino == "APERITIVO CALÇOTADA":
                items = [
                    {"id": "REC-1", "nombre": "APERITIVO CALÇOTADA"},
                    {"id": "REC-2", "nombre": "APERITIVO CALÇOTADA VEGANO"},
                ]
                return {"estado": "AMBIGUO", "elaboracion": None, "elaboraciones": items, "datos_reales_modificados": False}
            raise AssertionError("Un término genérico de una palabra no debe consultar la Biblioteca")

    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(registry, escandallos_read_service=Recipes())
    catalog = HostAIToolCatalog.for_general_agent(registry)

    partial = HostAIAgent(_SingleFinalEngine(AgentTurnResult(FINAL_RESPONSE, text="genérico")), executor, catalog).run("CALÇOTADA ESPECIAL")
    assert partial.text == "He encontrado APERITIVO CALÇOTADA ESPECIAL. ¿Qué quieres revisar?"
    assert partial.context_updates["receta_activa"]["id"] == "REC-1"

    ambiguous = HostAIAgent(_SingleFinalEngine(AgentTurnResult(FINAL_RESPONSE, text="genérico")), executor, catalog).run("APERITIVO CALÇOTADA")
    assert "varias elaboraciones" in ambiguous.text
    assert "REC-1" in ambiguous.text and "REC-2" in ambiguous.text
    assert "receta_activa" not in ambiguous.context_updates

    generic = HostAIAgent(_SingleFinalEngine(AgentTurnResult(FINAL_RESPONSE, text="Respuesta culinaria normal.")), executor, catalog).run("aperitivo")
    assert generic.text == "Respuesta culinaria normal."
    assert generic.executed_tools == []


def test_seleccion_aislada_preserva_candidatos_economicos_para_followup() -> None:
    class Recipes:
        def consultar(self, **_kwargs):
            entity = {"id": "REC-A", "nombre": "APERITIVO CALÇOTADA", "estado_coste": "PARCIAL"}
            return {"estado": "OK", "elaboracion": entity, "elaboraciones": [entity], "datos_reales_modificados": False}

    candidates = [{"receta_id": "REC-A", "nombre": "APERITIVO CALÇOTADA", "estado_coste": "PARCIAL"}]
    incidents = [{"receta_id": "REC-A", "incidencia": "SIN_PRECIO", "articulo_id": "ART-1"}]
    registry = build_default_tool_registry()
    result = HostAIAgent(
        _SingleFinalEngine(AgentTurnResult(FINAL_RESPONSE, text="inventado")),
        HostAIToolExecutor(registry, escandallos_read_service=Recipes()),
        HostAIToolCatalog.for_general_agent(registry),
    ).run("APERITIVO CALÇOTADA.", conversation_context={
        "economic_recipe_candidates": candidates, "economic_incidents": incidents,
    })
    assert result.context_updates["economic_recipe_candidates"] == candidates
    assert result.context_updates["economic_incidents"] == incidents
    assert result.context_updates["receta_activa"]["id"] == "REC-A"


def test_cuatro_dominios_read_caben_en_el_budget_global_actual() -> None:
    registry = build_default_tool_registry()
    calls = [
        ToolCall("consultar_estado_stock", {"consulta": "resumen"}, "stock"),
        ToolCall("consultar_produccion", {"consulta": "pendientes"}, "produccion"),
        ToolCall("consultar_compras_pendientes", {}, "compras"),
        ToolCall("consultar_escandallos", {"consulta": "buscar", "termino": "arroz"}, "escandallos"),
    ]

    class Engine:
        def __init__(self) -> None:
            self.turns = [
                AgentTurnResult(TOOL_CALL, tool_calls=calls),
                AgentTurnResult(FINAL_RESPONSE, text="Cruce final libre."),
            ]

        def ejecutar_turn_agente(self, _request):
            return self.turns.pop(0)

    class Executor:
        def __init__(self) -> None:
            self.calls = []

        def execute_agent_read(self, tool_id, arguments):
            self.calls.append((tool_id, arguments))
            return SimpleNamespace(
                estado="OK", datos={"fuente": tool_id, "datos_reales_modificados": False},
            )

    executor = Executor()
    result = HostAIAgent(
        Engine(), executor, HostAIToolCatalog.for_general_agent(registry),
    ).run("Cruza los cuatro dominios")

    assert result.ok
    assert result.executed_tools == [call.tool_id for call in calls]
    assert len(executor.calls) == HostAIAgentPolicy.MAX_TOOL_CALLS == 4


def test_incidencias_economicas_ofrecen_solo_ficha_canonica_con_contexto_opaco(monkeypatch) -> None:
    class Articles:
        def obtener(self, article_id):
            names = {
                "ART-PRECIO": "Ingrediente sin precio",
                "ART000285": "Servilleta MPRO 2C40 200 UNI NATU. 6,89€",
            }
            return {
                "ok": article_id in names,
                "articulo": {"id": article_id, "nombre": names[article_id]} if article_id in names else None,
            }

    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id="economic-a")
    shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    shell.tool_executor.articulos_read_service = Articles()
    incidents = [
        {"receta_id": "REC-EXCEL-6B4B251F8E", "incidencia": "SIN_PRECIO", "articulo_id": "ART-PRECIO", "nombre": "Ingrediente sin precio"},
        {"receta_id": "REC-EXCEL-6B4B251F8E", "incidencia": "CONVERSION_INEXISTENTE", "articulo_id": "ART000285", "nombre": "Servilleta MPRO 2C40 200 UNI NATU. 6,89€", "unidad_origen": "u", "unidad_destino": "kg"},
        {"receta_id": "REC-EXCEL-6B4B251F8E", "incidencia": "SIN_PRECIO", "articulo_id": "", "nombre": "Sin relacionar"},
        {"receta_id": "REC-EXCEL-6B4B251F8E", "incidencia": "SIN_PRECIO", "articulo_id": "ART-INEXISTENTE", "nombre": "No existe"},
        {"receta_id": "REC-EXCEL-6B4B251F8E", "incidencia": "RENDIMIENTO_INCOMPLETO", "articulo_id": "ART000285", "nombre": "No soportada"},
    ]
    monkeypatch.setattr(shell.general_agent, "run", lambda *_args, **_kwargs: AgentRunResult(
        True,
        "El coste está incompleto: falta el precio de Ingrediente sin precio y una conversión para Servilleta MPRO.",
        "HAA-ECON", "FAKE", "fake-model", 1, ["consultar_escandallos"],
        context_updates={"economic_incidents": incidents},
    ))

    response = shell.enviar("¿Por qué tiene el coste incompleto APERITIVO CALÇOTADA?")
    assert "economic_actions" in response["datos"], response
    actions = response["datos"]["economic_actions"]
    assert [item["action_id"] for item in actions] == [
        "RESOLVE_MISSING_PRICE", "RESOLVE_MISSING_CONVERSION",
    ]
    assert all(set(item) == {"action_id", "action_context_id", "label"} for item in actions)
    assert all(len(item["action_context_id"]) == 32 for item in actions)

    price = shell.ejecutar_accion_reserva(
        "RESOLVE_MISSING_PRICE", action_context_id=actions[0]["action_context_id"],
    )
    assert price["mensaje"] == "¿Qué precio de compra quieres registrar para Ingrediente sin precio?"
    assert price["datos"]["datos_reales_modificados"] is False
    assert "ui_action" not in price["datos"]

    stale = shell.ejecutar_accion_reserva(
        "RESOLVE_MISSING_CONVERSION", action_context_id=actions[1]["action_context_id"],
    )
    assert stale["datos"]["reason"] == "stale_economic_action"
    assert "ui_action" not in stale["datos"]

    other = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id="economic-b")
    other.tool_executor.articulos_read_service = Articles()
    rejected = other.ejecutar_accion_reserva(
        "RESOLVE_MISSING_PRICE", action_context_id=actions[0]["action_context_id"],
    )
    assert rejected["datos"]["reason"] == "stale_economic_action"


def test_aperitivo_calcotada_conversion_real_abre_articulo_000285_sin_write(monkeypatch) -> None:
    class Articles:
        def obtener(self, article_id):
            return {
                "ok": article_id == "ART000285",
                "articulo": {
                    "id": "ART000285",
                    "nombre": "Servilleta MPRO 2C40 200 UNI NATU. 6,89€",
                } if article_id == "ART000285" else None,
            }

    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id="calcotada")
    shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    shell.tool_executor.articulos_read_service = Articles()
    monkeypatch.setattr(shell.general_agent, "run", lambda *_args, **_kwargs: AgentRunResult(
        True, "Falta una conversión para Servilleta MPRO.", "HAA-CALCOTADA", "FAKE", "fake-model", 1,
        ["consultar_escandallos"], context_updates={"economic_incidents": [{
            "receta_id": "REC-EXCEL-6B4B251F8E", "incidencia": "UNIDAD_INCOMPATIBLE",
            "articulo_id": "ART000285", "nombre": "Servilleta MPRO 2C40 200 UNI NATU. 6,89€",
            "unidad_origen": "u", "unidad_destino": "kg",
        }]},
    ))

    response = shell.enviar("¿Por qué tiene el coste incompleto? aperitivo calçotada")
    assert len(response["datos"]["economic_actions"]) == 1
    action = response["datos"]["economic_actions"][0]
    assert action["action_id"] == "RESOLVE_MISSING_CONVERSION"
    assert action["label"] == "Configurar conversión"
    assert len(action["action_context_id"]) == 32

    clicked = shell.ejecutar_accion_reserva(action["action_id"], action["action_context_id"])
    assert clicked["mensaje"] == "¿A cuánto equivale 1 u de Servilleta MPRO 2C40 200 UNI NATU. 6,89€ en kg?"
    assert "ui_action" not in clicked["datos"]
    assert clicked["datos"]["datos_reales_modificados"] is False


def test_payload_chat_economico_requiere_action_context_cerrado() -> None:
    from API.contracts.http_models import validate_chat_payload

    assert validate_chat_payload({
        "mensaje": "", "action_id": "RESOLVE_MISSING_PRICE",
        "action_context_id": "a" * 32,
    }) == (True, "")
    assert validate_chat_payload({
        "mensaje": "", "action_id": "RESOLVE_MISSING_PRICE",
    }) == (False, "action_context_required")
    assert validate_chat_payload({
        "mensaje": "", "action_id": "RESOLVE_MISSING_CONVERSION",
        "action_context_id": "../../ART-PRECIO",
    }) == (False, "invalid_action_context_id")
    assert validate_chat_payload({
        "mensaje": "", "action_id": "CHECK_ESCANDALLO_COST",
        "action_context_id": "e" * 32,
    }) == (True, "")
    assert validate_chat_payload({
        "mensaje": "", "action_id": "CHECK_ESCANDALLO_COST",
    }) == (False, "action_context_required")
    assert validate_chat_payload({
        "mensaje": "", "action_id": "CHECK_ESCANDALLO_COST",
        "action_context_id": "invalid-context",
    }) == (False, "invalid_action_context_id")
    for forbidden in ("receta_id", "articulo_id", "scopes"):
        assert validate_chat_payload({
            "mensaje": "", "action_id": "CHECK_ESCANDALLO_COST",
            "action_context_id": "e" * 32, forbidden: "browser-controlled",
        }) == (False, "unknown_fields")
    assert validate_chat_payload({
        "mensaje": "", "action_id": "UNKNOWN_ECONOMIC_ACTION",
        "action_context_id": "e" * 32,
    }) == (False, "invalid_action_id")
    assert validate_chat_payload({
        "mensaje": "", "action_id": "APPLY_PENDING_ARTICLE_CHANGE",
    }) == (True, "")
    assert validate_chat_payload({
        "mensaje": "", "action_id": "DISCARD_PENDING_ARTICLE_CHANGE",
        "action_context_id": "a" * 32,
    }) == (False, "unexpected_action_context_id")


def test_detalle_preserva_null_y_muestra_propuesta_ia_separada() -> None:
    class Biblioteca:
        def listar(self, _query):
            return {"elaboraciones": {"total": 1, "items": [{
                "id": "REC-PROPU-1", "codigo": "REC-PROPU-1", "nombre": "Receta demo",
            }]}}

        def detalle(self, identity):
            assert identity == "REC-PROPU-1"
            return {"elaboracion": {
                "id": identity,
                "codigo": identity,
                "nombre": "Receta demo",
                "receta": {
                    "procedimiento": None,
                    "pasos": [],
                    "temperaturas": None,
                    "tecnicas": None,
                    "ingredientes": [{"nombre_original": "Patata", "cantidad": 1.0, "unidad": "kg", "estado_relacion": "relacionado"}],
                    "rendimiento": 4,
                    "unidad_rendimiento": "u",
                },
                "escandallo": {
                    "estado_coste": "PARCIAL",
                    "lineas": [{"nombre_original": "Patata", "cantidad": 1.0, "unidad": "kg", "estado_relacion": "relacionado", "estado_coste": "SIN_PRECIO", "coste_linea": None}],
                    "ingredientes_sin_coste": 1,
                    "ingredientes_sin_conversion": 0,
                },
                "alergenos": None,
                "conservacion": None,
                "propuestas_ia": {
                    "procedimiento": "Cocer y enfriar. Propuesta orientativa no guardada.",
                    "ingredientes": ["Sal", "Pimienta"],
                    "ingredientes_no_registrados": ["Sal", "Pimienta"],
                    "alergenos_posibles": ["Huevo"],
                    "conservacion": "Refrigerado 48 h",
                },
                "pendientes": ["Procedimiento", "Alérgenos", "Conservación"],
            }}

    detail = HostAIEscandallosReadService(Path("."), biblioteca=Biblioteca()).consultar(
        "detalle", termino="Receta demo",
    )["escandallo"]

    assert detail["procedimiento"] is None
    assert detail["estado_procedimiento"] == "PENDIENTE"
    assert detail["procedimiento_propuesto_ia"] == "Cocer y enfriar. Propuesta orientativa no guardada."
    assert detail["ingredientes_propuestos_no_registrados"] == ["Sal", "Pimienta"]
    assert detail["alergenos"] is None
    assert detail["alergenos_posibles"] == ["Huevo"]
    assert detail["conservacion"] is None
    assert detail["conservacion_propuesta_ia"] == "Refrigerado 48 h"
    assert [line["nombre_original"] for line in detail["ingredientes"]] == ["Patata"]
    assert detail["costes"]["estado_coste"] == "PARCIAL"
