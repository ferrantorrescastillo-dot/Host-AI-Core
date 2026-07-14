from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


@dataclass
class MovimientoStock:
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
    documento_relacionado: Optional[str] = None


@dataclass
class ResultadoMovimientoStock:
    ok: bool
    codigo: str
    articulo: str
    tipo: str
    cantidad: float
    stock_antes: float
    stock_despues: float
    mensaje: str
    id_movimiento: Optional[str] = None


class MotorMovimientosStock437:
    """
    Motor base de movimientos de stock.

    Lee y actualiza:
    - DATOS/db/stock_inicial.json

    Registra historial en:
    - DATOS/db/stock_movimientos.json

    Tipos:
    - entrada
    - salida
    - ajuste
    """

    TIPOS_VALIDOS = {"entrada", "salida", "ajuste"}

    def __init__(
        self,
        ruta_stock: str = "DATOS/db/stock_inicial.json",
        ruta_movimientos: str = "DATOS/db/stock_movimientos.json",
    ) -> None:
        self.ruta_stock = Path(ruta_stock)
        self.ruta_movimientos = Path(ruta_movimientos)

    def registrar_movimiento(
        self,
        codigo: str,
        cantidad: Any,
        tipo: str,
        motivo: str,
        usuario: str = "sistema",
        documento_relacionado: Optional[str] = None,
    ) -> ResultadoMovimientoStock:
        codigo_limpio = self._texto(codigo)
        tipo_limpio = self._texto(tipo).lower() if self._texto(tipo) else ""
        motivo_limpio = self._texto(motivo) or "Sin motivo"
        cantidad_num = self._numero(cantidad)

        if not codigo_limpio:
            raise ValueError("El código del artículo es obligatorio.")

        if tipo_limpio not in self.TIPOS_VALIDOS:
            raise ValueError(f"Tipo de movimiento no válido: {tipo}. Usa entrada, salida o ajuste.")

        if cantidad_num is None:
            raise ValueError("La cantidad debe ser numérica.")

        if tipo_limpio in {"entrada", "salida"} and cantidad_num <= 0:
            raise ValueError("La cantidad de entrada/salida debe ser mayor que 0.")

        stock = self._leer_json_lista(self.ruta_stock)
        articulo = self._buscar_articulo_stock(stock, codigo_limpio)

        if articulo is None:
            return ResultadoMovimientoStock(
                ok=False,
                codigo=codigo_limpio,
                articulo="",
                tipo=tipo_limpio,
                cantidad=cantidad_num,
                stock_antes=0.0,
                stock_despues=0.0,
                mensaje="No existe ese artículo en stock_inicial.json.",
            )

        stock_antes = self._numero(articulo.get("stock_actual")) or 0.0

        if tipo_limpio == "entrada":
            stock_despues = stock_antes + cantidad_num
        elif tipo_limpio == "salida":
            stock_despues = stock_antes - cantidad_num
            if stock_despues < 0:
                return ResultadoMovimientoStock(
                    ok=False,
                    codigo=codigo_limpio,
                    articulo=str(articulo.get("articulo", "") or ""),
                    tipo=tipo_limpio,
                    cantidad=cantidad_num,
                    stock_antes=stock_antes,
                    stock_despues=stock_antes,
                    mensaje="No hay stock suficiente para realizar la salida.",
                )
        else:
            # ajuste: la cantidad representa el stock final real
            if cantidad_num < 0:
                raise ValueError("El ajuste de stock no puede dejar stock negativo.")
            stock_despues = cantidad_num

        articulo["stock_actual"] = round(stock_despues, 4)
        self._guardar_json_lista(self.ruta_stock, stock)

        movimientos = self._leer_json_lista(self.ruta_movimientos)
        id_movimiento = f"MOV{len(movimientos) + 1:08d}"

        movimiento = MovimientoStock(
            id_movimiento=id_movimiento,
            fecha_hora=datetime.now().isoformat(timespec="seconds"),
            codigo=codigo_limpio,
            articulo=str(articulo.get("articulo", "") or ""),
            tipo=tipo_limpio,
            cantidad=cantidad_num,
            unidad=str(articulo.get("unidad", "") or ""),
            motivo=motivo_limpio,
            stock_antes=round(stock_antes, 4),
            stock_despues=round(stock_despues, 4),
            usuario=usuario,
            documento_relacionado=documento_relacionado,
        )

        movimientos.append(asdict(movimiento))
        self._guardar_json_lista(self.ruta_movimientos, movimientos)

        return ResultadoMovimientoStock(
            ok=True,
            codigo=codigo_limpio,
            articulo=movimiento.articulo,
            tipo=tipo_limpio,
            cantidad=cantidad_num,
            stock_antes=round(stock_antes, 4),
            stock_despues=round(stock_despues, 4),
            mensaje="Movimiento registrado correctamente.",
            id_movimiento=id_movimiento,
        )

    def _buscar_articulo_stock(self, stock: List[Dict[str, Any]], codigo: str) -> Optional[Dict[str, Any]]:
        for articulo in stock:
            if str(articulo.get("codigo", "")).strip() == codigo:
                return articulo
        return None

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


__all__ = ["MotorMovimientosStock437", "MovimientoStock", "ResultadoMovimientoStock"]
