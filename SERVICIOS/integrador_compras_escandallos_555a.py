from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from SERVICIOS.integrador_stock_escandallos_555a import LineaNecesidadStock


@dataclass(slots=True)
class LineaCompraPropuesta:
    codigo: str
    articulo: str
    unidad: str
    cantidad: float
    proveedor: str | None
    precio_unitario: float | None
    coste_estimado: float | None

    def a_dict(self) -> dict:
        return asdict(self)


def _leer_articulos(ruta: str | Path) -> list[dict]:
    path = Path(ruta)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


def _normalizar(texto: object) -> str:
    return str(texto or "").strip().casefold()


def preparar_compras_desde_faltantes(
    necesidades: list[LineaNecesidadStock],
    ruta_articulos: str | Path = "DATOS/db/articulos.json",
    incluir_stock_minimo: bool = False,
) -> list[LineaCompraPropuesta]:
    """Genera una propuesta de compra, nunca un pedido real.

    Solo incluye ingredientes con faltante. Opcionalmente repone además el stock mínimo.
    """
    articulos = _leer_articulos(ruta_articulos)
    por_codigo = {_normalizar(a.get("codigo")): a for a in articulos if a.get("codigo")}
    por_nombre = {_normalizar(a.get("nombre") or a.get("articulo")): a for a in articulos}
    propuestas: list[LineaCompraPropuesta] = []

    for linea in necesidades:
        if linea.faltante <= 1e-9:
            continue
        articulo = por_codigo.get(_normalizar(linea.codigo)) or por_nombre.get(_normalizar(linea.ingrediente), {})
        cantidad = linea.faltante + (linea.stock_minimo if incluir_stock_minimo else 0.0)
        precio_raw = articulo.get("precio")
        precio = float(precio_raw) if precio_raw not in (None, "") else None
        proveedor = articulo.get("proveedor") or linea.proveedor
        propuestas.append(
            LineaCompraPropuesta(
                codigo=linea.codigo or str(articulo.get("codigo", "")),
                articulo=linea.ingrediente,
                unidad=linea.unidad,
                cantidad=round(cantidad, 6),
                proveedor=proveedor,
                precio_unitario=precio,
                coste_estimado=(round(cantidad * precio, 2) if precio is not None else None),
            )
        )
    return propuestas
