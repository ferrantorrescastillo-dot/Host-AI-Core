from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from SERVICIOS.motor_movimientos_stock_437 import MotorMovimientosStock437


@dataclass
class LineaEntradaPedido:
    id_pedido: str
    proveedor: str
    codigo: str
    articulo: str
    cantidad: float
    unidad: str
    ok: bool
    mensaje: str
    id_movimiento: Optional[str] = None


@dataclass
class ResultadoEntradaPedido:
    pedidos_procesados: int
    lineas_procesadas: int
    entradas_ok: int
    entradas_error: int
    lineas: List[LineaEntradaPedido] = field(default_factory=list)
    estado: str = "sin_datos"


class EntradaStockDesdePedido438:
    """
    Convierte pedidos confirmados en entradas de stock.

    Entrada:
    DATOS/db/pedidos_confirmados.json

    Actualiza:
    DATOS/db/stock_inicial.json

    Registra movimientos:
    DATOS/db/stock_movimientos.json
    """

    def __init__(
        self,
        ruta_pedidos: str = "DATOS/db/pedidos_confirmados.json",
        ruta_stock: str = "DATOS/db/stock_inicial.json",
        ruta_movimientos: str = "DATOS/db/stock_movimientos.json",
    ) -> None:
        self.ruta_pedidos = Path(ruta_pedidos)
        self.ruta_stock = Path(ruta_stock)
        self.ruta_movimientos = Path(ruta_movimientos)

    def procesar(self) -> ResultadoEntradaPedido:
        pedidos = self._leer_json_lista(self.ruta_pedidos)
        motor = MotorMovimientosStock437(str(self.ruta_stock), str(self.ruta_movimientos))

        lineas_resultado: List[LineaEntradaPedido] = []
        pedidos_procesados = 0
        entradas_ok = 0
        entradas_error = 0

        for pedido in pedidos:
            if pedido.get("estado") == "recibido_stock":
                continue

            id_pedido = str(pedido.get("id_pedido", "") or "")
            proveedor = str(pedido.get("proveedor", "") or "SIN_PROVEEDOR")
            lineas = pedido.get("lineas", []) or []

            if not lineas:
                continue

            pedidos_procesados += 1
            pedido_ok = True

            for linea in lineas:
                codigo = str(linea.get("codigo", "") or "")
                articulo = str(linea.get("articulo", "") or "")
                cantidad = self._numero(linea.get("cantidad")) or 0.0
                unidad = str(linea.get("unidad", "") or "")

                if cantidad <= 0:
                    entradas_error += 1
                    pedido_ok = False
                    lineas_resultado.append(
                        LineaEntradaPedido(
                            id_pedido=id_pedido,
                            proveedor=proveedor,
                            codigo=codigo,
                            articulo=articulo,
                            cantidad=cantidad,
                            unidad=unidad,
                            ok=False,
                            mensaje="Cantidad inválida.",
                        )
                    )
                    continue

                resultado = motor.registrar_movimiento(
                    codigo=codigo,
                    cantidad=cantidad,
                    tipo="entrada",
                    motivo=f"Entrada desde pedido confirmado {id_pedido}",
                    usuario="sistema",
                    documento_relacionado=id_pedido,
                )

                if resultado.ok:
                    entradas_ok += 1
                else:
                    entradas_error += 1
                    pedido_ok = False

                lineas_resultado.append(
                    LineaEntradaPedido(
                        id_pedido=id_pedido,
                        proveedor=proveedor,
                        codigo=codigo,
                        articulo=articulo,
                        cantidad=cantidad,
                        unidad=unidad,
                        ok=resultado.ok,
                        mensaje=resultado.mensaje,
                        id_movimiento=resultado.id_movimiento,
                    )
                )

            if pedido_ok:
                pedido["estado"] = "recibido_stock"

        self._guardar_json_lista(self.ruta_pedidos, pedidos)

        estado = "ok" if entradas_ok and entradas_error == 0 else "revisar" if entradas_ok or entradas_error else "sin_datos"

        return ResultadoEntradaPedido(
            pedidos_procesados=pedidos_procesados,
            lineas_procesadas=len(lineas_resultado),
            entradas_ok=entradas_ok,
            entradas_error=entradas_error,
            lineas=lineas_resultado,
            estado=estado,
        )

    def exportar_txt(self, ruta_destino: str = "DATOS/db/entradas_desde_pedido_4_3_8.txt") -> ResultadoEntradaPedido:
        resultado = self.procesar()
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.3.8 - ENTRADAS DESDE PEDIDOS CONFIRMADOS",
            "=" * 72,
            f"Pedidos procesados: {resultado.pedidos_procesados}",
            f"Líneas procesadas: {resultado.lineas_procesadas}",
            f"Entradas OK: {resultado.entradas_ok}",
            f"Entradas error: {resultado.entradas_error}",
            f"Estado: {resultado.estado}",
            "",
            "DETALLE",
            "-" * 72,
        ]

        for linea in resultado.lineas:
            estado = "OK" if linea.ok else "ERROR"
            lineas.append(
                f"[{estado}] {linea.id_pedido} | {linea.proveedor} | {linea.codigo} | "
                f"{linea.articulo} | +{linea.cantidad} {linea.unidad} | {linea.mensaje}"
            )

        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return resultado

    def _leer_json_lista(self, ruta: Path) -> List[Dict[str, Any]]:
        if not ruta.exists():
            return []
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return contenido if isinstance(contenido, list) else []

    def _guardar_json_lista(self, ruta: Path, datos: List[Dict[str, Any]]) -> None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    def _numero(self, valor: Any) -> Optional[float]:
        if valor is None or str(valor).strip() == "":
            return None
        if isinstance(valor, (int, float)):
            return float(valor)
        try:
            return float(str(valor).replace(",", "."))
        except ValueError:
            return None


__all__ = ["EntradaStockDesdePedido438", "ResultadoEntradaPedido", "LineaEntradaPedido"]
