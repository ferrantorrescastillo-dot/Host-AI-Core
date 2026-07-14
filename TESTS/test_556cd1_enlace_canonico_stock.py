from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.cruce_stock_produccion_556c import CruceStockProduccion556C


def guardar(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "DATOS" / "db"
        guardar(db / "articulos.json", [
            {"codigo": "ART-PATATA", "nombre": "Patata Monalisa", "unidad": "kg", "proveedor": "Makro"},
            {"codigo": "ART-LECHE", "nombre": "Leche entera", "unidad": "L", "proveedor": "Makro"},
            {"codigo": "ART-GAMBA", "nombre": "Gamba paella", "unidad": "kg", "proveedor": "Pescados SL"},
        ])
        guardar(db / "stock_inicial.json", [
            {"codigo": "ART-PATATA", "articulo": "Patata Monalisa", "unidad": "kg", "stock_actual": 20, "stock_minimo": 5},
            {"codigo": "ART-LECHE", "articulo": "Leche entera", "unidad": "L", "stock_actual": 15, "stock_minimo": 3},
        ])
        guardar(db / "stock_movimientos.json", [
            {"codigo": "ART-PATATA", "articulo": "Patata Monalisa", "tipo": "entrada", "cantidad": 5, "unidad": "kg", "stock_despues": 25, "fecha_hora": "2026-07-10T10:00:00"},
        ])
        guardar(db / "escandallos_canonicos.json", [])

        servicio = CruceStockProduccion556C(base)
        servicio.motor.explotar = lambda *args, **kwargs: {
            "receta": "Prueba",
            "ingredientes_finales": [
                {"nombre": "Patata Monalisa", "articulo_id": "ART-PATATA", "cantidad": 11.25, "unidad": "kg"},
                {"nombre": "Leche entera.", "articulo_id": None, "cantidad": 2, "unidad": "l"},
                {"nombre": "Gamba paella", "articulo_id": "ART-GAMBA", "cantidad": 7.125, "unidad": "kg"},
                {"nombre": "Ingrediente inexistente", "articulo_id": None, "cantidad": 1, "unidad": "kg"},
            ],
        }
        r = servicio.cruzar("Prueba", 10)
        por_nombre = {x["nombre"]: x for x in r["lineas"]}

        assert por_nombre["Patata Monalisa"]["estado"] == "STOCK_CORRECTO"
        assert por_nombre["Patata Monalisa"]["disponible"] == 25
        assert por_nombre["Patata Monalisa"]["metodo_enlace_stock"] == "STOCK_ID_EXACTO"
        assert por_nombre["Leche entera."]["estado"] == "STOCK_CORRECTO"
        assert por_nombre["Leche entera."]["metodo_enlace_articulo"] == "ARTICULO_NOMBRE_EXACTO"
        assert por_nombre["Gamba paella"]["estado"] == "ARTICULO_SIN_INVENTARIO"
        assert por_nombre["Ingrediente inexistente"]["estado"] == "ARTICULO_NO_LOCALIZADO"
        assert r["datos_reales_modificados"] is False
        assert r["total_sin_registro_stock"] == 1
        assert r["total_articulos_no_localizados"] == 1

    print("TEST OK 5.5.6CD.1 - Enlace canónico producción-stock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
