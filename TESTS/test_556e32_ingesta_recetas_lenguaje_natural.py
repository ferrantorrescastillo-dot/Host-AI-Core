from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.ingesta_recetas_lenguaje_natural_556e32 import AnalizadorRecetasLenguajeNatural556E32
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "DATOS" / "db").mkdir(parents=True)
        motor = AnalizadorRecetasLenguajeNatural556E32(base)
        texto = """
        Cocer las patatas durante 35 minutos.
        Cocer los huevos 12 minutos.
        Enfriar en abatidor durante 40 minutos.
        Pelar y cortar durante 30 minutos.
        Mezclar durante 20 minutos.
        Reposar en cámara 2 horas.
        Porcionar y etiquetar 30 minutos.
        """
        r = motor.analizar("Ensaladilla de prueba", texto, 10, "personas")
        assert r["ok"] and len(r["ficha"]["fases"]) == 7
        assert r["ficha"]["fases"][0]["duracion_base_min"] == 35
        assert r["ficha"]["fases"][2]["tipo_tiempo"] == "pasivo"
        g = motor.guardar_confirmado(r["ficha"])
        assert g["datos_reales_modificados"] is True
        data = json.loads((base / "DATOS" / "db" / "fichas_produccion_reales.json").read_text(encoding="utf-8"))
        assert len(data["fichas"]) == 1

        o = OrquestadorInteligente52(base)
        a = o.procesar("Registra esta receta para Crema de prueba")
        assert a["estado"] == "ESPERANDO_TEXTO_RECETA"
        o.procesar("Cocer 20 minutos")
        b = o.procesar("FIN")
        assert b["estado"] == "FICHA_PROPUESTA"
        c = o.procesar("confirma la ficha de producción")
        assert c["datos"].get("datos_reales_modificados") is True

    print("TEST OK 5.5.6E.3.2 - Ingesta de recetas en lenguaje natural")


if __name__ == "__main__":
    main()
