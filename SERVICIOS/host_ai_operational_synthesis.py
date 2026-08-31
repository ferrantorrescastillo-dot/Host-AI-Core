from __future__ import annotations

from collections import defaultdict
from typing import Any

from SERVICIOS.articulo_economico_canonico import convert_quantity, normalize_unit


MISSING_RECIPE_OPTIONS = [
    "Buscar en mi biblioteca", "Proponer una receta con IA", "Crear la receta conmigo",
    "Vincular una receta existente", "Dejarla pendiente",
]


class HostAIOperationalSynthesis:
    """Sintesis pura de evidencias READ; no consulta ni modifica autoridades."""

    CONFIRMED_ORDER_STATES = {"confirmado", "confirmada", "preparado", "enviado", "parcialmente_recibido"}
    DRAFT_ORDER_STATES = {"borrador", "draft", "propuesta"}

    @classmethod
    def summarize(cls, evidence: list[dict[str, Any]]) -> dict[str, Any]:
        needs = cls._needs(evidence)
        ingredient_states = cls.ingredient_states(evidence)
        if not needs and not ingredient_states:
            return {}
        if not needs:
            return cls._state_summary(ingredient_states)
        stock, (confirmed, drafts) = cls._stock(evidence), cls._orders(evidence)
        purchases, incidents, covered = [], [], 0
        for need in needs:
            article_id = str(need.get("articulo_id") or "").strip()
            unit = str(need.get("unidad") or need.get("unidad_necesaria") or "").strip()
            required = cls._number(need.get("cantidad_necesaria", need.get("cantidad")))
            if not article_id or required is None:
                incidents.append({"articulo_id": article_id, "reason": "NEED_NOT_COMPARABLE"}); continue
            canonical_net = cls._number(need.get("necesidad_neta"))
            if canonical_net is not None:
                canonical_state = str(need.get("estado_operativo") or "").strip().upper()
                if canonical_state and canonical_state != "COMPRAR":
                    continue
                if canonical_net <= 0:
                    covered += 1; continue
                purchases.append({
                    "articulo_id": article_id,
                    "nombre": need.get("articulo_nombre") or need.get("nombre") or article_id,
                    "necesidad": required,
                    "stock_utilizable": cls._number(need.get("stock_disponible")),
                    "compra_confirmada_pendiente": cls._number(need.get("compras_confirmadas_pendientes")) or 0.0,
                    "necesidad_neta": canonical_net, "unidad": unit,
                    "formato_compra": need.get("formato_compra"),
                    "proveedor": need.get("proveedor_preferente"),
                    "precio_unitario": need.get("precio_unitario", need.get("precio_estimado")),
                    "unidad_precio": need.get("unidad_precio"),
                    "coste_neto": need.get("coste_neto"),
                })
                continue
            available = stock.get((article_id, unit)); incoming = confirmed.get((article_id, unit), 0.0)
            if available is None:
                incidents.append({"articulo_id": article_id, "reason": "STOCK_NOT_COMPARABLE", "unidad": unit}); continue
            net = max(required - available - incoming, 0.0)
            if net <= 0:
                covered += 1; continue
            purchases.append({"articulo_id": article_id, "nombre": need.get("nombre") or need.get("articulo_nombre") or article_id,
                              "necesidad": required, "stock_utilizable": available,
                              "compra_confirmada_pendiente": incoming, "necesidad_neta": round(net, 6), "unidad": unit})
        purchase_groups = cls._purchase_groups(purchases, evidence)
        return {"source": "DETERMINISTIC_READ_SYNTHESIS",
                "formula": "NECESIDAD - STOCK_UTILIZABLE - COMPRAS_CONFIRMADAS_PENDIENTES",
                "covered_count": covered, "purchase_required": purchases,
                "purchase_groups": purchase_groups,
                "draft_orders_not_coverage": [{"articulo_id": k[0], "unidad": k[1], "cantidad": round(v, 6)} for k, v in drafts.items() if v > 0 and k[0] in {str(item.get("articulo_id") or "") for item in purchases}],
                "incidents": incidents, "ingredient_states": ingredient_states,
                "state_counts": cls._state_counts(ingredient_states),
                "datos_reales_modificados": False}

    @classmethod
    def _purchase_groups(cls, purchases: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        provider_labels: dict[str, str] = {}
        for item in purchases:
            provider = str(item.get("proveedor") or "").strip() or "Sin proveedor asignado"
            key = cls._norm(provider)
            provider_labels.setdefault(key, provider)
            grouped[key].append({
                "articulo_id": str(item.get("articulo_id") or ""),
                "nombre": str(item.get("nombre") or item.get("articulo_id") or ""),
                "cantidad": item.get("necesidad_neta"),
                "unidad": str(item.get("unidad") or ""),
                "formato": item.get("formato_compra"),
                "precio_unitario": item.get("precio_unitario"),
                "unidad_precio": item.get("unidad_precio"),
                "coste_neto": item.get("coste_neto"),
            })
        menu_id = cls._menu_id(evidence)
        orders = [dict(order) for data in evidence for order in list(data.get("pedidos") or []) if isinstance(order, dict)]
        output = []
        for key, items in grouped.items():
            provider = provider_labels[key]
            article_ids = {str(item.get("articulo_id") or "") for item in items}
            relevant = [order for order in orders if cls._norm(order.get("proveedor_nombre") or order.get("proveedor")) == key and (
                not article_ids or article_ids.intersection(str(line.get("articulo_id") or "") for line in list(order.get("lineas") or []))
            )]
            open_order = next((order for order in relevant if cls._norm(order.get("estado")) in cls.CONFIRMED_ORDER_STATES), None)
            draft = next((order for order in relevant if cls._norm(order.get("estado")) in cls.DRAFT_ORDER_STATES), None)
            selected = open_order or draft
            related_lines = []
            if selected:
                by_article = {str(item.get("articulo_id") or ""): item for item in items}
                for line in list(selected.get("lineas") or []):
                    article_id = str(line.get("articulo_id") or "")
                    need = by_article.get(article_id)
                    if not need:
                        continue
                    planned = cls._number(line.get("pendiente", line.get("cantidad", line.get("pedido"))))
                    required = cls._number(need.get("cantidad"))
                    same_unit = cls._norm(line.get("unidad")) == cls._norm(need.get("unidad"))
                    related_lines.append({
                        "articulo_id": article_id,
                        "nombre": need.get("nombre"),
                        "cantidad_prevista": planned,
                        "unidad": str(line.get("unidad") or ""),
                        "cubriria_necesidad": bool(same_unit and planned is not None and required is not None and planned >= required),
                    })
            if selected:
                action = {
                    "type": "OPEN_ORDER",
                    "label": "Abrir pedido" if open_order else "Abrir borrador",
                    "pedido_id": str(selected.get("pedido_id") or selected.get("id") or ""),
                }
            elif provider != "Sin proveedor asignado" and menu_id:
                action = {"type": "PREPARE_ORDER", "label": "Preparar pedido", "menu_id": menu_id}
            else:
                action = None
            output.append({
                "proveedor": provider, "articulos": items,
                "estado_pedido": str((selected or {}).get("estado") or "ninguno"),
                "pedido_relacionado": ({"pedido_id": str((selected or {}).get("pedido_id") or (selected or {}).get("id") or ""), "estado": str((selected or {}).get("estado") or ""), "lineas_relevantes": related_lines} if selected else None),
                "action": action,
            })
        return output

    @staticmethod
    def _menu_id(evidence: list[dict[str, Any]]) -> str:
        for data in evidence:
            needs = data.get("necesidades")
            candidates = [data, needs] if isinstance(needs, dict) else [data]
            for candidate in candidates:
                value = str(candidate.get("menu_id") or candidate.get("id_menu") or "").strip()
                if value:
                    return value
        return ""

    @classmethod
    def ingredient_states(cls, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Clasifica ingredientes sin permitir que ausencia de evidencia implique compra o cobertura."""
        ingredients = cls._proposal_ingredients(evidence)
        stock_items = cls._stock_items(evidence)
        confirmed, drafts = cls._orders(evidence)
        orders_known = any(isinstance(data.get("pedidos"), list) for data in evidence)
        articles = cls._articles(evidence)
        output: list[dict[str, Any]] = []

        for ingredient in ingredients:
            name = str(ingredient.get("ingrediente") or ingredient.get("nombre") or ingredient.get("termino") or "").strip()
            relation = cls._relation_state(ingredient)
            article_id = str(ingredient.get("article_id") or ingredient.get("articulo_id") or "").strip()
            article = dict(articles.get(article_id) or {})
            required = cls._number(ingredient.get("necesidad", ingredient.get("cantidad_necesaria", ingredient.get("cantidad"))))
            need_unit = normalize_unit(ingredient.get("unidad_necesidad") or ingredient.get("unidad_necesaria") or ingredient.get("unidad"))
            row = {
                "ingrediente": name,
                "necesidad": required,
                "unidad_necesidad": need_unit or None,
                "relacion_estado": relation,
                "article_id": article_id or None,
                "articulo_nombre": ingredient.get("articulo_nombre") or ingredient.get("nombre_articulo") or article.get("nombre"),
                "stock_utilizable": None,
                "unidad_stock": None,
                "compras_confirmadas_pendientes": None,
                "unidades_compatibles": None,
                "necesidad_neta": None,
                "estado_operativo": "VERIFICAR_STOCK",
            }
            if relation == "AMBIGUO":
                row["estado_operativo"] = "CONFIRMAR_ARTICULO"
                output.append(row); continue
            if relation == "NO_ENCONTRADO":
                row["estado_operativo"] = "SIN_ARTICULO"
                output.append(row); continue
            if relation != "RESUELTO" or not article_id:
                output.append(row); continue

            matching_stock = [item for item in stock_items if cls._article_id(item) == article_id]
            if required is None or not need_unit or not matching_stock:
                output.append(row); continue

            converted_stock: list[float] = []
            stock_units: list[str] = []
            for item in matching_stock:
                value = cls._number(item.get("disponible", item.get("cantidad_disponible", item.get("cantidad"))))
                stock_unit = normalize_unit(item.get("unidad_stock") or item.get("unidad"))
                if value is None or not stock_unit:
                    continue
                stock_units.append(stock_unit)
                converted = convert_quantity(value, stock_unit, need_unit, article)
                if converted is not None:
                    converted_stock.append(float(converted))
            row["unidad_stock"] = stock_units[0] if len(set(stock_units)) == 1 else ",".join(sorted(set(stock_units))) or None
            if stock_units and not converted_stock:
                row["unidades_compatibles"] = False
                row["estado_operativo"] = "UNIDAD_INCOMPATIBLE"
                output.append(row); continue
            if not converted_stock:
                output.append(row); continue

            available = sum(converted_stock)
            incoming = 0.0
            incompatible_incoming = False
            for (ordered_id, ordered_unit), amount in confirmed.items():
                if ordered_id != article_id:
                    continue
                converted = convert_quantity(amount, ordered_unit, need_unit, article)
                if converted is None:
                    incompatible_incoming = True
                else:
                    incoming += float(converted)
            row["stock_utilizable"] = round(available, 6)
            row["unidades_compatibles"] = not incompatible_incoming
            row["compras_confirmadas_pendientes"] = round(incoming, 6) if orders_known and not incompatible_incoming else None
            if not orders_known or incompatible_incoming:
                output.append(row); continue
            net = max(required - available - incoming, 0.0)
            row["necesidad_neta"] = round(net, 6)
            row["estado_operativo"] = "COMPRAR" if net > 0 else "CUBIERTO"
            output.append(row)
        return output

    @classmethod
    def _state_summary(cls, states: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "source": "DETERMINISTIC_RECIPE_INGREDIENT_SYNTHESIS",
            "authority": "CANONICAL_OPERATIONAL_STATE",
            "formula": "NECESIDAD - STOCK_UTILIZABLE - COMPRAS_CONFIRMADAS_PENDIENTES",
            "ingredient_states": states,
            "state_counts": cls._state_counts(states),
            "draft_orders_reduce_need": False,
            "datos_reales_modificados": False,
        }

    @staticmethod
    def _state_counts(states: list[dict[str, Any]]) -> dict[str, int]:
        counts = {name: 0 for name in (
            "COMPRAR", "CUBIERTO", "VERIFICAR_STOCK", "CONFIRMAR_ARTICULO", "SIN_ARTICULO", "UNIDAD_INCOMPATIBLE",
        )}
        for item in states:
            state = str(item.get("estado_operativo") or "")
            if state in counts:
                counts[state] += 1
        return counts

    @classmethod
    def missing_recipe_resolution(cls, state: str, candidates: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        normalized = str(state or "").upper()
        if normalized == "AMBIGUO":
            return {"state": normalized, "candidates": list(candidates or [])[:10], "auto_selected": False}
        if normalized == "NO_ENCONTRADO":
            return {"state": normalized, "options": list(MISSING_RECIPE_OPTIONS), "auto_selected": False}
        return {}

    @classmethod
    def _needs(cls, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        output = []
        for data in evidence:
            values = data.get("necesidades")
            if isinstance(values, dict): values = values.get("lines")
            if isinstance(values, list): output.extend(dict(x) for x in values if isinstance(x, dict))
        return output

    @classmethod
    def _proposal_ingredients(cls, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        explicit: dict[str, dict[str, Any]] = {}
        search: dict[str, dict[str, Any]] = {}
        for data in evidence:
            for key in ("propuesta_ingredientes", "ingredientes_propuestos", "necesidades_propuesta"):
                for item in list(data.get(key) or []):
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("ingrediente") or item.get("nombre") or item.get("termino") or "").strip()
                    if name:
                        explicit[cls._norm(name)] = dict(item)
            for item in list(data.get("resultados") or []):
                if not isinstance(item, dict) or "termino" not in item:
                    continue
                name = str(item.get("termino") or "").strip()
                if not name:
                    continue
                state = str(item.get("estado") or "").upper()
                row = {"ingrediente": name, "relacion_estado": state}
                if state in {"OK", "EXACT", "RESUELTO"}:
                    row.update({
                        "article_id": item.get("article_id") or item.get("articulo_id"),
                        "articulo_nombre": item.get("nombre"),
                    })
                search[cls._norm(name)] = row
        keys = list(dict.fromkeys([*explicit, *search]))
        return [{**explicit.get(key, {}), **search.get(key, {})} for key in keys]

    @classmethod
    def _articles(cls, evidence: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        output: dict[str, dict[str, Any]] = {}
        for data in evidence:
            candidates: list[Any] = []
            candidates.extend(list(data.get("articulos") or []))
            article = data.get("articulo")
            if isinstance(article, dict):
                candidates.append(article)
            for result in list(data.get("resultados") or []):
                if not isinstance(result, dict):
                    continue
                candidates.extend(list(result.get("articulos") or result.get("candidatos") or []))
                if result.get("article_id") or result.get("articulo_id"):
                    candidates.append(result)
            for item in candidates:
                if not isinstance(item, dict):
                    continue
                article_id = cls._article_id(item)
                if article_id:
                    output[article_id] = {**output.get(article_id, {}), **item}
        return output

    @staticmethod
    def _stock_items(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for data in evidence:
            output.extend(dict(item) for item in list(data.get("existencias") or []) if isinstance(item, dict))
            for result in list(data.get("resultados") or []):
                if isinstance(result, dict):
                    output.extend(dict(item) for item in list(result.get("existencias") or []) if isinstance(item, dict))
        return output

    @staticmethod
    def _article_id(item: dict[str, Any]) -> str:
        return str(item.get("article_id") or item.get("articulo_id") or item.get("codigo") or "").strip()

    @staticmethod
    def _relation_state(item: dict[str, Any]) -> str:
        value = str(item.get("relacion_estado") or item.get("estado_relacion") or "").strip().upper()
        if value in {"OK", "EXACT", "RESUELTO", "RESUELTA"}:
            return "RESUELTO"
        if value in {"AMBIGUO", "AMBIGUA"}:
            return "AMBIGUO"
        if value in {"NO_ENCONTRADO", "NO_ENCONTRADA", "SIN_ARTICULO"}:
            return "NO_ENCONTRADO"
        return value or "DESCONOCIDO"

    @staticmethod
    def _norm(value: Any) -> str:
        return " ".join(str(value or "").strip().casefold().split())

    @classmethod
    def _stock(cls, evidence: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
        output = {}
        for data in evidence:
            for item in list(data.get("existencias") or []):
                if not isinstance(item, dict): continue
                key = (str(item.get("articulo_id") or item.get("article_id") or "").strip(), str(item.get("unidad") or item.get("unidad_stock") or "").strip())
                value = cls._number(item.get("disponible", item.get("cantidad_disponible", item.get("cantidad"))))
                if key[0] and key[1] and value is not None: output[key] = value
        return output

    @classmethod
    def _orders(cls, evidence: list[dict[str, Any]]) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], float]]:
        confirmed, drafts = defaultdict(float), defaultdict(float)
        for data in evidence:
            values = data.get("necesidades")
            if isinstance(values, dict):
                for line in list(values.get("lines") or []):
                    if not isinstance(line, dict): continue
                    key = (str(line.get("articulo_id") or "").strip(), str(line.get("unidad_necesaria") or "").strip())
                    value = cls._number(line.get("borradores_pendientes"))
                    if key[0] and key[1] and value is not None: drafts[key] += value
            for order in list(data.get("pedidos") or []):
                if not isinstance(order, dict): continue
                state = str(order.get("estado") or "").strip().lower()
                target = confirmed if state in cls.CONFIRMED_ORDER_STATES else drafts if state in cls.DRAFT_ORDER_STATES else None
                if target is None: continue
                for line in list(order.get("lineas") or []):
                    if not isinstance(line, dict): continue
                    key = (str(line.get("articulo_id") or "").strip(), str(line.get("unidad") or "").strip())
                    value = cls._number(line.get("pendiente", line.get("cantidad")))
                    if key[0] and key[1] and value is not None: target[key] += value
        return dict(confirmed), dict(drafts)

    @staticmethod
    def _number(value: Any) -> float | None:
        try: return float(value) if value not in (None, "") else None
        except (TypeError, ValueError): return None


__all__ = ["HostAIOperationalSynthesis", "MISSING_RECIPE_OPTIONS"]
