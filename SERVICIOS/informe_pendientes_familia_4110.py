from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import Counter
import json


@dataclass
class ArticuloPendienteFamilia:
    codigo: str
    nombre: str
    proveedor: Optional[str]
    precio: Optional[float]
    origen: Optional[str]


@dataclass
class InformePendientesFamilia:
    total_articulos: int
    pendientes: int
    por_proveedor: Dict[str, int]
    por_origen: Dict[str, int]
    articulos: List[ArticuloPendienteFamilia] = field(default_factory=list)
    estado: str = "sin_datos"


class InformePendientesFamilia4110:
    """
    Genera un informe de artículos que siguen sin familia después del clasificador 4.1.9.

    No modifica datos.
    Solo lee DATOS/db/articulos.json y exporta un txt para revisión.
    """

    def __init__(self, ruta_db: str = "DATOS/db/articulos.json") -> None:
        self.ruta_db = Path(ruta_db)

    def generar(self) -> InformePendientesFamilia:
        articulos = self._leer_articulos()
        pendientes: List[ArticuloPendienteFamilia] = []

        for articulo in articulos:
            familia = self._texto(articulo.get("familia"))
            if familia:
                continue

            pendientes.append(
                ArticuloPendienteFamilia(
                    codigo=str(articulo.get("codigo", "") or ""),
                    nombre=str(articulo.get("nombre", "") or ""),
                    proveedor=self._texto(articulo.get("proveedor")),
                    precio=articulo.get("precio"),
                    origen=self._texto(articulo.get("origen")),
                )
            )

        por_proveedor = Counter(item.proveedor or "SIN_PROVEEDOR" for item in pendientes)
        por_origen = Counter(item.origen or "SIN_ORIGEN" for item in pendientes)

        estado = "apto" if not pendientes else "revisar"

        return InformePendientesFamilia(
            total_articulos=len(articulos),
            pendientes=len(pendientes),
            por_proveedor=dict(por_proveedor.most_common()),
            por_origen=dict(por_origen.most_common()),
            articulos=pendientes,
            estado=estado,
        )

    def exportar_txt(self, ruta_destino: str = "DATOS/db/pendientes_familia_4_1_10.txt") -> InformePendientesFamilia:
        informe = self.generar()
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.1.10 - ARTÍCULOS PENDIENTES DE FAMILIA",
            "=" * 68,
            f"Total artículos: {informe.total_articulos}",
            f"Pendientes sin familia: {informe.pendientes}",
            f"Estado: {informe.estado}",
            "",
            "PENDIENTES POR PROVEEDOR",
            "-" * 68,
        ]

        for proveedor, cantidad in informe.por_proveedor.items():
            lineas.append(f"{proveedor}: {cantidad}")

        lineas.extend(["", "PENDIENTES POR ORIGEN", "-" * 68])
        for origen, cantidad in informe.por_origen.items():
            lineas.append(f"{origen}: {cantidad}")

        lineas.extend(["", "LISTADO DE ARTÍCULOS SIN FAMILIA", "-" * 68])
        for item in informe.articulos:
            lineas.append(
                f"{item.codigo} | {item.nombre} | Proveedor: {item.proveedor or '-'} | Precio: {item.precio}"
            )

        lineas.extend([
            "",
            "RECOMENDACIÓN",
            "-" * 68,
            "Revisar este listado y decidir si conviene:",
            "- Añadir nuevas reglas automáticas.",
            "- Corregir manualmente familias concretas.",
            "- Crear una familia nueva.",
        ])

        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return informe

    def _leer_articulos(self) -> List[Dict[str, Any]]:
        if not self.ruta_db.exists():
            return []
        try:
            contenido = json.loads(self.ruta_db.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return contenido if isinstance(contenido, list) else []

    def _texto(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None
        texto = str(valor).strip()
        return texto if texto else None


__all__ = [
    "InformePendientesFamilia4110",
    "InformePendientesFamilia",
    "ArticuloPendienteFamilia",
]
