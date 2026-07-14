import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.motor_movimientos_stock_437 import MotorMovimientosStock437


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

        motor = MotorMovimientosStock437(str(ruta_stock), str(ruta_mov))

        entrada = motor.registrar_movimiento("ART000001", 5, "entrada", "Compra recibida", usuario="test")
        assert entrada.ok is True
        assert entrada.stock_antes == 10
        assert entrada.stock_despues == 15

        salida = motor.registrar_movimiento("ART000001", 3, "salida", "Producción paella", usuario="test")
        assert salida.ok is True
        assert salida.stock_antes == 15
        assert salida.stock_despues == 12

        ajuste = motor.registrar_movimiento("ART000001", 8, "ajuste", "Inventario real", usuario="test")
        assert ajuste.ok is True
        assert ajuste.stock_antes == 12
        assert ajuste.stock_despues == 8

        fallo = motor.registrar_movimiento("ART000001", 20, "salida", "Salida imposible", usuario="test")
        assert fallo.ok is False
        assert "No hay stock suficiente" in fallo.mensaje

        movimientos = json.loads(ruta_mov.read_text(encoding="utf-8"))
        assert len(movimientos) == 3
        assert movimientos[0]["id_movimiento"] == "MOV00000001"

        stock_final = json.loads(ruta_stock.read_text(encoding="utf-8"))
        assert stock_final[0]["stock_actual"] == 8

    print("TEST OK - Host AI 4.3.7 Motor Movimientos Stock")
    print("Entrada, salida y ajuste: OK")
    print("Control stock insuficiente: OK")


if __name__ == "__main__":
    main()
