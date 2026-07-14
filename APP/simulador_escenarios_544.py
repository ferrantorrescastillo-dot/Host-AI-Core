from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.simulador_escenarios_544 import simular_escenario_544, formatear_simulacion_544


if __name__ == "__main__":
    evento = {"tipo": "boda", "personas": 180, "fecha": "sabado", "hora_servicio": "15:00", "menu": "paella", "lugar": "Restaurante", "restricciones": "sin restricciones", "objetivo": "todo el flujo completo"}
    contexto = {
        "stock": [{"nombre": "arroz bomba", "disponible": 18, "necesario": 18, "unidad": "kg"}],
        "personal": {"disponibles": 3, "necesarios": 3},
        "proveedores": [{"nombre": "Makro", "disponible": True}],
    }
    print(formatear_simulacion_544(simular_escenario_544(evento, contexto, "que pasa si vienen +40 personas")))
