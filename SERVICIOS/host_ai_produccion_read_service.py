from __future__ import annotations

from datetime import date
from typing import Any
import unicodedata


class HostAIProduccionReadService:
    """Adaptador estricto de solo lectura sobre MotorProduccionReal."""

    CONSULTAS = {"pendientes", "en_curso", "hoy", "bloqueadas", "terminadas", "buscar"}
    ACTIVAS = {"en_proceso", "en_preparacion", "en_espera"}

    def __init__(self, core: Any) -> None:
        self.motor = core.produccion_real

    def consultar(self, consulta: str, termino: str = "", fecha: str | None = None, limite: int = 10) -> dict[str, Any]:
        query = str(consulta or "pendientes").strip().lower()
        if query not in self.CONSULTAS:
            query = "pendientes"
        term = " ".join(str(termino or "").split()).strip()
        target_date = str(fecha or date.today().isoformat()) if query == "hoy" else None
        limit = max(1, min(10, int(limite or 10)))
        rows: list[dict[str, Any]] = []
        summaries: list[dict[str, Any]] = []

        for plan in list(self.motor.listar_planes() or []):
            plan_id = str(plan.get("id") or "")
            if not plan_id:
                continue
            summary = dict(self.motor.resumen_ejecucion(plan_id) or {})
            summaries.append(summary)
            config = dict(plan.get("configuracion_planificacion") or {})
            for task in list(summary.get("tareas") or []):
                row = self._project(plan, config, task)
                if self._matches(query, row, term, target_date):
                    rows.append(row)

        state = "OK"
        if query == "buscar":
            rows, state = self._resolve_search(rows, term)
        elif not rows:
            state = "VACIO"
        total = len(rows)
        return {
            "estado": state,
            "consulta": query,
            "termino": term,
            "fecha": target_date,
            "total_encontrados": total,
            "resultados": rows[:limit],
            "resumen": self._summary(summaries),
            "fuente": "produccion_real_canonica",
            "solo_lectura": True,
            "datos_reales_modificados": False,
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
    def _summary(summaries: list[dict[str, Any]]) -> dict[str, int]:
        states = [dict(item.get("estados") or {}) for item in summaries]
        return {
            "planes": len(summaries),
            "tareas": sum(int(item.get("total_tareas") or 0) for item in summaries),
            "pendientes": sum(len(list(item.get("tareas_pendientes") or [])) for item in summaries),
            "en_curso": sum(int(item.get("en_curso") or 0) for item in states),
            "bloqueadas": sum(int(item.get("bloqueada") or 0) for item in states),
            "finalizadas": sum(int(item.get("finalizada") or 0) for item in states),
        }

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
        return "".join(char for char in text if not unicodedata.combining(char))


__all__ = ["HostAIProduccionReadService"]
