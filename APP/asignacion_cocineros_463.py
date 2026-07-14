from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from SERVICIOS.asignacion_cocineros_463 import AsignadorCocineros463

if __name__ == "__main__":
    datos = [{"nombre":"Fondo", "tiempo_activo_min":40}, {"nombre":"Romesco", "tiempo_activo_min":55}, {"nombre":"Croquetas", "tiempo_activo_min":90}]
    print(AsignadorCocineros463().asignar(datos)["lectura_host_ai"])
