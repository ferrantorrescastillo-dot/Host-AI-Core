from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.motor_paralelizacion_produccion_556e4 import MotorParalelizacionProduccion556E4


class RepartoFalso:
    class Recursos:
        config = {"recursos": {"fogones": 1, "mesa_trabajo": 2, "abatidor": 1}}
    motor_recursos = Recursos()

    def repartir(self, producciones, cocineros, inicio, fin):
        nombres = ["Ana", "Luis"]
        asignaciones = []
        for idx, p in enumerate(producciones):
            coc = nombres[idx % 2]
            asignaciones.append({
                "receta": p["receta"], "objetivo": p["objetivo"], "unidad": "personas",
                "cocinero_principal": coc, "minutos_activos": 50,
                "tareas": [
                    {"fase": "Preparar", "tipo_tiempo": "activo", "duracion_min": 20, "recursos": [{"recurso": "mesa_trabajo"}]},
                    {"fase": "Cocinar", "tipo_tiempo": "activo", "duracion_min": 30, "recursos": [{"recurso": "fogones"}]},
                    {"fase": "Enfriar", "tipo_tiempo": "pasivo", "duracion_min": 60, "recursos": [{"recurso": "abatidor"}]},
                ],
            })
        return {
            "cocineros": [{"nombre": "Ana"}, {"nombre": "Luis"}],
            "asignaciones": asignaciones,
            "incidencias": [],
            "estado": "REPARTO_OK",
        }


def main():
    with tempfile.TemporaryDirectory() as td:
        motor = MotorParalelizacionProduccion556E4(Path(td), motor_reparto=RepartoFalso())
        r = motor.planificar([
            {"receta": "A", "objetivo": 100},
            {"receta": "B", "objetivo": 100},
        ], cocineros=2, inicio_jornada="08:00", fin_jornada="15:30")
        assert r["estado"] == "PLAN_PARALELO_OK"
        assert len(r["cronograma"]) == 6
        assert not r["conflictos_residuales"]
        cocinas = [x for x in r["cronograma"] if x["fase"] == "Cocinar"]
        assert len(cocinas) == 2
        assert cocinas[0]["fin_min"] <= cocinas[1]["inicio_min"] or cocinas[1]["fin_min"] <= cocinas[0]["inicio_min"]
        assert any(x["libera_cocinero"] for x in r["cronograma"])
        assert r["datos_reales_modificados"] is False
    print("TEST OK 5.5.6E.4 - Paralelización de tareas y recursos")


if __name__ == "__main__":
    main()
