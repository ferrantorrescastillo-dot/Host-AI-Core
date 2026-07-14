from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.clasificador_familias_articulos_419 import ClasificadorFamiliasArticulos419


def main():
    ruta_db = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_informe = ROOT / "DATOS" / "db" / "informe_familias_4_1_9.txt"

    clasificador = ClasificadorFamiliasArticulos419(str(ruta_db))
    informe = clasificador.exportar_informe_txt(str(ruta_informe))

    print("HOST AI 4.1.9 - Clasificador de Familias")
    print("Archivo informe:", ruta_informe)
    print("Artículos:", informe.total_articulos)
    print("Sin familia antes:", informe.sin_familia_antes)
    print("Familias aplicadas:", informe.familias_aplicadas)
    print("Sin familia después:", informe.sin_familia_despues)
    print("Estado:", informe.estado)


if __name__ == "__main__":
    main()
