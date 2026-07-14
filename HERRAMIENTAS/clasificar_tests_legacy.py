from __future__ import annotations

import argparse
import shutil
from pathlib import Path

CANDIDATOS = [
    Path("TESTS/test_5412_confirmaciones_inteligentes.py"),
    Path("TESTS/test_5413_conversacion_natural.py"),
    Path("TESTS/test_556e4_paralelizacion.py"),
    Path("HOST_AI_6.0.3_MODO_MANUAL_OPERATIVO/TESTS/test_603_lanzador_base_operativa.py"),
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clasifica tests legacy conocidos. Por defecto solo muestra el plan."
    )
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="Mueve los tests encontrados a TESTS_LEGACY conservando su ruta relativa.",
    )
    args = parser.parse_args()

    raiz = Path(__file__).resolve().parents[1]
    encontrados = [ruta for ruta in CANDIDATOS if (raiz / ruta).exists()]
    if not encontrados:
        print("No se encontraron los tests legacy conocidos. No se ha modificado nada.")
        return 0

    print("Tests legacy detectados:")
    for ruta in encontrados:
        print(f"- {ruta.as_posix()}")

    if not args.aplicar:
        print("\nModo simulación. No se ha movido ningún archivo.")
        print("Para aplicar: python HERRAMIENTAS\\clasificar_tests_legacy.py --aplicar")
        return 0

    destino_base = raiz / "TESTS_LEGACY"
    for relativa in encontrados:
        origen = raiz / relativa
        destino = destino_base / relativa
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(origen), str(destino))
        print(f"Movido: {relativa.as_posix()} -> {destino.relative_to(raiz).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
