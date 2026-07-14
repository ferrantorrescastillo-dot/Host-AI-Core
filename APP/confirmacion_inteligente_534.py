from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.confirmacion_inteligente_534 import analizar_confirmaciones_flujo


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
    resultado = analizar_confirmaciones_flujo(flujo)
    print(resultado["mensaje"])


if __name__ == "__main__":
    main()
