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
from SERVICIOS.host_ai_produccion_read_service import HostAIProduccionReadService
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


def _service(motor=None): return HostAIProduccionReadService(SimpleNamespace(produccion_real=motor or _Motor()))


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


def test_post_chat_real_temporal_no_modifica_planes(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("HOST_AI_AI_PROVIDER", "SIMULADO")
    db = tmp_path / "DATOS" / "db"; db.mkdir(parents=True)
    path = db / "planes_produccion.json"
    path.write_text(json.dumps([{"id": "PHTTP", "nombre": "Plan HTTP", "fecha": date.today().isoformat(), "estado": "pendiente", "tareas": [{"id": "THTTP", "titulo": "Paella", "estado_ejecucion": "pendiente"}]}]), encoding="utf-8")
    before = path.read_bytes()
    response = HostAIPlatformAPI(base_dir=tmp_path).handle(ApiRequest(method="POST", path="/api/v1/chat", body={"mensaje": "¿Qué tengo pendiente de producir?", "contexto": {}}))
    assert response.status_code == 200 and response.payload["chat"]["datos"]["tool_context"]["resultados"][0]["tarea_id"] == "THTTP"
    assert path.read_bytes() == before and response.payload["datos_reales_modificados"] is False
