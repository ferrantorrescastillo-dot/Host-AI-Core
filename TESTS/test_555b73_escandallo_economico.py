from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.conector_escandallos_real_555 import procesar_consulta_escandallos_real_555


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "DATOS" / "db"
        db.mkdir(parents=True)
        payload = {
            "schema_version": "1.0",
            "escandallos": [
                {
                    "receta": {
                        "codigo": "REC-ENS-001",
                        "nombre": "Ensaladilla de gamba",
                        "rendimiento": 4,
                        "unidad_rendimiento": "racion",
                        "ingredientes": [
                            {"codigo": "I1", "nombre": "Patata", "cantidad": 0.4, "unidad": "kg", "precio_unitario": 2.0},
                            {"codigo": "I2", "nombre": "Gamba", "cantidad": 0.2, "unidad": "kg", "precio_unitario": 10.0},
                        ],
                    },
                    "coste_total": 2.8,
                    "precio_venta_unitario": 5.0,
                    "iva_pct": 10,
                }
            ],
        }
        (db / "escandallos_canonicos.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        r = procesar_consulta_escandallos_real_555("Muéstrame el escandallo de ensaladilla de gamba", base)
        assert r["gestionado"] is True
        assert r["version"] == "5.5.5B.7.3.2"
        economia = r["datos"]["coincidencias"][0]["economia"]
        assert round(economia["coste_total"], 2) == 2.80
        assert round(economia["coste_unitario"], 2) == 0.70
        assert round(economia["precio_venta_unitario"], 2) == 5.00
        assert round(economia["beneficio_bruto_unitario"], 2) == 4.30
        assert round(economia["food_cost_pct"], 2) == 14.00
        assert "RESUMEN ECONÓMICO" in r["mensaje"]
        assert "Beneficio sobre coste" in r["mensaje"]
        assert "Margen bruto sobre venta" in r["mensaje"]

        payload["escandallos"][0].pop("precio_venta_unitario")
        (db / "escandallos_canonicos.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        r2 = procesar_consulta_escandallos_real_555("Muéstrame el escandallo de ensaladilla de gamba", base)
        assert "Precio de venta: NO DEFINIDO" in r2["mensaje"]
        assert r2["datos"]["coincidencias"][0]["economia"]["margen_bruto_pct"] is None

    print("TEST OK 5.5.5B.7.3 - Escandallo económico y rentabilidad")


if __name__ == "__main__":
    main()
