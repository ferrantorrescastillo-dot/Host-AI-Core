from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.auditor_modelo_escandallos_555a import auditar_modelo_555a, formatear_informe_555a
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos


def main() -> int:
    repositorio = RepositorioEscandallos(RAIZ / "DATOS" / "db" / "escandallos_canonicos.json")
    informe = auditar_modelo_555a(repositorio)
    print(formatear_informe_555a(informe))
    return 0 if informe.estado == "MODELO_CANONICO_APROBADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
