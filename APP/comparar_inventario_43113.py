from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.comparador_inventario_43113 import ComparadorInventario43113


def main():
    ruta_inventario = ROOT / "DATOS" / "db" / "inventario_contado_4_3_11_2.json"
    ruta_json = ROOT / "DATOS" / "db" / "comparacion_inventario_4_3_11_3.json"
    ruta_txt = ROOT / "DATOS" / "db" / "comparacion_inventario_4_3_11_3.txt"

    comparador = ComparadorInventario43113(str(ruta_inventario))
    informe = comparador.exportar(str(ruta_json), str(ruta_txt))

    print("HOST AI 4.3.11.3 - Comparador Inventario")
    print("JSON generado:", ruta_json)
    print("TXT generado:", ruta_txt)
    print("Artículos contados:", informe.total_contados)
    print("OK:", informe.ok)
    print("Faltantes:", informe.faltantes)
    print("Sobrantes:", informe.sobrantes)
    print("Revisar:", informe.revisar)
    print("Estado general:", informe.estado_general)


if __name__ == "__main__":
    main()
