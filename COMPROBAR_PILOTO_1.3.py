from __future__ import annotations

from types import SimpleNamespace

from SERVICIOS.produccion_guiada_piloto_13 import ProduccionGuiadaPiloto13, formatear_diagnostico_piloto13


class _Plan:
    def __init__(self, data): self.data = data
    def to_dict(self): return self.data


class _MotorDiagnostico:
    def __init__(self):
        self.plan = {"id":"PLAN-DIAG","nombre":"Producción diagnóstico","fecha":"2026-07-14","estado":"en_produccion","tareas":[{"id":"T1"},{"id":"T2"}],"asignacion_recursos":{"asignaciones":[{"clave":"T1","cocinero":"Cocinero 1","recurso":"horno"}]}}
        self.tareas = [
            {"id":"T1","titulo":"Asar carrilleras","estado_ejecucion":"en_curso","prioridad":90,"tiempo_real_min":30,"tiempo_restante_estimado_min":90,"fases":[],"bloqueo":"","checklist_pendiente":0},
            {"id":"T2","titulo":"Preparar guarnición","estado_ejecucion":"pendiente","prioridad":70,"tiempo_real_min":0,"tiempo_restante_estimado_min":45,"fases":[],"bloqueo":"","checklist_pendiente":0},
        ]
        self.acciones=[]
    def listar_planes(self): return [self.plan]
    def obtener_plan(self, _): return _Plan(self.plan)
    def resumen_ejecucion(self, _): return {"plan":self.plan["nombre"],"estado_plan":"en_produccion","porcentaje_completado":25,"total_tareas":2,"tareas":self.tareas,"alertas":[]}
    def iniciar_tarea(self,*a): self.acciones.append("iniciar"); return {}
    def pausar_tarea(self,*a): self.acciones.append("pausar"); return {}
    def reanudar_tarea(self,*a): self.acciones.append("reanudar"); return {}
    def finalizar_tarea(self,*a): self.acciones.append("finalizar"); return {}
    def actualizar_progreso_tarea(self,*a): self.acciones.append("avance"); return {}
    def registrar_incidencia_tarea(self,*a): self.acciones.append("incidencia"); return {}
    def resolver_bloqueo_tarea(self,*a): self.acciones.append("resolver"); return {}


def main() -> None:
    motor = _MotorDiagnostico()
    servicio = ProduccionGuiadaPiloto13(SimpleNamespace(produccion_real=motor))
    panel = servicio.construir_panel("PLAN-DIAG")
    servicio.pausar("PLAN-DIAG", "T1")
    servicio.actualizar_avance("PLAN-DIAG", "T2", 50)
    ok = (
        panel["version"] == "PILOTO-1.3"
        and panel["siguiente_accion"]["codigo"] == "CONTINUAR"
        and panel["tareas"][0]["tiempo_restante_texto"] == "1 h 30 min"
        and motor.acciones == ["pausar", "avance"]
    )
    d = {"diagnostico":"OK" if ok else "ERROR","planes":len(servicio.listar_planes_operativos()),"tareas":len(panel["tareas"]),"accion":panel["siguiente_accion"]["codigo"]}
    print(formatear_diagnostico_piloto13(d))
    if not ok: raise SystemExit(1)


if __name__ == "__main__": main()
