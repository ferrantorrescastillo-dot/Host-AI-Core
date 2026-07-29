from __future__ import annotations

from pathlib import Path
from typing import Optional

from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallosUI601
from SERVICIOS.biblioteca_menus_601 import BibliotecaMenusUI601
from SERVICIOS.biblioteca_recetas_601 import BibliotecaFichasTecnicasUI601, BibliotecaRecetasUI601
from SERVICIOS.catalogo_maestro_productos_601 import CatalogoMaestroProductos601, CatalogoMaestroProductosUI601
from SERVICIOS.centro_importacion_601 import CentroImportacionUI601


class ModuloEscandallosRecetas601:
    """
    Módulo independiente para la base gastronómica de Host AI.

    Estructura inicial preparada para crecer sin acoplarse a Eventos,
    Producción, Compras ni Stock.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self._biblioteca_fichas_tecnicas = BibliotecaFichasTecnicasUI601(self.base_dir)
        self._biblioteca_recetas = BibliotecaRecetasUI601(self.base_dir)
        self._biblioteca_escandallos = BibliotecaEscandallosUI601(self.base_dir)
        self._biblioteca_menus = BibliotecaMenusUI601(self.base_dir)
        self._centro_importacion = CentroImportacionUI601(self.base_dir)
        self._catalogo_maestro = CatalogoMaestroProductosUI601(
            CatalogoMaestroProductos601(self.base_dir),
            base_dir=self.base_dir,
        )

    def ejecutar(self) -> None:
        while True:
            self._imprimir_menu()
            opcion = input("Elige una opción: ").strip()

            if opcion == "1":
                self.fichas_tecnicas()
            elif opcion == "2":
                self.biblioteca_recetas()
            elif opcion == "3":
                self.biblioteca_escandallos()
            elif opcion == "4":
                self.biblioteca_menus()
            elif opcion == "5":
                self.importar()
            elif opcion == "6":
                self.incidencias()
            elif opcion == "7":
                self.estadisticas()
            elif opcion == "8":
                self.catalogo_maestro_productos()
            elif opcion == "0":
                return
            else:
                print("Opción no válida.")

    @staticmethod
    def _imprimir_menu() -> None:
        print("\n" + "=" * 40)
        print("FICHAS TÉCNICAS")
        print("=" * 40)
        print("1. Fichas Técnicas")
        print("2. Biblioteca de recetas")
        print("3. Biblioteca de escandallos")
        print("4. Biblioteca de menús")
        print("5. Importar")
        print("6. Incidencias")
        print("7. Estadísticas")
        print("8. Catálogo maestro de productos")
        print("0. Volver")
        print("=" * 40)

    def fichas_tecnicas(self) -> None:
        self._biblioteca_fichas_tecnicas.ejecutar()

    def biblioteca_recetas(self) -> None:
        self._biblioteca_recetas.ejecutar()

    def biblioteca_escandallos(self) -> None:
        self._biblioteca_escandallos.ejecutar()

    def biblioteca_menus(self) -> None:
        self._biblioteca_menus.ejecutar()

    def importar(self) -> None:
        self._centro_importacion.ejecutar()

    def incidencias(self) -> None:
        self._mostrar_pendiente("Incidencias")

    def estadisticas(self) -> None:
        self._mostrar_pendiente("Estadísticas")

    def catalogo_maestro_productos(self) -> None:
        self._catalogo_maestro.ejecutar()

    @staticmethod
    def _mostrar_pendiente(seccion: str) -> None:
        print(f"\n{seccion}")
        print("Funcionalidad en desarrollo")
        input("Pulsa Enter para volver...")


__all__ = ["ModuloEscandallosRecetas601"]
