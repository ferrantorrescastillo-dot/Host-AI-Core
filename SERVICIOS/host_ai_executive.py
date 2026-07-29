from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import unicodedata

from SERVICIOS.gestor_contexto_permanente_5410 import GestorContextoPermanente5410
from SERVICIOS.orquestador_flujo_operativo import OrquestadorFlujoOperativo


_WORKFLOW_POR_CODIGO = {
    "EVENTO_CREAR": "PREPARACION_EVENTO",
    "MENU_ASOCIAR": "PREPARACION_EVENTO",
    "PRODUCCION_PLAN": "PRODUCCION_INTELIGENTE",
    "RECURSOS_REVISAR": "PRODUCCION_INTELIGENTE",
    "PLANNING_GENERAR": "PRODUCCION_INTELIGENTE",
    "STOCK_REVISAR": "STOCK_OPERATIVO",
    "COMPRAS_PREPARAR": "COMPRAS_INTELIGENTES",
    "COSTES_CALCULAR": "RENTABILIDAD",
}

_PRIORIDAD_WORKFLOW = {
    "PREPARACION_EVENTO": 1,
    "PRODUCCION_INTELIGENTE": 2,
    "STOCK_OPERATIVO": 3,
    "COMPRAS_INTELIGENTES": 4,
    "RENTABILIDAD": 5,
}

_TITULO_WORKFLOW = {
    "PREPARACION_EVENTO": "Completar Menú",
    "PRODUCCION_INTELIGENTE": "Preparar Producción",
    "STOCK_OPERATIVO": "Validar Stock",
    "COMPRAS_INTELIGENTES": "Revisar Compras",
    "RENTABILIDAD": "Revisar Rentabilidad",
}

_PENDIENTE_POR_CODIGO = {
    "EVENTO_CREAR": "Confirmar creación del evento.",
    "MENU_ASOCIAR": "Completar planificación del menú.",
    "PRODUCCION_PLAN": "Preparar Producción.",
    "RECURSOS_REVISAR": "Revisar recursos de Producción.",
    "PLANNING_GENERAR": "Completar planificación de Producción.",
    "STOCK_REVISAR": "Validar stock operativo.",
    "COMPRAS_PREPARAR": "Revisar Compras.",
    "COSTES_CALCULAR": "Revisar rentabilidad prevista.",
}

_PRESENTACION_ACCIONES = {
    "completar menu": "Completar el menú del evento",
    "completar planificación del menú": "Asignar los platos y pases que faltan al menú del evento",
    "completar planificacion del menu": "Asignar los platos y pases que faltan al menú del evento",
    "preparar produccion": "Generar la planificación de cocina",
    "revisar compras": "Revisar la propuesta de compras del evento",
    "validar stock": "Comprobar que hay stock suficiente",
    "evento_crear": "Confirmar creación del evento",
    "menu_asociar": "Asignar los platos y pases que faltan al menú del evento",
    "produccion_plan": "Generar la planificación de cocina",
    "recursos_revisar": "Revisar recursos de cocina y secuencia de producción",
    "planning_generar": "Generar la planificación de cocina",
    "stock_revisar": "Comprobar que hay stock suficiente",
    "compras_preparar": "Revisar la propuesta de compras del evento",
    "costes_calcular": "Revisar la previsión de rentabilidad del evento",
}

EXEC_INTENCION_ANALISIS = "analisis_completo"
EXEC_INTENCION_PENDIENTES = "pendientes"
EXEC_INTENCION_PRIORIDAD = "prioridad"
EXEC_INTENCION_RIESGOS = "riesgos"
EXEC_INTENCION_RECOMENDACIONES = "recomendaciones"
EXEC_INTENCION_RESUMEN = "resumen"
EXEC_INTENCION_RESTAURANTE = "restaurante"
EXEC_INTENCION_IMPACTO_GENERAL = "impacto_general"
EXEC_INTENCION_IMPACTO_PRODUCCION = "impacto_produccion"
EXEC_INTENCION_IMPACTO_COMPRAS = "impacto_compras"
EXEC_INTENCION_BLOQUEO_PRODUCCION = "bloqueo_produccion"
EXEC_INTENCION_DESBLOQUEO = "desbloqueo"
EXEC_INTENCION_MOTIVO_PRIORIDAD = "motivo_prioridad"
EXEC_INTENCION_PLAN_OPERATIVO = "plan_operativo"
EXEC_INTENCION_PLAN_DIA = "plan_dia"

_DEPENDENCIAS_POR_CODIGO = {
    "MENU_ASOCIAR": ["PRODUCCION_PLAN", "COMPRAS_PREPARAR", "STOCK_REVISAR"],
    "PRODUCCION_PLAN": ["COMPRAS_PREPARAR"],
    "COMPRAS_PREPARAR": ["STOCK_REVISAR"],
}

_ORDEN_PLAN_CODIGO = {
    "MENU_ASOCIAR": 1,
    "PRODUCCION_PLAN": 2,
    "PLANNING_GENERAR": 2,
    "RECURSOS_REVISAR": 2,
    "COMPRAS_PREPARAR": 3,
    "STOCK_REVISAR": 4,
}

_MOTIVO_PLAN_EVENTO = {
    "MENU_ASOCIAR": "desbloquea la planificación de cocina y la propuesta de compras.",
    "PRODUCCION_PLAN": "permite calcular necesidades reales de producción.",
    "PLANNING_GENERAR": "permite calcular necesidades reales de producción.",
    "RECURSOS_REVISAR": "asegura que el plan de cocina sea ejecutable.",
    "COMPRAS_PREPARAR": "confirma los faltantes antes de comprar.",
    "STOCK_REVISAR": "evita incidencias antes del servicio.",
}

_MOTIVO_PLAN_RESTAURANTE = {
    "MENU_ASOCIAR": "desbloquea la secuencia de producción y compras de los eventos activos.",
    "PRODUCCION_PLAN": "ordena la ejecución de cocina del día.",
    "COMPRAS_PREPARAR": "asegura aprovisionamiento para los próximos servicios.",
    "STOCK_REVISAR": "reduce incidencias operativas durante el servicio.",
}


def _normalizar_evento(datos_evento: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": datos_evento.get("id"),
        "nombre": datos_evento.get("nombre"),
        "tipo": datos_evento.get("tipo") or datos_evento.get("tipo_evento") or "evento",
        "personas": datos_evento.get("personas") or datos_evento.get("pax"),
        "fecha": datos_evento.get("fecha"),
        "hora_servicio": datos_evento.get("hora_servicio") or datos_evento.get("hora"),
        "menu": datos_evento.get("menu") or datos_evento.get("menú"),
        "lugar": datos_evento.get("lugar") or datos_evento.get("ubicacion") or datos_evento.get("ubicación"),
        "restricciones": datos_evento.get("restricciones") or datos_evento.get("alergias"),
        "objetivo": datos_evento.get("objetivo") or "flujo completo",
    }


def _detecta_workflows(flujo: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for paso in list(flujo.get("pasos") or []):
        codigo = str(paso.get("codigo") or "")
        workflow = _WORKFLOW_POR_CODIGO.get(codigo, "WORKFLOW_OPERATIVO")
        prioridad = int(_PRIORIDAD_WORKFLOW.get(workflow, 99))
        items.append(
            {
                "codigo": codigo,
                "paso": str(paso.get("nombre") or codigo),
                "workflow": workflow,
                "prioridad": prioridad,
                "requiere_confirmacion": bool(paso.get("requiere_confirmacion")),
                "modifica_datos": bool(paso.get("modifica_datos")),
            }
        )
    items.sort(key=lambda x: (x["prioridad"], x["codigo"]))
    return items


def _riesgos_desde_resultado(resultado: Dict[str, Any]) -> List[Dict[str, Any]]:
    salida: List[Dict[str, Any]] = []
    detalle_raw = resultado.get("detalle") or {}
    detalle = dict(detalle_raw) if isinstance(detalle_raw, dict) else {}

    propuesta_produccion = dict(detalle.get("propuesta_produccion_integrada") or {})
    for riesgo in list(propuesta_produccion.get("riesgos") or []):
        if isinstance(riesgo, dict):
            salida.append(
                {
                    "workflow": "PRODUCCION_INTELIGENTE",
                    "tipo": str(riesgo.get("tipo") or "riesgo"),
                    "nivel": str(riesgo.get("nivel") or "medio"),
                    "mensaje": str(riesgo.get("mensaje") or ""),
                }
            )

    propuesta_compras = dict(detalle.get("propuesta_compra_integrada") or {})
    for aviso in list(propuesta_compras.get("alertas") or []):
        salida.append(
            {
                "workflow": "COMPRAS_INTELIGENTES",
                "tipo": "alerta_compra",
                "nivel": "medio",
                "mensaje": str(aviso),
            }
        )

    for aviso in list(propuesta_produccion.get("advertencias") or []):
        salida.append(
            {
                "workflow": "PRODUCCION_INTELIGENTE",
                "tipo": "advertencia",
                "nivel": "medio",
                "mensaje": str(aviso),
            }
        )

    return salida


def _codigo_pendiente(item: Dict[str, Any]) -> str:
    return str(item.get("codigo") or item.get("id_paso") or "")


def _recomendaciones_ejecutivas(
    pendientes: List[Dict[str, Any]],
    riesgos: List[Dict[str, Any]],
    workflows: List[Dict[str, Any]],
) -> List[str]:
    recomendaciones: List[str] = []
    if any(bool(p.get("modifica_datos")) for p in pendientes):
        recomendaciones.append("Confirmar explícitamente los pasos críticos antes de cualquier escritura real.")
    if any(str(r.get("workflow") or "") == "PRODUCCION_INTELIGENTE" for r in riesgos):
        recomendaciones.append("Revisar riesgos de Producción Inteligente y ajustar secuencia antes de ejecutar cambios reales.")
    if any(str(w.get("workflow") or "") == "COMPRAS_INTELIGENTES" for w in workflows):
        recomendaciones.append("Usar COMPRAS_PREPARAR solo en modo propuesta y validar stock/proveedores antes de confirmar pedidos.")
    if not recomendaciones:
        recomendaciones.append("Mantener ejecución en modo seguro y confirmar solo cuando los datos operativos estén verificados.")
    return recomendaciones


def _deduplicar_textos(items: List[str]) -> List[str]:
    vistos = set()
    salida: List[str] = []
    for item in items:
        t = str(item or "").strip()
        if not t:
            continue
        k = t.lower()
        if k in vistos:
            continue
        vistos.add(k)
        salida.append(t)
    return salida


def _evento_ya_creado(datos_evento: Dict[str, Any]) -> bool:
    return bool(str(datos_evento.get("id") or "").strip())


def _pendiente_visible_en_ux(pendiente: Dict[str, Any], datos_evento: Dict[str, Any]) -> bool:
    codigo = str(pendiente.get("codigo") or "")
    if codigo == "EVENTO_CREAR" and _evento_ya_creado(datos_evento):
        return False
    return True


def _pendientes_operativos(pendientes: List[Dict[str, Any]], datos_evento: Dict[str, Any]) -> List[str]:
    frases: List[str] = []
    for p in pendientes:
        if not _pendiente_visible_en_ux(p, datos_evento):
            continue
        codigo = str(p.get("codigo") or "")
        frase = _PENDIENTE_POR_CODIGO.get(codigo)
        if frase:
            frases.append(presentar_accion_ejecutiva(codigo or frase))
            continue

        paso = str(p.get("paso") or "").strip()
        if paso:
            frases.append(presentar_accion_ejecutiva(paso))
    return _deduplicar_textos(frases)


def _mensaje_riesgo_natural(riesgo: Dict[str, Any]) -> str:
    workflow = str(riesgo.get("workflow") or "")
    tipo = str(riesgo.get("tipo") or "riesgo")
    mensaje = str(riesgo.get("mensaje") or "").strip()

    if tipo == "confirmaciones_pendientes":
        return "Existe riesgo operativo porque hay acciones pendientes de confirmación antes de escribir datos reales."
    if workflow == "PRODUCCION_INTELIGENTE" and mensaje:
        return f"Existe riesgo de retraso en Producción porque {mensaje.rstrip('.')} .".replace(" .", ".")
    if workflow == "COMPRAS_INTELIGENTES" and mensaje:
        return f"Existe riesgo en Compras porque {mensaje.rstrip('.')} .".replace(" .", ".")
    if mensaje:
        return f"Riesgo detectado en {workflow or 'workflow operativo'}: {mensaje.rstrip('.')} .".replace(" .", ".")
    return f"Riesgo detectado en {workflow or 'workflow operativo'} ({tipo})."


def _riesgos_operativos(riesgos: List[Dict[str, Any]], pendientes: List[Dict[str, Any]]) -> List[str]:
    codigos_pendientes = {str(p.get("codigo") or "") for p in pendientes}
    concretos: List[str] = []

    if "MENU_ASOCIAR" in codigos_pendientes:
        concretos.append("Mientras el menú no esté completo no se puede calcular correctamente la producción ni las compras.")
    if any(c in codigos_pendientes for c in {"PRODUCCION_PLAN", "PLANNING_GENERAR", "RECURSOS_REVISAR"}):
        concretos.append("Todavía no existe una planificación de cocina para este evento.")
    if "COMPRAS_PREPARAR" in codigos_pendientes:
        concretos.append("La propuesta de compras aún no ha sido revisada.")

    base = [_mensaje_riesgo_natural(r) for r in riesgos]
    return _deduplicar_textos(concretos + base)


def _estado_general(pendientes: List[Dict[str, Any]], riesgos: List[Dict[str, Any]]) -> str:
    if not pendientes and not riesgos:
        return "El evento está correctamente preparado."

    niveles = {str(r.get("nivel") or "").lower() for r in riesgos}
    if "alto" in niveles or "critico" in niveles or "crítico" in niveles:
        return "El evento presenta incidencias relevantes."

    if pendientes:
        return "Faltan elementos importantes antes de comenzar."

    return "El evento presenta incidencias relevantes."


def _prioridad_inmediata(
    *,
    pendientes: List[Dict[str, Any]],
    workflows: List[Dict[str, Any]],
    riesgos: List[Dict[str, Any]],
) -> Dict[str, str]:
    workflow_por_codigo = {str(w.get("codigo") or ""): str(w.get("workflow") or "WORKFLOW_OPERATIVO") for w in workflows}
    pendientes_con_prioridad: List[Dict[str, Any]] = []
    for p in pendientes:
        codigo = str(p.get("codigo") or "")
        wf = workflow_por_codigo.get(codigo, "WORKFLOW_OPERATIVO")
        prioridad = int(_PRIORIDAD_WORKFLOW.get(wf, 99))
        pendientes_con_prioridad.append({"codigo": codigo, "workflow": wf, "prioridad": prioridad})

    if pendientes_con_prioridad:
        pendientes_con_prioridad.sort(key=lambda x: (int(x.get("prioridad") or 99), str(x.get("codigo") or "")))
        primero = pendientes_con_prioridad[0]
        wf = str(primero.get("workflow") or "WORKFLOW_OPERATIVO")
        titulo = presentar_accion_ejecutiva(_TITULO_WORKFLOW.get(wf, "Revisar workflow operativo"))
        justificacion = "Es el bloque pendiente más prioritario del flujo y condiciona las siguientes acciones."
        if wf == "PREPARACION_EVENTO":
            justificacion = "Sin el menú no es posible cerrar correctamente Producción y Compras."
        elif wf == "PRODUCCION_INTELIGENTE":
            justificacion = "Sin la planificación de cocina no se puede coordinar la ejecución del evento."
        elif wf == "COMPRAS_INTELIGENTES":
            justificacion = "Sin revisar compras no se puede asegurar el aprovisionamiento del evento."

        return {
            "workflow": wf,
            "titulo": titulo,
            "justificacion": justificacion,
        }

    if riesgos:
        riesgo = dict(riesgos[0] or {})
        wf = str(riesgo.get("workflow") or "WORKFLOW_OPERATIVO")
        return {
            "workflow": wf,
            "titulo": presentar_accion_ejecutiva(_TITULO_WORKFLOW.get(wf, "Resolver incidencias")),
            "justificacion": "No hay pendientes críticos, pero existe un riesgo detectado que requiere atención inmediata.",
        }

    return {
        "workflow": "GOBERNANZA",
        "titulo": "Mantener seguimiento operativo",
        "justificacion": "No hay pendientes ni riesgos relevantes en este momento.",
    }


def _recomendaciones_operativas(
    prioridad: Dict[str, str],
    pendientes: List[Dict[str, Any]],
    workflows: List[Dict[str, Any]],
) -> List[str]:
    recomendaciones: List[str] = []
    titulo_prioridad = presentar_accion_ejecutiva(str(prioridad.get("titulo") or "Revisar operación"))
    recomendaciones.append(f"{titulo_prioridad}.")

    workflow_por_codigo = {str(w.get("codigo") or ""): str(w.get("workflow") or "WORKFLOW_OPERATIVO") for w in workflows}
    workflow_ordenado: List[str] = []
    for p in pendientes:
        wf = workflow_por_codigo.get(str(p.get("codigo") or ""), "WORKFLOW_OPERATIVO")
        workflow_ordenado.append(wf)
    workflow_ordenado.sort(key=lambda x: (int(_PRIORIDAD_WORKFLOW.get(x, 99)), x))

    otros = [wf for wf in workflow_ordenado if presentar_accion_ejecutiva(_TITULO_WORKFLOW.get(wf, "")) != titulo_prioridad]
    otros_titulos = _deduplicar_textos([
        presentar_accion_ejecutiva(_TITULO_WORKFLOW.get(wf, ""))
        for wf in otros
        if _TITULO_WORKFLOW.get(wf, "")
    ])
    recomendaciones.extend([f"{_sin_punto(t)}." for t in otros_titulos[:2]])

    recomendaciones.append(f"{presentar_accion_ejecutiva('Validar Stock')}.")
    return _deduplicar_textos(recomendaciones)


def _sin_punto(texto: str) -> str:
    return str(texto or "").strip().rstrip(".")


def _normalizar_texto(texto: str) -> str:
    t = str(texto or "").strip().lower()
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return " ".join(t.split())


def presentar_accion_ejecutiva(codigo_o_nombre: str) -> str:
    base = str(codigo_o_nombre or "").strip()
    if not base:
        return "Acción operativa pendiente"

    norm = _normalizar_texto(base)
    key = norm.replace(" ", "_")

    if key in _PRESENTACION_ACCIONES:
        return _PRESENTACION_ACCIONES[key]
    if norm in _PRESENTACION_ACCIONES:
        return _PRESENTACION_ACCIONES[norm]
    return base.rstrip(".")


def _codigos_pendientes(resultado: Dict[str, Any]) -> List[str]:
    pendientes = list(resultado.get("pendientes") or [])
    codigos = [str(p.get("codigo") or "") for p in pendientes if str(p.get("codigo") or "").strip()]
    return _deduplicar_textos(codigos)


def _prioridad_codigo(resultado: Dict[str, Any]) -> str:
    prioridad = dict(resultado.get("prioridad_inmediata") or {})
    wf = str(prioridad.get("workflow") or "").strip()
    if wf == "PREPARACION_EVENTO":
        return "MENU_ASOCIAR"
    if wf == "PRODUCCION_INTELIGENTE":
        return "PRODUCCION_PLAN"
    if wf == "COMPRAS_INTELIGENTES":
        return "COMPRAS_PREPARAR"
    if wf == "STOCK_OPERATIVO":
        return "STOCK_REVISAR"
    return ""


def _deps_desbloqueadas(codigo: str) -> List[str]:
    deps = list(_DEPENDENCIAS_POR_CODIGO.get(codigo, []))
    return [presentar_accion_ejecutiva(x) for x in deps]


def _es_paso_completado(resultado: Dict[str, Any], codigo: str) -> bool:
    flujo = dict(resultado.get("flujo") or {})
    pasos = list(flujo.get("pasos") or [])
    for paso in pasos:
        if str(paso.get("codigo") or "") != codigo:
            continue
        estado = str(paso.get("estado") or "").lower()
        if estado in {"completado", "preparado_modo_seguro", "rechazado", "cancelado"}:
            return True
    return False


def _ordenar_codigos_plan(codigos: List[str], codigo_prioridad: str) -> List[str]:
    dedup = _deduplicar_textos(codigos)
    conocidos = [c for c in dedup if c in _ORDEN_PLAN_CODIGO]
    conocidos.sort(key=lambda x: (_ORDEN_PLAN_CODIGO.get(x, 99), x))
    if codigo_prioridad and codigo_prioridad in conocidos:
        conocidos = [codigo_prioridad] + [c for c in conocidos if c != codigo_prioridad]
    return conocidos[:5]


def _motivo_plan_evento(codigo: str, resultado: Dict[str, Any]) -> str:
    if codigo in _MOTIVO_PLAN_EVENTO:
        return _MOTIVO_PLAN_EVENTO[codigo]

    riesgos = [str(x) for x in list(resultado.get("riesgos_operativos") or []) if str(x).strip()]
    if riesgos:
        return f"reduce este riesgo actual: {_sin_punto(riesgos[0]).lower()}."
    return "mantiene el flujo operativo en orden."


def _motivo_plan_restaurante(codigo: str, resultado: Dict[str, Any]) -> str:
    if codigo in _MOTIVO_PLAN_RESTAURANTE:
        return _MOTIVO_PLAN_RESTAURANTE[codigo]

    riesgo = str(dict(resultado.get("resumen_restaurante") or {}).get("riesgo_principal") or "").strip()
    if riesgo and "no hay incidencias" not in riesgo.lower():
        return f"ayuda a contener este riesgo: {_sin_punto(riesgo).lower()}."
    return "mantiene el día operativo bajo control."


def _pasos_plan_evento(resultado: Dict[str, Any]) -> List[Dict[str, Any]]:
    evento = dict(resultado.get("evento") or {})
    pendientes = list(resultado.get("pendientes") or [])
    codigo_prioridad = _prioridad_codigo(resultado)

    codigos: List[str] = []
    for item in pendientes:
        codigo = str(item.get("codigo") or "").strip()
        if not codigo:
            continue
        if not _pendiente_visible_en_ux({"codigo": codigo}, evento):
            continue
        if _es_paso_completado(resultado, codigo):
            continue
        codigos.append(codigo)

    codigos_ordenados = _ordenar_codigos_plan(codigos, codigo_prioridad)
    pasos: List[Dict[str, Any]] = []
    for idx, codigo in enumerate(codigos_ordenados, start=1):
        pasos.append(
            {
                "orden": idx,
                "accion": _sin_punto(presentar_accion_ejecutiva(codigo)),
                "motivo": _motivo_plan_evento(codigo, resultado),
                "codigo_origen": codigo,
            }
        )
    return pasos


def _pasos_plan_restaurante(resultado: Dict[str, Any]) -> List[Dict[str, Any]]:
    rest = dict(resultado.get("resumen_restaurante") or {})
    prioridad = dict(rest.get("prioridad_dia") or {})
    produccion = dict(rest.get("produccion") or {})
    compras = dict(rest.get("compras") or {})
    stock = dict(rest.get("stock") or {})

    codigos: List[str] = []
    codigo_principal = str(prioridad.get("codigo") or "").strip()
    if codigo_principal and codigo_principal != "SIN_INCIDENCIAS":
        codigos.append(codigo_principal)
    if int(produccion.get("pendientes") or 0) > 0:
        codigos.append("PRODUCCION_PLAN")
    if int(compras.get("propuestas_pendientes") or 0) > 0:
        codigos.append("COMPRAS_PREPARAR")
    if int(stock.get("incidencias_abiertas") or 0) > 0:
        codigos.append("STOCK_REVISAR")

    codigos_ordenados = _ordenar_codigos_plan(codigos, codigo_principal)
    pasos: List[Dict[str, Any]] = []
    for idx, codigo in enumerate(codigos_ordenados, start=1):
        pasos.append(
            {
                "orden": idx,
                "accion": _sin_punto(presentar_accion_ejecutiva(codigo)),
                "motivo": _motivo_plan_restaurante(codigo, resultado),
                "codigo_origen": codigo,
            }
        )
    return pasos


def _generar_plan_operativo_desde_resultado(resultado: Dict[str, Any], tipo_plan: Optional[str] = None) -> Dict[str, Any]:
    tipo = str(tipo_plan or "").strip().lower()
    if not tipo:
        tipo = "restaurante" if bool(resultado.get("resumen_restaurante")) else "evento"

    if tipo == "restaurante":
        pasos = _pasos_plan_restaurante(resultado)
    else:
        pasos = _pasos_plan_evento(resultado)
        tipo = "evento"

    if pasos:
        prioridad_principal = str(pasos[0].get("accion") or "Acción operativa prioritaria")
        mensaje_cierre = "Cuando completes estos pasos, vuelve a pedirme un análisis para actualizar la prioridad."
    else:
        prioridad_principal = "Sin acciones operativas pendientes"
        mensaje_cierre = "No hay acciones operativas pendientes en este momento.\n\nPuedes pedirme un resumen del restaurante o revisar los próximos eventos."

    return {
        "estado": "plan_operativo_generado",
        "tipo_plan": tipo,
        "prioridad_principal": prioridad_principal,
        "pasos": pasos,
        "mensaje_cierre": mensaje_cierre,
        "datos_reales_modificados": False,
    }


def explicar_impacto_operativo(resultado: Dict[str, Any], intencion: str) -> str:
    resumen_rest = dict(resultado.get("resumen_restaurante") or {})
    prioridad = dict(resultado.get("prioridad_inmediata") or resumen_rest.get("prioridad_dia") or {})
    riesgos_operativos = [str(x) for x in list(resultado.get("riesgos_operativos") or []) if str(x).strip()]
    codigos_pendientes = set(_codigos_pendientes(resultado))
    codigo_prioridad = _prioridad_codigo(resultado) or str(prioridad.get("codigo") or "")
    titulo_prioridad = presentar_accion_ejecutiva(str(prioridad.get("titulo") or prioridad.get("mensaje") or codigo_prioridad or "la prioridad actual")).rstrip(".")

    if intencion == EXEC_INTENCION_MOTIVO_PRIORIDAD:
        deps = _deps_desbloqueadas(codigo_prioridad)
        if deps:
            deps_txt = " y ".join([d.lower() for d in deps[:2]])
            return f"{titulo_prioridad} es la prioridad porque {deps_txt} dependen de ello."
        motivo = str(prioridad.get("justificacion") or prioridad.get("motivo") or "Es el siguiente bloque que más trabajo desbloquea.")
        return f"{titulo_prioridad} es la prioridad porque {motivo[0].lower() + motivo[1:] if len(motivo) > 1 else motivo.lower()}"

    if intencion == EXEC_INTENCION_BLOQUEO_PRODUCCION:
        if "MENU_ASOCIAR" in codigos_pendientes:
            return "La producción está bloqueada porque el menú del evento todavía no está completo."
        if any(c in codigos_pendientes for c in {"PRODUCCION_PLAN", "PLANNING_GENERAR", "RECURSOS_REVISAR"}):
            return "La producción sigue pendiente porque todavía no existe una planificación de cocina cerrada."
        return "No se detecta un bloqueo operativo directo sobre Producción en este momento."

    if intencion == EXEC_INTENCION_IMPACTO_COMPRAS:
        lineas = [
            "La propuesta de compras seguirá pendiente.",
            "No se detecta un bloqueo inmediato de producción, pero aumenta el riesgo de no disponer de ingredientes a tiempo si el evento está próximo.",
        ]
        return "\n\n".join(lineas)

    if intencion == EXEC_INTENCION_IMPACTO_PRODUCCION:
        if any(c in codigos_pendientes for c in {"PRODUCCION_PLAN", "PLANNING_GENERAR", "RECURSOS_REVISAR"}):
            return "Si no preparas Producción, seguirá pendiente la planificación de cocina y se retrasa la coordinación del evento."
        return "Producción no aparece como bloqueo inmediato ahora mismo, pero conviene mantenerla sincronizada con menú y compras."

    if intencion == EXEC_INTENCION_DESBLOQUEO:
        deps = _deps_desbloqueadas(codigo_prioridad)
        if deps:
            lineas = [f"{titulo_prioridad} desbloquea:", ""]
            lineas.extend([f"• {d.lower()};" for d in deps[:3]])
            return "\n".join(lineas)
        return f"{titulo_prioridad} es el siguiente paso que desbloquea más trabajo operativo."

    if intencion == EXEC_INTENCION_IMPACTO_GENERAL:
        if riesgos_operativos:
            return f"Si no se actúa ahora, se mantiene este riesgo principal: {riesgos_operativos[0]}"
        return "Si no se actúa ahora, las tareas pendientes se mantendrán abiertas y no se desbloquearán los siguientes pasos del flujo."

    return "No hay impacto operativo adicional que explicar con la información disponible."


def detectar_intencion_executive(texto: str) -> Optional[str]:
    norm = _normalizar_texto(texto)
    if not norm:
        return None

    if any(x in norm for x in ["analiza el evento actual", "analizar el evento actual"]):
        return EXEC_INTENCION_ANALISIS
    if any(x in norm for x in ["que falta", "que falta para este evento", "que queda pendiente", "que nos queda"]):
        return EXEC_INTENCION_PENDIENTES
    if any(x in norm for x in ["que hago ahora paso a paso", "hazme un plan", "dime el orden de trabajo", "que deberia hacer primero y despues", "dame un plan operativo", "organiza las tareas pendientes"]):
        return EXEC_INTENCION_PLAN_OPERATIVO
    if any(x in norm for x in ["cual es el plan de hoy", "organiza el dia", "que hago hoy"]):
        return EXEC_INTENCION_PLAN_DIA
    if any(x in norm for x in ["que es lo mas urgente", "que hago ahora", "que hago primero", "que prioridad tengo"]):
        return EXEC_INTENCION_PRIORIDAD
    if any(x in norm for x in ["que riesgos hay", "hay algun problema", "hay incidencias"]):
        return EXEC_INTENCION_RIESGOS
    if any(x in norm for x in ["que me recomiendas", "que deberia hacer", "que harias tu"]):
        return EXEC_INTENCION_RECOMENDACIONES
    if any(x in norm for x in ["que pasa si no hago esto"]):
        return EXEC_INTENCION_IMPACTO_GENERAL
    if any(x in norm for x in ["que pasa si no preparo produccion"]):
        return EXEC_INTENCION_IMPACTO_PRODUCCION
    if any(x in norm for x in ["que pasa si dejo compras para manana"]):
        return EXEC_INTENCION_IMPACTO_COMPRAS
    if any(x in norm for x in ["que bloquea la produccion"]):
        return EXEC_INTENCION_BLOQUEO_PRODUCCION
    if any(x in norm for x in ["que desbloquea mas trabajo"]):
        return EXEC_INTENCION_DESBLOQUEO
    if any(x in norm for x in ["por que es la prioridad"]):
        return EXEC_INTENCION_MOTIVO_PRIORIDAD
    if any(x in norm for x in [
        "como esta hoy el restaurante",
        "como esta el restaurante",
        "situacion del restaurante",
        "estado general",
        "resumen del restaurante",
        "resumen del dia",
        "que tengo hoy",
        "panorama general",
    ]):
        return EXEC_INTENCION_RESTAURANTE
    if any(x in norm for x in ["hazme un resumen", "resumen ejecutivo", "resumen"]):
        return EXEC_INTENCION_RESUMEN
    return None


def _leer_json_lista(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [dict(x) for x in data] if isinstance(data, list) else []


def _evento_a_dict(evento: Any) -> Dict[str, Any]:
    if isinstance(evento, dict):
        return dict(evento)
    return {
        "id": getattr(evento, "id", ""),
        "nombre": getattr(evento, "nombre", ""),
        "fecha": getattr(evento, "fecha", ""),
        "estado": getattr(evento, "estado", ""),
        "pax": getattr(evento, "pax", None),
    }


def _eventos_activos_desde_core(core: Any) -> List[Dict[str, Any]]:
    try:
        eventos = list(core.eventos.listar_eventos())
    except Exception:
        return []

    cerrados = {"finalizado", "facturado", "cancelado", "cerrado"}
    activos: List[Dict[str, Any]] = []
    for e in eventos:
        d = _evento_a_dict(e)
        estado = str(d.get("estado") or "pendiente").lower()
        if estado in cerrados:
            continue
        activos.append(d)
    activos.sort(key=lambda x: (str(x.get("fecha") or "9999-99-99"), str(x.get("nombre") or "").lower()))
    return activos


def _contar_planes_pendientes(base_dir: Path) -> int:
    planes = _leer_json_lista(base_dir / "DATOS" / "db" / "planes_produccion.json")
    cerrados = {"finalizado", "completado", "cerrado", "cancelado"}
    return len([p for p in planes if str(p.get("estado") or "pendiente").lower() not in cerrados])


def _contar_propuestas_pendientes(base_dir: Path, core: Any = None) -> int:
    if core is not None:
        try:
            propuestas = list(core.compras.listar_propuestas_compra(solo_pendientes=True))
            return len(propuestas)
        except Exception:
            pass
    propuestas = _leer_json_lista(base_dir / "DATOS" / "db" / "compras_propuestas.json")
    return len([p for p in propuestas if str(p.get("estado") or "pendiente").lower() in {"pendiente", "preparada", "propuesta"}])


def _contar_incidencias_stock(base_dir: Path) -> int:
    stock = _leer_json_lista(base_dir / "DATOS" / "db" / "stock_inicial.json")
    if not stock:
        return 0
    total = 0
    for item in stock:
        try:
            actual = float(item.get("stock_actual") or 0)
            minimo = float(item.get("stock_minimo") or 0)
        except (TypeError, ValueError):
            continue
        if actual < minimo:
            total += 1
    return total


def _nombre_evento(evento: Dict[str, Any]) -> str:
    return str(evento.get("nombre") or evento.get("id") or "No hay eventos activos.").strip()


def _prioridad_del_dia(
    *,
    evento_prioritario: Dict[str, Any],
    planes_pendientes: int,
    propuestas_pendientes: int,
    incidencias_stock: int,
) -> Dict[str, str]:
    nombre = _nombre_evento(evento_prioritario)
    menu_incompleto = bool(evento_prioritario.get("menu_incompleto", False))

    if menu_incompleto:
        return {
            "codigo": "MENU_ASOCIAR",
            "mensaje": f"Completar el menú del evento {nombre} para desbloquear Producción.",
            "motivo": f"El evento {nombre} todavía no tiene el menú completamente preparado.",
        }
    if planes_pendientes > 0:
        return {
            "codigo": "PRODUCCION_PLAN",
            "mensaje": "Generar la planificación de cocina.",
            "motivo": "Todavía no existe una planificación de cocina cerrada para hoy.",
        }
    if propuestas_pendientes > 0:
        return {
            "codigo": "COMPRAS_PREPARAR",
            "mensaje": "Revisar la propuesta de compras del evento.",
            "motivo": "Hay propuestas de compra pendientes de revisión.",
        }
    if incidencias_stock > 0:
        return {
            "codigo": "STOCK_REVISAR",
            "mensaje": "Comprobar que hay stock suficiente.",
            "motivo": "Hay incidencias de stock abiertas que pueden bloquear la operativa.",
        }
    return {
        "codigo": "SIN_INCIDENCIAS",
        "mensaje": "Sin incidencias operativas críticas hoy.",
        "motivo": "No hay bloqueos relevantes en eventos, producción, compras ni stock.",
    }


def _riesgo_principal(
    *,
    evento_prioritario: Dict[str, Any],
    planes_pendientes: int,
    propuestas_pendientes: int,
    incidencias_stock: int,
) -> str:
    nombre = _nombre_evento(evento_prioritario)
    if bool(evento_prioritario.get("menu_incompleto", False)):
        return f"El evento {nombre} todavía no tiene el menú completamente preparado."
    if planes_pendientes > 0:
        return "Todavía no existe una planificación de cocina para hoy."
    if propuestas_pendientes > 0:
        return "La propuesta de compras aún no ha sido revisada."
    if incidencias_stock > 0:
        return "Hay incidencias de stock abiertas que pueden afectar al servicio."
    return "No hay incidencias graves detectadas."


def _render_resumen_restaurante(resultado: Dict[str, Any]) -> str:
    rest = dict(resultado.get("resumen_restaurante") or {})
    eventos = dict(rest.get("eventos") or {})
    produccion = dict(rest.get("produccion") or {})
    compras = dict(rest.get("compras") or {})
    stock = dict(rest.get("stock") or {})
    prioridad = dict(rest.get("prioridad_dia") or {})
    riesgo = str(rest.get("riesgo_principal") or "No hay información disponible.")

    lineas = [
        "HOST AI EXECUTIVE",
        "",
        "RESUMEN DEL RESTAURANTE",
        "",
        "Eventos",
        f"• Eventos activos: {eventos.get('activos', 'No hay información disponible.')}",
        f"• Evento prioritario: {eventos.get('prioritario_nombre') or 'No hay información disponible.'}",
        "",
        "Producción",
        f"• Planificaciones pendientes: {produccion.get('pendientes', 'No hay información disponible.')}",
        "",
        "Compras",
        f"• Propuestas pendientes: {compras.get('propuestas_pendientes', 'No hay información disponible.')}",
        "",
        "Stock",
        f"• Incidencias abiertas: {stock.get('incidencias_abiertas', 'No hay información disponible.')}",
        "",
        "Prioridad del día",
        f"\"{prioridad.get('mensaje') or 'No hay información disponible.'}\"",
        "",
        "Riesgo principal",
        f"\"{riesgo}\"",
        "",
        "Modo seguro",
        "datos_reales_modificados=False",
    ]
    return "\n".join(lineas)


def _render_conversacional_restaurante(resultado: Dict[str, Any]) -> str:
    rest = dict(resultado.get("resumen_restaurante") or {})
    eventos = dict(rest.get("eventos") or {})
    compras = dict(rest.get("compras") or {})
    stock = dict(rest.get("stock") or {})
    prioridad = dict(rest.get("prioridad_dia") or {})
    riesgo = str(rest.get("riesgo_principal") or "No hay información disponible.")

    activos = int(eventos.get("activos") or 0)
    nombre_evento = str(eventos.get("prioritario_nombre") or "").strip()
    propuestas = int(compras.get("propuestas_pendientes") or 0)
    incidencias = int(stock.get("incidencias_abiertas") or 0)

    lineas = ["Hoy la situación general es estable."]
    if activos <= 0:
        lineas.append("No hay eventos activos.")
    else:
        lineas.append(f"Hay {activos} evento{'s' if activos != 1 else ''} activo{'s' if activos != 1 else ''}.")

    if nombre_evento:
        lineas.append(f"La prioridad del día es {str(prioridad.get('mensaje') or '').strip().rstrip('.') if prioridad.get('mensaje') else f'completar la operativa del evento {nombre_evento}'}.")
    else:
        lineas.append(f"La prioridad del día es {str(prioridad.get('mensaje') or 'mantener seguimiento operativo').strip().rstrip('.')}.")

    if propuestas > 0:
        lineas.append("Todavía queda revisar la propuesta de compras.")
    if incidencias > 0:
        lineas.append(f"Hay {incidencias} incidencia{'s' if incidencias != 1 else ''} de stock abiertas.")
    else:
        lineas.append("No hay incidencias graves de stock.")

    if riesgo and riesgo != "No hay incidencias graves detectadas.":
        lineas.append(f"Riesgo principal: {riesgo}")
    lineas.append("Modo seguro activado.")
    return "\n".join(lineas)


def _render_analisis_completo(resultado: Dict[str, Any]) -> str:
    pendientes = list(resultado.get("pendientes_operativos") or [])
    riesgos = list(resultado.get("riesgos_operativos") or [])
    recomendaciones = list(resultado.get("recomendaciones_operativas") or resultado.get("recomendaciones") or [])
    ejecutados = list(resultado.get("workflows_ejecutados") or [])
    evento = dict(resultado.get("evento") or {})
    prioridad = dict(resultado.get("prioridad_inmediata") or {})
    estado_general = str(resultado.get("estado_general") or "")
    resumen_lineas = list(resultado.get("resumen_ejecutivo_lineas") or [])

    lineas = [
        "HOST AI EXECUTIVE",
        f"Evento: {evento.get('tipo') or 'evento'} | Pax: {evento.get('personas') or evento.get('pax') or 'pendiente'} | Fecha: {evento.get('fecha') or 'pendiente'}",
        f"Estado general: {estado_general}",
        f"Prioridad inmediata: {prioridad.get('titulo') or 'Seguimiento operativo'}",
        f"Justificación: {prioridad.get('justificacion') or 'Sin incidencias críticas.'}",
        f"Workflows preparados: {len(ejecutados)}",
        "Pendientes:",
    ]

    if pendientes:
        lineas.extend([f"• {p}" for p in pendientes])
    else:
        lineas.append("• No hay pendientes operativos.")

    lineas.append("Riesgos:")
    if riesgos:
        lineas.extend([f"• {r}" for r in riesgos])
    else:
        lineas.append("• No se detectan riesgos críticos.")

    lineas.append("Recomendaciones:")
    if recomendaciones:
        lineas.extend([f"• {rec}" for rec in recomendaciones])
    else:
        lineas.append("• Mantener seguimiento operativo en modo seguro.")

    lineas.append("Resumen ejecutivo:")
    if resumen_lineas:
        lineas.extend([f"• {ln}" for ln in resumen_lineas[:5]])
    else:
        lineas.append(f"• {str(resultado.get('resumen_ejecutivo') or '').strip()}")
    lineas.append("Modo seguro: datos_reales_modificados=False")
    return "\n".join(lineas)


def _render_pendientes(resultado: Dict[str, Any]) -> str:
    pendientes = list(resultado.get("pendientes_operativos") or [])
    prioridad = dict(resultado.get("prioridad_inmediata") or {})
    if not pendientes:
        return "No quedan tareas pendientes en este momento."

    lineas = ["Todavía quedan estas tareas:", ""]
    lineas.extend([f"• {presentar_accion_ejecutiva(p)}." for p in pendientes])
    titulo = _sin_punto(presentar_accion_ejecutiva(str(prioridad.get("titulo") or "")))
    if titulo:
        lineas.append("")
        continuidad = "la planificación de cocina"
        if "menú" in titulo.lower() or "menu" in titulo.lower():
            continuidad = "la planificación de cocina"
        elif "planificación de cocina" in titulo.lower() or "planificacion de cocina" in titulo.lower():
            continuidad = "la revisión de compras"
        elif "compras" in titulo.lower():
            continuidad = "la validación final de stock"
        lineas.append(f"Cuando completes {_sin_punto(titulo).lower()} podré continuar con {continuidad}.")
    return "\n".join(lineas)


def _render_prioridad(resultado: Dict[str, Any]) -> str:
    prioridad = dict(resultado.get("prioridad_inmediata") or {})
    titulo = _sin_punto(presentar_accion_ejecutiva(str(prioridad.get("titulo") or "seguimiento operativo")))
    justificacion = str(prioridad.get("justificacion") or "Es el siguiente paso operativo más importante.")
    return "\n".join(
        [
            f"Ahora mismo la prioridad es {titulo.lower()}.",
            "",
            "Motivo:",
            justificacion,
        ]
    )


def _render_riesgos(resultado: Dict[str, Any]) -> str:
    riesgos = list(resultado.get("riesgos_operativos") or [])
    if not riesgos:
        return "No se detectan riesgos operativos críticos en este momento."
    if len(riesgos) == 1:
        return "\n".join(["He detectado un riesgo operativo.", "", riesgos[0]])

    lineas = ["He detectado estos riesgos operativos:", ""]
    lineas.extend([f"• {r}" for r in riesgos])
    return "\n".join(lineas)


def _render_recomendaciones(resultado: Dict[str, Any]) -> str:
    recomendaciones = list(resultado.get("recomendaciones_operativas") or resultado.get("recomendaciones") or [])
    if not recomendaciones:
        return "Mi recomendación es mantener el modo seguro y revisar el siguiente paso pendiente."

    lineas = ["Mi recomendación es:", ""]
    for idx, rec in enumerate(recomendaciones, start=1):
        lineas.append(f"{idx}. {presentar_accion_ejecutiva(str(rec))}.")
    return "\n".join(lineas)


def _render_resumen(resultado: Dict[str, Any]) -> str:
    lineas = [str(x) for x in list(resultado.get("resumen_ejecutivo_lineas") or []) if str(x).strip()]
    if not lineas:
        base = str(resultado.get("resumen_ejecutivo") or "No hay resumen ejecutivo disponible.").strip()
        return base
    return "\n".join(lineas[:5])


def _render_plan_operativo(resultado: Dict[str, Any]) -> str:
    plan = dict(resultado.get("plan_operativo") or _generar_plan_operativo_desde_resultado(resultado))
    pasos = list(plan.get("pasos") or [])
    if not pasos:
        return "\n".join(
            [
                str(plan.get("mensaje_cierre") or "No hay acciones operativas pendientes en este momento."),
                "",
                "Modo seguro activado.",
                "datos_reales_modificados=False",
            ]
        )

    lineas = ["PLAN OPERATIVO RECOMENDADO", ""]
    for paso in pasos:
        orden = int(paso.get("orden") or 0)
        accion = _sin_punto(str(paso.get("accion") or "Acción pendiente"))
        motivo = _sin_punto(str(paso.get("motivo") or "mantiene el flujo operativo"))
        lineas.append(f"{orden}. {accion}.")
        lineas.append(f"   Motivo: {motivo}.")
        lineas.append("")

    lineas.append(str(plan.get("mensaje_cierre") or "Cuando completes estos pasos, vuelve a pedirme un análisis para actualizar la prioridad."))
    lineas.append("")
    lineas.append("Modo seguro activado.")
    lineas.append("datos_reales_modificados=False")
    return "\n".join(lineas)


def formatear_respuesta_executive_conversacional(resultado: Dict[str, Any], intencion: str) -> str:
    if not bool(resultado.get("ok")):
        return str(resultado.get("resumen_ejecutivo") or "No se pudo completar el análisis ejecutivo.")

    if intencion == EXEC_INTENCION_RESTAURANTE:
        return _render_conversacional_restaurante(resultado)

    if intencion in {EXEC_INTENCION_PLAN_OPERATIVO, EXEC_INTENCION_PLAN_DIA}:
        return _render_plan_operativo(resultado)

    if intencion in {
        EXEC_INTENCION_IMPACTO_GENERAL,
        EXEC_INTENCION_IMPACTO_PRODUCCION,
        EXEC_INTENCION_IMPACTO_COMPRAS,
        EXEC_INTENCION_BLOQUEO_PRODUCCION,
        EXEC_INTENCION_DESBLOQUEO,
        EXEC_INTENCION_MOTIVO_PRIORIDAD,
    }:
        return explicar_impacto_operativo(resultado, intencion)

    if intencion == EXEC_INTENCION_PENDIENTES:
        return _render_pendientes(resultado)
    if intencion == EXEC_INTENCION_PRIORIDAD:
        return _render_prioridad(resultado)
    if intencion == EXEC_INTENCION_RIESGOS:
        return _render_riesgos(resultado)
    if intencion == EXEC_INTENCION_RECOMENDACIONES:
        return _render_recomendaciones(resultado)
    if intencion == EXEC_INTENCION_RESUMEN:
        return _render_resumen(resultado)
    return _render_analisis_completo(resultado)


def _resumen_ejecutivo_lineas(
    *,
    estado_general: str,
    prioridad_inmediata: Dict[str, str],
    pendientes_operativos: List[str],
    riesgos_operativos: List[str],
) -> List[str]:
    lineas = [estado_general]
    if pendientes_operativos:
        p = ", ".join(_sin_punto(presentar_accion_ejecutiva(x)) for x in pendientes_operativos[:2])
        lineas.append(f"Pendientes principales: {p}.")
    else:
        lineas.append("No hay pendientes operativos por confirmar.")

    if riesgos_operativos:
        lineas.append(f"Riesgo principal: {_sin_punto(riesgos_operativos[0])}.")
    else:
        lineas.append("No se detectan riesgos críticos.")

    lineas.append(f"Prioridad inmediata: {presentar_accion_ejecutiva(str(prioridad_inmediata.get('titulo') or 'seguimiento operativo'))}.")
    lineas.append("Modo seguro activado (datos_reales_modificados=False).")
    return lineas[:5]


class HostAIExecutive:
    """Coordinador ejecutivo determinista sobre el workflow canónico.

    No calcula negocio ni ejecuta motores de forma directa. Solo coordina el
    flujo existente y agrega resultados ejecutivos en modo seguro.
    """

    VERSION = "2.0"

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.orquestador_flujo = OrquestadorFlujoOperativo(self.base_dir)

    def generar_plan_operativo(self, resultado: Dict[str, Any], tipo_plan: Optional[str] = None) -> Dict[str, Any]:
        return _generar_plan_operativo_desde_resultado(resultado, tipo_plan=tipo_plan)

    def analizar_evento_para_plan(self, datos_evento: Dict[str, Any], core: Any = None) -> Dict[str, Any]:
        datos = _normalizar_evento(datos_evento)
        evento_id = str(datos.get("id") or "").strip()

        menu_incompleto = False
        if core is not None and evento_id:
            try:
                resumen_evento = core.eventos.resumen_ejecutivo(evento_id)
                avisos = list((resumen_evento or {}).get("avisos") or [])
                menu_incompleto = any(a in {"Faltan servicios.", "Hay servicios sin pases.", "Hay pases sin recetas."} for a in avisos)
            except Exception:
                menu_incompleto = False

        planes_pendientes = _contar_planes_pendientes(self.base_dir)
        propuestas_pendientes = _contar_propuestas_pendientes(self.base_dir, core=core)
        incidencias_stock = _contar_incidencias_stock(self.base_dir)

        codigos_pendientes: List[str] = []
        if not evento_id:
            codigos_pendientes.append("EVENTO_CREAR")
        if menu_incompleto:
            codigos_pendientes.append("MENU_ASOCIAR")
        if planes_pendientes > 0:
            codigos_pendientes.append("PRODUCCION_PLAN")
        if propuestas_pendientes > 0:
            codigos_pendientes.append("COMPRAS_PREPARAR")
        if incidencias_stock > 0:
            codigos_pendientes.append("STOCK_REVISAR")

        codigos_pendientes = _deduplicar_textos(codigos_pendientes)
        pendientes = [
            {
                "codigo": c,
                "paso": c,
                "motivo": "pendiente_plan",
                "modifica_datos": True,
            }
            for c in codigos_pendientes
        ]
        workflows = [
            {
                "codigo": c,
                "paso": c,
                "workflow": _WORKFLOW_POR_CODIGO.get(c, "WORKFLOW_OPERATIVO"),
                "prioridad": int(_PRIORIDAD_WORKFLOW.get(_WORKFLOW_POR_CODIGO.get(c, "WORKFLOW_OPERATIVO"), 99)),
                "requiere_confirmacion": True,
                "modifica_datos": True,
            }
            for c in codigos_pendientes
        ]

        riesgos: List[Dict[str, Any]] = []
        riesgos_operativos = _riesgos_operativos(riesgos, pendientes)
        estado_general = _estado_general(pendientes, riesgos)
        prioridad_inmediata = _prioridad_inmediata(
            pendientes=pendientes,
            workflows=workflows,
            riesgos=riesgos,
        )
        pendientes_operativos = _pendientes_operativos(pendientes, datos)
        recomendaciones_operativas = _recomendaciones_operativas(prioridad_inmediata, pendientes, workflows)
        resumen_lineas = _resumen_ejecutivo_lineas(
            estado_general=estado_general,
            prioridad_inmediata=prioridad_inmediata,
            pendientes_operativos=pendientes_operativos,
            riesgos_operativos=riesgos_operativos,
        )

        return {
            "ok": True,
            "estado": "analisis_plan_evento",
            "evento": datos,
            "pendientes": pendientes,
            "riesgos": riesgos,
            "recomendaciones": [],
            "estado_general": estado_general,
            "prioridad_inmediata": prioridad_inmediata,
            "pendientes_operativos": pendientes_operativos,
            "riesgos_operativos": riesgos_operativos,
            "recomendaciones_operativas": recomendaciones_operativas,
            "resumen_ejecutivo_lineas": resumen_lineas,
            "workflows_ejecutados": [],
            "workflows_priorizados": workflows,
            "resumen_ejecutivo": self._resumen_ejecutivo(lineas=resumen_lineas),
            "datos_reales_modificados": False,
        }

    def analizar_restaurante(self, core: Any = None) -> Dict[str, Any]:
        eventos_activos = _eventos_activos_desde_core(core) if core is not None else _leer_json_lista(self.base_dir / "DATOS" / "db" / "eventos.json")

        evento_prioritario = eventos_activos[0] if eventos_activos else {}
        menu_incompleto = False
        if core is not None and evento_prioritario:
            try:
                resumen_evento = core.eventos.resumen_ejecutivo(str(evento_prioritario.get("id") or ""))
                avisos = list((resumen_evento or {}).get("avisos") or [])
                menu_incompleto = any(a in {"Faltan servicios.", "Hay servicios sin pases.", "Hay pases sin recetas."} for a in avisos)
            except Exception:
                menu_incompleto = False
        evento_prioritario = dict(evento_prioritario or {})
        evento_prioritario["menu_incompleto"] = bool(menu_incompleto)

        planes_pendientes = _contar_planes_pendientes(self.base_dir)
        propuestas_pendientes = _contar_propuestas_pendientes(self.base_dir, core=core)
        incidencias_stock = _contar_incidencias_stock(self.base_dir)

        prioridad_dia = _prioridad_del_dia(
            evento_prioritario=evento_prioritario,
            planes_pendientes=planes_pendientes,
            propuestas_pendientes=propuestas_pendientes,
            incidencias_stock=incidencias_stock,
        )
        riesgo = _riesgo_principal(
            evento_prioritario=evento_prioritario,
            planes_pendientes=planes_pendientes,
            propuestas_pendientes=propuestas_pendientes,
            incidencias_stock=incidencias_stock,
        )

        resumen_restaurante = {
            "eventos": {
                "activos": len(eventos_activos),
                "prioritario_nombre": _nombre_evento(evento_prioritario) if evento_prioritario else "No hay eventos activos.",
                "prioritario_id": str(evento_prioritario.get("id") or "") if evento_prioritario else "",
            },
            "produccion": {
                "pendientes": planes_pendientes,
            },
            "compras": {
                "propuestas_pendientes": propuestas_pendientes,
            },
            "stock": {
                "incidencias_abiertas": incidencias_stock,
            },
            "prioridad_dia": prioridad_dia,
            "riesgo_principal": riesgo,
        }

        return {
            "ok": True,
            "estado": "resumen_restaurante_generado",
            "resumen_restaurante": resumen_restaurante,
            "resumen_ejecutivo_restaurante": _render_resumen_restaurante({"resumen_restaurante": resumen_restaurante}),
            "datos_reales_modificados": False,
        }

    def analizar_evento(self, datos_evento: Dict[str, Any]) -> Dict[str, Any]:
        datos = _normalizar_evento(datos_evento)
        inicio = self.orquestador_flujo.iniciar_flujo_operativo(datos)
        if not inicio.get("ok"):
            return {
                "ok": False,
                "estado": "analisis_incompleto",
                "evento": datos,
                "pendientes": list(inicio.get("datos", {}).get("faltan") or []),
                "riesgos": [
                    {
                        "workflow": "PREPARACION_EVENTO",
                        "tipo": "dato_faltante",
                        "nivel": "alto",
                        "mensaje": str(inicio.get("mensaje") or "Faltan datos para iniciar el workflow."),
                    }
                ],
                "workflows_ejecutados": [],
                "resumen_ejecutivo": "No se pudo iniciar el análisis ejecutivo por falta de datos mínimos.",
                "datos_reales_modificados": False,
            }

        flujo = dict(inicio.get("flujo") or {})
        workflows = _detecta_workflows(flujo)

        pre = self.orquestador_flujo.ejecutar_flujo_seguro(flujo, confirmar=False)
        flujo_actual = dict(pre.get("flujo") or flujo)

        resultados = list(pre.get("resultados") or [])
        ejecutados: List[Dict[str, Any]] = []
        codigos_ejecutados = set()

        for item in resultados:
            codigo = str(item.get("codigo") or "")
            if codigo:
                codigos_ejecutados.add(codigo)
                ejecutados.append(
                    {
                        "workflow": _WORKFLOW_POR_CODIGO.get(codigo, "WORKFLOW_OPERATIVO"),
                        "codigo": codigo,
                        "estado": str(item.get("estado") or "ejecutado"),
                        "modifica_datos": False,
                        "datos_reales_modificados": bool(item.get("modifico_datos_reales", False)),
                    }
                )

        pendientes_pre = list(pre.get("pendientes_confirmacion") or [])
        codigos_pendientes = {_codigo_pendiente(p) for p in pendientes_pre if _codigo_pendiente(p)}

        # Solo se ejecutan pasos no críticos (sin modificación de datos) para conservar modo seguro.
        for wf in workflows:
            codigo = str(wf.get("codigo") or "")
            if not codigo or codigo in codigos_ejecutados:
                continue
            if codigo not in codigos_pendientes:
                continue
            if bool(wf.get("modifica_datos")):
                continue

            paso = self.orquestador_flujo.ejecutar_paso_seguro(flujo_actual, codigo_paso=codigo)
            flujo_actual = dict(paso.get("flujo") or flujo_actual)
            paso_info = dict(paso.get("paso") or {})
            paso_resultado = dict(paso_info.get("resultado") or {})
            codigos_ejecutados.add(codigo)
            ejecutados.append(
                {
                    "workflow": str(wf.get("workflow") or "WORKFLOW_OPERATIVO"),
                    "codigo": codigo,
                    "estado": str(paso_info.get("estado") or paso.get("estado") or "ejecutado"),
                    "modifica_datos": bool(wf.get("modifica_datos")),
                    "datos_reales_modificados": bool(paso_resultado.get("datos_reales_modificados", False)),
                }
            )

            detalle = dict(paso_resultado.get("detalle") or {})
            if detalle:
                resultados.append({
                    "codigo": codigo,
                    "estado": paso_info.get("estado") or paso.get("estado"),
                    "detalle": detalle,
                    "modifico_datos_reales": bool(paso_resultado.get("datos_reales_modificados", False)),
                })

        resultados_por_codigo: Dict[str, Dict[str, Any]] = {}
        for item in resultados:
            codigo_item = str(item.get("codigo") or "")
            if not codigo_item:
                continue
            detalle_raw = item.get("detalle")
            detalle = dict(detalle_raw) if isinstance(detalle_raw, dict) else {"texto": str(detalle_raw or "")}
            resultados_por_codigo[codigo_item] = {
                "estado": str(item.get("estado") or ""),
                "detalle": detalle,
                "datos_reales_modificados": bool(item.get("modifico_datos_reales", False)),
            }
        for paso in list(flujo_actual.get("pasos") or []):
            codigo_paso = str((paso or {}).get("codigo") or "")
            if codigo_paso and codigo_paso in resultados_por_codigo:
                paso["resultado"] = deepcopy(resultados_por_codigo[codigo_paso])

        pendientes_finales: List[Dict[str, Any]] = []
        for paso in list((flujo_actual.get("pasos") or [])):
            estado = str(paso.get("estado") or "")
            if estado in {"completado", "preparado_modo_seguro", "rechazado", "cancelado"}:
                continue
            if bool(paso.get("requiere_confirmacion")):
                pendientes_finales.append(
                    {
                        "codigo": str(paso.get("codigo") or ""),
                        "paso": str(paso.get("nombre") or ""),
                        "motivo": "requiere_confirmacion",
                        "modifica_datos": bool(paso.get("modifica_datos")),
                    }
                )

        riesgos: List[Dict[str, Any]] = []
        for resultado in resultados:
            riesgos.extend(_riesgos_desde_resultado(resultado))

        if pendientes_finales:
            riesgos.append(
                {
                    "workflow": "GOBERNANZA",
                    "tipo": "confirmaciones_pendientes",
                    "nivel": "medio",
                    "mensaje": "Existen acciones pendientes de confirmación explícita antes de cualquier escritura real.",
                }
            )

        modifica_real = any(bool(x.get("datos_reales_modificados", False)) for x in ejecutados)
        contexto = GestorContextoPermanente5410()

        recomendaciones = _recomendaciones_ejecutivas(pendientes_finales, riesgos, workflows)
        estado_general = _estado_general(pendientes_finales, riesgos)
        prioridad_inmediata = _prioridad_inmediata(
            pendientes=pendientes_finales,
            workflows=workflows,
            riesgos=riesgos,
        )
        pendientes_operativos = _pendientes_operativos(pendientes_finales, datos)
        riesgos_operativos = _riesgos_operativos(riesgos, pendientes_finales)
        recomendaciones_operativas = _recomendaciones_operativas(prioridad_inmediata, pendientes_finales, workflows)
        resumen_lineas = _resumen_ejecutivo_lineas(
            estado_general=estado_general,
            prioridad_inmediata=prioridad_inmediata,
            pendientes_operativos=pendientes_operativos,
            riesgos_operativos=riesgos_operativos,
        )

        resumen = self._resumen_ejecutivo(
            lineas=resumen_lineas,
        )

        flujo_salida = deepcopy(flujo_actual)
        flujo_salida["informe_ejecutivo"] = {
            "estado": "analisis_completo",
            "pendientes": deepcopy(pendientes_finales),
            "riesgos": deepcopy(riesgos),
            "workflows_priorizados": deepcopy(workflows),
            "workflows_ejecutados": deepcopy(ejecutados),
            "recomendaciones": deepcopy(recomendaciones),
            "estado_general": estado_general,
            "prioridad_inmediata": deepcopy(prioridad_inmediata),
            "pendientes_operativos": deepcopy(pendientes_operativos),
            "riesgos_operativos": deepcopy(riesgos_operativos),
            "recomendaciones_operativas": deepcopy(recomendaciones_operativas),
            "resumen_ejecutivo_lineas": deepcopy(resumen_lineas),
            "resumen_ejecutivo": resumen,
            "datos_reales_modificados": False,
        }

        contexto.activar_flujo(
            {
                "flujo_pendiente_confirmacion": bool(pendientes_finales),
                "datos_flujo": deepcopy(datos),
                "flujo": deepcopy(flujo_salida),
                "estado_conversacion": "pendiente_confirmacion" if pendientes_finales else "flujo_revisado_esperando_siguiente_accion",
            }
        )

        return {
            "ok": True,
            "estado": "analisis_completo",
            "evento": datos,
            "pendientes": pendientes_finales,
            "riesgos": riesgos,
            "recomendaciones": recomendaciones,
            "estado_general": estado_general,
            "prioridad_inmediata": prioridad_inmediata,
            "pendientes_operativos": pendientes_operativos,
            "riesgos_operativos": riesgos_operativos,
            "recomendaciones_operativas": recomendaciones_operativas,
            "resumen_ejecutivo_lineas": resumen_lineas,
            "workflows_ejecutados": ejecutados,
            "workflows_priorizados": workflows,
            "flujo": flujo_salida,
            "continuidad_conversacional": contexto.snapshot(),
            "resumen_ejecutivo": resumen,
            "datos_reales_modificados": bool(modifica_real),
        }

    @staticmethod
    def _resumen_ejecutivo(
        *,
        lineas: List[str],
    ) -> str:
        return "\n".join([str(x) for x in list(lineas or [])][:5])


__all__ = [
    "HostAIExecutive",
    "detectar_intencion_executive",
    "formatear_respuesta_executive_conversacional",
    "presentar_accion_ejecutiva",
    "explicar_impacto_operativo",
    "EXEC_INTENCION_ANALISIS",
    "EXEC_INTENCION_PENDIENTES",
    "EXEC_INTENCION_PRIORIDAD",
    "EXEC_INTENCION_RIESGOS",
    "EXEC_INTENCION_RECOMENDACIONES",
    "EXEC_INTENCION_RESUMEN",
    "EXEC_INTENCION_RESTAURANTE",
    "EXEC_INTENCION_IMPACTO_GENERAL",
    "EXEC_INTENCION_IMPACTO_PRODUCCION",
    "EXEC_INTENCION_IMPACTO_COMPRAS",
    "EXEC_INTENCION_BLOQUEO_PRODUCCION",
    "EXEC_INTENCION_DESBLOQUEO",
    "EXEC_INTENCION_MOTIVO_PRIORIDAD",
    "EXEC_INTENCION_PLAN_OPERATIVO",
    "EXEC_INTENCION_PLAN_DIA",
]
