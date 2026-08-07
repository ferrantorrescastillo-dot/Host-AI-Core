from __future__ import annotations

from datetime import datetime
from typing import Any

from MODELOS.produccion_real import PlanProduccionReal, TareaProduccionReal
from SERVICIOS.menu_necesidades_service import MenuNecesidadesService
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService


class MenuProduccionService:
    """Orquesta Menús, Producción Real y Stock sin duplicar sus reglas."""

    def __init__(self, core: Any) -> None:
        self.core = core
        self.menus = MenusInteligentesService(core.base_dir)
        self.necesidades = MenuNecesidadesService(core.base_dir, compras=core.compras)

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

    @staticmethod
    def _project(plan: PlanProduccionReal) -> dict[str, Any]:
        data = plan.to_dict()
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
            MenuProduccionService._collect_subelaborations(task["subelaboraciones"], task, subelaboraciones)
        config = data.get("configuracion_planificacion") or {}
        ingredients = [{
            "nombre": item.get("articulo_nombre") or item.get("ingrediente_nombre"),
            "articulo_id": item.get("articulo_id") or "", "cantidad": item.get("cantidad_necesaria") or 0,
            "unidad": item.get("unidad_necesaria") or "u", "disponible": item.get("stock_disponible"),
            "faltante": item.get("cantidad_faltante"), "proveedor": item.get("proveedor_preferente"),
            "estado": item.get("estado"), "coste_estimado": item.get("coste_estimado"),
        } for item in config.get("ingredientes_agrupados") or [item for task in data["tareas"] for item in task["ingredientes"]]]
        blockers = config.get("errores_bloqueantes") or []
        missing = sum(1 for x in ingredients if float(x.get("faltante") or 0) > 0)
        data.update({
            "plan_id": plan.id, "menu_id": config.get("menu_id"), "menu_version": config.get("menu_version"),
            "comensales": plan.pax, "elaboraciones": data["tareas"], "ingredientes": ingredients,
            "subelaboraciones": list(subelaboraciones.values()),
            "advertencias": data.get("avisos") or [], "errores_bloqueantes": blockers,
            "generated_at": config.get("generated_at") or plan.creado_en,
            "estado": "BLOQUEADO" if blockers or missing else "LISTO",
            "resumen": {"elaboraciones": len(data["tareas"]), "subelaboraciones": len(subelaboraciones), "ingredientes": len(ingredients), "faltantes": missing, "bloqueadas": sum(x["estado"] == "BLOQUEADO" for x in data["tareas"]), "coste_previsto": round(sum(float(x.get("coste_estimado") or 0) for x in ingredients), 2)},
            "solo_planificacion": True, "stock_modificado": False,
        })
        return data

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
