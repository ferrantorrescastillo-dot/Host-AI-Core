from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.salidas_stock_439 import SalidasStock439


def main():
    if len(sys.argv) < 5:
        print("Uso:")
        print('python APP\\salida_stock_439.py ART000001 2 produccion "Producción paella"')
        print('python APP\\salida_stock_439.py ART000001 1 merma "Producto caducado"')
        print('python APP\\salida_stock_439.py ART000001 1 rotura "Botella rota"')
        return

    codigo = sys.argv[1]
    cantidad = sys.argv[2]
    tipo_salida = sys.argv[3]
    motivo = sys.argv[4]

    ruta_stock = ROOT / "DATOS" / "db" / "stock_inicial.json"
    ruta_movimientos = ROOT / "DATOS" / "db" / "stock_movimientos.json"

    salidas = SalidasStock439(str(ruta_stock), str(ruta_movimientos))
    resultado = salidas.registrar_salida(
        codigo=codigo,
        cantidad=cantidad,
        tipo_salida=tipo_salida,
        motivo=motivo,
        usuario="usuario_local",
    )

    print("HOST AI 4.3.9 - Salida Manual de Stock")
    print("OK:", resultado.ok)
    print("Movimiento:", resultado.id_movimiento or "-")
    print("Código:", resultado.codigo)
    print("Artículo:", resultado.articulo)
    print("Tipo salida:", resultado.tipo_salida)
    print("Cantidad:", resultado.cantidad)
    print("Stock antes:", resultado.stock_antes)
    print("Stock después:", resultado.stock_despues)
    print("Mensaje:", resultado.mensaje)


if __name__ == "__main__":
    main()
