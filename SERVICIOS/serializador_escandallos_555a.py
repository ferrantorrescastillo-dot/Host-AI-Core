from __future__ import annotations

from dataclasses import asdict
from typing import Any

from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import (
    EstadoRendimiento,
    OrigenRendimiento,
    Receta,
    RendimientoNeto,
)
from SERVICIOS.schema_escandallos_555a import SCHEMA_VERSION, normalizar_unidad
from SERVICIOS.validador_escandallos_555a import validar_escandallo


def escandallo_a_dict(escandallo: Escandallo) -> dict[str, Any]:
    resultado = validar_escandallo(escandallo)
    if not resultado.valido:
        raise ValueError("Escandallo inválido: " + " | ".join(resultado.errores))
    return {
        "schema_version": SCHEMA_VERSION,
        "escandallo": asdict(escandallo),
    }


def escandallo_desde_dict(payload: dict[str, Any]) -> Escandallo:
    datos = payload.get("escandallo", payload)
    coste_total_raw = datos.get("coste_total")
    if coste_total_raw in (None, ""):
        raise ValueError("Escandallo inválido: escandallo.coste_total: obligatorio.")
    receta_datos = datos.get("receta", {})
    ingredientes: list[Ingrediente] = []
    for item in receta_datos.get("ingredientes", []):
        item = dict(item)
        item["unidad"] = normalizar_unidad(item.get("unidad", "")) or str(item.get("unidad", "")).strip()
        ingredientes.append(Ingrediente(**item))

    receta = Receta(
        codigo=str(receta_datos.get("codigo", "")).strip(),
        nombre=str(receta_datos.get("nombre", "")).strip(),
        rendimiento=float(receta_datos.get("rendimiento", 0) or 0),
        unidad_rendimiento=str(receta_datos.get("unidad_rendimiento", "")).strip(),
        ingredientes=ingredientes,
        estado_rendimiento=(
            EstadoRendimiento.desde_valor(receta_datos["estado_rendimiento"])
            if receta_datos.get("estado_rendimiento") else None
        ),
        origen_rendimiento=OrigenRendimiento.desde_dict(receta_datos.get("origen_rendimiento")),
        rendimiento_neto=RendimientoNeto.desde_dict(receta_datos.get("rendimiento_neto")),
    )
    escandallo = Escandallo(receta=receta, coste_total=float(coste_total_raw))
    resultado = validar_escandallo(escandallo)
    if not resultado.valido:
        raise ValueError("Escandallo inválido: " + " | ".join(resultado.errores))
    return escandallo
