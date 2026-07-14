from __future__ import annotations

import re
import unicodedata
from typing import Any


def _clave(texto: object) -> str:
    valor = str(texto or "").strip().lower()
    valor = "".join(c for c in unicodedata.normalize("NFD", valor) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", valor).split())


class NormalizadorFichasEscandallo555B:
    """Normaliza la vista previa extraída al contrato canónico de 5.5.5A, sin guardarla."""

    def normalizar_ficha(self, ficha: dict[str, Any]) -> dict[str, Any]:
        nombre = str(ficha.get("nombre") or "").strip()
        ingredientes = []
        for item in ficha.get("ingredientes", []):
            ingredientes.append({
                "nombre": str(item.get("nombre") or "").strip(),
                "cantidad": float(item.get("cantidad") or 0),
                "unidad": str(item.get("unidad") or "unidad_origen").strip(),
                "precio_unitario": item.get("precio_unitario"),
                "coste_racion": item.get("coste_racion"),
                "origen": {
                    "hoja": ficha.get("hoja"),
                    "fila": item.get("fila_origen"),
                },
            })
        return {
            "id_externo": f"excel:{_clave(ficha.get('hoja'))}:{ficha.get('fila_inicio')}",
            "nombre": nombre,
            "rendimiento": ficha.get("rendimiento"),
            "unidad_rendimiento": ficha.get("unidad_rendimiento"),
            "ingredientes": ingredientes,
            "origen": {
                "tipo": "excel",
                "hoja": ficha.get("hoja"),
                "fila_inicio": ficha.get("fila_inicio"),
                "fila_fin": ficha.get("fila_fin"),
            },
            "confianza_extraccion": ficha.get("confianza", 0),
            "estado_importacion": "VISTA_PREVIA",
        }

    def normalizar_resultado(self, resultado: dict[str, Any]) -> dict[str, Any]:
        fichas = [self.normalizar_ficha(f) for f in resultado.get("fichas", [])]
        return {
            "archivo": resultado.get("archivo"),
            "escandallos_canonicos_previsualizados": fichas,
            "total": len(fichas),
            "modo": "vista_previa_solo_lectura",
            "datos_reales_modificados": False,
        }
