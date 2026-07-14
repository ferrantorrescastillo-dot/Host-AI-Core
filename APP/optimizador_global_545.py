from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from SERVICIOS.optimizador_global_545 import optimizar_operacion_545, formatear_optimizacion_545


if __name__ == "__main__":
    evento = {"tipo": "boda", "personas": 180, "fecha": "sabado", "menu": "paella"}
    contexto = {
        "personal": {"disponibles": 2, "necesarios": 3},
        "stock": [{"articulo": "arroz bomba", "disponible": 8, "necesario": 18}],
        "recursos": [{"nombre": "horno", "estado": "ocupado", "conflicto": True}],
    }
    print(formatear_optimizacion_545(optimizar_operacion_545(evento, contexto)))
