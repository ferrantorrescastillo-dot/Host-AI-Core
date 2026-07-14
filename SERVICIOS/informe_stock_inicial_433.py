from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import Counter
import json


@dataclass
class AlertaStockInicial:
    codigo: str
    articulo: str
    unidad: Optional[str]
    stock_actual: float
    stock_minimo: float
    ubicacion: Optional[str]
    tipo: str
    mensaje: str


@dataclass
class InformeStockInicial:
    total_registros_stock: int
    articulos_totales_catalogo: int
    articulos_sin_stock_cargado: int
    bajo_minimo: int
    sin_unidad: int
    sin_ubicacion: int
    ubicaciones: Dict[str, int]
    unidades: Dict[str, int]
    alertas: List[AlertaStockInicial] = field(default_factory=list)
    estado: str = "sin_datos"


class InformeStockInicial433:
    """
    Genera informe del stock inicial real.

    Fuentes:
    - DATOS/db/stock_inicial.json
    - DATOS/db/articulos.json
    """

    def __init__(
        self,
        ruta_stock: str = "DATOS/db/stock_inicial.json",
        ruta_articulos: str = "DATOS/db/articulos.json",
    ) -> None:
        self.ruta_stock = Path(ruta_stock)
        self.ruta_articulos = Path(ruta_articulos)

    def generar(self) -> InformeStockInicial:
        stock = self._leer_json_lista(self.ruta_stock)
        articulos = self._leer_json_lista(self.ruta_articulos)

        codigos_stock = {str(item.get("codigo", "")) for item in stock if item.get("codigo")}
        codigos_articulos = {str(item.get("codigo", "")) for item in articulos if item.get("codigo")}

        articulos_sin_stock = len(codigos_articulos - codigos_stock)

        alertas: List[AlertaStockInicial] = []
        bajo_minimo = 0
        sin_unidad = 0
        sin_ubicacion = 0

        ubicaciones = Counter()
        unidades = Counter()

        for item in stock:
            codigo = str(item.get("codigo", "") or "")
            articulo = str(item.get("articulo", "") or "")
            unidad = self._texto(item.get("unidad"))
            ubicacion = self._texto(item.get("ubicacion"))
            stock_actual = self._numero(item.get("stock_actual")) or 0.0
            stock_minimo = self._numero(item.get("stock_minimo")) or 0.0

            if unidad:
                unidades[unidad] += 1
            else:
                sin_unidad += 1
                alertas.append(AlertaStockInicial(
                    codigo=codigo,
                    articulo=articulo,
                    unidad=unidad,
                    stock_actual=stock_actual,
                    stock_minimo=stock_minimo,
                    ubicacion=ubicacion,
                    tipo="sin_unidad",
                    mensaje="Artículo con stock cargado pero sin unidad.",
                ))

            if ubicacion:
                ubicaciones[ubicacion] += 1
            else:
                sin_ubicacion += 1
                alertas.append(AlertaStockInicial(
                    codigo=codigo,
                    articulo=articulo,
                    unidad=unidad,
                    stock_actual=stock_actual,
                    stock_minimo=stock_minimo,
                    ubicacion=ubicacion,
                    tipo="sin_ubicacion",
                    mensaje="Artículo con stock cargado pero sin ubicación.",
                ))

            if stock_actual < stock_minimo:
                bajo_minimo += 1
                alertas.append(AlertaStockInicial(
                    codigo=codigo,
                    articulo=articulo,
                    unidad=unidad,
                    stock_actual=stock_actual,
                    stock_minimo=stock_minimo,
                    ubicacion=ubicacion,
                    tipo="bajo_minimo",
                    mensaje="Stock actual por debajo del stock mínimo.",
                ))

        estado = self._estado(len(stock), articulos_sin_stock, bajo_minimo, sin_unidad, sin_ubicacion)

        return InformeStockInicial(
            total_registros_stock=len(stock),
            articulos_totales_catalogo=len(codigos_articulos),
            articulos_sin_stock_cargado=articulos_sin_stock,
            bajo_minimo=bajo_minimo,
            sin_unidad=sin_unidad,
            sin_ubicacion=sin_ubicacion,
            ubicaciones=dict(ubicaciones.most_common()),
            unidades=dict(unidades.most_common()),
            alertas=alertas,
            estado=estado,
        )

    def exportar_txt(self, ruta_destino: str = "DATOS/db/informe_stock_inicial_4_3_3.txt") -> InformeStockInicial:
        informe = self.generar()
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.3.3 - INFORME STOCK INICIAL",
            "=" * 64,
            f"Registros de stock cargados: {informe.total_registros_stock}",
            f"Artículos totales catálogo: {informe.articulos_totales_catalogo}",
            f"Artículos sin stock cargado: {informe.articulos_sin_stock_cargado}",
            f"Bajo mínimo: {informe.bajo_minimo}",
            f"Sin unidad: {informe.sin_unidad}",
            f"Sin ubicación: {informe.sin_ubicacion}",
            f"Estado: {informe.estado}",
            "",
            "UBICACIONES",
            "-" * 64,
        ]

        for ubicacion, cantidad in informe.ubicaciones.items():
            lineas.append(f"{ubicacion}: {cantidad}")

        lineas.extend(["", "UNIDADES", "-" * 64])
        for unidad, cantidad in informe.unidades.items():
            lineas.append(f"{unidad}: {cantidad}")

        lineas.extend(["", "ALERTAS", "-" * 64])
        for alerta in informe.alertas[:200]:
            lineas.append(
                f"{alerta.tipo} | {alerta.codigo} | {alerta.articulo} | "
                f"Stock: {alerta.stock_actual} {alerta.unidad or ''} | Mín: {alerta.stock_minimo} | {alerta.mensaje}"
            )

        if len(informe.alertas) > 200:
            lineas.append(f"... {len(informe.alertas) - 200} alertas más")

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
        limpio = str(valor).replace(" ", "").replace(",", ".")
        try:
            return float(limpio)
        except ValueError:
            return None

    def _estado(self, total_stock: int, sin_stock: int, bajo_minimo: int, sin_unidad: int, sin_ubicacion: int) -> str:
        if total_stock == 0:
            return "sin_datos"
        if sin_unidad:
            return "no_apto"
        if bajo_minimo or sin_stock or sin_ubicacion:
            return "apto_con_observaciones"
        return "apto"


__all__ = ["InformeStockInicial433", "InformeStockInicial", "AlertaStockInicial"]
