from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List


def _n(texto: str) -> str:
    t = (texto or "").strip().lower()
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def resolver_referencia_natural_5413(texto: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
    t = _n(texto)
    acciones: List[Dict[str, Any]] = list(((contexto.get("confirmaciones") or {}).get("acciones_con_confirmacion") or []))
    ultima = contexto.get("accion_seleccionada")

    if t in {"que queda", "que queda pendiente", "pendientes", "que falta", "que nos falta"}:
        confirmadas = contexto.get("confirmaciones_especificas") or {}
        pendientes = [a for a in acciones if not (confirmadas.get(str(a.get("codigo") or a.get("nombre") or "accion")) or {}).get("confirmada")]
        return {"gestionado": True, "tipo": "consultar_pendientes", "acciones": pendientes}

    if t in {"esa", "esa opcion", "esa accion", "hazlo", "aplicalo", "confirmala", "confirmalo", "perfecto"} and ultima:
        return {"gestionado": True, "tipo": "referencia_ultima_accion", "accion": ultima}

    if "la otra" in t or "otra opcion" in t or "mejor la otra" in t:
        if not acciones:
            return {"gestionado": False, "tipo": "sin_acciones"}
        indice_actual = -1
        for i, accion in enumerate(acciones):
            if ultima and (accion.get("codigo") == ultima.get("codigo") or accion.get("nombre") == ultima.get("nombre")):
                indice_actual = i
                break
        nuevo = 0 if indice_actual < 0 else (indice_actual + 1) % len(acciones)
        return {"gestionado": True, "tipo": "otra_accion", "indice": nuevo, "accion": acciones[nuevo]}

    ordinales = {"primera": 0, "primero": 0, "segunda": 1, "segundo": 1, "tercera": 2, "tercero": 2}
    for palabra, indice in ordinales.items():
        if palabra in t and 0 <= indice < len(acciones):
            return {"gestionado": True, "tipo": "referencia_ordinal", "indice": indice, "accion": acciones[indice]}

    if t in {"continua", "continuar", "sigue", "adelante"}:
        return {"gestionado": True, "tipo": "continuar_contexto"}
    return {"gestionado": False, "tipo": "desconocido"}


def formatear_pendientes_5413(acciones: List[Dict[str, Any]]) -> str:
    if not acciones:
        return "No quedan acciones pendientes de confirmación en este flujo."
    lineas = ["ACCIONES QUE QUEDAN PENDIENTES"]
    for i, accion in enumerate(acciones, 1):
        lineas.append(f"{i}. {accion.get('nombre')}")
    lineas.extend(["", "Puedes decirme el número, 'la segunda', 'esa opción' o el nombre de la acción."])
    return "\n".join(lineas)


__all__ = ["resolver_referencia_natural_5413", "formatear_pendientes_5413"]
