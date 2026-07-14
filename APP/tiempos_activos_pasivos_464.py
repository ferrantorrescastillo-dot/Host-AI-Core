from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from SERVICIOS.tiempos_activos_pasivos_464 import GestorTiemposActivosPasivos464

if __name__ == "__main__":
    datos = [{"nombre":"Pan", "pasos":[{"tipo":"amasado", "duracion_min":20}, {"tipo":"fermentación", "duracion_min":90}]}]
    print(GestorTiemposActivosPasivos464().normalizar_elaboraciones(datos)["lectura_host_ai"])
