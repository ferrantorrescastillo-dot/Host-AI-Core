from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.clasificador_inteligente_articulos_412 import ClasificadorInteligenteArticulos412


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print('python APP\\clasificar_articulos_412.py "C:\\Ruta\\Escandallos Boronat  (HostIA).xlsx"')
        return

    ruta_excel = Path(sys.argv[1]).resolve()
    if not ruta_excel.exists():
        print(f"No existe el archivo: {ruta_excel}")
        return

    ruta_destino = ruta_excel.with_name(ruta_excel.stem + "_CLASIFICADO_4_1_2.xlsx")

    clasificador = ClasificadorInteligenteArticulos412()
    informe = clasificador.exportar_excel_clasificado(str(ruta_excel), str(ruta_destino))

    print("HOST AI 4.1.2 - Clasificación completada")
    print("Archivo generado:", ruta_destino)
    print("Artículos:", informe.total_articulos)
    print("A revisar:", informe.total_revisar)
    print("Resumen tipos:", informe.resumen_tipos)


if __name__ == "__main__":
    main()
