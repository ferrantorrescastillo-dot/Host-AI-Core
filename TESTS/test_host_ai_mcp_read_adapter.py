from __future__ import annotations

from copy import deepcopy

from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_mcp_adapter import HostAIMCPAdapter
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolResult
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class _Executor:
    def __init__(self) -> None:
        self.calls = []

    def execute_agent_read(self, tool_id, arguments):
        self.calls.append((tool_id, deepcopy(arguments)))
        return HostAIToolResult(
            estado="OK",
            mensaje="resultado",
            datos={
                "resultados": [{"id": index, "cantidad": None if index == 0 else index, "unidad": "kg"} for index in range(14)],
                "estado_real": "PENDIENTE",
            },
            tool_id=tool_id,
        )


def _adapter():
    executor = _Executor()
    catalog = HostAIToolCatalog(build_default_tool_registry())
    return HostAIMCPAdapter(catalog, executor, HostAIAgentPolicy()), executor


def test_publica_solo_catalogo_read_efectivo() -> None:
    adapter, _ = _adapter()
    tools = adapter.list_tools()
    assert [item["name"] for item in tools] == [
        "consultar_produccion", "consultar_estado_stock", "consultar_compras_pendientes",
    ]
    assert all(item["inputSchema"]["additionalProperties"] is False for item in tools)
    assert all(item["annotations"]["readOnlyHint"] is True for item in tools)
    assert all(item["annotations"]["destructiveHint"] is False for item in tools)


def test_stock_mcp_reutiliza_executor_y_preserva_null() -> None:
    adapter, executor = _adapter()
    payload = adapter.call_tool("consultar_estado_stock", {"consulta": "articulo", "termino": "salmon"})
    assert executor.calls == [("consultar_estado_stock", {"consulta": "articulo", "termino": "salmon"})]
    structured = payload["structuredContent"]
    assert structured["datos"]["resultados"][0]["cantidad"] is None
    assert len(structured["datos"]["resultados"]) == 10
    assert structured["solo_lectura"] is True
    assert structured["datos_reales_modificados"] is False


def test_produccion_y_compras_conservan_dto_del_executor() -> None:
    adapter, executor = _adapter()
    for tool_id, arguments in (
        ("consultar_produccion", {"consulta": "pendientes", "limite": 10}),
        ("consultar_compras_pendientes", {"estado": "preparado"}),
    ):
        direct = executor.execute_agent_read(tool_id, arguments).to_dict()
        mcp = adapter.call_tool(tool_id, arguments)["structuredContent"]
        assert mcp["estado"] == direct["estado"]
        assert mcp["mensaje"] == direct["mensaje"]
        assert mcp["datos"]["estado_real"] == direct["datos"]["estado_real"]
        assert mcp["datos_reales_modificados"] is False
