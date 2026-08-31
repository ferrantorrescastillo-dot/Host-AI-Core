from pathlib import Path
import sys

"""Punto de entrada oficial de Host AI Core 1.0 (Freeze-A1).

Define y documenta el ciclo de vida de arranque (solo documentación,
sin cambiar comportamiento):

1) Inicio de la aplicación: `main()` — resuelve `BASE_DIR` y prepara imports.
2) Inicialización del núcleo: `HostAICore` es creado por el lanzador.
3) Ejecución del piloto: `LanzadorPiloto01` invoca la consola de piloto.
4) Gestión de errores: `main()` captura y re-lanza excepciones para no
  ocultar fallos (el lanzador gestiona errores en el menú interactivo).
5) Finalización: la finalización es responsabilidad del lanzador/consola.

Ruta oficial de arranque (única):

main.py
-> SERVICIOS.lanzador_piloto_01.ejecutar_piloto_01
-> LanzadorPiloto01.ejecutar
-> opción 1: abrir_modo_piloto
-> APP.consola_piloto_01.ConsolaPiloto01

Las demás rutas de entrada quedan clasificadas como desarrollo, QA o
compatibilidad y no sustituyen esta ruta oficial.
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
