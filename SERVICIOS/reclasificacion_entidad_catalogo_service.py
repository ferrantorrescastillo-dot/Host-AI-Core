from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from SERVICIOS.clasificacion_entidad_catalogo import (
    ARTICULO_COMPRADO, PRODUCTO_VENDIBLE, TIPOS_COSTE_DERIVADO,
    TIPOS_ENTIDAD, AuditorClasificacionLegada,
)
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


class ReclasificacionEntidadError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code; super().__init__(message)


class ReclasificacionEntidadCatalogoService:
    REQUIRED_SCOPE = "articulos:write"

    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.repo = RepositorioProductosMaestro601(self.base_dir)
        self.audit_path = self.base_dir / "DATOS" / "auditoria" / "reclasificacion_entidades.jsonl"

    def candidates(self) -> dict[str, Any]:
        return AuditorClasificacionLegada(self.base_dir).candidatos()

    def preview(self, rows: list[dict[str, Any]], context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context)
        proposals = [self._proposal(dict(row)) for row in rows]
        payload = {"propuestas": proposals, "versiones": {p["article_id"]: p["version_actual"] for p in proposals}}
        token = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {"ok": True, **payload, "preview_token": token, "requiere_confirmacion": True, "datos_reales_modificados": False}

    def confirm(self, rows: list[dict[str, Any]], preview_token: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        preview = self.preview(rows, context)
        if not preview_token or preview_token != preview["preview_token"]:
            raise ReclasificacionEntidadError("stale_or_invalid_preview", "La clasificación o los registros han cambiado desde la vista previa.")
        changed = []; unchanged = []
        for proposal in preview["propuestas"]:
            article_id = proposal["article_id"]
            current = self.repo.obtener_producto(article_id) or {}
            proposed = proposal["propuesto"]
            if all(current.get(key) == value for key, value in proposed.items()):
                unchanged.append(article_id); continue
            history = list(current.get("historial_clasificacion") or [])
            history.append({
                "fecha": datetime.now().isoformat(timespec="seconds"),
                "actor_id": context.user_id, "request_id": context.request_id,
                "anterior": {key: current.get(key) for key in proposed}, "nuevo": proposed,
            })
            self.repo.editar_producto(article_id, {**proposed, "historial_clasificacion": history})
            changed.append(article_id)
        result = {"ok": True, "estado": "CONFIRMADO", "modificados": changed, "sin_cambios": unchanged, "idempotente": not changed, "writes_logicos": len(changed), "datos_reales_modificados": bool(changed)}
        if changed: self._audit(context, result)
        result["articulos"] = [self.repo.obtener_producto(item) for item in changed + unchanged]
        return result

    def _proposal(self, row: dict[str, Any]) -> dict[str, Any]:
        article_id = str(row.get("article_id") or "").strip()
        article = self.repo.obtener_producto(article_id)
        if not article: raise ReclasificacionEntidadError("article_not_found", "El artículo no existe.")
        kind = str(row.get("tipo_entidad") or "").strip().upper()
        if kind not in TIPOS_ENTIDAD: raise ReclasificacionEntidadError("invalid_entity_type", "El tipo de entidad no es válido.")
        elaboration_id = str(row.get("elaboracion_id") or "").strip() or None
        if kind in TIPOS_COSTE_DERIVADO and not elaboration_id:
            raise ReclasificacionEntidadError("elaboration_required", "La elaboración vinculada es obligatoria.")
        if kind == ARTICULO_COMPRADO: elaboration_id = None
        cost_origin = "COSTE_DERIVADO_ELABORACION" if elaboration_id and kind != ARTICULO_COMPRADO else "COSTE_COMPRA"
        proposed = {"tipo_entidad": kind, "elaboracion_id": elaboration_id or "", "origen_coste": cost_origin}
        return {
            "article_id": article_id,
            "registro_actual": {key: article.get(key) for key in ("codigo", "nombre", "tipo_entidad", "precio", "proveedor", "origen", "observaciones", "elaboracion_id", "origen_coste")},
            "propuesto": proposed,
            "valor_legado_sin_clasificar": article.get("precio") if article.get("precio") not in (None, "") and kind != ARTICULO_COMPRADO else None,
            "consecuencias": ["NO_REQUIERE_PRECIO_COMPRA", "COSTE_DERIVADO_ESCANDALLO", "NO_MODIFICA_STOCK", "NO_MODIFICA_ESCANDALLO", "CONSERVA_HISTORICO"] if cost_origin == "COSTE_DERIVADO_ELABORACION" else ["REQUIERE_COSTE_COMPRA", "NO_MODIFICA_STOCK"],
            "version_actual": self._fingerprint(article),
        }

    def _authorize(self, context: AuthorizedExecutionContext) -> None:
        valid, _ = context.validate() if isinstance(context, AuthorizedExecutionContext) else (False, "")
        if not valid or self.REQUIRED_SCOPE not in context.scopes:
            raise ReclasificacionEntidadError("unauthorized", "El actor no está autorizado para reclasificar artículos.")

    @staticmethod
    def _fingerprint(article: dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(article, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def _audit(self, context: AuthorizedExecutionContext, result: dict[str, Any]) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"fecha": datetime.now().isoformat(timespec="seconds"), "actor_id": context.user_id, "request_id": context.request_id, **result}, ensure_ascii=False) + "\n")


__all__ = ["ReclasificacionEntidadCatalogoService", "ReclasificacionEntidadError"]
