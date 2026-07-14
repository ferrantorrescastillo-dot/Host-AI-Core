from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.importador_inventario_43112 import ImportadorInventario43112


def main():
    ruta_excel = ROOT / "DATOS" / "inventario_4_3_11_1.xlsx"
    ruta_destino = ROOT / "DATOS" / "db" / "inventario_contado_4_3_11_2.json"

    if len(sys.argv) >= 2:
        ruta_excel = Path(sys.argv[1]).resolve()

    importador = ImportadorInventario43112()
    resultado = importador.importar_desde_excel(str(ruta_excel), str(ruta_destino))

    print("HOST AI 4.3.11.2 - Importador Inventario")
    print("Excel origen:", ruta_excel)
    print("Archivo generado:", resultado.ruta_destino)
    print("Filas leídas:", resultado.total_filas)
    print("Importados:", resultado.importados)
    print("Ignorados sin contar:", resultado.ignorados)
    print("Errores:", resultado.errores)
    print("")
    for mensaje in resultado.mensajes:
        print("-", mensaje)


if __name__ == "__main__":
    main()
