from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


@dataclass
class ResultadoEdicionArticulo:
    encontrado: bool
    actualizado: bool
    codigo: Optional[str]
    nombre: Optional[str]
    mensaje: str
    campos_actualizados: Dict[str, Any]


class EditorArticulos417:
    """
    Edita artículos reales en DATOS/db/articulos.json.

    Permite editar por:
    - código interno Host AI
    - nombre exacto
    """

    CAMPOS_EDITABLES = {"nombre", "proveedor", "familia", "precio", "observaciones", "activo"}

    def __init__(self, ruta_db: str = "DATOS/db/articulos.json") -> None:
        self.ruta_db = Path(ruta_db)

    def editar_por_codigo(self, codigo: str, **cambios: Any) -> ResultadoEdicionArticulo:
        codigo_limpio = self._texto(codigo)
        if not codigo_limpio:
            raise ValueError("El código es obligatorio.")

        return self._editar(lambda articulo: str(articulo.get("codigo", "")).strip() == codigo_limpio, cambios)

    def editar_por_nombre(self, nombre: str, **cambios: Any) -> ResultadoEdicionArticulo:
        nombre_limpio = self._normalizar(nombre)
        if not nombre_limpio:
            raise ValueError("El nombre es obligatorio.")

        return self._editar(lambda articulo: self._normalizar(articulo.get("nombre", "")) == nombre_limpio, cambios)

    def _editar(self, criterio, cambios: Dict[str, Any]) -> ResultadoEdicionArticulo:
        articulos = self._leer_articulos()
        cambios_validos = self._normalizar_cambios(cambios)

        if not cambios_validos:
            return ResultadoEdicionArticulo(
                encontrado=False,
                actualizado=False,
                codigo=None,
                nombre=None,
                mensaje="No hay campos válidos para actualizar.",
                campos_actualizados={},
            )

        for articulo in articulos:
            if criterio(articulo):
                for campo, valor in cambios_validos.items():
                    articulo[campo] = valor

                self._guardar_articulos(articulos)
                return ResultadoEdicionArticulo(
                    encontrado=True,
                    actualizado=True,
                    codigo=articulo.get("codigo"),
                    nombre=articulo.get("nombre"),
                    mensaje="Artículo actualizado correctamente.",
                    campos_actualizados=cambios_validos,
                )

        return ResultadoEdicionArticulo(
            encontrado=False,
            actualizado=False,
            codigo=None,
            nombre=None,
            mensaje="No se ha encontrado ningún artículo que coincida.",
            campos_actualizados={},
        )

    def _normalizar_cambios(self, cambios: Dict[str, Any]) -> Dict[str, Any]:
        resultado: Dict[str, Any] = {}

        alias = {
            "articulo": "nombre",
            "Artículo": "nombre",
            "Articulo": "nombre",
            "Proveedor": "proveedor",
            "Familia": "familia",
            "Precio": "precio",
            "Observaciones": "observaciones",
        }

        for campo, valor in cambios.items():
            campo_normalizado = alias.get(campo, campo)

            if campo_normalizado not in self.CAMPOS_EDITABLES:
                continue

            if campo_normalizado == "precio":
                resultado[campo_normalizado] = self._precio(valor)
            elif campo_normalizado == "activo":
                resultado[campo_normalizado] = self._bool(valor)
            else:
                resultado[campo_normalizado] = self._texto(valor)

        return resultado

    def _leer_articulos(self) -> List[Dict[str, Any]]:
        self.ruta_db.parent.mkdir(parents=True, exist_ok=True)

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

    def _precio(self, valor: Any) -> Optional[float]:
        if valor is None or str(valor).strip() == "":
            return None

        if isinstance(valor, (int, float)):
            return float(valor)

        limpio = str(valor).replace("€", "").replace(" ", "").strip()

        if "," in limpio and "." in limpio:
            limpio = limpio.replace(".", "").replace(",", ".")
        else:
            limpio = limpio.replace(",", ".")

        try:
            return float(limpio)
        except ValueError:
            return None

    def _bool(self, valor: Any) -> bool:
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() in {"1", "true", "si", "sí", "yes", "activo"}


__all__ = ["EditorArticulos417", "ResultadoEdicionArticulo"]
