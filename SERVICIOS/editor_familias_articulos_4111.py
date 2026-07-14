from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


@dataclass
class ResultadoEdicionFamilia:
    encontrado: bool
    actualizado: bool
    codigo: Optional[str]
    nombre: Optional[str]
    familia_anterior: Optional[str]
    familia_nueva: Optional[str]
    mensaje: str


class EditorFamiliasArticulos4111:
    """
    Editor manual de familias para artículos reales.

    Fuente:
    DATOS/db/articulos.json

    Permite asignar familia por:
    - código
    - nombre exacto
    """

    def __init__(self, ruta_db: str = "DATOS/db/articulos.json") -> None:
        self.ruta_db = Path(ruta_db)

    def asignar_por_codigo(self, codigo: str, familia: str) -> ResultadoEdicionFamilia:
        codigo_limpio = self._texto(codigo)
        familia_limpia = self._texto(familia)

        if not codigo_limpio:
            raise ValueError("El código es obligatorio.")
        if not familia_limpia:
            raise ValueError("La familia es obligatoria.")

        return self._asignar(lambda a: str(a.get("codigo", "")).strip() == codigo_limpio, familia_limpia)

    def asignar_por_nombre(self, nombre_busqueda: str, familia: str) -> ResultadoEdicionFamilia:
        nombre_norm = self._normalizar(nombre_busqueda)
        familia_limpia = self._texto(familia)

        if not nombre_norm:
            raise ValueError("El nombre es obligatorio.")
        if not familia_limpia:
            raise ValueError("La familia es obligatoria.")

        return self._asignar(lambda a: self._normalizar(a.get("nombre", "")) == nombre_norm, familia_limpia)

    def _asignar(self, criterio, familia: str) -> ResultadoEdicionFamilia:
        articulos = self._leer_articulos()

        for articulo in articulos:
            if criterio(articulo):
                anterior = self._texto(articulo.get("familia"))
                articulo["familia"] = familia
                articulo["familia_asignada_manual"] = True

                self._guardar_articulos(articulos)

                return ResultadoEdicionFamilia(
                    encontrado=True,
                    actualizado=True,
                    codigo=articulo.get("codigo"),
                    nombre=articulo.get("nombre"),
                    familia_anterior=anterior,
                    familia_nueva=familia,
                    mensaje="Familia actualizada correctamente.",
                )

        return ResultadoEdicionFamilia(
            encontrado=False,
            actualizado=False,
            codigo=None,
            nombre=None,
            familia_anterior=None,
            familia_nueva=None,
            mensaje="No se ha encontrado ningún artículo que coincida.",
        )

    def _leer_articulos(self) -> List[Dict[str, Any]]:
        if not self.ruta_db.exists():
            return []
        try:
            contenido = json.loads(self.ruta_db.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return contenido if isinstance(contenido, list) else []

    def _guardar_articulos(self, articulos: List[Dict[str, Any]]) -> None:
        self.ruta_db.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_db.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

    def _texto(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None
        texto = str(valor).strip()
        return texto if texto else None

    def _normalizar(self, valor: Any) -> str:
        return str(valor or "").strip().lower()


__all__ = ["EditorFamiliasArticulos4111", "ResultadoEdicionFamilia"]
