from __future__ import annotations

from dataclasses import replace
from datetime import datetime, time, timedelta
import hashlib
import json
from pathlib import Path
import secrets
from threading import RLock
from typing import Any, Callable

from MODELOS.reserva import RESERVA_ID_PATTERN, Reserva
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.host_ai_platform.contracts import AuthorizedExecutionContext as PlatformAuthorizedExecutionContext
from SERVICIOS.repositorio_reservas import RepositorioReservas
from SERVICIOS.reservas_read_service import ReservasReadService


class ErrorReservasWrite(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ReservasWriteService:
    REQUIRED_SCOPE = "reservas:write"
    PREVIEW_SCOPE = "reservas:preview"
    EDITABLE_FIELDS = frozenset({"nombre_cliente", "fecha", "hora", "pax", "servicio", "observaciones", "evento_id"})
    TRANSITIONS = {
        "PENDIENTE": frozenset({"CONFIRMADA", "CANCELADA"}),
        "CONFIRMADA": frozenset({"CANCELADA", "NO_SHOW", "COMPLETADA"}),
        "CANCELADA": frozenset(), "NO_SHOW": frozenset(), "COMPLETADA": frozenset(),
    }
    TERMINAL_STATES = frozenset({"CANCELADA", "NO_SHOW", "COMPLETADA"})
    OPERATIONS = frozenset({"CREAR", "MODIFICAR", "CONFIRMAR", "CANCELAR", "NO_SHOW", "COMPLETAR"})
    _lock = RLock()

    def __init__(self, base_dir: Path | str, *, now_provider: Callable[[], datetime] = datetime.now, ttl_seconds: int = 900) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.repo = RepositorioReservas(self.base_dir)
        self.read = ReservasReadService(self.base_dir)
        self.now_provider = now_provider
        self.ttl_seconds = max(30, int(ttl_seconds))
        self.audit_path = self.base_dir / "DATOS" / "auditoria" / "reservas.jsonl"
        self._pending: dict[str, dict[str, Any]] = {}
        self._completed: dict[str, dict[str, Any]] = {}

    def preview(self, *, operacion: str, payload: dict[str, Any], context: AuthorizedExecutionContext, reserva_id: str = "", session_id: str = "") -> dict[str, Any]:
        self._authorize_preview(context)
        operation = str(operacion or "").strip().upper()
        if operation not in self.OPERATIONS:
            raise ErrorReservasWrite("invalid_operation", "Operacion de reserva no permitida.")
        data = dict(payload or {})
        identity = str(reserva_id or data.pop("reserva_id", "") or "").strip().upper()
        current = self._current(identity) if operation != "CREAR" else None
        if current is not None:
            self._ensure_state_allows_operation(current, operation)
        if operation == "CREAR":
            if identity:
                raise ErrorReservasWrite("immutable_field", "reserva_id se genera internamente.")
            proposed = self._build_create(data)
            before, expected = None, "NEW"
        elif operation == "MODIFICAR":
            self._validate_edit_fields(data)
            try:
                proposed = Reserva.from_dict({**current.to_dict(), **data, "actualizado_en": current.actualizado_en})
                self.read.validar_evento(proposed)
            except ValueError as exc:
                raise ErrorReservasWrite("invalid_reserva", str(exc)) from exc
            before, expected = current.to_dict(), self._fingerprint(current)
        else:
            if data:
                raise ErrorReservasWrite("unknown_fields", "La transicion no acepta campos adicionales.")
            target = {"CONFIRMAR": "CONFIRMADA", "CANCELAR": "CANCELADA", "NO_SHOW": "NO_SHOW", "COMPLETAR": "COMPLETADA"}[operation]
            if target not in self.TRANSITIONS[current.estado]:
                raise ErrorReservasWrite("invalid_transition", f"Transicion {current.estado} -> {target} no permitida.")
            proposed = replace(current, estado=target)
            before, expected = current.to_dict(), self._fingerprint(current)
        normalized = proposed.to_dict()
        token = secrets.token_urlsafe(32)
        expires = self.now_provider() + timedelta(seconds=self.ttl_seconds)
        self._pending[token] = {
            "operacion": operation, "reserva_id": identity, "payload": normalized,
            "expected": expected, "actor": self._actor_key(context, session_id), "expires": expires,
            "payload_hash": self._payload_hash(normalized), "before": before,
        }
        return {
            "ok": True, "estado": "LISTO_PARA_CONFIRMAR", "operacion": operation,
            "reserva_id": identity or None, "antes": self._safe_preview(before),
            "propuesto": self._safe_preview(normalized), "preview_token": token,
            "expira_en": expires.isoformat(timespec="seconds"), "requiere_confirmacion": True,
            "datos_reales_modificados": False,
        }

    def confirm(self, *, preview_token: str, context: AuthorizedExecutionContext, session_id: str = "") -> dict[str, Any]:
        self._authorize(context)
        token = str(preview_token or "").strip()
        with self._lock:
            if token in self._completed:
                completed = self._completed[token]
                if completed["actor"] != self._actor_key(context, session_id):
                    raise ErrorReservasWrite("invalid_preview", "La confirmacion no pertenece a esta sesion.")
                return {**completed["result"], "idempotente": True}
            item = self._pending.get(token)
            if not item:
                raise ErrorReservasWrite("invalid_preview", "Token de confirmacion invalido.")
            if item["actor"] != self._actor_key(context, session_id):
                raise ErrorReservasWrite("invalid_preview", "La confirmacion no pertenece a esta sesion.")
            if self.now_provider() > item["expires"]:
                self._pending.pop(token, None)
                raise ErrorReservasWrite("expired_preview", "La vista previa ha caducado.")
            current = self.repo.obtener(item["reserva_id"]) if item["reserva_id"] else None
            actual = self._fingerprint(current) if current else "NEW"
            if actual != item["expected"]:
                raise ErrorReservasWrite("stale_preview", "La reserva ha cambiado desde la vista previa.")
            reservations = self.repo.listar()
            proposed = Reserva.from_dict(item["payload"])
            now = self.now_provider().isoformat(timespec="seconds")
            if item["operacion"] == "CREAR":
                proposed = replace(proposed, creado_en=now, actualizado_en=now)
                reservations.append(proposed)
                previous_state = None
            else:
                proposed = replace(proposed, actualizado_en=now)
                reservations = [proposed if value.reserva_id == proposed.reserva_id else value for value in reservations]
                previous_state = str((item["before"] or {}).get("estado") or "") or None
            data_snapshot = self.repo.path.read_bytes() if self.repo.path.exists() else None
            audit_snapshot = self.audit_path.read_bytes() if self.audit_path.exists() else None
            try:
                self.repo.guardar_todos(reservations)
                self._audit(context, item, proposed, previous_state)
            except Exception:
                self._restore(self.repo.path, data_snapshot)
                self._restore(self.audit_path, audit_snapshot)
                raise
            result = {
                "ok": True, "estado": "CONFIRMADO", "operacion": item["operacion"],
                "reserva": proposed.to_dict(), "idempotente": False,
                "datos_reales_modificados": True,
            }
            self._pending.pop(token, None)
            self._completed[token] = {"actor": item["actor"], "result": result}
            return result

    def _build_create(self, data: dict[str, Any]) -> Reserva:
        allowed = self.EDITABLE_FIELDS | {"estado"}
        if set(data) - allowed:
            raise ErrorReservasWrite("unknown_fields", "La reserva contiene campos no permitidos.")
        state = str(data.get("estado") or "PENDIENTE").upper()
        if state not in {"PENDIENTE", "CONFIRMADA"}:
            raise ErrorReservasWrite("invalid_initial_state", "El estado inicial debe ser PENDIENTE o CONFIRMADA explicita.")
        try:
            normalized = dict(data)
            normalized["servicio"] = str(normalized.get("servicio") or self._service_for_time(normalized.get("hora"))).upper()
            item = Reserva.crear(**{**normalized, "estado": state})
            self.read.validar_evento(item)
            return item
        except ValueError as exc:
            raise ErrorReservasWrite("invalid_reserva", str(exc)) from exc

    @staticmethod
    def _service_for_time(value: Any) -> str:
        """Canonical R4 fallback: evening reservations are CENA; earlier ones COMIDA."""
        try:
            parsed = time.fromisoformat(str(value or ""))
        except ValueError as exc:
            raise ErrorReservasWrite("invalid_reserva", "hora debe usar HH:MM") from exc
        return "CENA" if parsed >= time(18, 0) else "COMIDA"

    def _validate_edit_fields(self, data: dict[str, Any]) -> None:
        if not data or set(data) - self.EDITABLE_FIELDS:
            raise ErrorReservasWrite("immutable_or_unknown_fields", "Solo pueden modificarse campos editables de la reserva.")

    def _ensure_state_allows_operation(self, current: Reserva, operation: str) -> None:
        if current.estado in self.TERMINAL_STATES:
            raise ErrorReservasWrite(
                "terminal_state",
                f"La reserva esta {current.estado} y no admite modificaciones ni cambios de estado.",
            )

    def _current(self, reserva_id: str) -> Reserva:
        if RESERVA_ID_PATTERN.fullmatch(reserva_id) is None:
            raise ErrorReservasWrite("invalid_reserva_id", "Identificador de reserva no valido.")
        item = self.repo.obtener(reserva_id)
        if not item:
            raise ErrorReservasWrite("reserva_not_found", "Reserva no encontrada.")
        return item

    def _authorize(self, context: AuthorizedExecutionContext) -> None:
        if not isinstance(context, (AuthorizedExecutionContext, PlatformAuthorizedExecutionContext)):
            raise ErrorReservasWrite("unauthorized", "Falta contexto autorizado.")
        valid, _ = context.validate()
        if not valid or self.REQUIRED_SCOPE not in context.scopes:
            raise ErrorReservasWrite("unauthorized", "El actor no esta autorizado.")

    def _authorize_preview(self, context: AuthorizedExecutionContext) -> None:
        if not isinstance(context, (AuthorizedExecutionContext, PlatformAuthorizedExecutionContext)):
            raise ErrorReservasWrite("unauthorized", "Falta contexto autorizado.")
        valid, _ = context.validate()
        if not valid or not ({self.PREVIEW_SCOPE, self.REQUIRED_SCOPE} & context.scopes):
            raise ErrorReservasWrite("unauthorized", "El actor no esta autorizado para preparar la vista previa.")

    def _audit(self, context: AuthorizedExecutionContext, pending: dict[str, Any], proposed: Reserva, previous_state: str | None) -> None:
        event = {
            "request_id": context.request_id, "operacion": pending["operacion"],
            "reserva_id": proposed.reserva_id, "estado_anterior": previous_state,
            "estado_nuevo": proposed.estado, "timestamp": self.now_provider().isoformat(timespec="seconds"),
            "resultado": "CONFIRMADO", "actor": context.user_id,
            "tenant_hash": hashlib.sha256(context.tenant_id.encode()).hexdigest()[:16],
            "payload_hash": pending["payload_hash"],
        }
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    @staticmethod
    def _safe_preview(value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None: return None
        return {key: value.get(key) for key in ("reserva_id", "nombre_cliente", "fecha", "hora", "pax", "estado", "servicio", "observaciones", "evento_id") if key in value}

    @staticmethod
    def _fingerprint(item: Reserva | None) -> str:
        if item is None: return "NEW"
        return ReservasWriteService._payload_hash(item.to_dict())

    @staticmethod
    def _payload_hash(value: dict[str, Any]) -> str:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _actor_key(context: AuthorizedExecutionContext, session_id: str) -> tuple[str, str, str]:
        return context.user_id, context.tenant_id, str(session_id or "")

    @staticmethod
    def _restore(path: Path, content: bytes | None) -> None:
        if content is None:
            if path.exists(): path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)


__all__ = ["ReservasWriteService", "ErrorReservasWrite"]
