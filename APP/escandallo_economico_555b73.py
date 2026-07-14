from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.conector_escandallos_real_555 import procesar_consulta_escandallos_real_555


def main() -> int:
    consulta = " ".join(sys.argv[1:]).strip() or "Muéstrame el escandallo de ensaladilla de gamba"
    resultado = procesar_consulta_escandallos_real_555(consulta, RAIZ)
    print(resultado.get("mensaje", "Consulta no gestionada."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
