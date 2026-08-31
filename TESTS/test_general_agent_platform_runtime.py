from __future__ import annotations

from SERVICIOS.host_ai_platform import GeneralAgentPlatformRuntime, SessionContext
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor, HostAIToolResult
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class LegacyProbe:
    def __init__(self) -> None:
        self.calls = []
        self.write_context = None

    def execute_agent_read(self, tool_id, params=None, execution_context=None):
        self.calls.append(("read", tool_id, dict(params or {})))
        return HostAIToolResult("OK", "read", datos={"ok": True}, contexto_actualizado={"active": tool_id})

    def execute_agent_ui_action(self, tool_id, params=None):
        self.calls.append(("ui", tool_id, dict(params or {})))
        return HostAIToolResult("OK", "ui", acciones=[{"type": "OPEN_VIEW"}])

    def execute_agent_write_flow(self, tool_id, params=None, request_id=""):
        self.calls.append(("reservation_write", tool_id, dict(params or {})))
        return HostAIToolResult("OK", "preview")

    def execute_article_change_flow(self, tool_id, params=None, request_id=""):
        self.calls.append(("article_write", tool_id, dict(params or {})))
        return HostAIToolResult("OK", "preview")

    def execute(self, tool_id, params=None, session_context=None):
        return HostAIToolResult("OK", "legacy deterministic")


def test_all_enabled_general_agent_domains_are_registered_on_platform() -> None:
    legacy_registry = build_default_tool_registry()
    runtime = GeneralAgentPlatformRuntime(LegacyProbe(), legacy_registry, SessionContext("runtime"))
    capabilities = runtime.platform_registry.capabilities()
    domains = {item["metadata"]["domain"] for item in capabilities}
    assert {"culinary_catalog", "catalog", "stock", "events", "menus", "purchases", "production",
            "imports", "incidents", "statistics", "configuration", "reservations"} <= domains
    assert all(item["operation_class"] in {"READ", "PURE_CALC", "PREVIEW", "CONFIRM", "UI_ACTION"}
               for item in capabilities)
    assert not any(item["tool_id"] in {"crear_menu", "aprobar_compra", "importar_documento"} for item in capabilities)


def test_runtime_routes_read_ui_preview_and_confirm_through_platform() -> None:
    probe, registry = LegacyProbe(), build_default_tool_registry()
    runtime = GeneralAgentPlatformRuntime(probe, registry, SessionContext("runtime"))
    assert runtime.execute_agent_read("consultar_menu", {"menu_id": "MENU-DYNAMIC"}).estado == "OK"
    assert runtime.execute_agent_ui_action("abrir_compra", {}).estado == "OK"
    assert runtime.execute_agent_write_flow("crear_reserva", {"nombre_cliente": "Dynamic"}).estado == "OK"
    assert runtime.execute_article_change_flow("preparar_precio_articulo", {"articulo_id": "DYNAMIC"}).estado == "OK"
    assert [call[0] for call in probe.calls] == ["read", "ui", "reservation_write", "article_write"]
    assert runtime.session.get_domain_state("menus")["active"] == "consultar_menu"


def test_runtime_preserves_legacy_attribute_injection_for_transition() -> None:
    probe, registry = LegacyProbe(), build_default_tool_registry()
    runtime = GeneralAgentPlatformRuntime(probe, registry, SessionContext("runtime"))
    marker = object()
    runtime.escandallos_read_service = marker
    assert probe.escandallos_read_service is marker
