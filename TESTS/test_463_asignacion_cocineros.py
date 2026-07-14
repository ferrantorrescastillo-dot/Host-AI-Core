from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from SERVICIOS.asignacion_cocineros_463 import AsignadorCocineros463

def main():
    datos = [{"nombre":"Fondo", "tiempo_activo_min":45}, {"nombre":"Romesco", "tiempo_activo_min":55}, {"nombre":"Croquetas", "tiempo_activo_min":90}]
    r = AsignadorCocineros463().asignar(datos, cocineros=2)
    assert r["version"] == "4.6.3"
    assert r["total_asignaciones"] == 3
    assert len(r["carga_por_cocinero_min"]) == 2
    assert {a["regla_continuidad"] for a in r["asignaciones"]} == {"quien_empieza_intenta_terminar"}
    print("TEST OK - Host AI 4.6.3 Asignación inteligente de cocineros")
if __name__ == "__main__": main()
