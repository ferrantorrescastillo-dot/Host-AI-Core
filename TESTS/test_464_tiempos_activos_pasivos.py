from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from SERVICIOS.tiempos_activos_pasivos_464 import GestorTiemposActivosPasivos464

def main():
    datos = [{"nombre":"Pan", "pasos":[{"tipo":"amasado", "duracion_min":20}, {"tipo":"fermentación", "duracion_min":90}, {"tipo":"horno", "duracion_min":25}]}]
    s = GestorTiemposActivosPasivos464()
    r = s.normalizar_elaboraciones(datos)
    assert r["version"] == "4.6.4"
    assert r["minutos_activos"] == 20
    assert r["minutos_pasivos"] == 115
    assert s.generar_bloques_tiempo(datos[0])[1]["requiere_cocinero"] is False
    print("TEST OK - Host AI 4.6.4 Gestión de tiempos activos y pasivos")
if __name__ == "__main__": main()
