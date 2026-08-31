from copy import deepcopy
from types import SimpleNamespace

import pytest

from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_agent_models import AgentRunResult
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


EVENTOS = [
    {"id": "EVT-002", "nombre": "Cena empresa", "fecha": "2026-08-22", "pax": 40, "estado": "ACTIVO", "servicios": 1},
    {"id": "EVT-003", "nombre": "Boda Jardines", "fecha": "2026-08-29", "pax": 120, "estado": "ACTIVO", "servicios": 2},
]


class _Home:
    core = None

    def cargar_home(self):
        return {"modulos": {"eventos": {"items": deepcopy(EVENTOS)}}}


def _executor():
    return HostAIToolExecutor(build_default_tool_registry(), home_read_service=_Home())


def test_catalogo_publica_read_eventos_separado_de_produccion_y_sin_write():
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    by_id = {tool["tool_id"]: tool for tool in tools}
    assert by_id["consultar_eventos"]["type"] == "READ"
    assert "Produccion" in by_id["consultar_eventos"]["description"]
    assert by_id["abrir_eventos"]["type"] == "UI_ACTION"
    assert "crear_evento" not in by_id


@pytest.mark.parametrize("consulta", ["listar", "proximos"])
def test_read_eventos_lista_proximos_ordenados_y_limitados(consulta):
    before = deepcopy(EVENTOS)
    result = _executor().execute_agent_read("consultar_eventos", {"consulta": consulta, "limite": 1})
    assert result.estado == "OK"
    assert result.datos["resultados"] == [EVENTOS[0]]
    assert result.datos["orden"] == "fecha_ascendente"
    assert result.datos["datos_reales_modificados"] is False
    assert EVENTOS == before


@pytest.mark.parametrize("params", [
    {"consulta": "buscar", "termino": "boda"},
    {"consulta": "detalle", "evento_id": "EVT-003"},
])
def test_read_evento_por_nombre_o_id_sin_inventar(params):
    result = _executor().execute_agent_read("consultar_eventos", params)
    assert [item["id"] for item in result.datos["resultados"]] == ["EVT-003"]


def test_evento_inexistente_no_inventa_resultado():
    result = _executor().execute_agent_read("consultar_eventos", {"consulta": "buscar", "termino": "inexistente"})
    assert result.estado == "OK"
    assert result.datos["estado"] == "NO_ENCONTRADO"
    assert result.datos["resultados"] == []


def test_ui_action_eventos_abre_solo_vista_real_de_listado():
    result = _executor().execute_agent_ui_action("abrir_eventos", {})
    assert result.datos["ui_action"] == {
        "type": "OPEN_VIEW", "target": "EVENTOS", "id": "", "view": "LISTADO",
        "label": "Eventos", "safe": True, "datos_reales_modificados": False,
    }
    assert ServicioChatHostAIShell._validated_ui_action(result.datos["ui_action"]) == result.datos["ui_action"]


@pytest.mark.parametrize("mensaje", [
    "Enséñame los eventos que tenemos.",
    "Me refiero al módulo Eventos de HOST AI.",
    "Los próximos 10 eventos.",
    "No Producción, módulo Eventos.",
    "¿Qué eventos tenemos esta semana?",
])
def test_shell_fija_dominio_eventos_tras_read_sin_produccion(monkeypatch, mensaje):
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), home_read_service=_Home())
    shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    captured = []

    def run(_message, conversation_context=None):
        captured.append(deepcopy(conversation_context or {}))
        return AgentRunResult(True, "Eventos consultados.", "HAA-EVENTOS", "FAKE", "fake", 1, ["consultar_eventos"])

    monkeypatch.setattr(shell.general_agent, "run", run)
    response = shell.enviar(mensaje)
    assert response["datos"]["general_agent"]["tools_executed"] == ["consultar_eventos"]
    assert shell.estado_sesion()["contexto_activo"] == "EVENTO"
    assert "consultar_produccion" not in response["datos"]["general_agent"]["tools_executed"]


def test_follow_up_proximos_10_recibe_contexto_eventos(monkeypatch):
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), home_read_service=_Home())
    shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    captured = []

    def run(_message, conversation_context=None):
        captured.append(deepcopy(conversation_context or {}))
        return AgentRunResult(True, "Eventos consultados.", "HAA-EVENTOS", "FAKE", "fake", 1, ["consultar_eventos"])

    monkeypatch.setattr(shell.general_agent, "run", run)
    shell.enviar("Enséñame los eventos que tenemos.")
    shell.enviar("Los próximos 10.")
    assert captured[1]["contexto_activo"] == "EVENTO"
    assert captured[1]["active_entity"] == {"tipo": "EVENTO", "dominio": "EVENTOS"}
