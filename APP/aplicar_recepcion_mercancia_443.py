from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.aplicador_recepcion_mercancia_443 import AplicadorRecepcionMercancia443


def main():
    ruta_borrador = ROOT / "DATOS" / "db" / "recepcion_borrador_4_4_2.json"
    ruta_stock = ROOT / "DATOS" / "db" / "stock_inicial.json"
    ruta_movimientos = ROOT / "DATOS" / "db" / "stock_movimientos.json"
    ruta_articulos = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_json = ROOT / "DATOS" / "db" / "recepcion_aplicada_4_4_3.json"
    ruta_txt = ROOT / "DATOS" / "db" / "recepcion_aplicada_4_4_3.txt"

    aplicador = AplicadorRecepcionMercancia443(
        str(ruta_borrador),
        str(ruta_stock),
        str(ruta_movimientos),
        str(ruta_articulos),
    )
    resultado = aplicador.aplicar_y_exportar(str(ruta_json), str(ruta_txt))

    print("HOST AI 4.4.3 - Aplicar Recepción a Stock/Precios")
    print("JSON generado:", ruta_json)
    print("TXT generado:", ruta_txt)
    print("Estado:", resultado.estado)
    print("Total líneas:", resultado.total_lineas)
    print("Entradas stock OK:", resultado.entradas_stock_ok)
    print("Precios actualizados:", resultado.precios_actualizados)
    print("Pendientes artículo nuevo:", resultado.pendientes_articulo_nuevo)
    print("Omitidas revisión:", resultado.omitidas_revision)
    print("Errores:", resultado.errores)

    for linea in resultado.lineas:
        print(f"- {linea.producto_texto}: stock={linea.aplicada_stock}, precio={linea.precio_actualizado}, msg={linea.mensaje}")


if __name__ == "__main__":
    main()
