from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.motor_reparto_cocineros_556e3 import MotorRepartoCocineros556E3


class RecursosFalsos:
    def analizar(self, receta, objetivo, unidad):
        fases = [
            {"orden": 1, "fase": "Preparar", "tipo_tiempo": "activo", "duracion_estimada_min": 30, "recursos": []},
            {"orden": 2, "fase": "Enfriar", "tipo_tiempo": "pasivo", "duracion_estimada_min": 60, "recursos": []},
            {"orden": 3, "fase": "Porcionar", "tipo_tiempo": "activo", "duracion_estimada_min": 20, "recursos": []},
        ]
        return {"receta": receta, "fases": fases, "estado": "RECURSOS_OK"}


def main():
    with tempfile.TemporaryDirectory() as td:
        motor = MotorRepartoCocineros556E3(Path(td), motor_recursos=RecursosFalsos())
        r = motor.repartir([
            {"receta": "Receta A", "objetivo": 100},
            {"receta": "Receta B", "objetivo": 80},
        ], cocineros=["Ana", "Luis"], inicio_jornada="08:00", fin_jornada="15:30")
        assert r["estado"] == "REPARTO_OK"
        assert len(r["asignaciones"]) == 2
        assert {x["cocinero_principal"] for x in r["asignaciones"]} == {"Ana", "Luis"}
        assert all(x["minutos_activos"] == 50 for x in r["cocineros"])
        assert all(a["tareas"][1]["libera_cocinero"] for a in r["asignaciones"])
        assert r["datos_reales_modificados"] is False
    print("TEST OK 5.5.6E.3 - Reparto equilibrado entre cocineros")


if __name__ == "__main__":
    main()
