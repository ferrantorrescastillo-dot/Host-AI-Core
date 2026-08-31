from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import AuthorizedExecutionContext, OperationClass, ToolDefinition, ToolResult
from .session_context import SessionContext
from .tool_executor import ToolExecutor
from .tool_registry import ToolRegistry


DOMAIN_NAMES = {
    "RECETAS_ESCANDALLOS": "culinary_catalog",
    "CATALOGO": "catalog",
    "STOCK": "stock",
    "EVENTOS": "events",
    "MENUS": "menus",
    "COMPRAS": "purchases",
    "PRODUCCION": "production",
    "IMPORTACIONES": "imports",
    "INCIDENCIAS": "incidents",
    "ESTADISTICAS": "statistics",
    "CONFIGURACION": "configuration",
    "RESERVAS": "reservations",
}


@dataclass
class GeneralAgentPlatformRuntime:
    """Compatibility runtime: platform policy/dispatch in front of legacy domain handlers."""

    legacy: Any
    legacy_registry: Any
    session: SessionContext

    def __post_init__(self) -> None:
        registry = ToolRegistry()
        self._definitions: dict[str, ToolDefinition] = {}
        for tool in self.legacy_registry.list_all():
            if str(getattr(tool, "estado", "")) != "ACTIVADA":
                continue
            operation = self._operation_class(str(tool.tipo))
            if operation is None:
                continue
            domain = DOMAIN_NAMES.get(str(tool.modulo), str(tool.modulo or "general").lower())
            # This generic confirm carries only an opaque preview token. The
            # canonical service authorizes the exact domain kept server-side.
            scopes = frozenset() if str(tool.id) == "aplicar_creacion_catalogo" else self._scopes(domain, operation)
            definition = ToolDefinition(
                tool_id=str(tool.id), description=str(tool.descripcion), operation_class=operation,
                required_scopes=scopes, grounding_requirement=f"INTERNAL_{domain.upper()}",
                metadata={"domain": domain, "legacy_handler": True},
            )
            registry.register(definition, self._handler(str(tool.id), operation, domain))
            self._definitions[definition.tool_id] = definition
        self.platform_registry = registry
        self.platform_executor = ToolExecutor(registry)

    def execute_agent_read(self, tool_id: str, params: dict[str, Any] | None = None, execution_context: Any | None = None):
        return self._execute(tool_id, params, "read", execution_context=execution_context)

    def execute_agent_ui_action(self, tool_id: str, params: dict[str, Any] | None = None):
        return self._execute(tool_id, params, "ui")

    def execute_agent_write_flow(self, tool_id: str, params: dict[str, Any] | None = None, request_id: str = ""):
        return self._execute(tool_id, params, "reservation_write", request_id=request_id)

    def execute_article_change_flow(self, tool_id: str, params: dict[str, Any] | None = None, request_id: str = ""):
        return self._execute(tool_id, params, "article_write", request_id=request_id)

    def execute_catalog_create_flow(self, tool_id: str, params: dict[str, Any] | None = None, request_id: str = ""):
        return self._execute(tool_id, params, "catalog_write", request_id=request_id)

    def execute_stock_lot_location_flow(self, tool_id: str, params: dict[str, Any] | None = None, request_id: str = ""):
        return self._execute(tool_id, params, "stock_lot_write", request_id=request_id)

    def execute(self, tool_id: str, params: dict[str, Any] | None = None, session_context: dict[str, Any] | None = None):
        return self.legacy.execute(tool_id, params=params, session_context=session_context)

    def _execute(self, tool_id: str, params: dict[str, Any] | None, route: str, **extra: Any):
        definition = self._definitions.get(str(tool_id or ""))
        if definition is None:
            return self._legacy_call(route, str(tool_id or ""), dict(params or {}), extra)
        context = self._execution_context(extra.get("execution_context"), extra.get("request_id"))
        result = self.platform_executor.execute(definition.tool_id, {**dict(params or {}), "_route": route,
                                                                    "_request_id": str(extra.get("request_id") or "")}, context)
        legacy_result = result.data.get("legacy_result")
        return legacy_result if legacy_result is not None else self._legacy_call(route, definition.tool_id, {}, extra)

    def _handler(self, tool_id: str, operation: OperationClass, domain: str):
        def handler(params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
            route = str(params.pop("_route", "read")); request_id = str(params.pop("_request_id", ""))
            legacy_result = self._legacy_call(route, tool_id, params, {"request_id": request_id})
            state = dict(getattr(legacy_result, "contexto_actualizado", None) or {})
            if state:
                self.session.set_domain_state(domain, state)
            status = "OK" if str(getattr(legacy_result, "estado", "ERROR")) in {"OK", "ADVERTENCIA"} else "ERROR"
            errors = list(getattr(legacy_result, "errores", None) or [])
            return ToolResult(status, str(getattr(legacy_result, "mensaje", "")),
                              data={"legacy_result": legacy_result}, context_updates={domain: state} if state else {},
                              error_code=str(errors[0]) if errors else "")
        return handler

    def _legacy_call(self, route: str, tool_id: str, params: dict[str, Any], extra: dict[str, Any]):
        if route == "ui":
            return self.legacy.execute_agent_ui_action(tool_id, params)
        if route == "reservation_write":
            return self.legacy.execute_agent_write_flow(tool_id, params, request_id=str(extra.get("request_id") or ""))
        if route == "article_write":
            return self.legacy.execute_article_change_flow(tool_id, params, request_id=str(extra.get("request_id") or ""))
        if route == "catalog_write":
            return self.legacy.execute_catalog_create_flow(tool_id, params, request_id=str(extra.get("request_id") or ""))
        if route == "stock_lot_write":
            return self.legacy.execute_stock_lot_location_flow(tool_id, params, request_id=str(extra.get("request_id") or ""))
        return self.legacy.execute_agent_read(tool_id, params, execution_context=extra.get("execution_context"))

    def _execution_context(self, supplied: Any, request_id: Any) -> AuthorizedExecutionContext:
        source = supplied or getattr(self.legacy, "write_context", None)
        scopes = set(getattr(source, "scopes", None) or ())
        scopes.update({f"{domain}:read" for domain in set(DOMAIN_NAMES.values())})
        return AuthorizedExecutionContext(
            request_id=str(request_id or getattr(source, "request_id", None) or "general-agent"),
            user_id=str(getattr(source, "user_id", None) or "host-ai-internal"),
            tenant_id=str(getattr(source, "tenant_id", None) or "host-ai-local"),
            roles=frozenset(getattr(source, "roles", None) or ("internal",)), scopes=frozenset(scopes),
        )

    @staticmethod
    def _operation_class(value: str) -> OperationClass | None:
        return {"READ": OperationClass.READ, "ANALYSIS": OperationClass.PURE_CALC,
                "UI_ACTION": OperationClass.UI_ACTION, "NAVIGATION": OperationClass.UI_ACTION,
                "PREVIEW": OperationClass.PREVIEW, "CONFIRM": OperationClass.CONFIRM}.get(value.upper())

    @staticmethod
    def _scopes(domain: str, operation: OperationClass) -> frozenset[str]:
        if operation == OperationClass.CONFIRM:
            return frozenset({{"catalog": "articulos:write", "events": "eventos:write", "culinary_catalog": "recetas:write"}.get(domain, "reservas:write")})
        if operation == OperationClass.PREVIEW:
            return frozenset({{"catalog": "articulos:preview", "events": "eventos:preview", "culinary_catalog": "recetas:preview"}.get(domain, "reservas:preview")})
        if operation in {OperationClass.READ, OperationClass.PURE_CALC}:
            return frozenset({f"{domain}:read"})
        return frozenset()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.legacy, name)

    def __setattr__(self, name: str, value: Any) -> None:
        own = {"legacy", "legacy_registry", "session", "platform_registry", "platform_executor", "_definitions"}
        if name in own or "legacy" not in self.__dict__:
            object.__setattr__(self, name, value)
        else:
            setattr(self.legacy, name, value)
