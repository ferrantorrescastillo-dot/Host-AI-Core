from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.escalador_explosion_recetas_556ab import (
    MotorEscaladoExplosion556AB,
    RecetaAmbigua556AB,
    formatear_escalado_556ab,
    formatear_explosion_556ab,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Host AI 5.5.6AB.1 - Escalado, explosión y selección de variantes")
    parser.add_argument("receta")
    parser.add_argument("objetivo", type=float)
    parser.add_argument("--unidad", default="personas")
    parser.add_argument("--desglosar", action="store_true")
    args = parser.parse_args()

    motor = MotorEscaladoExplosion556AB(ROOT)
    termino = args.receta
    try:
        resultado = motor.explotar(termino, args.objetivo, args.unidad) if args.desglosar else motor.escalar(termino, args.objetivo, args.unidad)
    except RecetaAmbigua556AB as exc:
        print(f"HE ENCONTRADO VARIAS RECETAS PARA: {exc.termino}\n")
        for i, opcion in enumerate(exc.opciones, 1):
            print(f"{i}. {opcion['nombre']} — {opcion['rendimiento']:g} {opcion['unidad_rendimiento']} — {opcion['origen']}")
        while True:
            valor = input("\nElige una opción (o 0 para cancelar): ").strip()
            if valor == "0":
                print("Selección cancelada. Datos reales modificados: NO.")
                return 0
            if valor.isdigit() and 1 <= int(valor) <= len(exc.opciones):
                termino = exc.opciones[int(valor)-1]["nombre"]
                break
            print("Opción no válida.")
        resultado = motor.explotar(termino, args.objetivo, args.unidad) if args.desglosar else motor.escalar(termino, args.objetivo, args.unidad)
    print(formatear_explosion_556ab(resultado) if args.desglosar else formatear_escalado_556ab(resultado))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
