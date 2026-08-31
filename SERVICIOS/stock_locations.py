from __future__ import annotations

import unicodedata
from typing import Any


STOCK_LOCATIONS: tuple[dict[str, str], ...] = (
    {"id": "Congelador", "nombre": "Congelador"},
    {"id": "Cámara", "nombre": "Cámara"},
    {"id": "Seco", "nombre": "Seco"},
    {"id": "Bodega", "nombre": "Bodega"},
    {"id": "Limpieza", "nombre": "Limpieza"},
)


def canonical_location_id(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").strip())
    normalized = "".join(char for char in text if not unicodedata.combining(char)).upper()
    aliases = {unicodedata.normalize("NFKD", item["id"]).encode("ascii", "ignore").decode().upper(): item["id"] for item in STOCK_LOCATIONS}
    aliases.update({
        "CAMARA": "Cámara", "CONGELADOR": "Congelador", "SECO": "Seco",
        "BODEGA": "Bodega", "LIMPIEZA": "Limpieza",
    })
    return aliases.get(normalized, "")


def location_name(value: Any) -> str:
    location_id = canonical_location_id(value)
    return next((item["nombre"] for item in STOCK_LOCATIONS if item["id"] == location_id), "")


__all__ = ["STOCK_LOCATIONS", "canonical_location_id", "location_name"]
