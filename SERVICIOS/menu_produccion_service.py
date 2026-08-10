from __future__ import annotations

from datetime import datetime
from copy import deepcopy
import json
from pathlib import Path
import os
import tempfile
from typing import Any

from MODELOS.produccion_real import PlanProduccionReal, TareaProduccionReal
from SERVICIOS.menu_necesidades_service import MenuNecesidadesService
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService
from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.stock_ajustes_service import StockAjustesService


class _ProductionStockAbort(Exception):
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        super().__init__(str((result.get("error") or {}).get("message") or "No se pudo registrar Stock."))


class MenuProduccionService:
    """Orquesta Menús, Producción Real y Stock sin duplicar sus reglas."""

    def __init__(self, core: Any) -> None:
        self.core = core
        self.menus = MenusInteligentesService(core.base_dir)
        self.necesidades = MenuNecesidadesService(core.base_dir, compras=core.compras, stock_motor=core.stock)

    def generar(self, menu_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = dict(body or {})
        menu_result = self.menus.obtener(menu_id)
        if not menu_result.get("ok"):
            return menu_result
        menu = menu_result["menu"]
        existing = next((p for p in self.core.produccion_real.planes.values()
                         if p.configuracion_planificacion.get("menu_id") == menu_id
                         and int(p.configuracion_planificacion.get("menu_version") or 0) == int(menu["version"])), None)
        if existing:
            return {"ok": True, "plan": self._project(existing), "idempotente": True, "stock_modificado": False}

        projection = self.necesidades.necesidades(menu_id)
        if not projection.get("ok"):
            return projection
        needs = projection["necesidades"]
        tasks: dict[str, TareaProduccionReal] = {}
        production_errors = list(needs.get("blocking_errors") or [])
        for section in menu.get("secciones") or []:
            for ref in section.get("elaboraciones") or []:
                rid = str(ref.get("elaboracion_id") or "")
                target = float(menu["comensales"]) * float(ref.get("cantidad") or 1)
                task = tasks.get(rid)
                if task is None:
                    task = TareaProduccionReal(
                        titulo=str(ref.get("elaboracion_nombre") or rid), receta_id=rid,
                        receta=str(ref.get("elaboracion_nombre") or rid), cantidad=0, unidad="raciones",
                        origen=f"menu:{menu_id}",
                    )
                    task.requisitos_recursos = {"ingredientes": [], "origenes": [], "fecha_produccion": str(body.get("fecha_produccion") or body.get("fecha_servicio") or "")}
                    tasks[rid] = task
                task.cantidad += target
                task.requisitos_recursos["origenes"].append({"seccion": section.get("nombre"), "cantidad": target})
                try:
                    explosion = self.necesidades.stock.motor.explotar(task.titulo, target, "raciones")
                    task.requisitos_recursos["arbol_subelaboraciones"] = explosion.get("arbol")
                    task.requisitos_recursos["rendimiento_base"] = explosion.get("rendimiento_base")
                    task.requisitos_recursos["factor_escalado"] = explosion.get("factor")
                    for issue in explosion.get("incidencias") or []:
                        if issue.get("tipo") == "ciclo_detectado":
                            production_errors.append({"code": "PRODUCTION_CYCLE", "message": f"Ciclo detectado en {issue.get('receta') or rid}.", "elaboracion_id": rid})
                except (LookupError, ValueError) as exc:
                    production_errors.append({"code": "PRODUCTION_EXPLOSION_ERROR", "message": str(exc), "elaboracion_id": rid})

        for line in needs.get("lines") or []:
            for origin in line.get("origenes") or []:
                task = tasks.get(str(origin.get("elaboracion_id") or ""))
                if not task:
                    continue
                total_need = float(line.get("cantidad_necesaria") or 0)
                share = float(origin.get("cantidad") or 0) / total_need if total_need else 0
                task.requisitos_recursos["ingredientes"].append({
                    "nombre": line.get("articulo_nombre") or line.get("ingrediente_nombre"),
                    "articulo_id": line.get("articulo_id") or "", "cantidad": origin.get("cantidad") or 0,
                    "unidad": origin.get("unidad") or line.get("unidad_necesaria") or "u",
                    "disponible": line.get("stock_disponible"), "faltante": line.get("cantidad_faltante"),
                    "proveedor": line.get("proveedor_preferente"), "estado": line.get("estado"),
                    "factor_escalado": origin.get("factor_escalado") or 0,
                    "coste_estimado": float(line.get("coste_estimado") or 0) * share,
                })
                task.requisitos_recursos["coste_estimado"] = float(task.requisitos_recursos.get("coste_estimado") or 0) + float(line.get("coste_estimado") or 0) * share

        generated_at = datetime.now().isoformat(timespec="seconds")
        plan = PlanProduccionReal(
            nombre=f"Producción · {menu['nombre']}", fecha=str(body.get("fecha_servicio") or ""),
            evento_id=str(body.get("event_id") or ""), pax=int(menu["comensales"]), estado="borrador",
            tareas=list(tasks.values()), avisos=list(needs.get("warnings") or []),
            configuracion_planificacion={
                "generado_desde": "menu", "generated_at": generated_at, "menu_id": menu_id,
                "menu_version": int(menu["version"]), "errores_bloqueantes": production_errors,
                "ingredientes_agrupados": list(needs.get("lines") or []),
            },
        )
        self.core.produccion_real.planes[plan.id] = plan
        self.core.produccion_real._persistir()
        return {"ok": True, "plan": self._project(plan), "idempotente": False, "stock_modificado": False}

    def obtener(self, plan_id: str) -> dict[str, Any]:
        return {"ok": True, "plan": self._project(self.core.produccion_real.obtener_plan(plan_id))}

    def crear_propuesta_compra(self, plan_id: str) -> dict[str, Any]:
        plan = self.core.produccion_real.obtener_plan(plan_id)
        projected = self._project(plan)
        menu_id = str(projected.get("menu_id") or "")
        if not menu_id:
            return {"ok": False, "error": {"status": 400, "code": "menu_trace_required", "message": "El plan no conserva un menú de origen."}}
        result = self.necesidades.crear_propuesta_faltantes_produccion(menu_id, {
            "production_plan_id": plan_id, "event_id": plan.evento_id or None,
            "fecha": plan.fecha or projected.get("generated_at"),
        })
        if result.get("ok") and (result.get("propuesta") or {}).get("id"):
            plan.configuracion_planificacion["propuesta_compra_id"] = result["propuesta"]["id"]
            self.core.produccion_real._persistir()
        return {**result, "clasificacion": self._classification(projected["ingredientes"])}

    def revisar_stock(self, plan_id: str) -> dict[str, Any]:
        plan = self._project(self.core.produccion_real.obtener_plan(plan_id))
        products = self.necesidades.productos
        rows = []
        for item in plan["ingredientes"]:
            product = products.obtener_producto(str(item.get("articulo_id") or "")) or {}
            state = self._resolution_state(item, product)
            rows.append({**item, "ingrediente": item.get("nombre"),
                "unidad_requerida": item.get("unidad"), "unidad_base": product.get("unidad_base") or product.get("unidad") or None,
                "unidad_base_sugerida": bool(product.get("unidad_base_sugerida")),
                "estado_unidad_base": product.get("estado_unidad_base") or "CONFIRMADA", "estado_resolucion": state})
        summary = {"ingredientes_totales": len(rows)}
        for key, state in (("cubiertos", "CUBIERTO"), ("faltantes_conocidos", "FALTANTE_CONOCIDO"),
                           ("stock_desconocido", "STOCK_DESCONOCIDO"), ("sin_relacionar", "SIN_ARTICULO"),
                           ("unidad_pendiente", "UNIDAD_PENDIENTE"), ("conversion_pendiente", "CONVERSION_PENDIENTE")):
            summary[key] = sum(row["estado_resolucion"] == state for row in rows)
        return {"ok": True, "revision_stock": {"production_plan_id": plan_id, "plan_nombre": plan.get("nombre"),
            "menu_id": plan.get("menu_id"), "menu_version": plan.get("menu_version"), "event_id": plan.get("evento_id"),
            "ingredientes": rows, "resumen": summary, "stock_modificado": False}}

    def registrar_inventario_desde_revision(self, plan_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Confirma una unidad sugerida y registra Stock como una sola operación lógica."""
        if body.get("confirmacion") != "REGISTRAR_STOCK_DESDE_PRODUCCION":
            return self._error(400, "confirmation_required", "Confirma el registro de Stock desde Producción.")
        review = self.revisar_stock(plan_id)
        article_id = str(body.get("article_id") or "").strip()
        row = next((item for item in review["revision_stock"]["ingredientes"] if item.get("articulo_id") == article_id), None)
        if not row:
            return self._error(404, "production_article_not_found", "El artículo no pertenece a este plan de Producción.")
        selected_unit = str(body.get("unidad") or "").strip().lower()
        product = self.necesidades.productos.obtener_producto(article_id) or {}
        canonical_unit = str(product.get("unidad_base") or product.get("unidad") or "").strip().lower()
        suggested = bool(product.get("unidad_base_sugerida"))
        if not selected_unit:
            return self._error(400, "unit_required", "Selecciona una unidad base.")
        if not suggested and selected_unit != canonical_unit:
            return self._error(409, "confirmed_unit_mismatch", f"La unidad confirmada del artículo es {canonical_unit}.")

        article_path = Path(self.core.base_dir) / "DATOS" / "db" / "articulos.json"
        article_before = article_path.read_bytes()
        lots_before, movements_before = deepcopy(self.core.stock.lotes), deepcopy(self.core.stock.movimientos)
        try:
            if suggested:
                articles = ArticulosCatalogReadService(self.core.base_dir, stock=self.core.stock, compras=self.core.compras)
                update = articles.actualizar(article_id, {
                    "confirmacion": "ACTUALIZAR_ARTICULO_MAESTRO", "nombre": str(product.get("nombre") or article_id),
                    "unidad_base": selected_unit,
                })
                if not update.get("ok"):
                    return update
                confirmed = update["articulo"]
                if confirmed.get("unidad_base_sugerida") or str(confirmed.get("unidad_base") or "").lower() != selected_unit:
                    raise RuntimeError("La unidad seleccionada no quedó confirmada en la ficha canónica.")
            movement_body = {**body, "confirmacion": "REGISTRAR_MOVIMIENTO_STOCK", "production_plan_id": plan_id,
                             "unidad": selected_unit}
            result = StockAjustesService(self.core).registrar(movement_body)
            if not result.get("ok"):
                raise _ProductionStockAbort(result)
            refreshed = self.revisar_stock(plan_id)["revision_stock"]
            return {**result, "revision_stock": refreshed, "unidad_canonica": selected_unit}
        except _ProductionStockAbort as exc:
            self._rollback_stock_resolution(article_path, article_before, lots_before, movements_before)
            return exc.result
        except Exception:
            self._rollback_stock_resolution(article_path, article_before, lots_before, movements_before)
            raise

    def _rollback_stock_resolution(self, article_path: Path, article_before: bytes,
                                   lots_before: dict[str, Any], movements_before: dict[str, Any]) -> None:
        fd, temporary = tempfile.mkstemp(prefix=f".{article_path.name}.", dir=str(article_path.parent))
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(article_before)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, article_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        self.core.stock.lotes = lots_before
        self.core.stock.movimientos = movements_before
        self.core.stock._guardar_automatico()

    @staticmethod
    def _error(status: int, code: str, message: str) -> dict[str, Any]:
        return {"ok": False, "error": {"status": status, "code": code, "message": message}}

    def relacionar_articulo(self, plan_id: str, body: dict[str, Any]) -> dict[str, Any]:
        if body.get("confirmacion") != "RELACIONAR_INGREDIENTE_ARTICULO":
            return {"ok": False, "error": {"status": 400, "code": "confirmation_required", "message": "Confirma la relación del ingrediente."}}
        article_id = str(body.get("article_id") or "").strip()
        if not self.necesidades.productos.obtener_producto(article_id):
            return {"ok": False, "error": {"status": 404, "code": "article_not_found", "message": "El artículo seleccionado no existe."}}
        recipe_id, ingredient_name = str(body.get("elaboration_id") or "").strip(), str(body.get("ingredient_name") or "").strip()
        path = Path(self.core.base_dir) / "DATOS" / "db" / "escandallos_canonicos.json"
        try: data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"ok": False, "error": {"status": 500, "code": "recipes_unavailable", "message": "No se pudo leer el catálogo de recetas."}}
        entries = data if isinstance(data, list) else data.get("escandallos", [])
        changed = False
        for entry in entries:
            recipe = entry.get("receta") if isinstance(entry.get("receta"), dict) else entry
            if str(recipe.get("codigo") or recipe.get("id") or "") != recipe_id: continue
            for ingredient in recipe.get("ingredientes") or []:
                if str(ingredient.get("nombre") or "").strip().casefold() == ingredient_name.casefold():
                    ingredient["articulo_id"] = article_id; changed = True; break
        if not changed:
            return {"ok": False, "error": {"status": 404, "code": "ingredient_not_found", "message": "No se encontró el ingrediente en la elaboración de origen."}}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.necesidades.stock.motor = type(self.necesidades.stock.motor)(self.core.base_dir)
        return {**self.revisar_stock(plan_id), "datos_reales_modificados": True, "relacion_guardada": True}

    @staticmethod
    def _resolution_state(item: dict[str, Any], product: dict[str, Any]) -> str:
        if not item.get("articulo_id"): return "SIN_ARTICULO"
        if not (product.get("unidad_base") or product.get("unidad")): return "UNIDAD_PENDIENTE"
        if item.get("estado_stock") == "UNIDAD_INCOMPATIBLE": return "CONVERSION_PENDIENTE"
        if item.get("disponible") is None: return "STOCK_DESCONOCIDO"
        if float(item.get("faltante") or 0) > 0: return "FALTANTE_CONOCIDO"
        return "CUBIERTO"

    def _project(self, plan: PlanProduccionReal) -> dict[str, Any]:
        data = plan.to_dict()
        config = data.get("configuracion_planificacion") or {}
        current = self.necesidades.necesidades(str(config.get("menu_id") or ""))
        if current.get("ok"):
            fresh = current["necesidades"]
            config["ingredientes_agrupados"] = list(fresh.get("lines") or [])
            fresh_by_key = {
                (str(x.get("articulo_id") or "").casefold(), str(x.get("unidad_necesaria") or "u").casefold()): x
                for x in fresh.get("lines") or []
            }
            for task in data["tareas"]:
                for item in (task.get("requisitos_recursos") or {}).get("ingredientes") or []:
                    line = fresh_by_key.get((str(item.get("articulo_id") or "").casefold(), str(item.get("unidad") or "u").casefold()))
                    if line:
                        item.update({
                            "disponible": line.get("stock_disponible"),
                            "faltante": line.get("cantidad_faltante"),
                            "estado": line.get("estado"),
                            "estado_stock": line.get("estado_stock"),
                            "stock_disponible": line.get("stock_disponible"),
                        })
        subelaboraciones: dict[tuple[str, str], dict[str, Any]] = {}
        for task in data["tareas"]:
            task["ingredientes"] = list((task.get("requisitos_recursos") or {}).get("ingredientes") or [])
            resources = task.get("requisitos_recursos") or {}
            factors = [float(x.get("factor_escalado") or 0) for x in task["ingredientes"]]
            task["factor_escalado"] = float(resources.get("factor_escalado") or max(factors, default=0))
            task["rendimiento_base"] = float(resources.get("rendimiento_base") or (task["cantidad"] / task["factor_escalado"] if task["factor_escalado"] else 0))
            task["cantidad_a_producir"] = task["cantidad"]
            task["subelaboraciones"] = resources.get("arbol_subelaboraciones") or {}
            task["coste_estimado"] = round(float(resources.get("coste_estimado") or 0), 2)
            task["estado"] = "BLOQUEADO" if any(float(x.get("faltante") or 0) > 0 for x in task["ingredientes"]) else "LISTO"
            self._collect_subelaborations(task["subelaboraciones"], task, subelaboraciones)
        ingredients = [{
            "nombre": item.get("articulo_nombre") or item.get("ingrediente_nombre"),
            "articulo_id": item.get("articulo_id") or "", "cantidad": item.get("cantidad_necesaria") or 0,
            "unidad": item.get("unidad_necesaria") or "u", "disponible": item.get("stock_disponible"),
            "faltante": item.get("cantidad_faltante"), "proveedor": item.get("proveedor_preferente"),
            "estado": item.get("estado"), "coste_estimado": item.get("coste_estimado"),
            "cantidad_necesaria": item.get("cantidad_necesaria") or 0,
            "stock_disponible": item.get("stock_disponible"), "estado_stock": item.get("estado_stock"),
            "inventario_incompatible": list(item.get("inventario_incompatible") or []),
            "origenes": list(item.get("origenes") or []),
        } for item in config.get("ingredientes_agrupados") or [item for task in data["tareas"] for item in task["ingredientes"]]]
        blockers = config.get("errores_bloqueantes") or []
        missing = sum(1 for x in ingredients if float(x.get("faltante") or 0) > 0)
        data.update({
            "plan_id": plan.id, "menu_id": config.get("menu_id"), "menu_version": config.get("menu_version"),
            "propuesta_compra_id": config.get("propuesta_compra_id"),
            "comensales": plan.pax, "elaboraciones": data["tareas"], "ingredientes": ingredients,
            "subelaboraciones": list(subelaboraciones.values()),
            "advertencias": data.get("avisos") or [], "errores_bloqueantes": blockers,
            "generated_at": config.get("generated_at") or plan.creado_en,
            "estado": "BLOQUEADO" if blockers or missing else "LISTO",
            "clasificacion": self._classification(ingredients),
            "resumen": {"elaboraciones": len(data["tareas"]), "subelaboraciones": len(subelaboraciones), "ingredientes": len(ingredients), "faltantes": missing, "bloqueadas": sum(x["estado"] == "BLOQUEADO" for x in data["tareas"]), "coste_previsto": round(sum(float(x.get("coste_estimado") or 0) for x in ingredients), 2)},
            "solo_planificacion": True, "stock_modificado": False,
        })
        return data

    @staticmethod
    def _classification(ingredients: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "cubiertos": sum(item.get("faltante") == 0 for item in ingredients),
            "faltantes_conocidos": sum(MenuNecesidadesService._es_faltante_conocido(item) for item in ingredients),
            "stock_desconocido": sum(item.get("estado") == "Stock no disponible" for item in ingredients),
            "sin_relacionar": sum(not item.get("articulo_id") or item.get("estado") == "Sin artículo relacionado" for item in ingredients),
            "conversion_pendiente": sum(item.get("estado") == "Conversión pendiente" for item in ingredients),
        }

    @staticmethod
    def _collect_subelaborations(node: dict[str, Any], task: dict[str, Any], aggregated: dict[tuple[str, str], dict[str, Any]]) -> None:
        for component in node.get("componentes") or []:
            if component.get("tipo") != "elaboracion":
                continue
            key = (str(component.get("receta_referenciada_id") or component.get("nombre")), str(component.get("unidad") or "u"))
            current = aggregated.setdefault(key, {
                "elaboracion_id": component.get("receta_referenciada_id"), "nombre": component.get("nombre"),
                "cantidad_a_producir": 0.0, "unidad": component.get("unidad") or "u", "origenes": [],
            })
            current["cantidad_a_producir"] = round(float(current["cantidad_a_producir"]) + float(component.get("cantidad_necesaria") or 0), 6)
            current["origenes"].append({"elaboracion_id": task.get("receta_id"), "nombre": task.get("titulo"), "cantidad": component.get("cantidad_necesaria")})
            MenuProduccionService._collect_subelaborations(component.get("detalle") or {}, task, aggregated)
