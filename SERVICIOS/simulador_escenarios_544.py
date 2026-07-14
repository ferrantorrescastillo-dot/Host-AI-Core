"""Host AI 5.4.4 - Simulador Inteligente de Escenarios.

Permite preguntar "que pasa si..." sin tocar datos reales. Simula impacto en
produccion, compras, stock, personal, recursos y riesgo operativo.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from SERVICIOS.evaluador_alternativas_543 import evaluar_alternativas_543


def _num(valor: Any, defecto: float = 0.0) -> float:
    try:
        if valor in (None, ""):
            return defecto
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def _normalizar_escenario(escenario: Dict[str, Any] | str) -> Dict[str, Any]:
    if isinstance(escenario, dict):
        return dict(escenario)
    texto = str(escenario).lower()
    datos: Dict[str, Any] = {"descripcion": escenario, "tipo": "generico"}
    if "personas" in texto or "pax" in texto or "invitados" in texto:
        datos["tipo"] = "cambio_pax"
        import re
        m = re.search(r"([+-]?\d+)\s*(personas|pax|invitados)", texto)
        if m:
            datos["delta_personas"] = int(m.group(1))
    if "proveedor" in texto or "makro" in texto or "no puede servir" in texto:
        datos["tipo"] = "fallo_proveedor"
    if "cocinero" in texto or "personal" in texto:
        datos["tipo"] = "falta_personal"
        if "falta" in texto or "solo" in texto:
            datos["delta_cocineros"] = -1
    if "horno" in texto or "abatidor" in texto or "cámara" in texto or "camara" in texto:
        datos["tipo"] = "recurso_bloqueado"
    if "cierra" in texto or "cerrar" in texto or "una hora" in texto:
        datos["tipo"] = "menos_tiempo"
        datos["horas_menos"] = 1
    return datos


def _aplicar_escenario(evento: Dict[str, Any], contexto: Dict[str, Any], escenario: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any], List[str]]:
    evento_sim = deepcopy(evento or {})
    contexto_sim = deepcopy(contexto or {})
    cambios: List[str] = []
    tipo = escenario.get("tipo", "generico")

    if tipo == "cambio_pax":
        delta = int(_num(escenario.get("delta_personas", escenario.get("personas_extra", 0))))
        base = int(_num(evento_sim.get("personas", 0)))
        if delta == 0 and escenario.get("personas"):
            nuevo = int(_num(escenario.get("personas")))
            delta = nuevo - base
        evento_sim["personas"] = max(0, base + delta)
        cambios.append(f"Pax simulados: {base} -> {evento_sim['personas']}")
        factor = (evento_sim["personas"] / base) if base else 1
        for item in contexto_sim.get("stock", []) or []:
            if isinstance(item, dict) and item.get("necesario") is not None:
                item["necesario"] = round(_num(item.get("necesario")) * factor, 2)
        contexto_sim.setdefault("simulacion", {})["factor_pax"] = round(factor, 3)

    elif tipo == "fallo_proveedor":
        proveedores = contexto_sim.setdefault("proveedores", [{"nombre": escenario.get("proveedor", "Proveedor habitual")}])
        for p in proveedores:
            if isinstance(p, dict):
                p["disponible"] = False
                p["estado"] = "no disponible"
        cambios.append("Proveedor marcado como no disponible en simulacion")

    elif tipo == "falta_personal":
        personal = contexto_sim.setdefault("personal", {})
        actual = int(_num(personal.get("disponibles", personal.get("actual", 3))))
        delta = int(_num(escenario.get("delta_cocineros", -1)))
        personal["disponibles"] = max(0, actual + delta)
        personal.setdefault("necesarios", max(actual, 3))
        cambios.append(f"Personal simulado: {actual} -> {personal['disponibles']} cocineros")

    elif tipo == "recurso_bloqueado":
        recurso = escenario.get("recurso", "recurso critico")
        contexto_sim.setdefault("recursos", []).append({"nombre": recurso, "estado": "ocupado", "conflicto": True})
        cambios.append(f"Recurso bloqueado en simulacion: {recurso}")

    elif tipo == "menos_tiempo":
        horas = _num(escenario.get("horas_menos", 1), 1)
        contexto_sim.setdefault("tiempo", {})["horas_menos"] = horas
        contexto_sim.setdefault("riesgos", []).append({"tipo": "tiempo", "gravedad": "alto", "detalle": f"{horas} horas menos de cocina"})
        cambios.append(f"Tiempo disponible reducido: -{horas} h")

    else:
        contexto_sim.setdefault("riesgos", []).append({"tipo": "simulacion", "gravedad": "medio", "detalle": escenario.get("descripcion", "escenario generico")})
        cambios.append("Escenario generico añadido como riesgo medio")

    return evento_sim, contexto_sim, cambios


def _impacto(evento_base: Dict[str, Any], evento_sim: Dict[str, Any], contexto_sim: Dict[str, Any], evaluacion: Dict[str, Any]) -> Dict[str, Any]:
    pax_base = _num(evento_base.get("personas"), 0)
    pax_sim = _num(evento_sim.get("personas"), pax_base)
    factor = (pax_sim / pax_base) if pax_base else 1
    coste_estimado = round((factor - 1) * 100, 1)
    personal = contexto_sim.get("personal", {}) if isinstance(contexto_sim.get("personal"), dict) else {}
    disponibles = _num(personal.get("disponibles"), 0)
    necesarios = _num(personal.get("necesarios"), 0)
    alternativas = evaluacion.get("alternativas", [])
    riesgo = evaluacion.get("riesgo_general", "medio")
    return {
        "pax_base": int(pax_base) if pax_base else None,
        "pax_simulado": int(pax_sim) if pax_sim else None,
        "variacion_pax_pct": round((factor - 1) * 100, 1) if pax_base else 0,
        "produccion_pct": round((factor - 1) * 100, 1) if pax_base else 0,
        "compras_pct": round((factor - 1) * 100, 1) if pax_base else 0,
        "coste_estimado_pct": coste_estimado,
        "personal_disponible": disponibles,
        "personal_necesario": necesarios,
        "falta_personal": bool(necesarios and disponibles < necesarios),
        "alternativas_generadas": len(alternativas),
        "riesgo_resultante": riesgo,
    }


def simular_escenario_544(datos_evento: Dict[str, Any], contexto: Dict[str, Any] | None = None, escenario: Dict[str, Any] | str | None = None) -> Dict[str, Any]:
    """Simula un escenario sin modificar datos reales."""
    contexto = contexto or {}
    escenario_norm = _normalizar_escenario(escenario or {"tipo": "generico", "descripcion": "escenario sin detalle"})
    evento_sim, contexto_sim, cambios = _aplicar_escenario(datos_evento or {}, contexto, escenario_norm)
    evaluacion = evaluar_alternativas_543(evento_sim, contexto_sim)
    return {
        "ok": True,
        "version": "5.4.4",
        "estado": "escenario_simulado",
        "escenario": escenario_norm,
        "cambios_simulados": cambios,
        "evento_original": deepcopy(datos_evento or {}),
        "evento_simulado": evento_sim,
        "impacto": _impacto(datos_evento or {}, evento_sim, contexto_sim, evaluacion),
        "evaluacion_alternativas": evaluacion,
        "requiere_confirmacion": False,
        "aplicado": False,
        "mensaje": "Simulacion realizada en modo seguro. No se ha modificado ningun dato real.",
        "lectura_jefe_cocina": _lectura(evaluacion),
    }


def simular_varios_escenarios_544(datos_evento: Dict[str, Any], contexto: Dict[str, Any] | None, escenarios: List[Dict[str, Any] | str]) -> Dict[str, Any]:
    resultados = [simular_escenario_544(datos_evento, contexto, e) for e in escenarios]
    ordenados = sorted(resultados, key=lambda r: {"critico": 4, "alto": 3, "medio": 2, "bajo": 1}.get(r.get("impacto", {}).get("riesgo_resultante", "medio"), 2), reverse=True)
    return {"ok": True, "version": "5.4.4", "estado": "escenarios_comparados", "resultados": ordenados, "aplicado": False, "mensaje": "Escenarios comparados sin modificar datos reales."}


def _lectura(evaluacion: Dict[str, Any]) -> str:
    rec = evaluacion.get("recomendacion_global") or {}
    if rec:
        return f"En esta simulacion vigilaria primero: {rec.get('titulo')}."
    return "La simulacion no muestra una decision clara; validaria datos reales antes de actuar."


def formatear_simulacion_544(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = ["HOST AI 5.4.4 - SIMULADOR INTELIGENTE DE ESCENARIOS", "-" * 60]
    esc = resultado.get("escenario", {}) or {}
    impacto = resultado.get("impacto", {}) or {}
    lineas.append(f"Escenario: {esc.get('descripcion', esc.get('tipo'))}")
    lineas.append(f"Aplicado a datos reales: {resultado.get('aplicado')}")
    lineas.append("")
    lineas.append("CAMBIOS SIMULADOS")
    for c in resultado.get("cambios_simulados", []):
        lineas.append(f"- {c}")
    lineas.append("")
    lineas.append("IMPACTO ESTIMADO")
    lineas.append(f"- Pax: {impacto.get('pax_base')} -> {impacto.get('pax_simulado')} ({impacto.get('variacion_pax_pct')}%)")
    lineas.append(f"- Produccion: {impacto.get('produccion_pct')}%")
    lineas.append(f"- Compras: {impacto.get('compras_pct')}%")
    lineas.append(f"- Riesgo resultante: {impacto.get('riesgo_resultante')}")
    lineas.append(f"- Alternativas generadas: {impacto.get('alternativas_generadas')}")
    lineas.append("")
    lineas.append("LECTURA DE SEGUNDO JEFE")
    lineas.append(f"- {resultado.get('lectura_jefe_cocina')}")
    return "\n".join(lineas)


__all__ = ["simular_escenario_544", "simular_varios_escenarios_544", "formatear_simulacion_544"]
