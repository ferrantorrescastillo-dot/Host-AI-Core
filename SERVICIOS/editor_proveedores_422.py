from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import unicodedata


@dataclass
class ResultadoEdicionProveedor:
    encontrado: bool
    actualizado: bool
    codigo: Optional[str]
    nombre: Optional[str]
    mensaje: str
    campos_actualizados: Dict[str, Any]


class EditorProveedores422:
    """
    Edita y normaliza proveedores reales en DATOS/db/proveedores.json.

    Permite:
    - Cambiar nombre oficial.
    - Añadir observaciones.
    - Activar/desactivar proveedor.
    - Buscar por código o por nombre normalizado.
    """

    CAMPOS_EDITABLES = {"nombre", "estado", "observaciones"}

    def __init__(self, ruta_proveedores: str = "DATOS/db/proveedores.json") -> None:
        self.ruta_proveedores = Path(ruta_proveedores)

    def editar_por_codigo(self, codigo: str, **cambios: Any) -> ResultadoEdicionProveedor:
        codigo_limpio = self._texto(codigo)
        if not codigo_limpio:
            raise ValueError("El código del proveedor es obligatorio.")

        return self._editar(lambda proveedor: str(proveedor.get("codigo", "")).strip() == codigo_limpio, cambios)

    def editar_por_nombre(self, nombre_busqueda: str, **cambios: Any) -> ResultadoEdicionProveedor:
        """
        Busca el proveedor por nombre actual/normalizado y permite cambiar su campo 'nombre'.

        Se llama nombre_busqueda para evitar conflicto con cambios como nombre="Makro".
        """
        nombre_norm = self._normalizar(nombre_busqueda)
        if not nombre_norm:
            raise ValueError("El nombre del proveedor es obligatorio.")

        return self._editar(
            lambda proveedor: proveedor.get("nombre_normalizado") == nombre_norm
            or self._normalizar(proveedor.get("nombre")) == nombre_norm,
            cambios,
        )

    def _editar(self, criterio, cambios: Dict[str, Any]) -> ResultadoEdicionProveedor:
        proveedores = self._leer_proveedores()
        cambios_validos = self._normalizar_cambios(cambios)

        if not cambios_validos:
            return ResultadoEdicionProveedor(
                encontrado=False,
                actualizado=False,
                codigo=None,
                nombre=None,
                mensaje="No hay campos válidos para actualizar.",
                campos_actualizados={},
            )

        for proveedor in proveedores:
            if criterio(proveedor):
                for campo, valor in cambios_validos.items():
                    proveedor[campo] = valor
                    if campo == "nombre":
                        proveedor["nombre_normalizado"] = self._normalizar(valor)

                self._guardar_proveedores(proveedores)
                return ResultadoEdicionProveedor(
                    encontrado=True,
                    actualizado=True,
                    codigo=proveedor.get("codigo"),
                    nombre=proveedor.get("nombre"),
                    mensaje="Proveedor actualizado correctamente.",
                    campos_actualizados=cambios_validos,
                )

        return ResultadoEdicionProveedor(
            encontrado=False,
            actualizado=False,
            codigo=None,
            nombre=None,
            mensaje="No se ha encontrado ningún proveedor que coincida.",
            campos_actualizados={},
        )

    def _normalizar_cambios(self, cambios: Dict[str, Any]) -> Dict[str, Any]:
        alias = {
            "Nombre": "nombre",
            "Proveedor": "nombre",
            "proveedor": "nombre",
            "Estado": "estado",
            "Observaciones": "observaciones",
        }

        resultado: Dict[str, Any] = {}

        for campo, valor in cambios.items():
            campo_normalizado = alias.get(campo, campo)

            if campo_normalizado not in self.CAMPOS_EDITABLES:
                continue

            texto = self._texto(valor)
            if texto is None:
                continue

            resultado[campo_normalizado] = texto

        return resultado

    def _leer_proveedores(self) -> List[Dict[str, Any]]:
        self.ruta_proveedores.parent.mkdir(parents=True, exist_ok=True)

        if not self.ruta_proveedores.exists():
            return []

        try:
            contenido = json.loads(self.ruta_proveedores.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        return contenido if isinstance(contenido, list) else []

    def _guardar_proveedores(self, proveedores: List[Dict[str, Any]]) -> None:
        self.ruta_proveedores.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_proveedores.write_text(json.dumps(proveedores, ensure_ascii=False, indent=2), encoding="utf-8")

    def _texto(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None
        texto = str(valor).strip()
        return texto if texto else None

    def _normalizar(self, valor: Any) -> str:
        texto = "" if valor is None else str(valor)
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
        texto = texto.lower().strip()
        texto = texto.replace(".", "").replace(",", "").replace(";", "")
        texto = " ".join(texto.split())
        return texto


__all__ = ["EditorProveedores422", "ResultadoEdicionProveedor"]
