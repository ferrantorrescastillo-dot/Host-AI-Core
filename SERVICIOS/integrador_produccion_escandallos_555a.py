from __future__ import annotations

from dataclasses import dataclass, asdict

from CORE.entidades.escandallo import Escandallo


@dataclass(slots=True)
class LineaProduccion:
    codigo: str
    elaboracion: str
    personas: float
    factor: float
    cantidad_objetivo: float
    unidad_rendimiento: str
    ingredientes: list[dict]
    estado: str = "preliminar_no_aplicado"

    def a_dict(self) -> dict:
        return asdict(self)


def preparar_plan_produccion(escandallo: Escandallo, personas: float) -> LineaProduccion:
    """Prepara cantidades de producción desde un escandallo canónico.

    No crea órdenes de producción ni reserva recursos.
    """
    if personas <= 0:
        raise ValueError("Las personas deben ser mayores que cero")
    rendimiento = float(escandallo.receta.rendimiento)
    if rendimiento <= 0:
        raise ValueError("El rendimiento del escandallo debe ser mayor que cero")
    factor = personas / rendimiento
    ingredientes = [
        {
            "codigo": i.articulo_id or i.codigo,
            "nombre": i.nombre,
            "cantidad": round(float(i.cantidad) * factor, 6),
            "unidad": i.unidad,
            "merma_pct": float(i.merma_pct),
        }
        for i in escandallo.receta.ingredientes
    ]
    return LineaProduccion(
        codigo=escandallo.receta.codigo,
        elaboracion=escandallo.receta.nombre,
        personas=personas,
        factor=round(factor, 6),
        cantidad_objetivo=personas,
        unidad_rendimiento=escandallo.receta.unidad_rendimiento,
        ingredientes=ingredientes,
    )
