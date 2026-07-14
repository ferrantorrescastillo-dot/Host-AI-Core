from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.analizador_situacion_541 import analizar_situacion_operativa_541, formatear_situacion_541


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
        "recursos": [{"nombre": "horno 1", "estado": "ocupado", "detalle": "ocupado hasta las 12"}],
        "proveedores": [{"nombre": "Makro", "disponible": False, "detalle": "sin reparto mañana"}],
    }
    print(formatear_situacion_541(analizar_situacion_operativa_541(evento, contexto)))
