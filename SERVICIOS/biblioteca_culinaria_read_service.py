from __future__ import annotations

import math
import re
import unicodedata
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

from SERVICIOS.articulo_economico_canonico import normalize_incident_type

from CORE.entidades.receta import Receta, RendimientoNeto
from SERVICIOS.calculador_coste_subelaboraciones import CalculadorCosteSubelaboraciones
from SERVICIOS.calculador_rendimiento_fisico_teorico import CalculadorRendimientoFisicoTeorico
from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.biblioteca_escandallos_601 import RepositorioBibliotecaEscandallos601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.lector_modelo_canonico_555b72 import LectorModeloCanonico555B72
from SERVICIOS.motor_calculo_escandallos_601 import MotorCalculoEscandallos601
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from SERVICIOS.escalador_explosion_recetas_556ab import MotorEscaladoExplosion556AB


def _is_no_aplica(value: Any) -> bool:
    return isinstance(value, dict) and str(value.get("estado") or "").strip().upper() == "NO_APLICA"


class BibliotecaCulinariaReadService:
    """Contrato público de solo lectura sobre la Biblioteca 6.0.1."""

    ALLOWED = {
        "q", "page", "page_size", "estado", "categoria", "tiene_receta",
        "tiene_escandallo", "tiene_ficha_tecnica", "tiene_documentos",
        "orden", "direccion",
    }
    ORDERS = {"nombre", "actualizacion", "coste", "categoria", "estado"}
    COST_AGGREGATIONS = {
        "MAX_COSTE_POR_RACION": ("coste_por_racion", "MAX"),
        "MIN_COSTE_POR_RACION": ("coste_por_racion", "MIN"),
        "MAX_COSTE_TOTAL": ("coste_total", "MAX"),
        "MIN_COSTE_TOTAL": ("coste_total", "MIN"),
        "RANK_COSTE_POR_RACION": ("coste_por_racion", "RANK"),
        "COUNT_COSTE_DISPONIBLE": ("", "COUNT_AVAILABLE"),
        "COUNT_COSTE_INCOMPLETO": ("", "COUNT_INCOMPLETE"),
    }
    COST_STATES = {
        "PARCIAL", "PROVISIONAL", "SIN_ESCANDALLO", "SIN_COSTE", "SIN_PRECIO",
        "SIN_CONVERSION", "NO_CALCULABLE",
    }

    def __init__(self, base_dir: Path) -> None:
        self.recetas = RepositorioBibliotecaRecetas601(base_dir)
        self.escandallos = RepositorioBibliotecaEscandallos601(base_dir)
        self.articulos = RepositorioProductosMaestro601(base_dir)
        self.catalogo_articulos = ArticulosCatalogReadService(base_dir)
        self.motor_escandallos = MotorCalculoEscandallos601(self.articulos)
        self.motor_explosion = MotorEscaladoExplosion556AB(base_dir)
        self.calculador_subelaboraciones = CalculadorCosteSubelaboraciones()
        self.calculador_rendimiento_teorico = CalculadorRendimientoFisicoTeorico()
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
    def _yield_pending(receta: dict[str, Any]) -> bool:
        pending = {
            str(field or "").strip().casefold()
            for field in receta.get("campos_pendientes_importacion") or []
        }
        return (
            str(receta.get("estado") or "").upper() == "PENDIENTE_DE_COMPLETAR"
            and "rendimiento" in pending
        )

    @staticmethod
    def _list_or_none(value: Any) -> list[Any] | None:
        if value in (None, ""):
            return None
        if isinstance(value, list):
            return list(value)
        return [value]

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
        recipe_payload = escandallo.get("receta") if isinstance(escandallo.get("receta"), dict) else {}
        if not recipe_payload and isinstance(escandallo.get("receta_payload"), dict):
            recipe_payload = dict(escandallo.get("receta_payload") or {})

        def _source_value(*keys: str) -> Any:
            for container in (escandallo, recipe_payload, raw):
                if not isinstance(container, dict):
                    continue
                for key in keys:
                    if key in container:
                        return container.get(key)
            return None

        ingredients = [
            dict(item)
            for item in list(escandallo.get("ingredientes") or escandallo.get("lineas") or [])
            if isinstance(item, dict)
        ]
        if not ingredients:
            ingredients = [
                dict(item)
                for item in list(recipe_payload.get("ingredientes") or [])
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
        total_cost = self._number(escandallo.get("coste_total"))
        yield_value = self._number(escandallo.get("rendimiento") or escandallo.get("raciones_base"))
        unit_cost = self._number(escandallo.get("coste_por_racion"))
        if unit_cost is None and total_cost is not None and yield_value and yield_value > 0:
            unit_cost = round(total_cost / yield_value, 6)
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
            "estado_rendimiento": escandallo.get("estado_rendimiento"),
            "origen_rendimiento": self._public_value(escandallo.get("origen_rendimiento")),
            "rendimiento_neto": self._public_value(escandallo.get("rendimiento_neto")),
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
            "coste_por_racion": unit_cost,
            "_origen_modelo": escandallo.get("origen_modelo") or "legacy",
            "_ingredientes_estructurados": ingredients,
            "_escandallo_canonico": escandallo,
            "alergenos": _source_value("alergenos"),
            "propuesta_procedimiento_ia": _source_value(
                "propuesta_procedimiento_ia", "procedimiento_propuesto", "procedimiento_sugerido_ia",
            ),
            "ingredientes_propuestos_ia": _source_value(
                "ingredientes_propuestos_ia", "ingredientes_propuestos", "ingredientes_sugeridos_ia",
            ),
            "alergenos_posibles": _source_value(
                "alergenos_posibles", "posibles_alergenos", "alergenos_inferidos",
            ),
            "conservacion_propuesta_ia": _source_value(
                "conservacion_propuesta_ia", "propuesta_conservacion_ia",
            ),
            "temperaturas_sugeridas_ia": _source_value(
                "temperaturas_sugeridas_ia", "temperaturas_propuestas",
            ),
            "tiempos_estimados_ia": _source_value(
                "tiempos_estimados_ia", "tiempos_propuestos",
            ),
            "observaciones_propuestas_ia": _source_value(
                "observaciones_propuestas_ia", "observaciones_sugeridas_ia",
            ),
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
                "coste_por_racion": self._first_present(
                    canonical.get("coste_por_racion"), receta.get("coste_por_racion")
                ),
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

    def _summary(
        self,
        receta: dict[str, Any],
        cost_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        esc = self._escandallo_for(receta)
        public_costing = (
            self._costing(
                receta, esc, self._ingredients(receta, esc), context=cost_context,
            )
            if esc else None
        )
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
        total_cost = (
            self._number(public_costing.get("coste_total"))
            if public_costing else self._number(receta.get("coste_total"))
        )
        yield_pending = self._yield_pending(receta)
        unit_cost = (
            self._number(public_costing.get("coste_por_racion"))
            if public_costing else self._number(receta.get("coste_por_racion"))
        )
        if yield_pending:
            unit_cost = None
        return {
            "id": str(receta.get("id") or ""),
            "codigo": str(receta.get("codigo") or ""),
            "nombre": self._public_text(receta.get("nombre")),
            "descripcion": self._public_text(receta.get("descripcion")) or None,
            "categoria": self._public_text(receta.get("categoria") or receta.get("familia")) or None,
            "tipo": self._public_text(receta.get("tipo")) or "Elaboración",
            "estado": str(receta.get("estado") or "PENDIENTE_DE_COMPLETAR"),
            "rendimiento": None if yield_pending else self._number(receta.get("rendimiento") or receta.get("numero_raciones")),
            "unidad_rendimiento": None if yield_pending else receta.get("unidad_rendimiento") or ("raciones" if receta.get("numero_raciones") else None),
            "estado_rendimiento": receta.get("estado_rendimiento") or None,
            "origen_rendimiento": self._public_value(receta.get("origen_rendimiento")),
            "rendimiento_neto": self._public_value(receta.get("rendimiento_neto")),
            "raciones": None if yield_pending else self._number(receta.get("numero_raciones")),
            "coste_total": total_cost,
            "coste_por_racion": unit_cost,
            "estado_coste": (
                public_costing.get("estado_coste") if public_costing else "SIN_ESCANDALLO"
            ),
            "coste_completo": bool(
                public_costing and public_costing.get("estado_coste") == "DISPONIBLE"
            ),
            "coste_provisional": bool(
                public_costing and public_costing.get("estado_coste") == "PROVISIONAL"
            ),
            "motivo_coste_no_disponible": (
                "Pendiente de rendimiento." if yield_pending
                else self._cost_unavailable_reason(public_costing)
            ),
            "fecha_calculo": public_costing.get("fecha_calculo") if public_costing else None,
            "tiene_receta": self._has_recipe(receta),
            "tiene_escandallo": esc is not None,
            "tiene_ficha_tecnica": bool(technical),
            "tiene_fotografia": bool(receta.get("fotografia") or receta.get("documentos_fotografias")),
            "tiene_documentos": bool(documents),
            "tiene_produccion": has_production,
            "tiene_relaciones_menu_evento": has_relations,
            "completitud": self._number(completeness.get("porcentaje")),
            "actualizado_en": receta.get("actualizado_en") or None,
            "version": receta.get("version") or None,
        }

    @staticmethod
    def _cost_unavailable_reason(costing: dict[str, Any] | None) -> str | None:
        if not costing:
            return "Sin escandallo."
        if costing.get("estado_coste") == "DISPONIBLE":
            return None
        if costing.get("estado_coste") == "PROVISIONAL":
            return "Coste calculado exclusivamente con uno o más precios de referencia; pendiente de precio confirmado."
        return (
            f"Coste incompleto: {int(costing.get('ingredientes_sin_coste') or 0)} "
            f"ingrediente(s) sin precio y {int(costing.get('ingredientes_sin_conversion') or 0)} "
            "sin conversiÃ³n."
        )

    def resumen(self) -> dict[str, Any]:
        recipes = self._all_recipes(incluir_archivadas=False)
        context = self._cost_context(recipes)
        items = [self._summary(x, context) for x in recipes]
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

    def agregar_costes(
        self, agregacion: str, *, orden: str = "", posicion: int = 1,
    ) -> dict[str, Any]:
        operation = str(agregacion or "").strip().upper()
        contract = self.COST_AGGREGATIONS.get(operation)
        if contract is None:
            return self._error("invalid_aggregation", "Agregación económica no admitida.", 400)
        field, direction = contract
        recipes = self._all_recipes(incluir_archivadas=True)
        context = self._cost_context(recipes)
        summaries = [self._summary(recipe, context) for recipe in recipes]
        if direction.startswith("COUNT_"):
            available = [item for item in summaries if item.get("coste_completo") is True]
            incomplete = [item for item in summaries if item.get("coste_completo") is not True]
            selected = available if direction == "COUNT_AVAILABLE" else incomplete
            breakdown: dict[str, int] = {}
            for item in selected:
                state = str(item.get("estado_coste") or "SIN_ESTADO")
                breakdown[state] = breakdown.get(state, 0) + 1
            response = {
                "ok": True, "agregacion": operation, "estado": "OK",
                "total_evaluadas": len(summaries),
                "total_disponibles": len(available),
                "total_incompletas": len(incomplete),
                "conteo": len(selected),
                "desglose": dict(sorted(breakdown.items())),
                "datos_reales_modificados": False,
            }
            if direction == "COUNT_INCOMPLETE":
                response["candidatos_economicos"] = [{
                    "receta_id": str(item.get("id") or item.get("codigo") or ""),
                    "nombre": item.get("nombre"), "estado_coste": item.get("estado_coste"),
                } for item in incomplete[:10]]
            return response
        order = str(orden or "").strip().upper()
        rank = int(posicion or 0)
        if direction == "RANK" and order not in {"ASC", "DESC"}:
            return self._error("invalid_order", "Orden economico no admitido.", 400)
        if direction == "RANK" and not 1 <= rank <= 10:
            return self._error("invalid_position", "La posicion debe estar entre 1 y 10.", 400)
        valid: list[tuple[Decimal, dict[str, Any]]] = []
        for item in summaries:
            if item.get("estado_coste") != "DISPONIBLE" or item.get("coste_completo") is not True:
                continue
            if field == "coste_por_racion":
                yield_value = self._decimal(item.get("rendimiento") or item.get("raciones"))
                if yield_value is None or yield_value <= 0:
                    continue
            value = self._decimal(item.get(field))
            if value is None:
                continue
            valid.append((value, item))
        if not valid:
            return {
                "ok": True, "agregacion": operation, "estado": "SIN_RESULTADOS",
                "total_evaluadas": len(summaries), "total_validas": 0,
                "total_excluidas": len(summaries), "resultado": [],
                "datos_reales_modificados": False,
            }
        if direction == "RANK":
            values = sorted({value for value, _item in valid}, reverse=order == "DESC")
            if rank > len(values):
                return {
                    "ok": True, "agregacion": operation, "estado": "POSICION_NO_DISPONIBLE",
                    "orden": order, "posicion": rank,
                    "total_evaluadas": len(summaries), "total_validas": len(valid),
                    "total_excluidas": len(summaries) - len(valid), "numero_empates": 0,
                    "resultado": [], "datos_reales_modificados": False,
                }
            target = values[rank - 1]
        else:
            target = (max if direction == "MAX" else min)(value for value, _item in valid)
        winners = sorted(
            (item for value, item in valid if value == target),
            key=lambda item: str(item.get("id") or item.get("codigo") or ""),
        )
        response = {
            "ok": True, "agregacion": operation, "estado": "OK",
            "total_evaluadas": len(summaries), "total_validas": len(valid),
            "total_excluidas": len(summaries) - len(valid),
            "numero_empates": len(winners),
            "resultado": [{
                "receta_id": str(item.get("id") or item.get("codigo") or ""),
                "nombre": item.get("nombre"), field: float(target),
            } for item in winners],
            "datos_reales_modificados": False,
        }
        if direction == "RANK":
            response.update({"orden": order, "posicion": rank})
        return response

    def listar_costes_incompletos(
        self, *, estado_coste: str = "", pagina: int = 1, limite: int = 10,
    ) -> dict[str, Any]:
        state_filter = str(estado_coste or "").strip().upper()
        if state_filter and state_filter not in self.COST_STATES:
            return self._error("invalid_cost_state", "Estado economico no admitido.", 400)
        page = max(1, int(pagina or 1))
        size = max(1, min(int(limite or 10), 10))
        recipes = self._all_recipes(incluir_archivadas=True)
        context = self._cost_context(recipes)
        summaries = [self._summary(recipe, context) for recipe in recipes]
        matches = [
            item for item in summaries
            if item.get("coste_completo") is not True
            and (not state_filter or str(item.get("estado_coste") or "").upper() == state_filter)
        ]
        matches.sort(key=lambda item: str(item.get("id") or item.get("codigo") or ""))
        start = (page - 1) * size
        selected = matches[start:start + size]
        return {
            "ok": True, "consulta_economica": "LIST_COSTE_INCOMPLETO", "estado": "OK",
            "grounding_scope": "COSTE_INCOMPLETO_LIST",
            "filtro_estado_coste": state_filter or None,
            "total_evaluadas": len(summaries), "total_coincidencias": len(matches),
            "items_devueltos": len(selected), "pagina": page, "limite": size,
            "truncado": start + len(selected) < len(matches),
            "resultado": [{
                "receta_id": str(item.get("id") or item.get("codigo") or ""),
                "nombre": item.get("nombre"),
                "estado_coste": item.get("estado_coste"),
                "coste_completo": False,
                "resumen_causa": item.get("motivo_coste_no_disponible"),
            } for item in selected],
            "datos_reales_modificados": False,
        }

    def resolver_receta_economica(self, termino: str) -> dict[str, Any]:
        wanted = self._norm(termino)
        if not wanted:
            return {"ok": False, "estado": "REQUIERE_TERMINO", "candidatos": []}
        recipes = self._all_recipes(incluir_archivadas=True)
        context = self._cost_context(recipes)
        summaries = [self._summary(recipe, context) for recipe in recipes]
        exact = [
            item for item in summaries
            if wanted in {
                self._norm(item.get("id")), self._norm(item.get("codigo")),
                self._norm(item.get("nombre")),
            }
        ]
        matches = exact or [
            item for item in summaries if wanted in self._norm(item.get("nombre"))
        ]
        candidates = [{
            "receta_id": str(item.get("id") or item.get("codigo") or ""),
            "nombre": item.get("nombre"), "estado_coste": item.get("estado_coste"),
        } for item in matches[:10]]
        if len(matches) != 1:
            return {
                "ok": True, "estado": "AMBIGUO" if matches else "NO_ENCONTRADO",
                "total_coincidencias": len(matches), "candidatos": candidates,
                "datos_reales_modificados": False,
            }
        return {
            "ok": True, "estado": "RESUELTO", "receta_id": candidates[0]["receta_id"],
            "nombre": candidates[0]["nombre"], "estado_coste": candidates[0]["estado_coste"],
            "candidatos": candidates, "datos_reales_modificados": False,
        }

    def detalle_coste_incompleto(self, receta_id: str) -> dict[str, Any]:
        response = dict(self.detalle(receta_id) or {})
        detail = response.get("elaboracion")
        if response.get("ok") is False or not isinstance(detail, dict):
            return response
        costing = detail.get("escandallo") if isinstance(detail.get("escandallo"), dict) else None
        state = str(detail.get("estado_coste") or "SIN_ESCANDALLO")
        complete = detail.get("coste_completo") is True
        if state == "SIN_ESCANDALLO":
            return {
                "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO", "estado": "OK",
                "grounding_scope": "COSTE_INCOMPLETO",
                "receta_id": str(detail.get("id") or detail.get("codigo") or receta_id),
                "nombre": detail.get("nombre"), "estado_coste": "SIN_ESCANDALLO",
                "coste_completo": False,
                "causa": {
                    "tipo": "SIN_ESCANDALLO",
                    "mensaje": "No existe un escandallo registrado.",
                },
                "datos_reales_modificados": False,
            }
        reasons: list[dict[str, Any]] = []
        if costing:
            for line in list(costing.get("lineas") or []):
                if not isinstance(line, dict) or line.get("coste_linea") is not None:
                    continue
                reason = {
                    "tipo": normalize_incident_type(line.get("estado_coste")),
                    "articulo_id": line.get("articulo_id"),
                    "escandallo_hijo_id": line.get("escandallo_hijo_id"),
                    "nombre": line.get("nombre_articulo") or line.get("nombre_original"),
                    "detalle": line.get("motivo_sin_coste"),
                }
                source_unit = line.get("unidad") or line.get("unidad_receta")
                target_unit = line.get("unidad_base") or line.get("unidad_precio")
                if source_unit not in (None, ""):
                    reason["unidad_origen"] = source_unit
                if target_unit not in (None, ""):
                    reason["unidad_destino"] = target_unit
                if any(value not in (None, "") for value in reason.values()):
                    reasons.append(reason)
        reasons = reasons[:10]
        if complete:
            explanation = "El coste esta completo y disponible."
        elif reasons:
            explanation = "El detalle economico expone motivos estructurados."
        else:
            explanation = "El dominio marca el coste como incompleto, pero no expone una causa concreta."
        return {
            "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO", "estado": "OK",
            "grounding_scope": "COSTE_INCOMPLETO",
            "receta_id": str(detail.get("id") or detail.get("codigo") or receta_id),
            "nombre": detail.get("nombre"), "estado_coste": state,
            "coste_completo": complete, "explicacion": explanation,
            "coste_total": costing.get("coste_total") if costing else None,
            "coste_total_parcial": costing.get("coste_total_parcial") if costing else None,
            "coste_por_racion": costing.get("coste_por_racion") if costing else None,
            "motivos": reasons, "numero_motivos": len(reasons),
            "datos_reales_modificados": False,
        }

    @staticmethod
    def _decimal(value: Any) -> Decimal | None:
        if value in (None, "") or isinstance(value, bool):
            return None
        try:
            parsed = Decimal(str(value))
        except Exception:
            return None
        return parsed if parsed.is_finite() else None

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
        context = self._cost_context(all_recipes)
        all_items = [self._summary(x, context) for x in all_recipes]
        items = list(all_items)
        q = self._norm(query.get("q"))
        if q:
            raw_by_id = {str(x.get("id")): x for x in all_recipes}
            items = [
                x for x in items
                if any(q in self._norm(x.get(k)) for k in ("id", "nombre", "codigo", "categoria"))
                or any(
                    q in self._norm(alias)
                    for field in ("alias", "aliases", "variantes", "nombres_alternativos")
                    for alias in (
                        raw_by_id.get(x["id"], {}).get(field)
                        if isinstance(raw_by_id.get(x["id"], {}).get(field), list)
                        else [raw_by_id.get(x["id"], {}).get(field)]
                    )
                    if alias
                )
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
        all_recipes = self._all_recipes(incluir_archivadas=True)
        receta = next(
            (
                item
                for item in all_recipes
                if identity in {self._norm(item.get("id")), self._norm(item.get("codigo"))}
            ),
            None,
        )
        if not receta:
            return self._error("elaboration_not_found", "Elaboración no encontrada.", 404)
        esc = self._escandallo_for(receta)
        ingredients = self._ingredients(receta, esc)
        context = self._cost_context(all_recipes)
        public_escandallo = self._costing(receta, esc, ingredients, context=context)
        documents = self._documents(receta)
        production = self._production(receta)
        menus = self._menus_for_recipe(receta)
        events = list(receta.get("eventos_utilizacion") or [])
        pending = self._pending_fields(receta, public_escandallo)
        technical = self._technical_sheet(
            receta, ingredients, public_escandallo, documents, production, pending,
        )
        theoretical_yield = self.calculador_rendimiento_teorico.calcular(
            ingredients,
            rendimiento=(None if self._yield_pending(receta) else self._first_present(
                receta.get("rendimiento"), receta.get("numero_raciones"),
            )),
            unidad_rendimiento=str(receta.get("unidad_rendimiento") or ""),
        )
        technical["rendimiento_fisico_teorico"] = theoretical_yield
        summary = self._summary(receta, context)
        if public_escandallo:
            summary["coste_total"] = public_escandallo.get("coste_total")
            summary["coste_por_racion"] = public_escandallo.get("coste_por_racion")
        canonical_ingredient_names = {
            self._norm(item.get("nombre_original"))
            for item in ingredients
            if isinstance(item, dict) and item.get("nombre_original")
        }
        proposed_ingredients_raw = self._first_present(
            receta.get("ingredientes_propuestos_ia"),
            receta.get("ingredientes_propuestos"),
            receta.get("ingredientes_sugeridos_ia"),
        )
        proposed_ingredients = self._list_or_none(proposed_ingredients_raw) or []
        ingredientes_propuestos_no_registrados = []
        for item in proposed_ingredients:
            if isinstance(item, dict):
                nombre = str(item.get("nombre") or item.get("ingrediente") or "").strip()
            else:
                nombre = str(item or "").strip()
            if not nombre:
                continue
            if self._norm(nombre) in canonical_ingredient_names:
                continue
            ingredientes_propuestos_no_registrados.append(nombre)
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
                "estado_rendimiento": summary.get("estado_rendimiento"),
                "origen_rendimiento": summary.get("origen_rendimiento"),
                "rendimiento_neto": summary.get("rendimiento_neto"),
                "rendimiento_fisico_teorico": theoretical_yield,
                "raciones": summary.get("raciones"),
            },
            "escandallo": public_escandallo,
            "ficha_tecnica": technical,
            "alergenos": self._list_or_none(receta.get("alergenos")),
            "conservacion": receta.get("conservacion") or None,
            "regeneracion": receta.get("regeneracion") or None,
            "procedencia_campos": self._public_value(dict(receta.get("procedencia_campos") or {})),
            "historial_procedencia": self._public_value(list(receta.get("historial_procedencia") or [])),
            "propuestas_ia": {
                "procedimiento": self._public_text(self._first_present(
                    receta.get("propuesta_procedimiento_ia"),
                    receta.get("procedimiento_propuesto"),
                    receta.get("procedimiento_sugerido_ia"),
                )) or None,
                "ingredientes": self._public_value(proposed_ingredients) if proposed_ingredients else None,
                "ingredientes_no_registrados": self._public_value(ingredientes_propuestos_no_registrados) or None,
                "alergenos_posibles": self._public_value(self._list_or_none(self._first_present(
                    receta.get("alergenos_posibles"),
                    receta.get("posibles_alergenos"),
                    receta.get("alergenos_inferidos"),
                ))),
                "conservacion": self._public_text(self._first_present(
                    receta.get("conservacion_propuesta_ia"),
                    receta.get("propuesta_conservacion_ia"),
                )) or None,
                "temperaturas": self._public_value(self._list_or_none(self._first_present(
                    receta.get("temperaturas_sugeridas_ia"),
                    receta.get("temperaturas_propuestas"),
                ))),
                "tiempos": self._public_value(self._first_present(
                    receta.get("tiempos_estimados_ia"),
                    receta.get("tiempos_propuestos"),
                )),
                "observaciones": self._public_text(self._first_present(
                    receta.get("observaciones_propuestas_ia"),
                    receta.get("observaciones_sugeridas_ia"),
                )) or None,
                "persistida": False,
            },
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

    def proyectar_provisional(
        self, elaboracion_id: str, *, propuestas: dict[str, Any],
        metadatos_propuestas: dict[str, dict[str, Any]] | None = None,
        completitud: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Proyecta ficha y escandallo con propuestas sin persistir el dominio."""
        identity = self._norm(elaboracion_id)
        all_recipes = self._all_recipes(incluir_archivadas=True)
        current = next((
            item for item in all_recipes
            if identity in {self._norm(item.get("id")), self._norm(item.get("codigo"))}
        ), None)
        if not current:
            return self._error("elaboration_not_found", "Elaboración no encontrada.", 404)
        recipe = deepcopy(current)
        selected = deepcopy(dict(propuestas or {}))
        metadata = deepcopy(dict(metadatos_propuestas or {}))
        operational_states = deepcopy(dict(recipe.get("estados_campos_operativos") or {}))
        for field, value in selected.items():
            if _is_no_aplica(value):
                operational_states[field] = {
                    **dict(metadata.get(field) or {}),
                    "estado": "NO_APLICA", "confirmado": False,
                    "estado_revision": "REQUIERE_REVISION_HUMANA",
                }
            else:
                recipe[field] = value
        if operational_states:
            recipe["estados_campos_operativos"] = operational_states
        if isinstance(selected.get("ingredientes_estructurados"), list):
            recipe["_ingredientes_estructurados"] = deepcopy(
                selected["ingredientes_estructurados"]
            )
        if any(field in selected for field in {"rendimiento", "numero_raciones", "unidad_rendimiento"}):
            recipe["campos_pendientes_importacion"] = [
                field for field in list(recipe.get("campos_pendientes_importacion") or [])
                if str(field or "").strip().casefold() != "rendimiento"
            ]
            recipe["estado_rendimiento"] = "PROPUESTO"
            recipe["origen_rendimiento"] = deepcopy(
                metadata.get("rendimiento") or metadata.get("numero_raciones")
                or metadata.get("unidad_rendimiento") or {"origen": "IA_PROPUESTA"}
            )
        field_origins = deepcopy(dict(recipe.get("procedencia_campos") or {}))
        for field, value in metadata.items():
            field_origins[field] = {
                **dict(value or {}),
                "tipo": str((value or {}).get("origen") or "IA_PROPUESTA"),
                "estado_revision": "REQUIERE_REVISION_HUMANA",
                "persistido": False,
            }
        recipe["procedencia_campos"] = field_origins
        esc = self._escandallo_for(current)
        if esc is None and list(recipe.get("ingredientes") or []):
            esc = {
                "id": f"PREVIEW-{recipe.get('id') or recipe.get('codigo')}",
                "estado": "PROVISIONAL", "lineas": [], "otros_costes": 0,
            }
        ingredients = self._ingredients(recipe, esc)
        costing = self._costing(
            recipe, esc, ingredients, context=self._cost_context([
                recipe if item is current else item for item in all_recipes
            ]),
        ) if esc else None
        pending = self._pending_fields(recipe, costing)
        production = self._production(recipe)
        technical = self._technical_sheet(
            recipe, ingredients, costing, self._documents(recipe), production, pending,
        )
        technical.update({
            "estado": "PROVISIONAL",
            "origen": "proyeccion_propuestas",
            "persistida": False,
            "procedencias_provisionales": field_origins,
            "campos_criticos_pendientes_revision": [
                field for field, value in metadata.items()
                if str((value or {}).get("estado_revision") or "").upper()
                == "REQUIERE_REVISION_HUMANA"
            ],
        })
        if costing:
            costing["estado_coste"] = (
                "PROVISIONAL" if costing.get("coste_total") is not None
                else costing.get("estado_coste")
            )
            costing["coste_provisional"] = costing.get("coste_total") is not None
            costing["motivos_provisionalidad"] = [
                {
                    "campo": field,
                    "origen": (metadata.get(field) or {}).get("origen") or "IA_PROPUESTA",
                }
                for field in selected
                if field in {"ingredientes_estructurados", "rendimiento", "numero_raciones", "unidad_rendimiento"}
            ]
        return {
            "ok": True,
            "estado": "PROVISIONAL",
            "recipe_id": str(recipe.get("id") or recipe.get("codigo") or elaboracion_id),
            "nombre": self._public_text(recipe.get("nombre")),
            "propuestas_aplicadas_solo_lectura": sorted(selected),
            "completitud": deepcopy(completitud or {}),
            "escandallo": costing,
            "ficha_tecnica": technical,
            "datos_reales_modificados": False,
        }

    def _menus_for_recipe(self, recipe: dict[str, Any]) -> list[dict[str, Any]]:
        """Deriva relaciones desde el repositorio MENU601 sin duplicarlas en REC601."""
        from SERVICIOS.biblioteca_menus_601 import RepositorioBibliotecaMenus601

        identities = {
            self._norm(recipe.get("id")), self._norm(recipe.get("codigo")),
        } - {""}
        output: list[dict[str, Any]] = []
        for menu in RepositorioBibliotecaMenus601(self.recetas.base_dir).listar(incluir_archivados=True):
            matched_references = [
                deepcopy(reference)
                for references in dict(menu.get("composicion") or {}).values()
                for reference in list(references or [])
                if isinstance(reference, dict)
                and str(reference.get("tipo_referencia") or "").upper() == "RECETA"
                and self._norm(reference.get("referencia")) in identities
            ]
            used = bool(matched_references)
            if used:
                output.append({
                    "menu_id": str(menu.get("menu_id") or ""),
                    "nombre": str(menu.get("nombre") or ""),
                    "tipo": str(menu.get("tipo") or ""),
                    "estado": str(menu.get("estado_publicacion") or menu.get("estado") or ""),
                    "pax": self._number(
                        menu.get("comensales_recomendado") or menu.get("numero_comensales")
                        or menu.get("pax")
                    ),
                    "referencias_receta": matched_references,
                })
        return output

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
        if self._yield_pending(receta):
            declared.append("Rendimiento")
        checks = (
            ("Descripción", receta.get("descripcion")),
            ("Procedimiento", receta.get("elaboracion")),
            ("Tiempo total", receta.get("tiempo_total") or receta.get("tiempo_elaboracion")),
            ("Conservación", receta.get("conservacion")),
            ("Alérgenos", receta.get("alergenos") if "alergenos" in receta else None),
            ("Coste por ración", (escandallo or {}).get("coste_por_racion")),
        )
        pending = [self._public_text(item) for item in declared]
        states = dict(receta.get("estados_campos_operativos") or {})
        labels_to_fields = {
            "Tiempo de descongelaciÃ³n": "tiempo_descongelacion",
            "Vida Ãºtil congelada": "vida_util_congelado",
            "Tiempo de regeneraciÃ³n": "regeneracion",
        }
        pending = [
            label for label in pending
            if str(((states.get(labels_to_fields.get(label, "")) or {}).get("estado") or "")).upper()
            != "NO_APLICA"
        ]
        for label, value in checks:
            if label == "Alérgenos" and "alergenos" in receta and isinstance(value, list):
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
                "preparacion": receta.get("tiempo_preparacion") or None,
                "activo": receta.get("tiempo_activo") or None,
                "pasivo": receta.get("tiempo_pasivo") or None,
                "coccion_proceso": receta.get("tiempo_coccion") or None,
                "reposo": receta.get("tiempo_reposo") or None,
                "enfriamiento": receta.get("tiempo_enfriamiento") or None,
                "total": receta.get("tiempo_total") or receta.get("tiempo_elaboracion") or None,
            },
            "temperaturas": self._public_value(list(receta.get("temperaturas") or [])),
            "rendimiento": None if self._yield_pending(receta) else self._number(receta.get("rendimiento") or receta.get("numero_raciones")),
            "unidad_rendimiento": None if self._yield_pending(receta) else receta.get("unidad_rendimiento") or None,
            "estado_rendimiento": receta.get("estado_rendimiento") or None,
            "origen_rendimiento": self._public_value(receta.get("origen_rendimiento")),
            "rendimiento_neto": self._public_value(receta.get("rendimiento_neto")),
            "raciones": None if self._yield_pending(receta) else self._number(receta.get("numero_raciones")),
            "escandallo": escandallo,
            "alergenos": self._list_or_none(receta.get("alergenos")),
            "conservacion": receta.get("conservacion") or None,
            "caducidad": receta.get("caducidad") or receta.get("vida_util_refrigerado") or None,
            "regeneracion": receta.get("regeneracion") or None,
            "presentacion": receta.get("presentacion") or None,
            "utensilios": list(receta.get("utensilios") or []),
            "produccion": production,
            "tanda": {
                "produccion_maxima": receta.get("produccion_maxima") or None,
                "unidad": receta.get("unidad_tanda") or None,
                "rendimiento": receta.get("rendimiento_por_tanda") or None,
                "limitacion": receta.get("limitacion_tanda") or None,
            },
            "documentos": documents,
            "procedencia_campos": self._public_value(dict(receta.get("procedencia_campos") or {})),
            "historial_procedencia": self._public_value(list(receta.get("historial_procedencia") or [])),
            "estados_campos_operativos": self._public_value(dict(receta.get("estados_campos_operativos") or {})),
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
        structured = list(
            receta.get("_ingredientes_estructurados")
            or receta.get("ingredientes_estructurados") or []
        )
        output = []
        names = list(receta.get("ingredientes") or [])
        amounts = list(receta.get("cantidades") or [])
        for index, name in enumerate(names):
            source = structured[index] if index < len(structured) and isinstance(structured[index], dict) else {}
            line = esc_lines[index] if index < len(esc_lines) and isinstance(esc_lines[index], dict) else {}
            metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
            component_type = str(
                metadata.get("tipo") or source.get("tipo_componente") or source.get("tipo") or "ARTICULO"
            ).strip().upper()
            reference = str(
                metadata.get("referencia_elaboracion")
                or source.get("referencia_elaboracion")
                or ""
            ).strip() or None
            explicit_child_id = str(
                source.get("receta_id")
                or source.get("elaboracion_id")
                or source.get("receta_referenciada_id")
                or ""
            ).strip() or None
            child = (
                self.motor_explosion.resolver_receta_referenciada(source)
                if component_type == "ELABORACION"
                else None
            )
            source_code = str(
                source.get("article_id") or source.get("articulo_id")
                or source.get("codigo") or ""
            ).strip()
            direct = by_code.get(self._norm(source_code)) if source_code else None
            matches = [direct] if direct else by_name.get(self._norm(name), [])
            linked = matches[0] if len(matches) == 1 else None
            linked_article = linked if component_type == "ARTICULO" else None
            output.append({
                "tipo_componente": component_type,
                "articulo_id": (
                    str(linked_article.get("codigo")) if linked_article else None
                ),
                "escandallo_hijo_id": child.get("receta_id") if child else explicit_child_id,
                "referencia_elaboracion": reference,
                "codigo": str(linked_article.get("codigo")) if linked_article else None,
                "nombre_articulo": self._public_text(linked_article.get("nombre")) if linked_article else None,
                "unidad_base": linked_article.get("unidad_base") or linked_article.get("unidad") or None if linked_article else None,
                "unidad_compra": linked_article.get("unidad_compra") or None if linked_article else None,
                "cantidad_formato": linked_article.get("cantidad_formato") or None if linked_article else None,
                "unidad_formato": linked_article.get("unidad_formato") or None if linked_article else None,
                "proveedor": linked_article.get("proveedor") or None if linked_article else None,
                "precio_catalogo": self._number(linked_article.get("precio")) if linked_article else None,
                "conversion_unidades": linked_article.get("conversion_unidades") or [] if linked_article else [],
                "nombre_original": self._public_text(name),
                "cantidad_texto": str(
                    source.get("cantidad_texto")
                    or source.get("cantidad_original")
                    or (amounts[index] if index < len(amounts) else "")
                ) or None,
                "cantidad_original": self._number(
                    source.get("cantidad_original") or source.get("cantidad")
                    or source.get("quantity")
                ),
                "unidad_original": source.get("unidad") or source.get("unit") or None,
                "cantidad": self._number(
                    source.get("cantidad_normalizada") or source.get("cantidad")
                    or source.get("quantity") or line.get("cantidad_neta") or line.get("cantidad")
                ),
                "ambito_cantidad": "LOTE_COMPLETO",
                "unidad": (
                    source.get("unidad_normalizada") or source.get("unidad") or source.get("unit")
                    or line.get("unidad_normalizada") or line.get("unidad") or None
                ),
                "cantidad_normalizada": self._number(
                    source.get("cantidad_normalizada") or source.get("cantidad_neta")
                    or line.get("cantidad_neta")
                ),
                "unidad_normalizada": (
                    source.get("unidad_normalizada") or line.get("unidad_normalizada") or None
                ),
                "merma": self._number(
                    source.get("merma") or source.get("merma_porcentaje")
                    or line.get("merma_porcentaje") or line.get("merma_pct")
                ),
                "cantidad_neta": self._number(
                    source.get("cantidad_normalizada") or source.get("cantidad_neta")
                    or line.get("cantidad_neta")
                ),
                "coste_unitario": self._number(line.get("precio_unitario") or line.get("coste_unitario")),
                "coste_linea": self._number(line.get("coste_linea") or line.get("coste_total")),
                "observaciones": line.get("observaciones") or None,
                "dato_provisional": bool(
                    source.get("dato_provisional")
                    or (
                        source.get("procedencia_propuesta")
                        and str((source.get("procedencia_propuesta") or {}).get("estado_revision") or "").upper()
                        != "CONFIRMADO"
                    )
                ),
                "procedencia_propuesta": self._public_value(
                    deepcopy(source.get("procedencia_propuesta"))
                ),
                "conversion_propuesta": self._public_value(
                    deepcopy(source.get("conversion"))
                ),
                "estado_relacion": (
                    "elaboracion_relacionada"
                    if component_type == "ELABORACION" and child
                    else "elaboracion_id_roto"
                    if component_type == "ELABORACION" and explicit_child_id and not child
                    else "elaboracion_sin_resolver"
                    if component_type == "ELABORACION"
                    else "relacionado"
                    if len(matches) == 1
                    else "coincidencia_dudosa"
                    if matches
                    else "sin_relacionar"
                ),
            })
        return output

    def _costing(
        self,
        receta: dict[str, Any],
        esc: dict[str, Any] | None,
        ingredients: list[dict[str, Any]],
        *,
        context: dict[str, Any] | None = None,
        depth: int = 0,
    ) -> dict[str, Any] | None:
        if not esc:
            return None
        context = context or self._cost_context(self._all_recipes(incluir_archivadas=True))
        identity = self._recipe_identity(receta)
        memo_key = (identity, depth)
        if memo_key in context["memo"]:
            return deepcopy(context["memo"][memo_key])
        if identity in context["stack"]:
            return self._recursive_cost_error("CICLO_DETECTADO")
        if depth > context["max_depth"]:
            return self._recursive_cost_error("PROFUNDIDAD_EXCEDIDA")
        context["stack"].append(identity)
        try:
            result = self._costing_inner(receta, esc, ingredients, context, depth)
            context["memo"][memo_key] = deepcopy(result)
            return result
        finally:
            context["stack"].pop()

    def _costing_inner(
        self,
        receta: dict[str, Any],
        esc: dict[str, Any],
        ingredients: list[dict[str, Any]],
        context: dict[str, Any],
        depth: int,
    ) -> dict[str, Any]:
        public_prices = self._article_prices(ingredients)
        calculation = self.motor_escandallos.calcular(
            nombre_escandallo=str(receta.get("nombre") or "Escandallo"),
            numero_raciones=0.0 if self._yield_pending(receta) else float(
                receta.get("numero_raciones")
                or receta.get("rendimiento")
                or (esc or {}).get("numero_raciones")
                or (esc or {}).get("rendimiento_total")
                or 0
            ),
            lineas_entrada=[
                {
                    # El motor solo recibe una identidad cuando la relación pública
                    # ya es estable; nunca se le permite enlazar por parecido.
                    "producto_codigo": (
                        item.get("articulo_id")
                        if item.get("tipo_componente") == "ARTICULO"
                        and item.get("estado_relacion") == "relacionado"
                        else f"__SIN_RELACION_{index}"
                    ),
                    "nombre_mostrado": (
                        f"__SUBELABORACION_{index}"
                        if item.get("tipo_componente") == "ELABORACION"
                        else
                        item.get("nombre_original")
                        if item.get("estado_relacion") == "relacionado"
                        else ""
                    ),
                    "cantidad_neta": item.get("cantidad_neta") or item.get("cantidad"),
                    "cantidad_texto": item.get("cantidad_texto"),
                    "unidad_receta": item.get("unidad"),
                    "merma_especifica": item.get("merma"),
                    "dato_manual": False,
                }
                for index, item in enumerate(ingredients)
            ],
            precio_venta_por_racion=float((esc or {}).get("precio_venta_por_racion") or 0),
            receta_asociada={
                "id": str(receta.get("id") or ""),
                "codigo": str(receta.get("codigo") or ""),
                "nombre": str(receta.get("nombre") or ""),
            },
            precios_fijados=public_prices or None,
        )
        calculated_lines = list(calculation.get("lineas") or [])
        public_lines = []
        for index, item in enumerate(ingredients):
            calculated = calculated_lines[index] if index < len(calculated_lines) else {}
            if item.get("tipo_componente") == "ELABORACION":
                public_lines.append(
                    self._subelaboration_cost_line(receta, item, context, depth)
                )
            else:
                public_lines.append(self._cost_line(item, calculated))
        missing_price = sum(line.get("coste_linea") is None for line in public_lines)
        missing_conversion = sum(
            line.get("estado_coste") in {
                "CONVERSION_NO_DISPONIBLE", "UNIDADES_INCOMPATIBLES",
                "RENDIMIENTO_INSUFICIENTE",
            }
            for line in public_lines
        )
        complete = bool(public_lines) and not missing_price and not missing_conversion
        provisional_price_lines = [
            line for line in public_lines
            if line.get("coste_linea") is not None and line.get("precio_provisional") is True
        ]
        provisional_data_lines = [
            line for line in public_lines
            if line.get("coste_linea") is not None and line.get("dato_provisional") is True
        ]
        provisional_lines = list({
            index: line for index, line in enumerate(public_lines)
            if line in provisional_price_lines or line in provisional_data_lines
        }.values())
        real_price_lines = [
            line for line in public_lines
            if line.get("coste_linea") is not None
            and line.get("clasificacion_precio") == "REAL"
        ]
        confirmed_lines = [
            line for line in public_lines
            if line.get("coste_linea") is not None
            and line.get("clasificacion_precio") == "CONFIRMADO"
        ]
        partial_decimal = sum(
            (Decimal(str(line["coste_linea"])) for line in public_lines
             if line.get("coste_linea") is not None),
            Decimal("0"),
        )
        partial_total = round(float(partial_decimal), 6)
        rendimiento = None if self._yield_pending(receta) else self._number(
            receta.get("numero_raciones")
            or receta.get("rendimiento")
            or esc.get("numero_raciones")
            or esc.get("rendimiento_total")
        )
        total_lines = len(public_lines)
        priced_lines = total_lines - missing_price
        completion_percentage = round((priced_lines / total_lines) * 100, 2) if total_lines else 0.0
        total_with_overheads = round(
            partial_total + float(self._number(esc.get("otros_costes")) or 0), 6,
        )
        unit_cost = (
            round(total_with_overheads / float(rendimiento), 6)
            if complete and rendimiento and rendimiento > 0 else None
        )
        yield_unit = str(
            receta.get("unidad_rendimiento") or esc.get("unidad_rendimiento") or ""
        ).strip() or None
        normalized_yield_unit = self._norm(yield_unit)
        physical_unit_cost = unit_cost if normalized_yield_unit in {
            "kg", "kilogramo", "kilogramos", "l", "litro", "litros",
            "u", "ud", "uds", "unidad", "unidades",
        } else None
        cost_state = (
            "PROVISIONAL" if complete and provisional_lines
            else "DISPONIBLE" if complete
            else "PARCIAL" if partial_total
            else "SIN_COSTE"
        )
        return {
            "id": esc.get("id"),
            "estado": esc.get("estado"),
            "estado_coste": cost_state,
            "coste_provisional": bool(provisional_lines),
            "lineas_datos_propuestos": len(provisional_data_lines),
            "precios_reales": len(real_price_lines),
            "precios_confirmados": len(confirmed_lines),
            "precios_referencia": len(provisional_price_lines),
            "completitud_coste_porcentaje": completion_percentage,
            "lineas": public_lines,
            "coste_ingredientes": partial_total if complete else None,
            "coste_ingredientes_parcial": partial_total if not complete and partial_total else None,
            "otros_costes": self._number(esc.get("otros_costes")),
            "coste_total": (
                total_with_overheads
                if complete else None
            ),
            "coste_total_parcial": partial_total if not complete and partial_total else None,
            "rendimiento": rendimiento,
            "coste_por_racion": unit_cost,
            "coste_por_unidad_rendimiento": physical_unit_cost,
            "unidad_coste_rendimiento": yield_unit if physical_unit_cost is not None else None,
            "precio_objetivo": self._number(esc.get("precio_venta_por_racion")),
            "margen": self._number(esc.get("margen_porcentual") or esc.get("margen")),
            "fecha_calculo": calculation.get("fecha_calculo"),
            "desactualizado": str(esc.get("estado") or "").upper() == "DESACTUALIZADO",
            "ingredientes_sin_coste": missing_price,
            "ingredientes_sin_precio": [
                line.get("nombre_original") or line.get("articulo_nombre")
                for line in public_lines if line.get("estado_coste") == "SIN_PRECIO"
            ],
            "ingredientes_pendientes_coste": [
                line.get("nombre_original") or line.get("articulo_nombre")
                for line in public_lines if line.get("coste_linea") is None
            ],
            "ingredientes_sin_conversion": missing_conversion,
            "incidencias": [
                incidence
                for incidence in list(calculation.get("incidencias") or [])
                if incidence.get("tipo") not in {"PRECIO_VENTA_IGUAL_A_CERO", "RECETA_SIN_RACIONES"}
                and "__SUBELABORACION_" not in str(incidence.get("detalle") or "")
            ] + [
                {
                    "tipo": line.get("estado_coste"),
                    "detalle": line.get("motivo_sin_coste"),
                    "escandallo_hijo_id": line.get("escandallo_hijo_id"),
                }
                for line in public_lines
                if line.get("tipo_componente") == "ELABORACION"
                and line.get("coste_linea") is None
            ],
        }

    def _cost_context(self, recipes: list[dict[str, Any]]) -> dict[str, Any]:
        by_identity: dict[str, dict[str, Any]] = {}
        for recipe in recipes:
            for value in (recipe.get("id"), recipe.get("codigo"), recipe.get("nombre")):
                key = self._norm(value)
                if key:
                    by_identity[key] = recipe
        return {
            "recipes": by_identity,
            "memo": {},
            "stack": [],
            "max_depth": self.motor_explosion.MAX_PROFUNDIDAD,
        }

    def _recipe_identity(self, recipe: dict[str, Any]) -> str:
        return self._norm(recipe.get("codigo") or recipe.get("id") or recipe.get("nombre"))

    @staticmethod
    def _recursive_cost_error(state: str) -> dict[str, Any]:
        return {
            "estado_coste": "SIN_COSTE",
            "coste_total": None,
            "coste_total_parcial": None,
            "lineas": [],
            "ingredientes_sin_coste": 1,
            "ingredientes_sin_conversion": 0,
            "incidencias": [{"tipo": state, "detalle": state}],
            "_resolution_error": state,
        }

    @staticmethod
    def _recipe_entity(recipe: dict[str, Any]) -> Receta:
        return Receta(
            codigo=str(recipe.get("codigo") or recipe.get("id") or ""),
            nombre=str(recipe.get("nombre") or ""),
            rendimiento=float(recipe.get("rendimiento") or recipe.get("numero_raciones") or 0),
            unidad_rendimiento=str(recipe.get("unidad_rendimiento") or ""),
            rendimiento_neto=RendimientoNeto.desde_dict(recipe.get("rendimiento_neto")),
        )

    def _subelaboration_cost_line(
        self,
        parent: dict[str, Any],
        ingredient: dict[str, Any],
        context: dict[str, Any],
        depth: int,
    ) -> dict[str, Any]:
        output = self._cost_line(ingredient, {})
        child_id = str(ingredient.get("escandallo_hijo_id") or "").strip()
        child = context["recipes"].get(self._norm(child_id))
        cycle_path = list(context.get("stack") or [])
        if child_id:
            cycle_path.append(self._norm(child_id))
        if child is None:
            result = self.calculador_subelaboraciones.unresolved(
                "SUBELABORACION_NO_ENCONTRADA",
                "La subelaboracion referenciada no existe en el modelo canonico.",
                trace={
                    "ruta": cycle_path,
                    "escandallo_hijo_id": child_id or None,
                },
            )
        elif self._recipe_identity(child) in context["stack"]:
            result = self.calculador_subelaboraciones.unresolved(
                "CICLO_DETECTADO", "La relacion de subelaboraciones contiene un ciclo.",
                trace={
                    "ruta": cycle_path,
                    "escandallo_hijo_id": child_id,
                },
            )
        elif depth + 1 > context["max_depth"]:
            result = self.calculador_subelaboraciones.unresolved(
                "PROFUNDIDAD_EXCEDIDA", "Se alcanzo el limite seguro de profundidad.",
                trace={
                    "ruta": cycle_path,
                    "escandallo_hijo_id": child_id,
                },
            )
        else:
            child_esc = self._escandallo_for(child)
            child_cost = self._costing(
                child,
                child_esc,
                self._ingredients(child, child_esc),
                context=context,
                depth=depth + 1,
            )
            recursive_error = (child_cost or {}).get("_resolution_error")
            nested_states = {
                str(item.get("tipo") or "")
                for item in list((child_cost or {}).get("incidencias") or [])
                if isinstance(item, dict)
            }
            boundary_error = next(
                (state for state in ("CICLO_DETECTADO", "PROFUNDIDAD_EXCEDIDA")
                 if state in nested_states),
                None,
            )
            result = (
                self.calculador_subelaboraciones.unresolved(
                    recursive_error or boundary_error,
                    "No se pudo resolver la cadena de subelaboraciones.",
                    trace={
                        "ruta": cycle_path,
                        "escandallo_hijo_id": child_id,
                    },
                )
                if recursive_error or boundary_error
                else self.calculador_subelaboraciones.calcular(
                    parent_id=str(parent.get("codigo") or parent.get("id") or ""),
                    line_id=str(
                        ingredient.get("id")
                        or ingredient.get("referencia_elaboracion")
                        or ingredient.get("nombre_original")
                        or ""
                    ),
                    child_id=child_id,
                    required_quantity=self._number(
                        ingredient.get("cantidad_neta") or ingredient.get("cantidad")
                    ),
                    required_unit=str(ingredient.get("unidad") or ""),
                    child_recipe=self._recipe_entity(child),
                    child_costing=child_cost or {},
                    depth=depth + 1,
                )
            )
        output.update(result)
        output.update({
            "precio_aplicado": (
                result.get("trazabilidad_coste") or {}
            ).get("coste_total_hijo"),
            "precio_unitario": (
                result.get("trazabilidad_coste") or {}
            ).get("coste_total_hijo"),
            "coste_unitario": (
                result.get("trazabilidad_coste") or {}
            ).get("coste_total_hijo"),
            "origen_precio": "escandallo_hijo" if result.get("coste_linea") is not None else "no_disponible",
            "tipo_conversion": (
                ((result.get("trazabilidad_coste") or {}).get("conversion") or {}).get("procedencia")
                or "no_disponible"
            ),
            "factor_conversion": (
                result.get("trazabilidad_coste") or {}
            ).get("fraccion_lote"),
            "coste_con_merma": result.get("coste_linea"),
        })
        return output

    def _article_prices(
        self,
        ingredients: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Adapta el mismo contrato público que alimenta la ficha de Artículos."""
        prices: dict[str, dict[str, Any]] = {}
        for ingredient in ingredients:
            code = str(ingredient.get("articulo_id") or "")
            if not code or code in prices:
                continue
            response = self.catalogo_articulos.obtener(code)
            article = dict(response.get("articulo") or {}) if response.get("ok") else {}
            price = self._number(article.get("precio"))
            if price is None:
                continue
            product = self.articulos.obtener_producto(code) or {}
            normalized_price, normalized_unit, normalization_issues = (
                self.motor_escandallos.precio_catalogo_normalizado(product)
            )
            if normalized_price is None and normalization_issues:
                # Nunca degradar el precio de un paquete incompleto a precio
                # unitario: el motor volverá a evaluarlo y expondrá la incidencia.
                continue
            recipe_unit = ingredient.get("unidad") or ""
            original_unit = (
                article.get("unidad_compra")
                or article.get("unidad")
                or article.get("unidad_base")
                or ""
            )
            inherited_unit = not bool(original_unit)
            purchase_unit = str(article.get("unidad_compra") or "")
            format_quantity = self._number(article.get("cantidad_formato"))
            prices[code] = {
                "precio_neto_unidad_base": (
                    normalized_price if normalized_price is not None else price
                ),
                "unidad_base": (
                    normalized_unit
                    or article.get("unidad")
                    or article.get("unidad_base")
                    # Compatibilidad con el catálogo legado: el enriquecedor
                    # 5.5.5B usa la unidad de la línea cuando el enlace por
                    # código es exacto y el artículo no conserva unidad.
                    or recipe_unit
                    or ""
                ),
                "proveedor": article.get("proveedor") or "",
                "fecha": article.get("actualizado_en") or "",
                "provisional": False,
                "precio_incluye_iva": bool(article.get("precio_incluye_iva", False)),
                "fuente": "catalogo_articulos_publico",
                "precio_original": price,
                "unidad_precio_original": original_unit or None,
                "normalizacion": (
                    "heredada"
                    if inherited_unit
                    else "envase"
                    if (purchase_unit or article.get("unidad_formato"))
                    and format_quantity and normalized_price != price
                    else "ninguna"
                ),
            }
        return prices

    def _cost_line(
        self,
        ingredient: dict[str, Any],
        calculated: dict[str, Any],
    ) -> dict[str, Any]:
        output = dict(ingredient)
        if ingredient.get("tipo_componente") == "ELABORACION":
            output.update({
                "articulo_codigo": None,
                "articulo_nombre": None,
                "cantidad_receta": ingredient.get("cantidad"),
                "unidad_receta": ingredient.get("unidad"),
                "precio_original": None,
                "unidad_precio_original": None,
                "precio_aplicado": None,
                "unidad_precio_aplicado": None,
                "precio_unitario": None,
                "coste_unitario": None,
                "unidad_precio": None,
                "origen_precio": "no_disponible",
                "fecha_precio": None,
                "tipo_conversion": "no_aplica_subelaboracion",
                "factor_conversion": None,
                "cantidad_utilizada": ingredient.get("cantidad"),
                "cantidad_con_merma": None,
                "coste_linea": None,
                "coste_con_merma": None,
                "estado_coste": "COSTE_SUBELABORACION_NO_RESUELTO",
                "motivo_sin_coste": "El motor económico actual no calcula subelaboraciones recursivamente",
            })
            return output
        if ingredient.get("estado_relacion") != "relacionado":
            output.update({
                "articulo_codigo": ingredient.get("articulo_id"),
                "articulo_nombre": ingredient.get("nombre_articulo") or ingredient.get("nombre_original"),
                "cantidad_receta": ingredient.get("cantidad"),
                "unidad_receta": ingredient.get("unidad"),
                "precio_original": None,
                "unidad_precio_original": None,
                "precio_aplicado": None,
                "unidad_precio_aplicado": None,
                "precio_unitario": None,
                "coste_unitario": None,
                "unidad_precio": None,
                "origen_precio": "no_disponible",
                "fecha_precio": None,
                "tipo_conversion": "no_disponible",
                "factor_conversion": None,
                "cantidad_utilizada": ingredient.get("cantidad"),
                "cantidad_con_merma": None,
                "coste_linea": None,
                "coste_con_merma": None,
                "estado_coste": (
                    "RELACION_DUDOSA"
                    if ingredient.get("estado_relacion") == "coincidencia_dudosa"
                    else "ARTICULO_SIN_RELACIONAR"
                ),
                "motivo_sin_coste": (
                    "Relación dudosa"
                    if ingredient.get("estado_relacion") == "coincidencia_dudosa"
                    else "Artículo sin relacionar"
                ),
            })
            return output

        incidence_types = {
            normalize_incident_type(item.get("tipo"))
            for item in list(calculated.get("incidencias") or [])
        }
        price = self._number(calculated.get("precio_compra_utilizado"))
        factor = self._number(calculated.get("factor_conversion"))
        if "SIN_PRECIO" in incidence_types:
            state, reason = "SIN_PRECIO", "Sin precio vigente"
        elif "CONVERSION_NO_DISPONIBLE" in incidence_types:
            state, reason = "CONVERSION_NO_DISPONIBLE", "Conversión no disponible"
        elif price is None:
            state, reason = "SIN_PRECIO", "Sin precio vigente"
        else:
            state, reason = "DISPONIBLE", None
        reference = dict(calculated.get("precio_referencia") or {})
        price_unit = calculated.get("unidad_precio") or None
        recipe_unit = calculated.get("unidad_receta") or ingredient.get("unidad") or None
        normalization = str(reference.get("normalizacion") or "")
        if normalization == "heredada":
            conversion_type = "normalizacion_heredada"
        elif normalization == "envase":
            conversion_type = "envase"
        elif factor is None:
            conversion_type = "no_disponible"
        elif factor == 1:
            conversion_type = "directa"
        else:
            conversion_type = "metrica"
        origin = {
            "asociacion": "tarifa_proveedor",
            "historico": "historico_compras",
            "catalogo_producto": "catalogo_articulos",
            "catalogo_articulos_publico": "catalogo_articulos",
            "referencia_externa": "referencia_externa",
        }.get(str(reference.get("fuente") or ""), "no_disponible")
        source = str(reference.get("fuente") or "")
        provisional = bool(calculated.get("precio_provisional"))
        price_classification = (
            "REFERENCIA" if price is not None and provisional
            else "REAL" if price is not None and source == "historico"
            else "CONFIRMADO" if price is not None
            else "NO_DISPONIBLE"
        )
        output.update({
            "articulo_codigo": ingredient.get("articulo_id"),
            "articulo_nombre": ingredient.get("nombre_articulo") or ingredient.get("nombre_original"),
            "cantidad_receta": self._number(calculated.get("cantidad_neta")),
            "unidad_receta": recipe_unit,
            "precio_original": self._number(reference.get("precio_original")),
            "unidad_precio_original": reference.get("unidad_precio_original") or None,
            "precio_aplicado": price,
            "unidad_precio_aplicado": price_unit,
            "precio_unitario": price,
            "coste_unitario": price,
            "unidad_precio": price_unit,
            "origen_precio": origin if price is not None else "no_disponible",
            "clasificacion_precio": price_classification,
            "precio_provisional": provisional,
            "tienda_referencia": reference.get("tienda_referencia") or None,
            "referencia_precio": self._public_value(reference) if reference else None,
            "proveedor_precio": calculated.get("proveedor_precio") or None,
            "fecha_precio": calculated.get("fecha_precio") or None,
            "factor_conversion": factor,
            "tipo_conversion": conversion_type,
            "cantidad_utilizada": self._number(calculated.get("cantidad_neta")),
            "cantidad_con_merma": self._number(calculated.get("cantidad_bruta")),
            "coste_linea": (
                self._number(calculated.get("coste_linea"))
                if state == "DISPONIBLE" else None
            ),
            "coste_con_merma": (
                self._number(calculated.get("coste_linea"))
                if state == "DISPONIBLE" else None
            ),
            "estado_coste": state,
            "motivo_sin_coste": reason,
        })
        return output

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
