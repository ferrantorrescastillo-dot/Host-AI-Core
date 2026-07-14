from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.escalador_explosion_recetas_556ab import MotorEscaladoExplosion556AB
from SERVICIOS.conector_produccion_real_556 import procesar_consulta_produccion_real_556


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "DATOS" / "db"
        db.mkdir(parents=True)
        (db / "articulos.json").write_text(json.dumps([
            {"codigo": "A-PAT", "nombre": "Patata", "precio": 2.0},
            {"codigo": "A-TOM", "nombre": "Tomate", "precio": 3.0},
            {"codigo": "A-ACE", "nombre": "Aceite", "precio": 5.0},
        ]), encoding="utf-8")
        (db / "escandallos_canonicos.json").write_text(json.dumps({"escandallos": [
            {"receta": {"codigo": "R-SALSA", "nombre": "Salsa brava", "rendimiento": 1, "unidad_rendimiento": "kg", "ingredientes": [
                {"nombre": "Tomate", "articulo_id": "A-TOM", "cantidad": 0.8, "unidad": "kg"},
                {"nombre": "Aceite", "articulo_id": "A-ACE", "cantidad": 0.2, "unidad": "kg"},
            ]}},
            {"receta": {"codigo": "R-BRAVAS", "nombre": "Patatas bravas", "rendimiento": 4, "unidad_rendimiento": "u", "ingredientes": [
                {"nombre": "Patata", "articulo_id": "A-PAT", "cantidad": 1.2, "unidad": "kg"},
                {"nombre": "Salsa brava", "receta_id": "R-SALSA", "cantidad": 0.4, "unidad": "kg"},
            ]}},
        ]}), encoding="utf-8")

        motor = MotorEscaladoExplosion556AB(base)
        escalado = motor.escalar("patatas bravas", 100, "personas")
        assert round(escalado["factor"], 2) == 25.0
        assert escalado["ingredientes"][0]["cantidad_escalada"] == 30.0
        assert escalado["ingredientes"][1]["es_elaboracion"] is True

        explosion = motor.explotar("patatas bravas", 100, "personas")
        finales = {x["nombre"]: x["cantidad"] for x in explosion["ingredientes_finales"]}
        assert finales["Patata"] == 30.0
        assert finales["Tomate"] == 8.0
        assert finales["Aceite"] == 2.0
        assert explosion["incidencias"] == []

        respuesta = procesar_consulta_produccion_real_556("Desglosa toda la producción de patatas bravas para 100 personas incluyendo elaboraciones internas", base)
        assert respuesta["gestionado"] is True
        assert respuesta["ok"] is True
        assert "INGREDIENTES FINALES CONSOLIDADOS" in respuesta["mensaje"]

    print("TEST OK 5.5.6AB - Escalador de recetas y explosión de elaboraciones")


if __name__ == "__main__":
    main()
