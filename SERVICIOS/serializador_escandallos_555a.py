from __future__ import annotations

from dataclasses import asdict
from typing import Any

from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
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
    )
    escandallo = Escandallo(receta=receta, coste_total=float(datos.get("coste_total", 0) or 0))
    resultado = validar_escandallo(escandallo)
    if not resultado.valido:
        raise ValueError("Escandallo inválido: " + " | ".join(resultado.errores))
    return escandallo
