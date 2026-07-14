from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.generador_codigos_articulos_413 import GeneradorCodigosArticulos413


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print('python APP\\generar_codigos_articulos_413.py "C:\\Ruta\\Escandallos Boronat  (HostIA).xlsx"')
        return

    ruta_excel = Path(sys.argv[1]).resolve()
    if not ruta_excel.exists():
        print(f"No existe el archivo: {ruta_excel}")
        return

    ruta_destino = ruta_excel.with_name(ruta_excel.stem + "_CODIGOS_4_1_3.xlsx")

    generador = GeneradorCodigosArticulos413()
    informe = generador.exportar_excel_con_codigos(str(ruta_excel), str(ruta_destino))

    print("HOST AI 4.1.3 - Códigos generados")
    print("Archivo generado:", ruta_destino)
    print("Artículos:", informe.total_articulos)
    print("Códigos generados:", informe.codigos_generados)
    print("Códigos respetados:", informe.codigos_respetados)
    print("Códigos duplicados:", informe.codigos_duplicados)
    print("A revisar:", informe.total_revisar)


if __name__ == "__main__":
    main()
