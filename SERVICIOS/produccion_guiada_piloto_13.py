from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from SERVICIOS.produccion_stock_piloto_14 import ProduccionStockPiloto14


ESTADOS_TERMINADOS = {"finalizada", "completada", "cancelada"}
ESTADOS_ACTIVOS = {"en_curso", "en_proceso", "en_preparacion", "en_espera", "incidencia"}
ESTADOS_PAUSADOS = {"pausada"}


@dataclass(frozen=True)
class AccionGuiada:
    codigo: str
    texto: str
    explicacion: str
    tarea_id: str = ""


class ProduccionGuiadaPiloto13:
    """Capa operativa del piloto para ejecutar producción sin duplicar motores.

    Lee y acciona exclusivamente a través de ``core.produccion_real``. Su misión
    es traducir el seguimiento técnico existente a decisiones simples de cocina.
    """

    VERSION = "PILOTO-1.3"

    def __init__(self, core: Any):
        self.core = core
        self.motor = core.produccion_real
        self.produccion_stock = ProduccionStockPiloto14(core) if hasattr(core, "stock") else None

    def listar_planes_operativos(self) -> list[dict[str, Any]]:
        planes = list(self.motor.listar_planes())
        validos = [p for p in planes if p.get("tareas") and str(p.get("estado", "")).lower() not in {"finalizado", "cancelado"}]
        return sorted(validos, key=lambda p: (self._orden_plan(p), str(p.get("fecha") or "9999-99-99"), str(p.get("nombre") or "")))

    def construir_panel(self, plan_id: str) -> dict[str, Any]:
        plan = self.motor.obtener_plan(plan_id).to_dict()
        resumen = self.motor.resumen_ejecucion(plan_id)
        tareas = [self._humanizar_tarea(t, plan) for t in resumen.get("tareas", [])]
        tareas.sort(key=lambda t: self._orden_tarea(t))
        siguiente = self._siguiente_accion(plan_id, tareas)
        recomendacion_motor = self._recomendacion_motor(plan_id, tareas)
        bloqueadas = [t for t in tareas if t.get("bloqueo")]
        activas = [t for t in tareas if t.get("estado_codigo") == "en_curso"]
        pendientes = [t for t in tareas if t.get("estado_codigo") not in ESTADOS_TERMINADOS]
        return {
            "version": self.VERSION,
            "plan_id": plan_id,
            "plan": plan.get("nombre") or plan.get("evento") or "Producción",
            "fecha": plan.get("fecha", ""),
            "estado_plan": resumen.get("estado_plan", plan.get("estado", "")),
            "avance": resumen.get("porcentaje_completado", 0),
            "total_tareas": resumen.get("total_tareas", len(tareas)),
            "pendientes": len(pendientes),
            "en_curso": len(activas),
            "bloqueadas": len(bloqueadas),
            "alertas": list(resumen.get("alertas", [])),
            "tareas": tareas,
            "siguiente_accion": siguiente.__dict__,
            "recomendacion_motor": recomendacion_motor,
            "lectura": self._lectura_general(tareas, siguiente),
        }

    def iniciar(self, plan_id: str, tarea_id: str) -> dict[str, Any]:
        return self.motor.iniciar_tarea(plan_id, tarea_id)

    def pausar(self, plan_id: str, tarea_id: str) -> dict[str, Any]:
        return self.motor.pausar_tarea(plan_id, tarea_id)

    def reanudar(self, plan_id: str, tarea_id: str) -> dict[str, Any]:
        return self.motor.reanudar_tarea(plan_id, tarea_id)

    def finalizar(self, plan_id: str, tarea_id: str) -> dict[str, Any]:
        return self.motor.finalizar_tarea(plan_id, tarea_id)

    def finalizar_con_stock(self, plan_id: str, tarea_id: str, operario: str = "cocina", lote: str = "") -> dict[str, Any]:
        if self.produccion_stock is None:
            raise ValueError("El núcleo no tiene módulo de stock disponible para cierre transaccional.")
        return self.produccion_stock.cerrar_y_actualizar_stock(plan_id, tarea_id, operario=operario, lote=lote)

    def actualizar_avance(self, plan_id: str, tarea_id: str, porcentaje: float) -> dict[str, Any]:
        return self.motor.actualizar_progreso_tarea(plan_id, tarea_id, porcentaje)

    def registrar_incidencia(self, plan_id: str, tarea_id: str, descripcion: str, bloqueo: bool = False, retraso_min: int = 0) -> dict[str, Any]:
        tipo = "bloqueo" if bloqueo else "incidencia"
        efecto = "pausa" if bloqueo else "no_bloquea"
        return self.motor.registrar_incidencia_tarea(plan_id, tarea_id, tipo, descripcion, retraso_min, "media", efecto, "", "")

    def registrar_merma(self, plan_id: str, tarea_id: str, cantidad: float, unidad: str, motivo: str = "") -> dict[str, Any]:
        return self.motor.registrar_merma_tarea(plan_id, tarea_id, cantidad, unidad, motivo=motivo)

    def cambiar_fase(self, plan_id: str, tarea_id: str, fase_id: str = "", observaciones: str = "") -> dict[str, Any]:
        return self.motor.cambiar_fase_tarea(plan_id, tarea_id, fase_id=fase_id, observaciones=observaciones)

    def resolver_bloqueo(self, plan_id: str, tarea_id: str, observacion: str = "") -> dict[str, Any]:
        return self.motor.resolver_bloqueo_tarea(plan_id, tarea_id, observacion)

    def resumen_vivo(self, plan_id: str) -> dict[str, Any]:
        panel = self.construir_panel(plan_id)
        siguiente = panel.get("siguiente_accion", {})
        tarea = siguiente.get("tarea_id")
        return {
            "plan_id": plan_id,
            "plan": panel.get("plan"),
            "progreso": panel.get("avance", 0),
            "pendientes": panel.get("pendientes", 0),
            "en_curso": panel.get("en_curso", 0),
            "bloqueadas": panel.get("bloqueadas", 0),
            "siguiente_tarea_id": tarea,
            "siguiente_accion": siguiente.get("texto", ""),
            "siguiente_explicacion": siguiente.get("explicacion", ""),
            "lectura": panel.get("lectura", ""),
        }

    def _humanizar_tarea(self, tarea: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        estado = str(tarea.get("estado_ejecucion") or "pendiente").lower()
        prioridad = int(tarea.get("prioridad", 50) or 50)
        asignaciones = (plan.get("asignacion_recursos") or {}).get("asignaciones", []) or []
        asignacion = next((a for a in asignaciones if str(a.get("datos", {}).get("tarea_id") or a.get("clave") or "") == str(tarea.get("id") or "")), {})
        responsable = asignacion.get("cocinero") or next((f.get("responsable") for f in tarea.get("fases", []) if f.get("responsable")), "Sin asignar")
        recurso = asignacion.get("recurso") or next((f.get("recurso") for f in tarea.get("fases", []) if f.get("recurso")), "")
        restante = int(float(tarea.get("tiempo_restante_estimado_min", 0) or 0))
        real = int(float(tarea.get("tiempo_real_min", 0) or 0))
        return {
            **tarea,
            "estado_codigo": estado,
            "estado_texto": self._estado_texto(estado, bool(tarea.get("bloqueo"))),
            "prioridad_texto": self._prioridad_texto(prioridad),
            "responsable_texto": str(responsable).replace("_", " "),
            "recurso_texto": str(recurso).replace("_", " ") if recurso else "Sin recurso específico",
            "tiempo_restante_texto": self._hm(restante),
            "tiempo_real_texto": self._hm(real),
            "puede_iniciar": estado in {"pendiente", "retrasada", "lista", "en_espera", "incidencia"} and not tarea.get("bloqueo"),
            "puede_pausar": estado in ESTADOS_ACTIVOS,
            "puede_reanudar": estado == "pausada" and not tarea.get("bloqueo"),
            "puede_finalizar": estado not in ESTADOS_TERMINADOS and not tarea.get("bloqueo"),
        }

    def _siguiente_accion(self, plan_id: str, tareas: list[dict[str, Any]]) -> AccionGuiada:
        bloqueada = next((t for t in tareas if t.get("bloqueo")), None)
        if bloqueada:
            return AccionGuiada("RESOLVER_BLOQUEO", f"Resuelve el bloqueo de {bloqueada.get('titulo')}", str(bloqueada.get("bloqueo")), str(bloqueada.get("id")))
        activa = next((t for t in tareas if t.get("estado_codigo") in ESTADOS_ACTIVOS), None)
        if activa:
            return AccionGuiada("CONTINUAR", f"Continúa con {activa.get('titulo')}", "Ya está en marcha; conviene terminarla antes de abrir otra elaboración.", str(activa.get("id")))
        pausada = next((t for t in tareas if t.get("estado_codigo") == "pausada"), None)
        if pausada:
            return AccionGuiada("REANUDAR", f"Reanuda {pausada.get('titulo')}", "La tarea quedó pausada y todavía no está terminada.", str(pausada.get("id")))
        if hasattr(self.motor, "siguiente_tarea_recomendada"):
            recomendacion = self.motor.siguiente_tarea_recomendada(plan_id)
            if recomendacion.get("codigo") == "SUGERIDA" and recomendacion.get("tarea_id"):
                tarea_id = str(recomendacion.get("tarea_id"))
                tarea = next((t for t in tareas if str(t.get("id")) == tarea_id), None)
                if tarea and tarea.get("estado_codigo") not in ESTADOS_TERMINADOS:
                    return AccionGuiada(
                        "INICIAR",
                        f"Empieza por {tarea.get('titulo')}",
                        self._explicacion_culinaria(recomendacion, tarea),
                        tarea_id,
                    )
        pendiente = next((t for t in tareas if t.get("estado_codigo") not in ESTADOS_TERMINADOS), None)
        if pendiente:
            return AccionGuiada("INICIAR", f"Empieza por {pendiente.get('titulo')}", f"Es la siguiente tarea por prioridad: {pendiente.get('prioridad_texto')}.", str(pendiente.get("id")))
        return AccionGuiada("FINALIZADO", "La producción está terminada", "No quedan tareas abiertas en este plan.")

    def _recomendacion_motor(self, plan_id: str, tareas: list[dict[str, Any]]) -> dict[str, str]:
        if not hasattr(self.motor, "siguiente_tarea_recomendada"):
            return {}
        recomendacion = self.motor.siguiente_tarea_recomendada(plan_id)
        if recomendacion.get("codigo") != "SUGERIDA" or not recomendacion.get("tarea_id"):
            return {}
        tarea_id = str(recomendacion.get("tarea_id"))
        tarea = next((t for t in tareas if str(t.get("id")) == tarea_id), None)
        if not tarea:
            return {}
        return {
            "tarea_id": tarea_id,
            "texto": f"Empieza por {tarea.get('titulo')}",
            "explicacion": self._explicacion_culinaria(recomendacion, tarea),
        }

    @staticmethod
    def _explicacion_culinaria(recomendacion: dict[str, Any], tarea: dict[str, Any]) -> str:
        criterios = [str(x).strip() for x in (recomendacion.get("criterios") or []) if str(x).strip()]
        if not criterios and str(recomendacion.get("motivo") or "").strip():
            criterios = [str(recomendacion.get("motivo")).strip()]
        if not criterios:
            return "Es la mejor opción operativa disponible para avanzar la jornada sin perder control."
        encabezado = f"Se recomienda {tarea.get('titulo')} porque:"
        detalle = "\n".join(f"- {criterio}" for criterio in criterios)
        return f"{encabezado}\n{detalle}"

    @staticmethod
    def _orden_plan(plan: dict[str, Any]) -> int:
        estados = {"en_produccion": 0, "pausado": 1, "planificado": 2, "pendiente": 3, "borrador": 4}
        return estados.get(str(plan.get("estado", "")).lower(), 5)

    @staticmethod
    def _orden_tarea(t: dict[str, Any]) -> tuple[int, int, str]:
        estado = t.get("estado_codigo")
        if t.get("bloqueo"): grupo = 0
        elif estado == "en_curso": grupo = 1
        elif estado == "pausada": grupo = 2
        elif estado in ESTADOS_TERMINADOS: grupo = 4
        else: grupo = 3
        return grupo, -int(t.get("prioridad", 50) or 50), str(t.get("titulo") or "")

    @staticmethod
    def _estado_texto(estado: str, bloqueo: bool) -> str:
        if bloqueo: return "🔴 Bloqueada"
        return {
            "pendiente": "⚪ Pendiente", "lista": "🟢 Lista", "en_curso": "🟠 En marcha",
            "en_preparacion": "🟠 En preparación", "en_proceso": "🟠 En proceso", "en_espera": "🟣 En espera", "incidencia": "🟤 Incidencia",
            "pausada": "🟡 Pausada",
            "finalizada": "✅ Terminada", "completada": "✅ Terminada", "retrasada": "🔴 Retrasada",
            "cancelada": "⚫ Cancelada",
        }.get(estado, estado.replace("_", " ").capitalize())

    @staticmethod
    def _prioridad_texto(prioridad: int) -> str:
        if prioridad >= 90: return "Muy urgente"
        if prioridad >= 70: return "Alta"
        if prioridad >= 40: return "Normal"
        return "Puede esperar"

    @staticmethod
    def _hm(minutes: int) -> str:
        h, m = divmod(max(0, int(minutes)), 60)
        if h and m: return f"{h} h {m} min"
        if h: return f"{h} h"
        return f"{m} min"

    @staticmethod
    def _lectura_general(tareas: list[dict[str, Any]], siguiente: AccionGuiada) -> str:
        abiertas = [t for t in tareas if t.get("estado_codigo") not in ESTADOS_TERMINADOS]
        if not abiertas:
            return "La producción está terminada. Revisa el cierre antes de abandonar el plan."
        return f"Quedan {len(abiertas)} tarea(s) abiertas. {siguiente.texto}."


def formatear_diagnostico_piloto13(d: dict[str, Any]) -> str:
    return "\n".join([
        "PILOTO-1.3 — PRODUCCIÓN GUIADA",
        "=" * 78,
        f"Diagnóstico: {d.get('diagnostico')} | Planes: {d.get('planes')} | Tareas: {d.get('tareas')}",
        f"Siguiente acción: {d.get('accion')} | Escrituras delegadas al motor existente: SÍ",
        "-" * 78,
        "Se validaron selección del siguiente trabajo, estados humanos, tiempos legibles y delegación de acciones.",
    ])


__all__ = ["ProduccionGuiadaPiloto13", "AccionGuiada", "formatear_diagnostico_piloto13"]
