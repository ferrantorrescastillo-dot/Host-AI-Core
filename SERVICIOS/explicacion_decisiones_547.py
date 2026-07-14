"""Host AI 5.4.7 - Explicacion Inteligente de Decisiones.

Convierte decisiones operativas en explicaciones profesionales de cocina:
que se decide, por que, que riesgo evita, que impacto tiene y que requiere
confirmacion. No ejecuta cambios reales.
"""
from __future__ import annotations

from typing import Any, Dict, List

try:
    from SERVICIOS.motor_decisiones_542 import tomar_decisiones_operativas_542
except ModuleNotFoundError:
    tomar_decisiones_operativas_542 = None  # type: ignore

try:
    from SERVICIOS.evaluador_alternativas_543 import evaluar_alternativas_543
except ModuleNotFoundError:
    evaluar_alternativas_543 = None  # type: ignore

try:
    from SERVICIOS.optimizador_global_545 import optimizar_operacion_545
except ModuleNotFoundError:
    optimizar_operacion_545 = None  # type: ignore


def explicar_decisiones_547(contexto: Dict[str, Any] | None = None, decisiones: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Genera explicaciones claras para las decisiones propuestas por Host AI."""
    contexto = contexto or _contexto_demo()
    decisiones = decisiones or _obtener_decisiones(contexto)

    explicaciones: List[Dict[str, Any]] = []
    for idx, decision in enumerate(decisiones, start=1):
        accion = str(decision.get("accion") or decision.get("decision") or decision.get("tarea") or "Revisar operativa")
        area = str(decision.get("area") or decision.get("tipo") or _inferir_area(accion))
        prioridad = str(decision.get("prioridad") or decision.get("gravedad") or "media").lower()
        razon = str(decision.get("razon") or decision.get("motivo") or _razon_por_area(area, contexto))
        impacto = _impacto(area, prioridad, contexto)
        riesgo_evitado = _riesgo_evitado(area, contexto)
        confirma = bool(decision.get("requiere_confirmacion", _requiere_confirmacion(area, accion)))
        explicaciones.append({
            "orden": idx,
            "area": area,
            "prioridad": prioridad,
            "accion": accion,
            "por_que": razon,
            "impacto_operativo": impacto,
            "riesgo_evitado": riesgo_evitado,
            "requiere_confirmacion": confirma,
            "frase_jefe_cocina": _frase_jefe(accion, razon, impacto, confirma),
        })

    criticas = [e for e in explicaciones if e["prioridad"] in ("critica", "crítica", "alta")]
    return {
        "ok": True,
        "version": "5.4.7",
        "estado": "explicacion_decisiones_generada",
        "decisiones_explicadas": len(explicaciones),
        "decisiones_criticas_o_altas": len(criticas),
        "explicaciones": explicaciones,
        "resumen_ejecutivo": _resumen(explicaciones),
        "aplicado": False,
        "requiere_confirmacion": any(e["requiere_confirmacion"] for e in explicaciones),
        "mensaje": "Explicacion generada en modo seguro. No se han aplicado cambios reales.",
    }


def _obtener_decisiones(contexto: Dict[str, Any]) -> List[Dict[str, Any]]:
    if tomar_decisiones_operativas_542:
        try:
            resultado = tomar_decisiones_operativas_542(contexto)
            decisiones = resultado.get("decisiones") or resultado.get("acciones") or resultado.get("plan")
            if isinstance(decisiones, list) and decisiones:
                return [d if isinstance(d, dict) else {"accion": str(d)} for d in decisiones]
        except Exception:
            pass
    return [
        {"area": "eventos", "prioridad": "alta", "accion": "Confirmar evento y bloquear capacidad de cocina", "razon": "Hay una boda de alto volumen y conviene asegurar recursos antes de producir.", "requiere_confirmacion": True},
        {"area": "stock", "prioridad": "alta", "accion": "Revisar arroz bomba, caldo y proteina principal", "razon": "Son ingredientes criticos para una paella de 180 personas.", "requiere_confirmacion": False},
        {"area": "compras", "prioridad": "media", "accion": "Preparar pedido preliminar segun stock real", "razon": "Evita comprar de mas y reduce riesgo de rotura.", "requiere_confirmacion": True},
        {"area": "produccion", "prioridad": "media", "accion": "Adelantar mise en place y fondos al dia anterior", "razon": "Reduce presion el dia del servicio.", "requiere_confirmacion": False},
    ]


def _inferir_area(texto: str) -> str:
    t = texto.lower()
    if any(p in t for p in ("stock", "arroz", "caldo", "inventario")):
        return "stock"
    if any(p in t for p in ("compra", "pedido", "proveedor")):
        return "compras"
    if any(p in t for p in ("produccion", "mise", "elaboracion")):
        return "produccion"
    if any(p in t for p in ("personal", "cocinero", "turno")):
        return "personal"
    if any(p in t for p in ("evento", "boda", "servicio")):
        return "eventos"
    return "operativa"


def _razon_por_area(area: str, contexto: Dict[str, Any]) -> str:
    personas = contexto.get("personas") or contexto.get("comensales") or "alto volumen"
    razones = {
        "eventos": f"El evento condiciona toda la operativa y debe quedar confirmado antes de mover compras o produccion.",
        "stock": f"Con {personas} personas, una rotura de stock puede comprometer el servicio.",
        "compras": "Las compras deben salir despues de revisar stock real para evitar errores de coste y cantidad.",
        "produccion": "La produccion anticipada baja el riesgo de retrasos el dia del evento.",
        "personal": "La carga de trabajo debe cuadrar con las horas reales del equipo.",
        "recursos": "Los recursos criticos deben reservarse antes de cerrar el planning.",
    }
    return razones.get(area, "Es una accion necesaria para mantener el flujo operativo bajo control.")


def _impacto(area: str, prioridad: str, contexto: Dict[str, Any]) -> str:
    if area == "stock":
        return "Evita parar produccion por falta de ingredientes criticos."
    if area == "compras":
        return "Reduce sobrecostes y asegura que el pedido llegue a tiempo."
    if area == "produccion":
        return "Reparte carga de trabajo y protege la hora de servicio."
    if area == "personal":
        return "Evita llegar al servicio con horas insuficientes o tareas sin responsable."
    if area == "eventos":
        return "Asegura que el evento queda bloqueado antes de comprometer recursos."
    return "Mejora el control operativo general."


def _riesgo_evitado(area: str, contexto: Dict[str, Any]) -> str:
    mapa = {
        "stock": "rotura de stock",
        "compras": "pedido incompleto o proveedor tarde",
        "produccion": "retraso de produccion",
        "personal": "falta de personal",
        "eventos": "evento mal definido",
        "recursos": "conflicto de recursos",
    }
    return mapa.get(area, "perdida de control operativo")


def _requiere_confirmacion(area: str, accion: str) -> bool:
    texto = accion.lower()
    return area in ("compras", "eventos") or any(p in texto for p in ("crear", "aplicar", "pedido", "confirmar", "modificar"))


def _frase_jefe(accion: str, razon: str, impacto: str, confirma: bool) -> str:
    cierre = "Antes de aplicarlo, pediria confirmacion." if confirma else "Esto se puede preparar en modo seguro."
    return f"Haria esto: {accion}. Motivo: {razon} Impacto: {impacto} {cierre}"


def _resumen(explicaciones: List[Dict[str, Any]]) -> str:
    if not explicaciones:
        return "No hay decisiones que explicar."
    primera = explicaciones[0]
    pendientes = sum(1 for e in explicaciones if e.get("requiere_confirmacion"))
    return f"Primero actuaria sobre {primera.get('area')}: {primera.get('accion')}. Hay {pendientes} decision(es) que requieren confirmacion antes de modificar datos reales."


def _contexto_demo() -> Dict[str, Any]:
    return {"tipo_evento": "boda", "personas": 180, "menu": "paella", "fecha": "sabado", "hora_servicio": "15:00"}


def formatear_explicacion_547(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = ["HOST AI 5.4.7 - EXPLICACION INTELIGENTE DE DECISIONES", "-" * 70]
    lineas.append(f"Estado: {resultado.get('estado')}")
    lineas.append(f"Decisiones explicadas: {resultado.get('decisiones_explicadas')}")
    lineas.append(f"Requiere confirmacion: {resultado.get('requiere_confirmacion')}")
    lineas.append("")
    lineas.append("RESUMEN EJECUTIVO")
    lineas.append(f"- {resultado.get('resumen_ejecutivo')}")
    lineas.append("")
    lineas.append("DECISIONES")
    for e in resultado.get("explicaciones", []):
        lineas.append(f"{e.get('orden')}. [{e.get('prioridad')}] {e.get('area')} -> {e.get('accion')}")
        lineas.append(f"   Por que: {e.get('por_que')}")
        lineas.append(f"   Impacto: {e.get('impacto_operativo')}")
        lineas.append(f"   Riesgo evitado: {e.get('riesgo_evitado')}")
        lineas.append(f"   Confirmacion: {e.get('requiere_confirmacion')}")
    return "\n".join(lineas)


__all__ = ["explicar_decisiones_547", "formatear_explicacion_547"]
