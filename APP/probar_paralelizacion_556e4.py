from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.motor_paralelizacion_produccion_556e4 import MotorParalelizacionProduccion556E4, formatear_paralelizacion_556e4


def _produccion(valor: str):
    try:
        receta, objetivo = valor.rsplit(":", 1)
        return {"receta": receta.strip(), "objetivo": float(objetivo), "unidad": "personas"}
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Usa el formato 'Receta:150'.") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera un cronograma paralelo para varias producciones.")
    parser.add_argument("--produccion", action="append", type=_produccion, required=True)
    parser.add_argument("--cocineros", type=int, default=3)
    parser.add_argument("--inicio", default="08:00")
    parser.add_argument("--fin", default="15:30")
    args = parser.parse_args()
    motor = MotorParalelizacionProduccion556E4(ROOT)
    resultado = motor.planificar(args.produccion, args.cocineros, args.inicio, args.fin)
    print(formatear_paralelizacion_556e4(resultado))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
