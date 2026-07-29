from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Callable, Dict, Optional


@dataclass(frozen=True)
class EstadoArranque603:
    ok: bool
    base_dir: str
    elementos: Dict[str, bool]


class LanzadorHostAIBase603:
    """Punto de entrada de compatibilidad legacy para Host AI Base 6.0.3.

    Freeze-A1: esta ruta se conserva por compatibilidad histórica y QA.
    No sustituye la ruta oficial de arranque de Core 1.0.

    Separa la operativa diaria del restaurante de las herramientas técnicas.
    No contiene lógica de negocio: únicamente crea el core y dirige al usuario
    hacia interfaces que reutilizan los motores existentes.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self._asegurar_pythonpath()

    def _asegurar_pythonpath(self) -> None:
        ruta = str(self.base_dir)
        if ruta not in sys.path:
            sys.path.insert(0, ruta)

    def validar_estructura(self) -> EstadoArranque603:
        elementos = {
            "CORE": (self.base_dir / "CORE").is_dir(),
            "APP": (self.base_dir / "APP").is_dir(),
            "SERVICIOS": (self.base_dir / "SERVICIOS").is_dir(),
            "main.py": (self.base_dir / "main.py").is_file(),
            "consola_base": (self.base_dir / "APP" / "consola.py").is_file(),
            "core": (self.base_dir / "CORE" / "host_ai_core.py").is_file(),
            "bootloader_tecnico": (
                self.base_dir / "SERVICIOS" / "bootloader_host_ai_502.py"
            ).is_file(),
        }
        return EstadoArranque603(
            ok=all(elementos.values()),
            base_dir=str(self.base_dir),
            elementos=elementos,
        )

    def abrir_base_operativa(self) -> None:
        estado = self.validar_estructura()
        if not estado.ok:
            faltan = [nombre for nombre, existe in estado.elementos.items() if not existe]
            raise RuntimeError(
                "No se puede iniciar Host AI Base. Faltan: " + ", ".join(faltan)
            )

        from APP.consola import AppConsolaHostAI
        from CORE.host_ai_core import HostAICore

        core = HostAICore(self.base_dir)
        AppConsolaHostAI(core).ejecutar()

    def abrir_conversacion(self) -> None:
        # Mantiene el chat actual como acceso independiente, sin sustituir el Base.
        from SERVICIOS.bootloader_host_ai_502 import BootloaderHostAI502

        resultado = BootloaderHostAI502(self.base_dir).ejecutar_opcion("1")
        if not resultado.get("ok"):
            raise RuntimeError(resultado.get("error") or "No se pudo abrir la conversación")

    def abrir_herramientas_tecnicas(self) -> None:
        from SERVICIOS.bootloader_host_ai_502 import ejecutar_menu

        ejecutar_menu(self.base_dir)

    def ejecutar_menu(
        self,
        input_fn: Callable[[str], str] = input,
        print_fn: Callable[..., None] = print,
    ) -> None:
        while True:
            print_fn("=" * 70)
            print_fn("HOST AI BASE 6.0.3")
            print_fn("Punto de entrada operativo")
            print_fn("=" * 70)
            print_fn("1. Abrir Host AI Base (modo manual)")
            print_fn("2. Hablar con Host AI")
            print_fn("9. Herramientas técnicas y pruebas")
            print_fn("0. Salir")

            opcion = input_fn("Elige una opción: ").strip()
            try:
                if opcion == "1":
                    self.abrir_base_operativa()
                elif opcion == "2":
                    self.abrir_conversacion()
                elif opcion == "9":
                    self.abrir_herramientas_tecnicas()
                elif opcion == "0":
                    print_fn("Saliendo de Host AI.")
                    return
                else:
                    print_fn("Opción no válida.")
            except (KeyboardInterrupt, EOFError):
                print_fn("\nOperación cancelada. Volviendo al menú principal.")
            except Exception as exc:
                print_fn(f"No se pudo abrir la opción: {exc}")


def ejecutar_host_ai(base_dir: Optional[Path] = None) -> None:
    LanzadorHostAIBase603(base_dir).ejecutar_menu()


__all__ = ["EstadoArranque603", "LanzadorHostAIBase603", "ejecutar_host_ai"]
