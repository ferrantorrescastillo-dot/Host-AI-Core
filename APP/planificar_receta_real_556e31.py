from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.motor_planificacion_recetas_reales_556e31 import MotorPlanificacionRecetasReales556E31, formatear_plan_real_556e31


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("receta")
    p.add_argument("objetivo", type=float)
    p.add_argument("--unidad", default="personas")
    p.add_argument("--cocineros", type=int, default=3)
    p.add_argument("--inicio", default="08:00")
    p.add_argument("--fin", default="15:30")
    args = p.parse_args()
    r = MotorPlanificacionRecetasReales556E31(ROOT).planificar(args.receta, args.objetivo, args.unidad, args.cocineros, args.inicio, args.fin)
    print(formatear_plan_real_556e31(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
