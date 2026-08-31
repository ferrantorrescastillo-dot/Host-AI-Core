from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Protocol
import uuid

from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.host_ai_engine.models import HostAIEngineRequest
from SERVICIOS.host_ai_engine.service import HostAIEngine


logger = logging.getLogger(__name__)


class ArticuloDocumentacionError(ValueError):
    def __init__(self, code: str, message: str): self.code = code; super().__init__(message)


class ArticleProposalGenerator(Protocol):
    def generate(self, *, article: dict[str, Any], missing_fields: list[str], allowed_fields: set[str]) -> dict[str, Any]: ...


class GeneratedArticleProposals(dict[str, Any]):
    def __init__(self, values: dict[str, Any], cost_breakdown: dict[str, Any], telemetry: dict[str, Any]) -> None:
        super().__init__(values); self.cost_breakdown = cost_breakdown; self.telemetry = telemetry


class HostAIArticleProposalGenerator:
    """Adaptador READ del engine canónico. El resultado nunca tiene autoridad de escritura."""

    def __init__(self, base_dir: Path, engine: HostAIEngine | None = None) -> None:
        self.engine = engine or HostAIEngine(base_dir)

    @staticmethod
    def _present(value: Any) -> bool:
        return value is not None and value != "" and value != []

    def generate(self, *, article: dict[str, Any], missing_fields: list[str], allowed_fields: set[str], session_id: str = "", culinary_context: dict[str, Any] | None = None) -> dict[str, Any]:
        requested = sorted(set(missing_fields) & allowed_fields)
        if not requested: return {}
        provider = str(self.engine.default_provider or "SIMULADO").upper()
        providers = getattr(self.engine, "_providers", {})
        selected = providers.get(provider)
        if provider == "SIMULADO" or not bool(getattr(selected, "connected", False)):
            provider = next((name for name, value in providers.items() if name != "SIMULADO" and bool(getattr(value, "connected", False))), "")
        if not provider: raise ArticuloDocumentacionError("ai_provider_unavailable", "No hay un proveedor IA productivo configurado.")
        existing = {
            key: article.get(key) for key in sorted(allowed_fields)
            if self._present(article.get(key))
        }
        safe_culinary = {
            key: value for key, value in dict(culinary_context or {}).items()
            if key in {"ingrediente_original", "receta_nombre", "receta_id", "uso_culinario", "cantidad_receta", "unidad_receta", "procedimiento_receta"}
            and self._present(value)
        }
        context = {
            "articulo": {
                "articulo_id": article.get("id") or article.get("codigo"),
                "codigo": article.get("codigo"),
                "nombre": article.get("nombre"),
            },
            "contexto_culinario": safe_culinary,
            "datos_existentes": existing,
            "campos_faltantes_proponibles": requested,
        }
        telemetry = {
            "contexto_receta_presente": bool(safe_culinary.get("receta_nombre") or safe_culinary.get("receta_id")),
            "ingrediente_presente": bool(safe_culinary.get("ingrediente_original")),
            "campos_existentes_enviados": sorted(existing),
            "campos_solicitados": requested,
        }
        logger.info("article_ai_context %s", json.dumps(telemetry, ensure_ascii=False, sort_keys=True))
        response = self.engine.ejecutar(HostAIEngineRequest(
            origen="ARTICULOS_WEB", modulo="ARTICULOS_IA", tipo_peticion="completar_campos_faltantes_articulo",
            proveedor_preferido=provider, datos_enviados={"pregunta": "Devuelve solo un objeto JSON plano con propuestas útiles para hostelería/restauración. Usa los datos existentes y el contexto culinario para mantener coherencia, pero no los sobrescribas. No incluyas datos existentes, precios, proveedores, stock ni compras. Claves permitidas: " + json.dumps(requested, ensure_ascii=False) + ". Contexto estructurado: " + json.dumps(context, ensure_ascii=False, sort_keys=True)},
            operation_id="ARTICLE_AI-" + str(uuid.uuid4()), session_id=session_id, entity_type="ARTICLE", entity_id=str(article.get("id") or article.get("codigo") or ""),
        ))
        if not response.estado.startswith("OK"): raise ArticuloDocumentacionError("ai_provider_error", "El proveedor IA no pudo generar propuestas.")
        raw = str((response.respuesta or {}).get("mensaje") or "").strip()
        if raw.startswith("```"): raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try: parsed = json.loads(raw)
        except (TypeError, ValueError): raise ArticuloDocumentacionError("ai_invalid_response", "La propuesta IA no es JSON válido.")
        if not isinstance(parsed, dict): raise ArticuloDocumentacionError("ai_invalid_response", "La propuesta IA no tiene el formato esperado.")
        return GeneratedArticleProposals({key: value for key, value in parsed.items() if key in requested}, dict(response.cost_breakdown or {}), telemetry)


class ArticuloDocumentacionWriteService:
    REQUIRED_SCOPE = "articulos:write"
    FIELDS = frozenset({"familia", "unidad_base", "unidad_compra", "cantidad_formato", "unidad_formato", "observaciones"})
    _lock = RLock()

    def __init__(self, base_dir: Path | str, generator: ArticleProposalGenerator | None = None, now_provider=datetime.now) -> None:
        self.base_dir = Path(base_dir).resolve(); self.path = self.base_dir / "DATOS" / "db" / "articulos.json"
        self.audit_path = self.base_dir / "DATOS" / "auditoria" / "articulos.jsonl"
        self.generator = generator or HostAIArticleProposalGenerator(self.base_dir); self.now_provider = now_provider
        self._completed: dict[str, dict[str, Any]] = {}

    def proposal(self, *, article_id: str, proposed: dict[str, Any] | None = None, session_id: str = "", culinary_context: dict[str, Any] | None = None) -> dict[str, Any]:
        article = self._article(article_id)
        missing = sorted(key for key in self.FIELDS if not self._present(article.get(key)))
        raw = dict(proposed) if proposed else self._generate(article, missing, session_id, culinary_context)
        clean = {key: value for key, value in raw.items() if key in missing and self._present(value)}
        return {"ok": True, "articulo_id": self._identity(article), "datos_existentes": {k: article.get(k) for k in self.FIELDS if self._present(article.get(k))}, "campos_sin_datos": missing, "datos_propuestos_ia": clean, "campos_descartados": sorted(set(raw) - set(clean)), "cost_breakdown": dict(getattr(raw, "cost_breakdown", {}) or {}), "contexto_ia": dict(getattr(raw, "telemetry", {}) or {}), "datos_reales_modificados": False}

    def draft_proposal(self, *, draft: dict[str, Any], proposed: dict[str, Any] | None = None, session_id: str = "", culinary_context: dict[str, Any] | None = None) -> dict[str, Any]:
        current = dict(draft or {})
        if not str(current.get("nombre") or "").strip():
            raise ArticuloDocumentacionError("article_name_required", "Indica el nombre del artículo antes de solicitar propuestas.")
        missing = sorted(key for key in self.FIELDS if not self._present(current.get(key)))
        raw = dict(proposed) if proposed else self._generate(current, missing, session_id, culinary_context)
        clean = {key: value for key, value in raw.items() if key in missing and self._present(value)}
        return {"ok": True, "modo": "BORRADOR_NO_PERSISTIDO", "datos_propuestos_ia": clean, "campos_sin_datos": missing, "campos_descartados": sorted(set(raw) - set(clean)), "cost_breakdown": dict(getattr(raw, "cost_breakdown", {}) or {}), "contexto_ia": dict(getattr(raw, "telemetry", {}) or {}), "datos_reales_modificados": False}

    def preview(self, *, article_id: str, selected: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context); article = self._article(article_id)
        changes = self._changes(article, selected); token = self._token(article, changes, context)
        return {"ok": True, "estado": "LISTO_PARA_CONFIRMAR" if changes else "SIN_CAMBIOS", "articulo_antes": article, "cambios_seleccionados": changes, "articulo_propuesto": {**article, **changes}, "preview_token": token, "requiere_confirmacion": bool(changes), "datos_reales_modificados": False}

    def confirm(self, *, article_id: str, selected: dict[str, Any], preview_token: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        with self._lock:
            if preview_token in self._completed: return {**self._completed[preview_token], "idempotente": True}
            preview = self.preview(article_id=article_id, selected=selected, context=context)
            if not preview_token or preview_token != preview["preview_token"]: raise ArticuloDocumentacionError("stale_or_invalid_preview", "La vista previa ya no es válida.")
            if not preview["requiere_confirmacion"]: return {**preview, "idempotente": True}
            current = preview["articulo_antes"]; now = self.now_provider().isoformat(timespec="seconds")
            origins = dict(current.get("procedencia_campos") or {}); history = list(current.get("historial_procedencia") or [])
            for field, value in preview["cambios_seleccionados"].items():
                history.append({"campo": field, "valor_anterior": current.get(field), "valor_nuevo": value, "origen_anterior": origins.get(field), "origen_nuevo": "IA", "actor": context.user_id, "timestamp": now, "estado_revision": "PENDIENTE_REVISION"})
                origins[field] = {"tipo": "IA", "actor_id": context.user_id, "fecha": now, "estado_revision": "PENDIENTE_REVISION"}
            values = self._read(); persisted = {**current, **preview["cambios_seleccionados"], "procedencia_campos": origins, "historial_procedencia": history}
            values = [persisted if self._identity(value) == self._identity(current) else value for value in values]; self._write(values)
            reread = self._article(article_id)
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"request_id": context.request_id, "articulo_id": self._identity(reread), "actor": context.user_id, "operacion": "COMPLETAR_DOCUMENTACION_IA", "campos": sorted(preview["cambios_seleccionados"]), "timestamp": now}, ensure_ascii=False, sort_keys=True) + "\n")
            result = {"ok": True, "estado": "CONFIRMADO", "articulo": reread, "campos_confirmados": sorted(preview["cambios_seleccionados"]), "lectura_posterior_verificada": all(reread.get(k) == v for k, v in preview["cambios_seleccionados"].items()), "idempotente": False, "datos_reales_modificados": True}
            self._completed[preview_token] = result; return result

    def _changes(self, article: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
        if set(selected) - self.FIELDS: raise ArticuloDocumentacionError("unsupported_field", "La selección contiene campos no permitidos.")
        return {key: value for key, value in selected.items() if self._present(value) and not self._present(article.get(key))}
    def _generate(self, article: dict[str, Any], missing: list[str], session_id: str, culinary_context: dict[str, Any] | None = None) -> dict[str, Any]:
        if isinstance(self.generator, HostAIArticleProposalGenerator): return self.generator.generate(article=article, missing_fields=missing, allowed_fields=set(self.FIELDS), session_id=session_id, culinary_context=culinary_context)
        return self.generator.generate(article=article, missing_fields=missing, allowed_fields=set(self.FIELDS))
    def _article(self, identity: str) -> dict[str, Any]:
        found = next((dict(v) for v in self._read() if self._identity(v) == str(identity)), None)
        if not found: raise ArticuloDocumentacionError("article_not_found", "Artículo no encontrado.")
        return found
    def _read(self) -> list[dict[str, Any]]:
        raw = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []; return [dict(v) for v in raw] if isinstance(raw, list) else []
    def _write(self, values: list[dict[str, Any]]) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp"); tmp.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8"); tmp.replace(self.path)
    def _authorize(self, context: AuthorizedExecutionContext) -> None:
        valid, _ = context.validate() if isinstance(context, AuthorizedExecutionContext) else (False, "")
        if not valid or self.REQUIRED_SCOPE not in context.scopes: raise ArticuloDocumentacionError("unauthorized", "Actor no autorizado.")
    @staticmethod
    def _present(value: Any) -> bool: return value is not None and value != "" and value != []
    @staticmethod
    def _identity(article: dict[str, Any]) -> str: return str(article.get("id") or article.get("codigo") or "")
    @staticmethod
    def _token(article: dict[str, Any], changes: dict[str, Any], context: AuthorizedExecutionContext) -> str:
        raw = json.dumps({"article": article, "changes": changes, "actor": context.user_id, "tenant": context.tenant_id}, ensure_ascii=False, sort_keys=True, separators=(",", ":")); return hashlib.sha256(raw.encode()).hexdigest()


__all__ = ["ArticuloDocumentacionWriteService", "ArticuloDocumentacionError", "HostAIArticleProposalGenerator", "ArticleProposalGenerator"]
