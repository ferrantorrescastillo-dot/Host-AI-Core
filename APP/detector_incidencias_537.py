from __future__ import annotations

from SERVICIOS.detector_incidencias_537 import detectar_incidencias_operativas, formatear_incidencias
from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.planificador_inteligente_535 import planificar_ejecucion_inteligente
from SERVICIOS.priorizador_tareas_536 import priorizar_tareas_operativas


def main() -> None:
    datos = {
        "tipo": "boda", "personas": 180, "fecha": "sabado", "hora_servicio": "15:00",
        "menu": "menu boda", "lugar": "Mas Boronat", "restricciones": "sin restricciones", "objetivo": "flujo completo",
    }
    contexto = {
        "stock": [{"nombre": "arroz bomba", "disponible": 8, "necesario": 18, "unidad": "kg", "imprescindible": True}],
        "recursos": [{"nombre": "horno 1", "estado": "ocupado", "detalle": "Reservado por otro evento"}],
        "personal": {"disponibles": 2, "necesarios": 3},
    }
    flujo = generar_flujo_operativo_evento(datos)
    plan = planificar_ejecucion_inteligente(flujo)
    prioridades = priorizar_tareas_operativas(plan)
    resultado = detectar_incidencias_operativas(plan, prioridades, contexto)
    print(formatear_incidencias(resultado))


if __name__ == "__main__":
    main()
