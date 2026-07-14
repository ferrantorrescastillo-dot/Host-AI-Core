from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def main() -> int:
    raiz = Path(__file__).resolve().parent
    env = os.environ.copy()
    env["PYTHONPATH"] = str(raiz) + os.pathsep + env.get("PYTHONPATH", "")
    comando = [sys.executable, "-m", "pytest", "-q"]
    proceso = subprocess.run(comando, cwd=raiz, env=env, text=True, capture_output=True)

    salida = (proceso.stdout or "") + ("\n" + proceso.stderr if proceso.stderr else "")
    estado = "APROBADA" if proceso.returncode == 0 else "NO APROBADA"
    informe = raiz / "INFORME_RR1.6.2_AUTOMATICO.md"
    informe.write_text(
        "# Informe automático RR1.6.2\n\n"
        f"- Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
        f"- Estado: **{estado}**\n"
        f"- Comando: `{' '.join(comando)}`\n\n"
        "## Resultado\n\n"
        "```text\n" + salida.strip() + "\n```\n\n"
        "## Nota\n\n"
        "La aprobación automática no sustituye la checklist manual del evento completo.\n",
        encoding="utf-8",
    )
    print(salida.strip())
    print(f"\nInforme generado: {informe.name}")
    return proceso.returncode


if __name__ == "__main__":
    raise SystemExit(main())
