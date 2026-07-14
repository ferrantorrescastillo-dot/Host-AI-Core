from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


@dataclass
class AlertaStockBajo:
    codigo: str
    articulo: str
    proveedor: Optional[str]
    familia: Optional[str]
    unidad: str
    stock_actual: float
    stock_minimo: float
    diferencia: float
    ubicacion: Optional[str]
    prioridad: str
    mensaje: str


@dataclass
class InformeAlertasStockBajo:
    total_registros_stock: int
    total_alertas: int
    alertas_criticas: int
    alertas_altas: int
    alertas_medias: int
    alertas: List[AlertaStockBajo] = field(default_factory=list)
    estado: str = "sin_datos"


class AlertasStockBajo434:
    """
    Genera alertas de stock bajo desde DATOS/db/stock_inicial.json.
    """

    def __init__(self, ruta_stock: str = "DATOS/db/stock_inicial.json") -> None:
        self.ruta_stock = Path(ruta_stock)

    def generar(self) -> InformeAlertasStockBajo:
        stock = self._leer_json_lista(self.ruta_stock)
        alertas: List[AlertaStockBajo] = []

        for item in stock:
            stock_actual = self._numero(item.get("stock_actual")) or 0.0
            stock_minimo = self._numero(item.get("stock_minimo")) or 0.0

            if stock_actual >= stock_minimo:
                continue

            unidad = self._texto(item.get("unidad")) or ""
            diferencia = round(stock_minimo - stock_actual, 4)
            prioridad = self._prioridad(stock_actual, stock_minimo)

            alertas.append(
                AlertaStockBajo(
                    codigo=str(item.get("codigo", "") or ""),
                    articulo=str(item.get("articulo", "") or ""),
                    proveedor=self._texto(item.get("proveedor")),
                    familia=self._texto(item.get("familia")),
                    unidad=unidad,
                    stock_actual=stock_actual,
                    stock_minimo=stock_minimo,
                    diferencia=diferencia,
                    ubicacion=self._texto(item.get("ubicacion")),
                    prioridad=prioridad,
                    mensaje=f"Faltan {diferencia} {unidad} para llegar al mínimo.",
                )
            )

        alertas.sort(key=lambda a: {"critica": 0, "alta": 1, "media": 2}.get(a.prioridad, 9))

        criticas = sum(1 for a in alertas if a.prioridad == "critica")
        altas = sum(1 for a in alertas if a.prioridad == "alta")
        medias = sum(1 for a in alertas if a.prioridad == "media")

        estado = "ok" if not alertas and stock else "revisar" if alertas else "sin_datos"

        return InformeAlertasStockBajo(
            total_registros_stock=len(stock),
            total_alertas=len(alertas),
            alertas_criticas=criticas,
            alertas_altas=altas,
            alertas_medias=medias,
            alertas=alertas,
            estado=estado,
        )

    def exportar_txt(self, ruta_destino: str = "DATOS/db/alertas_stock_bajo_4_3_4.txt") -> InformeAlertasStockBajo:
        informe = self.generar()
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.3.4 - ALERTAS DE STOCK BAJO",
            "=" * 64,
            f"Registros stock: {informe.total_registros_stock}",
            f"Total alertas: {informe.total_alertas}",
            f"Críticas: {informe.alertas_criticas}",
            f"Altas: {informe.alertas_altas}",
            f"Medias: {informe.alertas_medias}",
            f"Estado: {informe.estado}",
            "",
            "ALERTAS",
            "-" * 64,
        ]

        if not informe.alertas:
            lineas.append("No hay alertas de stock bajo.")

        for alerta in informe.alertas:
            lineas.append(
                f"[{alerta.prioridad.upper()}] {alerta.codigo} | {alerta.articulo} | "
                f"Stock: {alerta.stock_actual} {alerta.unidad} | Mínimo: {alerta.stock_minimo} {alerta.unidad} | "
                f"Faltan: {alerta.diferencia} {alerta.unidad} | Ubicación: {alerta.ubicacion or '-'} | "
                f"Proveedor: {alerta.proveedor or '-'}"
            )

        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return informe

    def _prioridad(self, stock_actual: float, stock_minimo: float) -> str:
        if stock_minimo <= 0:
            return "media"

        ratio = stock_actual / stock_minimo

        if stock_actual <= 0:
            return "critica"
        if ratio <= 0.5:
            return "alta"
        return "media"

    def _leer_json_lista(self, ruta: Path) -> List[Dict[str, Any]]:
        if not ruta.exists():
            return []
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return contenido if isinstance(contenido, list) else []

    def _texto(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None
        texto = str(valor).strip()
        return texto if texto else None

    def _numero(self, valor: Any) -> Optional[float]:
        if valor is None or str(valor).strip() == "":
            return None
        if isinstance(valor, (int, float)):
            return float(valor)
        limpio = str(valor).replace(" ", "").replace(",", ".")
        try:
            return float(limpio)
        except ValueError:
            return None


__all__ = ["AlertasStockBajo434", "InformeAlertasStockBajo", "AlertaStockBajo"]
