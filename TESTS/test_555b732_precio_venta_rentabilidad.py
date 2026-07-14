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
        (db / "articulos.json").write_text(json.dumps([
            {"codigo": "A1", "nombre": "Patata", "precio": 2.0, "unidad": "kg"},
            {"codigo": "A2", "nombre": "Gamba", "precio": 10.0, "unidad": "kg"},
        ]), encoding="utf-8")
        canonico = {"escandallos": [{"receta": {
            "codigo": "R1", "nombre": "Ensaladilla de gamba", "rendimiento": 4,
            "unidad_rendimiento": "u", "ingredientes": [
                {"articulo_id": "A1", "nombre": "Patata", "cantidad": 0.4, "unidad": "kg"},
                {"articulo_id": "A2", "nombre": "Gamba", "cantidad": 0.2, "unidad": "kg"},
            ]
        }}]}
        (db / "escandallos_canonicos.json").write_text(json.dumps(canonico), encoding="utf-8")

        propuesta = procesar_consulta_escandallos_real_555(
            "Pon un precio de venta de 5,00 € por unidad para ensaladilla de gamba con IVA 10%", base
        )
        assert propuesta["gestionado"] is True, propuesta
        assert propuesta["estado"] == "PENDIENTE_CONFIRMACION", propuesta
        assert "No se ha modificado" in propuesta["mensaje"]
        antes = json.loads((db / "escandallos_canonicos.json").read_text())
        assert "precio_venta_unitario" not in antes["escandallos"][0]

        confirmado = procesar_consulta_escandallos_real_555("Confirma el precio de venta", base)
        assert confirmado["estado"] == "PRECIO_APLICADO", confirmado
        despues = json.loads((db / "escandallos_canonicos.json").read_text())
        registro = despues["escandallos"][0]
        assert registro["precio_venta_unitario"] == 5.0, registro
        assert registro["iva_pct"] == 10.0, registro
        assert list((db / "backups").glob("escandallos_canonicos_precio_*.json.bak"))

        rent = procesar_consulta_escandallos_real_555("Muéstrame la rentabilidad de ensaladilla de gamba", base)
        assert rent["estado"] == "RENTABILIDAD_CONSULTADA", rent
        eco = rent["datos"]["economia"]
        assert round(eco["coste_unitario"], 2) == 0.70, eco
        assert round(eco["beneficio_bruto_unitario"], 2) == 4.30, eco
        assert round(eco["food_cost_pct"], 2) == 14.00, eco
        assert "Margen bruto" in rent["mensaje"]

        otra = procesar_consulta_escandallos_real_555(
            "Pon un precio de venta de 6 euros para ensaladilla de gamba", base
        )
        assert otra["estado"] == "PENDIENTE_CONFIRMACION"
        cancelada = procesar_consulta_escandallos_real_555("Cancela el precio de venta", base)
        assert cancelada["estado"] == "PROPUESTA_CANCELADA"
        final = json.loads((db / "escandallos_canonicos.json").read_text())
        assert final["escandallos"][0]["precio_venta_unitario"] == 5.0

    print("TEST OK 5.5.5B.7.3.2 - Precio de venta, confirmación segura y rentabilidad completa")


if __name__ == "__main__":
    main()
