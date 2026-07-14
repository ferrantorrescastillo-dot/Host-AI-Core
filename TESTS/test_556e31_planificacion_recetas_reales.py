from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.fichas_produccion_reales_556e31 import RepositorioFichasProduccion556E31
from SERVICIOS.motor_planificacion_recetas_reales_556e31 import MotorPlanificacionRecetasReales556E31


def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo = RepositorioFichasProduccion556E31(root)
        sin = MotorPlanificacionRecetasReales556E31(root).planificar("Ensaladilla", 100)
        assert sin["estado"] == "NECESITA_FICHA_PRODUCCION"
        ficha = {
            "receta": "Ensaladilla",
            "rendimiento_base": 10,
            "unidad_rendimiento": "personas",
            "fases": [
                {"nombre": "Cocer patata", "duracion_base_min": 30, "tipo_tiempo": "pasivo", "requiere_presencia": False, "escalable_por_volumen": False, "recursos": ["fogones"]},
                {"nombre": "Pelar y cortar", "duracion_base_min": 20, "tipo_tiempo": "activo", "requiere_presencia": True, "escalable_por_volumen": True, "recursos": ["mesa_trabajo"]},
                {"nombre": "Reposar", "duracion_base_min": 60, "tipo_tiempo": "pasivo", "requiere_presencia": False, "escalable_por_volumen": False, "recursos": ["camara_fria"]},
            ],
        }
        previa = repo.guardar(ficha, confirmar=False)
        assert previa["estado"] == "PROPUESTA_LISTA"
        guardada = repo.guardar(ficha, confirmar=True)
        assert guardada["datos_reales_modificados"] is True
        plan = MotorPlanificacionRecetasReales556E31(root).planificar("Ensaladilla", 100, cocineros=3)
        assert plan["puede_planificar"] is True
        assert plan["fuente"] == "FICHA_PRODUCCION_REAL_VALIDADA"
        assert any(t["libera_cocinero"] for t in plan["tareas"])
        assert plan["cocineros"][1]["minutos_activos"] > 0 or plan["cocineros"][0]["minutos_activos"] > 0
        assert plan["datos_reales_modificados"] is False
    print("TEST OK 5.5.6E.3.1 - Planificación basada en recetas reales")


if __name__ == "__main__":
    main()
