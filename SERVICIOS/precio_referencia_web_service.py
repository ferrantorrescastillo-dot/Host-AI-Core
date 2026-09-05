from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from threading import RLock
from typing import Any, Callable
from urllib.parse import urlparse

from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext


class PrecioReferenciaWebError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class PrecioReferenciaWebService:
    """Guarda referencias observadas; nunca altera precio ni proveedor reales."""

    REQUIRED_SCOPE = "articulos:write"
    _lock = RLock()

    def __init__(self, base_dir: Path | str, *, now_provider: Callable[[], datetime] = datetime.now) -> None:
        root = Path(base_dir).resolve()
        self.path = root / "DATOS" / "db" / "articulos.json"
        self.audit_path = root / "DATOS" / "auditoria" / "precios_referencia_web.jsonl"
        self.now_provider = now_provider
        self._completed: dict[str, dict[str, Any]] = {}

    def preview(self, *, article_id: str, result: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context)
        article = self._article(article_id)
        reference = self._normalize(result)
        token = self._token(article, reference, context)
        return {"ok": True, "estado": "LISTO_PARA_CONFIRMAR", "articulo_id": article_id, "referencia_propuesta": reference, "precio_real_actual": article.get("precio"), "proveedor_real_actual": article.get("proveedor") or article.get("proveedor_preferente"), "preview_token": token, "requiere_confirmacion": True, "datos_reales_modificados": False}

    def preview_manual(self, *, article_id: str, result: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context)
        article = self._article(article_id)
        reference = self._normalize_manual(result, context)
        token = self._token(article, reference, context)
        return {"ok": True, "estado": "LISTO_PARA_CONFIRMAR", "articulo_id": article_id, "referencia_propuesta": reference, "precio_real_actual": article.get("precio"), "proveedor_real_actual": article.get("proveedor") or article.get("proveedor_preferente"), "preview_token": token, "requiere_confirmacion": True, "datos_reales_modificados": False}

    def normalize_web_candidate(self, result: dict[str, Any]) -> dict[str, Any]:
        """Public normalization boundary shared by search and persistence."""
        return self._normalize(result)

    def normalize_imported_candidate(self, result: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        reference = self._normalize(result)
        return {**reference, "tipo": "PRECIO_REFERENCIA_IMPORTADA", "origen": "IMPORTADO", "fuente": "WEB", "actor_id": context.user_id, "modelo_busqueda": "", "escalado_modelos": [], "web_search_calls": 0, "cache_hit": False}

    def preview_imported(self, *, article_id: str, result: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context); article = self._article(article_id)
        reference = self.normalize_imported_candidate(result, context)
        return {"ok": True, "estado": "LISTO_PARA_CONFIRMAR", "articulo_id": article_id, "referencia_propuesta": reference, "precio_real_actual": article.get("precio"), "proveedor_real_actual": article.get("proveedor") or article.get("proveedor_preferente"), "preview_token": self._token(article, reference, context), "requiere_confirmacion": True, "datos_reales_modificados": False}

    def confirm_imported(self, *, article_id: str, result: dict[str, Any], preview_token: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        with self._lock:
            if preview_token in self._completed:
                return {**self._completed[preview_token], "idempotente": True, "datos_reales_modificados": False}
            self._authorize(context)
            article = self._article(article_id)
            reference = self.normalize_imported_candidate(result, context)
            matching_index = self._matching_reference_index(article, reference)
            if matching_index is not None:
                current_token = self._token(article, reference, context)
                before = dict(article)
                previous_references = list(before.get("precios_referencia") or [])
                previous_references.pop(matching_index)
                if previous_references:
                    before["precios_referencia"] = previous_references
                else:
                    before.pop("precios_referencia", None)
                prior_token = self._token(before, reference, context)
                if preview_token not in {current_token, prior_token}:
                    raise PrecioReferenciaWebError("stale_or_invalid_preview", "La referencia cambió desde la vista previa.")
                response = {
                    "ok": True,
                    "estado": "CONFIRMADO",
                    "articulo": article,
                    "referencia": list(article.get("precios_referencia") or [])[matching_index],
                    "precio_real_modificado": False,
                    "proveedor_real_modificado": False,
                    "lectura_posterior_verificada": True,
                    "idempotente": True,
                    "datos_reales_modificados": False,
                }
                self._completed[preview_token] = response
                return response
            preview = self.preview_imported(article_id=article_id, result=reference, context=context)
            if preview_token != preview["preview_token"]: raise PrecioReferenciaWebError("stale_or_invalid_preview", "La referencia cambió desde la vista previa.")
            values = self._read()
            for article in values:
                if self._identity(article) == article_id:
                    article["precios_referencia"] = [*list(article.get("precios_referencia") or []), preview["referencia_propuesta"]]; break
            self._write(values); self._audit(article_id, preview["referencia_propuesta"], context)
            reread = self._article(article_id)
            response = {"ok": True, "estado": "CONFIRMADO", "articulo": reread, "referencia": reread["precios_referencia"][-1], "precio_real_modificado": False, "proveedor_real_modificado": False, "lectura_posterior_verificada": reread["precios_referencia"][-1] == preview["referencia_propuesta"], "idempotente": False, "datos_reales_modificados": True}
            self._completed[preview_token] = response; return response

    @classmethod
    def _matching_reference_index(cls, article: dict[str, Any], proposed: dict[str, Any]) -> int | None:
        target = cls._reference_fingerprint(proposed)
        for index, reference in enumerate(article.get("precios_referencia") or []):
            if isinstance(reference, dict) and cls._reference_fingerprint(reference) == target:
                return index
        return None

    @staticmethod
    def _reference_fingerprint(reference: dict[str, Any]) -> str:
        stable_fields = (
            "tipo", "origen", "producto", "precio_comercial", "moneda",
            "cantidad_formato", "unidad_formato", "formato_comercial",
            "precio_normalizado", "unidad_normalizada", "tienda_referencia",
            "url", "evidencia", "confianza", "fuente", "autoridad",
        )
        stable = {field: reference.get(field) for field in stable_fields}
        return hashlib.sha256(
            json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def confirm(self, *, article_id: str, result: dict[str, Any], preview_token: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        with self._lock:
            if preview_token in self._completed:
                return {**self._completed[preview_token], "idempotente": True}
            preview = self.preview(article_id=article_id, result=result, context=context)
            if preview_token != preview["preview_token"]:
                raise PrecioReferenciaWebError("stale_or_invalid_preview", "La referencia cambió desde la vista previa.")
            values = self._read()
            for article in values:
                if self._identity(article) != article_id:
                    continue
                references = list(article.get("precios_referencia") or [])
                references.append(preview["referencia_propuesta"])
                article["precios_referencia"] = references
                break
            self._write(values)
            self._audit(article_id, preview["referencia_propuesta"], context)
            reread = self._article(article_id)
            response = {"ok": True, "estado": "CONFIRMADO", "articulo": reread, "referencia": reread["precios_referencia"][-1], "precio_real_modificado": False, "proveedor_real_modificado": False, "lectura_posterior_verificada": reread["precios_referencia"][-1] == preview["referencia_propuesta"], "idempotente": False, "datos_reales_modificados": True}
            self._completed[preview_token] = response
            return response

    def confirm_manual(self, *, article_id: str, result: dict[str, Any], preview_token: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        with self._lock:
            if preview_token in self._completed:
                return {**self._completed[preview_token], "idempotente": True}
            preview = self.preview_manual(article_id=article_id, result=result, context=context)
            if preview_token != preview["preview_token"]:
                raise PrecioReferenciaWebError("stale_or_invalid_preview", "La referencia cambió desde la vista previa.")
            values = self._read()
            for article in values:
                if self._identity(article) == article_id:
                    article["precios_referencia"] = [*list(article.get("precios_referencia") or []), preview["referencia_propuesta"]]
                    break
            self._write(values)
            reread = self._article(article_id)
            response = {"ok": True, "estado": "CONFIRMADO", "articulo": reread, "referencia": reread["precios_referencia"][-1], "precio_real_modificado": False, "proveedor_real_modificado": False, "lectura_posterior_verificada": reread["precios_referencia"][-1] == preview["referencia_propuesta"], "idempotente": False, "datos_reales_modificados": True}
            self._completed[preview_token] = response
            return response

    def _normalize(self, value: dict[str, Any]) -> dict[str, Any]:
        commercial = self._positive(value.get("precio_comercial") or value.get("precio"), "precio_comercial")
        amount = self._positive(value.get("cantidad_formato"), "cantidad_formato")
        unit = str(value.get("unidad_formato") or "").strip().lower()
        if unit not in {"g", "kg", "ml", "l", "u"}:
            raise PrecioReferenciaWebError("invalid_format", "La unidad comercial no es normalizable.")
        base, factor = ({"g": ("kg", Decimal("1000")), "kg": ("kg", Decimal("1")), "ml": ("l", Decimal("1000")), "l": ("l", Decimal("1")), "u": ("u", Decimal("1"))})[unit]
        normalized = commercial / (amount / factor)
        url = str(value.get("url") or "").strip()
        if urlparse(url).scheme not in {"http", "https"} or not urlparse(url).netloc:
            raise PrecioReferenciaWebError("invalid_source", "La fuente web no es válida.")
        return {"tipo": "PRECIO_REFERENCIA_WEB", "origen": "WEB", "producto": str(value.get("producto") or "").strip(), "precio_comercial": float(commercial), "moneda": str(value.get("moneda") or "EUR").upper(), "cantidad_formato": float(amount), "unidad_formato": unit, "formato_comercial": str(value.get("formato_comercial") or f"{float(amount):g} {unit}"), "precio_normalizado": float(normalized), "unidad_normalizada": base, "tienda_referencia": str(value.get("tienda_referencia") or value.get("tienda") or "").strip(), "url": url, "consultado_en": str(value.get("consultado_en") or self.now_provider().isoformat(timespec="seconds")), "evidencia": str(value.get("evidencia") or "").strip(), "confianza": value.get("confianza"), "modelo_busqueda": str(value.get("modelo_busqueda") or ""), "escalado_modelos": list(value.get("escalado_modelos") or []), "web_search_calls": int(value.get("web_search_calls") or 0), "cache_hit": bool(value.get("cache_hit")), "fuente_verificada": bool(value.get("fuente_verificada", True)), "autoridad": "REFERENCIA_NO_REAL"}

    def _normalize_manual(self, value: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        normalized = self._normalize_commercial(value)
        return {"tipo": "PRECIO_REFERENCIA_MANUAL", "origen": "USUARIO", **normalized, "registrado_en": self.now_provider().isoformat(timespec="seconds"), "actor_id": context.user_id, "autoridad": "REFERENCIA_NO_REAL"}

    def _normalize_commercial(self, value: dict[str, Any]) -> dict[str, Any]:
        commercial = self._positive(value.get("precio_comercial") or value.get("precio"), "precio_comercial")
        amount = self._positive(value.get("cantidad_formato") or 1, "cantidad_formato")
        unit = str(value.get("unidad_formato") or value.get("unidad") or "").strip().lower()
        if unit not in {"g", "kg", "ml", "l", "u"}: raise PrecioReferenciaWebError("invalid_format", "La unidad comercial no es normalizable.")
        base, factor = ({"g": ("kg", Decimal("1000")), "kg": ("kg", Decimal("1")), "ml": ("l", Decimal("1000")), "l": ("l", Decimal("1")), "u": ("u", Decimal("1"))})[unit]
        normalized = commercial / (amount / factor)
        return {"precio_comercial": float(commercial), "cantidad_formato": float(amount), "unidad_formato": unit, "precio_normalizado": float(normalized), "unidad_normalizada": base}

    @staticmethod
    def _positive(value: Any, field: str) -> Decimal:
        try: parsed = Decimal(str(value))
        except (InvalidOperation, ValueError): raise PrecioReferenciaWebError("invalid_price", f"{field} no es válido.")
        if parsed <= 0: raise PrecioReferenciaWebError("invalid_price", f"{field} debe ser mayor que cero.")
        return parsed

    def _article(self, identity: str) -> dict[str, Any]:
        found = next((dict(item) for item in self._read() if self._identity(item) == str(identity)), None)
        if not found: raise PrecioReferenciaWebError("article_not_found", "Artículo no encontrado.")
        return found

    def _read(self) -> list[dict[str, Any]]:
        raw = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []
        return [dict(item) for item in raw] if isinstance(raw, list) else []

    def _write(self, values: list[dict[str, Any]]) -> None:
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def _audit(self, article_id: str, reference: dict[str, Any], context: AuthorizedExecutionContext) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        event = {"tipo": "PRECIO_REFERENCIA_WEB_CONFIRMADO", "articulo_id": article_id, "actor_id": context.user_id, "request_id": context.request_id, "registrado_en": self.now_provider().isoformat(timespec="seconds"), "tienda_referencia": reference.get("tienda_referencia"), "url": reference.get("url")}
        with self.audit_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")

    def _authorize(self, context: AuthorizedExecutionContext) -> None:
        valid, _ = context.validate() if isinstance(context, AuthorizedExecutionContext) else (False, "")
        if not valid or self.REQUIRED_SCOPE not in context.scopes: raise PrecioReferenciaWebError("unauthorized", "Actor no autorizado.")

    @staticmethod
    def _identity(article: dict[str, Any]) -> str: return str(article.get("id") or article.get("codigo") or "")

    @staticmethod
    def _token(article: dict[str, Any], reference: dict[str, Any], context: AuthorizedExecutionContext) -> str:
        stable_reference = {
            key: value for key, value in dict(reference or {}).items()
            if key != "registrado_en"
        }
        raw = json.dumps({"article": article, "reference": stable_reference, "actor": context.user_id, "tenant": context.tenant_id}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()


__all__ = ["PrecioReferenciaWebService", "PrecioReferenciaWebError"]
