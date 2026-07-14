from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.evaluador_alternativas_543 import evaluar_alternativas_543, formatear_alternativas_543


if __name__ == "__main__":
    evento = {"tipo": "boda", "personas": 180, "fecha": "sabado", "hora_servicio": "15:00", "menu": "paella", "lugar": "Restaurante", "restricciones": "sin restricciones", "objetivo": "todo el flujo completo"}
    contexto = {
        "stock": [{"nombre": "arroz bomba", "disponible": 12, "necesario": 18, "unidad": "kg"}],
        "personal": {"disponibles": 2, "necesarios": 3},
        "proveedores": [{"nombre": "Makro", "disponible": False}],
    }
    print(formatear_alternativas_543(evaluar_alternativas_543(evento, contexto)))
