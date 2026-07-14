from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.generador_pedido_stock_bajo_435 import GeneradorPedidoStockBajo435


def main():
    ruta_stock = ROOT / "DATOS" / "db" / "stock_inicial.json"
    ruta_json = ROOT / "DATOS" / "db" / "pedido_sugerido_stock_bajo_4_3_5.json"
    ruta_txt = ROOT / "DATOS" / "db" / "pedido_sugerido_stock_bajo_4_3_5.txt"

    generador = GeneradorPedidoStockBajo435(str(ruta_stock))
    informe = generador.generar(str(ruta_json), str(ruta_txt))

    print("HOST AI 4.3.5 - Pedido Sugerido desde Stock Bajo")
    print("JSON generado:", ruta_json)
    print("TXT generado:", ruta_txt)
    print("Líneas de pedido:", informe.total_lineas)
    print("Proveedores:", informe.total_proveedores)
    print("Estado:", informe.estado)

    for pedido in informe.pedidos_por_proveedor:
        print("")
        print("Proveedor:", pedido.proveedor)
        for linea in pedido.lineas:
            print(f"- [{linea.prioridad.upper()}] {linea.articulo}: pedir {linea.cantidad_sugerida} {linea.unidad}")


if __name__ == "__main__":
    main()
