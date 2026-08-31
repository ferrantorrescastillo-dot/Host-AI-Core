from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest
from MOTORES.motor_compras import MotorCompras
from SERVICIOS.base_datos_local import BaseDatosLocal
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_compras_read_service import HostAIComprasReadService
from SERVICIOS.host_ai_deterministic_intent_router import (
    HostAIDeterministicIntentRouter,
    INTENT_BUSCAR_PEDIDOS_PROVEEDOR,
    INTENT_CONSULTAR_COMPRAS_PENDIENTES,
    INTENT_CONSULTAR_NECESIDADES_COMPRA,
    INTENT_CONSULTAR_PENDIENTE_RECEPCION,
    INTENT_CONSULTAR_PROPUESTAS_COMPRA,
)
from SERVICIOS.host_ai_engine.models import HostAIEngineRequest
from SERVICIOS.host_ai_engine.openai_provider import OpenAIProvider
from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.host_ai_tool_resolver import HostAIToolResolver


class _Compras:
    def __init__(self):
        self.pedidos = [
            {"id": "PED-1", "proveedor": "PAU GAVALDA", "estado": "preparado", "fecha": "2026-08-12", "lineas": [{"id": "L1", "articulo_id": "ART-1", "nombre": "Patata", "cantidad": 1, "unidad": "kg", "precio_unitario": 2}]},
            {"id": "PED-2", "proveedor": "MAKRO", "estado": "parcialmente_recibido", "lineas": [{"id": "L2", "articulo_id": "ART-2", "nombre": "Leche", "cantidad": 1, "unidad": "l", "precio_unitario": 1.5}]},
            {"id": "PED-3", "proveedor": "MAKRO", "estado": "recibido", "lineas": [{"id": "L3", "articulo_id": "ART-3", "nombre": "Sal", "cantidad": 2, "unidad": "kg", "precio_unitario": 1}]},
        ]
        self.recepciones = [
            {"pedido_id": "PED-2", "estado": "confirmada", "lineas": [{"order_line_id": "L2", "received_quantity": .4}]},
            {"pedido_id": "PED-3", "estado": "confirmada", "lineas": [{"order_line_id": "L3", "received_quantity": 2}]},
        ]
        self.proveedores = [
            {"id": "PROV-1", "nombre": "PAU GAVALDA", "estado": "activo", "telefono": "NO ENVIAR", "email": "NO ENVIAR"},
            {"id": "PROV-2", "nombre": "GARCIA NORTE", "estado": "activo"},
            {"id": "PROV-3", "nombre": "GARCIA SUR", "estado": "activo"},
        ]

    def listar_pedidos(self): return deepcopy(self.pedidos)
    def listar_recepciones(self, pedido_id=""): return [deepcopy(x) for x in self.recepciones if not pedido_id or x["pedido_id"] == pedido_id]
    def listar_propuestas_compra(self, solo_pendientes=True): return [{"id": "PROP-1", "producto": "Patata", "comprar": .25, "unidad": "kg", "estado": "pendiente", "proveedor_sugerido": "PAU GAVALDA"}]
    def listar_necesidades(self, solo_pendientes=True): return [{"id": "NEC-1", "articulo_id": "ART-1", "nombre": "Patata", "cantidad": .25, "unidad": "kg", "estado": "pendiente", "prioridad": 80}]
    def listar_proveedores(self, incluir_inactivos=False, texto=""):
        q = texto.lower()
        return [deepcopy(x) for x in self.proveedores if q in x["nombre"].lower()]


class _Orchestrator:
    def __init__(self, result):
        self.host_ai_engine = SimpleNamespace(default_provider="OPENAI")
        self.result = result; self.requests = []
    def resolver(self, request):
        self.requests.append(request)
        return SimpleNamespace(to_dict=lambda: {"datos": {"host_ai_engine": self.result}})


def _executor(compras):
    service = HostAIComprasReadService(SimpleNamespace(compras=compras))
    return HostAIToolExecutor(build_default_tool_registry(), compras_read_service=service)


class _Engine:
    def __init__(self, turns):
        self.turns = list(turns)
        self.requests = []

    def ejecutar_turn_agente(self, request):
        self.requests.append(request)
        return self.turns.pop(0)


def test_registry_router_y_resolver_reconocen_cinco_herramientas_read():
    registry = build_default_tool_registry(); resolver = HostAIToolResolver(); router = HostAIDeterministicIntentRouter()
    tools = {
        INTENT_CONSULTAR_COMPRAS_PENDIENTES: "consultar_compras_pendientes",
        INTENT_CONSULTAR_PENDIENTE_RECEPCION: "consultar_pendiente_recepcion",
        INTENT_CONSULTAR_PROPUESTAS_COMPRA: "consultar_propuestas_compra",
        INTENT_CONSULTAR_NECESIDADES_COMPRA: "consultar_necesidades_compra",
        INTENT_BUSCAR_PEDIDOS_PROVEEDOR: "buscar_pedidos_por_proveedor",
    }
    for intent, tool_id in tools.items():
        assert resolver.resolve(intent) == tool_id
        assert registry.get(tool_id).tipo == "READ" and registry.get(tool_id).solo_lectura is True
    assert router.detectar("¿Qué compras tengo pendientes?").intent == INTENT_CONSULTAR_COMPRAS_PENDIENTES
    assert router.detectar("¿Qué pedidos están preparados?").terms == {"estado": "preparado"}
    assert router.detectar("¿Qué me falta por recibir?").intent == INTENT_CONSULTAR_PENDIENTE_RECEPCION
    assert router.detectar("¿Qué propuestas de compra tengo?").intent == INTENT_CONSULTAR_PROPUESTAS_COMPRA
    assert router.detectar("¿Qué necesidades de compra hay?").intent == INTENT_CONSULTAR_NECESIDADES_COMPRA
    assert router.detectar("¿Qué pedidos tengo de Makro?").terms == {"proveedor": "makro"}
    assert router.detectar("¿Tengo compras abiertas con Pau Gavalda?").terms == {"proveedor": "pau gavalda"}


def test_executor_preserva_estados_pendiente_real_y_excluye_recibido():
    compras = _Compras(); executor = _executor(compras)
    open_orders = executor.execute("consultar_compras_pendientes").datos
    pending = executor.execute("consultar_pendiente_recepcion").datos
    prepared = executor.execute("consultar_compras_pendientes", {"estado": "preparado"}).datos
    assert [x["estado"] for x in open_orders["pedidos"]] == ["preparado", "parcialmente_recibido"]
    assert prepared["pedidos"][0]["estado"] == "preparado"
    assert [x["pedido_id"] for x in pending["pedidos"]] == ["PED-1", "PED-2"]
    partial = next(x for x in pending["pedidos"] if x["pedido_id"] == "PED-2")
    assert partial["lineas"][0] == {"articulo_id": "ART-2", "nombre": "Leche", "pedido": 1.0, "recibido": .4, "pendiente": .6, "unidad": "l"}
    assert all(x["pedido_id"] != "PED-3" for x in pending["pedidos"])
    assert pending["datos_reales_modificados"] is False and pending["solo_lectura"] is True


def test_propuestas_necesidades_limite_y_proveedor_saneado_ambiguo_inexistente():
    compras = _Compras(); service = HostAIComprasReadService(SimpleNamespace(compras=compras)); executor = _executor(compras)
    assert executor.execute("consultar_propuestas_compra").datos["propuestas"][0]["propuesta_id"] == "PROP-1"
    assert executor.execute("consultar_necesidades_compra").datos["necesidades"][0]["necesidad_id"] == "NEC-1"
    found = service.buscar_por_proveedor("PAU GAVALDA")
    assert found["proveedores"] == [{"proveedor_id": "PROV-1", "nombre": "PAU GAVALDA", "estado": "activo"}]
    assert "telefono" not in found["proveedores"][0] and "email" not in found["proveedores"][0]
    assert service.buscar_por_proveedor("Garcia")["estado"] == "AMBIGUO"
    assert service.buscar_por_proveedor("Nadie")["estado"] == "NO_ENCONTRADO"
    compras.pedidos *= 6
    assert len(service.consultar_pedidos()["pedidos"]) == 10


def test_chat_ejecuta_antes_de_openai_y_fallback_sin_modificar_compras():
    compras = _Compras(); before = deepcopy(compras.__dict__)
    ok = {"estado": "OK", "proveedor": "OPENAI", "respuesta": {"mensaje": "Hay dos pedidos abiertos."}, "errores": []}
    orchestrator = _Orchestrator(ok); chat = ServicioChatHostAIShell(orchestrator); chat.tool_executor = _executor(compras)
    response = chat.enviar("¿Qué compras tengo pendientes?")
    context = orchestrator.requests[0].parametros["datos_enviados"]["tool_context"]
    assert response["mensaje"] == "Hay dos pedidos abiertos." and context["fuente"] == "compras_canonico"
    assert context["datos_reales_modificados"] is False and compras.__dict__ == before
    assert "navigation_request" not in response["datos"]
    prompt = OpenAIProvider._input_text(HostAIEngineRequest(
        origen="CHAT", modulo="chat_host_ai", tipo_peticion="consulta_general",
        datos_enviados={"pregunta": "¿Qué compras tengo pendientes?", "tool_context": context},
        proveedor_preferido="OPENAI",
    ))
    assert "exclusivamente de lectura" in prompt
    assert "No sugieras escrituras, exportaciones ni capacidades" in prompt
    failure = {"estado": "ERROR", "proveedor": "OPENAI", "respuesta": {}, "errores": ["fallo"]}
    fallback = ServicioChatHostAIShell(_Orchestrator(failure)); fallback.tool_executor = _executor(compras)
    assert fallback.enviar("¿Qué propuestas de compra tengo?")["ok"] is True


def test_consultas_compras_informativas_no_obligan_navegacion_y_mantienen_solo_lectura():
    compras = _Compras(); before = deepcopy(compras.__dict__)
    simulated = {"estado": "OK", "proveedor": "SIMULADO", "respuesta": {}, "errores": []}
    chat = ServicioChatHostAIShell(_Orchestrator(simulated)); chat.tool_executor = _executor(compras)

    for query in (
        "¿Qué compras tengo pendientes?",
        "¿Qué pedidos están preparados?",
        "¿Qué me falta por recibir?",
        "¿Qué propuestas de compra tengo?",
        "¿Qué necesidades de compra hay?",
        "¿Qué pedidos tengo de PAU GAVALDA?",
    ):
        response = chat.enviar(query)
        assert "navigation_request" not in response["datos"]
        assert response["datos"]["datos_reales_modificados"] is False

    assert compras.__dict__ == before


def test_consulta_visual_compras_en_flujo_legacy_si_incluye_navegacion():
    compras = _Compras(); simulated = {"estado": "OK", "proveedor": "SIMULADO", "respuesta": {}, "errores": []}
    chat = ServicioChatHostAIShell(_Orchestrator(simulated)); chat.tool_executor = _executor(compras)
    response = chat.enviar("Enséñame las compras pendientes.")
    assert response["datos"]["navigation_request"]["target_module"] == "COMPRAS"
    assert response["datos"]["datos_reales_modificados"] is False


def test_general_agent_visual_listado_compra_ejecuta_read_y_open_view_listado():
    compras = _Compras(); registry = build_default_tool_registry(); executor = _executor(compras)
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_compras_pendientes", {"consulta": "listado"}, "c-read")]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("abrir_compra", {"vista": "listado"}, "c-open")]),
        AgentTurnResult(FINAL_RESPONSE, text="Te he abierto Compras."),
    ])
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run("Enséñame las compras pendientes.")
    assert result.ok is True
    assert result.executed_tools == ["consultar_compras_pendientes", "abrir_compra"]
    assert result.ui_actions == [{
        "type": "OPEN_VIEW", "target": "COMPRA", "id": "", "view": "LISTADO", "label": "Compras", "safe": True,
        "datos_reales_modificados": False,
    }]


def test_general_agent_informativo_compras_no_navega():
    compras = _Compras(); registry = build_default_tool_registry(); executor = _executor(compras)
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_compras_pendientes", {}, "c-info")]),
        AgentTurnResult(FINAL_RESPONSE, text="Tienes compras pendientes."),
    ])
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run("¿Qué compras hay pendientes?")
    assert result.ok is True
    assert result.executed_tools == ["consultar_compras_pendientes"]
    assert result.ui_actions == []


def test_general_agent_pedido_exacto_abre_pedido_canonico():
    compras = _Compras(); registry = build_default_tool_registry(); executor = _executor(compras)
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_compras_pendientes", {"consulta": "pedido", "pedido_id": "PED-1"}, "c-pedido-read")]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("abrir_compra", {"vista": "pedido", "pedido_id": "PED-1"}, "c-pedido-open")]),
        AgentTurnResult(FINAL_RESPONSE, text="Te he abierto el pedido PED-1."),
    ])
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run("Abre el pedido PED-1.")
    assert result.ok is True
    assert result.executed_tools == ["consultar_compras_pendientes", "abrir_compra"]
    assert result.ui_actions[0]["target"] == "COMPRA"
    assert result.ui_actions[0]["view"] == "PEDIDO"
    assert result.ui_actions[0]["id"] == "PED-1"


def test_general_agent_pedido_ambiguo_devuelve_candidatos_sin_navegacion():
    compras = _Compras(); registry = build_default_tool_registry(); executor = _executor(compras)
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_compras_pendientes", {"consulta": "pedido", "proveedor": "makro"}, "c-amb")]),
        AgentTurnResult(FINAL_RESPONSE, text="Tengo varios pedidos de Makro; dime el id exacto."),
    ])
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run("Abre el pedido de Makro.")
    assert result.ok is True
    assert result.executed_tools == ["consultar_compras_pendientes"]
    assert result.ui_actions == []
    tool_data = next(item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    assert tool_data["content"]["estado"] == "AMBIGUO"
    assert len(tool_data["content"]["pedidos"]) == 2


def test_general_agent_follow_up_compra_reutiliza_pedido_activo_sin_navegar():
    compras = _Compras(); registry = build_default_tool_registry(); executor = _executor(compras)
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_compras_pendientes", {"consulta": "pedido"}, "c-follow")]),
        AgentTurnResult(FINAL_RESPONSE, text="A ese pedido le queda por recibir 0,6 l de leche."),
    ])
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run(
        "¿Qué falta por recibir?",
        {"active_entity": {"id": "PED-2", "tipo": "COMPRA", "nombre": "MAKRO"}},
    )
    assert result.ok is True
    assert result.executed_tools == ["consultar_compras_pendientes"]
    assert result.ui_actions == []
    tool_data = next(item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    assert tool_data["content"]["estado"] == "OK"
    assert {item["pedido_id"] for item in tool_data["content"]["pedidos"]} == {"PED-2"}


def test_general_agent_pedido_inexistente_no_navega_ni_inventa():
    compras = _Compras(); registry = build_default_tool_registry(); executor = _executor(compras)
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_compras_pendientes", {"consulta": "pedido", "pedido_id": "PED-NO"}, "c-missing")]),
        AgentTurnResult(FINAL_RESPONSE, text="No encuentro ese pedido."),
    ])
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run("Abre el pedido PED-NO.")
    assert result.ok is True
    assert result.executed_tools == ["consultar_compras_pendientes"]
    assert result.ui_actions == []
    tool_data = next(item for item in engine.requests[1].messages if item.get("type") == "TOOL_DATA")
    assert tool_data["content"]["estado"] == "NO_ENCONTRADO"


def test_capability_awareness_compras_no_habilita_write_en_general_agent():
    registry = build_default_tool_registry()
    tools = HostAIToolCatalog.for_general_agent(registry).effective_tools()
    policy = HostAIAgentPolicy()
    assert not any(item.get("tool_id") in {"aprobar_compra", "crear_pedido", "modificar_compra"} for item in tools)
    authorized, reason = policy.authorize("aprobar_compra", {"pedido_id": "PED-1"}, tools)
    assert authorized is False and reason == "tool_not_allowed"


def test_post_chat_compras_ruta_http_real_temporal_no_modifica_repositorios(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("HOST_AI_AI_PROVIDER", "SIMULADO")
    motor = MotorCompras(BaseDatosLocal(tmp_path))
    motor.crear_proveedor_manual("Proveedor Temporal")
    order_id = motor.crear_pedidos_borrador_transaccional([{
        "proveedor": "Proveedor Temporal", "origen_tipo": "manual",
        "lineas": [{"nombre": "Patata", "articulo_id": "ART-T", "cantidad": 1, "unidad": "kg", "precio_unitario": 2}],
    }])[0]["id"]
    motor.cambiar_estado_pedido(order_id, "preparado")
    paths = [tmp_path / "DATOS/db/compras_pedidos.json", tmp_path / "DATOS/db/compras_recepciones.json", tmp_path / "DATOS/db/stock_movimientos.json"]
    before = {path: path.read_bytes() if path.exists() else None for path in paths}

    response = HostAIPlatformAPI(base_dir=tmp_path).handle(ApiRequest(method="POST", path="/api/v1/chat", body={"mensaje": "¿Qué compras tengo pendientes?", "contexto": {}}))

    assert response.status_code == 200 and response.payload["ok"] is True
    context = response.payload["chat"]["datos"]["tool_context"]
    assert context["pedidos"][0]["pedido_id"] == order_id
    assert context["datos_reales_modificados"] is False
    assert all((path.read_bytes() if path.exists() else None) == before[path] for path in paths)
