from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.enriquecedor_precios_articulos_555b731 import EnriquecedorPreciosArticulos555B731
from SERVICIOS.conector_escandallos_real_555 import ConectorEscandallosReal555


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp)
        db = base / "DATOS" / "db"
        db.mkdir(parents=True)
        articulos = [
            {"codigo": "ART001", "nombre": "Patata Monalisa.", "precio": 2.0, "proveedor": "Proveedor A", "unidad": "kg"},
            {"codigo": "ART002", "nombre": "Huevos L", "precio": 0.26, "proveedor": "Proveedor B", "unidad": "u"},
            {"codigo": "ART003", "nombre": "Sin precio", "precio": None, "unidad": "kg"},
        ]
        (db / "articulos.json").write_text(json.dumps(articulos, ensure_ascii=False), encoding="utf-8")
        canonico = {
            "escandallos": [{
                "receta": {
                    "codigo": "REC001", "nombre": "Receta prueba", "rendimiento": 2,
                    "unidad_rendimiento": "u",
                    "ingredientes": [
                        {"nombre": "Patata Monalisa", "cantidad": 0.5, "unidad": "kg", "articulo_id": "ART001"},
                        {"nombre": "Huevos L", "cantidad": 2, "unidad": "u"},
                        {"nombre": "Sin precio", "cantidad": 0.1, "unidad": "kg"},
                    ],
                }
            }]
        }
        (db / "escandallos_canonicos.json").write_text(json.dumps(canonico, ensure_ascii=False), encoding="utf-8")

        enriquecedor = EnriquecedorPreciosArticulos555B731(base)
        r = enriquecedor.enriquecer([
            {"nombre": "Patata Monalisa", "articulo_id": "ART001", "cantidad": 0.5, "unidad": "kg"},
            {"nombre": "Huevos L", "cantidad": 2, "unidad": "u"},
            {"nombre": "Sin precio", "cantidad": 0.1, "unidad": "kg"},
        ])
        assert r["valoradas"] == 2, r
        assert r["sin_precio"] == 1, r
        assert abs(r["coste_total"] - 1.52) < 1e-9, r
        assert r["lineas"][0]["metodo_enlace_precio"] == "CODIGO_EXACTO"
        assert r["lineas"][1]["metodo_enlace_precio"] == "NOMBRE_EXACTO"

        consulta = ConectorEscandallosReal555(base).consultar("receta prueba")
        eco = consulta["coincidencias"][0]["economia"]
        assert abs(eco["coste_total"] - 1.52) < 1e-9, eco
        assert abs(eco["coste_unitario"] - 0.76) < 1e-9, eco
        assert eco["ingredientes_valorados"] == 2, eco
        assert eco["ingredientes_sin_precio"] == 1, eco
        assert eco["estado"] == "COSTE_PARCIAL", eco

    print("TEST OK 5.5.5B.7.3.1 - Enriquecimiento económico desde artículos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
