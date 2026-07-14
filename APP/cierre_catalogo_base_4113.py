from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.cierre_catalogo_base_4113 import CierreCatalogoBase4113


def main():
    ruta_articulos = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_proveedores = ROOT / "DATOS" / "db" / "proveedores.json"
    ruta_informe = ROOT / "DATOS" / "db" / "cierre_catalogo_base_4_1_13.txt"

    cierre = CierreCatalogoBase4113(str(ruta_articulos), str(ruta_proveedores))
    informe = cierre.exportar_txt(str(ruta_informe))

    print("HOST AI 4.1.13 - Cierre Catálogo Base")
    print("Archivo generado:", ruta_informe)
    print("Artículos:", informe.total_articulos)
    print("Proveedores:", informe.total_proveedores)
    print("Sin proveedor:", informe.sin_proveedor)
    print("Sin familia:", informe.sin_familia)
    print("Sin precio:", informe.sin_precio)
    print("Precio cero:", informe.precio_cero)
    print("Proveedores con variantes:", informe.proveedores_con_variantes)
    print("Estado:", informe.estado)
    print("Bloque siguiente:", informe.bloque_siguiente)
    print("")
    print("Recomendaciones:")
    for recomendacion in informe.recomendaciones:
        print("-", recomendacion)


if __name__ == "__main__":
    main()
