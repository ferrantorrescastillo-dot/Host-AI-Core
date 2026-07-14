"""Host AI 5.4.5 - Optimizador Global.

Optimiza decisiones de cocina equilibrando tiempo, coste, personal, recursos,
stock y riesgo. No aplica cambios reales: propone el mejor plan operativo como
lo haria un segundo jefe de cocina antes de confirmar cambios.
"""
from __future__ import annotations

from typing import Any, Dict, List

try:
    from SERVICIOS.simulador_escenarios_544 import simular_varios_escenarios_544
    from SERVICIOS.evaluador_alternativas_543 import evaluar_alternativas_543
except ModuleNotFoundError:  # permite ejecucion aislada en tests antiguos
    simular_varios_escenarios_544 = None  # type: ignore
    evaluar_alternativas_543 = None  # type: ignore

PESO_RIESGO = {"bajo": 1, "medio": 2, "alto": 3, "critico": 4}


def _num(valor: Any, defecto: float = 0.0) -> float:
    try:
        if valor in (None, ""):
            return defecto
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def _score_plan(plan: Dict[str, Any]) -> int:
    riesgo = PESO_RIESGO.get(str(plan.get("riesgo", "medio")).lower(), 2)
    coste = _num(plan.get("coste_relativo"), 50)
    tiempo = _num(plan.get("tiempo_relativo"), 50)
    servicio = _num(plan.get("seguridad_servicio"), 70)
    requiere_refuerzo = 8 if plan.get("requiere_refuerzo") else 0
    score = 100 + servicio - (riesgo * 18) - (coste * 0.25) - (tiempo * 0.25) - requiere_refuerzo
    return max(0, min(100, int(round(score))))


def _planes_base(datos_evento: Dict[str, Any], contexto: Dict[str, Any]) -> List[Dict[str, Any]]:
    personas = int(_num(datos_evento.get("personas"), 0))
    personal = contexto.get("personal", {}) if isinstance(contexto.get("personal"), dict) else {}
    disponibles = int(_num(personal.get("disponibles", personal.get("actual", 3)), 3))
    necesarios = int(_num(personal.get("necesarios", 3), 3))
    falta_personal = disponibles < necesarios or (personas >= 160 and disponibles < 3)

    stock_critico = any(
        isinstance(item, dict) and _num(item.get("disponible"), 0) < _num(item.get("necesario"), 0)
        for item in (contexto.get("stock", []) or [])
    )
    recursos_conflicto = any(
        isinstance(r, dict) and (r.get("conflicto") or str(r.get("estado", "")).lower() in {"ocupado", "bloqueado"})
        for r in (contexto.get("recursos", []) or [])
    )

    planes: List[Dict[str, Any]] = [
        {
            "codigo": "PLAN_SEGURO",
            "nombre": "Plan seguro de servicio",
            "descripcion": "Proteger el servicio: confirmar evento, revisar stock real, preparar compras y reservar recursos criticos.",
            "acciones": [
                "Confirmar evento y menu operativo",
                "Consultar stock real antes de cerrar compras",
                "Preparar pedido de articulos criticos",
                "Reservar recursos de cocina por franjas",
                "Validar personal necesario antes de aplicar planning",
            ],
            "riesgo": "bajo" if not (stock_critico or falta_personal or recursos_conflicto) else "medio",
            "coste_relativo": 55,
            "tiempo_relativo": 55,
            "seguridad_servicio": 88,
            "requiere_refuerzo": falta_personal,
        },
        {
            "codigo": "PLAN_COSTE",
            "nombre": "Plan de coste controlado",
            "descripcion": "Priorizar proveedor habitual y produccion interna, aceptando algo mas de riesgo operativo.",
            "acciones": [
                "Comprar primero al proveedor habitual",
                "Evitar compras urgentes salvo articulos criticos",
                "Adelantar elaboraciones que reduzcan merma",
                "Mantener menu sin cambios si el stock lo permite",
            ],
            "riesgo": "alto" if stock_critico else "medio",
            "coste_relativo": 35,
            "tiempo_relativo": 65,
            "seguridad_servicio": 72,
            "requiere_refuerzo": False,
        },
        {
            "codigo": "PLAN_TIEMPO",
            "nombre": "Plan rapido de ejecucion",
            "descripcion": "Comprar urgente, adelantar produccion critica y simplificar tareas para ganar tiempo.",
            "acciones": [
                "Comprar articulos criticos con entrega mas rapida",
                "Mover elaboraciones frias al primer hueco libre",
                "Reasignar recursos para evitar esperas",
                "Simplificar tareas no visibles para el cliente",
            ],
            "riesgo": "bajo" if not falta_personal else "medio",
            "coste_relativo": 75,
            "tiempo_relativo": 35,
            "seguridad_servicio": 84,
            "requiere_refuerzo": falta_personal,
        },
    ]

    if falta_personal:
        planes.append({
            "codigo": "PLAN_REFUERZO",
            "nombre": "Plan con refuerzo de personal",
            "descripcion": "Pedir apoyo en las horas de carga alta para no comprometer calidad ni tiempos.",
            "acciones": [
                "Pedir un cocinero de apoyo en franja critica",
                "Asignar a cada cocinero tareas completas",
                "Adelantar mise en place que no dependa del ultimo momento",
                "Revisar planning antes de confirmar al cliente",
            ],
            "riesgo": "bajo",
            "coste_relativo": 80,
            "tiempo_relativo": 45,
            "seguridad_servicio": 92,
            "requiere_refuerzo": True,
        })

    for plan in planes:
        plan["puntuacion"] = _score_plan(plan)
    return sorted(planes, key=lambda p: p["puntuacion"], reverse=True)


def optimizar_operacion_545(datos_evento: Dict[str, Any] | None = None, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Devuelve el mejor plan global sin modificar datos reales."""
    datos_evento = datos_evento or {"tipo": "evento", "personas": 180, "menu": "paella"}
    contexto = contexto or {}
    planes = _planes_base(datos_evento, contexto)
    recomendado = planes[0] if planes else None

    evaluacion = None
    if evaluar_alternativas_543:
        try:
            evaluacion = evaluar_alternativas_543(datos_evento, contexto)
        except Exception as exc:  # seguro ante entornos incompletos
            evaluacion = {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "version": "5.4.5",
        "estado": "optimizacion_global_preparada",
        "evento": datos_evento,
        "planes": planes,
        "plan_recomendado": recomendado,
        "criterios": ["seguridad_servicio", "riesgo", "coste", "tiempo", "personal", "recursos"],
        "requiere_confirmacion": True,
        "aplicado": False,
        "evaluacion_alternativas": evaluacion,
        "lectura_jefe_cocina": _lectura_jefe(recomendado),
        "mensaje": "Optimizacion global generada en modo seguro. No se ha aplicado ningun cambio real.",
    }


def _lectura_jefe(plan: Dict[str, Any] | None) -> str:
    if not plan:
        return "No tomaria una decision global sin validar stock, personal y recursos."
    return f"Yo iria con {plan.get('nombre')}: {plan.get('descripcion')}"


def formatear_optimizacion_545(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = ["HOST AI 5.4.5 - OPTIMIZADOR GLOBAL", "-" * 60]
    plan = resultado.get("plan_recomendado") or {}
    lineas.append(f"Estado: {resultado.get('estado')}")
    lineas.append(f"Aplicado a datos reales: {resultado.get('aplicado')}")
    lineas.append("")
    lineas.append("PLAN RECOMENDADO")
    lineas.append(f"- {plan.get('nombre')} ({plan.get('puntuacion')}/100)")
    lineas.append(f"- {plan.get('descripcion')}")
    lineas.append("")
    lineas.append("ACCIONES PROPUESTAS")
    for accion in plan.get("acciones", []):
        lineas.append(f"- {accion}")
    lineas.append("")
    lineas.append("PLANES COMPARADOS")
    for p in resultado.get("planes", []):
        lineas.append(f"- {p.get('nombre')}: {p.get('puntuacion')}/100 | riesgo {p.get('riesgo')}")
    lineas.append("")
    lineas.append("LECTURA DE SEGUNDO JEFE")
    lineas.append(f"- {resultado.get('lectura_jefe_cocina')}")
    lineas.append("")
    lineas.append("Confirmacion necesaria antes de aplicar cambios reales.")
    return "\n".join(lineas)


__all__ = ["optimizar_operacion_545", "formatear_optimizacion_545"]
