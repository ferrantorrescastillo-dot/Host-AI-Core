from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT_PROJECT = Path(__file__).resolve().parents[1]
if str(ROOT_PROJECT) not in sys.path:
    sys.path.insert(0, str(ROOT_PROJECT))

from SERVICIOS.ingesta_recetas_lenguaje_natural_556e32 import AnalizadorRecetasLenguajeNatural556E32
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "DATOS" / "db").mkdir(parents=True)
        analizador = AnalizadorRecetasLenguajeNatural556E32(root)
        propuesta = analizador.analizar(
            "Ensaladilla de gamba",
            "Cocer las patatas durante 35 minutos.\nPelar y cortar durante 30 minutos.\nReposar en cámara durante 2 horas.",
            10,
            "personas",
        )
        assert propuesta["ok"]
        nombres = [f["nombre"] for f in propuesta["ficha"]["fases"]]
        assert nombres == ["Cocer patatas", "Pelar y cortar", "Reposar en cámara"], nombres
        guardado = analizador.guardar_confirmado(propuesta["ficha"])
        assert guardado["datos_reales_modificados"] is True

        o = OrquestadorInteligente52(root)
        o.contexto_post_ficha_556e33 = {"estado": "ESPERANDO_CONFIRMACION_PLANIFICAR", "receta": "Ensaladilla de gamba"}
        r1 = o.procesar("sí")
        assert r1["estado"] == "ESPERANDO_OBJETIVO", r1
        r2 = o.procesar("150 personas con 3 cocineros")
        assert r2["intencion"] == "planificacion_receta_real", r2
        assert "PLANIFICACIÓN REAL" in r2["mensaje"]
        assert r2["datos"]["objetivo"] == 150
        assert len(r2["datos"]["cocineros"]) == 3
        assert not o.contexto_post_ficha_556e33

    print("TEST OK 5.5.6E.3.3 - Continuidad post-ficha y planificación guiada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
