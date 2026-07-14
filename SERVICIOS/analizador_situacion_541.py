"""Host AI 5.4.1 - Analizador Inteligente de Situacion.

Primer sprint del Motor de Decisiones Autonomas. No ejecuta acciones ni modifica
datos: lee el contexto operativo disponible, reutiliza el cierre 5.3.9 y genera
un estado de cocina claro para que Host AI decida como un segundo jefe de cocina.
"""
from __future__ import annotations

from typing import Any, Dict, List

from SERVICIOS.integracion_operativa_539 import cerrar_inteligencia_operativa_539

NIVELES = {"critico": 4, "alto": 3, "medio": 2, "bajo": 1}


def _lista(valor: Any) -> List[Any]:
    if valor is None:
        return []
    if isinstance(valor, list):
        return valor
    if isinstance(valor, tuple):
        return list(valor)
    return [valor]


def _num(valor: Any, defecto: float = 0.0) -> float:
    try:
        if valor in (None, ""):
            return defecto
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def _estado_stock(contexto: Dict[str, Any]) -> Dict[str, Any]:
    stock = _lista(contexto.get("stock") or contexto.get("stock_actual"))
    faltantes = _lista(contexto.get("faltantes_stock") or contexto.get("faltantes"))
    articulos_bajos = []
    articulos_faltantes = []
    for item in stock:
        if not isinstance(item, dict):
            continue
        nombre = item.get("nombre") or item.get("articulo") or item.get("codigo") or "artículo"
        disponible = _num(item.get("disponible", item.get("stock", item.get("cantidad"))))
        necesario = _num(item.get("necesario", item.get("requerido", item.get("cantidad_necesaria"))))
        minimo = _num(item.get("minimo", item.get("stock_minimo")))
        if necesario and disponible < necesario:
            articulos_faltantes.append(nombre)
        elif minimo and disponible < minimo:
            articulos_bajos.append(nombre)
    for item in faltantes:
        if isinstance(item, dict):
            articulos_faltantes.append(item.get("nombre") or item.get("articulo") or "artículo")
        else:
            articulos_faltantes.append(str(item))
    if articulos_faltantes:
        estado, riesgo = "faltante", "critico"
    elif articulos_bajos:
        estado, riesgo = "stock_bajo", "medio"
    elif stock:
        estado, riesgo = "controlado", "bajo"
    else:
        estado, riesgo = "pendiente_consulta", "medio"
    return {"estado": estado, "riesgo": riesgo, "faltantes": articulos_faltantes, "bajos": articulos_bajos, "total_articulos_revisados": len(stock)}


def _estado_personal(contexto: Dict[str, Any]) -> Dict[str, Any]:
    personal = contexto.get("personal") or {}
    disponibles = _num(personal.get("disponibles", personal.get("cocineros_disponibles", personal.get("actual")))) if isinstance(personal, dict) else 0
    necesarios = _num(personal.get("necesarios", personal.get("cocineros_necesarios", personal.get("requeridos")))) if isinstance(personal, dict) else 0
    if necesarios and disponibles < necesarios:
        return {"estado": "insuficiente", "riesgo": "alto" if disponibles else "critico", "disponibles": disponibles, "necesarios": necesarios}
    if disponibles:
        return {"estado": "controlado", "riesgo": "bajo", "disponibles": disponibles, "necesarios": necesarios}
    return {"estado": "pendiente", "riesgo": "medio", "disponibles": disponibles, "necesarios": necesarios}


def _estado_recursos(contexto: Dict[str, Any]) -> Dict[str, Any]:
    recursos = _lista(contexto.get("recursos") or contexto.get("recursos_cocina"))
    ocupados = []
    for r in recursos:
        if not isinstance(r, dict):
            continue
        estado = str(r.get("estado") or r.get("situacion") or "").lower()
        if r.get("ocupado") or r.get("conflicto") or estado in {"ocupado", "averiado", "bloqueado", "no disponible"}:
            ocupados.append(r.get("nombre") or r.get("recurso") or "recurso")
    if ocupados:
        return {"estado": "conflicto", "riesgo": "alto", "ocupados": ocupados, "total": len(recursos)}
    if recursos:
        return {"estado": "controlado", "riesgo": "bajo", "ocupados": [], "total": len(recursos)}
    return {"estado": "pendiente", "riesgo": "medio", "ocupados": [], "total": 0}


def _estado_proveedores(contexto: Dict[str, Any]) -> Dict[str, Any]:
    proveedores = _lista(contexto.get("proveedores") or contexto.get("proveedores_estado"))
    no_disponibles = []
    for p in proveedores:
        if not isinstance(p, dict):
            continue
        estado = str(p.get("estado") or "").lower()
        if p.get("disponible") is False or estado in {"cerrado", "no disponible", "sin reparto", "bloqueado"}:
            no_disponibles.append(p.get("nombre") or p.get("proveedor") or "proveedor")
    if no_disponibles:
        return {"estado": "riesgo_reparto", "riesgo": "alto", "no_disponibles": no_disponibles, "total": len(proveedores)}
    if proveedores:
        return {"estado": "controlado", "riesgo": "bajo", "no_disponibles": [], "total": len(proveedores)}
    return {"estado": "pendiente", "riesgo": "medio", "no_disponibles": [], "total": 0}


def _riesgo_general(componentes: Dict[str, Dict[str, Any]], cierre: Dict[str, Any]) -> str:
    maximo = 1
    for comp in componentes.values():
        maximo = max(maximo, NIVELES.get(comp.get("riesgo", "bajo"), 1))
    resumen = cierre.get("resumen_incidencias", {}) or {}
    if resumen.get("critico", 0):
        maximo = max(maximo, 4)
    elif resumen.get("alto", 0):
        maximo = max(maximo, 3)
    return {4: "critico", 3: "alto", 2: "medio", 1: "bajo"}.get(maximo, "medio")


def analizar_situacion_operativa_541(datos_evento: Dict[str, Any], contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Construye el estado de cocina previo a decidir.

    Reutiliza 5.3.9 para no duplicar flujo, planning, incidencias ni
    replanificacion. Su salida es una lectura ejecutiva apta para el 5.4.2.
    """
    contexto = contexto or {}
    cierre = cerrar_inteligencia_operativa_539(datos_evento, contexto=contexto, confirmar_ejecucion=False)
    componentes = {
        "stock": _estado_stock(contexto),
        "personal": _estado_personal(contexto),
        "recursos": _estado_recursos(contexto),
        "proveedores": _estado_proveedores(contexto),
    }
    riesgo = _riesgo_general(componentes, cierre)
    datos = cierre.get("datos_evento", datos_evento) or {}
    estado = "cocina_controlada" if riesgo in {"bajo", "medio"} else "requiere_intervencion"
    if riesgo == "critico":
        estado = "servicio_en_riesgo"
    return {
        "ok": bool(cierre.get("ok")),
        "version": "5.4.1",
        "estado": estado,
        "riesgo_general": riesgo,
        "datos_evento": datos,
        "componentes": componentes,
        "incidencias": cierre.get("incidencias", {}),
        "resumen_incidencias": cierre.get("resumen_incidencias", {}),
        "planning_base": cierre.get("planificacion", {}),
        "replanificacion_base": cierre.get("replanificacion", {}),
        "requiere_confirmacion": bool(cierre.get("requiere_confirmacion")),
        "diagnostico": _diagnostico(componentes, riesgo),
        "mensaje": "Situacion operativa analizada. No se han modificado datos reales.",
    }


def _diagnostico(componentes: Dict[str, Dict[str, Any]], riesgo: str) -> str:
    if riesgo == "critico":
        return "No confirmaria el servicio hasta resolver primero las incidencias criticas."
    if riesgo == "alto":
        return "El servicio es trabajable, pero exige decision del jefe de cocina antes de aplicar cambios."
    if riesgo == "medio":
        return "La operativa es viable, pendiente de validar datos reales incompletos."
    return "La operativa esta controlada; se puede pasar a decisiones y confirmaciones."


def formatear_situacion_541(resultado: Dict[str, Any]) -> str:
    datos = resultado.get("datos_evento", {}) or {}
    comp = resultado.get("componentes", {}) or {}
    lineas: List[str] = ["HOST AI 5.4.1 - ANALIZADOR INTELIGENTE DE SITUACION", "-" * 60]
    lineas.append(f"Evento: {datos.get('tipo', 'evento')} | Pax: {datos.get('personas', 'pendiente')} | Fecha: {datos.get('fecha', 'pendiente')}")
    lineas.append(f"Riesgo general: {resultado.get('riesgo_general')} | Estado: {resultado.get('estado')}")
    lineas.append("")
    lineas.append("ESTADO DE COCINA")
    for nombre in ["stock", "personal", "recursos", "proveedores"]:
        c = comp.get(nombre, {})
        lineas.append(f"- {nombre.title()}: {c.get('estado')} | Riesgo: {c.get('riesgo')}")
    lineas.append("")
    lineas.append("LECTURA DE SEGUNDO JEFE")
    lineas.append(f"- {resultado.get('diagnostico')}")
    return "\n".join(lineas)


__all__ = ["analizar_situacion_operativa_541", "formatear_situacion_541"]
