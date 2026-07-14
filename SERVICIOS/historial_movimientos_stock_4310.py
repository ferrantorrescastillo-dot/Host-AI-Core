from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


@dataclass
class MovimientoStockResumen:
    id_movimiento: str
    fecha_hora: str
    codigo: str
    articulo: str
    tipo: str
    cantidad: float
    unidad: str
    motivo: str
    stock_antes: float
    stock_despues: float
    usuario: str
    documento_relacionado: Optional[str]


@dataclass
class InformeHistorialStock:
    total_movimientos: int
    movimientos_filtrados: int
    codigo_filtro: Optional[str]
    tipo_filtro: Optional[str]
    movimientos: List[MovimientoStockResumen] = field(default_factory=list)
    estado: str = "sin_datos"


class HistorialMovimientosStock4310:
    """
    Consulta historial de movimientos de stock.

    Fuente:
    DATOS/db/stock_movimientos.json
    """

    def __init__(self, ruta_movimientos: str = "DATOS/db/stock_movimientos.json") -> None:
        self.ruta_movimientos = Path(ruta_movimientos)

    def consultar(
        self,
        codigo: Optional[str] = None,
        tipo: Optional[str] = None,
        limite: int = 50,
    ) -> InformeHistorialStock:
        movimientos_raw = self._leer_json_lista(self.ruta_movimientos)

        codigo_limpio = self._texto(codigo)
        tipo_limpio = self._texto(tipo).lower() if self._texto(tipo) else None

        filtrados = []

        for movimiento in movimientos_raw:
            if codigo_limpio and str(movimiento.get("codigo", "")).strip() != codigo_limpio:
                continue
            if tipo_limpio and str(movimiento.get("tipo", "")).strip().lower() != tipo_limpio:
                continue
            filtrados.append(movimiento)

        # Últimos movimientos primero.
        filtrados = list(reversed(filtrados))[:limite]

        movimientos = [
            MovimientoStockResumen(
                id_movimiento=str(m.get("id_movimiento", "") or ""),
                fecha_hora=str(m.get("fecha_hora", "") or ""),
                codigo=str(m.get("codigo", "") or ""),
                articulo=str(m.get("articulo", "") or ""),
                tipo=str(m.get("tipo", "") or ""),
                cantidad=self._numero(m.get("cantidad")) or 0.0,
                unidad=str(m.get("unidad", "") or ""),
                motivo=str(m.get("motivo", "") or ""),
                stock_antes=self._numero(m.get("stock_antes")) or 0.0,
                stock_despues=self._numero(m.get("stock_despues")) or 0.0,
                usuario=str(m.get("usuario", "") or ""),
                documento_relacionado=self._texto(m.get("documento_relacionado")),
            )
            for m in filtrados
        ]

        estado = "ok" if movimientos else "sin_resultados" if movimientos_raw else "sin_datos"

        return InformeHistorialStock(
            total_movimientos=len(movimientos_raw),
            movimientos_filtrados=len(movimientos),
            codigo_filtro=codigo_limpio,
            tipo_filtro=tipo_limpio,
            movimientos=movimientos,
            estado=estado,
        )

    def exportar_txt(
        self,
        ruta_destino: str = "DATOS/db/historial_movimientos_stock_4_3_10.txt",
        codigo: Optional[str] = None,
        tipo: Optional[str] = None,
        limite: int = 50,
    ) -> InformeHistorialStock:
        informe = self.consultar(codigo=codigo, tipo=tipo, limite=limite)
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.3.10 - HISTORIAL MOVIMIENTOS DE STOCK",
            "=" * 76,
            f"Total movimientos: {informe.total_movimientos}",
            f"Movimientos mostrados: {informe.movimientos_filtrados}",
            f"Filtro código: {informe.codigo_filtro or '-'}",
            f"Filtro tipo: {informe.tipo_filtro or '-'}",
            f"Estado: {informe.estado}",
            "",
            "MOVIMIENTOS",
            "-" * 76,
        ]

        if not informe.movimientos:
            lineas.append("No hay movimientos para mostrar.")

        for mov in informe.movimientos:
            lineas.append(
                f"{mov.fecha_hora} | {mov.id_movimiento} | {mov.codigo} | {mov.articulo} | "
                f"{mov.tipo.upper()} {mov.cantidad} {mov.unidad} | "
                f"{mov.stock_antes} -> {mov.stock_despues} | "
                f"{mov.motivo} | Usuario: {mov.usuario} | Doc: {mov.documento_relacionado or '-'}"
            )

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
        try:
            return float(str(valor).replace(",", "."))
        except ValueError:
            return None


__all__ = ["HistorialMovimientosStock4310", "InformeHistorialStock", "MovimientoStockResumen"]
