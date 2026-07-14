"""Host AI 5.3.7 - Detector Inteligente de Incidencias.

Detecta riesgos operativos del flujo/planning como lo haría un segundo jefe de
cocina: primero lo que puede romper el servicio, después lo que bloquea la
producción, compras o rentabilidad. No modifica datos reales.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

NIVELES = ("critico", "alto", "medio", "bajo")
PESO_NIVEL = {"critico": 0, "alto": 1, "medio": 2, "bajo": 3}


def _lista(valor: Any) -> List[Any]:
    if valor is None:
        return []
    if isinstance(valor, list):
        return valor
    if isinstance(valor, tuple):
        return list(valor)
    return [valor]


def _normalizar_item(item: Any, nombre_por_defecto: str) -> Dict[str, Any]:
    if isinstance(item, dict):
        return dict(item)
    return {"nombre": str(item or nombre_por_defecto)}


def _cantidad(item: Dict[str, Any], *claves: str) -> float:
    for clave in claves:
        try:
            valor = item.get(clave)
            if valor is not None and valor != "":
                return float(valor)
        except (TypeError, ValueError):
            continue
    return 0.0


def _nueva_incidencia(tipo: str, nivel: str, titulo: str, detalle: str, accion: str, origen: str, bloquea: Iterable[str] | None = None) -> Dict[str, Any]:
    nivel = nivel if nivel in NIVELES else "medio"
    return {
        "tipo": tipo,
        "nivel": nivel,
        "titulo": titulo,
        "detalle": detalle,
        "accion_recomendada": accion,
        "origen": origen,
        "bloquea": list(bloquea or []),
    }


def _ordenar_incidencias(incidencias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(incidencias, key=lambda i: (PESO_NIVEL.get(i.get("nivel", "medio"), 2), i.get("tipo", ""), i.get("titulo", "")))


def _detectar_bloqueos_plan(planificacion: Dict[str, Any]) -> List[Dict[str, Any]]:
    incidencias: List[Dict[str, Any]] = []
    for paso in planificacion.get("plan", []) or []:
        bloqueos = list(paso.get("bloqueado_por") or [])
        if bloqueos:
            incidencias.append(_nueva_incidencia(
                "tarea_bloqueada",
                "alto",
                f"{paso.get('nombre') or paso.get('codigo')} está bloqueada",
                f"No conviene avanzar esta tarea hasta resolver: {', '.join(bloqueos)}.",
                "Resolver primero las dependencias y después volver a lanzar el planning.",
                "planificador_535",
                [str(paso.get("codigo"))],
            ))
    return incidencias


def _detectar_stock(contexto: Dict[str, Any]) -> List[Dict[str, Any]]:
    incidencias: List[Dict[str, Any]] = []
    for raw in _lista(contexto.get("stock") or contexto.get("stock_actual")):
        item = _normalizar_item(raw, "artículo")
        nombre = item.get("nombre") or item.get("articulo") or item.get("codigo") or "artículo"
        disponible = _cantidad(item, "disponible", "stock", "cantidad", "actual")
        necesario = _cantidad(item, "necesario", "requerido", "cantidad_necesaria")
        minimo = _cantidad(item, "minimo", "stock_minimo")
        unidad = item.get("unidad", "")
        if necesario and disponible < necesario:
            faltan = round(necesario - disponible, 3)
            nivel = "critico" if item.get("imprescindible", True) else "alto"
            incidencias.append(_nueva_incidencia(
                "falta_stock",
                nivel,
                f"Falta stock de {nombre}",
                f"Disponible: {disponible:g} {unidad}. Necesario: {necesario:g} {unidad}. Faltan: {faltan:g} {unidad}.",
                "Preparar compra urgente o ajustar producción/menú antes de confirmar el servicio.",
                "stock",
                ["STOCK_REVISAR", "COMPRAS_PREPARAR"],
            ))
        elif minimo and disponible < minimo:
            incidencias.append(_nueva_incidencia(
                "stock_bajo",
                "medio",
                f"Stock bajo de {nombre}",
                f"Disponible: {disponible:g} {unidad}. Mínimo recomendado: {minimo:g} {unidad}.",
                "Incluirlo en pedido sugerido si afecta a producción próxima.",
                "stock",
                ["COMPRAS_PREPARAR"],
            ))
    for raw in _lista(contexto.get("faltantes_stock") or contexto.get("faltantes")):
        item = _normalizar_item(raw, "faltante")
        nombre = item.get("nombre") or item.get("articulo") or "artículo"
        incidencias.append(_nueva_incidencia(
            "falta_stock", "critico", f"Faltante confirmado: {nombre}",
            str(item.get("detalle") or "El sistema marca este artículo como faltante para la operativa."),
            "Convertir el faltante en compra prioritaria o validar sustitución con cocina.", "stock", ["COMPRAS_PREPARAR"]
        ))
    return incidencias


def _detectar_recursos(contexto: Dict[str, Any]) -> List[Dict[str, Any]]:
    incidencias: List[Dict[str, Any]] = []
    for raw in _lista(contexto.get("recursos") or contexto.get("recursos_cocina")):
        item = _normalizar_item(raw, "recurso")
        nombre = item.get("nombre") or item.get("recurso") or "recurso"
        estado = str(item.get("estado") or item.get("situacion") or "").lower()
        conflicto = item.get("conflicto") or item.get("ocupado") or estado in {"ocupado", "no disponible", "averiado", "bloqueado"}
        if conflicto:
            nivel = "critico" if item.get("imprescindible") else "alto"
            incidencias.append(_nueva_incidencia(
                "recurso_ocupado",
                nivel,
                f"Recurso no disponible: {nombre}",
                str(item.get("detalle") or item.get("motivo") or "El recurso está ocupado, averiado o bloqueado."),
                "Reasignar horario, buscar recurso alternativo o mover tareas que dependan de este recurso.",
                "recursos",
                ["RECURSOS_REVISAR", "PLANNING_GENERAR"],
            ))
    return incidencias


def _detectar_proveedores(contexto: Dict[str, Any]) -> List[Dict[str, Any]]:
    incidencias: List[Dict[str, Any]] = []
    for raw in _lista(contexto.get("proveedores") or contexto.get("proveedores_estado")):
        item = _normalizar_item(raw, "proveedor")
        nombre = item.get("nombre") or item.get("proveedor") or "proveedor"
        disponible = item.get("disponible")
        estado = str(item.get("estado") or "").lower()
        if disponible is False or estado in {"cerrado", "no disponible", "sin reparto", "bloqueado"}:
            incidencias.append(_nueva_incidencia(
                "proveedor_no_disponible",
                "alto",
                f"Proveedor no disponible: {nombre}",
                str(item.get("detalle") or item.get("motivo") or "No hay garantía de servicio para este proveedor."),
                "Buscar proveedor alternativo antes de generar el pedido definitivo.",
                "proveedores",
                ["COMPRAS_PREPARAR"],
            ))
    return incidencias


def _detectar_tareas(contexto: Dict[str, Any], planificacion: Dict[str, Any]) -> List[Dict[str, Any]]:
    incidencias: List[Dict[str, Any]] = []
    tareas = _lista(contexto.get("tareas") or contexto.get("planning") or contexto.get("plan_produccion"))
    if not tareas and planificacion.get("plan"):
        tareas = planificacion.get("plan", [])
    for raw in tareas:
        tarea = _normalizar_item(raw, "tarea")
        nombre = tarea.get("nombre") or tarea.get("codigo") or "tarea"
        responsable = tarea.get("responsable") or tarea.get("cocinero") or tarea.get("asignado_a")
        if tarea.get("requiere_responsable") and not responsable:
            incidencias.append(_nueva_incidencia(
                "tarea_sin_responsable", "alto", f"Tarea sin responsable: {nombre}",
                "Hay una tarea operativa que debe quedar asignada antes de empezar producción.",
                "Asignar un cocinero responsable y evitar que quede en tierra de nadie.", "planning", [str(tarea.get("codigo") or nombre)]
            ))
        retraso = tarea.get("retraso") or tarea.get("retrasada") or tarea.get("minutos_retraso")
        minutos = _cantidad(tarea, "minutos_retraso", "retraso_minutos")
        if retraso or minutos > 0:
            nivel = "critico" if minutos >= 60 or tarea.get("bloquea_servicio") else "alto"
            incidencias.append(_nueva_incidencia(
                "retraso", nivel, f"Retraso en {nombre}",
                str(tarea.get("detalle") or f"Retraso detectado de {minutos:g} minutos."),
                "Reordenar tareas, adelantar elaboraciones críticas y revisar personal/recurso necesario.", "planning", [str(tarea.get("codigo") or nombre)]
            ))
    return incidencias


def _detectar_personal(contexto: Dict[str, Any]) -> List[Dict[str, Any]]:
    incidencias: List[Dict[str, Any]] = []
    personal = contexto.get("personal") or {}
    if isinstance(personal, dict):
        disponibles = _cantidad(personal, "disponibles", "cocineros_disponibles", "actual")
        necesarios = _cantidad(personal, "necesarios", "cocineros_necesarios", "requeridos")
        if necesarios and disponibles < necesarios:
            incidencias.append(_nueva_incidencia(
                "falta_personal", "critico" if disponibles == 0 else "alto", "Falta personal para cubrir la producción",
                f"Disponibles: {disponibles:g}. Necesarios: {necesarios:g}.",
                "Reducir carga, adelantar producción o pedir refuerzo antes de confirmar el planning.", "personal", ["PLANNING_GENERAR"]
            ))
    return incidencias


def _detectar_conflictos(contexto: Dict[str, Any]) -> List[Dict[str, Any]]:
    incidencias: List[Dict[str, Any]] = []
    for raw in _lista(contexto.get("conflictos") or contexto.get("conflictos_produccion_eventos")):
        item = _normalizar_item(raw, "conflicto")
        incidencias.append(_nueva_incidencia(
            item.get("tipo", "conflicto_produccion_evento"),
            item.get("nivel", "alto"),
            item.get("titulo") or item.get("nombre") or "Conflicto producción/evento",
            str(item.get("detalle") or item.get("motivo") or "Hay un conflicto entre producción, evento, recurso o horario."),
            str(item.get("accion_recomendada") or "Separar prioridades, replanificar y confirmar antes de aplicar cambios."),
            item.get("origen", "conflictos"),
            item.get("bloquea", ["PLANNING_GENERAR"]),
        ))
    return incidencias


def detectar_incidencias_operativas(planificacion: Dict[str, Any], prioridades: Dict[str, Any] | None = None, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Devuelve incidencias operativas clasificadas por criticidad.

    Entradas esperadas: plan de 5.3.5, prioridades de 5.3.6 y contexto opcional
    con stock, recursos, proveedores, tareas, personal y conflictos. Todo es
    tolerante a datos parciales para poder conectarlo a motores existentes.
    """
    contexto = contexto or {}
    prioridades = prioridades or {}
    if not planificacion.get("ok"):
        return {
            "ok": False,
            "estado": "no_detectable",
            "mensaje": "No puedo detectar incidencias porque no hay un planning operativo válido.",
            "incidencias": [],
            "resumen": {nivel: 0 for nivel in NIVELES},
        }

    incidencias: List[Dict[str, Any]] = []
    incidencias.extend(_detectar_bloqueos_plan(planificacion))
    incidencias.extend(_detectar_stock(contexto))
    incidencias.extend(_detectar_recursos(contexto))
    incidencias.extend(_detectar_proveedores(contexto))
    incidencias.extend(_detectar_tareas(contexto, planificacion))
    incidencias.extend(_detectar_personal(contexto))
    incidencias.extend(_detectar_conflictos(contexto))

    incidencias = _ordenar_incidencias(incidencias)
    resumen = {nivel: 0 for nivel in NIVELES}
    for incidencia in incidencias:
        resumen[incidencia["nivel"]] += 1

    estado = "sin_incidencias" if not incidencias else "incidencias_detectadas"
    mensaje = "No hay incidencias operativas detectadas." if not incidencias else "Incidencias detectadas y clasificadas por impacto operativo."
    return {
        "ok": True,
        "estado": estado,
        "incidencias": incidencias,
        "resumen": resumen,
        "total_incidencias": len(incidencias),
        "requiere_replanificacion": any(i["nivel"] in {"critico", "alto"} for i in incidencias),
        "prioridades_base": prioridades.get("prioridades", {}),
        "mensaje": mensaje,
    }


def formatear_incidencias(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = ["HOST AI 5.3.7 - DETECTOR INTELIGENTE DE INCIDENCIAS", "-" * 60, resultado.get("mensaje", "")]
    if not resultado.get("ok"):
        return "\n".join(lineas)
    if not resultado.get("incidencias"):
        lineas.append("La producción puede seguir según el planning actual.")
        return "\n".join(lineas)
    lineas.append("")
    for nivel in NIVELES:
        grupo = [i for i in resultado.get("incidencias", []) if i.get("nivel") == nivel]
        if not grupo:
            continue
        lineas.append(nivel.upper())
        for inc in grupo:
            lineas.append(f"- {inc.get('titulo')}")
            lineas.append(f"  Detalle: {inc.get('detalle')}")
            lineas.append(f"  Acción: {inc.get('accion_recomendada')}")
        lineas.append("")
    return "\n".join(lineas).rstrip()


__all__ = ["detectar_incidencias_operativas", "formatear_incidencias", "NIVELES"]
