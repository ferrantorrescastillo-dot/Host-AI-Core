from __future__ import annotations

from datetime import date
from typing import Any
import unicodedata


class HostAIProduccionReadService:
    """Adaptador estricto de solo lectura sobre MotorProduccionReal."""

    CONSULTAS = {"pendientes", "en_curso", "hoy", "bloqueadas", "terminadas", "buscar"}
    ACTIVAS = {"en_proceso", "en_preparacion", "en_espera"}

    def __init__(self, core: Any, menus_read_service: Any | None = None) -> None:
        self.motor = core.produccion_real
        self.menus_read_service = menus_read_service

    def consultar(self, consulta: str, termino: str = "", fecha: str | None = None, limite: int = 10,
                  plan_id: str = "", menu_id: str = "") -> dict[str, Any]:
        query = str(consulta or "pendientes").strip().lower()
        if query not in self.CONSULTAS:
            query = "pendientes"
        term = " ".join(str(termino or "").split()).strip()
        target_date = str(fecha or date.today().isoformat()) if query == "hoy" else None
        limit = max(1, min(10, int(limite or 10)))
        identity = str(plan_id or "").strip()
        menu_identity = str(menu_id or "").strip()
        plans = [dict(item) for item in list(self.motor.listar_planes() or []) if str((item or {}).get("id") or "")]
        selected, selection_state, resolved_by = self._resolve_plans(
            plans, query=query, term=term, plan_id=identity, menu_id=menu_identity,
        )
        scoped_plans = selected if selected is not None else plans
        rows: list[dict[str, Any]] = []
        summaries: list[dict[str, Any]] = []

        for plan in scoped_plans:
            plan_id = str(plan.get("id") or "")
            if not plan_id:
                continue
            summary = dict(self.motor.resumen_ejecucion(plan_id) or {})
            summaries.append(summary)
            config = dict(plan.get("configuracion_planificacion") or {})
            for task in list(summary.get("tareas") or []):
                row = self._project(plan, config, task)
                if (query == "buscar" and selected is not None) or self._matches(query, row, term, target_date):
                    rows.append(row)

        state = selection_state or "OK"
        if selection_state in {"NO_ENCONTRADO", "AMBIGUO"}:
            rows = []
        elif query == "buscar" and selected is None:
            rows, state = self._resolve_search(rows, term)
        elif not rows:
            state = "VACIO"
        total = len(rows)
        plan_candidates = [self._plan_summary(plan) for plan in list(selected or [])]
        selected_plan = plan_candidates[0] if len(plan_candidates) == 1 else None
        return {
            "estado": state,
            "consulta": query,
            "termino": term,
            "plan_id": identity or None,
            "menu_id": menu_identity or None,
            "ambito_resultados": "PLAN" if selected is not None else "GLOBAL",
            "resuelto_por": resolved_by,
            "plan": selected_plan,
            "candidatos": plan_candidates if state == "AMBIGUO" else [],
            "fecha": target_date,
            "total_encontrados": total,
            "resultados": rows[:limit],
            "resumen": self._summary(summaries),
            "fuente": "produccion_real_canonica",
            "solo_lectura": True,
            "datos_reales_modificados": False,
        }

    def _resolve_plans(self, plans: list[dict[str, Any]], *, query: str, term: str,
                       plan_id: str, menu_id: str) -> tuple[list[dict[str, Any]] | None, str | None, str | None]:
        if plan_id:
            matched = [plan for plan in plans if self._norm(plan.get("id")) == self._norm(plan_id)]
            return self._selection(matched, "PLAN_ID")
        if menu_id:
            matched = [plan for plan in plans if self._norm(self._plan_menu_id(plan)) == self._norm(menu_id)]
            return self._selection(matched, "MENU_ID")
        if query != "buscar" or not term:
            return None, None, None

        exact_id = [plan for plan in plans if self._norm(plan.get("id")) == self._norm(term)]
        if exact_id:
            return self._selection(exact_id, "PLAN_ID")
        exact_name = [plan for plan in plans if self._norm(plan.get("nombre")) == self._norm(term)]
        if exact_name:
            return self._selection(exact_name, "PLAN_NOMBRE")

        menu_result = self.menus_read_service.consultar(termino=term) if self.menus_read_service else {}
        if menu_result.get("estado") == "OK":
            resolved_menu_id = str((menu_result.get("menu") or {}).get("menu_id") or "")
            matched = [plan for plan in plans if self._plan_menu_id(plan) == resolved_menu_id]
            return self._selection(matched, "MENU_CANONICO")
        if menu_result.get("estado") == "AMBIGUO":
            menu_ids = {str(item.get("menu_id") or "") for item in list(menu_result.get("candidatos") or [])}
            matched = [plan for plan in plans if self._plan_menu_id(plan) in menu_ids]
            return self._selection(matched, "MENU_CANONICO")
        return None, None, None

    @staticmethod
    def _selection(plans: list[dict[str, Any]], source: str) -> tuple[list[dict[str, Any]], str, str]:
        if not plans:
            return [], "NO_ENCONTRADO", source
        return plans, "OK" if len(plans) == 1 else "AMBIGUO", source

    @staticmethod
    def _plan_menu_id(plan: dict[str, Any]) -> str:
        return str((plan.get("configuracion_planificacion") or {}).get("menu_id") or "")

    @classmethod
    def _plan_summary(cls, plan: dict[str, Any]) -> dict[str, Any]:
        config = dict(plan.get("configuracion_planificacion") or {})
        return {
            "plan_id": str(plan.get("id") or ""),
            "nombre": str(plan.get("nombre") or ""),
            "estado": str(plan.get("estado") or "") or None,
            "fecha": str(plan.get("fecha") or "") or None,
            "origen": str(config.get("generado_desde") or "") or None,
            "menu_id": str(config.get("menu_id") or "") or None,
            "menu_version": config.get("menu_version") if config.get("menu_version") is not None else None,
        }

    def _matches(self, query: str, row: dict[str, Any], term: str, target_date: str | None) -> bool:
        state = str(row.get("estado") or "")
        if query == "pendientes":
            return state not in {"finalizada", "cancelada"}
        if query == "en_curso":
            return state in self.ACTIVAS
        if query == "hoy":
            return bool(target_date and row.get("fecha") == target_date)
        if query == "bloqueadas":
            return state == "bloqueada" or bool(row.get("bloqueo"))
        if query == "terminadas":
            return state == "finalizada"
        if query == "buscar":
            needle = self._norm(term)
            return bool(needle and any(needle in self._norm(row.get(key)) for key in ("tarea_id", "titulo", "receta_id", "receta", "origen")))
        return False

    def _resolve_search(self, rows: list[dict[str, Any]], term: str) -> tuple[list[dict[str, Any]], str]:
        if not rows:
            return [], "NO_ENCONTRADO"
        needle = self._norm(term)
        exact_id = [r for r in rows if needle == self._norm(r.get("tarea_id")) or needle == self._norm(r.get("receta_id"))]
        exact_name = [r for r in rows if needle == self._norm(r.get("titulo")) or needle == self._norm(r.get("receta"))]
        selected = exact_id or exact_name
        if len(selected) == 1:
            return selected, "OK"
        if len(selected) > 1:
            return selected, "AMBIGUO"
        return (rows, "OK") if len(rows) == 1 else (rows, "AMBIGUO")

    @staticmethod
    def _project(plan: dict[str, Any], config: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
        def nullable(key: str) -> Any:
            value = task.get(key)
            return value if value not in ("", None) else None

        return {
            "plan_id": str(plan.get("id") or ""),
            "plan_nombre": str(plan.get("nombre") or ""),
            "fecha": str(plan.get("fecha") or "") or None,
            "estado_plan": str(plan.get("estado") or "") or None,
            "evento_id": str(plan.get("evento_id") or "") or None,
            "evento": str(plan.get("evento") or "") or None,
            "menu_id": str(config.get("menu_id") or "") or None,
            "menu_version": config.get("menu_version") if config.get("menu_version") is not None else None,
            "tarea_id": str(task.get("id") or ""),
            "titulo": str(task.get("titulo") or ""),
            "receta_id": str(task.get("receta_id") or "") or None,
            "receta": str(task.get("receta") or "") or None,
            "origen": str(task.get("origen") or "") or None,
            "cantidad": nullable("cantidad"),
            "unidad": nullable("unidad"),
            "estado": str(task.get("estado_ejecucion") or "") or None,
            "prioridad": nullable("prioridad"),
            "progreso": nullable("porcentaje_avance"),
            "responsable": nullable("responsable"),
            "bloqueo": nullable("bloqueo"),
            "retraso_min": nullable("retraso_min"),
            "duracion_prevista_min": nullable("tiempo_previsto_min"),
            "duracion_real_min": nullable("tiempo_real_min"),
            "duracion_restante_min": nullable("tiempo_restante_estimado_min"),
            "incidencias": list(task.get("incidencias") or []),
        }

    @staticmethod
    def _summary(summaries: list[dict[str, Any]]) -> dict[str, Any]:
        states = [dict(item.get("estados") or {}) for item in summaries]
        principal: dict[str, int] = {}
        blocked = 0
        open_tasks = 0
        for summary in summaries:
            for task in list(summary.get("tareas") or []):
                state = str(task.get("estado_ejecucion") or "pendiente")
                principal[state] = principal.get(state, 0) + 1
                if state not in {"finalizada", "cancelada"}:
                    open_tasks += 1
                if state == "bloqueada" or bool(str(task.get("bloqueo") or "").strip()):
                    blocked += 1
        return {
            "planes": len(summaries),
            "tareas": sum(int(item.get("total_tareas") or 0) for item in summaries),
            "pendientes": open_tasks,
            "en_curso": sum(int(item.get("en_curso") or 0) for item in states),
            "bloqueadas": blocked,
            "finalizadas": sum(int(item.get("finalizada") or 0) for item in states),
            "por_estado_principal": principal,
            "indicadores_transversales": {"bloqueadas": blocked},
            "semantica_contadores": {
                "pendientes": "tareas abiertas no finalizadas ni canceladas",
                "en_curso": "subconjunto de pendientes en ejecución",
                "bloqueadas": "indicador transversal; puede solaparse con pendientes",
            },
        }

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
        plain = "".join(char for char in text if not unicodedata.combining(char))
        return " ".join("".join(char if char.isalnum() else " " for char in plain).split())


__all__ = ["HostAIProduccionReadService"]
