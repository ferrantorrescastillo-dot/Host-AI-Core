from __future__ import annotations

from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.host_ai_uso_elaboracion_read_service import HostAIUsoElaboracionReadService


TARGET = "REC-EXCEL-F851AC82AC"
PARENT = "REC-EXCEL-BBE14A0601"


class _Biblioteca:
    recipes = [
        {"id": TARGET, "nombre": "Crema catalana"},
        {"id": PARENT, "nombre": "Crema Catalana quemada con carquiñoli"},
        {"id": "REC-SIN-USO", "nombre": "Elaboración sin uso"},
    ]

    def listar(self, query):
        term = str(query.get("q") or "").lower()
        items = [item for item in self.recipes if not term or term in item["nombre"].lower()]
        return {"elaboraciones": {"items": items, "total": len(items)}}

    def detalle(self, identity):
        item = next((item for item in self.recipes if item["id"] == identity), None)
        if item is None:
            return {"ok": False}
        ingredients = [{"escandallo_hijo_id": TARGET}] if identity == PARENT else []
        return {"ok": True, "elaboracion": {**item, "receta": {"ingredientes": ingredients}}}


class _Menus:
    def listar(self, _query):
        def line(identity):
            return {"elaboracion_id": identity, "cantidad": 1}
        return {"menus": [
            {"id": "MENU601-000002", "nombre": "Menú pba", "estado": "ARCHIVADO", "version": 3,
             "secciones": [{"nombre": "Postre", "elaboraciones": [line(TARGET)]}]},
            {"id": "MENU601-000003", "nombre": "pbd", "estado": "BORRADOR", "version": 1,
             "secciones": [{"nombre": "Postre", "elaboraciones": [line(TARGET)]}]},
            {"id": "MENU-TEXTO", "nombre": "Texto parecido", "estado": "BORRADOR", "version": 1,
             "secciones": [{"nombre": "Postre", "elaboraciones": [{"elaboracion_nombre": "Crema catalana"}]}]},
        ]}


class _Produccion:
    def consultar(self, consulta, termino="", fecha=None, limite=10):
        assert consulta == "buscar"
        rows = [{"plan_id": "PLANPR-FCEB14E386", "plan_nombre": "Producción · pbd", "estado_plan": "borrador",
                 "fecha": None, "tarea_id": "TAREAPR-1F35644943", "titulo": "Crema catalana", "receta_id": TARGET}]
        return {"estado": "OK", "resultados": [row for row in rows if row["receta_id"] == termino][:limite]}


def _service():
    return HostAIUsoElaboracionReadService(".", biblioteca=_Biblioteca(), menus=_Menus(), produccion=_Produccion())


def test_crema_exacta_devuelve_menus_produccion_padre_y_eventos_no_disponibles():
    result = _service().consultar(escandallo_id=TARGET)

    assert result["estado"] == "OK"
    assert result["elaboracion"] == {"escandallo_id": TARGET, "nombre": "Crema catalana"}
    assert [item["menu_id"] for item in result["menus"]] == ["MENU601-000002", "MENU601-000003"]
    assert result["menus"][0]["estado"] == "ARCHIVADO" and result["menus"][1]["estado"] == "BORRADOR"
    assert result["produccion"][0]["plan_id"] == "PLANPR-FCEB14E386"
    assert result["produccion"][0]["tarea_id"] == "TAREAPR-1F35644943"
    assert result["padres"][0]["escandallo_id"] == PARENT
    assert result["padres"][0]["tipo_relacion"] == "SUBELABORACION_DIRECTA"
    assert result["eventos"]["estado"] == "NO_DISPONIBLE_RELACION_CANONICA"
    assert result["solo_lectura"] is True and result["datos_reales_modificados"] is False
    assert "MENU-TEXTO" not in {item["menu_id"] for item in result["menus"]}


def test_identidades_distintas_sin_usos_e_inexistente():
    parent = _service().consultar(escandallo_id=PARENT)
    assert parent["elaboracion"]["nombre"] == "Crema Catalana quemada con carquiñoli"
    assert parent["elaboracion"]["escandallo_id"] != TARGET
    assert parent["padres"] == []

    unused = _service().consultar(escandallo_id="REC-SIN-USO")
    assert unused["menus"] == [] and unused["produccion"] == [] and unused["padres"] == []
    assert _service().consultar(escandallo_id="REC-NO-EXISTE")["estado"] == "NO_ENCONTRADO"


def test_schema_lista_blanca_y_executor_read_rechazan_argumentos_y_write():
    registry = build_default_tool_registry()
    tools = HostAIToolCatalog.for_general_agent(registry).effective_tools()
    contract = next(item for item in tools if item["tool_id"] == "consultar_uso_elaboracion")
    assert contract["type"] == "READ" and contract["confirmation_policy"] == "NONE"
    assert contract["max_results"] == 10
    assert "consultar_uso_elaboracion" not in {item["tool_id"] for item in HostAIToolCatalog(registry).effective_tools()}
    policy = HostAIAgentPolicy()
    assert policy.authorize("consultar_uso_elaboracion", {"ruta": "DATOS/db/menus.json"}, tools) == (
        False, "additional_properties_not_allowed",
    )
    assert policy.authorize("crear_menu", {}, tools)[0] is False

    executor = HostAIToolExecutor(registry, uso_elaboracion_read_service=_service())
    result = executor.execute_agent_read("consultar_uso_elaboracion", {"escandallo_id": TARGET})
    assert result.estado == "OK" and result.datos["datos_reales_modificados"] is False
    assert executor.execute_agent_read("abrir_menus", {}).errores == ["agent_tool_not_allowed"]


def test_provider_falso_recibe_tool_data_no_confiable_y_multitool():
    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(registry, uso_elaboracion_read_service=_service(),
                                  escandallos_read_service=SimpleNamespace(consultar=lambda **_: {"estado": "OK", "escandallo": {"id": TARGET}}))

    class Engine:
        def __init__(self):
            self.requests = []

        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return AgentTurnResult(TOOL_CALL, tool_calls=[
                    ToolCall("consultar_escandallos", {"consulta": "detalle", "termino": "Crema catalana"}, "id-1"),
                    ToolCall("consultar_uso_elaboracion", {"escandallo_id": TARGET}, "id-2"),
                ])
            return AgentTurnResult(FINAL_RESPONSE, text="Respuesta final libre y basada en las tools.")

    engine = Engine()
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run(
        "¿En qué menús se utiliza la elaboración Crema catalana?",
    )
    assert result.ok and result.executed_tools == ["consultar_escandallos", "consultar_uso_elaboracion"]
    tool_data = [item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA"]
    assert len(tool_data) == 2 and all(item["untrusted_data"] is True for item in tool_data)
    usage = next(item for item in tool_data if item["tool_id"] == "consultar_uso_elaboracion")
    assert usage["content"]["menus"][0]["menu_id"] == "MENU601-000002"


def test_follow_up_puede_responder_desde_historial_sin_reconsultar():
    class Engine:
        def __init__(self): self.requests = []
        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            return AgentTurnResult(FINAL_RESPONSE, text="Sí, existe producción relacionada según el contexto anterior.")

    engine = Engine()
    result = HostAIAgent(engine, SimpleNamespace(), HostAIToolCatalog.for_general_agent(build_default_tool_registry())).run(
        "¿Y está en producción?", conversation_context={"conversation_history": [
            {"role": "user", "content": "¿En qué menús se usa Crema catalana?"},
            {"role": "assistant", "content": "Se usa en Menú pba y pbd; también figura en Producción · pbd."},
        ]},
    )
    assert result.ok and result.executed_tools == []
    assert len(engine.requests) == 1
