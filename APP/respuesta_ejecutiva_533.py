from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.ejecutor_flujo_operativo_532 import ejecutar_flujo_operativo
from SERVICIOS.respuesta_ejecutiva_533 import generar_respuesta_ejecutiva_evento


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
    ejecucion = ejecutar_flujo_operativo(flujo, confirmar=False)
    respuesta = generar_respuesta_ejecutiva_evento(flujo, ejecucion)
    print(respuesta["mensaje"])


if __name__ == "__main__":
    main()
