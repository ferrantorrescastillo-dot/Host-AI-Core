from __future__ import annotations

from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


def test_catalogo_expone_solo_tres_read_sin_internos():
    tools = HostAIToolCatalog(build_default_tool_registry()).effective_tools()
    assert [item["tool_id"] for item in tools] == ["consultar_produccion", "consultar_estado_stock", "consultar_compras_pendientes"]
    assert all(item["type"] == "READ" and item["confirmation_policy"] == "NONE" and item["max_results"] == 10 for item in tools)
    serialized = str(tools)
    assert "Navigation" not in serialized and "WRITE" not in serialized and "DATOS" not in serialized and "HostAI" not in serialized


def test_policy_rechaza_inventada_extras_tipos_enum_y_limite():
    policy = HostAIAgentPolicy(); tools = HostAIToolCatalog(build_default_tool_registry()).effective_tools()
    assert policy.authorize("inventada", {}, tools)[0] is False
    assert policy.authorize("consultar_estado_stock", {"consulta": "resumen", "metodo": "guardar"}, tools)[0] is False
    assert policy.authorize("consultar_estado_stock", {"consulta": "otro"}, tools)[0] is False
    assert policy.authorize("consultar_produccion", {"limite": 11}, tools)[0] is False
    assert policy.authorize("consultar_produccion", {"consulta": "hoy", "limite": 10}, tools)[0] is True


def test_executor_agente_usa_mapa_explicito_y_rechaza_navigation_write():
    from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
    executor = HostAIToolExecutor(build_default_tool_registry())
    assert set(executor._agent_read_handlers) == {
        "consultar_produccion",
        "consultar_estado_stock",
        "buscar_articulos",
        "consultar_articulo_detalle",
        "consultar_compras_pendientes",
        "consultar_escandallos",
        "consultar_uso_elaboracion",
        "consultar_menu",
        "consultar_eventos",
        "consultar_evento_detalle",
        "consultar_reservas",
        "consultar_necesidades_operativas",
    }
    assert executor.execute_agent_read("abrir_stock", {}).errores == ["agent_tool_not_allowed"]
    assert executor.execute_agent_read("crear_receta", {}).errores == ["agent_tool_not_allowed"]


def test_policy_permite_preview_minimo_reserva_y_prohibe_write_directo():
    policy = HostAIAgentPolicy()
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    minimal = {"nombre_cliente": "Marta", "fecha": "2030-05-20", "hora": "21:00", "pax": 4}
    allowed, reason = policy.authorize("crear_reserva", minimal, tools)
    assert allowed is True and reason == ""
    contract = next(item for item in tools if item["tool_id"] == "crear_reserva")
    assert contract["type"] == "PREVIEW" and contract["confirmation_policy"] == "EXPLICIT_HUMAN"
    assert policy.authorize("escribir_reserva", minimal, tools) == (False, "tool_not_allowed")
    assert all(item["type"] != "WRITE" for item in tools)
