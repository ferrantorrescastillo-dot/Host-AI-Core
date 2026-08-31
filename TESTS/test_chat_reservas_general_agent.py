from copy import deepcopy
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from MODELOS.reserva import Reserva
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_agent_models import AgentRunResult
from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnRequest, AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.reservas_read_service import ReservasReadService


def _service(tmp_path: Path, items=()):
    service = ReservasReadService(tmp_path, today_provider=lambda: date(2026, 8, 20))
    service.repo.guardar_todos([Reserva.from_dict(item) for item in items])
    return service


def _executor(tmp_path: Path, items=()):
    return HostAIToolExecutor(build_default_tool_registry(), reservas_read_service=_service(tmp_path, items))


ITEMS = [
    {"reserva_id": "RES-AAAAAAAAAAAA", "nombre_cliente": "Marta Sol", "fecha": "2026-08-20", "hora": "14:00", "pax": 2, "estado": "CONFIRMADA", "servicio": "COMIDA", "observaciones": "Mesa tranquila"},
    {"reserva_id": "RES-BBBBBBBBBBBB", "nombre_cliente": "Marta Ruiz", "fecha": "2026-08-21", "hora": "21:00", "pax": 4, "estado": "PENDIENTE", "servicio": "CENA"},
]


def test_catalogo_publica_solo_read_y_ui_action_de_reservas():
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    by_id = {tool["tool_id"]: tool for tool in tools}
    assert by_id["consultar_reservas"]["type"] == "READ"
    assert by_id["consultar_reservas"]["input_schema"]["additionalProperties"] is False
    assert by_id["abrir_reservas"]["type"] == "UI_ACTION"
    assert by_id["abrir_reserva"]["type"] == "UI_ACTION"
    assert not [tool for tool in tools if "reserva" in tool["tool_id"] and tool["type"] == "WRITE"]
    assert all(word in by_id["consultar_reservas"]["description"] for word in ["Eventos", "Produccion", "stock reservado"])


def test_listado_vacio_es_resultado_valido(tmp_path):
    result = _executor(tmp_path).execute_agent_read("consultar_reservas", {})
    assert result.estado == "OK"
    assert result.mensaje == "No hay reservas registradas."
    assert result.datos["estado"] == "NO_ENCONTRADO"
    assert result.datos["datos_reales_modificados"] is False


@pytest.mark.parametrize(("params", "ids"), [
    ({"alcance": "hoy"}, ["RES-AAAAAAAAAAAA"]),
    ({"alcance": "proximas"}, ["RES-AAAAAAAAAAAA", "RES-BBBBBBBBBBBB"]),
    ({"estado": "PENDIENTE"}, ["RES-BBBBBBBBBBBB"]),
    ({"servicio": "CENA"}, ["RES-BBBBBBBBBBBB"]),
    ({"q": "Ruiz"}, ["RES-BBBBBBBBBBBB"]),
])
def test_consulta_reservas_filtra_y_no_expone_observaciones(tmp_path, params, ids):
    result = _executor(tmp_path, ITEMS).execute_agent_read("consultar_reservas", params)
    assert [item["reserva_id"] for item in result.datos["resultados"]] == ids
    assert all("observaciones" not in item for item in result.datos["resultados"])
    assert result.contexto_actualizado["contexto_activo"] == "RESERVA"
    assert result.contexto_actualizado["ultimo_modulo"] == "RESERVAS"


def test_id_prioriza_detalle_y_no_inventa_inexistente(tmp_path):
    executor = _executor(tmp_path, ITEMS)
    found = executor.execute_agent_read("consultar_reservas", {"reserva_id": "RES-AAAAAAAAAAAA", "q": "otra"})
    assert found.datos["resultados"][0]["observaciones"] == "Mesa tranquila"
    assert found.contexto_actualizado["reserva_activa"]["reserva_id"] == "RES-AAAAAAAAAAAA"
    missing = executor.execute_agent_read("consultar_reservas", {"reserva_id": "RES-CCCCCCCCCCCC"})
    assert missing.datos["estado"] == "NO_ENCONTRADO"
    assert "reserva_activa" not in missing.contexto_actualizado


def test_nombre_ambiguo_devuelve_candidatos_sin_seleccionar(tmp_path):
    result = _executor(tmp_path, ITEMS).execute_agent_read("consultar_reservas", {"q": "Marta"})
    assert result.datos["estado"] == "AMBIGUO"
    assert len(result.datos["resultados"]) == 2
    assert "reserva_activa" not in result.contexto_actualizado


def test_ui_actions_cerradas_listado_detalle_e_id_invalido(tmp_path):
    executor = _executor(tmp_path, ITEMS)
    listing = executor.execute_agent_ui_action("abrir_reservas", {}).datos["ui_action"]
    detail = executor.execute_agent_ui_action("abrir_reserva", {"reserva_id": "RES-AAAAAAAAAAAA"}).datos["ui_action"]
    assert (listing["target"], listing["view"], listing["id"]) == ("RESERVAS", "LISTADO", "")
    assert (detail["target"], detail["view"], detail["id"]) == ("RESERVAS", "DETALLE", "RES-AAAAAAAAAAAA")
    assert executor.execute_agent_ui_action("abrir_reserva", {"reserva_id": "../../evil"}).estado == "ERROR"
    assert ServicioChatHostAIShell._validated_ui_action(detail) == detail


def test_contexto_followup_y_aislamiento_entre_sesiones(monkeypatch):
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    contexts = []

    def make_shell():
        shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()))
        shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
        def run(_message, conversation_context=None):
            contexts.append(deepcopy(conversation_context or {}))
            updates = {"contexto_activo": "RESERVA", "ultimo_modulo": "RESERVAS"}
            if len(contexts) == 1:
                updates["reserva_activa"] = {"reserva_id": "RES-AAAAAAAAAAAA", "nombre_cliente": "Marta Sol", "pax": 2}
            return AgentRunResult(True, "Reservas consultadas.", "HAA-RES", "FAKE", "fake", 1, ["consultar_reservas"], context_updates=updates)
        shell.general_agent.run = run
        return shell

    first, second = make_shell(), make_shell()
    first.enviar("Enseñame las reservas que tenemos.")
    first.enviar("Las de mañana.")
    assert contexts[1]["contexto_activo"] == "RESERVA"
    assert contexts[1]["active_entity"]["reserva_id"] == "RES-AAAAAAAAAAAA"
    assert contexts[1]["active_entity"]["pax"] == 2
    assert second.estado_sesion()["contexto_activo"] == "HOME"
    assert second.estado_sesion()["reserva_activa"] == {}


class _Turns:
    def __init__(self, *turns):
        self.turns = list(turns)
        self.requests = []

    def ejecutar_turn_agente(self, request):
        self.requests.append(request)
        return self.turns.pop(0)


def test_runtime_recupera_abrir_reserva_sin_id_con_read_segura(tmp_path):
    engine = _Turns(
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("abrir_reserva", {}, "bad-detail")]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_reservas", {}, "safe-read")]),
        AgentTurnResult(FINAL_RESPONSE, text="No hay reservas registradas."),
    )
    agent = HostAIAgent(engine, _executor(tmp_path), HostAIToolCatalog.for_general_agent(build_default_tool_registry()))
    result = agent.run("Enseñame las reservas que tenemos.")
    assert result.ok is True
    assert result.executed_tools == ["consultar_reservas"]
    assert "abrir_reserva" not in result.executed_tools
    correction = engine.requests[1].messages[-1]["content"]
    assert correction["reason"] == "required_property_missing:reserva_id"
    assert correction["datos_reales_modificados"] is False


def test_runtime_recupera_filtro_temporal_invalido_y_lookup_es_consistente(tmp_path):
    engine = _Turns(
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_reservas", {"alcance": "mañana"}, "bad-date")]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_reservas", {"fecha": "2026-08-21"}, "valid-date")]),
        AgentTurnResult(FINAL_RESPONSE, text="No hay reservas mañana."),
    )
    registry = build_default_tool_registry()
    catalog = HostAIToolCatalog.for_general_agent(registry)
    tools = catalog.effective_tools()
    assert len({tool["tool_id"] for tool in tools}) == len(tools)
    assert all(registry.get(tool["tool_id"]) is not None for tool in tools)
    result = HostAIAgent(engine, _executor(tmp_path), catalog).run("¿Qué reservas hay mañana?")
    assert result.ok is True
    assert result.executed_tools == ["consultar_reservas"]


def test_runtime_visual_listado_y_desconocida_controlada(tmp_path):
    visual = _Turns(
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("abrir_reservas", {}, "open-list")]),
        AgentTurnResult(FINAL_RESPONSE, text="Listado abierto."),
    )
    catalog = HostAIToolCatalog.for_general_agent(build_default_tool_registry())
    opened = HostAIAgent(visual, _executor(tmp_path), catalog).run("Abre el listado de reservas")
    assert opened.ok is True and opened.executed_tools == ["abrir_reservas"]
    unknown = HostAIAgent(_Turns(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_reservas_manana", {}, "unknown")])), _executor(tmp_path), catalog).run("mañana")
    assert unknown.ok is False and unknown.safe_error == "invalid_tool"


def test_nombres_de_funcion_enviados_al_provider_coinciden_con_catalogo(monkeypatch):
    from SERVICIOS.host_ai_engine.openai_provider import OpenAIProvider
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia-de-test")
    captured = {}
    class Responses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output=[], output_text='{"grounding_requirement":"NONE","answer":"ok"}', usage=None)
    provider = OpenAIProvider(client_factory=lambda **_kwargs: SimpleNamespace(responses=Responses()))
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    result = provider.ejecutar_turn_agente(AgentTurnRequest(messages=[{"role": "user", "content": "reservas"}], allowed_tools=tools, request_id="FAKE"))
    sent_names = [tool["name"] for tool in captured["tools"]]
    assert result.kind == FINAL_RESPONSE
    assert sent_names == [tool["tool_id"] for tool in tools]
    assert len(sent_names) == len(set(sent_names))
    assert {"consultar_reservas", "abrir_reservas", "abrir_reserva"} <= set(sent_names)


@pytest.mark.parametrize("reserva_id", ["", "RES-abc", "RES-ABCDEFGHIJKL"])
def test_policy_rechaza_id_de_detalle_no_canonico(reserva_id):
    from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    allowed, reason = HostAIAgentPolicy().authorize("abrir_reserva", {"reserva_id": reserva_id}, tools)
    assert allowed is False
    assert reason == "invalid_pattern:reserva_id"
