from __future__ import annotations

"""Lanzador del Piloto 01.

Rol y responsabilidades en el ciclo de vida de arranque:

1) Inicio de la aplicación: `main()` delega aquí la ejecución.
2) Inicialización del núcleo: valida auditoría y crea `HostAICore`.
3) Ejecución del piloto: instancia y ejecuta `ConsolaPiloto01`.
4) Gestión de errores: el método `ejecutar()` controla errores de menú y
    muestra mensajes al usuario sin modificar la lógica subyacente.
5) Finalización: la consola o el lanzador deciden cuándo terminar el proceso.

Este módulo documenta su responsabilidad y mantiene la delegación de
funciones a `CORE` y `APP` sin introducir cambios de comportamiento.
"""

from pathlib import Path
import sys
from typing import Callable, Optional

from SERVICIOS.auditor_arranque_piloto_01 import AuditorArranquePiloto01
from SERVICIOS.certificador_piloto_01 import CertificadorPiloto01


class LanzadorPiloto01:
    """Punto de entrada único y estable de Host AI para el piloto privado."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Inicializa el lanzador y asegura que `base_dir` esté en `sys.path`.

        `base_dir` puede ser `None` — por defecto se usa el directorio de trabajo
        actual resuelto.
        """
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        ruta = str(self.base_dir)
        if ruta not in sys.path:
            sys.path.insert(0, ruta)

    def abrir_modo_piloto(self) -> None:
        """Inicia la consola de piloto tras validar la auditoría mínima.

        Se importa localmente `HostAICore` y `ConsolaPiloto01` para evitar
        sobrecargar el import en el módulo y mantener el comportamiento.
        """
        auditoria = AuditorArranquePiloto01(self.base_dir).ejecutar(importar_modulos=False)
        if not auditoria["ok"]:
            raise RuntimeError("La línea base requiere revisión antes de abrir el modo piloto.")

        from CORE.host_ai_core import HostAICore
        from APP.consola_piloto_01 import ConsolaPiloto01

        ConsolaPiloto01(HostAICore(self.base_dir)).ejecutar()

    def abrir_modo_desarrollo(self) -> None:
        from SERVICIOS.host_ai_launcher import HostAILauncher

        HostAILauncher(self.base_dir).ejecutar()

    def mostrar_auditoria(self, print_fn: Callable[..., None] = print) -> dict:
        """Ejecuta y muestra la auditoría de arranque.

        Devuelve el diccionario resultado para permitir usos programáticos.
        """
        resultado = AuditorArranquePiloto01(self.base_dir).ejecutar(importar_modulos=True)
        print_fn("\nAUDITORÍA DE ARRANQUE PILOTO-0.1")
        print_fn("=" * 70)
        print_fn(f"Estado: {resultado['estado']} | Errores: {resultado['errores']} | Avisos: {resultado['avisos']}")
        for item in resultado["comprobaciones"]:
            print_fn(f"- {item['codigo']}: {'OK' if item['ok'] else 'REVISAR'}")
        return resultado

    def certificar(self, print_fn: Callable[..., None] = print) -> dict:
        """Ejecuta la certificación y muestra los enlaces al informe si existen."""
        resultado = CertificadorPiloto01(self.base_dir).ejecutar(guardar_informe=True)
        print_fn("\n" + CertificadorPiloto01.formatear(resultado))
        if resultado.get("informe_json"):
            print_fn(f"Informe JSON: {resultado['informe_json']}")
            print_fn(f"Informe TXT: {resultado['informe_txt']}")
        return resultado

    def ejecutar(
        self,
        input_fn: Callable[[str], str] = input,
        print_fn: Callable[..., None] = print,
    ) -> None:
        """Bucle principal que muestra el menú y delega en los manejadores.

        Separé la renderización del menú y el manejo de opciones para mejorar
        la lectura manteniendo el comportamiento original.
        """

        while True:
            # Renderización del menú
            print_fn("=" * 70)
            print_fn("HOST AI 6.0 — LÍNEA BASE PILOTO")
            print_fn("=" * 70)
            print_fn("1. Modo Piloto privado")
            print_fn("2. Modo Desarrollo y herramientas técnicas")
            print_fn("8. Auditoría de arranque")
            print_fn("9. Certificar PILOTO-0.1")
            print_fn("0. Salir")

            opcion = input_fn("Elige una opción: ").strip()

            # Manejo de la opción seleccionada (mismos comandos que antes)
            try:
                if opcion == "1":
                    self.abrir_modo_piloto()
                elif opcion == "2":
                    self.abrir_modo_desarrollo()
                elif opcion == "8":
                    self.mostrar_auditoria(print_fn)
                elif opcion == "9":
                    self.certificar(print_fn)
                elif opcion == "0":
                    print_fn("Saliendo de Host AI.")
                    return
                else:
                    print_fn("Opción no válida.")
            except (KeyboardInterrupt, EOFError):
                print_fn("\nOperación cancelada.")
            except Exception as exc:
                print_fn(f"No se pudo abrir la opción: {exc}")


def ejecutar_piloto_01(base_dir: Optional[Path] = None) -> None:
    LanzadorPiloto01(base_dir).ejecutar()


__all__ = ["LanzadorPiloto01", "ejecutar_piloto_01"]
