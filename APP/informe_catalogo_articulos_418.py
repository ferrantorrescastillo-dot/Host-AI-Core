from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.informe_catalogo_articulos_418 import InformeCatalogoArticulos418


def main():
    ruta_db = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_informe = ROOT / "DATOS" / "db" / "informe_catalogo_articulos_4_1_8.txt"

    generador = InformeCatalogoArticulos418(str(ruta_db))
    informe = generador.exportar_txt(str(ruta_informe))

    print("HOST AI 4.1.8 - Informe Catálogo de Artículos")
    print("Archivo generado:", ruta_informe)
    print("Artículos:", informe.total_articulos)
    print("Activos:", informe.activos)
    print("Sin proveedor:", informe.sin_proveedor)
    print("Sin familia:", informe.sin_familia)
    print("Sin precio:", informe.sin_precio)
    print("Precio cero:", informe.precio_cero)
    print("Estado:", informe.estado)
    print("")
    print("Recomendaciones:")
    for recomendacion in informe.recomendaciones:
        print("-", recomendacion)


if __name__ == "__main__":
    main()
