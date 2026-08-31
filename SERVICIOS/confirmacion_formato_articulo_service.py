from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from pathlib import Path
import secrets
from threading import RLock
from typing import Any, Callable

from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.articulo_economico_canonico import merge_physical_conversion


class ErrorConfirmacionFormatoArticulo(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ConfirmacionFormatoArticuloService:
    """Preview/confirmación segura sobre el editor canónico de Artículos."""

    REQUIRED_SCOPE = "articulos:write"
    CONTENT_UNITS = frozenset({"kg", "g", "l", "ml", "u"})
    _lock = RLock()

    def __init__(self, base_dir: Path, articles: ArticulosCatalogReadService | None = None, *, ttl_seconds: int = 900, now_provider: Callable[[], datetime] = datetime.now) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.articles = articles or ArticulosCatalogReadService(self.base_dir)
        self.ttl_seconds = max(30, int(ttl_seconds))
        self.now_provider = now_provider
        self.audit_path = self.base_dir / "DATOS" / "auditoria" / "articulos.jsonl"
        self._pending: dict[str, dict[str, Any]] = {}
        self._completed: dict[str, dict[str, Any]] = {}

    def preview_change(
        self, *, operation: str, article_id: str, value: Any,
        context: AuthorizedExecutionContext, session_id: str = "",
        unidad_origen: str = "", unidad_destino: str = "", unidad_compra: str = "",
        precio_propuesto: Any = None,
    ) -> dict[str, Any]:
        self._authorize_preview(context)
        current = self._find(article_id)
        op = str(operation or "").strip().upper()
        before: dict[str, Any]
        proposed: dict[str, Any]
        if op == "UPDATE_PRICE":
            price = self._positive_decimal(value, "invalid_price", "El precio debe ser mayor que cero.")
            before = {"precio": current.get("precio")}
            proposed = {"precio": float(price)}
        elif op == "UPDATE_CONVERSION":
            factor = self._positive_decimal(value, "invalid_conversion_factor", "La conversión debe ser mayor que cero.")
            if factor > Decimal("1000000000"):
                raise ErrorConfirmacionFormatoArticulo("invalid_conversion_factor", "La conversión excede el límite admitido.")
            source = str(unidad_origen or "").strip().lower()
            target = str(unidad_destino or "").strip().lower()
            if source not in self.CONTENT_UNITS or target not in self.CONTENT_UNITS or source == target:
                raise ErrorConfirmacionFormatoArticulo("incompatible_units", "Las unidades de la conversión no son compatibles.")
            before = {"conversion_unidades": current.get("conversion_unidades") or []}
            proposed = {"conversion_unidades": merge_physical_conversion(
                current.get("conversion_unidades"), source, target, factor,
            )}
        elif op == "UPDATE_FORMAT":
            quantity = self._positive_decimal(value, "invalid_format_quantity", "La cantidad del formato debe ser mayor que cero.")
            purchase_unit = str(unidad_compra or "").strip().lower()
            content_unit = str(unidad_destino or unidad_origen or "").strip().lower()
            if not purchase_unit:
                raise ErrorConfirmacionFormatoArticulo("invalid_purchase_unit", "Falta la unidad de compra.")
            if content_unit not in self.CONTENT_UNITS:
                raise ErrorConfirmacionFormatoArticulo("invalid_format_unit", "La unidad del contenido no es válida.")
            format_before = {
                "unidad_compra": current.get("unidad_compra") or None,
                "cantidad_formato": self._contract(current)["cantidad_formato"],
                "unidad_formato": current.get("unidad_formato") or None,
                "unidad_base": current.get("unidad_base") or None,
            }
            format_proposed = {
                "unidad_compra": purchase_unit, "cantidad_formato": float(quantity),
                "unidad_formato": content_unit, "unidad_base": content_unit,
            }
            if precio_propuesto not in (None, ""):
                proposed_price = self._positive_decimal(
                    precio_propuesto, "invalid_price", "El precio debe ser mayor que cero.",
                )
                before = {"precio": current.get("precio"), **format_before}
                proposed = {"precio": float(proposed_price), **format_proposed}
            else:
                before, proposed = format_before, format_proposed
        else:
            raise ErrorConfirmacionFormatoArticulo("invalid_operation", "Operación de artículo no permitida.")
        fingerprint = self._fingerprint(current)
        token = secrets.token_urlsafe(32)
        expires = self.now_provider() + timedelta(seconds=self.ttl_seconds)
        actor = self._actor_key(context, session_id)
        self._pending[token] = {
            "operation": op, "article_id": str(current.get("codigo") or article_id),
            "before": before, "proposed": proposed, "expected": fingerprint,
            "actor": actor, "expires": expires, "change_hash": self._change_hash(op, proposed),
        }
        derived: dict[str, Any] = {}
        if op == "UPDATE_CONVERSION":
            derived = {
                "conversion_factor_display": format(factor, "f"),
                "unidad_origen": source, "unidad_destino": target,
            }
        effective_price = proposed.get("precio", current.get("precio"))
        if op == "UPDATE_FORMAT" and effective_price not in (None, ""):
            package_price = self._positive_decimal(effective_price, "invalid_price", "El precio debe ser mayor que cero.")
            unit_price = package_price / quantity
            derived = {"precio_unitario": str(unit_price), "unidad_precio": content_unit}
        presentation = self._presentation(current, op, before, proposed, derived)
        return {
            "ok": True, "estado": "LISTO_PARA_CONFIRMAR", "operacion": op,
            "articulo_id": str(current.get("codigo") or article_id),
            "articulo_nombre": str(current.get("nombre") or ""), "antes": before,
            "propuesto": proposed, "derivado": derived, "presentation": presentation,
            "preview_token": token,
            "expira_en": expires.isoformat(timespec="seconds"), "requiere_confirmacion": True,
            "datos_reales_modificados": False,
        }

    def confirm_change(
        self, *, preview_token: str, context: AuthorizedExecutionContext, session_id: str = "",
    ) -> dict[str, Any]:
        self._authorize(context)
        token = str(preview_token or "").strip()
        actor = self._actor_key(context, session_id)
        with self._lock:
            completed = self._completed.get(token)
            if completed:
                if completed["actor"] != actor:
                    raise ErrorConfirmacionFormatoArticulo("invalid_preview", "La confirmación no pertenece a esta sesión.")
                return {**completed["result"], "idempotente": True}
            pending = self._pending.get(token)
            if not pending or pending["actor"] != actor:
                raise ErrorConfirmacionFormatoArticulo("invalid_preview", "La confirmación no pertenece a esta sesión.")
            if self.now_provider() > pending["expires"]:
                self._pending.pop(token, None)
                raise ErrorConfirmacionFormatoArticulo("expired_preview", "La vista previa ha caducado.")
            current = self._find(pending["article_id"])
            if self._fingerprint(current) != pending["expected"]:
                raise ErrorConfirmacionFormatoArticulo("stale_preview", "El artículo ha cambiado desde la vista previa.")
            body = {"confirmacion": "ACTUALIZAR_ARTICULO_MAESTRO", **pending["proposed"]}
            repository = self.articles.catalogo.repositorio
            paths = (repository.path_articulos, repository.path_historico_precios, self.audit_path)
            snapshots = {path: path.read_bytes() if path.exists() else None for path in paths}
            try:
                result = self.articles.actualizar(pending["article_id"], body, audit_context={
                    "user_id": context.user_id, "tenant_id": context.tenant_id,
                    "request_id": context.request_id,
                })
                if not result.get("ok"):
                    error = dict(result.get("error") or {})
                    raise ErrorConfirmacionFormatoArticulo(
                        str(error.get("code") or "article_update_failed"),
                        str(error.get("message") or "No se pudo actualizar el artículo."),
                    )
                self._audit_change(context, pending)
            except Exception:
                self._restore(snapshots)
                raise
            confirmed = {
                "ok": True, "estado": "CONFIRMADO", "operacion": pending["operation"],
                "articulo_id": pending["article_id"], "articulo": result.get("articulo"),
                "idempotente": False, "datos_reales_modificados": True,
            }
            self._pending.pop(token, None)
            self._completed[token] = {"actor": actor, "result": confirmed}
            return confirmed

    def discard_change(self, *, preview_token: str, context: AuthorizedExecutionContext, session_id: str = "") -> dict[str, Any]:
        self._authorize_preview(context)
        token = str(preview_token or "").strip()
        pending = self._pending.get(token)
        if not pending or pending["actor"] != self._actor_key(context, session_id):
            raise ErrorConfirmacionFormatoArticulo("invalid_preview", "La vista previa no pertenece a esta sesión.")
        self._pending.pop(token, None)
        return {"ok": True, "estado": "DESCARTADO", "datos_reales_modificados": False}

    def preview(
        self, *, article_id: str, precio: Any, unidad_compra: str,
        cantidad_formato: Any, unidad_formato: str,
        context: AuthorizedExecutionContext, cantidad_uso: Any = None,
        unidad_uso: str = "",
    ) -> dict[str, Any]:
        self._authorize(context)
        current = self._find(article_id)
        price = self._positive_decimal(precio, "invalid_price", "El precio debe ser mayor que cero.")
        format_quantity = self._positive_decimal(
            cantidad_formato, "invalid_format_quantity",
            "La cantidad del formato debe ser mayor que cero.",
        )
        purchase_unit = str(unidad_compra or "").strip().lower()
        content_unit = str(unidad_formato or "").strip().lower()
        if not purchase_unit:
            raise ErrorConfirmacionFormatoArticulo("invalid_purchase_unit", "Falta la unidad de compra.")
        if content_unit not in self.CONTENT_UNITS:
            raise ErrorConfirmacionFormatoArticulo("invalid_format_unit", "Unidad de contenido no admitida.")

        before = self._contract(current)
        proposed = {
            "precio": float(price),
            "unidad_compra": purchase_unit,
            "cantidad_formato": float(format_quantity),
            "unidad_formato": content_unit,
            "unidad_base": content_unit,
            "unidad_base_sugerida": False,
            "estado_unidad_base": "CONFIRMADA",
        }
        unit_price = price / format_quantity
        usage = self._usage(cantidad_uso, unidad_uso, content_unit, unit_price)
        fingerprint = self._fingerprint(current)
        token = self._token(article_id, fingerprint, proposed, context)
        return {
            "ok": True,
            "estado": "SIN_CAMBIOS" if before == proposed else "LISTO_PARA_CONFIRMAR",
            "articulo_id": str(current.get("codigo") or article_id),
            "antes": before,
            "propuesto": proposed,
            "derivado": {
                "precio_unitario": str(unit_price),
                "unidad_precio": content_unit,
                **({"uso": usage} if usage is not None else {}),
            },
            "version_esperada": fingerprint,
            "preview_token": token,
            "requiere_confirmacion": before != proposed,
            "actor": {
                "user_id": context.user_id,
                "tenant_id": context.tenant_id,
                "request_id": context.request_id,
            },
            "datos_reales_modificados": False,
        }

    def execute(self, *, preview_token: str, **kwargs: Any) -> dict[str, Any]:
        context = kwargs.get("context")
        with self._lock:
            preview = self.preview(**kwargs)
            if not preview_token or preview_token != preview["preview_token"]:
                raise ErrorConfirmacionFormatoArticulo(
                    "stale_or_invalid_preview",
                    "La vista previa no corresponde al estado actual del artículo.",
                )
            if preview["estado"] == "SIN_CAMBIOS":
                return {**preview, "idempotente": True, "datos_reales_modificados": False}

            article_id = str(preview["articulo_id"])
            current = self._find(article_id)
            body = {
                "confirmacion": "ACTUALIZAR_ARTICULO_MAESTRO",
                "nombre": current.get("nombre"),
                "unidad_base": preview["propuesto"]["unidad_base"],
                "precio": preview["propuesto"]["precio"],
                "unidad_compra": preview["propuesto"]["unidad_compra"],
                "cantidad_formato": preview["propuesto"]["cantidad_formato"],
                "unidad_formato": preview["propuesto"]["unidad_formato"],
            }
            repository = self.articles.catalogo.repositorio
            paths = (repository.path_articulos, repository.path_historico_precios)
            snapshots = {
                path: path.read_bytes() if path.exists() else None for path in paths
            }
            try:
                result = self.articles.actualizar(
                    article_id, body,
                    audit_context={
                        "user_id": context.user_id,
                        "tenant_id": context.tenant_id,
                        "request_id": context.request_id,
                    },
                )
                if not result.get("ok"):
                    self._restore(snapshots)
            except Exception:
                self._restore(snapshots)
                raise
            if not result.get("ok"):
                error = dict(result.get("error") or {})
                raise ErrorConfirmacionFormatoArticulo(
                    str(error.get("code") or "article_update_failed"),
                    str(error.get("message") or "No se pudo actualizar el artículo."),
                )
            return {
                "ok": True,
                "estado": "CONFIRMADO",
                "articulo_id": article_id,
                "articulo": result.get("articulo"),
                "derivado": preview["derivado"],
                "idempotente": False,
                "datos_reales_modificados": True,
            }

    @staticmethod
    def _restore(snapshots: dict[Path, bytes | None]) -> None:
        for path, content in snapshots.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

    def _authorize(self, context: AuthorizedExecutionContext) -> None:
        if not isinstance(context, AuthorizedExecutionContext):
            raise ErrorConfirmacionFormatoArticulo("unauthorized", "Falta contexto autorizado.")
        valid, _reason = context.validate()
        if not valid or self.REQUIRED_SCOPE not in context.scopes:
            raise ErrorConfirmacionFormatoArticulo("unauthorized", "El actor no está autorizado.")

    def _authorize_preview(self, context: AuthorizedExecutionContext) -> None:
        if not isinstance(context, AuthorizedExecutionContext):
            raise ErrorConfirmacionFormatoArticulo("unauthorized", "Falta contexto autorizado.")
        valid, _reason = context.validate()
        if not valid or not ({"articulos:preview", self.REQUIRED_SCOPE} & context.scopes):
            raise ErrorConfirmacionFormatoArticulo("unauthorized", "El actor no está autorizado para preparar cambios.")

    def _find(self, article_id: str) -> dict[str, Any]:
        key = str(article_id or "").strip()
        if not key or any(char in key for char in ("/", "\\")):
            raise ErrorConfirmacionFormatoArticulo("invalid_article_id", "Identificador no válido.")
        product = self.articles.catalogo.repositorio.obtener_producto(key)
        if not product:
            raise ErrorConfirmacionFormatoArticulo("article_not_found", "Artículo no encontrado.")
        return product

    @staticmethod
    def _positive_decimal(value: Any, code: str, message: str) -> Decimal:
        try:
            parsed = Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError):
            raise ErrorConfirmacionFormatoArticulo(code, message)
        if not parsed.is_finite() or parsed <= 0:
            raise ErrorConfirmacionFormatoArticulo(code, message)
        return parsed

    @staticmethod
    def _contract(product: dict[str, Any]) -> dict[str, Any]:
        return {
            "precio": product.get("precio"),
            "unidad_compra": product.get("unidad_compra") or None,
            "cantidad_formato": (
                float(product["cantidad_formato"])
                if product.get("cantidad_formato") not in (None, "") else None
            ),
            "unidad_formato": product.get("unidad_formato") or None,
            "unidad_base": product.get("unidad_base") or None,
            "unidad_base_sugerida": bool(product.get("unidad_base_sugerida")),
            "estado_unidad_base": product.get("estado_unidad_base"),
        }

    @classmethod
    def _usage(
        cls, quantity: Any, unit: str, content_unit: str, unit_price: Decimal,
    ) -> dict[str, Any] | None:
        if quantity in (None, ""):
            return None
        amount = cls._positive_decimal(quantity, "invalid_usage_quantity", "Cantidad de uso no válida.")
        usage_unit = str(unit or "").strip().lower()
        if usage_unit != content_unit:
            raise ErrorConfirmacionFormatoArticulo(
                "incompatible_usage_unit", "La unidad de uso no coincide con la unidad del contenido.",
            )
        cost = amount * unit_price
        return {
            "cantidad": float(amount),
            "unidad": usage_unit,
            "coste": str(cost),
            "presentacion": f"{cost.quantize(Decimal('0.01')):.2f}",
        }

    @staticmethod
    def _fingerprint(product: dict[str, Any]) -> str:
        payload = json.dumps(product, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _token(
        article_id: str, fingerprint: str, proposed: dict[str, Any],
        context: AuthorizedExecutionContext,
    ) -> str:
        payload = json.dumps({
            "article_id": article_id,
            "version": fingerprint,
            "propuesto": proposed,
            "user_id": context.user_id,
            "tenant_id": context.tenant_id,
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _actor_key(context: AuthorizedExecutionContext, session_id: str) -> tuple[str, str, str]:
        return context.user_id, context.tenant_id, str(session_id or "")

    @staticmethod
    def _change_hash(operation: str, proposed: dict[str, Any]) -> str:
        raw = json.dumps(
            {"operation": operation, "proposed": proposed},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _audit_change(self, context: AuthorizedExecutionContext, pending: dict[str, Any]) -> None:
        event = {
            "operacion": pending["operation"], "articulo_id": pending["article_id"],
            "campos_modificados": sorted(pending["proposed"]), "actor": context.user_id,
            "tenant_hash": hashlib.sha256(context.tenant_id.encode("utf-8")).hexdigest()[:16],
            "request_id": context.request_id, "timestamp": self.now_provider().isoformat(timespec="seconds"),
            "resultado": "CONFIRMADO", "change_hash": pending["change_hash"],
        }
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    @classmethod
    def _presentation(
        cls, current: dict[str, Any], operation: str, before: dict[str, Any],
        proposed: dict[str, Any], derived: dict[str, Any],
    ) -> dict[str, Any]:
        labels = {
            "precio": "Precio canónico", "unidad_compra": "Unidad de compra",
            "cantidad_formato": "Cantidad por formato", "unidad_formato": "Unidad del formato",
            "unidad_base": "Unidad base",
        }
        if operation == "UPDATE_FORMAT":
            labels["precio"] = "Precio del paquete con IVA" if bool(current.get("precio_incluye_iva")) else "Precio del paquete sin IVA"
        changes = [
            {
                "field": field, "label": labels[field],
                "before": cls._display_value(before.get(field)),
                "after": cls._display_value(value),
            }
            for field, value in proposed.items()
            if field in labels and before.get(field) != value
        ]
        unchanged: list[dict[str, str]] = []
        if operation == "UPDATE_FORMAT" and "precio" not in proposed:
            price = current.get("precio")
            price_label = "Precio del paquete con IVA" if bool(current.get("precio_incluye_iva")) else "Precio del paquete sin IVA"
            unchanged.append({"field": "precio", "label": price_label, "value": cls._money(price), "status": "Sin cambios"})
        derived_items: list[dict[str, str]] = []
        if operation == "UPDATE_FORMAT" and derived.get("precio_unitario"):
            price = Decimal(str(proposed.get("precio", current.get("precio"))))
            quantity = Decimal(str(proposed.get("cantidad_formato")))
            unit = str(derived.get("unidad_precio") or "")
            derived_items.append({
                "label": "Precio unitario derivado sin IVA" if not bool(current.get("precio_incluye_iva")) else "Precio unitario derivado con IVA",
                "value": f"{derived['precio_unitario']} €/{unit}",
                "formula": f"{cls._decimal_text(price)} / {cls._decimal_text(quantity)}",
                "status": "Calculado; no se persiste como campo independiente",
            })
        elif operation == "UPDATE_CONVERSION":
            source = str(derived.get("unidad_origen") or "")
            target = str(derived.get("unidad_destino") or "")
            factor = str(derived.get("conversion_factor_display") or cls._display_value(proposed.get("cantidad_formato")))
            derived_items.append({
                "label": "Conversión física propuesta", "value": f"1 {source} = {factor} {target}",
                "formula": "Relación aportada por el usuario", "status": "Propuesta",
            })
        return {
            "schema": "ARTICLE_CHANGE_PREVIEW_V1", "entity_type": "ARTICULO",
            "entity_id": str(current.get("codigo") or ""), "title": str(current.get("nombre") or ""),
            "operation": operation, "changes": changes, "derived": derived_items,
            "unchanged": unchanged, "notice": "Todavía no se ha modificado ningún dato.",
            "datos_reales_modificados": False,
        }

    @staticmethod
    def _display_value(value: Any) -> str:
        if value in (None, ""):
            return "No disponible"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    @staticmethod
    def _decimal_text(value: Decimal) -> str:
        return format(value.normalize(), "f")

    @classmethod
    def _money(cls, value: Any) -> str:
        if value in (None, ""):
            return "Sin precio"
        return f"{cls._decimal_text(Decimal(str(value)))} €"


__all__ = ["ConfirmacionFormatoArticuloService", "ErrorConfirmacionFormatoArticulo"]
