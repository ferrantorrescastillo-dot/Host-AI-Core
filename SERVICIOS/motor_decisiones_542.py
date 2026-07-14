"""Host AI 5.4.2 - Motor de Toma de Decisiones.

Recibe el analisis 5.4.1 y propone que haria un segundo jefe de cocina.
No aplica cambios reales. Ordena decisiones, acciones seguras y confirmaciones.
"""
from __future__ import annotations

from typing import Any, Dict, List

from SERVICIOS.analizador_situacion_541 import analizar_situacion_operativa_541

PESO_RIESGO = {"critico": 0, "alto": 1, "medio": 2, "bajo": 3}


def _decision(codigo: str, prioridad: int, titulo: str, accion: str, motivo: str, requiere_confirmacion: bool = False, origen: str = "motor_542") -> Dict[str, Any]:
    return {
        "codigo": codigo,
        "prioridad": prioridad,
        "titulo": titulo,
        "accion": accion,
        "motivo": motivo,
        "requiere_confirmacion": requiere_confirmacion,
        "origen": origen,
    }


def _decisiones_por_componentes(analisis: Dict[str, Any]) -> List[Dict[str, Any]]:
    comp = analisis.get("componentes", {}) or {}
    decisiones: List[Dict[str, Any]] = []
    stock = comp.get("stock", {})
    if stock.get("estado") == "faltante":
        decisiones.append(_decision("DEC_COMPRAS_URGENTES", 1, "Resolver faltantes de stock", "Preparar compra urgente o validar sustitucion antes de cerrar el evento.", "Sin genero suficiente, produccion y servicio quedan en riesgo.", True))
    elif stock.get("estado") == "pendiente_consulta":
        decisiones.append(_decision("DEC_CONSULTAR_STOCK", 4, "Consultar stock real", "Revisar inventario activo antes de generar pedidos.", "No conviene comprar ni prometer produccion sin stock real.", False))

    personal = comp.get("personal", {})
    if personal.get("estado") == "insuficiente":
        decisiones.append(_decision("DEC_REFUERZO_PERSONAL", 2, "Cubrir falta de personal", "Pedir refuerzo, adelantar produccion o reducir carga del dia.", "Con menos cocineros de los necesarios aumenta el riesgo de retraso.", True))
    elif personal.get("estado") == "pendiente":
        decisiones.append(_decision("DEC_VALIDAR_PERSONAL", 5, "Validar equipo disponible", "Confirmar cuantos cocineros trabajan antes de cerrar el planning.", "El planning real depende del equipo disponible.", False))

    recursos = comp.get("recursos", {})
    if recursos.get("estado") == "conflicto":
        decisiones.append(_decision("DEC_REASIGNAR_RECURSOS", 3, "Resolver recursos ocupados", "Mover tareas dependientes o reservar recurso alternativo.", "Un recurso bloqueado puede parar una elaboracion critica.", True))
    elif recursos.get("estado") == "pendiente":
        decisiones.append(_decision("DEC_REVISAR_RECURSOS", 6, "Revisar recursos de cocina", "Comprobar horno, abatidor, camaras y fuegos antes de confirmar produccion.", "Los recursos condicionan el orden real de trabajo.", False))

    proveedores = comp.get("proveedores", {})
    if proveedores.get("estado") == "riesgo_reparto":
        decisiones.append(_decision("DEC_PROVEEDOR_ALTERNATIVO", 1, "Buscar proveedor alternativo", "No generar pedido definitivo hasta tener proveedor viable.", "Si el proveedor falla, la compra urgente no sirve.", True))
    elif proveedores.get("estado") == "pendiente":
        decisiones.append(_decision("DEC_VALIDAR_PROVEEDORES", 7, "Validar proveedores", "Comprobar disponibilidad antes de cerrar compras.", "La compra depende de reparto y horarios reales.", False))
    return decisiones


def _decisiones_desde_replanificacion(analisis: Dict[str, Any]) -> List[Dict[str, Any]]:
    decisiones: List[Dict[str, Any]] = []
    replan = analisis.get("replanificacion_base", {}) or {}
    for tarea in (replan.get("nuevo_planning") or [])[:6]:
        codigo = str(tarea.get("codigo") or "REPLAN").upper()
        decisiones.append(_decision(
            f"DEC_{codigo}",
            8 + int(tarea.get("orden", 99)),
            tarea.get("nombre") or "Tarea del nuevo planning",
            tarea.get("accion") or "Mantener tarea propuesta por replanificacion.",
            tarea.get("detalle") or "Viene del cierre operativo 5.3.9.",
            bool(tarea.get("requiere_confirmacion")),
            "replanificador_538",
        ))
    return decisiones


def tomar_decisiones_operativas_542(datos_evento: Dict[str, Any] | None = None, contexto: Dict[str, Any] | None = None, analisis: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Propone decisiones ejecutivas a partir del analisis de situacion.

    Puede recibir un analisis 5.4.1 ya calculado o generarlo desde evento +
    contexto. La salida no se aplica automaticamente.
    """
    contexto = contexto or {}
    if analisis is None:
        analisis = analizar_situacion_operativa_541(datos_evento or {}, contexto)
    if not analisis.get("ok"):
        return {
            "ok": False,
            "version": "5.4.2",
            "estado": "sin_decision",
            "mensaje": "No puedo tomar decisiones porque el analisis de situacion no es valido.",
            "decisiones": [],
            "requiere_confirmacion": True,
            "aplicado": False,
        }

    decisiones = []
    decisiones.extend(_decisiones_por_componentes(analisis))
    decisiones.extend(_decisiones_desde_replanificacion(analisis))

    if not decisiones:
        decisiones.append(_decision("DEC_CONTINUAR_FLUJO", 10, "Continuar flujo completo", "Ejecutar produccion, stock, compras y rentabilidad en modo seguro.", "No hay incidencias relevantes que obliguen a cambiar el plan.", False))

    # deduplicar por codigo manteniendo la primera decision de mayor prioridad
    vistos = set()
    limpias = []
    for d in sorted(decisiones, key=lambda x: (x.get("prioridad", 99), x.get("codigo", ""))):
        if d["codigo"] in vistos:
            continue
        vistos.add(d["codigo"])
        d["orden"] = len(limpias) + 1
        limpias.append(d)

    requiere = any(d.get("requiere_confirmacion") for d in limpias)
    riesgo = analisis.get("riesgo_general", "medio")
    estado = "decision_propuesta"
    if riesgo == "critico":
        estado = "decision_bloqueante"
    elif not requiere:
        estado = "decision_segura"

    return {
        "ok": True,
        "version": "5.4.2",
        "estado": estado,
        "riesgo_general": riesgo,
        "decisiones": limpias,
        "primera_decision": limpias[0] if limpias else None,
        "requiere_confirmacion": requiere,
        "aplicado": False,
        "mensaje": "Decisiones operativas propuestas. No se ha aplicado ningun cambio real.",
        "lectura_jefe_cocina": _lectura_jefe_cocina(riesgo, requiere),
        "analisis": analisis,
    }


def _lectura_jefe_cocina(riesgo: str, requiere: bool) -> str:
    if riesgo == "critico":
        return "Primero resolveria lo que puede romper el servicio; no confirmaria produccion ni compras definitivas todavia."
    if requiere:
        return "El plan es viable, pero antes de aplicar cambios reales pediria confirmacion del jefe de cocina."
    return "La situacion permite avanzar en modo seguro con el flujo operativo normal."


def formatear_decisiones_542(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = ["HOST AI 5.4.2 - MOTOR DE TOMA DE DECISIONES", "-" * 60]
    lineas.append(f"Estado: {resultado.get('estado')} | Riesgo: {resultado.get('riesgo_general')}")
    lineas.append(f"Confirmacion necesaria: {resultado.get('requiere_confirmacion')}")
    lineas.append("")
    lineas.append("LECTURA DE SEGUNDO JEFE")
    lineas.append(f"- {resultado.get('lectura_jefe_cocina')}")
    lineas.append("")
    lineas.append("DECISIONES PROPUESTAS")
    for d in resultado.get("decisiones", []):
        marca = "CONFIRMAR" if d.get("requiere_confirmacion") else "SEGURO"
        lineas.append(f"{d.get('orden')}. [{marca}] {d.get('titulo')}")
        lineas.append(f"   Accion: {d.get('accion')}")
        lineas.append(f"   Motivo: {d.get('motivo')}")
    return "\n".join(lineas)


__all__ = ["tomar_decisiones_operativas_542", "formatear_decisiones_542"]
