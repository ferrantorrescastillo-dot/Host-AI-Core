from __future__ import annotations

import math
import unicodedata
from pathlib import Path
from typing import Any

from SERVICIOS.catalogo_maestro_productos_601 import CatalogoMaestroProductos601


class ArticulosCatalogReadService:
    """Vista pública de solo lectura del catálogo maestro existente."""

    ALLOWED_QUERY = {
        "q", "familia", "proveedor", "estado", "con_stock",
        "page", "page_size", "orden", "direccion",
    }
    SORT_FIELDS = {"nombre", "codigo", "precio", "stock", "actualizacion"}

    def __init__(self, base_dir: Path, stock: Any | None = None) -> None:
        self.catalogo = CatalogoMaestroProductos601(base_dir)
        self.stock = stock

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
            "unidad_base": product.get("unidad_base") or None,
            "unidad_recetas": product.get("unidad_recetas") or None,
            "iva": self._number(product.get("iva")),
            "precio_incluye_iva": bool(product.get("precio_incluye_iva", False)),
            "alergenos": list(product.get("alergenos") or []),
            "conservacion": product.get("conservacion") or None,
            "stock_minimo": self._number(product.get("stock_minimo")),
            "observaciones": product.get("observaciones_ext") or product.get("observaciones") or None,
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
        }
        return {"ok": True, "articulo": detail}

    @staticmethod
    def _error(code: str, message: str, status: int) -> dict[str, Any]:
        return {"ok": False, "error": {"code": code, "message": message, "status": status}}
