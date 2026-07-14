from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.auditor_cierre_escandallos_555b74 import AuditorCierreEscandallos555B74, formatear_auditoria_555b74


def main() -> int:
    resultado = AuditorCierreEscandallos555B74(RAIZ).auditar()
    print(formatear_auditoria_555b74(resultado))
    informe = RAIZ / "DATOS" / "informes" / "auditoria_cierre_555b74.json"
    informe.parent.mkdir(parents=True, exist_ok=True)
    informe.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nInforme guardado: {informe.relative_to(RAIZ)}")
    return 1 if resultado.get("estado") == "CIERRE_NO_APROBADO" else 0


if __name__ == "__main__":
    raise SystemExit(main())
