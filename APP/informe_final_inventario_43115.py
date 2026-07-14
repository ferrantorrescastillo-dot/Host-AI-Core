from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.informe_final_inventario_43115 import InformeFinalInventario43115


def main():
    ruta_comparacion = ROOT / "DATOS" / "db" / "comparacion_inventario_4_3_11_3.json"
    ruta_movimientos = ROOT / "DATOS" / "db" / "stock_movimientos.json"
    ruta_informe = ROOT / "DATOS" / "db" / "informe_final_inventario_4_3_11_5.txt"

    informeador = InformeFinalInventario43115(str(ruta_comparacion), str(ruta_movimientos))
    informe = informeador.exportar_txt(str(ruta_informe))

    print("HOST AI 4.3.11.5 - Informe Final Inventario")
    print("Archivo generado:", ruta_informe)
    print("Artículos contados:", informe.total_contados)
    print("OK:", informe.ok)
    print("Faltantes:", informe.faltantes)
    print("Sobrantes:", informe.sobrantes)
    print("Revisar:", informe.revisar)
    print("Ajustes aplicados:", informe.ajustes_aplicados)
    print("Estado final:", informe.estado_final)
    print("")
    print("Recomendaciones:")
    for rec in informe.recomendaciones:
        print("-", rec)


if __name__ == "__main__":
    main()
