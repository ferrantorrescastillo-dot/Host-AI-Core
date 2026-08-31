from __future__ import annotations

from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_menus_read_service import HostAIMenusReadService
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


PBD_LINES = [
    ("Entrante", "REC-EXCEL-E2BC710519", "TABLA DE QUESOS Y EMBUTIDOS"),
    ("Principal", "REC-EXCEL-7E82F179E3", "Ensaladilla de gamba"),
    ("Postre", "REC-EXCEL-F851AC82AC", "Crema catalana"),
]


class _Menus:
    def __init__(self):
        self.items = [self._pbd(), {"id": "MENU-OTRO", "nombre": "pbd especial", "estado": "BORRADOR",
                                    "version": 1, "secciones": []}]

    @staticmethod
    def _pbd():
        return {
            "id": "MENU601-000003", "codigo": "", "nombre": "pbd", "estado": "BORRADOR",
            "estado_operativo": "borrador", "version": 1, "comensales": 10,
            "coste_total": 5.83592, "coste_por_comensal": 0.583592, "coste_completo": True,
            "lineas_sin_coste": 0, "advertencias": [], "incidencias": [],
            "secciones": [
                {"id": f"SEC-{index:03d}", "nombre": section, "orden": index - 1, "elaboraciones": [{
                    "elaboracion_id": recipe_id, "elaboracion_nombre": name, "cantidad": 1,
                    "coste_por_racion": 0.5 + index / 100, "coste_linea_total": 5 + index,
                    "estado_coste": "DISPONIBLE", "orden": 0,
                }]}
                for index, (section, recipe_id, name) in enumerate(PBD_LINES, 1)
            ],
        }

    def obtener(self, menu_id):
        item = next((item for item in self.items if item["id"] == menu_id), None)
        return {"ok": True, "menu": item} if item else {"ok": False}

    def listar(self, query):
        term = str(query.get("q") or "").lower()
        items = [item for item in self.items if term in item["nombre"].lower()]
        return {"ok": True, "menus": items, "total": len(items)}


def _service():
    return HostAIMenusReadService(".", menus=_Menus())


def test_pbd_devuelve_composicion_completa_canonica_sin_omitir_lineas():
    result = _service().consultar(menu_id="MENU601-000003")
    menu = result["menu"]

    assert result["estado"] == "OK"
    assert menu["menu_id"] == "MENU601-000003" and menu["estado"] == "BORRADOR" and menu["version"] == 1
    assert menu["total_elaboraciones"] == 3 and menu["composicion_completa"] is True
    assert [(line["seccion"], line["elaboracion_id"], line["nombre"], line["cantidad"])
            for line in menu["elaboraciones"]] == [(*line, 1) for line in PBD_LINES]
    assert all(line["tipo_referencia"] == "RECETA" for line in menu["elaboraciones"])
    assert result["solo_lectura"] is True and result["datos_reales_modificados"] is False


def test_limite_no_trunca_composicion_y_no_anade_texto_no_canonico():
    result = _service().consultar(menu_id="MENU601-000003", limite=1)
    assert len(result["menu"]["elaboraciones"]) == 3
    assert all(line["elaboracion_id"].startswith("REC-") for line in result["menu"]["elaboraciones"])


def test_resolucion_por_termino_exacta_ambigua_e_inexistente():
    exact = _service().consultar(termino="pbd")
    assert exact["estado"] == "OK" and exact["menu"]["menu_id"] == "MENU601-000003"
    ambiguous = _service().consultar(termino="pbd ")
    assert ambiguous["estado"] == "OK"
    partial = _service().consultar(termino="p")
    assert partial["estado"] == "AMBIGUO" and len(partial["candidatos"]) == 2
    assert _service().consultar(menu_id="MENU-NO-EXISTE")["estado"] == "NO_ENCONTRADO"


def test_capability_es_read_interna_schema_cerrado_y_navigation_write_rechazados():
    registry = build_default_tool_registry()
    internal = HostAIToolCatalog.for_general_agent(registry).effective_tools()
    contract = next(item for item in internal if item["tool_id"] == "consultar_menu")
    assert contract["type"] == "READ" and contract["confirmation_policy"] == "NONE"
    assert contract["input_schema"]["additionalProperties"] is False
    assert "consultar_menu" not in {item["tool_id"] for item in HostAIToolCatalog(registry).effective_tools()}
    policy = HostAIAgentPolicy()
    assert policy.authorize("consultar_menu", {"ruta": "DATOS/db/menus.json"}, internal) == (
        False, "additional_properties_not_allowed",
    )
    assert policy.authorize("abrir_menus", {}, internal)[0] is False
    assert policy.authorize("crear_menu", {}, internal)[0] is False


def test_abrir_menu_publica_intencion_visual_directa_sin_reconfirmacion():
    internal = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    opening = next(item for item in internal if item["tool_id"] == "abrir_menu")

    assert opening["type"] == "UI_ACTION"
    assert opening["confirmation_policy"] == "NONE"
    assert opening["input_schema"]["additionalProperties"] is False
    assert all(term in opening["description"] for term in ("abrir", "mostrar", "enseñar", "ver"))
    assert "ejecútala directamente" in opening["description"]
    assert "sin pedir una confirmación adicional" in opening["description"]
    assert "No consulta ni modifica datos" in opening["description"]


def test_general_agent_recibe_dto_completo_como_untrusted_data():
    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(registry, menus_read_service=_service())

    class Engine:
        def __init__(self): self.requests = []
        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return AgentTurnResult(TOOL_CALL, tool_calls=[
                    ToolCall("consultar_menu", {"consulta": "elaboraciones", "termino": "pbd"}, "menu-1"),
                ])
            return AgentTurnResult(FINAL_RESPONSE, text="Las tres elaboraciones del menú están enumeradas.")

    engine = Engine()
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run(
        "¿Qué elaboraciones tiene el menú pbd? Lista todas sin omitir ninguna.",
    )
    assert result.ok and result.executed_tools == ["consultar_menu"]
    tool_data = next(item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    assert tool_data["untrusted_data"] is True
    assert len(tool_data["content"]["menu"]["elaboraciones"]) == 3


def test_menu_ambiguo_no_abre_y_aclaracion_posterior_abre_id_canonico():
    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(registry, menus_read_service=_service())

    class Engine:
        def __init__(self, turns):
            self.turns = list(turns)
            self.requests = []

        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            return self.turns.pop(0)

    ambiguous_engine = Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[
            ToolCall("consultar_menu", {"consulta": "detalle", "termino": "p"}, "menu-ambiguous"),
        ]),
        AgentTurnResult(FINAL_RESPONSE, text="He encontrado varios menús; necesito que indiques cuál."),
    ])
    ambiguous = HostAIAgent(
        ambiguous_engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run("Enséñame el menú de verano.")

    assert ambiguous.executed_tools == ["consultar_menu"]
    assert ambiguous.ui_actions == []
    tool_data = next(item for item in ambiguous_engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    assert tool_data["content"]["estado"] == "AMBIGUO"

    clarification_engine = Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[
            ToolCall("abrir_menu", {"menu_id": "MENU601-000003"}, "menu-open"),
        ]),
        AgentTurnResult(FINAL_RESPONSE, text="He abierto el menú pbd."),
    ])
    clarification = HostAIAgent(
        clarification_engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run(
        "Me refiero a MENU601-000003.",
        {"active_entity": {"id": "MENU601-000003", "tipo": "MENU", "nombre": "pbd"}},
    )

    assert clarification.executed_tools == ["abrir_menu"]
    assert clarification.ui_actions == [{
        "type": "OPEN_VIEW", "target": "MENU", "id": "MENU601-000003",
        "view": "DETALLE", "label": "pbd", "safe": True,
        "datos_reales_modificados": False,
    }]


def test_peticion_visual_con_analisis_abre_menu_y_conserva_respuesta_fundamentada():
    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(registry, menus_read_service=_service())

    class Engine:
        def __init__(self):
            self.turns = [
                AgentTurnResult(TOOL_CALL, tool_calls=[
                    ToolCall("consultar_menu", {"consulta": "detalle", "termino": "pbd"}, "menu-read"),
                ]),
                AgentTurnResult(TOOL_CALL, tool_calls=[
                    ToolCall("abrir_menu", {"menu_id": "MENU601-000003"}, "menu-open"),
                ]),
                AgentTurnResult(FINAL_RESPONSE, text="He abierto pbd. La elaboración con mayor coste de línea es Ensaladilla de gamba."),
            ]

        def ejecutar_turn_agente(self, _request):
            return self.turns.pop(0)

    result = HostAIAgent(
        Engine(), executor, HostAIToolCatalog.for_general_agent(registry),
    ).run("Enséñame el menú pbd y dime cuál es la elaboración más cara.")

    assert result.executed_tools == ["consultar_menu", "abrir_menu"]
    assert result.ui_actions[0]["id"] == "MENU601-000003"
    assert "Ensaladilla de gamba" in result.text
    assert result.datos_reales_modificados is False


def test_follow_up_menu_sin_termino_reutiliza_menu_activo():
    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(registry, menus_read_service=_service())

    class Engine:
        def __init__(self):
            self.turns = [
                AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                    "consultar_menu", {"consulta": "elaboraciones"}, "menu-follow",
                )]),
                AgentTurnResult(FINAL_RESPONSE, text="La más cara es Ensaladilla de gamba."),
            ]
            self.requests = []

        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            return self.turns.pop(0)

    engine = Engine()
    result = HostAIAgent(
        engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run(
        "¿Cuál es la elaboración más cara?",
        {"active_entity": {"id": "MENU601-000003", "tipo": "MENU", "nombre": "pbd"}},
    )

    assert result.executed_tools == ["consultar_menu"]
    assert result.ui_actions == []
    tool_data = next(item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    assert tool_data["content"]["estado"] == "OK"
    assert tool_data["content"]["menu"]["menu_id"] == "MENU601-000003"


def test_multitool_menu_produccion_escandallos_cabe_en_limite_global():
    registry = build_default_tool_registry()
    calls = [
        ToolCall("consultar_menu", {"consulta": "detalle", "termino": "pbd"}, "menu"),
        ToolCall("consultar_produccion", {"consulta": "buscar", "termino": "pbd"}, "prod"),
        ToolCall("consultar_escandallos", {"consulta": "buscar", "termino": "pbd"}, "esc"),
    ]

    class Engine:
        def __init__(self): self.turns = [AgentTurnResult(TOOL_CALL, tool_calls=calls), AgentTurnResult(FINAL_RESPONSE, text="Respuesta cruzada.")]
        def ejecutar_turn_agente(self, _request): return self.turns.pop(0)

    class Executor:
        def __init__(self): self.calls = []
        def execute_agent_read(self, tool_id, arguments):
            self.calls.append((tool_id, arguments))
            return SimpleNamespace(estado="OK", datos={"fuente": tool_id, "datos_reales_modificados": False})

    executor = Executor()
    result = HostAIAgent(Engine(), executor, HostAIToolCatalog.for_general_agent(registry)).run("Cruza menú, producción y costes")
    assert result.ok and result.executed_tools == [call.tool_id for call in calls]
    assert len(executor.calls) == 3 < HostAIAgentPolicy.MAX_TOOL_CALLS + 1
