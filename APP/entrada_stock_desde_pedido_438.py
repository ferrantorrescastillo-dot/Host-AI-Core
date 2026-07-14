from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.entrada_stock_desde_pedido_438 import EntradaStockDesdePedido438


def main():
    ruta_pedidos = ROOT / "DATOS" / "db" / "pedidos_confirmados.json"
    ruta_stock = ROOT / "DATOS" / "db" / "stock_inicial.json"
    ruta_movimientos = ROOT / "DATOS" / "db" / "stock_movimientos.json"
    ruta_informe = ROOT / "DATOS" / "db" / "entradas_desde_pedido_4_3_8.txt"

    procesador = EntradaStockDesdePedido438(str(ruta_pedidos), str(ruta_stock), str(ruta_movimientos))
    resultado = procesador.exportar_txt(str(ruta_informe))

    print("HOST AI 4.3.8 - Entrada Stock desde Pedido")
    print("Archivo informe:", ruta_informe)
    print("Pedidos procesados:", resultado.pedidos_procesados)
    print("Líneas procesadas:", resultado.lineas_procesadas)
    print("Entradas OK:", resultado.entradas_ok)
    print("Entradas error:", resultado.entradas_error)
    print("Estado:", resultado.estado)


if __name__ == "__main__":
    main()
