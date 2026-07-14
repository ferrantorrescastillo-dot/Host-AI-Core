from pathlib import Path
import sys, tempfile
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from SERVICIOS.planificador_diario_produccion_461 import PlanificadorDiarioProduccion461

ELABORACIONES = [
    {"nombre":"Fondo oscuro", "tiempo_activo_min":45, "tiempo_pasivo_min":240, "recursos":["olla"], "prioridad":"critica"},
    {"nombre":"Carrilleras", "tiempo_activo_min":110, "tiempo_pasivo_min":180, "recursos":["horno"], "prioridad":"alta", "dependencias":["Fondo oscuro"]},
    {"nombre":"Romesco", "tiempo_activo_min":55, "tiempo_pasivo_min":20, "recursos":["robot"], "prioridad":"normal"},
]

def main():
    with tempfile.TemporaryDirectory() as tmp:
        s = PlanificadorDiarioProduccion461(tmp)
        r = s.planificar_dia(ELABORACIONES, cocineros=3)
        assert r["version"] == "4.6.1"
        assert r["total_elaboraciones"] == 3
        assert r["minutos_activos"] == 210
        assert any(b["tipo_tiempo"] == "pasivo" for b in r["bloques"])
        assert s.exportar_plan(r)["archivo"]
        print("TEST OK - Host AI 4.6.1 Planificador diario de producción")
if __name__ == "__main__": main()
