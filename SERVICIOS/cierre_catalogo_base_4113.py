from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
import json


@dataclass
class InformeCierreCatalogoBase:
    total_articulos: int
    total_proveedores: int
    sin_proveedor: int
    sin_familia: int
    sin_precio: int
    precio_cero: int
    precio_negativo: int
    proveedores_con_variantes: int
    estado: str
    bloque_siguiente: str
    recomendaciones: List[str] = field(default_factory=list)


class CierreCatalogoBase4113:
    """
    Cierre del catálogo base real.

    Comprueba si el sistema ya tiene una base suficiente de:
    - artículos
    - proveedores
    - familias
    - precios

    antes de pasar a Host AI 4.3 Stock real.
    """

    def __init__(
        self,
        ruta_articulos: str = "DATOS/db/articulos.json",
        ruta_proveedores: str = "DATOS/db/proveedores.json",
    ) -> None:
        self.ruta_articulos = Path(ruta_articulos)
        self.ruta_proveedores = Path(ruta_proveedores)

    def cerrar(self) -> InformeCierreCatalogoBase:
        articulos = self._leer_json_lista(self.ruta_articulos)
        proveedores = self._leer_json_lista(self.ruta_proveedores)

        total_articulos = len(articulos)
        total_proveedores = len(proveedores)

        sin_proveedor = sum(1 for a in articulos if not self._texto(a.get("proveedor")))
        sin_familia = sum(1 for a in articulos if not self._texto(a.get("familia")))
        sin_precio = sum(1 for a in articulos if a.get("precio") is None)
        precio_cero = sum(1 for a in articulos if a.get("precio") == 0)
        precio_negativo = sum(1 for a in articulos if isinstance(a.get("precio"), (int, float)) and a.get("precio") < 0)
        proveedores_con_variantes = sum(1 for p in proveedores if len(p.get("variantes_detectadas", []) or []) > 1)

        estado = self._calcular_estado(
            total_articulos=total_articulos,
            total_proveedores=total_proveedores,
            sin_proveedor=sin_proveedor,
            sin_familia=sin_familia,
            sin_precio=sin_precio,
            precio_cero=precio_cero,
            precio_negativo=precio_negativo,
            proveedores_con_variantes=proveedores_con_variantes,
        )

        recomendaciones = self._recomendaciones(
            total_articulos,
            total_proveedores,
            sin_proveedor,
            sin_familia,
            sin_precio,
            precio_cero,
            precio_negativo,
            proveedores_con_variantes,
        )

        bloque_siguiente = "Host AI 4.3 - Stock inicial real" if estado in {"apto", "apto_con_observaciones"} else "Corregir catálogo antes de stock"

        return InformeCierreCatalogoBase(
            total_articulos=total_articulos,
            total_proveedores=total_proveedores,
            sin_proveedor=sin_proveedor,
            sin_familia=sin_familia,
            sin_precio=sin_precio,
            precio_cero=precio_cero,
            precio_negativo=precio_negativo,
            proveedores_con_variantes=proveedores_con_variantes,
            estado=estado,
            bloque_siguiente=bloque_siguiente,
            recomendaciones=recomendaciones,
        )

    def exportar_txt(self, ruta_destino: str = "DATOS/db/cierre_catalogo_base_4_1_13.txt") -> InformeCierreCatalogoBase:
        informe = self.cerrar()
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.1.13 - CIERRE CATÁLOGO BASE",
            "=" * 64,
            f"Artículos: {informe.total_articulos}",
            f"Proveedores: {informe.total_proveedores}",
            "",
            "CALIDAD",
            "-" * 64,
            f"Artículos sin proveedor: {informe.sin_proveedor}",
            f"Artículos sin familia: {informe.sin_familia}",
            f"Artículos sin precio: {informe.sin_precio}",
            f"Artículos con precio cero: {informe.precio_cero}",
            f"Artículos con precio negativo: {informe.precio_negativo}",
            f"Proveedores con variantes: {informe.proveedores_con_variantes}",
            "",
            "RECOMENDACIONES",
            "-" * 64,
        ]

        for recomendacion in informe.recomendaciones:
            lineas.append(f"- {recomendacion}")

        lineas.extend([
            "",
            f"ESTADO FINAL: {informe.estado}",
            f"BLOQUE SIGUIENTE: {informe.bloque_siguiente}",
        ])

        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return informe

    def _leer_json_lista(self, ruta: Path) -> List[Dict[str, Any]]:
        if not ruta.exists():
            return []
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return contenido if isinstance(contenido, list) else []

    def _texto(self, valor: Any):
        if valor is None:
            return None
        texto = str(valor).strip()
        return texto if texto else None

    def _calcular_estado(
        self,
        total_articulos: int,
        total_proveedores: int,
        sin_proveedor: int,
        sin_familia: int,
        sin_precio: int,
        precio_cero: int,
        precio_negativo: int,
        proveedores_con_variantes: int,
    ) -> str:
        if total_articulos == 0 or total_proveedores == 0:
            return "no_apto"
        if precio_negativo:
            return "no_apto"
        if sin_proveedor or sin_familia or sin_precio or precio_cero or proveedores_con_variantes:
            return "apto_con_observaciones"
        return "apto"

    def _recomendaciones(
        self,
        total_articulos: int,
        total_proveedores: int,
        sin_proveedor: int,
        sin_familia: int,
        sin_precio: int,
        precio_cero: int,
        precio_negativo: int,
        proveedores_con_variantes: int,
    ) -> List[str]:
        recomendaciones: List[str] = []

        if total_articulos == 0:
            recomendaciones.append("Importar artículos reales antes de continuar.")
        if total_proveedores == 0:
            recomendaciones.append("Extraer proveedores reales antes de continuar.")
        if sin_proveedor:
            recomendaciones.append("Completar artículos sin proveedor cuando sea posible.")
        if sin_familia:
            recomendaciones.append("Completar familias pendientes para mejorar informes y escandallos.")
        if sin_precio or precio_cero:
            recomendaciones.append("Revisar artículos sin precio antes de calcular escandallos definitivos.")
        if precio_negativo:
            recomendaciones.append("Corregir precios negativos antes de continuar.")
        if proveedores_con_variantes:
            recomendaciones.append("Normalizar variantes de proveedores para comparativas limpias.")
        if not recomendaciones:
            recomendaciones.append("Catálogo base preparado para iniciar stock real.")

        return recomendaciones


__all__ = ["CierreCatalogoBase4113", "InformeCierreCatalogoBase"]
