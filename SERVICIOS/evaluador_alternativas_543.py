"""Host AI 5.4.3 - Evaluador Inteligente de Alternativas.

Cuando Host AI detecta un problema operativo, no propone una unica salida.
Compara alternativas como lo haria un segundo jefe de cocina: coste, tiempo,
riesgo, impacto en servicio y necesidad de confirmacion.
"""
from __future__ import annotations

from typing import Any, Dict, List

from SERVICIOS.motor_decisiones_542 import tomar_decisiones_operativas_542

PESO_RIESGO = {"bajo": 1, "medio": 2, "alto": 3, "critico": 4}
PESO_COSTE = {"nulo": 0, "bajo": 1, "medio": 2, "alto": 3, "muy_alto": 4}
PESO_TIEMPO = {"rapido": 1, "normal": 2, "lento": 3, "bloqueante": 4}


def _alt(codigo: str, titulo: str, accion: str, coste: str, tiempo: str, riesgo: str, impacto: str, confirma: bool, motivo: str) -> Dict[str, Any]:
    puntuacion = 100 - (PESO_RIESGO.get(riesgo, 2) * 18) - (PESO_COSTE.get(coste, 2) * 8) - (PESO_TIEMPO.get(tiempo, 2) * 10)
    if impacto == "mantiene_servicio":
        puntuacion += 12
    elif impacto == "afecta_cliente":
        puntuacion -= 18
    elif impacto == "bloquea_servicio":
        puntuacion -= 35
    return {
        "codigo": codigo,
        "titulo": titulo,
        "accion": accion,
        "coste": coste,
        "tiempo": tiempo,
        "riesgo": riesgo,
        "impacto": impacto,
        "requiere_confirmacion": confirma,
        "motivo": motivo,
        "puntuacion": max(0, min(100, int(puntuacion))),
    }


def _alternativas_para_decision(decision: Dict[str, Any], contexto: Dict[str, Any]) -> List[Dict[str, Any]]:
    codigo = decision.get("codigo", "")
    alternativas: List[Dict[str, Any]] = []

    if codigo in {"DEC_COMPRAS_URGENTES", "DEC_PROVEEDOR_ALTERNATIVO"}:
        alternativas.extend([
            _alt("ALT_COMPRA_HABITUAL", "Comprar al proveedor habitual", "Generar pedido urgente al proveedor habitual si confirma entrega.", "medio", "normal", "medio", "mantiene_servicio", True, "Mantiene producto y sistema de trabajo, pero depende de reparto real."),
            _alt("ALT_PROVEEDOR_ALTERNATIVO", "Cambiar a proveedor alternativo", "Pedir el genero critico a otro proveedor con entrega segura.", "alto", "rapido", "bajo", "mantiene_servicio", True, "Sube el coste, pero protege el servicio y reduce el riesgo de rotura."),
            _alt("ALT_AJUSTAR_PRODUCCION", "Ajustar produccion", "Reducir o mover elaboraciones no criticas para liberar genero.", "bajo", "rapido", "alto", "afecta_cliente", True, "Puede salvar la operativa, pero puede afectar al menu o a la promesa al cliente."),
            _alt("ALT_CAMBIAR_MENU", "Cambiar menu", "Proponer alternativa de menu solo si no hay compra viable.", "medio", "normal", "critico", "afecta_cliente", True, "Es la ultima opcion porque tiene impacto comercial alto."),
        ])
    elif codigo == "DEC_REFUERZO_PERSONAL":
        alternativas.extend([
            _alt("ALT_PEDIR_REFUERZO", "Pedir cocinero de apoyo", "Incorporar refuerzo en las horas de mas carga.", "alto", "normal", "bajo", "mantiene_servicio", True, "Es la opcion mas segura para mantener calidad y tiempos."),
            _alt("ALT_ADELANTAR_PRODUCCION", "Adelantar produccion", "Pasar elaboraciones frias o fondos al dia anterior.", "bajo", "normal", "medio", "mantiene_servicio", True, "Reduce presion el dia del evento sin tocar el menu."),
            _alt("ALT_REDUCIR_CARGA", "Reducir carga operativa", "Simplificar emplatados o mise en place no esencial.", "nulo", "rapido", "alto", "afecta_cliente", True, "Ahorra tiempo, pero puede bajar el nivel del servicio."),
        ])
    elif codigo in {"DEC_REASIGNAR_RECURSOS", "DEC_REVISAR_RECURSOS"}:
        alternativas.extend([
            _alt("ALT_CAMBIAR_ORDEN_TAREAS", "Cambiar orden de tareas", "Mover tareas que necesitan horno/abatidor a otra franja libre.", "nulo", "rapido", "bajo", "mantiene_servicio", True, "Es la solucion natural si el problema es un recurso ocupado."),
            _alt("ALT_RECURSO_ALTERNATIVO", "Usar recurso alternativo", "Asignar otro horno, abatidor, fuego o camara disponible.", "bajo", "rapido", "medio", "mantiene_servicio", True, "Mantiene el planning aunque requiere validar capacidad real."),
            _alt("ALT_EXTERNALIZAR_PARTE", "Externalizar parte critica", "Comprar o encargar una elaboracion si el recurso bloquea el servicio.", "alto", "normal", "medio", "mantiene_servicio", True, "Puede salvar tiempo cuando cocina no tiene capacidad."),
        ])
    else:
        alternativas.extend([
            _alt("ALT_CONTINUAR_SEGURO", "Continuar en modo seguro", "Avanzar solo con consultas y acciones sin escritura real.", "nulo", "rapido", "bajo", "mantiene_servicio", False, "No hay bloqueo claro; conviene seguir validando datos."),
            _alt("ALT_PEDIR_CONFIRMACION", "Pedir confirmacion", "Solicitar confirmacion antes de cambiar datos del sistema.", "nulo", "normal", "medio", "mantiene_servicio", True, "Protege datos reales ante decisiones sensibles."),
        ])

    return sorted(alternativas, key=lambda a: a["puntuacion"], reverse=True)


def evaluar_alternativas_543(datos_evento: Dict[str, Any] | None = None, contexto: Dict[str, Any] | None = None, decisiones: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Evalua alternativas por cada decision operativa relevante.

    No aplica cambios reales. Devuelve una recomendacion principal y opciones
    comparadas para que el usuario confirme con criterio.
    """
    contexto = contexto or {}
    if decisiones is None:
        decisiones = tomar_decisiones_operativas_542(datos_evento or {}, contexto)
    if not decisiones.get("ok"):
        return {"ok": False, "version": "5.4.3", "alternativas": [], "mensaje": "No hay decisiones validas para evaluar alternativas.", "aplicado": False}

    bloques = []
    for decision in decisiones.get("decisiones", [])[:8]:
        alts = _alternativas_para_decision(decision, contexto)
        recomendada = alts[0] if alts else None
        bloques.append({
            "decision_codigo": decision.get("codigo"),
            "decision": decision.get("titulo"),
            "motivo_decision": decision.get("motivo"),
            "alternativas": alts,
            "recomendada": recomendada,
        })

    recomendacion_global = None
    for bloque in bloques:
        rec = bloque.get("recomendada")
        if rec and (recomendacion_global is None or rec["puntuacion"] > recomendacion_global["puntuacion"]):
            recomendacion_global = rec

    return {
        "ok": True,
        "version": "5.4.3",
        "estado": "alternativas_evaluadas",
        "riesgo_general": decisiones.get("riesgo_general"),
        "bloques": bloques,
        "alternativas": [a for b in bloques for a in b.get("alternativas", [])],
        "recomendacion_global": recomendacion_global,
        "requiere_confirmacion": any(a.get("requiere_confirmacion") for b in bloques for a in b.get("alternativas", [])),
        "aplicado": False,
        "mensaje": "Alternativas evaluadas. No se ha aplicado ningun cambio real.",
        "lectura_jefe_cocina": _lectura_jefe(recomendacion_global),
        "decisiones": decisiones,
    }


def _lectura_jefe(recomendada: Dict[str, Any] | None) -> str:
    if not recomendada:
        return "No tomaria una decision definitiva sin mas datos operativos."
    return f"Mi primera opcion seria: {recomendada.get('titulo')}. {recomendada.get('motivo')}"


def formatear_alternativas_543(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = ["HOST AI 5.4.3 - EVALUADOR INTELIGENTE DE ALTERNATIVAS", "-" * 60]
    lineas.append(f"Estado: {resultado.get('estado')} | Riesgo: {resultado.get('riesgo_general')}")
    lineas.append(f"Confirmacion necesaria: {resultado.get('requiere_confirmacion')}")
    lineas.append("")
    lineas.append("LECTURA DE SEGUNDO JEFE")
    lineas.append(f"- {resultado.get('lectura_jefe_cocina')}")
    for bloque in resultado.get("bloques", []):
        lineas.append("")
        lineas.append(f"DECISION: {bloque.get('decision')}")
        for alt in bloque.get("alternativas", [])[:4]:
            marca = "RECOMENDADA" if alt == bloque.get("recomendada") else "opcion"
            lineas.append(f"- [{marca}] {alt.get('titulo')} | Puntuacion {alt.get('puntuacion')}/100")
            lineas.append(f"  Accion: {alt.get('accion')}")
            lineas.append(f"  Coste: {alt.get('coste')} | Tiempo: {alt.get('tiempo')} | Riesgo: {alt.get('riesgo')}")
    return "\n".join(lineas)


__all__ = ["evaluar_alternativas_543", "formatear_alternativas_543"]
