from __future__ import annotations

import math
import re
import unicodedata
from pathlib import Path
from typing import Any

from SERVICIOS.biblioteca_escandallos_601 import RepositorioBibliotecaEscandallos601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


class BibliotecaCulinariaReadService:
    """Contrato público de solo lectura sobre la Biblioteca 6.0.1."""

    ALLOWED = {
        "q", "page", "page_size", "estado", "categoria", "tiene_receta",
        "tiene_escandallo", "tiene_ficha_tecnica", "tiene_documentos",
        "orden", "direccion",
    }
    ORDERS = {"nombre", "actualizacion", "coste", "categoria", "estado"}

    def __init__(self, base_dir: Path) -> None:
        self.recetas = RepositorioBibliotecaRecetas601(base_dir)
        self.escandallos = RepositorioBibliotecaEscandallos601(base_dir)
        self.articulos = RepositorioProductosMaestro601(base_dir)

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(c for c in text if not unicodedata.combining(c)).strip().lower()

    @staticmethod
    def _public_text(value: Any) -> str:
        return re.sub(r"\bAP\b", "Elaboración", str(value or ""), flags=re.IGNORECASE)

    @classmethod
    def _public_value(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: cls._public_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._public_value(item) for item in value]
        if isinstance(value, str):
            return cls._public_text(value)
        return value

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            return float(value) if value not in ("", None) else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _bool_query(value: Any) -> bool | None:
        text = str(value or "").lower()
        if not text:
            return None
        if text == "true":
            return True
        if text == "false":
            return False
        raise ValueError("Los indicadores deben ser true o false.")

    def _escandallo_for(self, receta: dict[str, Any]) -> dict[str, Any] | None:
        rid = self._norm(receta.get("id"))
        code = self._norm(receta.get("codigo"))
        candidates = []
        for item in self.escandallos.listar(incluir_archivados=True):
            related = dict(item.get("receta_asociada") or {})
            if rid and self._norm(related.get("id")) == rid:
                candidates.append(item)
            elif code and self._norm(related.get("codigo")) == code:
                candidates.append(item)
        candidates.sort(
            key=lambda x: str(x.get("fecha_ultimo_calculo") or x.get("actualizado_en") or ""),
            reverse=True,
        )
        return candidates[0] if candidates else None

    @staticmethod
    def _has_recipe(receta: dict[str, Any]) -> bool:
        return bool(
            list(receta.get("ingredientes") or [])
            and str(receta.get("elaboracion") or "").strip()
        )

    @staticmethod
    def _documents(receta: dict[str, Any]) -> list[dict[str, Any]]:
        output = []
        for kind, field in (
            ("word", "documentos_word"),
            ("pdf", "documentos_pdf"),
            ("imagen", "documentos_fotografias"),
        ):
            for path in list(receta.get(field) or []):
                output.append({"tipo": kind, "nombre": Path(str(path)).name, "referencia": str(path)})
        return output

    def _summary(self, receta: dict[str, Any]) -> dict[str, Any]:
        esc = self._escandallo_for(receta)
        documents = self._documents(receta)
        technical = self._public_value(dict(receta.get("ficha_tecnica") or {}))
        completeness = dict(receta.get("completitud") or {})
        total_cost = self._number(esc.get("coste_total")) if esc else self._number(receta.get("coste_total"))
        unit_cost = self._number(esc.get("coste_por_racion")) if esc else self._number(receta.get("coste_por_racion"))
        return {
            "id": str(receta.get("id") or ""),
            "codigo": str(receta.get("codigo") or ""),
            "nombre": self._public_text(receta.get("nombre")),
            "descripcion": self._public_text(receta.get("descripcion")) or None,
            "categoria": self._public_text(receta.get("categoria") or receta.get("familia")) or None,
            "tipo": self._public_text(receta.get("tipo")) or "Elaboración",
            "estado": str(receta.get("estado") or "PENDIENTE_DE_COMPLETAR"),
            "rendimiento": self._number(receta.get("rendimiento") or receta.get("numero_raciones")),
            "unidad_rendimiento": "raciones" if receta.get("numero_raciones") else None,
            "raciones": self._number(receta.get("numero_raciones")),
            "coste_total": total_cost,
            "coste_por_racion": unit_cost,
            "tiene_receta": self._has_recipe(receta),
            "tiene_escandallo": esc is not None,
            "tiene_ficha_tecnica": bool(technical),
            "tiene_fotografia": bool(receta.get("fotografia") or receta.get("documentos_fotografias")),
            "tiene_documentos": bool(documents),
            "completitud": self._number(completeness.get("porcentaje")),
            "actualizado_en": receta.get("actualizado_en") or None,
        }

    def resumen(self) -> dict[str, Any]:
        items = [self._summary(x) for x in self.recetas.listar(incluir_archivadas=False)]
        return {
            "ok": True,
            "biblioteca": {
                "estado": "datos_disponibles" if items else "sin_datos",
                "total_elaboraciones": len(items),
                "sin_receta": sum(not x["tiene_receta"] for x in items),
                "sin_escandallo": sum(not x["tiene_escandallo"] for x in items),
                "sin_ficha_tecnica": sum(not x["tiene_ficha_tecnica"] for x in items),
                "con_documentos": sum(x["tiene_documentos"] for x in items),
                "capacidades": self._capabilities(),
            },
        }

    def listar(self, query: dict[str, Any]) -> dict[str, Any]:
        unknown = sorted(set(query) - self.ALLOWED)
        if unknown:
            return self._error("invalid_filter", f"Filtros no admitidos: {', '.join(unknown)}.", 400)
        try:
            page = int(query.get("page") or 1)
            size = int(query.get("page_size") or 25)
            flags = {
                key: self._bool_query(query.get(key))
                for key in ("tiene_receta", "tiene_escandallo", "tiene_ficha_tecnica", "tiene_documentos")
            }
        except (TypeError, ValueError) as exc:
            return self._error("invalid_parameters", str(exc), 400)
        if page < 1 or size < 1 or size > 100:
            return self._error("invalid_pagination", "page debe ser >= 1 y page_size entre 1 y 100.", 400)
        order = str(query.get("orden") or "nombre")
        direction = str(query.get("direccion") or "asc").lower()
        if order not in self.ORDERS or direction not in {"asc", "desc"}:
            return self._error("invalid_sort", "Ordenación no válida.", 400)

        all_items = [self._summary(x) for x in self.recetas.listar(incluir_archivadas=True)]
        items = list(all_items)
        q = self._norm(query.get("q"))
        if q:
            raw_by_id = {str(x.get("id")): x for x in self.recetas.listar(incluir_archivadas=True)}
            items = [
                x for x in items
                if any(q in self._norm(x.get(k)) for k in ("nombre", "codigo", "categoria"))
                or any(q in self._norm(v) for v in list(raw_by_id.get(x["id"], {}).get("ingredientes") or []))
            ]
        for key in ("estado", "categoria"):
            wanted = self._norm(query.get(key))
            if wanted:
                items = [x for x in items if self._norm(x.get(key)) == wanted]
        for key, wanted in flags.items():
            if wanted is not None:
                items = [x for x in items if bool(x[key]) is wanted]
        key_fn = {
            "nombre": lambda x: self._norm(x["nombre"]),
            "actualizacion": lambda x: str(x["actualizado_en"] or ""),
            "coste": lambda x: (x["coste_por_racion"] is None, x["coste_por_racion"] or 0),
            "categoria": lambda x: self._norm(x["categoria"]),
            "estado": lambda x: self._norm(x["estado"]),
        }[order]
        items.sort(key=key_fn, reverse=direction == "desc")
        total = len(items)
        start = (page - 1) * size
        return {
            "ok": True,
            "elaboraciones": {
                "items": items[start:start + size],
                "page": page,
                "page_size": size,
                "total": total,
                "total_pages": math.ceil(total / size) if total else 0,
                "filters": {
                    "estados": sorted({x["estado"] for x in all_items if x["estado"]}),
                    "categorias": sorted({x["categoria"] for x in all_items if x["categoria"]}),
                },
                "capabilities": self._capabilities(),
            },
        }

    def detalle(self, elaboracion_id: str) -> dict[str, Any]:
        receta = self.recetas.obtener(elaboracion_id)
        if not receta:
            return self._error("elaboration_not_found", "Elaboración no encontrada.", 404)
        esc = self._escandallo_for(receta)
        ingredients = self._ingredients(receta, esc)
        technical = self._public_value(dict(receta.get("ficha_tecnica") or {}))
        detail = {
            **self._summary(receta),
            "receta": {
                "ingredientes": ingredients,
                "procedimiento": self._public_text(receta.get("elaboracion")) or None,
                "observaciones": self._public_text(receta.get("observaciones")) or None,
                "tiempo_total": receta.get("tiempo_total") or receta.get("tiempo_elaboracion") or None,
                "tiempo_activo": receta.get("tiempo_activo") or None,
                "tiempo_pasivo": receta.get("tiempo_pasivo") or None,
                "tecnicas": list(receta.get("tecnicas_culinarias") or []),
            },
            "escandallo": self._public_escandallo(esc),
            "ficha_tecnica": technical or None,
            "alergenos": list(receta.get("alergenos") or []),
            "conservacion": receta.get("conservacion") or None,
            "regeneracion": receta.get("regeneracion") or None,
            "produccion": {
                "produccion_minima": receta.get("produccion_minima") or None,
                "produccion_maxima": receta.get("produccion_maxima") or None,
                "personal_recomendado": receta.get("personal_recomendado") or None,
                "recursos": list(receta.get("recursos_necesarios") or []),
            },
            "documentos": self._documents(receta),
            "imagenes": [x for x in [receta.get("fotografia")] if x] + list(receta.get("documentos_fotografias") or []),
            "versiones": [{"version": receta.get("version"), "fecha": receta.get("actualizado_en")}]
            if receta.get("version") else [],
            "menus": list(receta.get("menus_utilizacion") or []),
            "eventos": list(receta.get("eventos_utilizacion") or []),
            "historial": [],
            "pendientes": list((receta.get("completitud") or {}).get("campos_obligatorios_pendientes") or []),
        }
        return {"ok": True, "elaboracion": detail}

    def _ingredients(self, receta: dict[str, Any], esc: dict[str, Any] | None) -> list[dict[str, Any]]:
        catalog = self.articulos.listar_productos(incluir_archivados=True)
        by_name: dict[str, list[dict[str, Any]]] = {}
        for article in catalog:
            by_name.setdefault(self._norm(article.get("nombre")), []).append(article)
        esc_lines = list((esc or {}).get("lineas") or [])
        output = []
        names = list(receta.get("ingredientes") or [])
        amounts = list(receta.get("cantidades") or [])
        for index, name in enumerate(names):
            matches = by_name.get(self._norm(name), [])
            line = esc_lines[index] if index < len(esc_lines) and isinstance(esc_lines[index], dict) else {}
            output.append({
                "articulo_id": str(matches[0].get("codigo")) if len(matches) == 1 else None,
                "nombre_original": self._public_text(name),
                "cantidad_texto": str(amounts[index]) if index < len(amounts) else None,
                "cantidad": self._number(line.get("cantidad_neta") or line.get("cantidad")),
                "unidad": line.get("unidad_normalizada") or line.get("unidad") or None,
                "merma": self._number(line.get("merma_porcentaje")),
                "cantidad_neta": self._number(line.get("cantidad_neta")),
                "coste_unitario": self._number(line.get("precio_unitario")),
                "coste_linea": self._number(line.get("coste_linea")),
                "observaciones": line.get("observaciones") or None,
                "estado_relacion": "relacionado" if len(matches) == 1 else ("coincidencia_dudosa" if matches else "sin_relacionar"),
            })
        return output

    def _public_escandallo(self, esc: dict[str, Any] | None) -> dict[str, Any] | None:
        if not esc:
            return None
        return {
            "id": esc.get("id"),
            "estado": esc.get("estado"),
            "coste_ingredientes": self._number(esc.get("coste_ingredientes")),
            "otros_costes": self._number(esc.get("otros_costes")),
            "coste_total": self._number(esc.get("coste_total")),
            "rendimiento": self._number(esc.get("rendimiento_total") or esc.get("numero_raciones")),
            "coste_por_racion": self._number(esc.get("coste_por_racion")),
            "precio_objetivo": self._number(esc.get("precio_venta_por_racion")),
            "margen": self._number(esc.get("margen_porcentual") or esc.get("margen")),
            "fecha_calculo": esc.get("fecha_ultimo_calculo") or esc.get("fecha_calculo") or None,
            "desactualizado": str(esc.get("estado") or "").upper() == "DESACTUALIZADO",
            "incidencias": list(esc.get("incidencias") or []),
        }

    @staticmethod
    def _capabilities() -> dict[str, bool]:
        return {
            "lectura": True,
            "recetas": True,
            "escandallos": True,
            "fichas_tecnicas": True,
            "documentos": True,
            "menus": False,
            "importaciones": False,
            "crear": False,
            "editar": False,
            "duplicar": False,
        }

    @staticmethod
    def _error(code: str, message: str, status: int) -> dict[str, Any]:
        return {"ok": False, "error": {"code": code, "message": message, "status": status}}
