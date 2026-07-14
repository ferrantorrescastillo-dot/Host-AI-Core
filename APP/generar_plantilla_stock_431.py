from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.generador_plantilla_stock_inicial_431 import GeneradorPlantillaStockInicial431


def main():
    ruta_articulos = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_destino = ROOT / "DATOS" / "stock_inicial_4_3_1.xlsx"

    generador = GeneradorPlantillaStockInicial431(str(ruta_articulos))
    resultado = generador.generar_excel(str(ruta_destino))

    print("HOST AI 4.3.1 - Plantilla Stock Inicial")
    print("Archivo generado:", resultado.ruta_destino)
    print("Artículos incluidos:", resultado.total_articulos)
    print("Estado:", resultado.estado)
    print("Mensaje:", resultado.mensaje)


if __name__ == "__main__":
    main()
