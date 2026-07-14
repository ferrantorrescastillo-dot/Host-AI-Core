from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict
from datetime import datetime
import json


@dataclass
class LineaPedidoSugerido:
    codigo: str
    articulo: str
    proveedor: Optional[str]
    familia: Optional[str]
    unidad: str
    stock_actual: float
    stock_minimo: float
    cantidad_sugerida: float
    ubicacion: Optional[str]
    prioridad: str


@dataclass
class PedidoSugeridoProveedor:
    proveedor: str
    lineas: List[LineaPedidoSugerido] = field(default_factory=list)

    @property
    def total_lineas(self) -> int:
        return len(self.lineas)


@dataclass
class InformePedidoSugerido:
    fecha_generacion: str
    total_lineas: int
    total_proveedores: int
    pedidos_por_proveedor: List[PedidoSugeridoProveedor]
    ruta_json: str
    estado: str


class GeneradorPedidoStockBajo435:
    """
    Genera una propuesta de pedido a partir de stock bajo.

    Fuente:
    DATOS/db/stock_inicial.json

    Salida:
    DATOS/db/pedido_sugerido_stock_bajo_4_3_5.json
    """

    def __init__(self, ruta_stock: str = "DATOS/db/stock_inicial.json") -> None:
        self.ruta_stock = Path(ruta_stock)

    def generar(
        self,
        ruta_json: str = "DATOS/db/pedido_sugerido_stock_bajo_4_3_5.json",
        ruta_txt: str = "DATOS/db/pedido_sugerido_stock_bajo_4_3_5.txt",
    ) -> InformePedidoSugerido:
        stock = self._leer_json_lista(self.ruta_stock)
        grupos: Dict[str, List[LineaPedidoSugerido]] = defaultdict(list)

        for item in stock:
            stock_actual = self._numero(item.get("stock_actual")) or 0.0
            stock_minimo = self._numero(item.get("stock_minimo")) or 0.0

            if stock_actual >= stock_minimo:
                continue

            cantidad = round(stock_minimo - stock_actual, 4)
            proveedor = self._texto(item.get("proveedor")) or "SIN_PROVEEDOR"

            linea = LineaPedidoSugerido(
                codigo=str(item.get("codigo", "") or ""),
                articulo=str(item.get("articulo", "") or ""),
                proveedor=proveedor,
                familia=self._texto(item.get("familia")),
                unidad=self._texto(item.get("unidad")) or "",
                stock_actual=stock_actual,
                stock_minimo=stock_minimo,
                cantidad_sugerida=cantidad,
                ubicacion=self._texto(item.get("ubicacion")),
                prioridad=self._prioridad(stock_actual, stock_minimo),
            )
            grupos[proveedor].append(linea)

        pedidos = [
            PedidoSugeridoProveedor(proveedor=proveedor, lineas=sorted(lineas, key=lambda x: x.prioridad))
            for proveedor, lineas in sorted(grupos.items())
        ]

        informe = InformePedidoSugerido(
            fecha_generacion=datetime.now().isoformat(timespec="seconds"),
            total_lineas=sum(len(p.lineas) for p in pedidos),
            total_proveedores=len(pedidos),
            pedidos_por_proveedor=pedidos,
            ruta_json=str(Path(ruta_json)),
            estado="sin_necesidades" if not pedidos else "pedido_sugerido",
        )

        self._exportar_json(informe, ruta_json)
        self._exportar_txt(informe, ruta_txt)
        return informe

    def _exportar_json(self, informe: InformePedidoSugerido, ruta_json: str) -> None:
        ruta = Path(ruta_json)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(asdict(informe), ensure_ascii=False, indent=2), encoding="utf-8")

    def _exportar_txt(self, informe: InformePedidoSugerido, ruta_txt: str) -> None:
        ruta = Path(ruta_txt)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.3.5 - PEDIDO SUGERIDO DESDE STOCK BAJO",
            "=" * 72,
            f"Fecha: {informe.fecha_generacion}",
            f"Total líneas: {informe.total_lineas}",
            f"Total proveedores: {informe.total_proveedores}",
            f"Estado: {informe.estado}",
            "",
        ]

        if not informe.pedidos_por_proveedor:
            lineas.append("No hay necesidades de pedido según el stock mínimo.")

        for pedido in informe.pedidos_por_proveedor:
            lineas.extend([
                f"PROVEEDOR: {pedido.proveedor}",
                "-" * 72,
            ])

            for linea in pedido.lineas:
                lineas.append(
                    f"[{linea.prioridad.upper()}] {linea.codigo} | {linea.articulo} | "
                    f"Pedir: {linea.cantidad_sugerida} {linea.unidad} | "
                    f"Stock: {linea.stock_actual} | Mín: {linea.stock_minimo} | "
                    f"Ubicación: {linea.ubicacion or '-'}"
                )

            lineas.append("")

        ruta.write_text("\n".join(lineas), encoding="utf-8")

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
        limpio = str(valor).replace(" ", "").replace(",", ".")
        try:
            return float(limpio)
        except ValueError:
            return None

    def _texto(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None
        texto = str(valor).strip()
        return texto if texto else None

    def _prioridad(self, stock_actual: float, stock_minimo: float) -> str:
        if stock_minimo <= 0:
            return "media"
        if stock_actual <= 0:
            return "critica"
        if stock_actual / stock_minimo <= 0.5:
            return "alta"
        return "media"


__all__ = [
    "GeneradorPedidoStockBajo435",
    "LineaPedidoSugerido",
    "PedidoSugeridoProveedor",
    "InformePedidoSugerido",
]
