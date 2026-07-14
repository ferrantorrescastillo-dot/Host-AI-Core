from pathlib import Path
import sys

"""Punto de entrada oficial de Host AI (piloto).

Flujo de arranque documentado:
1) Entrada al sistema (`main`).
2) Creación/resolución de `BASE_DIR`.
3) Delegación al lanzador (`SERVICIOS.lanzador_piloto_01.ejecutar_piloto_01`).

Este módulo mantiene un único `main()` ligero que delega la lógica al
lanzador para mantener la responsabilidad clara.
"""

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main() -> None:
    """Entrada principal: inicialización, arranque y manejo mínimo de errores.

    - Inicialización: resolvemos rutas y evitamos efectos secundarios en
      la importación global.
    - Arranque: delegamos en `ejecutar_piloto_01`.
    - Gestión de errores: se captura la excepción para loguear, y se
      relanza para no alterar el comportamiento externo.
    """

    # Inicialización (import local para evitar efectos al importar el módulo)
    from SERVICIOS.lanzador_piloto_01 import ejecutar_piloto_01

    # Arranque — delegación explícita a la función del lanzador.
    try:
        ejecutar_piloto_01(BASE_DIR)
    except Exception as exc:  # Mantener comportamiento: relanzamos después de logging
        print(f"Error en arranque de Host AI: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
