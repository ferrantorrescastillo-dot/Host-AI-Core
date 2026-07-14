from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.motor_reparto_cocineros_556e3 import MotorRepartoCocineros556E3, formatear_reparto_556e3


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba el reparto de producciones entre cocineros.")
    parser.add_argument("receta")
    parser.add_argument("objetivo", type=float)
    parser.add_argument("--unidad", default="personas")
    parser.add_argument("--cocineros", type=int, default=3)
    parser.add_argument("--inicio", default="08:00")
    parser.add_argument("--fin", default="15:30")
    args = parser.parse_args()
    motor = MotorRepartoCocineros556E3(ROOT)
    resultado = motor.repartir(
        [{"receta": args.receta, "objetivo": args.objetivo, "unidad": args.unidad}],
        cocineros=args.cocineros,
        inicio_jornada=args.inicio,
        fin_jornada=args.fin,
    )
    print(formatear_reparto_556e3(resultado))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
