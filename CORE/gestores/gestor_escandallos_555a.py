from __future__ import annotations

from pathlib import Path

from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.integrador_eventos_escandallos_555a import analizar_evento_con_escandallo


class GestorEscandallos555A:
    """Fachada estable para que IA, eventos y motores reutilicen el modelo canónico."""

    def __init__(
        self,
        ruta_escandallos: str | Path = "DATOS/db/escandallos_canonicos.json",
        ruta_stock: str | Path = "DATOS/db/stock_inicial.json",
        ruta_articulos: str | Path = "DATOS/db/articulos.json",
    ) -> None:
        self.repositorio = RepositorioEscandallos(ruta_escandallos)
        self.ruta_stock = str(ruta_stock)
        self.ruta_articulos = str(ruta_articulos)

    def listar(self):
        return self.repositorio.listar()

    def buscar(self, texto: str):
        return self.repositorio.buscar_por_nombre(texto)

    def buscar_por_ingrediente(self, texto: str):
        return self.repositorio.buscar_por_ingrediente(texto)

    def analizar_evento(self, evento: dict) -> dict:
        resultado = analizar_evento_con_escandallo(
            evento=evento,
            repositorio=self.repositorio,
            ruta_stock=self.ruta_stock,
            ruta_articulos=self.ruta_articulos,
        )
        return resultado.a_dict()
