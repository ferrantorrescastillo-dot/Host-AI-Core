from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import unicodedata
from difflib import SequenceMatcher


@dataclass
class ResultadoBusquedaArticulo:
    codigo: str
    nombre: str
    proveedor: Optional[str]
    familia: Optional[str]
    precio: Optional[float]
    puntuacion: float
    motivo: str


@dataclass
class InformeBusquedaArticulos:
    consulta: str
    proveedor_filtro: Optional[str]
    total_articulos: int
    total_resultados: int
    resultados: List[ResultadoBusquedaArticulo] = field(default_factory=list)

    @property
    def encontrado(self) -> bool:
        return self.total_resultados > 0

    @property
    def mejor_resultado(self) -> Optional[ResultadoBusquedaArticulo]:
        return self.resultados[0] if self.resultados else None


class BuscadorInteligenteArticulos415:
    def __init__(self, ruta_db: str = "DATOS/db/articulos.json") -> None:
        self.ruta_db = Path(ruta_db)

    def buscar(self, consulta: str, proveedor: Optional[str] = None, limite: int = 10, umbral_minimo: float = 0.50) -> InformeBusquedaArticulos:
        consulta_limpia = (consulta or "").strip()
        proveedor_limpio = (proveedor or "").strip() or None
        articulos = self._leer_articulos()

        if proveedor_limpio:
            proveedor_norm = self._normalizar(proveedor_limpio)
            articulos = [a for a in articulos if proveedor_norm in self._normalizar(a.get("proveedor", ""))]

        resultados: List[ResultadoBusquedaArticulo] = []
        for articulo in articulos:
            nombre = str(articulo.get("nombre", "") or "")
            codigo = str(articulo.get("codigo", "") or "")
            puntuacion, motivo = self._puntuar(consulta_limpia, nombre, codigo)

            if puntuacion >= umbral_minimo:
                resultados.append(ResultadoBusquedaArticulo(
                    codigo=codigo,
                    nombre=nombre,
                    proveedor=articulo.get("proveedor"),
                    familia=articulo.get("familia"),
                    precio=articulo.get("precio"),
                    puntuacion=round(puntuacion, 4),
                    motivo=motivo,
                ))

        resultados.sort(key=lambda item: item.puntuacion, reverse=True)
        resultados = resultados[:limite]

        return InformeBusquedaArticulos(
            consulta=consulta_limpia,
            proveedor_filtro=proveedor_limpio,
            total_articulos=len(articulos),
            total_resultados=len(resultados),
            resultados=resultados,
        )

    def listar_por_proveedor(self, proveedor: str, limite: int = 50) -> InformeBusquedaArticulos:
        proveedor_limpio = (proveedor or "").strip()
        proveedor_norm = self._normalizar(proveedor_limpio)
        articulos = [a for a in self._leer_articulos() if proveedor_norm in self._normalizar(a.get("proveedor", ""))]

        resultados = [
            ResultadoBusquedaArticulo(
                codigo=str(a.get("codigo", "") or ""),
                nombre=str(a.get("nombre", "") or ""),
                proveedor=a.get("proveedor"),
                familia=a.get("familia"),
                precio=a.get("precio"),
                puntuacion=1.0,
                motivo="Listado por proveedor.",
            )
            for a in articulos[:limite]
        ]

        return InformeBusquedaArticulos("", proveedor_limpio, len(articulos), len(resultados), resultados)

    def diagnosticar(self, termino: str, limite: int = 30) -> InformeBusquedaArticulos:
        termino_limpio = (termino or "").strip()
        termino_norm = self._normalizar(termino_limpio)
        articulos = self._leer_articulos()
        resultados: List[ResultadoBusquedaArticulo] = []

        for articulo in articulos:
            nombre = str(articulo.get("nombre", "") or "")
            proveedor = articulo.get("proveedor")
            familia = articulo.get("familia")
            codigo = str(articulo.get("codigo", "") or "")
            texto = " ".join([self._normalizar(nombre), self._normalizar(proveedor or ""), self._normalizar(familia or ""), self._normalizar(codigo)])

            if termino_norm in texto:
                resultados.append(ResultadoBusquedaArticulo(
                    codigo=codigo,
                    nombre=nombre,
                    proveedor=proveedor,
                    familia=familia,
                    precio=articulo.get("precio"),
                    puntuacion=1.0,
                    motivo="Diagnóstico: término encontrado en nombre/proveedor/familia/código.",
                ))

        resultados = resultados[:limite]
        return InformeBusquedaArticulos(termino_limpio, None, len(articulos), len(resultados), resultados)

    def _puntuar(self, consulta: str, nombre: str, codigo: str) -> tuple[float, str]:
        if not consulta:
            return 0.0, "Consulta vacía."

        consulta_norm = self._normalizar(consulta)
        nombre_norm = self._normalizar(nombre)
        codigo_norm = self._normalizar(codigo)

        if consulta_norm == codigo_norm:
            return 1.0, "Coincidencia exacta por código."
        if consulta_norm == nombre_norm:
            return 1.0, "Coincidencia exacta por nombre."
        if consulta_norm in nombre_norm:
            return 0.95, "La consulta aparece dentro del nombre."

        palabras_consulta = [p for p in consulta_norm.split() if len(p) >= 2]
        palabras_nombre = set(nombre_norm.split())

        if not palabras_consulta:
            return 0.0, "Consulta demasiado corta."

        encontradas = sum(1 for p in palabras_consulta if p in palabras_nombre or p in nombre_norm)
        if encontradas == 0:
            return 0.0, "Ninguna palabra de la consulta aparece en el nombre."

        cobertura = encontradas / len(palabras_consulta)
        parecido = SequenceMatcher(None, consulta_norm, nombre_norm).ratio()

        if cobertura == 1.0:
            return max(0.88, parecido), "Todas las palabras aparecen en el nombre."
        if cobertura >= 0.5:
            return max(0.62, parecido * 0.85), "Coincidencia parcial por palabras."
        return max(0.45, parecido * 0.70), "Coincidencia débil por una palabra."

    def _leer_articulos(self) -> List[Dict[str, Any]]:
        if not self.ruta_db.exists():
            return []
        try:
            contenido = json.loads(self.ruta_db.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return contenido if isinstance(contenido, list) else []

    def _normalizar(self, texto: Any) -> str:
        texto = "" if texto is None else str(texto)
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
        return texto.strip().lower()


__all__ = ["BuscadorInteligenteArticulos415", "ResultadoBusquedaArticulo", "InformeBusquedaArticulos"]
