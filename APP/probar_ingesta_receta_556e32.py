from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.ingesta_recetas_lenguaje_natural_556e32 import AnalizadorRecetasLenguajeNatural556E32


def main() -> int:
    parser = argparse.ArgumentParser(description="Vista previa de una receta escrita en lenguaje natural")
    parser.add_argument("receta")
    parser.add_argument("--archivo", help="TXT/MD con el proceso. Si se omite, lee stdin.")
    parser.add_argument("--rendimiento", type=float, default=1)
    parser.add_argument("--unidad", default="u")
    parser.add_argument("--confirmar", action="store_true")
    args = parser.parse_args()

    texto = Path(args.archivo).read_text(encoding="utf-8") if args.archivo else sys.stdin.read()
    motor = AnalizadorRecetasLenguajeNatural556E32(BASE_DIR)
    resultado = motor.analizar(args.receta, texto, args.rendimiento, args.unidad)
    print(resultado.get("mensaje", ""))
    if args.confirmar and resultado.get("ok"):
        guardado = motor.guardar_confirmado(resultado["ficha"])
        print("\n" + guardado.get("mensaje", ""))
    return 0 if resultado.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
