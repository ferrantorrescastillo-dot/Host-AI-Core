from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.informe_stock_inicial_433 import InformeStockInicial433


def main():
    ruta_stock = ROOT / "DATOS" / "db" / "stock_inicial.json"
    ruta_articulos = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_informe = ROOT / "DATOS" / "db" / "informe_stock_inicial_4_3_3.txt"

    generador = InformeStockInicial433(str(ruta_stock), str(ruta_articulos))
    informe = generador.exportar_txt(str(ruta_informe))

    print("HOST AI 4.3.3 - Informe Stock Inicial")
    print("Archivo generado:", ruta_informe)
    print("Registros stock:", informe.total_registros_stock)
    print("Artículos catálogo:", informe.articulos_totales_catalogo)
    print("Sin stock cargado:", informe.articulos_sin_stock_cargado)
    print("Bajo mínimo:", informe.bajo_minimo)
    print("Sin unidad:", informe.sin_unidad)
    print("Sin ubicación:", informe.sin_ubicacion)
    print("Estado:", informe.estado)


if __name__ == "__main__":
    main()
