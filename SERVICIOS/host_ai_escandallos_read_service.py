from __future__ import annotations

import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService


class HostAIEscandallosReadService:
    """Adaptador conversacional READ sobre la Biblioteca culinaria canónica."""

    UNIDADES_RENDIMIENTO_DERIVABLES = {
        "u", "unidad", "unidades", "racion", "raciones", "pax", "persona", "personas",
    }

    def __init__(self, base_dir: Path, biblioteca: Any | None = None) -> None:
        self.biblioteca = biblioteca or BibliotecaCulinariaReadService(Path(base_dir))

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in text if not unicodedata.combining(char)).strip().lower()

    @staticmethod
    def _to_decimal(value: Any) -> Decimal | None:
        if value in (None, ""):
            return None
        text = str(value).strip().replace(" ", "")
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", ".")
        try:
            parsed = Decimal(text)
        except (InvalidOperation, ValueError):
            return None
        return parsed if parsed.is_finite() else None

    @staticmethod
    def _list_or_none(value: Any) -> list[Any] | None:
        if value in (None, ""):
            return None
        if isinstance(value, list):
            return list(value)
        return [value]

    def consultar(
        self, consulta: str = "buscar", *, termino: str = "", escandallo_id: str = "",
        limite: int = 10, agregacion: str = "", orden: str = "", posicion: int = 1,
        estado_coste: str = "", pagina: int = 1, escandallo_ids: list[str] | None = None, nombre_referencia: str = "",
    ) -> dict[str, Any]:
        mode = str(consulta or "buscar").strip().lower()
        aggregation = str(agregacion or "").strip().upper()
        identities = [str(value).strip() for value in list(escandallo_ids or []) if str(value).strip()]
        if identities:
            return self._detalle_lote(identities)
        if aggregation:
            if aggregation == "LIST_COSTE_INCOMPLETO":
                return dict(self.biblioteca.listar_costes_incompletos(
                    estado_coste=str(estado_coste or ""), pagina=int(pagina or 1),
                    limite=int(limite or 10),
                ) or {})
            if aggregation == "DETAIL_COSTE_INCOMPLETO":
                identity = str(escandallo_id or termino or "").strip()
                if not identity:
                    return self._result("REQUIERE_TERMINO", "detalle_coste", "")
                resolver = getattr(self.biblioteca, "resolver_receta_economica", None)
                if callable(resolver):
                    resolved = dict(resolver(identity) or {})
                    if resolved.get("estado") != "RESUELTO":
                        return {
                            "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO",
                            "estado": resolved.get("estado") or "NO_ENCONTRADO",
                            "total_coincidencias": int(resolved.get("total_coincidencias") or 0),
                            "candidatos": list(resolved.get("candidatos") or []),
                            "datos_reales_modificados": False,
                        }
                    identity = str(resolved.get("receta_id") or identity)
                return dict(self.biblioteca.detalle_coste_incompleto(identity) or {})
            if aggregation == "RANK_COSTE_POR_RACION":
                return dict(self.biblioteca.agregar_costes(
                    aggregation, orden=str(orden or ""), posicion=int(posicion or 0),
                ) or {})
            return dict(self.biblioteca.agregar_costes(aggregation) or {})
        size = max(1, min(int(limite or 10), 10))
        term = str(termino or "").strip()
        identity = str(escandallo_id or "").strip()
        if mode == "detalle":
            result = self._detalle(identity=identity, term=term, limit=size)
            fallback = str(nombre_referencia or "").strip()
            if identity and fallback and result.get("estado") == "NO_ENCONTRADO":
                resolved = self._detalle(identity="", term=fallback, limit=size)
                resolved["referencia_original"] = identity
                resolved["metodo_resolucion"] = "NOMBRE_REFERENCIA"
                return resolved
            return result
        # La capability consulta elaboraciones canónicas y su información de
        # receta/escandallo. Una elaboración SIN_ESCANDALLO debe seguir siendo
        # localizable para poder abrir su ficha culinaria.
        query = {"page": 1, "page_size": size}
        if mode == "buscar" and term:
            query["q"] = term
        response = dict(self.biblioteca.listar(query) or {})
        collection = dict(response.get("elaboraciones") or {})
        items = [self._summary(dict(item)) for item in list(collection.get("items") or [])[:size]]
        state = "OK" if items else "NO_ENCONTRADO" if term else "VACIO"
        return self._result(state, mode, term, items=items, total=int(collection.get("total") or len(items)))

    def _detalle_lote(self, identities: list[str]) -> dict[str, Any]:
        """Recupera hasta 50 detalles en una sola capability conversacional.

        Cada detalle sigue delegándose en la biblioteca canónica; el lote solo evita
        que el agente tenga que consumir una tool call por receta.
        """
        requested = list(dict.fromkeys(identities))[:50]
        details: list[dict[str, Any]] = []
        missing: list[str] = []
        ambiguous: dict[str, list[dict[str, Any]]] = {}
        for identity in requested:
            result = self._detalle(identity=identity, term="", limit=10)
            state = str(result.get("estado") or "NO_ENCONTRADO")
            if state == "OK" and isinstance(result.get("escandallo"), dict):
                details.append(dict(result["escandallo"]))
            elif state == "AMBIGUO":
                ambiguous[identity] = list(result.get("escandallos") or [])
            else:
                missing.append(identity)
        return {
            "estado": "OK" if len(details) == len(requested) else "PARCIAL",
            "consulta": "detalle_lote",
            "escandallos": [self._summary(item) for item in details],
            "elaboraciones": [self._summary(item) for item in details],
            "detalles": details,
            "total_solicitados": len(requested),
            "total_encontrados": len(details),
            "no_encontrados": missing,
            "ambiguos": ambiguous,
            "batch_size": len(requested),
            "resultados_parciales": bool(missing or ambiguous),
            "fuente": "biblioteca_culinaria_canonica",
            "solo_lectura": True,
            "datos_reales_modificados": False,
        }

    def _detalle(self, *, identity: str, term: str, limit: int) -> dict[str, Any]:
        selected_id = identity
        candidates: list[dict[str, Any]] = []
        if not selected_id:
            if not term:
                return self._result("REQUIERE_TERMINO", "detalle", "")
            listed = dict(self.biblioteca.listar({
                "q": term, "page": 1, "page_size": limit,
            }) or {})
            raw_items = list((listed.get("elaboraciones") or {}).get("items") or [])[:limit]
            candidates = [self._summary(dict(item)) for item in raw_items]
            exact = [
                item for item in candidates
                if self._norm(term) in {self._norm(item.get("id")), self._norm(item.get("codigo")), self._norm(item.get("nombre"))}
            ]
            if len(exact) == 1:
                selected_id = str(exact[0].get("id") or exact[0].get("codigo") or "")
            elif len(candidates) == 1:
                selected_id = str(candidates[0].get("id") or candidates[0].get("codigo") or "")
            elif candidates:
                return self._result("AMBIGUO", "detalle", term, items=candidates, total=len(candidates))
            else:
                return self._result("NO_ENCONTRADO", "detalle", term)

        response = dict(self.biblioteca.detalle(selected_id) or {})
        if response.get("ok") is False or not isinstance(response.get("elaboracion"), dict):
            return self._result("NO_ENCONTRADO", "detalle", term or identity)
        detail = self._detail_dto(dict(response["elaboracion"]))
        return self._result("OK", "detalle", term, items=[self._summary(detail)], total=1, detail=detail)

    @staticmethod
    def _summary(item: dict[str, Any]) -> dict[str, Any]:
        return {
            key: item.get(key) for key in (
                "id", "codigo", "nombre", "estado", "rendimiento", "unidad_rendimiento",
                "estado_rendimiento", "origen_rendimiento", "rendimiento_neto",
                "raciones", "coste_total", "coste_por_racion", "estado_coste",
                "coste_completo", "motivo_coste_no_disponible", "fecha_calculo",
                "tiene_receta", "tiene_escandallo",
            )
        }

    @classmethod
    def _detail_dto(cls, detail: dict[str, Any]) -> dict[str, Any]:
        recipe = dict(detail.get("receta") or {})
        costing = dict(detail.get("escandallo") or {})
        proposals = dict(detail.get("propuestas_ia") or {})
        rendimiento = recipe.get("rendimiento")
        rendimiento_dec = cls._to_decimal(rendimiento)
        unidad_rendimiento = str(recipe.get("unidad_rendimiento") or "")
        unidad_rendimiento_norm = cls._norm(unidad_rendimiento)
        rendimiento_valido = (
            rendimiento_dec is not None
            and rendimiento_dec > 0
            and unidad_rendimiento_norm in cls.UNIDADES_RENDIMIENTO_DERIVABLES
        )
        raw_ingredients = list(recipe.get("ingredientes") or [])
        cost_lines = list(costing.get("lineas") or [])
        ingredients = []
        for index, item in enumerate(raw_ingredients[:10]):
            line = dict(item or {})
            if index < len(cost_lines) and isinstance(cost_lines[index], dict):
                line.update(cost_lines[index])
            ingredient = {
                key: line.get(key) for key in (
                    "tipo_componente", "articulo_id", "escandallo_hijo_id",
                    "referencia_elaboracion", "codigo", "nombre_articulo", "nombre_original", "cantidad",
                    "cantidad_texto", "unidad", "unidad_base", "merma", "cantidad_neta",
                    "coste_unitario", "coste_linea", "estado_relacion", "estado_coste",
                    "motivo_sin_coste", "trazabilidad_coste",
                )
            }
            cantidad_dec = cls._to_decimal(line.get("cantidad"))
            cantidad_valida = cantidad_dec is not None and cantidad_dec >= 0
            ingredient["ambito_cantidad"] = "LOTE_COMPLETO"
            derivada = (
                (cantidad_dec / rendimiento_dec)
                if cantidad_valida and rendimiento_valido and cantidad_dec is not None and rendimiento_dec is not None
                else None
            )
            unidad_numerador = str(line.get("unidad") or "").strip()
            unidad_derivada = f"{unidad_numerador}/{unidad_rendimiento}" if derivada is not None and unidad_numerador else None
            presentacion = None
            if derivada is not None and unidad_derivada:
                unidad_n = cls._norm(unidad_numerador)
                if unidad_n == "kg":
                    presentacion = {"cantidad": float(derivada * Decimal("1000")), "unidad": f"g/{unidad_rendimiento}"}
                elif unidad_n == "l":
                    presentacion = {"cantidad": float(derivada * Decimal("1000")), "unidad": f"ml/{unidad_rendimiento}"}
            ingredient["cantidad_por_unidad_rendimiento"] = (
                float(derivada)
                if derivada is not None else None
            )
            ingredient["unidad_cantidad_por_rendimiento"] = unidad_derivada
            ingredient["cantidad_por_unidad_rendimiento_presentacion"] = presentacion
            ingredients.append(ingredient)
        return {
            **cls._summary(detail),
            "descripcion": detail.get("descripcion"),
            "procedimiento": recipe.get("procedimiento"),
            "estado_procedimiento": "CONFIRMADO" if recipe.get("procedimiento") else "PENDIENTE",
            "procedimiento_propuesto_ia": proposals.get("procedimiento"),
            "pasos": cls._list_or_none(recipe.get("pasos")) or [],
            "observaciones": recipe.get("observaciones"),
            "tiempo_total": recipe.get("tiempo_total"),
            "tiempo_activo": recipe.get("tiempo_activo"),
            "tiempo_pasivo": recipe.get("tiempo_pasivo"),
            "temperaturas": cls._list_or_none(recipe.get("temperaturas")),
            "tecnicas": cls._list_or_none(recipe.get("tecnicas")),
            "temperaturas_propuestas_ia": cls._list_or_none(proposals.get("temperaturas")),
            "tiempos_estimados_ia": proposals.get("tiempos"),
            "conservacion": detail.get("conservacion"),
            "conservacion_propuesta_ia": proposals.get("conservacion"),
            "alergenos": cls._list_or_none(detail.get("alergenos")),
            "alergenos_posibles": cls._list_or_none(proposals.get("alergenos_posibles")),
            "ingredientes_propuestos_ia": cls._list_or_none(proposals.get("ingredientes")),
            "ingredientes_propuestos_no_registrados": cls._list_or_none(proposals.get("ingredientes_no_registrados")),
            "observaciones_propuestas_ia": proposals.get("observaciones"),
            "ingredientes": ingredients,
            "semantica_cantidades": {
                "cantidad_ingrediente": "LOTE_COMPLETO",
                "rendimiento": rendimiento,
                "unidad_rendimiento": unidad_rendimiento,
                "cantidad_por_unidad_rendimiento": "DERIVADA_SOLO_SI_RENDIMIENTO_VALIDO",
            },
            "total_ingredientes": len(raw_ingredients),
            "ingredientes_limitados": len(raw_ingredients) > len(ingredients),
            "costes": {
                key: costing.get(key) for key in (
                    "estado_coste", "coste_ingredientes", "coste_ingredientes_parcial",
                    "otros_costes", "coste_total", "coste_total_parcial", "rendimiento",
                    "coste_por_racion", "precio_objetivo", "margen", "fecha_calculo",
                    "desactualizado", "ingredientes_sin_coste", "ingredientes_sin_conversion",
                    "incidencias",
                )
            } if costing else None,
            "moneda": None,
            "pendientes": list(detail.get("pendientes") or [])[:10],
        }

    @staticmethod
    def _result(
        state: str, mode: str, term: str, *, items: list[dict[str, Any]] | None = None,
        total: int = 0, detail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = {
            "estado": state,
            "consulta": mode,
            "termino": term,
            "total_encontrados": int(total),
            "escandallos": list(items or [])[:10],
            "escandallo": detail,
            "fuente": "biblioteca_culinaria_canonica",
            "semantica_costes": "calculo_canonico_actual",
            "solo_lectura": True,
            "datos_reales_modificados": False,
        }
        # Alias neutrales para consumidores nuevos. Se conservan las claves
        # históricas `escandallo(s)` para no romper contratos existentes.
        result["elaboraciones"] = result["escandallos"]
        result["elaboracion"] = result["escandallo"]
        return result


__all__ = ["HostAIEscandallosReadService"]
