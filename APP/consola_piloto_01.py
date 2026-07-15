from __future__ import annotations

from APP.consola import AppConsolaHostAI


class ConsolaPiloto01:
    """Interfaz reducida para el piloto privado.

    Reutiliza los menús operativos existentes y oculta diagnósticos, sprints y
    herramientas técnicas. No duplica lógica de negocio.
    """

    def __init__(self, core):
        self.app = AppConsolaHostAI(core)

    def ejecutar(self) -> None:
        self._cabecera()
        while True:
            self._menu()
            opcion = input("Elige una opción: ").strip()
            if opcion == "1":
                from APP.consola_jornada_piloto_12 import ConsolaJornadaPiloto12
                ConsolaJornadaPiloto12(self.app.core.base_dir).ejecutar()
            elif opcion == "2":
                from APP.consola_recepcion_piloto_1 import ConsolaRecepcionPiloto1
                ConsolaRecepcionPiloto1(self.app.core.base_dir, core=self.app.core).ejecutar()
            elif opcion == "3":
                self.app._menu_eventos()
            elif opcion == "4":
                from APP.consola_produccion_guiada_piloto_13 import ConsolaProduccionGuiadaPiloto13
                ConsolaProduccionGuiadaPiloto13(self.app.core, self.app._menu_produccion_real).ejecutar()
            elif opcion == "5":
                self.app._menu_compras()
            elif opcion == "6":
                self.app._menu_stock()
            elif opcion == "7":
                self.app._menu_costes()
            elif opcion == "8":
                self.app._hablar_host_ai()
            elif opcion == "0":
                print("Saliendo del modo piloto.")
                return
            else:
                print("Opción no válida.")

    @staticmethod
    def _cabecera() -> None:
        print("=" * 70)
        print("HOST AI — MODO PILOTO PRIVADO")
        print("Operativa diaria del restaurante")
        print("=" * 70)

    @staticmethod
    def _menu() -> None:
        print("\nMODO PILOTO")
        print("1. Mi jornada")
        print("2. Recepción inteligente de mercancía")
        print("3. Eventos")
        print("4. Producción")
        print("5. Compras")
        print("6. Stock")
        print("7. Costes y rentabilidad")
        print("8. Hablar con Host AI")
        print("0. Volver")


__all__ = ["ConsolaPiloto01"]
