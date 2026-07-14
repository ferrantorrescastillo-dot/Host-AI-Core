"""Host AI 5.4.8 - Integracion completa y Release Candidate 5.4.

Cierra el bloque 5.4 uniendo analisis de situacion, decisiones, alternativas,
simulacion, optimizacion, aprendizaje y explicacion. Funciona en modo seguro:
coordina resultados y valida el flujo sin escribir datos reales.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple


def _importar(nombre: str, funcion: str) -> Callable[..., Dict[str, Any]] | None:
    try:
        modulo = __import__(nombre, fromlist=[funcion])
        return getattr(modulo, funcion)
    except Exception:
        return None


analizar_situacion_operativa_541 = _importar("SERVICIOS.analizador_situacion_541", "analizar_situacion_operativa_541")
tomar_decisiones_operativas_542 = _importar("SERVICIOS.motor_decisiones_542", "tomar_decisiones_operativas_542")
evaluar_alternativas_543 = _importar("SERVICIOS.evaluador_alternativas_543", "evaluar_alternativas_543")
simular_escenario_544 = _importar("SERVICIOS.simulador_escenarios_544", "simular_escenario_544")
optimizar_operacion_545 = _importar("SERVICIOS.optimizador_global_545", "optimizar_operacion_545")
aprender_operativa_546 = _importar("SERVICIOS.aprendizaje_operativo_546", "aprender_operativa_546")
explicar_decisiones_547 = _importar("SERVICIOS.explicacion_decisiones_547", "explicar_decisiones_547")


def ejecutar_release_candidate_548(contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Ejecuta el cierre seguro de Host AI 5.4."""
    datos_evento, contexto_operativo = _preparar_contexto(contexto)
    etapas: List[Dict[str, Any]] = []
    resultados: Dict[str, Any] = {}

    situacion = _ejecutar("5.4.1", "Analizador de situacion", analizar_situacion_operativa_541, datos_evento, contexto_operativo)
    etapas.append(situacion[0]); resultados["situacion"] = situacion[1]

    decisiones = _ejecutar("5.4.2", "Motor de decisiones", tomar_decisiones_operativas_542, datos_evento, contexto_operativo, resultados.get("situacion"))
    etapas.append(decisiones[0]); resultados["decisiones"] = decisiones[1]

    alternativas = _ejecutar("5.4.3", "Evaluador de alternativas", evaluar_alternativas_543, datos_evento, contexto_operativo, resultados.get("decisiones"))
    etapas.append(alternativas[0]); resultados["alternativas"] = alternativas[1]

    escenario = {"tipo": "aumento_personas", "personas_extra": 40, "descripcion": "Simulacion de subida de invitados"}
    simulacion = _ejecutar("5.4.4", "Simulador de escenarios", simular_escenario_544, datos_evento, contexto_operativo, escenario)
    etapas.append(simulacion[0]); resultados["simulacion"] = simulacion[1]

    optimizacion = _ejecutar("5.4.5", "Optimizador global", optimizar_operacion_545, datos_evento, contexto_operativo)
    etapas.append(optimizacion[0]); resultados["optimizacion"] = optimizacion[1]

    aprendizaje = _ejecutar("5.4.6", "Aprendizaje operativo", aprender_operativa_546, None, contexto_operativo)
    etapas.append(aprendizaje[0]); resultados["aprendizaje"] = aprendizaje[1]

    lista_decisiones = _extraer_decisiones(resultados.get("decisiones"))
    contexto_explicacion = dict(contexto_operativo)
    contexto_explicacion.update(datos_evento)
    explicacion = _ejecutar("5.4.7", "Explicacion de decisiones", explicar_decisiones_547, contexto_explicacion, lista_decisiones)
    etapas.append(explicacion[0]); resultados["explicacion"] = explicacion[1]

    ok_etapas = sum(1 for e in etapas if e["ok"])
    total = len(etapas)
    bloque_ok = ok_etapas == total
    requiere_confirmacion = _requiere_confirmacion_global(resultados)
    lectura = _lectura_jefe(resultados, bloque_ok, requiere_confirmacion)

    return {
        "ok": bloque_ok,
        "version": "5.4.8",
        "estado": "release_candidate_5_4" if bloque_ok else "release_candidate_5_4_con_avisos",
        "etapas_ok": ok_etapas,
        "etapas_total": total,
        "porcentaje": round((ok_etapas / total) * 100, 2) if total else 0,
        "etapas": etapas,
        "resultados": resultados,
        "requiere_confirmacion": requiere_confirmacion,
        "aplicado": False,
        "lectura_jefe_cocina": lectura,
        "mensaje": "Cierre 5.4 ejecutado en modo seguro. No se han aplicado cambios reales.",
    }

def _ejecutar(version: str, nombre: str, funcion: Callable[..., Dict[str, Any]] | None, *args: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if funcion is None:
        etapa = {"version": version, "nombre": nombre, "ok": False, "estado": "no_disponible", "detalle": "Modulo no encontrado"}
        return etapa, {"ok": False, "estado": "no_disponible"}
    try:
        resultado = funcion(*args)
        ok = bool(resultado.get("ok", True)) if isinstance(resultado, dict) else True
        etapa = {"version": version, "nombre": nombre, "ok": ok, "estado": resultado.get("estado", "ejecutado") if isinstance(resultado, dict) else "ejecutado"}
        return etapa, resultado if isinstance(resultado, dict) else {"ok": ok, "valor": resultado}
    except TypeError:
        try:
            resultado = funcion()
            ok = bool(resultado.get("ok", True)) if isinstance(resultado, dict) else True
            etapa = {"version": version, "nombre": nombre, "ok": ok, "estado": resultado.get("estado", "ejecutado") if isinstance(resultado, dict) else "ejecutado"}
            return etapa, resultado if isinstance(resultado, dict) else {"ok": ok, "valor": resultado}
        except Exception as exc:
            etapa = {"version": version, "nombre": nombre, "ok": False, "estado": "error", "detalle": str(exc)}
            return etapa, {"ok": False, "error": str(exc)}
    except Exception as exc:
        etapa = {"version": version, "nombre": nombre, "ok": False, "estado": "error", "detalle": str(exc)}
        return etapa, {"ok": False, "error": str(exc)}


def _extraer_decisiones(resultado: Any) -> List[Dict[str, Any]]:
    if not isinstance(resultado, dict):
        return []
    for clave in ("decisiones", "acciones", "plan", "acciones_priorizadas"):
        valor = resultado.get(clave)
        if isinstance(valor, list):
            return [v if isinstance(v, dict) else {"accion": str(v)} for v in valor]
    return []


def _requiere_confirmacion_global(resultados: Dict[str, Any]) -> bool:
    for r in resultados.values():
        if isinstance(r, dict) and r.get("requiere_confirmacion"):
            return True
    return False


def _lectura_jefe(resultados: Dict[str, Any], bloque_ok: bool, requiere_confirmacion: bool) -> str:
    base = "La 5.4 queda cerrada como motor de decisiones en modo seguro." if bloque_ok else "La 5.4 se ha ejecutado con avisos y conviene revisar etapas no disponibles."
    if requiere_confirmacion:
        return base + " Hay decisiones listas, pero no aplicaria cambios reales sin confirmacion del jefe de cocina."
    return base + " No hay cambios reales pendientes de aplicar."


def _preparar_contexto(contexto: Dict[str, Any] | None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    base = _contexto_demo()
    if contexto:
        base.update(contexto)
    datos_evento = {
        "tipo": base.get("tipo") or base.get("tipo_evento") or "boda",
        "personas": base.get("personas") or base.get("comensales") or 180,
        "fecha": base.get("fecha") or "sabado",
        "hora_servicio": base.get("hora_servicio") or "15:00",
        "menu": base.get("menu") or "paella",
        "lugar": base.get("lugar") or "Restaurante",
        "restricciones": base.get("restricciones") or "sin restricciones",
        "objetivo": base.get("objetivo") or "todo el flujo completo",
    }
    contexto_operativo = {
        "stock": base.get("stock") or [
            {"articulo": "arroz bomba", "disponible": 35, "necesario": 32},
            {"articulo": "caldo", "disponible": 100, "necesario": 95},
            {"articulo": "proteina principal", "disponible": 42, "necesario": 40},
        ],
        "personal": base.get("personal") or {"disponibles": base.get("personal_disponible", 3), "necesarios": 3},
        "recursos": base.get("recursos") if isinstance(base.get("recursos"), list) else [
            {"nombre": "paellera 90", "estado": "disponible"},
            {"nombre": "fogones exteriores", "estado": "disponible"},
        ],
        "proveedores": base.get("proveedores") or [{"nombre": "Makro", "disponible": True}],
        "coste_objetivo": base.get("coste_objetivo", 45),
    }
    return datos_evento, contexto_operativo


def _contexto_demo() -> Dict[str, Any]:
    return {
        "tipo_evento": "boda",
        "personas": 180,
        "menu": "paella",
        "fecha": "sabado",
        "hora_servicio": "15:00",
        "personal_disponible": 3,
        "recursos": {"horno": "ocupado hasta 12:00", "paelleras": 6},
    }


def formatear_release_candidate_548(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = ["HOST AI 5.4.8 - RELEASE CANDIDATE 5.4", "-" * 70]
    lineas.append(f"Estado: {resultado.get('estado')}")
    lineas.append(f"Etapas OK: {resultado.get('etapas_ok')}/{resultado.get('etapas_total')} ({resultado.get('porcentaje')}%)")
    lineas.append(f"Aplicado a datos reales: {resultado.get('aplicado')}")
    lineas.append(f"Requiere confirmacion: {resultado.get('requiere_confirmacion')}")
    lineas.append("")
    lineas.append("ETAPAS")
    for etapa in resultado.get("etapas", []):
        marca = "OK" if etapa.get("ok") else "AVISO"
        lineas.append(f"- {marca} {etapa.get('version')} {etapa.get('nombre')} -> {etapa.get('estado')}")
    lineas.append("")
    lineas.append("LECTURA DE SEGUNDO JEFE")
    lineas.append(f"- {resultado.get('lectura_jefe_cocina')}")
    return "\n".join(lineas)


__all__ = ["ejecutar_release_candidate_548", "formatear_release_candidate_548"]
