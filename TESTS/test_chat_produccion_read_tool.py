from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
from types import SimpleNamespace

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest
from CORE.host_ai_core import HostAICore
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_deterministic_intent_router import HostAIDeterministicIntentRouter, INTENT_CONSULTAR_PRODUCCION
from SERVICIOS.host_ai_engine.models import HostAIEngineRequest
from SERVICIOS.host_ai_engine.openai_provider import OpenAIProvider
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService
from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_produccion_read_service import HostAIProduccionReadService
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.host_ai_tool_resolver import HostAIToolResolver


class _Motor:
    def __init__(self):
        self.plans = [{"id": "P1", "nombre": "Plan hoy", "fecha": date.today().isoformat(), "estado": "en_produccion", "configuracion_planificacion": {"menu_id": "M1", "menu_version": 2}}]
        states = ["pendiente", "en_proceso", "en_preparacion", "en_espera", "bloqueada", "finalizada", "en_proceso"]
        names = ["Paella", "Croquetas", "Fondo", "Salsa", "Arroz bloqueado", "Bizcocho", "Croquetas especiales"]
        self.tasks = []
        for index, (state, name) in enumerate(zip(states, names), 1):
            self.tasks.append({"id": f"T{index}", "titulo": name, "receta": name, "receta_id": f"R{index}", "origen": "menu", "estado_ejecucion": state, "cantidad": None if index == 1 else index, "unidad": None if index == 1 else "kg", "prioridad": None if index == 1 else 50, "porcentaje_avance": None if index == 1 else 10, "bloqueo": "Falta equipo" if state == "bloqueada" else "", "incidencias": []})

    def listar_planes(self): return deepcopy(self.plans)
    def resumen_ejecucion(self, _plan_id):
        normalized = [{**t, "estado_ejecucion": "en_proceso" if t["estado_ejecucion"] == "en_curso" else t["estado_ejecucion"]} for t in self.tasks]
        counts = {key: 0 for key in ("pendiente", "en_proceso", "en_preparacion", "en_espera", "bloqueada", "finalizada")}
        for task in normalized: counts[task["estado_ejecucion"]] = counts.get(task["estado_ejecucion"], 0) + 1
        counts["en_curso"] = counts["en_proceso"] + counts["en_preparacion"] + counts["en_espera"]
        return {"total_tareas": len(normalized), "estados": counts, "tareas": normalized, "tareas_pendientes": [t for t in normalized if t["estado_ejecucion"] != "finalizada"]}


class _Orchestrator:
    def __init__(self, result): self.host_ai_engine = SimpleNamespace(default_provider="OPENAI"); self.result = result; self.requests = []
    def resolver(self, request):
        self.requests.append(request)
        return SimpleNamespace(to_dict=lambda: {"datos": {"host_ai_engine": self.result}})


class _Menus:
    def consultar(self, termino="", menu_id="", **_kwargs):
        if menu_id == "MENU601-000003" or str(termino).strip().lower() == "pbd":
            return {"estado": "OK", "menu": {"menu_id": "MENU601-000003", "nombre": "pbd"}}
        return {"estado": "NO_ENCONTRADO", "menu": None, "candidatos": []}


def _service(motor=None, menus=None):
    return HostAIProduccionReadService(
        SimpleNamespace(produccion_real=motor or _Motor()), menus_read_service=menus,
    )


def test_servicio_filtra_estados_fecha_busqueda_limite_y_preserva_null():
    service = _service()
    assert service.consultar("en_curso")["resumen"]["en_curso"] == 4
    assert {x["estado"] for x in service.consultar("en_curso")["resultados"]} == {"en_proceso", "en_preparacion", "en_espera"}
    assert service.consultar("bloqueadas")["resultados"][0]["estado"] == "bloqueada"
    assert service.consultar("terminadas")["resultados"][0]["estado"] == "finalizada"
    assert len(service.consultar("hoy", fecha=date.today().isoformat())["resultados"]) == 7
    assert service.consultar("buscar", "Paella")["estado"] == "OK"
    assert service.consultar("buscar", "cro")["estado"] == "AMBIGUO"
    assert service.consultar("buscar", "inexistente")["estado"] == "NO_ENCONTRADO"
    assert len(service.consultar("pendientes", limite=1)["resultados"]) == 1
    unknown = service.consultar("buscar", "T1")["resultados"][0]
    assert unknown["cantidad"] is None and unknown["unidad"] is None and unknown["prioridad"] is None
    assert service.consultar("pendientes")["datos_reales_modificados"] is False


def test_resuelve_plan_por_id_nombre_menu_canonico_y_menu_id_sin_mezclar_global():
    motor = _Motor()
    motor.plans[0] = {
        "id": "PLANPR-FCEB14E386", "nombre": "Producción · pbd", "fecha": None,
        "estado": "borrador", "configuracion_planificacion": {
            "generado_desde": "menu", "menu_id": "MENU601-000003", "menu_version": 1,
        },
    }
    service = _service(motor, _Menus())

    by_term = service.consultar("buscar", termino="pbd")
    by_id = service.consultar("buscar", termino="PLANPR-FCEB14E386")
    by_name = service.consultar("buscar", termino="Produccion pbd")
    by_menu = service.consultar("pendientes", menu_id="MENU601-000003")

    for result in (by_term, by_id, by_name, by_menu):
        assert result["estado"] == "OK"
        assert result["ambito_resultados"] == "PLAN"
        assert result["plan"]["plan_id"] == "PLANPR-FCEB14E386"
        assert result["plan"]["menu_id"] == "MENU601-000003"
        assert {item["plan_id"] for item in result["resultados"]} == {"PLANPR-FCEB14E386"}
        assert result["datos_reales_modificados"] is False
    assert by_term["resuelto_por"] == "MENU_CANONICO"
    assert by_id["resuelto_por"] == "PLAN_ID"
    assert by_name["resuelto_por"] == "PLAN_NOMBRE"
    assert by_menu["resuelto_por"] == "MENU_ID"


def test_dos_planes_del_mismo_menu_son_ambiguos_y_no_se_selecciona_ninguno():
    motor = _Motor()
    motor.plans = [
        {"id": "PLAN-A", "nombre": "Producción A", "estado": "borrador", "fecha": "2026-08-15",
         "configuracion_planificacion": {"menu_id": "MENU601-000003"}},
        {"id": "PLAN-B", "nombre": "Producción B", "estado": "en_produccion", "fecha": "2026-08-16",
         "configuracion_planificacion": {"menu_id": "MENU601-000003"}},
    ]
    result = _service(motor, _Menus()).consultar("buscar", termino="pbd")

    assert result["estado"] == "AMBIGUO"
    assert result["resultados"] == [] and result["plan"] is None
    assert [(item["plan_id"], item["estado"], item["fecha"]) for item in result["candidatos"]] == [
        ("PLAN-A", "borrador", "2026-08-15"), ("PLAN-B", "en_produccion", "2026-08-16"),
    ]


def test_resumen_declara_contadores_principales_y_solapamientos():
    summary = _service().consultar("pendientes")["resumen"]

    assert summary["tareas"] == 7
    assert summary["pendientes"] == 6
    assert summary["en_curso"] == 4
    assert summary["bloqueadas"] == 1
    assert summary["finalizadas"] == 1
    assert sum(summary["por_estado_principal"].values()) == summary["tareas"]
    assert summary["indicadores_transversales"]["bloqueadas"] == 1
    assert "subconjunto" in summary["semantica_contadores"]["en_curso"]
    assert "solaparse" in summary["semantica_contadores"]["bloqueadas"]


def test_general_agent_resuelve_menu_abre_plan_y_follow_up_filtra_solo_ese_plan():
    registry = build_default_tool_registry()
    motor = _Motor()
    motor.plans[0] = {
        "id": "PLANPR-FCEB14E386", "nombre": "Producción · pbd", "estado": "borrador",
        "configuracion_planificacion": {"generado_desde": "menu", "menu_id": "MENU601-000003", "menu_version": 1},
    }
    service = _service(motor, _Menus())
    executor = HostAIToolExecutor(registry, produccion_read_service=service)

    class Engine:
        def __init__(self, turns): self.turns = list(turns); self.requests = []
        def ejecutar_turn_agente(self, request): self.requests.append(request); return self.turns.pop(0)

    opening_engine = Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "consultar_produccion", {"consulta": "buscar", "termino": "pbd"}, "production-read",
        )]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "abrir_produccion_ui", {"plan_id": "PLANPR-FCEB14E386"}, "production-open",
        )]),
        AgentTurnResult(FINAL_RESPONSE, text="Te he abierto el plan Producción · pbd."),
    ])
    opening = HostAIAgent(
        opening_engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run("Enséñame la producción de pbd.")

    assert opening.executed_tools == ["consultar_produccion", "abrir_produccion_ui"]
    assert opening.ui_actions == [{
        "type": "OPEN_VIEW", "target": "PRODUCCION", "id": "PLANPR-FCEB14E386",
        "view": "PLAN", "label": "Producción · pbd", "safe": True,
        "datos_reales_modificados": False,
    }]

    follow_engine = Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "consultar_produccion", {"consulta": "pendientes", "plan_id": "PLANPR-FCEB14E386"}, "production-follow",
        )]),
        AgentTurnResult(FINAL_RESPONSE, text="Estas son las tareas pendientes de ese plan."),
    ])
    follow = HostAIAgent(
        follow_engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run("¿Qué está pendiente?", {"active_entity": {"id": "PLANPR-FCEB14E386", "tipo": "PRODUCCION"}})

    assert follow.executed_tools == ["consultar_produccion"]
    assert follow.ui_actions == []
    tool_data = next(item for item in follow_engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    assert tool_data["content"]["ambito_resultados"] == "PLAN"
    assert {item["plan_id"] for item in tool_data["content"]["resultados"]} == {"PLANPR-FCEB14E386"}


def test_compatibilidad_historica_y_router_sin_colisiones():
    motor = _Motor(); motor.tasks[1]["estado_ejecucion"] = "en_curso"
    result = _service(motor).consultar("en_curso")
    assert next(x for x in result["resultados"] if x["tarea_id"] == "T2")["estado"] == "en_proceso"
    router = HostAIDeterministicIntentRouter()
    cases = {"¿Qué tengo pendiente de producir?": "pendientes", "¿Qué está en curso?": "en_curso", "¿Qué producción tengo hoy?": "hoy", "¿Qué tareas están bloqueadas?": "bloqueadas", "¿Qué producción está terminada?": "terminadas", "Busca producción de croquetas": "buscar"}
    for text, query in cases.items():
        match = router.detectar(text); assert match.intent == INTENT_CONSULTAR_PRODUCCION and match.terms["consulta"] == query
    assert router.detectar("¿Cómo está el stock?").intent != INTENT_CONSULTAR_PRODUCCION
    assert router.detectar("Busca artículos de leche").intent != INTENT_CONSULTAR_PRODUCCION
    assert router.detectar("¿Qué compras tengo pendientes?").intent != INTENT_CONSULTAR_PRODUCCION


def test_registry_executor_chat_openai_falso_y_fallback_son_read():
    registry = build_default_tool_registry(); tool = registry.get("consultar_produccion")
    assert tool and tool.tipo == "READ" and tool.solo_lectura is True
    contracts = HostAIToolCatalog.for_general_agent(registry).effective_tools()
    read_contract = next(item for item in contracts if item["tool_id"] == "consultar_produccion")
    open_contract = next(item for item in contracts if item["tool_id"] == "abrir_produccion_ui")
    assert {"plan_id", "menu_id"} <= set(read_contract["input_schema"]["properties"])
    assert read_contract["input_schema"]["additionalProperties"] is False
    assert open_contract["confirmation_policy"] == "NONE"
    assert "sin pedir una confirmación adicional" in open_contract["description"]
    assert HostAIToolResolver().resolve(INTENT_CONSULTAR_PRODUCCION) == "consultar_produccion"
    executor = HostAIToolExecutor(registry, produccion_read_service=_service())
    before = deepcopy(executor.produccion_read_service.motor.__dict__)
    orchestrator = _Orchestrator({"estado": "OK", "proveedor": "OPENAI", "respuesta": {"mensaje": "Produccion redactada."}, "errores": []})
    chat = ServicioChatHostAIShell(orchestrator); chat.tool_executor = executor
    response = chat.enviar("¿Qué estoy produciendo?")
    context = orchestrator.requests[0].parametros["datos_enviados"]["tool_context"]
    assert response["mensaje"] == "Produccion redactada." and context["fuente"] == "produccion_real_canonica"
    assert executor.produccion_read_service.motor.__dict__ == before
    prompt = OpenAIProvider._input_text(HostAIEngineRequest(origen="CHAT", modulo="chat", tipo_peticion="consulta_general", datos_enviados={"pregunta": "produccion", "tool_context": context}))
    assert "no recalcules en_curso" in prompt and "null en cero" in prompt
    fallback = ServicioChatHostAIShell(_Orchestrator({"estado": "ERROR", "proveedor": "OPENAI", "respuesta": {}, "errores": ["fallo"]})); fallback.tool_executor = executor
    assert fallback.enviar("¿Qué producción tengo pendiente?")["ok"] is True


def test_menu_activo_permite_resolver_y_abrir_produccion_sin_repetir_nombre():
    registry = build_default_tool_registry()
    motor = _Motor()
    motor.plans[0] = {
        "id": "PLANPR-FCEB14E386", "nombre": "Producción · pbd", "estado": "borrador",
        "configuracion_planificacion": {"generado_desde": "menu", "menu_id": "MENU601-000003", "menu_version": 1},
    }
    executor = HostAIToolExecutor(registry, produccion_read_service=_service(motor, _Menus()))

    class Engine:
        def __init__(self):
            self.requests = []
            self.turns = [
                AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                    "consultar_produccion", {"consulta": "buscar", "menu_id": "MENU601-000003"}, "context-read",
                )]),
                AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                    "abrir_produccion_ui", {"plan_id": "PLANPR-FCEB14E386"}, "context-open",
                )]),
                AgentTurnResult(FINAL_RESPONSE, text="Te he abierto el plan Producción · pbd."),
            ]

        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            return self.turns.pop(0)

    engine = Engine()
    result = HostAIAgent(
        engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run("Enséñame la producción.", {
        "contexto_activo": "MENU",
        "active_entity": {"id": "MENU601-000003", "tipo": "MENU", "nombre": "pbd"},
    })

    assert result.executed_tools == ["consultar_produccion", "abrir_produccion_ui"]
    assert result.ui_actions[0]["id"] == "PLANPR-FCEB14E386"
    assert "MENU601-000003" in engine.requests[0].messages[0]["content"]


def test_follow_up_produccion_sin_plan_id_reutiliza_plan_activo():
    registry = build_default_tool_registry()
    motor = _Motor()
    motor.plans[0] = {
        "id": "PLANPR-FCEB14E386", "nombre": "Producción · pbd", "estado": "borrador",
        "configuracion_planificacion": {"generado_desde": "menu", "menu_id": "MENU601-000003", "menu_version": 1},
    }
    executor = HostAIToolExecutor(registry, produccion_read_service=_service(motor, _Menus()))

    class Engine:
        def __init__(self):
            self.requests = []
            self.turns = [
                AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                    "consultar_produccion", {"consulta": "pendientes"}, "production-follow",
                )]),
                AgentTurnResult(FINAL_RESPONSE, text="Estas son las tareas pendientes."),
            ]

        def ejecutar_turn_agente(self, request):
            self.requests.append(request)
            return self.turns.pop(0)

    engine = Engine()
    result = HostAIAgent(
        engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run(
        "¿Qué está pendiente?",
        {"active_entity": {"id": "PLANPR-FCEB14E386", "tipo": "PRODUCCION", "nombre": "Producción · pbd"}},
    )

    assert result.executed_tools == ["consultar_produccion"]
    assert result.ui_actions == []
    tool_data = next(item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    assert tool_data["content"]["ambito_resultados"] == "PLAN"
    assert tool_data["content"]["plan"]["plan_id"] == "PLANPR-FCEB14E386"
    assert {item["plan_id"] for item in tool_data["content"]["resultados"]} == {"PLANPR-FCEB14E386"}


def test_post_chat_real_temporal_no_modifica_planes(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("HOST_AI_AI_PROVIDER", "SIMULADO")
    db = tmp_path / "DATOS" / "db"; db.mkdir(parents=True)
    path = db / "planes_produccion.json"
    path.write_text(json.dumps([{"id": "PHTTP", "nombre": "Plan HTTP", "fecha": date.today().isoformat(), "estado": "pendiente", "tareas": [{"id": "THTTP", "titulo": "Paella", "estado_ejecucion": "pendiente"}]}]), encoding="utf-8")
    before = path.read_bytes()
    response = HostAIPlatformAPI(base_dir=tmp_path).handle(ApiRequest(method="POST", path="/api/v1/chat", body={"mensaje": "¿Qué tengo pendiente de producir?", "contexto": {}}))
    assert response.status_code == 200 and response.payload["chat"]["datos"]["tool_context"]["resultados"][0]["tarea_id"] == "THTTP"
    assert path.read_bytes() == before and response.payload["datos_reales_modificados"] is False
