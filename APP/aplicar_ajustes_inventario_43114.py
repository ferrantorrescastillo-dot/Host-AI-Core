from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.aplicador_ajustes_inventario_43114 import AplicadorAjustesInventario43114


def main():
    ruta_comparacion = ROOT / "DATOS" / "db" / "comparacion_inventario_4_3_11_3.json"
    ruta_stock = ROOT / "DATOS" / "db" / "stock_inicial.json"
    ruta_movimientos = ROOT / "DATOS" / "db" / "stock_movimientos.json"
    ruta_informe = ROOT / "DATOS" / "db" / "ajustes_inventario_4_3_11_4.txt"

    motivo = "Ajuste por inventario físico"
    if len(sys.argv) >= 2:
        motivo = sys.argv[1]

    aplicador = AplicadorAjustesInventario43114(str(ruta_comparacion), str(ruta_stock), str(ruta_movimientos))
    resultado = aplicador.exportar_txt(str(ruta_informe), motivo=motivo)

    print("HOST AI 4.3.11.4 - Aplicador Ajustes Inventario")
    print("Archivo generado:", ruta_informe)
    print("Total líneas:", resultado.total_lineas)
    print("Ajustes aplicados:", resultado.ajustes_aplicados)
    print("Ajustes omitidos:", resultado.ajustes_omitidos)
    print("Errores:", resultado.errores)
    print("Estado:", resultado.estado)


if __name__ == "__main__":
    main()
