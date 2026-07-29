from __future__ import annotations

from APP.consola import AppConsolaHostAI


class ConsolaPiloto01:
    """Interfaz reducida para el piloto privado.

    Freeze-A1: es la interfaz operativa que cuelga de la ruta oficial
    de arranque (main -> LanzadorPiloto01 -> modo piloto).

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
                from APP.app_shell_host_ai import AppShellHostAI
                AppShellHostAI(self.app.core, app=self.app).ejecutar()
            elif opcion == "2":
                from APP.consola_jornada_piloto_12 import ConsolaJornadaPiloto12
                ConsolaJornadaPiloto12(self.app.core.base_dir).ejecutar()
            elif opcion == "3":
                from APP.consola_recepcion_piloto_1 import ConsolaRecepcionPiloto1
                ConsolaRecepcionPiloto1(self.app.core.base_dir, core=self.app.core).ejecutar()
            elif opcion == "4":
                self.app._menu_eventos()
            elif opcion == "5":
                from APP.consola_produccion_guiada_piloto_13 import ConsolaProduccionGuiadaPiloto13
                ConsolaProduccionGuiadaPiloto13(self.app.core, self.app._menu_produccion_real).ejecutar()
            elif opcion == "6":
                self.app._menu_compras()
            elif opcion == "7":
                self.app._menu_stock()
            elif opcion == "8":
                self.app._menu_costes()
            elif opcion == "9":
                self.app._hablar_host_ai()
            elif opcion == "10":
                from APP.consola_configuracion_restaurante import ConsolaConfiguracionRestaurante
                ConsolaConfiguracionRestaurante(self.app.core.base_dir).ejecutar()
            elif opcion == "11":
                self.app._menu_escandallos_recetas()
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
        print("1. Host AI App Shell (APP-01)")
        print("2. Mi jornada")
        print("3. Recepción inteligente de mercancía")
        print("4. Eventos")
        print("5. Producción")
        print("6. Compras")
        print("7. Stock")
        print("8. Costes y rentabilidad")
        print("9. Hablar con Host AI")
        print("10. Configuracion del Restaurante")
        print("11. Escandallos y recetas")
        print("0. Volver")


__all__ = ["ConsolaPiloto01"]
