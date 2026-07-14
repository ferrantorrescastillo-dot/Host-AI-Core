from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


@dataclass
class ResultadoAltaArticulo:
    codigo: str
    nombre: str
    accion: str
    ruta_db: str
    mensaje: str


class GestorArticulos416:
    """
    Alta manual/controlada de artículos reales.

    Trabaja sobre:
    DATOS/db/articulos.json

    Regla:
    - Si no se pasa código, genera el siguiente ART000001...
    - Si el código existe, no duplica.
    - Si el nombre ya existe parecido exacto, avisa.
    """

    def __init__(self, ruta_db: str = "DATOS/db/articulos.json") -> None:
        self.ruta_db = Path(ruta_db)

    def alta_articulo(
        self,
        nombre: str,
        proveedor: Optional[str] = None,
        familia: Optional[str] = None,
        precio: Optional[Any] = None,
        observaciones: Optional[str] = None,
        codigo: Optional[str] = None,
    ) -> ResultadoAltaArticulo:
        nombre_limpio = self._texto(nombre)
        if not nombre_limpio:
            raise ValueError("El nombre del artículo es obligatorio.")

        articulos = self._leer_articulos()
        codigos = {str(a.get("codigo", "")) for a in articulos if a.get("codigo")}

        if codigo:
            codigo_final = self._texto(codigo)
            if codigo_final in codigos:
                return ResultadoAltaArticulo(
                    codigo=codigo_final,
                    nombre=nombre_limpio,
                    accion="no_creado",
                    ruta_db=str(self.ruta_db),
                    mensaje=f"Ya existe un artículo con el código {codigo_final}.",
                )
        else:
            codigo_final = self._generar_siguiente_codigo(codigos)

        nombre_norm = self._normalizar(nombre_limpio)
        for articulo in articulos:
            if self._normalizar(articulo.get("nombre", "")) == nombre_norm:
                return ResultadoAltaArticulo(
                    codigo=str(articulo.get("codigo", "")),
                    nombre=str(articulo.get("nombre", "")),
                    accion="no_creado",
                    ruta_db=str(self.ruta_db),
                    mensaje="Ya existe un artículo con ese nombre exacto.",
                )

        nuevo = {
            "codigo": codigo_final,
            "nombre": nombre_limpio,
            "observaciones": self._texto(observaciones),
            "proveedor": self._texto(proveedor),
            "familia": self._texto(familia),
            "precio": self._precio(precio),
            "activo": True,
            "origen": "alta_manual_416",
            "fecha_importacion": datetime.now().isoformat(timespec="seconds"),
        }

        articulos.append(nuevo)
        articulos.sort(key=lambda item: str(item.get("codigo", "")))
        self._guardar_articulos(articulos)

        return ResultadoAltaArticulo(
            codigo=codigo_final,
            nombre=nombre_limpio,
            accion="creado",
            ruta_db=str(self.ruta_db),
            mensaje="Artículo creado correctamente.",
        )

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

    def _generar_siguiente_codigo(self, codigos: set[str]) -> str:
        max_numero = 0
        for codigo in codigos:
            if codigo.startswith("ART"):
                parte = codigo[3:]
                if parte.isdigit():
                    max_numero = max(max_numero, int(parte))
        return f"ART{max_numero + 1:06d}"

    def _texto(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None
        texto = str(valor).strip()
        return texto if texto else None

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

    def _normalizar(self, valor: Any) -> str:
        return str(valor or "").strip().lower()


__all__ = ["GestorArticulos416", "ResultadoAltaArticulo"]
