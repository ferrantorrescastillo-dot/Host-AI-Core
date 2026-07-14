from __future__ import annotations

from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.planificador_inteligente_535 import formatear_plan_inteligente, planificar_ejecucion_inteligente


def main() -> None:
    datos = {
        "tipo": "boda",
        "personas": 180,
        "fecha": "sabado",
        "hora_servicio": "15:00",
        "menu": "menu boda",
        "lugar": "Mas Boronat",
        "restricciones": "sin restricciones",
        "objetivo": "flujo completo",
    }
    flujo = generar_flujo_operativo_evento(datos)
    plan = planificar_ejecucion_inteligente(flujo)
    print(formatear_plan_inteligente(plan))


if __name__ == "__main__":
    main()
