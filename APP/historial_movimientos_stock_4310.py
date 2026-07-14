from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.historial_movimientos_stock_4310 import HistorialMovimientosStock4310


def main():
    codigo = None
    tipo = None

    if len(sys.argv) >= 2:
        codigo = sys.argv[1] if sys.argv[1] != "-" else None
    if len(sys.argv) >= 3:
        tipo = sys.argv[2] if sys.argv[2] != "-" else None

    ruta_movimientos = ROOT / "DATOS" / "db" / "stock_movimientos.json"
    ruta_informe = ROOT / "DATOS" / "db" / "historial_movimientos_stock_4_3_10.txt"

    historial = HistorialMovimientosStock4310(str(ruta_movimientos))
    informe = historial.exportar_txt(str(ruta_informe), codigo=codigo, tipo=tipo)

    print("HOST AI 4.3.10 - Historial Movimientos Stock")
    print("Archivo generado:", ruta_informe)
    print("Total movimientos:", informe.total_movimientos)
    print("Mostrados:", informe.movimientos_filtrados)
    print("Filtro código:", informe.codigo_filtro or "-")
    print("Filtro tipo:", informe.tipo_filtro or "-")
    print("Estado:", informe.estado)
    print("")

    for mov in informe.movimientos[:10]:
        print(f"{mov.fecha_hora} | {mov.codigo} | {mov.articulo} | {mov.tipo} {mov.cantidad} {mov.unidad} | {mov.stock_antes} -> {mov.stock_despues}")


if __name__ == "__main__":
    main()
