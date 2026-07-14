from __future__ import annotations

from pathlib import Path
import sys
from typing import Callable, Optional

from SERVICIOS.auditor_arranque_piloto_01 import AuditorArranquePiloto01
from SERVICIOS.certificador_piloto_01 import CertificadorPiloto01


class LanzadorPiloto01:
    """Punto de entrada único y estable de Host AI para el piloto privado."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        ruta = str(self.base_dir)
        if ruta not in sys.path:
            sys.path.insert(0, ruta)

    def abrir_modo_piloto(self) -> None:
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
        resultado = AuditorArranquePiloto01(self.base_dir).ejecutar(importar_modulos=True)
        print_fn("\nAUDITORÍA DE ARRANQUE PILOTO-0.1")
        print_fn("=" * 70)
        print_fn(f"Estado: {resultado['estado']} | Errores: {resultado['errores']} | Avisos: {resultado['avisos']}")
        for item in resultado["comprobaciones"]:
            print_fn(f"- {item['codigo']}: {'OK' if item['ok'] else 'REVISAR'}")
        return resultado

    def certificar(self, print_fn: Callable[..., None] = print) -> dict:
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
        while True:
            print_fn("=" * 70)
            print_fn("HOST AI 6.0 — LÍNEA BASE PILOTO")
            print_fn("=" * 70)
            print_fn("1. Modo Piloto privado")
            print_fn("2. Modo Desarrollo y herramientas técnicas")
            print_fn("8. Auditoría de arranque")
            print_fn("9. Certificar PILOTO-0.1")
            print_fn("0. Salir")
            opcion = input_fn("Elige una opción: ").strip()
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
