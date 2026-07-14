from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
from collections import Counter


@dataclass
class InformeCatalogoArticulos:
    total_articulos: int
    activos: int
    inactivos: int
    sin_proveedor: int
    sin_familia: int
    sin_precio: int
    precio_cero: int
    precio_negativo: int
    origenes: Dict[str, int]
    proveedores_top: Dict[str, int]
    familias_top: Dict[str, int]
    estado: str
    recomendaciones: List[str] = field(default_factory=list)


class InformeCatalogoArticulos418:
    """
    Genera informe final del catálogo real de artículos.

    Fuente:
    DATOS/db/articulos.json
    """

    def __init__(self, ruta_db: str = "DATOS/db/articulos.json") -> None:
        self.ruta_db = Path(ruta_db)

    def generar(self) -> InformeCatalogoArticulos:
        articulos = self._leer_articulos()

        total = len(articulos)
        activos = sum(1 for a in articulos if a.get("activo", True) is True)
        inactivos = total - activos

        sin_proveedor = sum(1 for a in articulos if not self._texto(a.get("proveedor")))
        sin_familia = sum(1 for a in articulos if not self._texto(a.get("familia")))
        sin_precio = sum(1 for a in articulos if a.get("precio") is None)
        precio_cero = sum(1 for a in articulos if a.get("precio") == 0)
        precio_negativo = sum(1 for a in articulos if isinstance(a.get("precio"), (int, float)) and a.get("precio") < 0)

        origenes = Counter(str(a.get("origen") or "desconocido") for a in articulos)
        proveedores = Counter(str(a.get("proveedor") or "SIN_PROVEEDOR") for a in articulos)
        familias = Counter(str(a.get("familia") or "SIN_FAMILIA") for a in articulos)

        informe = InformeCatalogoArticulos(
            total_articulos=total,
            activos=activos,
            inactivos=inactivos,
            sin_proveedor=sin_proveedor,
            sin_familia=sin_familia,
            sin_precio=sin_precio,
            precio_cero=precio_cero,
            precio_negativo=precio_negativo,
            origenes=dict(origenes.most_common()),
            proveedores_top=dict(proveedores.most_common(10)),
            familias_top=dict(familias.most_common(10)),
            estado="sin_datos",
        )

        informe.recomendaciones = self._recomendaciones(informe)
        informe.estado = self._estado(informe)
        return informe

    def exportar_txt(self, ruta_destino: str = "DATOS/db/informe_catalogo_articulos_4_1_8.txt") -> InformeCatalogoArticulos:
        informe = self.generar()
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.1.8 - INFORME CATÁLOGO DE ARTÍCULOS",
            "=" * 58,
            f"Total artículos: {informe.total_articulos}",
            f"Activos: {informe.activos}",
            f"Inactivos: {informe.inactivos}",
            "",
            "CALIDAD DEL CATÁLOGO",
            "-" * 58,
            f"Sin proveedor: {informe.sin_proveedor}",
            f"Sin familia: {informe.sin_familia}",
            f"Sin precio: {informe.sin_precio}",
            f"Precio cero: {informe.precio_cero}",
            f"Precio negativo: {informe.precio_negativo}",
            "",
            "ORÍGENES",
            "-" * 58,
        ]

        for origen, cantidad in informe.origenes.items():
            lineas.append(f"{origen}: {cantidad}")

        lineas.extend(["", "TOP PROVEEDORES", "-" * 58])
        for proveedor, cantidad in informe.proveedores_top.items():
            lineas.append(f"{proveedor}: {cantidad}")

        lineas.extend(["", "TOP FAMILIAS", "-" * 58])
        for familia, cantidad in informe.familias_top.items():
            lineas.append(f"{familia}: {cantidad}")

        lineas.extend(["", "RECOMENDACIONES", "-" * 58])
        for recomendacion in informe.recomendaciones:
            lineas.append(f"- {recomendacion}")

        lineas.extend(["", f"ESTADO FINAL: {informe.estado}"])
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

    def _recomendaciones(self, informe: InformeCatalogoArticulos) -> List[str]:
        recomendaciones: List[str] = []

        if informe.total_articulos == 0:
            return ["Importar artículos antes de generar el informe final."]

        if informe.sin_proveedor:
            recomendaciones.append("Completar proveedores para mejorar compras, comparativas y pedidos.")
        if informe.sin_familia:
            recomendaciones.append("Completar familias para mejorar filtros, informes y escandallos.")
        if informe.sin_precio or informe.precio_cero:
            recomendaciones.append("Revisar artículos sin precio o con precio cero antes de escandallar.")
        if informe.precio_negativo:
            recomendaciones.append("Corregir precios negativos: no son válidos para producción.")
        if not recomendaciones:
            recomendaciones.append("Catálogo preparado para trabajar con artículos reales.")

        return recomendaciones

    def _estado(self, informe: InformeCatalogoArticulos) -> str:
        if informe.total_articulos == 0:
            return "sin_datos"
        if informe.precio_negativo:
            return "no_apto"
        if informe.sin_proveedor or informe.sin_familia or informe.sin_precio or informe.precio_cero:
            return "apto_con_observaciones"
        return "apto"


__all__ = ["InformeCatalogoArticulos418", "InformeCatalogoArticulos"]
