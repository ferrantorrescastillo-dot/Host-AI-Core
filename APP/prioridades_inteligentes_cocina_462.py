from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from SERVICIOS.prioridades_inteligentes_cocina_462 import MotorPrioridadesInteligentesCocina462

if __name__ == "__main__":
    datos = [{"nombre":"Fondo", "tiempo_activo_min":40, "tiempo_pasivo_min":240, "prioridad":"alta"}, {"nombre":"Vinagreta", "tiempo_activo_min":10, "prioridad":"normal"}]
    print(MotorPrioridadesInteligentesCocina462().ordenar_prioridades(datos)["lectura_host_ai"])
