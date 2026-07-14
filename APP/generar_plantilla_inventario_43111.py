from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.generador_plantilla_inventario_43111 import GeneradorPlantillaInventario43111


def main():
    ruta_stock = ROOT / "DATOS" / "db" / "stock_inicial.json"
    ruta_destino = ROOT / "DATOS" / "inventario_4_3_11_1.xlsx"

    generador = GeneradorPlantillaInventario43111(str(ruta_stock))
    resultado = generador.generar_excel(str(ruta_destino))

    print("HOST AI 4.3.11.1 - Plantilla Inventario")
    print("Archivo generado:", resultado.ruta_destino)
    print("Registros stock incluidos:", resultado.total_registros_stock)
    print("Estado:", resultado.estado)
    print("Mensaje:", resultado.mensaje)


if __name__ == "__main__":
    main()
