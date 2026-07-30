from __future__ import annotations

import math
import re
import unicodedata
from hashlib import sha256
from pathlib import Path
from typing import Any

from SERVICIOS.biblioteca_escandallos_601 import RepositorioBibliotecaEscandallos601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.lector_modelo_canonico_555b72 import LectorModeloCanonico555B72
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
        self.modelo_canonico = LectorModeloCanonico555B72(base_dir)

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(c for c in text if not unicodedata.combining(c)).strip().lower()

    @staticmethod
    def _public_text(value: Any) -> str:
        return re.sub(r"\bA\.?P\.?(?=\s|$)", "Elaboración", str(value or ""), flags=re.IGNORECASE)

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
    def _first_present(*values: Any) -> Any:
        return next((value for value in values if value not in ("", None)), None)

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

    def _all_recipes(self, incluir_archivadas: bool) -> list[dict[str, Any]]:
        """Proyecta las fichas 6.0.1 y completa con el modelo culinario canónico."""
        recipes = self.recetas.listar(incluir_archivadas=incluir_archivadas)
        output = [dict(item) for item in recipes]
        identities = {
            self._norm(item.get("codigo") or item.get("id") or item.get("nombre"))
            for item in output
        }
        for escandallo in self.modelo_canonico.cargar().get("escandallos", []):
            recipe = self._canonical_recipe(dict(escandallo))
            identity = self._norm(recipe.get("codigo") or recipe.get("id") or recipe.get("nombre"))
            if not identity or identity in identities:
                continue
            output.append(recipe)
            identities.add(identity)
        return output

    def _canonical_recipe(self, escandallo: dict[str, Any]) -> dict[str, Any]:
        code = str(escandallo.get("codigo") or escandallo.get("receta_id") or "").strip()
        name = str(escandallo.get("nombre") or escandallo.get("receta") or "").strip()
        raw = escandallo.get("raw") if isinstance(escandallo.get("raw"), dict) else {}
        ingredients = [
            dict(item)
            for item in list(escandallo.get("ingredientes") or escandallo.get("lineas") or [])
            if isinstance(item, dict)
        ]
        if not code:
            seed = "|".join(
                (
                    self._norm(name),
                    str(escandallo.get("rendimiento") or escandallo.get("raciones_base") or ""),
                    self._norm(escandallo.get("unidad_rendimiento")),
                )
            )
            code = f"ELAB-{sha256(seed.encode('utf-8')).hexdigest()[:16].upper()}"
        amounts = []
        for ingredient in ingredients:
            quantity = ingredient.get("cantidad")
            unit = str(ingredient.get("unidad") or "").strip()
            amounts.append(
                " ".join(part for part in (self._format_number(quantity), unit) if part) or None
            )
        active = escandallo.get("activo")
        return {
            "id": code,
            "codigo": code,
            "nombre": name,
            "familia": escandallo.get("grupo") or escandallo.get("familia") or "",
            "categoria": escandallo.get("grupo") or escandallo.get("familia") or "",
            "tipo": "Elaboración",
            "descripcion": escandallo.get("observaciones") or "",
            "numero_raciones": escandallo.get("raciones_base"),
            "rendimiento": self._first_present(escandallo.get("rendimiento"), escandallo.get("raciones_base")),
            "unidad_rendimiento": escandallo.get("unidad_rendimiento") or "",
            "ingredientes": [str(item.get("nombre") or item.get("ingrediente") or "").strip() for item in ingredients],
            "cantidades": amounts,
            "elaboracion": escandallo.get("elaboracion") or escandallo.get("procedimiento") or "",
            "estado": "ARCHIVADA" if active is False else "PENDIENTE_DE_COMPLETAR",
            "actualizado_en": escandallo.get("actualizado_en") or None,
            "coste_total": (
                raw.get("coste_total")
                if "coste_total" in raw
                else self._first_present(escandallo.get("coste_total"), escandallo.get("coste_total_base"))
            ),
            "coste_por_racion": escandallo.get("coste_por_racion"),
            "_origen_modelo": escandallo.get("origen_modelo") or "legacy",
            "_ingredientes_estructurados": ingredients,
            "_escandallo_canonico": escandallo,
        }

    @staticmethod
    def _format_number(value: Any) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value or "").strip()
        return f"{number:g}"

    def _escandallo_for(self, receta: dict[str, Any]) -> dict[str, Any] | None:
        canonical = receta.get("_escandallo_canonico")
        if isinstance(canonical, dict):
            return {
                "id": receta.get("codigo"),
                "estado": "PARCIAL",
                "coste_total": receta.get("coste_total"),
                "coste_por_racion": canonical.get("coste_por_racion"),
                "rendimiento_total": canonical.get("rendimiento") or canonical.get("raciones_base"),
                "numero_raciones": canonical.get("raciones_base"),
                "precio_venta_por_racion": canonical.get("precio_venta_unitario"),
                "margen_porcentual": canonical.get("margen_porcentual"),
                "fecha_ultimo_calculo": canonical.get("actualizado_en"),
                "lineas": list(receta.get("_ingredientes_estructurados") or []),
                "incidencias": list(canonical.get("incidencias") or []),
            }
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
        if receta.get("_origen_modelo") in {"canonico", "legacy"}:
            return bool(list(receta.get("ingredientes") or []))
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
        has_production = any(
            (
                receta.get("produccion_minima"),
                receta.get("produccion_maxima"),
                receta.get("personal_recomendado"),
                receta.get("recursos_necesarios"),
            )
        )
        has_relations = bool(receta.get("menus_utilizacion") or receta.get("eventos_utilizacion"))
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
            "unidad_rendimiento": receta.get("unidad_rendimiento") or ("raciones" if receta.get("numero_raciones") else None),
            "raciones": self._number(receta.get("numero_raciones")),
            "coste_total": total_cost,
            "coste_por_racion": unit_cost,
            "tiene_receta": self._has_recipe(receta),
            "tiene_escandallo": esc is not None,
            "tiene_ficha_tecnica": bool(technical),
            "tiene_fotografia": bool(receta.get("fotografia") or receta.get("documentos_fotografias")),
            "tiene_documentos": bool(documents),
            "tiene_produccion": has_production,
            "tiene_relaciones_menu_evento": has_relations,
            "completitud": self._number(completeness.get("porcentaje")),
            "actualizado_en": receta.get("actualizado_en") or None,
        }

    def resumen(self) -> dict[str, Any]:
        items = [self._summary(x) for x in self._all_recipes(incluir_archivadas=False)]
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

        all_recipes = self._all_recipes(incluir_archivadas=True)
        all_items = [self._summary(x) for x in all_recipes]
        items = list(all_items)
        q = self._norm(query.get("q"))
        if q:
            raw_by_id = {str(x.get("id")): x for x in all_recipes}
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
        identity = self._norm(elaboracion_id)
        receta = next(
            (
                item
                for item in self._all_recipes(incluir_archivadas=True)
                if identity in {self._norm(item.get("id")), self._norm(item.get("codigo"))}
            ),
            None,
        )
        if not receta:
            return self._error("elaboration_not_found", "Elaboración no encontrada.", 404)
        esc = self._escandallo_for(receta)
        ingredients = self._ingredients(receta, esc)
        public_escandallo = self._public_escandallo(esc, ingredients)
        documents = self._documents(receta)
        production = self._production(receta)
        menus = list(receta.get("menus_utilizacion") or [])
        events = list(receta.get("eventos_utilizacion") or [])
        pending = self._pending_fields(receta, public_escandallo)
        technical = self._technical_sheet(
            receta, ingredients, public_escandallo, documents, production, pending,
        )
        summary = self._summary(receta)
        detail = {
            **summary,
            "receta": {
                "ingredientes": ingredients,
                "procedimiento": self._public_text(receta.get("elaboracion")) or None,
                "pasos": self._public_value(list(receta.get("pasos") or [])),
                "observaciones": self._public_text(receta.get("observaciones")) or None,
                "tiempo_total": receta.get("tiempo_total") or receta.get("tiempo_elaboracion") or None,
                "tiempo_activo": receta.get("tiempo_activo") or None,
                "tiempo_pasivo": receta.get("tiempo_pasivo") or None,
                "temperaturas": self._public_value(list(receta.get("temperaturas") or [])),
                "tecnicas": list(receta.get("tecnicas_culinarias") or []),
                "rendimiento": summary.get("rendimiento"),
                "unidad_rendimiento": summary.get("unidad_rendimiento"),
                "raciones": summary.get("raciones"),
            },
            "escandallo": public_escandallo,
            "ficha_tecnica": technical,
            "alergenos": list(receta.get("alergenos") or []),
            "conservacion": receta.get("conservacion") or None,
            "regeneracion": receta.get("regeneracion") or None,
            "produccion": production,
            "documentos": documents,
            "imagenes": [x for x in [receta.get("fotografia")] if x] + list(receta.get("documentos_fotografias") or []),
            "versiones": [{"version": receta.get("version"), "fecha": receta.get("actualizado_en")}]
            if receta.get("version") else [],
            "menus": menus,
            "eventos": events,
            "historial": self._history(esc),
            "pendientes": pending,
            "avisos": self._warnings(summary, ingredients, public_escandallo),
        }
        return {"ok": True, "elaboracion": detail}

    @staticmethod
    def _production(receta: dict[str, Any]) -> dict[str, Any]:
        return {
            "indicaciones": {
                "produccion_minima": receta.get("produccion_minima") or None,
                "produccion_maxima": receta.get("produccion_maxima") or None,
                "personal_recomendado": receta.get("personal_recomendado") or None,
                "recursos": list(receta.get("recursos_necesarios") or []),
                "notas": receta.get("notas_produccion") or None,
            },
            "ordenes": list(receta.get("ordenes_produccion") or []),
            "necesidades": list(receta.get("necesidades_produccion") or []),
            "historial": list(receta.get("historial_produccion") or []),
        }

    def _pending_fields(
        self,
        receta: dict[str, Any],
        escandallo: dict[str, Any] | None,
    ) -> list[str]:
        declared = list(
            (receta.get("completitud") or {}).get("campos_obligatorios_pendientes") or []
        )
        checks = (
            ("Descripción", receta.get("descripcion")),
            ("Procedimiento", receta.get("elaboracion")),
            ("Tiempo total", receta.get("tiempo_total") or receta.get("tiempo_elaboracion")),
            ("Conservación", receta.get("conservacion")),
            ("Alérgenos", receta.get("alergenos") if "alergenos" in receta else None),
            ("Coste por ración", (escandallo or {}).get("coste_por_racion")),
        )
        pending = [self._public_text(item) for item in declared]
        for label, value in checks:
            if label == "Alérgenos" and "alergenos" in receta:
                continue
            if value in (None, "", []):
                pending.append(label)
        return list(dict.fromkeys(pending))

    def _technical_sheet(
        self,
        receta: dict[str, Any],
        ingredients: list[dict[str, Any]],
        escandallo: dict[str, Any] | None,
        documents: list[dict[str, Any]],
        production: dict[str, Any],
        pending: list[str],
    ) -> dict[str, Any]:
        persisted = self._public_value(dict(receta.get("ficha_tecnica") or {}))
        return {
            "estado": "COMPLETA" if persisted and not pending else "EN_CONSTRUCCION",
            "origen": "ficha_persistida" if persisted else "proyeccion_datos_existentes",
            "persistida": bool(persisted),
            "identificacion": {
                "id": receta.get("id"),
                "codigo": receta.get("codigo"),
                "nombre": self._public_text(receta.get("nombre")),
                "categoria": self._public_text(receta.get("categoria") or receta.get("familia")) or None,
            },
            "descripcion": self._public_text(receta.get("descripcion")) or None,
            "fotografia": receta.get("fotografia") or None,
            "ingredientes": ingredients,
            "proceso": {
                "procedimiento": self._public_text(receta.get("elaboracion")) or None,
                "pasos": self._public_value(list(receta.get("pasos") or [])),
                "observaciones": self._public_text(receta.get("observaciones")) or None,
            },
            "tiempos": {
                "activo": receta.get("tiempo_activo") or None,
                "pasivo": receta.get("tiempo_pasivo") or None,
                "total": receta.get("tiempo_total") or receta.get("tiempo_elaboracion") or None,
            },
            "temperaturas": self._public_value(list(receta.get("temperaturas") or [])),
            "rendimiento": self._number(receta.get("rendimiento") or receta.get("numero_raciones")),
            "unidad_rendimiento": receta.get("unidad_rendimiento") or None,
            "raciones": self._number(receta.get("numero_raciones")),
            "escandallo": escandallo,
            "alergenos": list(receta.get("alergenos") or []),
            "conservacion": receta.get("conservacion") or None,
            "caducidad": receta.get("caducidad") or receta.get("vida_util_refrigerado") or None,
            "regeneracion": receta.get("regeneracion") or None,
            "presentacion": receta.get("presentacion") or None,
            "utensilios": list(receta.get("utensilios") or []),
            "produccion": production,
            "documentos": documents,
            "version": receta.get("version") or None,
            "actualizado_en": receta.get("actualizado_en") or None,
            "campos_pendientes": pending,
            "datos_persistidos": persisted or None,
        }

    def _history(self, escandallo: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not escandallo or not escandallo.get("id"):
            return []
        return self._public_value(self.escandallos.historial(str(escandallo["id"])))

    @staticmethod
    def _warnings(
        summary: dict[str, Any],
        ingredients: list[dict[str, Any]],
        escandallo: dict[str, Any] | None,
    ) -> list[str]:
        warnings = []
        unlinked = sum(item.get("estado_relacion") != "relacionado" for item in ingredients)
        if unlinked:
            warnings.append(f"{unlinked} ingrediente(s) sin relación confirmada con Artículos.")
        missing_cost = int((escandallo or {}).get("ingredientes_sin_coste") or 0)
        if missing_cost:
            warnings.append(f"{missing_cost} ingrediente(s) sin precio disponible.")
        if not summary.get("tiene_ficha_tecnica"):
            warnings.append("Ficha técnica en construcción.")
        if not summary.get("tiene_documentos"):
            warnings.append("Sin documentos asociados.")
        return warnings

    def _ingredients(self, receta: dict[str, Any], esc: dict[str, Any] | None) -> list[dict[str, Any]]:
        catalog = self.articulos.listar_productos(incluir_archivados=True)
        by_name: dict[str, list[dict[str, Any]]] = {}
        by_code: dict[str, dict[str, Any]] = {}
        for article in catalog:
            by_name.setdefault(self._norm(article.get("nombre")), []).append(article)
            code = self._norm(article.get("codigo"))
            if code:
                by_code[code] = article
        esc_lines = list((esc or {}).get("lineas") or [])
        structured = list(receta.get("_ingredientes_estructurados") or [])
        output = []
        names = list(receta.get("ingredientes") or [])
        amounts = list(receta.get("cantidades") or [])
        for index, name in enumerate(names):
            source = structured[index] if index < len(structured) and isinstance(structured[index], dict) else {}
            line = esc_lines[index] if index < len(esc_lines) and isinstance(esc_lines[index], dict) else {}
            source_code = str(source.get("articulo_id") or source.get("codigo") or "").strip()
            direct = by_code.get(self._norm(source_code)) if source_code else None
            matches = [direct] if direct else by_name.get(self._norm(name), [])
            linked = matches[0] if len(matches) == 1 else None
            output.append({
                "articulo_id": str(linked.get("codigo")) if linked else None,
                "codigo": source_code or (str(linked.get("codigo")) if linked else None),
                "nombre_original": self._public_text(name),
                "cantidad_texto": str(amounts[index]) if index < len(amounts) else None,
                "cantidad": self._number(line.get("cantidad_neta") or line.get("cantidad")),
                "unidad": line.get("unidad_normalizada") or line.get("unidad") or None,
                "merma": self._number(line.get("merma_porcentaje") or line.get("merma_pct")),
                "cantidad_neta": self._number(line.get("cantidad_neta")),
                "coste_unitario": self._number(line.get("precio_unitario") or line.get("coste_unitario")),
                "coste_linea": self._number(line.get("coste_linea") or line.get("coste_total")),
                "observaciones": line.get("observaciones") or None,
                "estado_relacion": "relacionado" if len(matches) == 1 else ("coincidencia_dudosa" if matches else "sin_relacionar"),
            })
        return output

    def _public_escandallo(
        self,
        esc: dict[str, Any] | None,
        ingredients: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        if not esc:
            return None
        lines = list(ingredients or [])
        missing_cost = sum(
            item.get("coste_unitario") in (None, 0, 0.0)
            for item in lines
        )
        return {
            "id": esc.get("id"),
            "estado": esc.get("estado"),
            "estado_coste": (
                "SIN_COSTE"
                if lines and missing_cost == len(lines)
                else ("PARCIAL" if missing_cost else "DISPONIBLE")
            ),
            "lineas": lines,
            "coste_ingredientes": self._number(esc.get("coste_ingredientes")),
            "otros_costes": self._number(esc.get("otros_costes")),
            "coste_total": self._number(esc.get("coste_total")),
            "rendimiento": self._number(esc.get("rendimiento_total") or esc.get("numero_raciones")),
            "coste_por_racion": self._number(esc.get("coste_por_racion")),
            "precio_objetivo": self._number(esc.get("precio_venta_por_racion")),
            "margen": self._number(esc.get("margen_porcentual") or esc.get("margen")),
            "fecha_calculo": esc.get("fecha_ultimo_calculo") or esc.get("fecha_calculo") or None,
            "desactualizado": str(esc.get("estado") or "").upper() == "DESACTUALIZADO",
            "ingredientes_sin_coste": missing_cost,
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
