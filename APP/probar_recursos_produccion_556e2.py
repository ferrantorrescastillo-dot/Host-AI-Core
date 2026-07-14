from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from SERVICIOS.motor_recursos_produccion_556e2 import MotorRecursosProduccion556E2, formatear_recursos_556e2

def main()->int:
    p=argparse.ArgumentParser(description='Host AI 5.5.6E.2 - Recursos de producción')
    p.add_argument('receta'); p.add_argument('objetivo',type=float); p.add_argument('--unidad',default='personas')
    a=p.parse_args(); print(formatear_recursos_556e2(MotorRecursosProduccion556E2(ROOT).analizar(a.receta,a.objetivo,a.unidad))); return 0
if __name__=='__main__': raise SystemExit(main())
