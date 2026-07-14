"""Host AI 5.3.4 - Confirmación inteligente de acciones.

Clasifica qué acciones del flujo se pueden ejecutar de forma segura, cuáles
requieren confirmación y cómo interpretar respuestas naturales del usuario.
"""
from __future__ import annotations

import unicodedata
from typing import Any, Dict, List


AFIRMATIVOS = {
    "s", "si", "sí", "ok", "vale", "adelante", "confirmar", "confirma",
    "hazlo", "ejecuta", "ejecutar", "todo", "si todo", "sí todo",
}
NEGATIVOS = {"n", "no", "cancelar", "cancela", "para", "parar", "de momento no"}
SELECCION = {"seleccionar", "elige", "por partes", "solo", "solo algunas", "una parte"}


def _normalizar(texto: str) -> str:
    t = (texto or "").strip().lower()
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    import re
    t = re.sub(r"[^a-z0-9ñçáéíóúàèòü ]+", " ", t)
    return " ".join(t.split())


def interpretar_confirmacion(texto: str) -> Dict[str, Any]:
    t = _normalizar(texto)
    if not t:
        return {"tipo": "vacio", "confirmado": False, "mensaje": "Respuesta vacía."}
    if t in AFIRMATIVOS or any(t.startswith(p + " ") for p in ["si", "vale", "ok", "adelante", "hazlo", "ejecuta"]):
        return {"tipo": "confirmar_todo", "confirmado": True, "mensaje": "Confirmación afirmativa detectada."}
    if t in NEGATIVOS:
        return {"tipo": "cancelar", "confirmado": False, "mensaje": "Cancelación detectada."}
    if t in SELECCION or "solo" in t or "por partes" in t:
        return {"tipo": "seleccionar", "confirmado": False, "mensaje": "El usuario quiere seleccionar acciones concretas."}
    return {"tipo": "desconocido", "confirmado": False, "mensaje": "No he entendido la confirmación."}


def analizar_confirmaciones_flujo(flujo: Dict[str, Any], ejecucion: Dict[str, Any] | None = None) -> Dict[str, Any]:
    pasos = list(flujo.get("pasos") or [])
    acciones_seguras: List[Dict[str, Any]] = []
    acciones_con_confirmacion: List[Dict[str, Any]] = []
    acciones_criticas: List[Dict[str, Any]] = []

    for paso in pasos:
        requiere = bool(paso.get("requiere_confirmacion"))
        modifica = bool(paso.get("modifica_datos"))
        item = {
            "codigo": paso.get("codigo"),
            "nombre": paso.get("nombre"),
            "modulo": paso.get("modulo"),
            "accion": paso.get("accion"),
            "modifica_datos": modifica,
            "requiere_confirmacion": requiere,
        }
        if requiere or modifica:
            acciones_con_confirmacion.append(item)
            if modifica:
                acciones_criticas.append(item)
        else:
            acciones_seguras.append(item)

    return {
        "ok": True,
        "estado": "confirmaciones_analizadas",
        "acciones_seguras": acciones_seguras,
        "acciones_con_confirmacion": acciones_con_confirmacion,
        "acciones_criticas": acciones_criticas,
        "requiere_confirmacion_global": bool(acciones_con_confirmacion),
        "puede_ejecutar_todo_sin_confirmar": not acciones_con_confirmacion,
        "mensaje": formatear_confirmaciones({
            "acciones_seguras": acciones_seguras,
            "acciones_con_confirmacion": acciones_con_confirmacion,
            "acciones_criticas": acciones_criticas,
        }),
    }


def formatear_confirmaciones(resultado: Dict[str, Any]) -> str:
    seguras = resultado.get("acciones_seguras", [])
    confirmar = resultado.get("acciones_con_confirmacion", [])
    criticas = resultado.get("acciones_criticas", [])

    lineas: List[str] = []
    lineas.append("CONFIRMACIÓN INTELIGENTE")
    lineas.append("-" * 60)
    lineas.append(f"Acciones seguras: {len(seguras)}")
    lineas.append(f"Acciones que requieren confirmación: {len(confirmar)}")
    lineas.append(f"Acciones críticas: {len(criticas)}")
    lineas.append("")

    if confirmar:
        lineas.append("Antes de modificar datos reales necesito confirmación para:")
        for item in confirmar:
            marca = "CRÍTICA" if item.get("modifica_datos") else "confirmar"
            lineas.append(f"- [{marca}] {item.get('nombre')}")
        lineas.append("")
        lineas.append("Puedes responder: 'sí', 'no' o 'seleccionar'.")
    else:
        lineas.append("No hay acciones críticas pendientes.")
    return "\n".join(lineas)


__all__ = ["analizar_confirmaciones_flujo", "interpretar_confirmacion", "formatear_confirmaciones"]
