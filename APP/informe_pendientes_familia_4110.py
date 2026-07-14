from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.informe_pendientes_familia_4110 import InformePendientesFamilia4110


def main():
    ruta_db = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_informe = ROOT / "DATOS" / "db" / "pendientes_familia_4_1_10.txt"

    generador = InformePendientesFamilia4110(str(ruta_db))
    informe = generador.exportar_txt(str(ruta_informe))

    print("HOST AI 4.1.10 - Informe Pendientes de Familia")
    print("Archivo generado:", ruta_informe)
    print("Artículos:", informe.total_articulos)
    print("Pendientes sin familia:", informe.pendientes)
    print("Estado:", informe.estado)
    print("")
    print("Top proveedores pendientes:")
    for proveedor, cantidad in list(informe.por_proveedor.items())[:10]:
        print(f"- {proveedor}: {cantidad}")


if __name__ == "__main__":
    main()
