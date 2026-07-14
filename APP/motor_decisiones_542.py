from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.motor_decisiones_542 import tomar_decisiones_operativas_542, formatear_decisiones_542


if __name__ == "__main__":
    evento = {
        "tipo": "boda",
        "personas": 180,
        "fecha": "sabado",
        "hora_servicio": "15:00",
        "menu": "paella",
        "lugar": "Restaurante",
        "restricciones": "sin restricciones",
        "objetivo": "todo el flujo completo",
    }
    contexto = {
        "stock": [{"nombre": "arroz bomba", "disponible": 12, "necesario": 18, "unidad": "kg"}],
        "personal": {"disponibles": 2, "necesarios": 3},
        "proveedores": [{"nombre": "Makro", "disponible": False}],
    }
    print(formatear_decisiones_542(tomar_decisiones_operativas_542(evento, contexto)))
