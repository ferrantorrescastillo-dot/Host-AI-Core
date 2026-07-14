from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.importador_articulos_restaurante_414 import ImportadorArticulosRestaurante414


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print('python APP\\importar_articulos_414.py "C:\\Ruta\\Escandallos Boronat  (HostIA)_CODIGOS_4_1_3.xlsx"')
        return

    ruta_excel = Path(sys.argv[1]).resolve()
    if not ruta_excel.exists():
        print(f"No existe el archivo: {ruta_excel}")
        return

    ruta_db = ROOT / "DATOS" / "db" / "articulos.json"

    importador = ImportadorArticulosRestaurante414()
    resultado = importador.importar_desde_excel(str(ruta_excel), str(ruta_db))

    print("HOST AI 4.1.4 - Importación de artículos completada")
    print("Excel origen:", ruta_excel)
    print("Base de datos:", resultado.ruta_destino)
    print("Procesados:", resultado.total_procesados)
    print("Nuevos:", resultado.nuevos)
    print("Actualizados:", resultado.actualizados)
    print("Errores:", resultado.errores)

    for mensaje in resultado.mensajes:
        print("-", mensaje)


if __name__ == "__main__":
    main()
