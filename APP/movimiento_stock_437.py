from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.motor_movimientos_stock_437 import MotorMovimientosStock437


def main():
    if len(sys.argv) < 5:
        print("Uso:")
        print('python APP\\movimiento_stock_437.py ART000001 entrada 5 "Compra recibida"')
        print('python APP\\movimiento_stock_437.py ART000001 salida 2 "Producción paella"')
        print('python APP\\movimiento_stock_437.py ART000001 ajuste 10 "Inventario real"')
        return

    codigo = sys.argv[1]
    tipo = sys.argv[2]
    cantidad = sys.argv[3]
    motivo = sys.argv[4]

    ruta_stock = ROOT / "DATOS" / "db" / "stock_inicial.json"
    ruta_movimientos = ROOT / "DATOS" / "db" / "stock_movimientos.json"

    motor = MotorMovimientosStock437(str(ruta_stock), str(ruta_movimientos))
    resultado = motor.registrar_movimiento(
        codigo=codigo,
        tipo=tipo,
        cantidad=cantidad,
        motivo=motivo,
        usuario="usuario_local",
    )

    print("HOST AI 4.3.7 - Movimiento de Stock")
    print("OK:", resultado.ok)
    print("Movimiento:", resultado.id_movimiento or "-")
    print("Código:", resultado.codigo)
    print("Artículo:", resultado.articulo)
    print("Tipo:", resultado.tipo)
    print("Cantidad:", resultado.cantidad)
    print("Stock antes:", resultado.stock_antes)
    print("Stock después:", resultado.stock_despues)
    print("Mensaje:", resultado.mensaje)


if __name__ == "__main__":
    main()
