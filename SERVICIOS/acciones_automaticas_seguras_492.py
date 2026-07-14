from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Iterable, List

ACCIONES_SEGURAS = {
    "crear_borrador_pedido",
    "crear_tarea_produccion",
    "generar_alerta",
    "crear_informe",
    "registrar_observacion",
}

ACCIONES_CON_CONFIRMACION = {
    "actualizar_stock",
    "cerrar_recepcion",
    "modificar_precio",
    "confirmar_pedido",
    "cerrar_evento",
}


@dataclass
class ResultadoAccion:
    accion: str
    estado: str
    requiere_confirmacion: bool
    mensaje: str
    fecha: str
    datos: Dict[str, Any]


def clasificar_accion(accion: str) -> Dict[str, Any]:
    accion_norm = str(accion).strip().lower()
    if accion_norm in ACCIONES_SEGURAS:
        return {"accion": accion_norm, "permitida": True, "requiere_confirmacion": False, "tipo": "segura"}
    if accion_norm in ACCIONES_CON_CONFIRMACION:
        return {"accion": accion_norm, "permitida": True, "requiere_confirmacion": True, "tipo": "confirmacion"}
    return {"accion": accion_norm, "permitida": False, "requiere_confirmacion": True, "tipo": "no_registrada"}


def preparar_accion_segura(accion: str, datos: Dict[str, Any] | None = None, confirmado: bool = False) -> Dict[str, Any]:
    datos = datos or {}
    clasificacion = clasificar_accion(accion)
    estado = "bloqueada"
    mensaje = f"Acción no permitida sin revisión: {clasificacion['accion']}"

    if clasificacion["permitida"] and not clasificacion["requiere_confirmacion"]:
        estado = "lista_para_ejecutar"
        mensaje = f"Acción segura preparada: {clasificacion['accion']}"
    elif clasificacion["permitida"] and clasificacion["requiere_confirmacion"] and confirmado:
        estado = "confirmada"
        mensaje = f"Acción confirmada por usuario: {clasificacion['accion']}"
    elif clasificacion["permitida"] and clasificacion["requiere_confirmacion"]:
        estado = "pendiente_confirmacion"
        mensaje = f"La acción requiere confirmación: {clasificacion['accion']}"

    resultado = ResultadoAccion(
        accion=clasificacion["accion"],
        estado=estado,
        requiere_confirmacion=bool(clasificacion["requiere_confirmacion"]),
        mensaje=mensaje,
        fecha=datetime.now().isoformat(timespec="seconds"),
        datos=datos,
    )
    return asdict(resultado)


def preparar_lote_acciones(acciones: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    resultados: List[Dict[str, Any]] = [preparar_accion_segura(a.get("accion", ""), a.get("datos", {}), bool(a.get("confirmado", False))) for a in acciones]
    return {
        "total": len(resultados),
        "listas": [r for r in resultados if r["estado"] in {"lista_para_ejecutar", "confirmada"}],
        "pendientes_confirmacion": [r for r in resultados if r["estado"] == "pendiente_confirmacion"],
        "bloqueadas": [r for r in resultados if r["estado"] == "bloqueada"],
        "acciones": resultados,
    }
