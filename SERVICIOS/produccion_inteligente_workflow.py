from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class ProductionInvestigation:
    summary: str
    event: dict[str, Any]
    tasks: list[dict[str, Any]]
    blocked: list[dict[str, Any]]
    unknown: list[str]
    aggregate: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary, "event": self.event, "tasks": self.tasks,
            "blocked": self.blocked, "unknown": self.unknown,
            "aggregate": dict(self.aggregate or {}),
            "datos_reales_modificados": False,
        }


class IntelligentProductionWorkflow:
    """Orquesta READ canónicos y prepara un contexto compacto para Producción."""

    def __init__(self, executor: Any) -> None:
        self.executor = executor

    def investigate(self, event_term: str = "", active_event: dict[str, Any] | None = None) -> ProductionInvestigation:
        event = dict(active_event or {})
        if not event:
            is_next_event = self._is_next_event_reference(event_term)
            event_result = self.executor.execute_agent_read(
                "consultar_eventos",
                {"consulta": "proximos" if is_next_event else "buscar", "termino": "" if is_next_event else event_term, "limite": 10},
            )
            events = list(getattr(event_result, "datos", {}).get("resultados") or [])
            if is_next_event:
                selected, diagnosis = self._select_next_event(events)
                if selected is not None:
                    event = selected
                else:
                    return ProductionInvestigation(
                        "No he podido determinar el próximo evento operativo.", {}, [], [], [diagnosis], {},
                    )
            elif len(events) == 1:
                event = dict(events[0])
            elif len(events) > 1:
                return ProductionInvestigation("He encontrado varios eventos con ese nombre; necesito que me indiques cuál es la boda.", {}, [], [], ["evento ambiguo"], {})
            else:
                return ProductionInvestigation("No he encontrado un evento inequívoco para preparar la producción.", {}, [], [], ["evento no localizado"], {})

        event_id = str(event.get("id") or event.get("evento_id") or "")
        if event_id:
            detail = self._data("consultar_evento_detalle", {"evento_id": event_id})
            if detail.get("estado") == "OK" and isinstance(detail.get("evento"), dict):
                event = {**event, **dict(detail["evento"]), "id": event_id}
        term = str(event.get("id") or event.get("nombre") or event_term)
        production_result = self.executor.execute_agent_read("consultar_produccion", {"consulta": "buscar", "termino": term, "limite": 10})
        data = dict(getattr(production_result, "datos", {}) or {})
        tasks = [dict(item) for item in list(data.get("resultados") or [])]
        if not tasks and term:
            fallback = self.executor.execute_agent_read("consultar_produccion", {"consulta": "pendientes", "limite": 10})
            all_tasks = [dict(item) for item in list(getattr(fallback, "datos", {}).get("resultados") or [])]
            event_id = str(event.get("id") or "")
            tasks = [item for item in all_tasks if event_id and str(item.get("evento_id") or "") == event_id]
        blocked = [task for task in tasks if str(task.get("estado") or "") == "bloqueada" or task.get("bloqueo")]
        unknown = []
        if event.get("pax") in (None, ""):
            unknown.append("pax")
        if not event.get("servicios"):
            unknown.append("servicios")
        if not tasks:
            unknown.append("plan de producción asociado")
        aggregate = self._aggregate(event, tasks)
        unknown.extend(item for item in aggregate["unknown"] if item not in unknown)
        return ProductionInvestigation(self._summary(event, tasks, blocked, unknown, aggregate), event, tasks, blocked, unknown, aggregate)

    @staticmethod
    def _is_next_event_reference(value: str) -> bool:
        text = str(value or "").lower()
        return any(phrase in text for phrase in ("proximo evento", "siguiente evento", "proxima boda", "lo siguiente", "produccion de lo proximo"))

    @classmethod
    def _select_next_event(cls, events: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
        today = date.today()
        candidates: list[tuple[date, str, dict[str, Any]]] = []
        invalid_dates = 0
        for raw in events:
            item = dict(raw or {})
            state = str(item.get("estado") or "").lower()
            if state in {"cancelado", "finalizado", "facturado"}:
                continue
            parsed = cls._parse_event_date(item.get("fecha"))
            if parsed is None:
                invalid_dates += 1
                continue
            if parsed >= today:
                candidates.append((parsed, str(item.get("hora_inicio") or item.get("hora") or ""), item))
        if not candidates:
            return None, "no hay evento futuro operativo con fecha válida"
        candidates.sort(key=lambda item: (item[0], item[1]))
        nearest_date, nearest_time, selected = candidates[0]
        tied = [item for item in candidates if item[0] == nearest_date and item[1] == nearest_time]
        if len(tied) > 1:
            return None, "hay varios eventos con la misma fecha y hora"
        return selected, "" if not invalid_dates else "fechas inválidas ignoradas"

    @staticmethod
    def _parse_event_date(value: Any) -> date | None:
        text = str(value or "").strip()
        for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, pattern).date()
            except ValueError:
                continue
        return None

    def _aggregate(self, event: dict[str, Any], tasks: list[dict[str, Any]]) -> dict[str, Any]:
        menu_id, menu_term = self._menu_reference(event)
        menu_response = self._data(
            "consultar_menu",
            {"consulta": "elaboraciones", "menu_id": menu_id, "termino": menu_term, "limite": 10},
        ) if menu_id or menu_term else {}
        menu = dict(menu_response.get("menu") or {})
        elaborations = list(menu.get("elaboraciones") or menu_response.get("elaboraciones") or event.get("elaboraciones") or self._pass_elaborations(event))
        recipe_ids = [str(item.get("elaboracion_id") or item.get("id") or item.get("receta_id") or "") for item in elaborations if isinstance(item, dict)]
        recipe_ids = [item for item in dict.fromkeys(recipe_ids) if item]
        recipes_data = self._data("consultar_escandallos", {"escandallo_ids": recipe_ids, "limite": 10}) if recipe_ids else {}
        recipes = list(recipes_data.get("detalles") or [])
        needs, unknown = self._needs(recipes, event.get("pax"))
        graph = self._dependency_graph(recipes)
        article_ids = [str(item.get("articulo_id") or "") for item in needs if item.get("articulo_id")]
        stock = self._data("consultar_estado_stock", {"consulta": "articulo", "terminos": article_ids[:10]}) if article_ids else {}
        purchases = self._data("consultar_compras_pendientes", {"consulta": "listado", "limite": 10})
        coverage = self._coverage(needs, stock, purchases)
        return {
            "menu": menu, "recipes": recipes, "needs": needs, "dependencies": graph,
            "stock": stock, "purchases": purchases, "coverage": coverage, "unknown": unknown,
            "facts": {"event_date": event.get("fecha"), "pax": event.get("pax")},
            "ai_proposals": self._timing_proposals(recipes, event),
        }

    @staticmethod
    def _menu_reference(event: dict[str, Any]) -> tuple[str, str]:
        direct_id = str(event.get("menu_id") or event.get("id_menu") or "").strip()
        raw_menu = event.get("menu") or event.get("menu_nombre") or ""
        if isinstance(raw_menu, dict):
            return str(raw_menu.get("menu_id") or raw_menu.get("id") or direct_id), str(raw_menu.get("nombre") or "")
        if direct_id:
            return direct_id, ""
        for service in list(event.get("servicios") or []):
            if not isinstance(service, dict):
                continue
            menu = service.get("menu") or service.get("menu_id") or ""
            if isinstance(menu, dict):
                return str(menu.get("menu_id") or menu.get("id") or ""), str(menu.get("nombre") or "")
            if menu:
                return str(menu), ""
            for course in list(service.get("pases") or []):
                if isinstance(course, dict) and course.get("menu_id"):
                    return str(course.get("menu_id") or ""), ""
        return "", str(raw_menu or "").strip()

    @staticmethod
    def _pass_elaborations(event: dict[str, Any]) -> list[dict[str, Any]]:
        rows = []
        for service in list(event.get("servicios") or []):
            if not isinstance(service, dict):
                continue
            for course in list(service.get("pases") or []):
                if not isinstance(course, dict):
                    continue
                for recipe_id in list(course.get("recetas") or []):
                    if isinstance(recipe_id, str) and recipe_id.strip():
                        rows.append({"elaboracion_id": recipe_id.strip(), "tipo_referencia": "RECETA"})
        return rows

    def _data(self, tool_id: str, params: dict[str, Any]) -> dict[str, Any]:
        result = self.executor.execute_agent_read(tool_id, params)
        return dict(getattr(result, "datos", {}) or {})

    @staticmethod
    def _needs(recipes: list[dict[str, Any]], pax: Any) -> tuple[list[dict[str, Any]], list[str]]:
        try:
            diners = float(pax)
        except (TypeError, ValueError):
            diners = 0
        output: list[dict[str, Any]] = []
        unknown: list[str] = []
        for recipe in recipes:
            try:
                yield_value = float(recipe.get("rendimiento") or recipe.get("raciones") or 0)
            except (TypeError, ValueError):
                yield_value = 0
            if diners <= 0 or yield_value <= 0:
                unknown.append(f"rendimiento o pax de {recipe.get('nombre') or recipe.get('id')}")
                continue
            factor = diners / yield_value
            for ingredient in list(recipe.get("ingredientes") or []):
                if not isinstance(ingredient, dict):
                    continue
                try:
                    amount = float(ingredient.get("cantidad") or 0)
                except (TypeError, ValueError):
                    amount = 0
                if amount <= 0:
                    unknown.append(f"cantidad de {ingredient.get('nombre_articulo') or ingredient.get('nombre_original')}")
                    continue
                output.append({
                    "recipe_id": str(recipe.get("id") or recipe.get("codigo") or ""),
                    "recipe": recipe.get("nombre"), "articulo_id": str(ingredient.get("articulo_id") or ""),
                    "nombre": ingredient.get("nombre_articulo") or ingredient.get("nombre_original"),
                    "cantidad_necesaria": amount * factor, "unidad": ingredient.get("unidad"),
                    "factor": factor,
                })
        return output, unknown

    @staticmethod
    def _dependency_graph(recipes: list[dict[str, Any]]) -> dict[str, Any]:
        nodes = {str(item.get("id") or item.get("codigo") or ""): item for item in recipes}
        edges = {key: [] for key in nodes if key}
        for key, recipe in nodes.items():
            for ingredient in list(recipe.get("ingredientes") or []):
                child = str(ingredient.get("escandallo_hijo_id") or ingredient.get("referencia_elaboracion") or "")
                if child and child in edges:
                    edges[key].append(child)
        visited, active, ordered, cycles = set(), set(), [], []
        def visit(node: str) -> None:
            if node in active:
                cycles.append(node); return
            if node in visited: return
            active.add(node)
            for child in edges.get(node, []): visit(child)
            active.remove(node); visited.add(node); ordered.append(node)
        for node in edges: visit(node)
        return {"edges": edges, "orden_tecnico": ordered, "ciclos": cycles}

    @staticmethod
    def _coverage(needs: list[dict[str, Any]], stock: dict[str, Any], purchases: dict[str, Any]) -> list[dict[str, Any]]:
        stock_items = list(stock.get("articulos") or stock.get("resultados") or [])
        for batch_item in list(stock.get("items") or []):
            if isinstance(batch_item, dict):
                stock_items.extend(list(batch_item.get("existencias") or []))
        for batch in list(stock.get("resultados_batch") or []):
            if isinstance(batch, dict):
                stock_items.extend(list(batch.get("articulos") or batch.get("resultados") or []))
        orders = list(purchases.get("pedidos") or [])
        output = []
        for need in needs:
            stock_item = next((item for item in stock_items if str(item.get("articulo_id") or item.get("article_id") or item.get("codigo") or item.get("id") or "") == need["articulo_id"]), {})
            stock_qty = float(stock_item.get("cantidad") or stock_item.get("stock") or 0)
            stock_unit = str(stock_item.get("unidad") or stock_item.get("unidad_stock") or need.get("unidad") or "")
            normalized_stock = IntelligentProductionWorkflow._convert(stock_qty, stock_unit, str(need.get("unidad") or ""))
            conversion_missing = normalized_stock is None
            if conversion_missing:
                normalized_stock = 0.0
            pending = 0.0
            for order in orders:
                if str(order.get("estado") or "").lower() in {"borrador", "cancelado", "recibido"}: continue
                for line in list(order.get("lineas") or []):
                    if str(line.get("articulo_id") or "") == need["articulo_id"]:
                        quantity = float(line.get("pendiente") or 0)
                        converted = IntelligentProductionWorkflow._convert(
                            quantity, str(line.get("unidad") or ""), str(need.get("unidad") or ""),
                        )
                        if converted is not None:
                            pending += converted
            pre = max(need["cantidad_necesaria"] - normalized_stock, 0)
            output.append({**need, "stock_utilizable": normalized_stock, "unidad_stock": stock_unit, "conversion_faltante": conversion_missing, "compra_pendiente_utilizable": pending, "faltante_pre_compra": pre, "faltante_final": max(pre - pending, 0)})
        return output

    @staticmethod
    def _convert(value: float, source: str, target: str) -> float | None:
        source = str(source or "").lower().strip()
        target = str(target or "").lower().strip()
        if not source or not target or source == target:
            return value
        factors = {("kg", "g"): 1000.0, ("g", "kg"): 0.001, ("l", "ml"): 1000.0, ("ml", "l"): 0.001}
        factor = factors.get((source, target))
        return value * factor if factor is not None else None

    @staticmethod
    def _timing_proposals(recipes: list[dict[str, Any]], event: dict[str, Any]) -> list[dict[str, Any]]:
        proposals = []
        for recipe in recipes:
            if not recipe.get("conservacion") and not recipe.get("tiempo_total"):
                proposals.append({"recipe_id": recipe.get("id"), "tipo": "AI_PROPOSAL", "mensaje": f"Revisaría {recipe.get('nombre')} antes de adelantarla: no hay conservación ni tiempo registrado."})
        return proposals

    @staticmethod
    def _summary(event: dict[str, Any], tasks: list[dict[str, Any]], blocked: list[dict[str, Any]], unknown: list[str], aggregate: dict[str, Any]) -> str:
        name = str(event.get("nombre") or "el evento")
        if not tasks:
            return f"He revisado {name}, pero no hay tareas de producción asociadas disponibles. Falta comprobar " + ", ".join(unknown) + "."
        pending = [task for task in tasks if str(task.get("estado") or "") not in {"finalizada", "cancelada"}]
        first = pending[0] if pending else {}
        text = f"Para {name} hay {len(pending)} tarea(s) abiertas"
        if first:
            text += f". Empezaría por {first.get('titulo') or 'la primera tarea pendiente'}"
            if first.get("cantidad") is not None:
                text += f" ({first.get('cantidad')} {first.get('unidad') or ''})"
        if blocked:
            text += ". Hay bloqueos que requieren decisión: " + ", ".join(str(task.get("titulo") or "tarea") for task in blocked)
        if unknown:
            text += ". Aún no están verificados: " + ", ".join(unknown)
        coverage = [item for item in aggregate.get("coverage", []) if item.get("faltante_final", 0) > 0]
        if coverage:
            first_gap = coverage[0]
            text += f". Falta comprar {first_gap['faltante_final']:g} {first_gap.get('unidad') or ''} de {first_gap.get('nombre') or 'un artículo'}"
        return text + "."

    @staticmethod
    def professional_summary(result: ProductionInvestigation) -> str:
        event = result.event
        aggregate = dict(result.aggregate or {})
        coverage = list(aggregate.get("coverage") or [])
        needs = list(aggregate.get("needs") or [])
        parts = [f"Para {event.get('nombre') or 'el evento'} tienes {len(result.tasks)} tarea(s) abiertas."]
        if needs:
            rendered = []
            for item in needs[:4]:
                quantity = float(item.get("cantidad_necesaria") or 0)
                unit = str(item.get("unidad") or "").strip()
                name = str(item.get("nombre") or item.get("recipe") or "elaboración")
                rendered.append(f"{name}: {quantity:g} {unit}".strip())
            parts.append("Producción calculada: " + "; ".join(rendered) + ".")
        blocked = [item for item in result.blocked if item.get("bloqueo")]
        if blocked:
            parts.append("Bloqueos: " + "; ".join(f"{item.get('titulo') or 'Tarea'} ({item.get('bloqueo')})" for item in blocked) + ".")
        gaps = [item for item in coverage if item.get("conversion_faltante") or float(item.get("faltante_final") or 0) > 0]
        if gaps:
            rendered = []
            for item in gaps[:4]:
                if item.get("conversion_faltante"):
                    rendered.append(f"no puedo comprobar {item.get('nombre') or 'un ingrediente'} porque falta conversión entre {item.get('unidad_stock') or 'la unidad de stock'} y {item.get('unidad') or 'la unidad requerida'}")
                else:
                    rendered.append(f"faltan {float(item.get('faltante_final') or 0):g} {item.get('unidad') or ''} de {item.get('nombre') or 'un artículo'}")
            parts.append("Compras y cobertura: " + "; ".join(rendered) + ".")
        elif coverage:
            parts.append("Las necesidades calculadas quedan cubiertas por stock y pedidos operativos registrados.")
        cycles = list((aggregate.get("dependencies") or {}).get("ciclos") or [])
        if cycles:
            parts.append("Hay una dependencia circular que debe revisarse antes de ordenar esa parte de la producción.")
        elif (aggregate.get("dependencies") or {}).get("orden_tecnico"):
            parts.append("El orden técnico ya incorpora las subelaboraciones antes de los platos que dependen de ellas.")
        if result.unknown:
            parts.append("Antes de cerrar el plan falta verificar: " + ", ".join(str(item) for item in result.unknown[:4]) + ".")
        proposals = list(aggregate.get("ai_proposals") or [])
        if proposals:
            parts.append("Como recomendación operativa, revisaría tiempos y conservación antes de adelantar las elaboraciones sin esos datos registrados.")
        return " ".join(parts)


__all__ = ["IntelligentProductionWorkflow", "ProductionInvestigation"]