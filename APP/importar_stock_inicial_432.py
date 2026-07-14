from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.importador_stock_inicial_432 import ImportadorStockInicial432


def main():
    ruta_excel = ROOT / "DATOS" / "stock_inicial_4_3_1.xlsx"
    ruta_destino = ROOT / "DATOS" / "db" / "stock_inicial.json"

    if len(sys.argv) >= 2:
        ruta_excel = Path(sys.argv[1]).resolve()

    importador = ImportadorStockInicial432()
    resultado = importador.importar_desde_excel(str(ruta_excel), str(ruta_destino))

    print("HOST AI 4.3.2 - Importador Stock Inicial")
    print("Excel origen:", ruta_excel)
    print("Base de datos:", resultado.ruta_destino)
    print("Filas leídas:", resultado.total_filas)
    print("Importados:", resultado.importados)
    print("Actualizados:", resultado.actualizados)
    print("Ignorados sin rellenar:", resultado.ignorados)
    print("Errores:", resultado.errores)
    print("")
    for mensaje in resultado.mensajes:
        print("-", mensaje)


if __name__ == "__main__":
    main()
