from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.alta_articulos_recepcion_444 import AltaArticulosDesdeRecepcion444


def main():
    ruta_borrador = ROOT / "DATOS" / "db" / "recepcion_borrador_4_4_2.json"
    ruta_articulos = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_json = ROOT / "DATOS" / "db" / "articulos_nuevos_recepcion_4_4_4.json"
    ruta_txt = ROOT / "DATOS" / "db" / "articulos_nuevos_recepcion_4_4_4.txt"

    familia_default = "Pendiente clasificar"
    if len(sys.argv) >= 2:
        familia_default = sys.argv[1]

    alta = AltaArticulosDesdeRecepcion444(str(ruta_borrador), str(ruta_articulos))
    resultado = alta.crear_y_exportar(str(ruta_json), str(ruta_txt), familia_default=familia_default)

    print("HOST AI 4.4.4 - Alta Artículos Nuevos desde Recepción")
    print("JSON generado:", ruta_json)
    print("TXT generado:", ruta_txt)
    print("Estado:", resultado.estado)
    print("Pendientes detectados:", resultado.total_pendientes)
    print("Creados:", resultado.creados)
    print("No creados:", resultado.no_creados)

    for item in resultado.articulos:
        print(f"- {item.producto_texto}: creado={item.creado}, código={item.codigo_creado}, msg={item.mensaje}")


if __name__ == "__main__":
    main()
