from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

SCHEMA_VERSION = "1.1"
UNIDADES_ADMITIDAS = {
    "kg", "g", "l", "ml", "u", "ud", "unidad", "unidades", "racion", "raciones"
}


def normalizar_unidad(unidad: str) -> str:
    valor = (unidad or "").strip().lower()
    equivalencias = {
        "kgs": "kg", "kilo": "kg", "kilos": "kg",
        "gr": "g", "gramo": "g", "gramos": "g",
        "litro": "l", "litros": "l",
        "mililitro": "ml", "mililitros": "ml",
        "uds": "u", "unidad": "u", "unidades": "u", "ud": "u",
        "ración": "racion", "raciones": "racion",
    }
    return equivalencias.get(valor, valor)


def a_dict(objeto: Any) -> dict[str, Any]:
    if not is_dataclass(objeto):
        raise TypeError("El objeto debe ser una entidad dataclass del modelo canónico.")
    datos = asdict(objeto)
    datos["schema_version"] = SCHEMA_VERSION
    return datos
