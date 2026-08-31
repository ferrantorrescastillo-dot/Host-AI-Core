from copy import deepcopy
from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentRunResult, AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell


class _Articles:
    state = {"ART-GAMBA": {"id": "ART-GAMBA", "nombre": "Gamba paella"}}
    def obtener(self, article_id):
        return {"ok": article_id in self.state, "articulo": deepcopy(self.state.get(article_id))}


class _Menus:
    state = {"MENU601-000003": {"menu_id": "MENU601-000003", "nombre": "pbd"}}
    def consultar(self, **kwargs):
        item = self.state.get(kwargs.get("menu_id"))
        return {"estado": "OK" if item else "NO_ENCONTRADO", "menu": deepcopy(item)}


class _Motor:
    state = [{"id": "PLANPR-FCEB14E386", "nombre": "Producción · pbd"}]
    def listar_planes(self): return deepcopy(self.state)


class _Production:
    motor = _Motor()


class _Purchases:
    state = [{"pedido_id": "PED-001", "proveedor_nombre": "PAU GAVALDA"}]
    def consultar_pedidos(self, **_kwargs): return {"pedidos": deepcopy(self.state)}


def _executor():
    return HostAIToolExecutor(
        build_default_tool_registry(), articulos_read_service=_Articles(),
        menus_read_service=_Menus(), produccion_read_service=_Production(),
        compras_read_service=_Purchases(),
    )


def test_ui_actions_resuelven_identidad_canonica_y_no_escriben():
    executor = _executor()
    cases = [
        ("abrir_articulo", {"articulo_id": "ART-GAMBA", "vista": "ficha"}, "ARTICULO", "ART-GAMBA", "FICHA"),
        ("abrir_menu", {"menu_id": "MENU601-000003"}, "MENU", "MENU601-000003", "DETALLE"),
        ("abrir_produccion_ui", {"plan_id": "PLANPR-FCEB14E386"}, "PRODUCCION", "PLANPR-FCEB14E386", "PLAN"),
        ("abrir_compra", {"vista": "pedido", "pedido_id": "PED-001"}, "COMPRA", "PED-001", "PEDIDO"),
        ("abrir_compra", {"vista": "listado"}, "COMPRA", "", "LISTADO"),
    ]
    before = deepcopy((_Articles.state, _Menus.state, _Motor.state, _Purchases.state))
    for tool_id, params, target, identity, view in cases:
        result = executor.execute_agent_ui_action(tool_id, params)
        assert result.estado == "OK"
        assert result.datos["ui_action"] == {
            "type": "OPEN_VIEW", "target": target, "id": identity, "view": view,
            "label": result.datos["ui_action"]["label"], "safe": True,
            "datos_reales_modificados": False,
        }
        assert result.datos["solo_lectura"] is True
    assert before == (_Articles.state, _Menus.state, _Motor.state, _Purchases.state)


def test_ui_actions_rechazan_entidades_inexistentes_y_parametros_hostiles():
    executor = _executor()
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    policy = HostAIAgentPolicy()
    invalid = [
        ("abrir_articulo", {"articulo_id": "../../admin", "vista": "ficha"}),
        ("abrir_menu", {"menu_id": "https://evil.example"}),
        ("abrir_produccion_ui", {"plan_id": "javascript:alert(1)"}),
        ("abrir_compra", {"vista": "pedido", "pedido_id": "PED-NO"}),
    ]
    for tool_id, params in invalid:
        assert executor.execute_agent_ui_action(tool_id, params).estado == "ERROR"
    assert policy.authorize("abrir_articulo", {"articulo_id": "ART-GAMBA", "vista": "ficha", "url": "javascript:alert(1)"}, tools)[0] is False
    assert policy.authorize("abrir_menu", {"menu_id": "MENU601-000003", "view": "admin"}, tools)[0] is False
    assert policy.authorize("abrir_produccion_ui", {"plan_id": "PLANPR-FCEB14E386", "pathname": "/admin"}, tools)[0] is False
    assert policy.authorize("abrir_compra", {"vista": "detalle"}, tools)[0] is False


def test_shell_sanea_targets_vistas_e_identidades_sin_aceptar_url():
    valid = ServicioChatHostAIShell._validated_ui_action({
        "type": "OPEN_VIEW", "target": "MENU", "id": "MENU601-000003",
        "view": "DETALLE", "label": "pbd", "url": "javascript:alert(1)",
    })
    assert valid == {
        "type": "OPEN_VIEW", "target": "MENU", "id": "MENU601-000003",
        "view": "DETALLE", "label": "pbd", "safe": True,
        "datos_reales_modificados": False,
    }
    assert ServicioChatHostAIShell._validated_ui_action({"type": "OPEN_VIEW", "target": "MENU", "id": "../../admin", "view": "DETALLE"}) is None
    assert ServicioChatHostAIShell._validated_ui_action({"type": "OPEN_VIEW", "target": "DESCONOCIDO", "id": "X", "view": "DETALLE"}) is None


def test_shell_conserva_entidad_activa_para_follow_up(monkeypatch):
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()))
    shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    captured = []
    results = [
        AgentRunResult(True, "Menú abierto.", "HAA-MENU", "FAKE", "fake", 1, ["abrir_menu"], ui_actions=[{
            "type": "OPEN_VIEW", "target": "MENU", "id": "MENU601-000003", "view": "DETALLE", "label": "pbd",
        }]),
        AgentRunResult(True, "Respuesta de seguimiento.", "HAA-FOLLOW", "FAKE", "fake", 1, ["consultar_menu"]),
    ]
    def run(_message, conversation_context=None):
        captured.append(deepcopy(conversation_context or {}))
        return results.pop(0)
    monkeypatch.setattr(shell.general_agent, "run", run)
    shell.enviar("Enséñame el menú pbd.")
    shell.enviar("¿Cuál es la más cara?")
    assert shell.estado_sesion()["menu_activo"] == {"id": "MENU601-000003", "nombre": "pbd", "tipo": "MENU", "vista": "DETALLE"}
    assert captured[1]["active_entity"]["id"] == "MENU601-000003"
    assert captured[1]["active_entity"]["tipo"] == "MENU"


class _Engine:
    def __init__(self, turns): self.turns = list(turns); self.requests = []
    def ejecutar_turn_agente(self, request): self.requests.append(request); return self.turns.pop(0)


def test_peticion_visual_ejecuta_read_y_ui_action_pero_follow_up_solo_read():
    executor = _executor()
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_menu", {"menu_id": "MENU601-000003"}, "read")]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("abrir_menu", {"menu_id": "MENU601-000003"}, "open")]),
        AgentTurnResult(FINAL_RESPONSE, text="Te he abierto el menú pbd en una nueva pestaña."),
    ])
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(build_default_tool_registry())).run("Enséñame el menú pbd.")
    assert result.executed_tools == ["consultar_menu", "abrir_menu"]
    assert result.ui_actions[0]["id"] == "MENU601-000003"
    follow_engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_menu", {"menu_id": "MENU601-000003", "consulta": "elaboraciones"}, "follow")]),
        AgentTurnResult(FINAL_RESPONSE, text="La elaboración más cara es la indicada por los datos."),
    ])
    follow = HostAIAgent(follow_engine, executor, HostAIToolCatalog.for_general_agent(build_default_tool_registry())).run(
        "¿Cuál es la elaboración más cara?", {"active_entity": {"id": "MENU601-000003", "tipo": "MENU"}},
    )
    assert follow.executed_tools == ["consultar_menu"] and follow.ui_actions == []
    assert "MENU601-000003" in follow_engine.requests[0].messages[0]["content"]
