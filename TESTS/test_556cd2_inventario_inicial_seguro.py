from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.inventario_inicial_seguro_556cd2 import InventarioInicialSeguro556CD2


def guardar(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "DATOS" / "db"
        config = base / "DATOS" / "config"
        guardar(db / "articulos.json", [
            {"codigo": "ART-PAT", "nombre": "Patata Monalisa", "unidad": "kg", "proveedor": "Makro", "familia": "Verduras"},
            {"codigo": "ART-HUE", "nombre": "Huevos L", "unidad": "u", "proveedor": "Granja Vidal"},
        ])
        guardar(db / "stock_inicial.json", [])
        guardar(db / "stock_movimientos.json", [])
        guardar(config / "stock_minimos_defecto_556cd2.json", {
            "por_unidad": {"kg": 2, "l": 2, "u": 10, "g": 500, "ml": 500},
            "por_familia": {"Verduras": 5},
        })

        servicio = InventarioInicialSeguro556CD2(base)
        propuesta = servicio.proponer("Patata Monalisa", 25, unidad="kg", ubicacion="Almacen seco")
        assert propuesta["ok"] is True
        assert propuesta["propuesta"]["stock_actual"] == 25
        assert propuesta["propuesta"]["stock_minimo"] == 5
        assert propuesta["datos_reales_modificados"] is False

        confirmado = servicio.confirmar(propuesta["propuesta"])
        assert confirmado["ok"] is True
        assert confirmado["datos_reales_modificados"] is True

        stock = json.loads((db / "stock_inicial.json").read_text(encoding="utf-8"))
        movimientos = json.loads((db / "stock_movimientos.json").read_text(encoding="utf-8"))
        assert len(stock) == 1 and stock[0]["codigo"] == "ART-PAT"
        assert stock[0]["stock_actual"] == 25 and stock[0]["stock_minimo"] == 5
        assert len(movimientos) == 1 and movimientos[0]["tipo"] == "inventario_inicial"
        assert movimientos[0]["stock_despues"] == 25

        # Repetir la misma alta no debe sobrescribir ni duplicar.
        servicio2 = InventarioInicialSeguro556CD2(base)
        repetida = servicio2.proponer("ART-PAT", 30, unidad="kg")
        assert repetida["ok"] is False and repetida["estado"] == "INVENTARIO_YA_EXISTE"
        assert len(json.loads((db / "stock_inicial.json").read_text(encoding="utf-8"))) == 1

        # El mínimo por unidad se aplica a artículos sin regla de familia.
        propuesta_huevos = servicio2.proponer("Huevos L", 60, unidad="u")
        assert propuesta_huevos["ok"] is True
        assert propuesta_huevos["propuesta"]["stock_minimo"] == 10

        listado = servicio2.listar_sin_inventario()
        assert listado["sin_inventario"] == 1
        assert listado["articulos"][0]["nombre"] == "Huevos L"

    print("TEST OK 5.5.6CD.2 - Alta e inicialización segura del inventario")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
