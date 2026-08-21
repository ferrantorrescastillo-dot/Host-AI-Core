from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .action_context import ActionContextError, ActionContextStore
from .contracts import AgentAction, AuthorizedExecutionContext, OperationClass, ToolDefinition, ToolResult, UIAction
from .session_context import SessionContext
from .tool_registry import ToolRegistry

RESERVATIONS_DOMAIN = "reservations"


class ReservationsPort(Protocol):
    def list_reservations(self, filters: dict[str, Any]) -> list[dict[str, Any]]: ...
    def reservation_detail(self, reservation_id: str) -> dict[str, Any] | None: ...
    def preview_reservation(self, operation: str, reservation_id: str, payload: dict[str, Any],
                            context: AuthorizedExecutionContext, session_id: str) -> dict[str, Any]: ...
    def confirm_reservation(self, preview_token: str, context: AuthorizedExecutionContext,
                            session_id: str) -> dict[str, Any]: ...


@dataclass
class HostAIReservationsPort:
    reads: Any
    writes: Any

    def list_reservations(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        allowed = {"fecha", "estado", "servicio", "nombre", "limite", "desde"}
        return self.reads.listar(**{key: value for key, value in filters.items() if key in allowed})

    def reservation_detail(self, reservation_id: str) -> dict[str, Any] | None:
        return self.reads.detalle(reservation_id)

    def preview_reservation(self, operation: str, reservation_id: str, payload: dict[str, Any],
                            context: AuthorizedExecutionContext, session_id: str) -> dict[str, Any]:
        return self.writes.preview(operacion=operation, reserva_id=reservation_id, payload=payload,
                                   context=context, session_id=session_id)

    def confirm_reservation(self, preview_token: str, context: AuthorizedExecutionContext,
                            session_id: str) -> dict[str, Any]:
        return self.writes.confirm(preview_token=preview_token, context=context, session_id=session_id)


@dataclass
class ReservationsDomain:
    port: ReservationsPort
    session: SessionContext
    actions: ActionContextStore
    action_ttl_seconds: int = 900

    def register(self, registry: ToolRegistry) -> None:
        definitions = (
            ("reservations.list", OperationClass.READ, frozenset({"reservas:read"}), self._list),
            ("reservations.detail", OperationClass.READ, frozenset({"reservas:read"}), self._detail),
            ("reservations.preview", OperationClass.PREVIEW, frozenset({"reservas:preview"}), self._preview),
            ("reservations.confirm", OperationClass.CONFIRM, frozenset({"reservas:write"}), self._confirm),
            ("reservations.open", OperationClass.UI_ACTION, frozenset(), self._open),
        )
        for tool_id, operation_class, scopes, handler in definitions:
            registry.register(ToolDefinition(tool_id, tool_id.replace("reservations.", "").replace("_", " "),
                                             operation_class, required_scopes=scopes,
                                             grounding_requirement="INTERNAL_RESERVATIONS",
                                             metadata={"domain": RESERVATIONS_DOMAIN}), handler)

    def _list(self, params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
        items = self.port.list_reservations(params)
        state = {"last_filters": dict(params), "candidate_ids": [str(item.get("reserva_id") or "") for item in items]}
        self.session.set_domain_state(RESERVATIONS_DOMAIN, state)
        return ToolResult("OK", "Reservations listed.", data={"reservas": items, "total": len(items)},
                          context_updates={RESERVATIONS_DOMAIN: state})

    def _detail(self, params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
        reservation_id = self._required(params, "reservation_id").upper()
        item = self.port.reservation_detail(reservation_id)
        if item is None:
            return ToolResult("ERROR", "Reservation not found.", error_code="reservation_not_found")
        self.session.active_entity = {"domain": RESERVATIONS_DOMAIN, "id": reservation_id,
                                      "name": str(item.get("nombre_cliente") or "")}
        state = {**self.session.get_domain_state(RESERVATIONS_DOMAIN), "reservation_id": reservation_id,
                 "reservation_state": item.get("estado")}
        self.session.set_domain_state(RESERVATIONS_DOMAIN, state)
        return ToolResult("OK", "Reservation detail loaded.", data={"reserva": item},
                          context_updates={RESERVATIONS_DOMAIN: state})

    def _preview(self, params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
        operation = self._required(params, "operation").upper()
        if operation not in {"CREAR", "MODIFICAR", "CONFIRMAR", "CANCELAR", "NO_SHOW", "COMPLETAR"}:
            return ToolResult("ERROR", "Unsupported reservation operation.", error_code="invalid_operation")
        reservation_id = str(params.get("reservation_id") or "").strip().upper()
        if operation != "CREAR" and not reservation_id:
            reservation_id = str(self.session.get_domain_state(RESERVATIONS_DOMAIN).get("reservation_id") or "")
        try:
            preview = self.port.preview_reservation(operation, reservation_id, dict(params.get("payload") or {}),
                                                     context, self.session.session_id)
        except Exception as exc:
            return ToolResult("ERROR", str(exc), error_code=str(getattr(exc, "code", "preview_rejected")))
        stored = self.actions.create("CONFIRM_RESERVATION_CHANGE", self.session.session_id,
                                     {"preview_token": self._required(preview, "preview_token")}, self.action_ttl_seconds)
        action = AgentAction("CONFIRM_RESERVATION_CHANGE", "Confirmar cambio", stored["action_context_id"])
        return ToolResult("OK", "Reservation preview ready.",
                          data={**preview, "action": action.to_public_dict(), "datos_reales_modificados": False})

    def _confirm(self, params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
        try:
            payload = self.actions.consume(self._required(params, "action_context_id"),
                                           "CONFIRM_RESERVATION_CHANGE", self.session.session_id)
        except ActionContextError as exc:
            return ToolResult("ERROR", "Invalid reservation confirmation context.", error_code=exc.code)
        try:
            result = self.port.confirm_reservation(payload["preview_token"], context, self.session.session_id)
        except Exception as exc:
            return ToolResult("ERROR", str(exc), error_code=str(getattr(exc, "code", "confirmation_rejected")))
        reservation = dict(result.get("reserva") or {})
        reservation_id = str(reservation.get("reserva_id") or "")
        if reservation_id:
            self.session.active_entity = {"domain": RESERVATIONS_DOMAIN, "id": reservation_id,
                                          "name": str(reservation.get("nombre_cliente") or "")}
            self.session.set_domain_state(RESERVATIONS_DOMAIN,
                                          {"reservation_id": reservation_id, "reservation_state": reservation.get("estado")})
        return ToolResult("OK", "Reservation change confirmed.", data=result,
                          context_updates={RESERVATIONS_DOMAIN: self.session.get_domain_state(RESERVATIONS_DOMAIN)})

    def _open(self, params: dict[str, Any], context: AuthorizedExecutionContext) -> ToolResult:
        reservation_id = str(params.get("reservation_id") or self.session.get_domain_state(RESERVATIONS_DOMAIN).get("reservation_id") or "")
        if not reservation_id:
            return ToolResult("ERROR", "Reservation required.", error_code="reservation_id_required")
        action = AgentAction("OPEN_RESERVATION", "Abrir reserva",
                             ui_action=UIAction("RESERVAS", "DETAIL", reservation_id, "Abrir reserva"))
        return ToolResult("OK", "Reservation ready to open.", data={"action": action.to_public_dict()})

    @staticmethod
    def _required(values: dict[str, Any], key: str) -> str:
        value = str(values.get(key) or "").strip()
        if not value:
            raise ValueError(f"{key}_required")
        return value


def register_reservations_domain(registry: ToolRegistry, port: ReservationsPort, session: SessionContext,
                                 actions: ActionContextStore | None = None) -> ReservationsDomain:
    domain = ReservationsDomain(port, session, actions or ActionContextStore())
    domain.register(registry)
    return domain
