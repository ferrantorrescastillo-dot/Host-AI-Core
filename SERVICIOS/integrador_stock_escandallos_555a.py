from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from CORE.entidades.escandallo import Escandallo


@dataclass(slots=True)
class LineaNecesidadStock:
    codigo: str
    ingrediente: str
    unidad: str
    necesario: float
    disponible: float
    faltante: float
    stock_minimo: float
    proveedor: str | None = None

    @property
    def cubierto(self) -> bool:
        return self.faltante <= 1e-9

    def a_dict(self) -> dict:
        data = asdict(self)
        data["cubierto"] = self.cubierto
        return data


def _leer_lista(ruta: str | Path) -> list[dict]:
    path = Path(ruta)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


def _normalizar(texto: object) -> str:
    return str(texto or "").strip().casefold()


def calcular_necesidades_stock(
    escandallo: Escandallo,
    personas: float,
    ruta_stock: str | Path = "DATOS/db/stock_inicial.json",
) -> list[LineaNecesidadStock]:
    """Escala un escandallo y lo contrasta con el inventario real.

    Es una operación de solo lectura. No descuenta existencias ni modifica datos.
    """
    if personas <= 0:
        raise ValueError("Las personas deben ser mayores que cero")
    rendimiento = float(escandallo.receta.rendimiento)
    if rendimiento <= 0:
        raise ValueError("El rendimiento del escandallo debe ser mayor que cero")

    stock = _leer_lista(ruta_stock)
    por_codigo = {_normalizar(x.get("codigo")): x for x in stock if x.get("codigo")}
    por_nombre = {_normalizar(x.get("articulo") or x.get("nombre")): x for x in stock}
    factor = personas / rendimiento
    salida: list[LineaNecesidadStock] = []

    for ingrediente in escandallo.receta.ingredientes:
        registro = None
        for clave in (ingrediente.articulo_id, ingrediente.codigo):
            if clave and _normalizar(clave) in por_codigo:
                registro = por_codigo[_normalizar(clave)]
                break
        if registro is None:
            registro = por_nombre.get(_normalizar(ingrediente.nombre), {})

        necesario = round(float(ingrediente.cantidad) * factor, 6)
        disponible = float(registro.get("stock_actual", 0) or 0)
        faltante = round(max(0.0, necesario - disponible), 6)
        salida.append(
            LineaNecesidadStock(
                codigo=str(ingrediente.articulo_id or ingrediente.codigo or registro.get("codigo", "")),
                ingrediente=ingrediente.nombre,
                unidad=ingrediente.unidad or str(registro.get("unidad", "")),
                necesario=necesario,
                disponible=disponible,
                faltante=faltante,
                stock_minimo=float(registro.get("stock_minimo", 0) or 0),
                proveedor=(registro.get("proveedor") or ingrediente.proveedor_habitual),
            )
        )
    return salida
