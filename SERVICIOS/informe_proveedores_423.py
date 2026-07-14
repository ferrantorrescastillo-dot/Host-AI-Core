from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
import json


@dataclass
class InformeProveedores:
    total_proveedores: int
    proveedores_activos: int
    proveedores_inactivos: int
    proveedores_con_variantes: int
    articulos_sin_proveedor: int
    top_proveedores: Dict[str, int]
    estado: str
    recomendaciones: List[str] = field(default_factory=list)


class InformeProveedores423:
    """
    Genera informe final de proveedores reales.

    Fuentes:
    - DATOS/db/proveedores.json
    - DATOS/db/articulos.json
    """

    def __init__(
        self,
        ruta_proveedores: str = "DATOS/db/proveedores.json",
        ruta_articulos: str = "DATOS/db/articulos.json",
    ) -> None:
        self.ruta_proveedores = Path(ruta_proveedores)
        self.ruta_articulos = Path(ruta_articulos)

    def generar(self) -> InformeProveedores:
        proveedores = self._leer_json_lista(self.ruta_proveedores)
        articulos = self._leer_json_lista(self.ruta_articulos)

        total = len(proveedores)
        activos = sum(1 for p in proveedores if str(p.get("estado", "activo")).lower() == "activo")
        inactivos = total - activos
        con_variantes = sum(1 for p in proveedores if len(p.get("variantes_detectadas", []) or []) > 1)
        articulos_sin_proveedor = sum(1 for a in articulos if not self._texto(a.get("proveedor")))

        top = {}
        for proveedor in sorted(proveedores, key=lambda p: p.get("articulos_asociados", 0), reverse=True)[:10]:
            top[str(proveedor.get("nombre", "SIN_NOMBRE"))] = int(proveedor.get("articulos_asociados", 0) or 0)

        estado = self._estado(total, con_variantes, articulos_sin_proveedor)
        recomendaciones = self._recomendaciones(total, con_variantes, articulos_sin_proveedor)

        return InformeProveedores(
            total_proveedores=total,
            proveedores_activos=activos,
            proveedores_inactivos=inactivos,
            proveedores_con_variantes=con_variantes,
            articulos_sin_proveedor=articulos_sin_proveedor,
            top_proveedores=top,
            estado=estado,
            recomendaciones=recomendaciones,
        )

    def exportar_txt(self, ruta_destino: str = "DATOS/db/informe_proveedores_4_2_3.txt") -> InformeProveedores:
        informe = self.generar()
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.2.3 - INFORME PROVEEDORES",
            "=" * 54,
            f"Total proveedores: {informe.total_proveedores}",
            f"Proveedores activos: {informe.proveedores_activos}",
            f"Proveedores inactivos: {informe.proveedores_inactivos}",
            f"Proveedores con variantes: {informe.proveedores_con_variantes}",
            f"Artículos sin proveedor: {informe.articulos_sin_proveedor}",
            "",
            "TOP PROVEEDORES POR ARTÍCULOS",
            "-" * 54,
        ]

        for proveedor, cantidad in informe.top_proveedores.items():
            lineas.append(f"{proveedor}: {cantidad}")

        lineas.extend(["", "RECOMENDACIONES", "-" * 54])
        for recomendacion in informe.recomendaciones:
            lineas.append(f"- {recomendacion}")

        lineas.extend(["", f"ESTADO FINAL: {informe.estado}"])
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

    def _estado(self, total: int, variantes: int, sin_proveedor: int) -> str:
        if total == 0:
            return "sin_datos"
        if variantes or sin_proveedor:
            return "apto_con_observaciones"
        return "apto"

    def _recomendaciones(self, total: int, variantes: int, sin_proveedor: int) -> List[str]:
        if total == 0:
            return ["Extraer proveedores antes de generar informe final."]
        recomendaciones = []
        if variantes:
            recomendaciones.append("Revisar proveedores con variantes para dejar un nombre oficial.")
        if sin_proveedor:
            recomendaciones.append("Completar proveedor en artículos sin proveedor.")
        if not recomendaciones:
            recomendaciones.append("Base de proveedores lista para compras y pedidos.")
        return recomendaciones


__all__ = ["InformeProveedores423", "InformeProveedores"]
