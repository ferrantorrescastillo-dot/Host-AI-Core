from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from SERVICIOS.planificador_diario_produccion_461 import PlanificadorDiarioProduccion461

DEMO = [
    {"nombre":"Fondo oscuro", "tiempo_activo_min":45, "tiempo_pasivo_min":240, "recursos":["olla"], "prioridad":"critica"},
    {"nombre":"Carrilleras", "tiempo_activo_min":110, "tiempo_pasivo_min":180, "recursos":["horno"], "prioridad":"alta", "dependencias":["Fondo oscuro"]},
    {"nombre":"Romesco", "tiempo_activo_min":55, "tiempo_pasivo_min":20, "recursos":["robot"], "prioridad":"normal"},
]

if __name__ == "__main__":
    servicio = PlanificadorDiarioProduccion461(BASE_DIR)
    plan = servicio.planificar_dia(DEMO)
    print(plan["lectura_host_ai"])
    print(servicio.exportar_plan(plan)["lectura_host_ai"])
