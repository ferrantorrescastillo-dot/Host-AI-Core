from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.cierre_modulo_stock_4312 import CierreModuloStock4312


def main():
    ruta_db = ROOT / "DATOS" / "db"
    ruta_informe = ROOT / "DATOS" / "db" / "cierre_modulo_stock_4_3_12.txt"

    cierre = CierreModuloStock4312(str(ruta_db))
    informe = cierre.exportar_txt(str(ruta_informe))

    print("HOST AI 4.3.12 - Cierre Módulo Stock")
    print("Archivo generado:", ruta_informe)
    print("Artículos stock:", informe.articulos_stock)
    print("Movimientos stock:", informe.movimientos_stock)
    print("Pedidos confirmados:", informe.pedidos_confirmados)
    print("Inventario contado:", informe.registros_inventario)
    print("Ajustes inventario:", informe.ajustes_inventario)
    print("Estado final:", informe.estado_final)
    print("Bloque siguiente:", informe.bloque_siguiente)
    print("")
    print("Recomendaciones:")
    for recomendacion in informe.recomendaciones:
        print("-", recomendacion)


if __name__ == "__main__":
    main()
