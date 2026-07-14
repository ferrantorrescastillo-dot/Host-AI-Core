from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List


def normalizar_5412(texto: str) -> str:
    t = (texto or "").strip().lower()
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def _buscar_accion(texto: str, acciones: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    t = normalizar_5412(texto)
    ordinales = {"primera": 0, "primero": 0, "segunda": 1, "segundo": 1, "tercera": 2, "tercero": 2}
    m = re.search(r"\b(\d+)\b", t)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(acciones):
            return {"indice": idx, "accion": acciones[idx]}
    for palabra, idx in ordinales.items():
        if palabra in t and 0 <= idx < len(acciones):
            return {"indice": idx, "accion": acciones[idx]}
    equivalencias = {
        "compra": ["compra", "pedido"],
        "menu": ["menu", "receta", "escandallo"],
        "evento": ["evento", "boda"],
        "produccion": ["produccion", "elaboracion"],
        "stock": ["stock", "inventario"],
    }
    for idx, accion in enumerate(acciones):
        nombre = normalizar_5412(str(accion.get("nombre") or ""))
        codigo = normalizar_5412(str(accion.get("codigo") or ""))
        if codigo and codigo in t:
            return {"indice": idx, "accion": accion}
        palabras = [p for p in nombre.split() if len(p) >= 4]
        if any(p in t for p in palabras):
            return {"indice": idx, "accion": accion}
        for clave, variantes in equivalencias.items():
            if clave in nombre and any(v in t for v in variantes):
                return {"indice": idx, "accion": accion}
    return None


def interpretar_confirmacion_contextual_5412(texto: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
    t = normalizar_5412(texto)
    acciones = list(((contexto.get("confirmaciones") or {}).get("acciones_con_confirmacion") or []))
    estado = str(contexto.get("estado_conversacion") or "")

    if not t:
        return {"gestionado": False, "tipo": "vacio"}

    if t in {"volver", "vuelve", "vuelve atras", "atras"}:
        return {"gestionado": True, "tipo": "volver_seleccion"}
    if t in {"no", "cancelar", "cancela", "dejalo", "para"}:
        if estado == "esperando_confirmacion_especifica":
            return {"gestionado": True, "tipo": "rechazar_accion", "accion": contexto.get("accion_seleccionada")}
        return {"gestionado": True, "tipo": "cancelar_flujo"}
    if "cancela" in t or "cancelar" in t:
        encontrada = _buscar_accion(t, acciones)
        if encontrada:
            return {"gestionado": True, "tipo": "cancelar_accion", **encontrada}
    if any(frase in t for frase in ["aplica solo", "confirma solo", "haz solo", "solo compra", "solo menu", "solo evento"]):
        encontrada = _buscar_accion(t, acciones)
        if encontrada:
            return {"gestionado": True, "tipo": "seleccionar_y_confirmar", **encontrada}
    if estado == "esperando_confirmacion_especifica" and t in {"si", "s", "vale", "ok", "adelante", "continua", "continuar", "confirmo", "confirmar", "hazlo", "aplica"}:
        return {"gestionado": True, "tipo": "confirmar_accion", "accion": contexto.get("accion_seleccionada")}
    if t in {"seleccionar", "elige", "por partes", "una por una"}:
        return {"gestionado": True, "tipo": "abrir_seleccion"}
    if t in {"si", "s", "vale", "ok", "adelante", "continua", "continuar", "hazlo", "aplica todo", "confirmar todo"}:
        return {"gestionado": True, "tipo": "confirmar_flujo"}

    encontrada = _buscar_accion(t, acciones)
    if encontrada and any(v in t for v in ["confirma", "aplica", "haz", "selecciona"]):
        return {"gestionado": True, "tipo": "seleccionar_accion", **encontrada}
    return {"gestionado": False, "tipo": "desconocido"}


def registrar_confirmacion_accion_5412(contexto: Dict[str, Any], accion: Dict[str, Any], confirmada: bool) -> Dict[str, Any]:
    codigo = str(accion.get("codigo") or accion.get("nombre") or "accion")
    registro = dict(contexto.get("confirmaciones_especificas") or {})
    registro[codigo] = {
        "nombre": accion.get("nombre"),
        "confirmada": bool(confirmada),
        "modifico_datos_reales": False,
    }
    return registro


def mensaje_confirmacion_especifica_5412(accion: Dict[str, Any]) -> str:
    return "\n".join([
        "He seleccionado la acción correcta dentro del evento activo.",
        "",
        f"ACCIÓN: {accion.get('nombre')}",
        "Esta acción puede modificar datos reales.",
        "¿Confirmas que quieres dejarla autorizada? Responde 'sí', 'no' o 'volver atrás'.",
    ])


__all__ = [
    "interpretar_confirmacion_contextual_5412",
    "registrar_confirmacion_accion_5412",
    "mensaje_confirmacion_especifica_5412",
    "normalizar_5412",
]
