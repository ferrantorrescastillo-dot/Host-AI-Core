from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.runner_tests_4412 import RunnerTests4412


def main() -> None:
    runner = RunnerTests4412(BASE_DIR)
    while True:
        print("\n" + "=" * 60)
        print("HOST AI TEST CENTER - 4.4.12")
        print("=" * 60)
        print("1. Catálogo")
        print("2. Proveedores")
        print("3. Stock")
        print("4. Recepción")
        print("5. Compras")
        print("6. Producción")
        print("7. IA")
        print("8. Todos")
        print("0. Salir")
        opcion = input("Selecciona bloque: ").strip()
        if opcion == "0":
            print("Saliendo del Test Center.")
            return
        if opcion not in runner.BLOQUES:
            print("Opción no válida.")
            continue
        archivos = runner.descubrir_tests(opcion)
        print(f"\nTests detectados: {len(archivos)}")
        if not archivos:
            print("No hay tests para este bloque.")
            continue
        confirmar = input("¿Ejecutar ahora? (s/n): ").strip().lower()
        if confirmar not in {"s", "si", "sí", "y", "yes"}:
            continue
        informe = runner.ejecutar_bloque(opcion)
        runner.imprimir_informe(informe)


if __name__ == "__main__":
    main()
