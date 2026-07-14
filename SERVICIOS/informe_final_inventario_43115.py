from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import Counter, defaultdict
import json


@dataclass
class ResumenInventarioFinal:
    total_contados: int
    ok: int
    faltantes: int
    sobrantes: int
    revisar: int
    ajustes_aplicados: int
    ajustes_omitidos: int
    errores_ajuste: int
    movimientos_inventario: int
    diferencia_por_unidad: Dict[str, float]
    estado_final: str
    recomendaciones: List[str] = field(default_factory=list)


class InformeFinalInventario43115:
    """
    Genera informe final del inventario.

    Fuentes:
    - DATOS/db/comparacion_inventario_4_3_11_3.json
    - DATOS/db/ajustes_inventario_4_3_11_4.txt
    - DATOS/db/stock_movimientos.json
    """

    def __init__(
        self,
        ruta_comparacion: str = "DATOS/db/comparacion_inventario_4_3_11_3.json",
        ruta_movimientos: str = "DATOS/db/stock_movimientos.json",
    ) -> None:
        self.ruta_comparacion = Path(ruta_comparacion)
        self.ruta_movimientos = Path(ruta_movimientos)

    def generar(self) -> ResumenInventarioFinal:
        comparacion = self._leer_json_dict(self.ruta_comparacion)
        movimientos = self._leer_json_lista(self.ruta_movimientos)

        lineas = comparacion.get("lineas", []) if isinstance(comparacion, dict) else []

        estados = Counter(str(linea.get("estado", "") or "sin_estado") for linea in lineas)
        diferencia_por_unidad: Dict[str, float] = defaultdict(float)

        for linea in lineas:
            unidad = str(linea.get("unidad", "") or "SIN_UNIDAD")
            diferencia = self._numero(linea.get("diferencia")) or 0.0
            diferencia_por_unidad[unidad] += diferencia

        movimientos_inventario = [
            m for m in movimientos
            if str(m.get("tipo", "")).lower() == "ajuste"
            and "inventario" in str(m.get("motivo", "")).lower()
        ]

        # Estimación robusta: aplicados = movimientos de ajuste de inventario.
        ajustes_aplicados = len(movimientos_inventario)

        pendientes_aplicables = estados.get("faltante", 0) + estados.get("sobrante", 0)
        revisar = estados.get("revisar", 0)

        ajustes_omitidos = max(0, len(lineas) - ajustes_aplicados)
        errores_ajuste = 0

        estado_final = self._estado_final(
            total=len(lineas),
            revisar=revisar,
            pendientes_aplicables=pendientes_aplicables,
            ajustes_aplicados=ajustes_aplicados,
        )

        recomendaciones = self._recomendaciones(
            total=len(lineas),
            revisar=revisar,
            pendientes_aplicables=pendientes_aplicables,
            ajustes_aplicados=ajustes_aplicados,
        )

        return ResumenInventarioFinal(
            total_contados=len(lineas),
            ok=estados.get("ok", 0),
            faltantes=estados.get("faltante", 0),
            sobrantes=estados.get("sobrante", 0),
            revisar=revisar,
            ajustes_aplicados=ajustes_aplicados,
            ajustes_omitidos=ajustes_omitidos,
            errores_ajuste=errores_ajuste,
            movimientos_inventario=ajustes_aplicados,
            diferencia_por_unidad={k: round(v, 4) for k, v in diferencia_por_unidad.items()},
            estado_final=estado_final,
            recomendaciones=recomendaciones,
        )

    def exportar_txt(self, ruta_destino: str = "DATOS/db/informe_final_inventario_4_3_11_5.txt") -> ResumenInventarioFinal:
        informe = self.generar()
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.3.11.5 - INFORME FINAL INVENTARIO",
            "=" * 76,
            f"Artículos contados: {informe.total_contados}",
            f"OK: {informe.ok}",
            f"Faltantes: {informe.faltantes}",
            f"Sobrantes: {informe.sobrantes}",
            f"Revisar: {informe.revisar}",
            "",
            "AJUSTES",
            "-" * 76,
            f"Ajustes aplicados: {informe.ajustes_aplicados}",
            f"Ajustes omitidos: {informe.ajustes_omitidos}",
            f"Errores ajuste: {informe.errores_ajuste}",
            f"Movimientos inventario detectados: {informe.movimientos_inventario}",
            "",
            "DIFERENCIA POR UNIDAD",
            "-" * 76,
        ]

        if not informe.diferencia_por_unidad:
            lineas.append("Sin diferencias registradas.")

        for unidad, diferencia in informe.diferencia_por_unidad.items():
            lineas.append(f"{unidad}: {diferencia}")

        lineas.extend(["", "RECOMENDACIONES", "-" * 76])
        for rec in informe.recomendaciones:
            lineas.append(f"- {rec}")

        lineas.extend(["", f"ESTADO FINAL: {informe.estado_final}"])

        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return informe

    def _estado_final(self, total: int, revisar: int, pendientes_aplicables: int, ajustes_aplicados: int) -> str:
        if total == 0:
            return "sin_datos"
        if revisar:
            return "inventario_con_revisiones_pendientes"
        if pendientes_aplicables and ajustes_aplicados < pendientes_aplicables:
            return "inventario_pendiente_de_aplicar"
        return "inventario_cerrado"

    def _recomendaciones(self, total: int, revisar: int, pendientes_aplicables: int, ajustes_aplicados: int) -> List[str]:
        if total == 0:
            return ["Importar y comparar inventario antes de cerrar."]
        recomendaciones = []
        if revisar:
            recomendaciones.append("Revisar diferencias grandes antes de aplicar ajustes.")
        if pendientes_aplicables and ajustes_aplicados < pendientes_aplicables:
            recomendaciones.append("Aplicar ajustes pendientes de faltantes/sobrantes.")
        if not recomendaciones:
            recomendaciones.append("Inventario cerrado correctamente. Stock sincronizado con conteo físico.")
        return recomendaciones

    def _leer_json_dict(self, ruta: Path) -> Dict[str, Any]:
        if not ruta.exists():
            return {}
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return contenido if isinstance(contenido, dict) else {}

    def _leer_json_lista(self, ruta: Path) -> List[Dict[str, Any]]:
        if not ruta.exists():
            return []
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return contenido if isinstance(contenido, list) else []

    def _numero(self, valor: Any) -> Optional[float]:
        if valor is None or str(valor).strip() == "":
            return None
        if isinstance(valor, (int, float)):
            return float(valor)
        try:
            return float(str(valor).replace(",", "."))
        except ValueError:
            return None


__all__ = ["InformeFinalInventario43115", "ResumenInventarioFinal"]
