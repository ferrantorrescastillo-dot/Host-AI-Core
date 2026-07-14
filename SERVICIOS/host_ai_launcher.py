from __future__ import annotations

import runpy
import sys
from pathlib import Path
from typing import Optional


class HostAILauncher:
    """
    Lanzador oficial de Host AI 6.x.

    Separa:
    - el uso diario manual del restaurante,
    - la conversación,
    - y las herramientas técnicas heredadas.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self._asegurar_pythonpath()

    def _asegurar_pythonpath(self) -> None:
        ruta = str(self.base_dir)
        if ruta not in sys.path:
            sys.path.insert(0, ruta)

    def validar_estructura(self) -> dict[str, object]:
        requeridos = {
            "APP": self.base_dir / "APP",
            "CORE": self.base_dir / "CORE",
            "SERVICIOS": self.base_dir / "SERVICIOS",
            "main.py": self.base_dir / "main.py",
            "APP/consola.py": self.base_dir / "APP" / "consola.py",
            "CORE/host_ai_core.py": self.base_dir / "CORE" / "host_ai_core.py",
            "bootloader técnico": self.base_dir / "SERVICIOS" / "bootloader_host_ai_502.py",
        }
        estado = {nombre: ruta.exists() for nombre, ruta in requeridos.items()}
        estado["ok"] = all(estado.values())
        estado["base_dir"] = str(self.base_dir)
        return estado

    def abrir_host_ai_base(self) -> None:
        """
        Abre la consola manual recuperada de Host AI 3,
        usando el núcleo y los datos de la versión actual.
        """
        self._asegurar_pythonpath()
        try:
            from CORE.host_ai_core import HostAICore
            from APP.consola import AppConsolaHostAI

            core = HostAICore(self.base_dir)
            app = AppConsolaHostAI(core)
            app.ejecutar()
        except Exception as exc:
            print("\nNo se ha podido abrir Host AI Base.")
            print(f"Error: {exc!r}")
            print("No se han modificado datos por este error.")

    def abrir_conversacion(self) -> None:
        """Abre el orquestador conversacional actual."""
        self._asegurar_pythonpath()
        try:
            runpy.run_module("APP.orquestador_inteligente_52", run_name="__main__")
        except SystemExit:
            pass
        except Exception as exc:
            print("\nNo se ha podido abrir Host AI Conversacional.")
            print(f"Error: {exc!r}")

    def abrir_herramientas_tecnicas(self) -> None:
        """
        Mantiene íntegro el bootloader 5.2 para auditorías,
        tests, QA y utilidades de desarrollo.
        """
        self._asegurar_pythonpath()
        try:
            from SERVICIOS.bootloader_host_ai_502 import ejecutar_menu

            ejecutar_menu(self.base_dir)
        except Exception as exc:
            print("\nNo se han podido abrir las herramientas técnicas.")
            print(f"Error: {exc!r}")

    @staticmethod
    def imprimir_cabecera() -> None:
        print("=" * 70)
        print("HOST AI 6.0")
        print("Lanzador oficial")
        print("=" * 70)

    @staticmethod
    def imprimir_menu() -> None:
        print("\nMENÚ PRINCIPAL")
        print("1. Host AI Base - Trabajo diario manual")
        print("2. Host AI Conversacional")
        print("3. Herramientas técnicas, auditorías y pruebas")
        print("9. Comprobar estructura")
        print("0. Salir")

    def imprimir_estado(self) -> None:
        estado = self.validar_estructura()
        print("\nESTADO DEL PROYECTO")
        print(f"Raíz: {estado['base_dir']}")
        for clave, valor in estado.items():
            if clave not in {"ok", "base_dir"}:
                print(f"- {clave}: {'OK' if valor else 'NO ENCONTRADO'}")
        print(f"Estado general: {'OK' if estado['ok'] else 'REVISAR'}")

    def ejecutar(self) -> None:
        self.imprimir_cabecera()

        while True:
            self.imprimir_menu()
            opcion = input("Elige una opción: ").strip()

            if opcion == "1":
                self.abrir_host_ai_base()
            elif opcion == "2":
                self.abrir_conversacion()
            elif opcion == "3":
                self.abrir_herramientas_tecnicas()
            elif opcion == "9":
                self.imprimir_estado()
            elif opcion == "0":
                print("Saliendo de Host AI.")
                break
            else:
                print("Opción no válida.")


def ejecutar_launcher(base_dir: Optional[Path] = None) -> None:
    HostAILauncher(base_dir).ejecutar()


__all__ = ["HostAILauncher", "ejecutar_launcher"]
