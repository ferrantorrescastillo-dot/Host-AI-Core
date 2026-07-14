import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.salidas_stock_439 import SalidasStock439


def main():
    stock = [
        {
            "codigo": "ART000001",
            "articulo": "Arroz bomba",
            "unidad": "kg",
            "stock_actual": 10,
            "stock_minimo": 5,
            "ubicacion": "Almacén seco",
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_stock = Path(tmpdir) / "stock_inicial.json"
        ruta_mov = Path(tmpdir) / "stock_movimientos.json"
        ruta_stock.write_text(json.dumps(stock, ensure_ascii=False, indent=2), encoding="utf-8")

        salidas = SalidasStock439(str(ruta_stock), str(ruta_mov))

        resultado = salidas.registrar_salida(
            codigo="ART000001",
            cantidad=3,
            tipo_salida="produccion",
            motivo="Producción paella",
            usuario="test",
            documento_relacionado="PROD000001",
        )

        assert resultado.ok is True
        assert resultado.stock_antes == 10
        assert resultado.stock_despues == 7
        assert resultado.tipo_salida == "produccion"

        fallo = salidas.registrar_salida(
            codigo="ART000001",
            cantidad=20,
            tipo_salida="merma",
            motivo="Merma imposible",
            usuario="test",
        )

        assert fallo.ok is False
        assert "No hay stock suficiente" in fallo.mensaje

        movimientos = json.loads(ruta_mov.read_text(encoding="utf-8"))
        assert len(movimientos) == 1
        assert movimientos[0]["motivo"] == "produccion: Producción paella"
        assert movimientos[0]["documento_relacionado"] == "PROD000001"

    print("TEST OK - Host AI 4.3.9 Salidas Manuales de Stock")
    print("Salida producción: OK")
    print("Control stock insuficiente: OK")


if __name__ == "__main__":
    main()
