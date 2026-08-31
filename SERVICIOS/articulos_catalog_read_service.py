from __future__ import annotations

import math
import unicodedata
from pathlib import Path
from typing import Any

from SERVICIOS.catalogo_maestro_productos_601 import CatalogoMaestroProductos601
from SERVICIOS.clasificacion_entidad_catalogo import (
    normalizar_tipo,
    origen_coste,
    relacion_elaboracion,
)


class ArticulosCatalogReadService:
    """Vista pública de solo lectura del catálogo maestro existente."""

    ALLOWED_QUERY = {
        "q", "familia", "proveedor", "estado", "con_stock",
        "page", "page_size", "orden", "direccion",
    }
    SORT_FIELDS = {"nombre", "codigo", "precio", "stock", "actualizacion"}
    BASE_UNITS = {"kg", "g", "l", "ml", "u"}
    EDITABLE_FIELDS = {"nombre", "familia", "unidad_base", "unidad_compra", "cantidad_formato", "unidad_formato", "conversion_unidades", "proveedor_preferente", "precio", "referencia_proveedor", "marca", "conservacion", "alergenos", "observaciones"}

    def __init__(self, base_dir: Path, stock: Any | None = None, compras: Any | None = None) -> None:
        self.catalogo = CatalogoMaestroProductos601(base_dir)
        self.stock = stock
        self.compras = compras

    def _providers(self) -> list[dict[str, Any]]:
        if self.compras is not None:
            return list(self.compras.listar_proveedores(incluir_inactivos=False) or [])
        return []

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(c for c in text if not unicodedata.combining(c)).strip().lower()

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            return float(value) if value not in ("", None) else None
        except (TypeError, ValueError):
            return None

    def _stock_index(self) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        if self.stock is None:
            return {}, {}
        result = self.stock.stock_actual()
        items = list(result.get("items") or [])
        by_id = {self._norm(x.get("articulo_id")): x for x in items if x.get("articulo_id")}
        by_name = {self._norm(x.get("nombre")): x for x in items if x.get("nombre")}
        return by_id, by_name

    def _stock_for(
        self,
        product: dict[str, Any],
        indexes: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]],
    ) -> dict[str, Any] | None:
        by_id, by_name = indexes
        return by_id.get(self._norm(product.get("codigo"))) or by_name.get(
            self._norm(product.get("nombre"))
        )

    def _summary(
        self,
        product: dict[str, Any],
        indexes: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]],
    ) -> dict[str, Any]:
        stock = self._stock_for(product, indexes)
        provider = product.get("proveedor_preferente") or product.get("proveedor") or None
        return {
            "id": str(product.get("codigo") or ""),
            "codigo": str(product.get("codigo") or ""),
            "nombre": str(product.get("nombre") or ""),
            "tipo_entidad": normalizar_tipo(product.get("tipo_entidad")),
            "elaboracion_id": relacion_elaboracion(product),
            "origen_coste": origen_coste(product),
            "familia": product.get("familia") or None,
            "subfamilia": product.get("subfamilia") or None,
            "marca": product.get("marca") or None,
            "proveedor": provider,
            "precio": self._number(product.get("precio")),
            "unidad": product.get("unidad_base") or product.get("unidad_compra") or None,
            "estado": product.get("estado") or ("activo" if product.get("activo", True) else "archivado"),
            "stock": self._number(stock.get("cantidad")) if stock else None,
            "unidad_stock": stock.get("unidad") if stock else None,
            "con_stock": bool(stock and float(stock.get("cantidad") or 0) > 0),
            "actualizado_en": product.get("fecha_modificacion") or product.get("fecha_precio") or None,
            "tiene_ficha_tecnica": False,
        }

    def listar(self, query: dict[str, Any]) -> dict[str, Any]:
        unknown = sorted(set(query) - self.ALLOWED_QUERY)
        if unknown:
            return self._error("invalid_filter", f"Filtros no admitidos: {', '.join(unknown)}.", 400)
        try:
            page = int(query.get("page") or 1)
            page_size = int(query.get("page_size") or 25)
        except (TypeError, ValueError):
            return self._error("invalid_pagination", "La paginación debe ser numérica.", 400)
        if page < 1 or page_size < 1 or page_size > 100:
            return self._error("invalid_pagination", "page debe ser >= 1 y page_size entre 1 y 100.", 400)
        order = str(query.get("orden") or "nombre")
        direction = str(query.get("direccion") or "asc").lower()
        if order not in self.SORT_FIELDS or direction not in {"asc", "desc"}:
            return self._error("invalid_sort", "Ordenación no válida.", 400)

        products = list(self.catalogo.listar(incluir_archivados=True).get("productos") or [])
        indexes = self._stock_index()
        items = [self._summary(p, indexes) for p in products]
        q = self._norm(query.get("q"))
        if q:
            matching_ids = {
                str(product.get("codigo") or "") for product in products
                if any(q in self._norm(value) for value in (
                    product.get("nombre"), product.get("codigo"), product.get("familia"),
                    product.get("proveedor"), product.get("alias"), product.get("aliases"),
                ))
            }
            items = [x for x in items if x["id"] in matching_ids]
        for key in ("familia", "proveedor", "estado"):
            value = self._norm(query.get(key))
            if value:
                items = [x for x in items if self._norm(x.get(key)) == value]
        with_stock = str(query.get("con_stock") or "").lower()
        if with_stock in {"true", "false"}:
            wanted = with_stock == "true"
            items = [x for x in items if x["con_stock"] is wanted]
        elif with_stock:
            return self._error("invalid_filter", "con_stock debe ser true o false.", 400)

        sort_key = {
            "nombre": lambda x: self._norm(x["nombre"]),
            "codigo": lambda x: self._norm(x["codigo"]),
            "precio": lambda x: (x["precio"] is None, x["precio"] or 0),
            "stock": lambda x: (x["stock"] is None, x["stock"] or 0),
            "actualizacion": lambda x: str(x["actualizado_en"] or ""),
        }[order]
        items.sort(key=sort_key, reverse=direction == "desc")
        total = len(items)
        start = (page - 1) * page_size
        all_summaries = [self._summary(p, indexes) for p in products]
        return {
            "ok": True,
            "catalogo": {
                "items": items[start:start + page_size],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": math.ceil(total / page_size) if total else 0,
                "filtros": {
                    "familias": sorted({x["familia"] for x in all_summaries if x["familia"]}),
                    "proveedores": sorted({x["proveedor"] for x in all_summaries if x["proveedor"]}),
                    "estados": sorted({x["estado"] for x in all_summaries if x["estado"]}),
                },
                "capacidades": {
                    "stock": self.stock is not None,
                    "ficha_tecnica": False,
                    "documentos": False,
                    "recetas": False,
                    "escandallos": False,
                },
            },
        }

    def obtener(self, article_id: str) -> dict[str, Any]:
        result = self.catalogo.obtener(article_id)
        if not result.get("ok"):
            return self._error("article_not_found", "Artículo no encontrado.", 404)
        product = dict(result.get("producto") or {})
        stock_item = self._stock_for(product, self._stock_index())
        associations = [dict(x) for x in list(result.get("asociaciones") or []) if isinstance(x, dict)]
        history = [dict(x) for x in list(result.get("historico_precios") or []) if isinstance(x, dict)]
        preferred_provider = product.get("proveedor_preferente") or product.get("proveedor")
        providers = []
        for row in associations:
            name = row.get("proveedor_nombre") or row.get("proveedor") or row.get("nombre_proveedor")
            providers.append({
                "id": row.get("proveedor_id") or None,
                "nombre": name,
                "referencia": row.get("referencia_proveedor") or row.get("referencia") or None,
                "preferente": bool(row.get("preferente", False)),
                "precio": self._number(row.get("precio")),
                "unidad": row.get("unidad") or None,
                "actualizado_en": row.get("fecha_actualizacion") or row.get("fecha") or None,
            })
        detail = {
            **self._summary(product, self._stock_index()),
            "referencia_proveedor": product.get("referencia_proveedor") or None,
            "unidad_compra": product.get("unidad_compra") or None,
            "cantidad_formato": self._number(product.get("cantidad_formato")),
            "unidad_formato": product.get("unidad_formato") or None,
            "unidad_base": product.get("unidad_base") or None,
            "unidad_base_sugerida": bool(product.get("unidad_base_sugerida")),
            "estado_unidad_base": product.get("estado_unidad_base") or "CONFIRMADA",
            "conversion_unidades": product.get("conversion_unidades") or None,
            "unidad_recetas": product.get("unidad_recetas") or None,
            "iva": self._number(product.get("iva")),
            "precio_incluye_iva": bool(product.get("precio_incluye_iva", False)),
            "alergenos": list(product.get("alergenos") or []),
            "conservacion": product.get("conservacion") or None,
            "stock_minimo": self._number(product.get("stock_minimo")),
            "observaciones": product.get("observaciones_ext") or product.get("observaciones") or None,
            "procedencia_campos": dict(product.get("procedencia_campos") or {}),
            "historial_procedencia": list(product.get("historial_procedencia") or []),
            "precios_referencia": list(product.get("precios_referencia") or []),
            "stock_detalle": {
                "cantidad": self._number(stock_item.get("cantidad")) if stock_item else None,
                "unidad": stock_item.get("unidad") if stock_item else None,
                "lotes": list(stock_item.get("lotes") or []) if stock_item else [],
            },
            "proveedores": providers,
            "precios": [{
                "precio": self._number(x.get("precio")),
                "unidad": x.get("unidad") or None,
                "proveedor": x.get("proveedor_nombre") or None,
                "fecha": x.get("fecha_factura") or x.get("fecha") or None,
                "origen": x.get("origen") or None,
            } for x in history],
            "documentos": [],
            "ficha_tecnica": None,
            "recetas": [],
            "escandallos": [],
            "historial": [{
                "tipo": "precio",
                "fecha": x.get("fecha_registro") or x.get("fecha_factura") or None,
                "descripcion": "Precio registrado",
                "precio": self._number(x.get("precio")),
                "proveedor": x.get("proveedor_nombre") or None,
            } for x in history],
            "operatividad": {
                "stock": bool(product.get("nombre") and product.get("unidad_base")),
                "compras": bool(product.get("nombre") and product.get("unidad_base") and preferred_provider and product.get("unidad_compra")),
                "escandallos": bool(product.get("nombre") and product.get("unidad_base")),
            },
            "edicion": {
                "unidades_base": sorted(self.BASE_UNITS),
                "proveedores": [{"id": p.get("id") or p.get("codigo"), "nombre": p.get("nombre")} for p in self._providers() if p.get("nombre")],
            },
        }
        return {"ok": True, "articulo": detail}

    def actualizar(
        self, article_id: str, body: dict[str, Any], *, audit_context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if body.get("confirmacion") != "ACTUALIZAR_ARTICULO_MAESTRO":
            return self._error("confirmation_required", "Confirma explícitamente la actualización.", 400)
        unknown = sorted(set(body) - self.EDITABLE_FIELDS - {"confirmacion"})
        if unknown:
            return self._error("invalid_field", f"Campos no admitidos: {', '.join(unknown)}.", 400)
        current = self.catalogo.repositorio.obtener_producto(article_id)
        if not current:
            return self._error("article_not_found", "Artículo no encontrado.", 404)
        changes = {key: body[key] for key in self.EDITABLE_FIELDS if key in body}
        name = str(changes.get("nombre", current.get("nombre")) or "").strip()
        base_unit = str(changes.get("unidad_base", current.get("unidad_base")) or "").strip().lower()
        if not name:
            return self._error("invalid_name", "El nombre es obligatorio.", 400)
        if base_unit not in self.BASE_UNITS:
            return self._error("invalid_base_unit", "Selecciona una unidad base válida.", 400)
        changes["nombre"] = name
        changes["unidad_base"] = base_unit
        if "cantidad_formato" in changes and changes["cantidad_formato"] not in (None, ""):
            value = self._number(changes["cantidad_formato"])
            if value is None or value <= 0:
                return self._error("invalid_format_quantity", "La cantidad por formato debe ser mayor que cero.", 400)
            changes["cantidad_formato"] = value
        if "unidad_formato" in changes:
            format_unit = str(changes["unidad_formato"] or "").strip().lower()
            if format_unit and format_unit not in self.BASE_UNITS:
                return self._error("invalid_format_unit", "Selecciona una unidad de contenido válida.", 400)
            changes["unidad_formato"] = format_unit
        if "precio" in changes and changes["precio"] not in (None, ""):
            value = self._number(changes["precio"])
            if value is None or value <= 0:
                return self._error("invalid_price", "El precio debe ser mayor que cero.", 400)
            changes["precio"] = value
        provider = str(changes.get("proveedor_preferente") or "").strip()
        if provider:
            providers = self._providers()
            match = next((p for p in providers if self._norm(p.get("nombre")) == self._norm(provider)), None)
            if not match:
                return self._error("provider_not_found", "Selecciona un proveedor existente.", 400)
            changes["proveedor_preferente"] = str(match.get("nombre"))
            changes["proveedor"] = str(match.get("nombre"))
        elif "proveedor_preferente" in changes:
            changes["proveedor"] = ""
        if audit_context:
            changes.update({
                "actor_modificacion": str(audit_context.get("user_id") or ""),
                "tenant_modificacion": str(audit_context.get("tenant_id") or ""),
                "request_id_modificacion": str(audit_context.get("request_id") or ""),
            })
        updated = self.catalogo.editar(article_id, changes)
        if not updated.get("ok"):
            return self._error("article_update_failed", str(updated.get("mensaje") or "No se pudo actualizar el artículo."), 400)
        return {**self.obtener(article_id), "datos_reales_modificados": True, "mensaje": "Artículo actualizado correctamente."}

    @staticmethod
    def _error(code: str, message: str, status: int) -> dict[str, Any]:
        return {"ok": False, "error": {"code": code, "message": message, "status": status}}
