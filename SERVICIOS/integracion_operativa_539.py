"""Host AI 5.3.9 - Integracion Operativa y Cierre RC 5.3.

Cierra el bloque 5.3 conectando, en modo seguro, los motores ya existentes:
5.3.1 flujo, 5.3.2 ejecucion simulada, 5.3.3 respuesta ejecutiva,
5.3.4 confirmacion, 5.3.5 planificacion, 5.3.6 prioridades,
5.3.7 incidencias y 5.3.8 replanificacion.

No sustituye motores ni duplica logica: solo orquesta y valida el flujo de punta
a punta como lo haria un segundo jefe de cocina antes de dar el servicio por
controlado.
"""
from __future__ import annotations

from typing import Any, Dict, List

from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.ejecutor_flujo_operativo_532 import ejecutar_flujo_operativo
from SERVICIOS.respuesta_ejecutiva_533 import generar_respuesta_ejecutiva_evento
from SERVICIOS.confirmacion_inteligente_534 import analizar_confirmaciones_flujo
from SERVICIOS.planificador_inteligente_535 import planificar_ejecucion_inteligente
from SERVICIOS.priorizador_tareas_536 import priorizar_tareas_operativas
from SERVICIOS.detector_incidencias_537 import detectar_incidencias_operativas
from SERVICIOS.replanificador_inteligente_538 import replanificar_operativa_inteligente


ORDEN_BLOQUES = [
    "flujo",
    "ejecucion_segura",
    "confirmacion",
    "planificacion",
    "priorizacion",
    "incidencias",
    "replanificacion",
    "respuesta_ejecutiva",
]


def _estado_bloque(nombre: str, resultado: Dict[str, Any] | None) -> Dict[str, Any]:
    resultado = resultado or {}
    return {
        "bloque": nombre,
        "ok": bool(resultado.get("ok")),
        "estado": resultado.get("estado", "sin_estado"),
        "mensaje": resultado.get("mensaje", ""),
    }


def _contar_incidencias(incidencias: Dict[str, Any]) -> Dict[str, int]:
    resumen = {"critico": 0, "alto": 0, "medio": 0, "bajo": 0}
    for incidencia in incidencias.get("incidencias", []) or []:
        nivel = str(incidencia.get("nivel", "medio")).lower()
        if nivel not in resumen:
            nivel = "medio"
        resumen[nivel] += 1
    return resumen


def _calcular_estado_rc(validacion: List[Dict[str, Any]], incidencias: Dict[str, Any], replanificacion: Dict[str, Any]) -> str:
    if not all(b.get("ok") for b in validacion):
        return "bloqueado"
    resumen = _contar_incidencias(incidencias)
    if resumen["critico"] > 0:
        return "requiere_decision_jefe_cocina"
    if resumen["alto"] > 0 or replanificacion.get("requiere_confirmacion"):
        return "operativo_con_confirmacion"
    return "release_candidate_5_3"


def _recomendacion_final(estado_rc: str, incidencias: Dict[str, Any], replanificacion: Dict[str, Any]) -> str:
    resumen = _contar_incidencias(incidencias)
    if estado_rc == "bloqueado":
        return "No cerraria la 5.3 todavia: hay algun bloque tecnico que no devuelve OK. Revisar tests antes de avanzar."
    if resumen["critico"]:
        return "No aplicaria cambios automaticos: primero resolveria las incidencias criticas y pediria confirmacion al jefe de cocina."
    if resumen["alto"] or replanificacion.get("requiere_confirmacion"):
        return "La operativa esta controlada, pero requiere confirmacion antes de aplicar la replanificacion propuesta."
    return "La 5.3 queda estable como Release Candidate: flujo, planning, incidencias, replanificacion y respuesta trabajan conectados."


def cerrar_inteligencia_operativa_539(datos_evento: Dict[str, Any], contexto: Dict[str, Any] | None = None, confirmar_ejecucion: bool = False) -> Dict[str, Any]:
    """Ejecuta el cierre integral del bloque 5.3 en modo seguro.

    La funcion no escribe datos reales. Genera un expediente operativo completo
    para comprobar si Host AI puede comportarse como segundo jefe de cocina ante
    un evento: prepara flujo, plan, prioridades, detecta problemas, propone
    replanificacion y redacta respuesta ejecutiva.
    """
    contexto = contexto or {}

    flujo = generar_flujo_operativo_evento(datos_evento)
    ejecucion = ejecutar_flujo_operativo(flujo, confirmar=confirmar_ejecucion) if flujo.get("ok") else {"ok": False, "estado": "sin_flujo", "mensaje": "Sin flujo valido."}
    confirmacion = analizar_confirmaciones_flujo(flujo, ejecucion) if flujo.get("ok") else {"ok": False, "estado": "sin_flujo", "mensaje": "Sin flujo valido."}
    planificacion = planificar_ejecucion_inteligente(flujo, contexto=contexto)
    priorizacion = priorizar_tareas_operativas(planificacion)
    incidencias = detectar_incidencias_operativas(planificacion, priorizacion, contexto)
    replanificacion = replanificar_operativa_inteligente(planificacion, incidencias, contexto=contexto, aplicar=False)
    respuesta = generar_respuesta_ejecutiva_evento(flujo, ejecucion) if flujo.get("ok") else {"ok": False, "estado": "sin_flujo", "mensaje": "No puedo generar respuesta ejecutiva sin datos mínimos."}

    validacion = [
        _estado_bloque("5.3.1 flujo", flujo),
        _estado_bloque("5.3.2 ejecucion_segura", ejecucion),
        _estado_bloque("5.3.4 confirmacion", confirmacion),
        _estado_bloque("5.3.5 planificacion", planificacion),
        _estado_bloque("5.3.6 priorizacion", priorizacion),
        _estado_bloque("5.3.7 incidencias", incidencias),
        _estado_bloque("5.3.8 replanificacion", replanificacion),
        _estado_bloque("5.3.3 respuesta_ejecutiva", respuesta),
    ]

    estado_rc = _calcular_estado_rc(validacion, incidencias, replanificacion)
    resumen_incidencias = _contar_incidencias(incidencias)

    return {
        "ok": estado_rc != "bloqueado",
        "estado": estado_rc,
        "version": "5.3.9",
        "modo": "seguro_sin_escritura_real",
        "datos_evento": flujo.get("datos", datos_evento),
        "validacion_bloques": validacion,
        "flujo": flujo,
        "ejecucion": ejecucion,
        "confirmacion": confirmacion,
        "planificacion": planificacion,
        "priorizacion": priorizacion,
        "incidencias": incidencias,
        "resumen_incidencias": resumen_incidencias,
        "replanificacion": replanificacion,
        "respuesta_ejecutiva": respuesta,
        "requiere_confirmacion": bool(replanificacion.get("requiere_confirmacion") or confirmacion.get("requiere_confirmacion")),
        "aplica_cambios_reales": False,
        "recomendacion_final": _recomendacion_final(estado_rc, incidencias, replanificacion),
        "mensaje": "Cierre operativo 5.3 generado en modo seguro. No se han modificado datos reales.",
    }


def formatear_cierre_operativo_539(resultado: Dict[str, Any]) -> str:
    """Devuelve una lectura ejecutiva compacta para consola."""
    datos = resultado.get("datos_evento", {}) or {}
    resumen = resultado.get("resumen_incidencias", {}) or {}
    lineas: List[str] = []
    lineas.append("HOST AI 5.3.9 - CIERRE INTELIGENCIA OPERATIVA")
    lineas.append("-" * 60)
    lineas.append(f"Estado: {resultado.get('estado')}")
    lineas.append(f"Evento: {datos.get('tipo', 'evento')} | Pax: {datos.get('personas', 'pendiente')} | Fecha: {datos.get('fecha', 'pendiente')}")
    lineas.append(f"Modo: {resultado.get('modo')} | Cambios reales: {resultado.get('aplica_cambios_reales')}")
    lineas.append("")
    lineas.append("VALIDACION DE BLOQUES")
    for bloque in resultado.get("validacion_bloques", []) or []:
        marca = "OK" if bloque.get("ok") else "FAIL"
        lineas.append(f"- {marca}: {bloque.get('bloque')} ({bloque.get('estado')})")
    lineas.append("")
    lineas.append("INCIDENCIAS")
    lineas.append(f"- Criticas: {resumen.get('critico', 0)}")
    lineas.append(f"- Altas: {resumen.get('alto', 0)}")
    lineas.append(f"- Medias: {resumen.get('medio', 0)}")
    lineas.append(f"- Bajas: {resumen.get('bajo', 0)}")
    lineas.append("")
    lineas.append("DECISION OPERATIVA")
    lineas.append(f"- Requiere confirmacion: {resultado.get('requiere_confirmacion')}")
    lineas.append(f"- Recomendacion: {resultado.get('recomendacion_final')}")

    replan = resultado.get("replanificacion", {}) or {}
    if replan.get("nuevo_planning"):
        lineas.append("")
        lineas.append("PRIMERAS ACCIONES PROPUESTAS")
        for tarea in (replan.get("nuevo_planning") or [])[:5]:
            lineas.append(f"{tarea.get('orden', '-')}. {tarea.get('nombre')} -> {tarea.get('accion')}")

    return "\n".join(lineas)


__all__ = ["cerrar_inteligencia_operativa_539", "formatear_cierre_operativo_539"]
