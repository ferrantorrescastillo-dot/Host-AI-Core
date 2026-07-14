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


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db = root / "DATOS" / "db"
        db.mkdir(parents=True)
        (db / "escandallos_canonicos.json").write_text(
            json.dumps({
                "escandallos": [{
                    "receta": {
                        "nombre": "Ensaladilla de gamba",
                        "rendimiento": 4,
                        "unidad_rendimiento": "u",
                        "ingredientes": [],
                    }
                }]
            }),
            encoding="utf-8",
        )

        repo = RepositorioFichasProduccion556E31(root)
        # Ficha antigua: no contiene puede_paralelizar. La 3.4.1 debe inferir
        # de forma conservadora qué fases permiten reparto interno.
        repo.guardar({
            "receta": "Ensaladilla de gamba",
            "rendimiento_base": 1,
            "unidad_rendimiento": "u",
            "fases": [
                {"nombre": "Cocer patatas", "duracion_base_min": 35, "tipo_tiempo": "pasivo", "requiere_presencia": False, "escalable_por_volumen": False, "recursos": ["fogones"]},
                {"nombre": "Cocer huevos", "duracion_base_min": 12, "tipo_tiempo": "pasivo", "requiere_presencia": False, "escalable_por_volumen": False, "recursos": ["fogones"]},
                {"nombre": "Enfriar en abatidor", "duracion_base_min": 40, "tipo_tiempo": "pasivo", "requiere_presencia": False, "escalable_por_volumen": False, "recursos": ["abatidor"]},
                {"nombre": "Pelar y cortar", "duracion_base_min": 30, "tipo_tiempo": "activo", "requiere_presencia": True, "escalable_por_volumen": True, "recursos": ["mesa_trabajo"]},
                {"nombre": "Mezclar", "duracion_base_min": 20, "tipo_tiempo": "activo", "requiere_presencia": True, "escalable_por_volumen": True, "recursos": ["mesa_trabajo"]},
                {"nombre": "Reposar en cámara", "duracion_base_min": 120, "tipo_tiempo": "pasivo", "requiere_presencia": False, "escalable_por_volumen": False, "recursos": ["camara_fria"]},
                {"nombre": "Porcionar y etiquetar", "duracion_base_min": 30, "tipo_tiempo": "activo", "requiere_presencia": True, "escalable_por_volumen": True, "recursos": ["mesa_trabajo"]},
            ],
        }, confirmar=True)

        plan = MotorPlanificacionRecetasReales556E31(root).planificar(
            "Ensaladilla de gamba", 150, "personas", 3, "08:00", "15:30"
        )

        assert plan["version"] == "5.5.6E.3.4.1"
        assert plan["dias_estimados"] == 1, plan
        assert plan["estado"] == "PLAN_REAL_OK"
        assert all(t["fin_min"] <= 15 * 60 + 30 for t in plan["tareas"])

        pelar = next(t for t in plan["tareas"] if t["fase"] == "Pelar y cortar")
        porcionar = next(t for t in plan["tareas"] if t["fase"] == "Porcionar y etiquetar")
        mezclar = next(t for t in plan["tareas"] if t["fase"] == "Mezclar")
        assert pelar["paralelizada"] is True and len(pelar["responsables"]) == 3
        assert porcionar["paralelizada"] is True and len(porcionar["responsables"]) == 3
        assert mezclar["paralelizada"] is False

        cargas = plan["cargas_por_dia"][0]["cocineros"]
        assert all(c["minutos_activos"] <= 450 for c in cargas)
        assert sum(1 for c in cargas if c["minutos_activos"] > 0) == 3
        assert plan["datos_reales_modificados"] is False

    print("TEST OK 5.5.6E.3.4.1 - Paralelización interna por lotes y equipo")


if __name__ == "__main__":
    main()
