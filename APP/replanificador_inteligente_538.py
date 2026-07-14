from __future__ import annotations

from SERVICIOS.detector_incidencias_537 import detectar_incidencias_operativas
from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.planificador_inteligente_535 import planificar_ejecucion_inteligente
from SERVICIOS.priorizador_tareas_536 import priorizar_tareas_operativas
from SERVICIOS.replanificador_inteligente_538 import formatear_replanificacion, replanificar_operativa_inteligente


def main() -> None:
    datos = {
        "tipo": "boda", "personas": 180, "fecha": "sabado", "hora_servicio": "15:00",
        "menu": "menu boda", "lugar": "Mas Boronat", "restricciones": "sin restricciones", "objetivo": "flujo completo",
    }
    contexto = {
        "stock": [{"nombre": "arroz bomba", "disponible": 8, "necesario": 18, "unidad": "kg", "imprescindible": True}],
        "proveedores": [{"nombre": "Proveedor habitual", "disponible": False, "detalle": "No reparte mañana"}],
        "tareas": [{"nombre": "Marcar fondos", "requiere_responsable": True}],
    }
    flujo = generar_flujo_operativo_evento(datos)
    plan = planificar_ejecucion_inteligente(flujo)
    prioridades = priorizar_tareas_operativas(plan)
    incidencias = detectar_incidencias_operativas(plan, prioridades, contexto)
    replan = replanificar_operativa_inteligente(plan, incidencias, contexto)
    print(formatear_replanificacion(replan))


if __name__ == "__main__":
    main()
