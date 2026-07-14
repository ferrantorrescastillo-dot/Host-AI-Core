from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.informe_proveedores_423 import InformeProveedores423


def main():
    ruta_proveedores = ROOT / "DATOS" / "db" / "proveedores.json"
    ruta_articulos = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_informe = ROOT / "DATOS" / "db" / "informe_proveedores_4_2_3.txt"

    generador = InformeProveedores423(str(ruta_proveedores), str(ruta_articulos))
    informe = generador.exportar_txt(str(ruta_informe))

    print("HOST AI 4.2.3 - Informe de Proveedores")
    print("Archivo generado:", ruta_informe)
    print("Proveedores:", informe.total_proveedores)
    print("Activos:", informe.proveedores_activos)
    print("Con variantes:", informe.proveedores_con_variantes)
    print("Artículos sin proveedor:", informe.articulos_sin_proveedor)
    print("Estado:", informe.estado)
    print("")
    print("Recomendaciones:")
    for recomendacion in informe.recomendaciones:
        print("-", recomendacion)


if __name__ == "__main__":
    main()
