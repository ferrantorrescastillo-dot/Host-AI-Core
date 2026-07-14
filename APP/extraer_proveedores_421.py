from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.extractor_proveedores_421 import ExtractorProveedores421


def main():
    ruta_articulos = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_proveedores = ROOT / "DATOS" / "db" / "proveedores.json"

    extractor = ExtractorProveedores421(str(ruta_articulos), str(ruta_proveedores))
    informe = extractor.extraer()

    print("HOST AI 4.2.1 - Extractor de Proveedores")
    print("Artículos:", informe.total_articulos)
    print("Proveedores detectados:", informe.proveedores_detectados)
    print("Artículos sin proveedor:", informe.articulos_sin_proveedor)
    print("Duplicados sospechosos:", informe.duplicados_sospechosos)
    print("Archivo generado:", informe.ruta_destino)
    print("Estado:", informe.estado)
    print("")
    print("Recomendaciones:")
    for recomendacion in informe.recomendaciones:
        print("-", recomendacion)


if __name__ == "__main__":
    main()
