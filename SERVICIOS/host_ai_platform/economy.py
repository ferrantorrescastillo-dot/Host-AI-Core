from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .action_context import ActionContextError, ActionContextStore
from .contracts import AgentAction, AuthorizedExecutionContext, OperationClass, ToolDefinition, ToolResult, UIAction
from .session_context import SessionContext
from .tool_registry import ToolRegistry

ECONOMY_DOMAIN = "economy"


class EconomyPort(Protocol):
    def incomplete_cost(self, recipe_id: str) -> dict[str, Any]: ...
    def preview_article_change(self, operation: str, article_id: str, values: dict[str, Any], context: AuthorizedExecutionContext, session_id: str) -> dict[str, Any]: ...
    def confirm_article_change(self, preview_token: str, context: AuthorizedExecutionContext, session_id: str) -> dict[str, Any]: ...
    def physical_yield(self, recipe_id: str) -> dict[str, Any]: ...


@dataclass
class HostAIEconomyPort:
    """Thin adapter over the existing canonical economic services."""

    costings: Any
    article_changes: Any
    yields: Any

    def incomplete_cost(self, recipe_id: str) -> dict[str, Any]:
        return self.costings.consultar(agregacion="DETAIL_COSTE_INCOMPLETO", escandallo_id=recipe_id)

    def preview_article_change(self, operation: str, article_id: str, values: dict[str, Any],
                               context: AuthorizedExecutionContext, session_id: str) -> dict[str, Any]:
        permitted = {"value", "unidad_origen", "unidad_destino", "unidad_compra", "precio_propuesto"}
        arguments = {key: value for key, value in values.items() if key in permitted}
        return self.article_changes.preview_change(operation=operation, article_id=article_id,
                                                   context=context, session_id=session_id, **arguments)

    def confirm_article_change(self, preview_token: str, context: AuthorizedExecutionContext,
                               session_id: str) -> dict[str, Any]:
        return self.article_changes.confirm_change(preview_token=preview_token, context=context, session_id=session_id)

    def physical_yield(self, recipe_id: str) -> dict[str, Any]:
        if callable(self.yields):
            return self.yields(recipe_id)
        return self.yields.consultar(escandallo_id=recipe_id)


@dataclass
class EconomyDomain:
    port: EconomyPort
    session: SessionContext
    actions: ActionContextStore
    action_ttl_seconds: int = 900

    def register(self, registry: ToolRegistry) -> None:
        definitions = (
            ("economy.incomplete_cost", OperationClass.READ, frozenset({"escandallos:read"}), self._incomplete_cost),
            ("economy.preview_article_change", OperationClass.PREVIEW, frozenset({"articulos:preview"}), self._preview_article_change),
            ("economy.confirm_article_change", OperationClass.CONFIRM, frozenset({"articulos:write"}), self._confirm_article_change),
            ("economy.check_costing", OperationClass.READ, frozenset({"escandallos:read"}), self._check_costing),
            ("economy.physical_yield", OperationClass.PURE_CALC, frozenset({"escandallos:read"}), self._physical_yield),
            ("economy.open_costing", OperationClass.UI_ACTION, frozenset(), self._open_costing),
        )
        for tool_id, operation_class, scopes, handler in definitions:
            registry.register(ToolDefinition(tool_id, tool_id.replace("economy.", "").replace("_", " "), operation_class,
                                             required_scopes=scopes, grounding_requirement="INTERNAL_ECONOMY",
                                             metadata={"domain": ECONOMY_DOMAIN}), handler)

    def _incomplete_cost(self, params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
        recipe_id = self._required(params, "recipe_id")
        detail = self.port.incomplete_cost(recipe_id)
        self.session.active_entity = {"domain": "escandallos", "id": recipe_id, "name": detail.get("nombre", "")}
        incidents = list(detail.get("motivos") or detail.get("economic_incidents") or [])
        state = {"recipe_id": recipe_id, "economic_incidents": incidents, "cost_complete": bool(detail.get("coste_completo"))}
        self.session.set_domain_state(ECONOMY_DOMAIN, state)
        actions = [self._incident_action(recipe_id, incident) for incident in incidents]
        actions.append(self._check_action(recipe_id))
        return ToolResult("OK", str(detail.get("explicacion") or "Economic cost checked."),
                          data={**detail, "actions": [item.to_public_dict() for item in actions]},
                          context_updates={ECONOMY_DOMAIN: state})

    def _preview_article_change(self, params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
        operation = self._required(params, "operation").upper()
        if operation not in {"UPDATE_PRICE", "UPDATE_CONVERSION", "UPDATE_FORMAT"}:
            return ToolResult("ERROR", "Unsupported article change.", error_code="unsupported_operation")
        article_id = self._required(params, "article_id")
        preview = self.port.preview_article_change(operation, article_id, dict(params.get("values") or {}), context, self.session.session_id)
        if not preview.get("ok"):
            return ToolResult("ERROR", str(preview.get("error") or "Preview rejected."), data=preview,
                              error_code=str(preview.get("codigo") or "preview_rejected"))
        stored = self.actions.create("CONFIRM_ARTICLE_CHANGE", self.session.session_id,
                                     {"preview_token": self._required(preview, "preview_token"), "article_id": article_id}, self.action_ttl_seconds)
        action = AgentAction("CONFIRM_ARTICLE_CHANGE", "Confirmar cambio", stored["action_context_id"])
        return ToolResult("OK", "Article change preview ready.",
                          data={**preview, "action": action.to_public_dict(), "datos_reales_modificados": False})

    def _confirm_article_change(self, params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
        try:
            payload = self.actions.consume(self._required(params, "action_context_id"), "CONFIRM_ARTICLE_CHANGE", self.session.session_id)
        except ActionContextError as exc:
            return ToolResult("ERROR", "Invalid article confirmation context.", error_code=exc.code)
        result = self.port.confirm_article_change(payload["preview_token"], context, self.session.session_id)
        data = dict(result)
        recipe_id = str(self.session.get_domain_state(ECONOMY_DOMAIN).get("recipe_id") or "")
        if result.get("ok") and recipe_id:
            data["action"] = self._check_action(recipe_id).to_public_dict()
        return ToolResult("OK" if result.get("ok") else "ERROR", "Article change confirmed." if result.get("ok") else "Article change rejected.", data=data)

    def _check_costing(self, params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
        try:
            payload = self.actions.consume(self._required(params, "action_context_id"), "CHECK_ESCANDALLO_COST", self.session.session_id)
        except ActionContextError as exc:
            return ToolResult("ERROR", "Invalid costing check context.", error_code=exc.code)
        return self._incomplete_cost({"recipe_id": payload["recipe_id"]}, context)

    def _physical_yield(self, params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
        recipe_id = str(params.get("recipe_id") or self.session.get_domain_state(ECONOMY_DOMAIN).get("recipe_id") or "")
        if not recipe_id:
            return ToolResult("ERROR", "Recipe required.", error_code="recipe_id_required")
        result = self.port.physical_yield(recipe_id)
        return ToolResult("OK" if result.get("ok", True) else "ERROR", str(result.get("explicacion") or "Physical yield calculated."), data=result)

    def _open_costing(self, params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
        recipe_id = str(params.get("recipe_id") or self.session.get_domain_state(ECONOMY_DOMAIN).get("recipe_id") or "")
        if not recipe_id:
            return ToolResult("ERROR", "Recipe required.", error_code="recipe_id_required")
        action = AgentAction("OPEN_ESCANDALLO", "Abrir escandallo", ui_action=UIAction("BIBLIOTECA", "ESCANDALLO", recipe_id, "Abrir escandallo"))
        return ToolResult("OK", "Costing sheet ready to open.", data={"action": action.to_public_dict()})

    def _incident_action(self, recipe_id: str, incident: dict[str, Any]) -> AgentAction:
        article_id = str(incident.get("articulo_id") or incident.get("article_id") or "")
        kind = str(incident.get("tipo") or incident.get("type") or "").upper()
        action_id = {"PRECIO_NO_DISPONIBLE": "RESOLVE_MISSING_PRICE",
                     "CONVERSION_NO_DISPONIBLE": "RESOLVE_MISSING_CONVERSION",
                     "FORMATO_NO_DISPONIBLE": "RESOLVE_MISSING_FORMAT"}.get(kind, "RESOLVE_ECONOMIC_INCIDENT")
        stored = self.actions.create(action_id, self.session.session_id,
                                     {"recipe_id": recipe_id, "article_id": article_id, "incident": dict(incident)}, self.action_ttl_seconds)
        return AgentAction(action_id, "Resolver incidencia", stored["action_context_id"])

    def _check_action(self, recipe_id: str) -> AgentAction:
        stored = self.actions.create("CHECK_ESCANDALLO_COST", self.session.session_id, {"recipe_id": recipe_id}, self.action_ttl_seconds)
        return AgentAction("CHECK_ESCANDALLO_COST", "Comprobar escandallo", stored["action_context_id"])

    @staticmethod
    def _required(values: dict[str, Any], key: str) -> str:
        value = str(values.get(key) or "").strip()
        if not value:
            raise ValueError(f"{key}_required")
        return value


def register_economy_domain(registry: ToolRegistry, port: EconomyPort, session: SessionContext,
                            actions: ActionContextStore | None = None) -> EconomyDomain:
    domain = EconomyDomain(port, session, actions or ActionContextStore())
    domain.register(registry)
    return domain
