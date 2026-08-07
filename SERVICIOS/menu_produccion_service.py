from __future__ import annotations

from datetime import datetime
from typing import Any

from MODELOS.produccion_real import PlanProduccionReal, TareaProduccionReal
from SERVICIOS.menu_necesidades_service import MenuNecesidadesService
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService
from SERVICIOS.produccion_stock_piloto_14 import ProduccionStockPiloto14


class MenuProduccionService:
    """Orquesta Menús, Producción Real y Stock sin duplicar sus reglas."""

    def __init__(self, core: Any) -> None:
        self.core = core
        self.menus = MenusInteligentesService(core.base_dir)
        self.necesidades = MenuNecesidadesService(core.base_dir, compras=core.compras)
        self.cierre = ProduccionStockPiloto14(core)

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
                task.requisitos_recursos["ingredientes"].append({
                    "nombre": line.get("articulo_nombre") or line.get("ingrediente_nombre"),
                    "articulo_id": line.get("articulo_id") or "", "cantidad": origin.get("cantidad") or 0,
                    "unidad": origin.get("unidad") or line.get("unidad_necesaria") or "u",
                    "disponible": line.get("stock_disponible"), "faltante": line.get("cantidad_faltante"),
                    "proveedor": line.get("proveedor_preferente"), "estado": line.get("estado"),
                    "factor_escalado": origin.get("factor_escalado") or 0,
                })
                total_need = float(line.get("cantidad_necesaria") or 0)
                share = float(origin.get("cantidad") or 0) / total_need if total_need else 0
                task.requisitos_recursos["coste_estimado"] = float(task.requisitos_recursos.get("coste_estimado") or 0) + float(line.get("coste_estimado") or 0) * share

        generated_at = datetime.now().isoformat(timespec="seconds")
        plan = PlanProduccionReal(
            nombre=f"Producción · {menu['nombre']}", fecha=str(body.get("fecha_servicio") or ""),
            evento_id=str(body.get("event_id") or ""), pax=int(menu["comensales"]), estado="borrador",
            tareas=list(tasks.values()), avisos=list(needs.get("warnings") or []),
            configuracion_planificacion={
                "generado_desde": "menu", "generated_at": generated_at, "menu_id": menu_id,
                "menu_version": int(menu["version"]), "errores_bloqueantes": production_errors,
            },
        )
        self.core.produccion_real.planes[plan.id] = plan
        self.core.produccion_real._persistir()
        return {"ok": True, "plan": self._project(plan), "idempotente": False, "stock_modificado": False}

    def obtener(self, plan_id: str) -> dict[str, Any]:
        return {"ok": True, "plan": self._project(self.core.produccion_real.obtener_plan(plan_id))}

    def consumo_previsto(self, plan_id: str, tarea_id: str) -> dict[str, Any]:
        return {"ok": True, "consumo_previsto": self.cierre.preparar_cierre(plan_id, tarea_id), "stock_modificado": False}

    def confirmar(self, plan_id: str, tarea_id: str, body: dict[str, Any]) -> dict[str, Any]:
        if body.get("confirmacion") != "CONFIRMAR_PRODUCCION_TERMINADA":
            return {"ok": False, "error": {"status": 400, "code": "confirmation_required", "message": "Confirma explícitamente la producción terminada."}}
        plan = self.core.produccion_real.obtener_plan(plan_id)
        blockers = list(plan.configuracion_planificacion.get("errores_bloqueantes") or [])
        if blockers:
            return {"ok": False, "error": {"status": 400, "code": "production_plan_blocked", "message": "El plan contiene errores bloqueantes."}, "errores_bloqueantes": blockers}
        result = self.cierre.cerrar_y_actualizar_stock(plan_id, tarea_id, str(body.get("usuario") or "web"), str(body.get("lote") or ""))
        if result.get("estado") == "YA_REGISTRADA":
            return {"ok": True, "resultado": result, "plan": self._project(plan), "stock_modificado": False, "idempotente": True}
        if not result.get("ok"):
            status = 409 if result.get("estado") == "STOCK_INSUFICIENTE" else 400
            return {"ok": False, "error": {"status": status, "code": str(result.get("estado") or "production_failed").lower(), "message": result.get("mensaje")}, "resultado": result}
        return {"ok": True, "resultado": result, "plan": self._project(self.core.produccion_real.obtener_plan(plan_id)), "stock_modificado": True, "idempotente": False}

    @staticmethod
    def _project(plan: PlanProduccionReal) -> dict[str, Any]:
        data = plan.to_dict()
        for task in data["tareas"]:
            task["ingredientes"] = list((task.get("requisitos_recursos") or {}).get("ingredientes") or [])
            resources = task.get("requisitos_recursos") or {}
            factors = [float(x.get("factor_escalado") or 0) for x in task["ingredientes"]]
            task["factor_escalado"] = float(resources.get("factor_escalado") or max(factors, default=0))
            task["rendimiento_base"] = float(resources.get("rendimiento_base") or (task["cantidad"] / task["factor_escalado"] if task["factor_escalado"] else 0))
            task["cantidad_a_producir"] = task["cantidad"]
            task["subelaboraciones"] = resources.get("arbol_subelaboraciones") or {}
            task["coste_estimado"] = round(float(resources.get("coste_estimado") or 0), 2)
        ingredients = [item for task in data["tareas"] for item in task["ingredientes"]]
        config = data.get("configuracion_planificacion") or {}
        data.update({
            "plan_id": plan.id, "menu_id": config.get("menu_id"), "menu_version": config.get("menu_version"),
            "comensales": plan.pax, "elaboraciones": data["tareas"], "ingredientes": ingredients,
            "advertencias": data.get("avisos") or [], "errores_bloqueantes": config.get("errores_bloqueantes") or [],
            "generated_at": config.get("generated_at") or plan.creado_en,
            "resumen": {"elaboraciones": len(data["tareas"]), "ingredientes": len(ingredients), "faltantes": sum(1 for x in ingredients if float(x.get("faltante") or 0) > 0), "bloqueadas": len(config.get("errores_bloqueantes") or [])},
        })
        return data
