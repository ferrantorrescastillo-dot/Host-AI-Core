from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from SERVICIOS.cruce_stock_produccion_556c import CruceStockProduccion556C, formatear_cruce_stock_556c
from SERVICIOS.planificador_produccion_556d import PlanificadorProduccion556D, formatear_plan_556d

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("receta")
    p.add_argument("objetivo", type=float)
    p.add_argument("--unidad", default="personas")
    p.add_argument("--plan", action="store_true")
    a = p.parse_args()
    if a.plan:
        print(formatear_plan_556d(PlanificadorProduccion556D(ROOT).generar(a.receta, a.objetivo, a.unidad)))
    else:
        print(formatear_cruce_stock_556c(CruceStockProduccion556C(ROOT).cruzar(a.receta, a.objetivo, a.unidad)))
    return 0
if __name__ == "__main__": raise SystemExit(main())
