from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main() -> None:
        """Punto de entrada único y oficial de Host AI 6.0 — línea piloto.

        Estructura:
        - Inicialización: resolvemos rutas y cargamos el lanzador.
        - Arranque: delegamos en `ejecutar_piloto_01`.
        - Gestión de errores: capturamos excepciones para dejar claro el
            punto de control sin alterar el comportamiento (se relanza la
            excepción tras el log).
        - Finalización: no hay finalización especial aquí; el lanzador
            controla el flujo de vida de la aplicación.
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
