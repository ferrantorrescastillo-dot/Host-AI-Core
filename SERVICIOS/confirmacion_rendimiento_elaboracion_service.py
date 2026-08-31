from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from CORE.entidades.escandallo import Escandallo
from CORE.entidades.receta import (
    EstadoRendimiento,
    OrigenRendimiento,
    RendimientoNeto,
)
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.schema_escandallos_555a import normalizar_unidad
from SERVICIOS.validador_escandallos_555a import validar_escandallo


class ErrorConfirmacionRendimiento(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ConfirmacionRendimientoElaboracionService:
    """Caso de uso interno para confirmar rendimiento fisico; no se publica como tool."""

    REQUIRED_SCOPE = "escandallos:write"
    PHYSICAL_UNITS = frozenset({"kg", "g", "l", "ml"})
    MODES = frozenset({"TOTAL", "POR_UNIDAD"})
    PROPOSAL_ORIGINS = frozenset({"MANUAL", "TEORICO_COMPLETO", "TEORICO_PARCIAL"})

    def __init__(self, base_dir: Path, repository: RepositorioEscandallos | None = None) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.repository = repository or RepositorioEscandallos(
            self.base_dir / "DATOS" / "db" / "escandallos_canonicos.json"
        )

    def preview(
        self,
        *,
        escandallo_id: str,
        cantidad: Any,
        unidad: str,
        origen: dict[str, Any],
        context: AuthorizedExecutionContext,
        modo: str = "TOTAL",
        propuesta_origen: str = "MANUAL",
    ) -> dict[str, Any]:
        self._authorize(context)
        escandallo = self._find(escandallo_id)
        net_amount, physical_unit, normalized_mode = self._normalize_input(
            escandallo, cantidad, unidad, modo,
        )
        source = self._source(origen, context)
        normalized_proposal_origin = self._proposal_origin(propuesta_origen)
        current_fingerprint = self._fingerprint(escandallo)
        proposed = RendimientoNeto(
            cantidad=float(net_amount),
            unidad=physical_unit,
            estado=EstadoRendimiento.CONFIRMADO,
            origen=source,
        )
        unchanged = self._same_net(escandallo.receta.rendimiento_neto, proposed)
        preview_token = self._preview_token(
            escandallo.receta.codigo, current_fingerprint, proposed, normalized_proposal_origin,
        )
        return {
            "ok": True,
            "estado": "SIN_CAMBIOS" if unchanged else "LISTO_PARA_CONFIRMAR",
            "escandallo_id": escandallo.receta.codigo,
            "rendimiento_declarado": {
                "cantidad": escandallo.receta.rendimiento,
                "unidad": escandallo.receta.unidad_rendimiento,
            },
            "rendimiento_neto_actual": self._net_dict(escandallo.receta.rendimiento_neto),
            "rendimiento_neto_propuesto": self._net_dict(proposed),
            "modo_entrada": normalized_mode,
            "propuesta_origen": normalized_proposal_origin,
            "version_esperada": current_fingerprint,
            "preview_token": preview_token,
            "requiere_confirmacion": not unchanged,
            "incidencias": [],
            "datos_reales_modificados": False,
        }

    def execute(
        self,
        *,
        escandallo_id: str,
        cantidad: Any,
        unidad: str,
        origen: dict[str, Any],
        context: AuthorizedExecutionContext,
        preview_token: str,
        modo: str = "TOTAL",
        propuesta_origen: str = "MANUAL",
        acepta_estimacion_parcial: bool = False,
    ) -> dict[str, Any]:
        preview = self.preview(
            escandallo_id=escandallo_id,
            cantidad=cantidad,
            unidad=unidad,
            origen=origen,
            context=context,
            modo=modo,
            propuesta_origen=propuesta_origen,
        )
        if not preview_token or preview_token != preview["preview_token"]:
            raise ErrorConfirmacionRendimiento(
                "stale_or_invalid_preview", "La vista previa no corresponde al estado actual.",
            )
        if preview["propuesta_origen"] == "TEORICO_PARCIAL" and acepta_estimacion_parcial is not True:
            raise ErrorConfirmacionRendimiento(
                "partial_estimate_acceptance_required",
                "Debes confirmar expresamente que la estimacion parcial corresponde al rendimiento fisico real.",
            )
        escandallo = self._find(escandallo_id)
        if preview["estado"] == "SIN_CAMBIOS":
            return {
                **preview,
                "estado": "SIN_CAMBIOS",
                "rendimiento_neto": self._net_dict(escandallo.receta.rendimiento_neto),
                "idempotente": True,
                "datos_reales_modificados": False,
            }

        proposed_data = dict(preview["rendimiento_neto_propuesto"] or {})
        escandallo.receta.rendimiento_neto = RendimientoNeto.desde_dict(proposed_data)
        validation = validar_escandallo(escandallo)
        if not validation.valido:
            raise ErrorConfirmacionRendimiento(
                "invalid_recipe", "El escandallo no admite la confirmacion: " + " | ".join(validation.errores),
            )
        action = self.repository.upsert(escandallo)
        persisted = self._find(escandallo.receta.codigo)
        return {
            "ok": True,
            "estado": "CONFIRMADO",
            "accion": action,
            "escandallo_id": persisted.receta.codigo,
            "rendimiento_declarado": {
                "cantidad": persisted.receta.rendimiento,
                "unidad": persisted.receta.unidad_rendimiento,
            },
            "rendimiento_neto": self._net_dict(persisted.receta.rendimiento_neto),
            "idempotente": False,
            "datos_reales_modificados": True,
        }

    def _authorize(self, context: AuthorizedExecutionContext) -> None:
        if not isinstance(context, AuthorizedExecutionContext):
            raise ErrorConfirmacionRendimiento("unauthorized", "Falta contexto autorizado.")
        valid, _reason = context.validate()
        if not valid or self.REQUIRED_SCOPE not in context.scopes:
            raise ErrorConfirmacionRendimiento("unauthorized", "El actor no esta autorizado.")

    def _find(self, identity: str) -> Escandallo:
        key = str(identity or "").strip().casefold()
        if not key or any(char in key for char in ("/", "\\")):
            raise ErrorConfirmacionRendimiento("invalid_escandallo_id", "Identificador no valido.")
        for item in self.repository.listar():
            if key == item.receta.codigo.strip().casefold():
                return item
        raise ErrorConfirmacionRendimiento("escandallo_not_found", "Escandallo no encontrado.")

    def _normalize_input(
        self, escandallo: Escandallo, cantidad: Any, unidad: str, modo: str,
    ) -> tuple[Decimal, str, str]:
        normalized_mode = str(modo or "TOTAL").strip().upper()
        if normalized_mode not in self.MODES:
            raise ErrorConfirmacionRendimiento("invalid_mode", "Modo de entrada no admitido.")
        try:
            amount = Decimal(str(cantidad))
        except (InvalidOperation, ValueError):
            raise ErrorConfirmacionRendimiento("invalid_quantity", "Cantidad no valida.")
        if not amount.is_finite() or amount <= 0:
            raise ErrorConfirmacionRendimiento("invalid_quantity", "Cantidad debe ser finita y mayor que cero.")
        physical_unit = normalizar_unidad(unidad)
        if physical_unit not in self.PHYSICAL_UNITS:
            raise ErrorConfirmacionRendimiento("invalid_unit", "Unidad fisica no admitida.")
        if normalized_mode == "POR_UNIDAD":
            declared_unit = normalizar_unidad(escandallo.receta.unidad_rendimiento)
            if declared_unit != "u" or not math.isfinite(float(escandallo.receta.rendimiento)) or escandallo.receta.rendimiento <= 0:
                raise ErrorConfirmacionRendimiento(
                    "invalid_declared_yield", "El modo por unidad requiere rendimiento positivo en unidades.",
                )
            amount *= Decimal(str(escandallo.receta.rendimiento))
        return amount, physical_unit, normalized_mode

    @staticmethod
    def _source(origen: dict[str, Any], context: AuthorizedExecutionContext) -> OrigenRendimiento:
        source = dict(origen or {}) if isinstance(origen, dict) else {}
        if str(source.get("tipo") or "").strip().upper() != "USUARIO":
            raise ErrorConfirmacionRendimiento("invalid_origin", "El origen debe identificar una confirmacion de usuario.")
        reference = str(source.get("referencia") or "").strip() or None
        if reference and len(reference) > 200:
            raise ErrorConfirmacionRendimiento("invalid_origin", "La referencia de origen es demasiado larga.")
        return OrigenRendimiento(
            tipo="USUARIO",
            referencia=reference,
            fecha=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            actor_id=context.user_id,
        )

    @classmethod
    def _proposal_origin(cls, value: str) -> str:
        normalized = str(value or "MANUAL").strip().upper()
        if normalized not in cls.PROPOSAL_ORIGINS:
            raise ErrorConfirmacionRendimiento("invalid_proposal_origin", "Origen de propuesta no admitido.")
        return normalized

    @staticmethod
    def _fingerprint(escandallo: Escandallo) -> str:
        payload = json.dumps(asdict(escandallo), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def _preview_token(
        cls, escandallo_id: str, fingerprint: str, proposed: RendimientoNeto, proposal_origin: str,
    ) -> str:
        source = proposed.origen
        payload = json.dumps(
            {
                "escandallo_id": escandallo_id,
                "version": fingerprint,
                "propuesta_origen": proposal_origin,
                "propuesto": {
                    "cantidad": proposed.cantidad,
                    "unidad": proposed.unidad,
                    "estado": proposed.estado,
                    "origen": {
                        "tipo": source.tipo if source else None,
                        "referencia": source.referencia if source else None,
                        "actor_id": source.actor_id if source else None,
                    },
                },
            },
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _same_net(current: RendimientoNeto | None, proposed: RendimientoNeto) -> bool:
        if current is None:
            return False
        return (
            Decimal(str(current.cantidad)) == Decimal(str(proposed.cantidad))
            and normalizar_unidad(current.unidad) == normalizar_unidad(proposed.unidad)
            and current.estado is EstadoRendimiento.CONFIRMADO
        )

    @staticmethod
    def _net_dict(value: RendimientoNeto | None) -> dict[str, Any] | None:
        return asdict(value) if value is not None else None


__all__ = ["ConfirmacionRendimientoElaboracionService", "ErrorConfirmacionRendimiento"]
