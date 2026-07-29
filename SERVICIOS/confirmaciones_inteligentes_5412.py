from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List

from SERVICIOS.modelo_flujo_operativo import cancelar_flujo, registrar_confirmacion, registrar_historial, seleccionar_paso


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
    flujo = contexto.get("flujo") if isinstance(contexto, dict) else None
    if isinstance(flujo, dict):
        acciones = [
            p
            for p in list(flujo.get("pasos") or [])
            if str(p.get("estado") or "") not in {"completado", "cancelado", "rechazado", "error", "preparado_modo_seguro"}
        ]
        if not acciones:
            acciones = list(((contexto.get("confirmaciones") or {}).get("acciones_con_confirmacion") or []))
    else:
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
    afirmativas = {"si", "s", "vale", "ok", "adelante", "continua", "continuar", "confirmo", "confirmar", "hazlo", "aplica"}
    if estado == "esperando_confirmacion_especifica" and (t in afirmativas or any(f"{a} " in f"{t} " for a in afirmativas)):
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
    flujo = contexto.get("flujo") if isinstance(contexto, dict) else None
    if isinstance(flujo, dict):
        id_o_codigo = str(accion.get("id_paso") or accion.get("codigo") or "")
        if not id_o_codigo:
            return {
                "ok": False,
                "estado": "accion_invalida",
                "mensaje": "La acción no tiene id_paso/codigo para registrar confirmación.",
                "flujo": flujo,
            }

        paso_actual = flujo.get("paso_actual")
        flujo_trabajo = flujo
        if not paso_actual:
            sel = seleccionar_paso(flujo_trabajo, id_o_codigo, origen="confirmaciones_5412")
            if sel.get("ok"):
                flujo_trabajo = dict(sel.get("flujo") or flujo_trabajo)

        if confirmada:
            reg = registrar_confirmacion(flujo_trabajo, id_o_codigo, True, origen="confirmaciones_5412", valor="si")
            return {
                "ok": bool(reg.get("ok")),
                "estado": reg.get("estado", "confirmacion_registrada"),
                "mensaje": "Confirmación registrada en flujo unificado." if reg.get("ok") else reg.get("mensaje", "No se pudo registrar confirmación."),
                "flujo": reg.get("flujo", flujo_trabajo),
                "paso": reg.get("paso"),
            }

        reg = registrar_confirmacion(flujo_trabajo, id_o_codigo, False, origen="confirmaciones_5412", valor="no")
        return {
            "ok": bool(reg.get("ok")),
            "estado": reg.get("estado", "rechazo_registrado"),
            "mensaje": "Rechazo registrado en flujo unificado." if reg.get("ok") else reg.get("mensaje", "No se pudo registrar rechazo."),
            "flujo": reg.get("flujo", flujo_trabajo),
            "paso": reg.get("paso"),
        }

    codigo = str(accion.get("codigo") or accion.get("nombre") or "accion")
    registro = dict(contexto.get("confirmaciones_especificas") or {})
    registro[codigo] = {
        "nombre": accion.get("nombre"),
        "confirmada": bool(confirmada),
        "modifico_datos_reales": False,
    }
    return registro


def aplicar_confirmacion_en_flujo_5412(texto: str, flujo: Dict[str, Any]) -> Dict[str, Any]:
    estado_ctx = str(flujo.get("estado") or "")
    if estado_ctx == "esperando_confirmacion":
        estado_ctx = "esperando_confirmacion_especifica"
    contexto = {
        "estado_conversacion": estado_ctx,
        "accion_seleccionada": dict(flujo.get("accion_seleccionada") or {}),
        "flujo": flujo,
    }
    interpretada = interpretar_confirmacion_contextual_5412(texto, contexto)
    if not interpretada.get("gestionado"):
        return {
            "ok": False,
            "estado": "confirmacion_no_entendida",
            "mensaje": "No se entendió la confirmación en el flujo activo.",
            "flujo": flujo,
            "interpretacion": interpretada,
        }

    tipo = str(interpretada.get("tipo") or "")
    if tipo in {"confirmar_accion", "seleccionar_y_confirmar"}:
        accion = interpretada.get("accion") or flujo.get("accion_seleccionada") or {}
        resultado = registrar_confirmacion_accion_5412({"flujo": flujo}, dict(accion), True)
        return {
            "ok": bool(resultado.get("ok")),
            "estado": resultado.get("estado", "confirmacion_registrada"),
            "mensaje": resultado.get("mensaje", "Confirmación registrada."),
            "flujo": resultado.get("flujo", flujo),
            "paso": resultado.get("paso"),
            "interpretacion": interpretada,
        }

    if tipo in {"rechazar_accion", "cancelar_accion"}:
        accion = interpretada.get("accion") or flujo.get("accion_seleccionada") or {}
        resultado = registrar_confirmacion_accion_5412({"flujo": flujo}, dict(accion), False)
        return {
            "ok": bool(resultado.get("ok")),
            "estado": resultado.get("estado", "rechazo_registrado"),
            "mensaje": resultado.get("mensaje", "Acción rechazada."),
            "flujo": resultado.get("flujo", flujo),
            "paso": resultado.get("paso"),
            "interpretacion": interpretada,
        }

    if tipo == "cancelar_flujo":
        cancelado = cancelar_flujo(flujo, motivo="cancelado_por_confirmacion", origen="confirmaciones_5412")
        return {
            "ok": bool(cancelado.get("ok")),
            "estado": cancelado.get("estado", "flujo_cancelado"),
            "mensaje": "Flujo cancelado por el usuario.",
            "flujo": cancelado.get("flujo", flujo),
            "interpretacion": interpretada,
        }

    if tipo in {"abrir_seleccion", "volver_seleccion"}:
        nuevo = dict(flujo)
        nuevo["estado"] = "esperando_seleccion"
        nuevo = registrar_historial(nuevo, "volver_seleccion", {"origen": "confirmaciones_5412"})
        return {
            "ok": True,
            "estado": "esperando_seleccion",
            "mensaje": "Se abrió selección de acciones del flujo.",
            "flujo": nuevo,
            "interpretacion": interpretada,
        }

    if tipo == "confirmar_flujo":
        return {
            "ok": True,
            "estado": "confirmar_flujo",
            "mensaje": "Confirmación global detectada. Debes seleccionar paso o ejecutar según política.",
            "flujo": flujo,
            "interpretacion": interpretada,
        }

    if tipo == "volver_atras":
        return {
            "ok": False,
            "estado": "volver_atras_no_implementado",
            "mensaje": "Volver atrás no está implementado de forma segura sin rollback explícito.",
            "flujo": flujo,
            "interpretacion": interpretada,
        }

    return {
        "ok": False,
        "estado": "confirmacion_no_aplicable",
        "mensaje": "La confirmación no aplica al flujo actual.",
        "flujo": flujo,
        "interpretacion": interpretada,
    }


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
    "aplicar_confirmacion_en_flujo_5412",
    "mensaje_confirmacion_especifica_5412",
    "normalizar_5412",
]
