from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


@dataclass
class LineaPedidoConfirmado:
    codigo: str
    articulo: str
    proveedor: str
    unidad: str
    cantidad: float
    prioridad: str
    estado: str = "pendiente"


@dataclass
class PedidoConfirmado:
    id_pedido: str
    fecha_confirmacion: str
    proveedor: str
    lineas: List[LineaPedidoConfirmado] = field(default_factory=list)
    estado: str = "confirmado"


@dataclass
class ResultadoConfirmacionPedido:
    pedidos_confirmados: int
    lineas_confirmadas: int
    ruta_destino: str
    estado: str
    mensaje: str


class ConfirmadorPedidoSugerido436:
    """
    Convierte pedido_sugerido_stock_bajo_4_3_5.json en pedidos confirmados.

    Entrada:
    DATOS/db/pedido_sugerido_stock_bajo_4_3_5.json

    Salida:
    DATOS/db/pedidos_confirmados.json
    """

    def __init__(
        self,
        ruta_pedido_sugerido: str = "DATOS/db/pedido_sugerido_stock_bajo_4_3_5.json",
        ruta_pedidos_confirmados: str = "DATOS/db/pedidos_confirmados.json",
    ) -> None:
        self.ruta_pedido_sugerido = Path(ruta_pedido_sugerido)
        self.ruta_pedidos_confirmados = Path(ruta_pedidos_confirmados)

    def confirmar(self) -> ResultadoConfirmacionPedido:
        sugerido = self._leer_json(self.ruta_pedido_sugerido)

        pedidos_por_proveedor = sugerido.get("pedidos_por_proveedor", [])
        if not pedidos_por_proveedor:
            return ResultadoConfirmacionPedido(
                pedidos_confirmados=0,
                lineas_confirmadas=0,
                ruta_destino=str(self.ruta_pedidos_confirmados),
                estado="sin_pedido",
                mensaje="No hay pedido sugerido para confirmar.",
            )

        existentes = self._leer_json_lista(self.ruta_pedidos_confirmados)
        nuevos_pedidos: List[Dict[str, Any]] = []

        fecha = datetime.now().isoformat(timespec="seconds")
        contador_base = len(existentes) + 1

        for idx, pedido in enumerate(pedidos_por_proveedor, start=contador_base):
            proveedor = str(pedido.get("proveedor") or "SIN_PROVEEDOR")
            lineas_raw = pedido.get("lineas", []) or []

            lineas: List[LineaPedidoConfirmado] = []
            for linea in lineas_raw:
                cantidad = self._numero(linea.get("cantidad_sugerida")) or 0.0
                if cantidad <= 0:
                    continue

                lineas.append(
                    LineaPedidoConfirmado(
                        codigo=str(linea.get("codigo", "") or ""),
                        articulo=str(linea.get("articulo", "") or ""),
                        proveedor=proveedor,
                        unidad=str(linea.get("unidad", "") or ""),
                        cantidad=cantidad,
                        prioridad=str(linea.get("prioridad", "media") or "media"),
                    )
                )

            if not lineas:
                continue

            pedido_confirmado = PedidoConfirmado(
                id_pedido=f"PED{idx:06d}",
                fecha_confirmacion=fecha,
                proveedor=proveedor,
                lineas=lineas,
            )

            nuevos_pedidos.append(asdict(pedido_confirmado))

        todos = existentes + nuevos_pedidos
        self.ruta_pedidos_confirmados.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_pedidos_confirmados.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")

        lineas_confirmadas = sum(len(p["lineas"]) for p in nuevos_pedidos)

        return ResultadoConfirmacionPedido(
            pedidos_confirmados=len(nuevos_pedidos),
            lineas_confirmadas=lineas_confirmadas,
            ruta_destino=str(self.ruta_pedidos_confirmados),
            estado="confirmado" if nuevos_pedidos else "sin_lineas_validas",
            mensaje=f"Pedidos confirmados: {len(nuevos_pedidos)}. Líneas: {lineas_confirmadas}.",
        )

    def _leer_json(self, ruta: Path) -> Dict[str, Any]:
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


__all__ = [
    "ConfirmadorPedidoSugerido436",
    "PedidoConfirmado",
    "LineaPedidoConfirmado",
    "ResultadoConfirmacionPedido",
]
