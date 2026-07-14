from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional


def _normalizar(texto: str) -> str:
    t = (texto or "").strip().lower()
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def acciones_seleccionables(contexto: Dict[str, Any]) -> List[Dict[str, Any]]:
    confirmaciones = contexto.get("confirmaciones") or {}
    return list(confirmaciones.get("acciones_con_confirmacion") or [])


def interpretar_seleccion(texto: str, acciones: List[Dict[str, Any]]) -> Dict[str, Any]:
    t = _normalizar(texto)
    if not t:
        return {"ok": False, "tipo": "vacio"}
    if t in {"no", "cancelar", "cancela", "volver"}:
        return {"ok": True, "tipo": "cancelar_seleccion"}
    m = re.search(r"\b(\d+)\b", t)
    if m:
        indice = int(m.group(1)) - 1
        if 0 <= indice < len(acciones):
            return {"ok": True, "tipo": "accion", "indice": indice, "accion": acciones[indice]}
        return {"ok": False, "tipo": "fuera_rango"}
    for indice, accion in enumerate(acciones):
        nombre = _normalizar(str(accion.get("nombre") or ""))
        codigo = _normalizar(str(accion.get("codigo") or ""))
        palabras = [p for p in nombre.split() if len(p) > 3]
        if (codigo and codigo in t) or any(p in t for p in palabras):
            return {"ok": True, "tipo": "accion", "indice": indice, "accion": accion}
    return {"ok": False, "tipo": "no_entendida"}


def ejecutar_accion_seleccionada_modo_seguro(accion: Dict[str, Any], contexto: Dict[str, Any]) -> Dict[str, Any]:
    """Continúa el flujo sin escribir datos reales.

    La conexión destructiva con cada motor queda protegida hasta disponer de
    confirmación específica y datos reales verificados.
    """
    nombre = accion.get("nombre") or accion.get("accion") or "Acción"
    modifica = bool(accion.get("modifica_datos"))
    if modifica:
        estado = "protegida_pendiente_confirmacion_especifica"
        detalle = f"{nombre}: seleccionada, pero todavía protegida porque modifica datos reales."
    else:
        estado = "preparada_modo_seguro"
        detalle = f"{nombre}: preparada en modo seguro; no se han modificado datos reales."
    return {"ok": True, "estado": estado, "accion": accion, "detalle": detalle, "modifico_datos_reales": False}


def formatear_resultado_seleccion(resultado: Dict[str, Any], evento: Dict[str, Any]) -> str:
    accion = resultado.get("accion") or {}
    lineas = [
        "Perfecto. Continúo exactamente desde el flujo activo.",
        "",
        "ACCIÓN SELECCIONADA",
        f"- {accion.get('nombre')}",
        f"- Estado: {resultado.get('estado')}",
        f"- Resultado: {resultado.get('detalle')}",
        "",
        "EVENTO QUE SIGUE ACTIVO",
        f"- Tipo: {evento.get('tipo')}",
        f"- Personas: {evento.get('personas')}",
        f"- Fecha: {evento.get('fecha')}",
        f"- Menú: {evento.get('menu')}",
        "",
        "No he enviado esta respuesta al clasificador general y no he modificado datos reales.",
        "Puedes escribir 'seleccionar' para elegir otra acción o 'finalizar' para cerrar el flujo.",
    ]
    return "\n".join(lineas)


__all__ = ["acciones_seleccionables", "interpretar_seleccion", "ejecutar_accion_seleccionada_modo_seguro", "formatear_resultado_seleccion"]
