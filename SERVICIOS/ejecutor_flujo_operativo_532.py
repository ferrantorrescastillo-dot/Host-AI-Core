"""Host AI 5.3.2 - Ejecutor inteligente del flujo operativo.

Ejecuta de forma segura un flujo generado por 5.3.1. En esta primera versión,
las acciones críticas quedan simuladas/pendientes para evitar modificar datos sin
confirmaciones específicas de cada motor.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Dict, List

from SERVICIOS.modelo_flujo_operativo import (
    actualizar_estado_general,
    obtener_paso,
    obtener_paso_actual,
    registrar_error,
    registrar_historial,
    registrar_resultado,
    seleccionar_paso,
)


def _leer_json(ruta: Path) -> Any:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _leer_json_lista(ruta: Path) -> List[Dict[str, Any]]:
    data = _leer_json(ruta)
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("items", "registros", "eventos", "menus"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def _normalizar_texto(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _hora_a_minutos(valor: str) -> int | None:
    try:
        horas, minutos = str(valor or "").split(":", 1)
        return int(horas) * 60 + int(minutos)
    except Exception:
        return None


def _minutos_a_hora(valor: int) -> str:
    total = max(0, int(valor))
    horas = (total // 60) % 24
    minutos = total % 60
    return f"{horas:02d}:{minutos:02d}"


def _evento_desde_datos(base_dir: Path, datos_evento: Dict[str, Any]) -> Dict[str, Any]:
    eventos = _leer_json_lista(base_dir / "DATOS" / "db" / "eventos.json")
    candidatos = [
        str(datos_evento.get("id_evento") or "").strip(),
        str(datos_evento.get("id") or "").strip(),
        str(datos_evento.get("evento") or "").strip(),
        str(datos_evento.get("nombre") or "").strip(),
    ]
    candidatos_norm = {_normalizar_texto(x) for x in candidatos if x}
    for evento in eventos:
        if str(evento.get("id") or "").strip() in candidatos:
            return dict(evento)
        nombre = _normalizar_texto(evento.get("nombre"))
        if nombre and nombre in candidatos_norm:
            return dict(evento)
    fecha = str(datos_evento.get("fecha") or "").strip()
    pax = int(datos_evento.get("personas") or datos_evento.get("pax") or 0)
    menu = _normalizar_texto(datos_evento.get("menu"))
    compatibles = []
    compatibles_sin_menu = []
    for evento in eventos:
        if fecha and str(evento.get("fecha") or "").strip() != fecha:
            continue
        if pax and int(evento.get("pax") or evento.get("personas") or 0) != pax:
            continue
        compatibles_sin_menu.append(dict(evento))
        if menu:
            recetas_evento = " ".join(
                _normalizar_texto(receta)
                for servicio in list(evento.get("servicios") or [])
                for pase in list(servicio.get("pases") or [])
                for receta in list(pase.get("recetas") or [])
            )
            nombre_evento = _normalizar_texto(evento.get("nombre"))
            if menu not in recetas_evento and menu not in nombre_evento:
                continue
        compatibles.append(dict(evento))
    if len(compatibles) == 1:
        return compatibles[0]
    if not compatibles and len(compatibles_sin_menu) == 1:
        return compatibles_sin_menu[0]
    return {}


def _indice_fichas_produccion(base_dir: Path) -> Dict[str, Dict[str, Any]]:
    data = _leer_json(base_dir / "DATOS" / "db" / "fichas_produccion_reales.json")
    fichas = []
    if isinstance(data, dict):
        fichas = list(data.get("fichas") or [])
    salida: Dict[str, Dict[str, Any]] = {}
    for ficha in fichas:
        if not isinstance(ficha, dict):
            continue
        nombre = _normalizar_texto(ficha.get("receta"))
        if nombre:
            salida[nombre] = dict(ficha)
    return salida


def _leer_planes_produccion(base_dir: Path) -> List[Dict[str, Any]]:
    return _leer_json_lista(base_dir / "DATOS" / "db" / "planes_produccion.json")


def _estado_tarea_produccion(valor: str) -> str:
    estado = _normalizar_texto(valor)
    if estado in {"finalizada", "preparado", "finalizado", "ok"}:
        return "preparado"
    if estado in {"en_produccion", "en proceso", "en_preparacion", "en preparacion", "planificado", "revisar", "parcial", "pendiente"}:
        return "parcial"
    return "desconocido"


def _estado_produccion_existente(planes: List[Dict[str, Any]], evento: Dict[str, Any], receta: str) -> str:
    evento_id = str(evento.get("id") or "").strip()
    evento_nombre = _normalizar_texto(evento.get("nombre"))
    receta_norm = _normalizar_texto(receta)
    for plan in planes:
        if not isinstance(plan, dict):
            continue
        plan_evento_id = str(plan.get("evento_id") or "").strip()
        plan_evento_nombre = _normalizar_texto(plan.get("evento") or plan.get("nombre_evento"))
        if evento_id and plan_evento_id and plan_evento_id != evento_id:
            continue
        if evento_nombre and plan_evento_nombre and plan_evento_nombre != evento_nombre:
            continue
        tareas = list(plan.get("tareas") or [])
        for tarea in tareas:
            receta_tarea = _normalizar_texto(tarea.get("receta") or tarea.get("titulo") or "")
            if receta_norm and receta_tarea and receta_norm not in receta_tarea and receta_tarea not in receta_norm:
                continue
            estado = _estado_tarea_produccion(str(tarea.get("estado") or plan.get("estado") or ""))
            if estado != "desconocido":
                return estado
        estado_plan = _estado_tarea_produccion(str(plan.get("estado") or ""))
        if estado_plan != "desconocido":
            return estado_plan
    return "desconocido"


def _extraer_elaboraciones_evento(evento: Dict[str, Any], datos_evento: Dict[str, Any]) -> List[Dict[str, Any]]:
    elaboraciones: List[Dict[str, Any]] = []
    for servicio in list(evento.get("servicios") or []):
        servicio_nombre = str(servicio.get("nombre") or "Servicio").strip() or "Servicio"
        hora_servicio = str(servicio.get("hora_inicio") or evento.get("hora_inicio") or datos_evento.get("hora_servicio") or "").strip()
        for pase in list(servicio.get("pases") or []):
            pase_nombre = str(pase.get("nombre") or "Pase").strip() or "Pase"
            for receta in list(pase.get("recetas") or []):
                ref = str(receta or "").strip()
                if ref:
                    elaboraciones.append({
                        "receta_ref": ref,
                        "servicio": servicio_nombre,
                        "pase": pase_nombre,
                        "hora_servicio": hora_servicio,
                    })
    if elaboraciones:
        return elaboraciones

    for campo in ("menu", "receta"):
        ref = str(evento.get(campo) or datos_evento.get(campo) or "").strip()
        if ref:
            elaboraciones.append({
                "receta_ref": ref,
                "servicio": str(evento.get("nombre") or "Servicio único"),
                "pase": "principal",
                "hora_servicio": str(evento.get("hora_inicio") or datos_evento.get("hora_servicio") or ""),
            })
    return elaboraciones


def _riesgo(tipo: str, nivel: str, mensaje: str, accion_recomendada: str) -> Dict[str, Any]:
    return {
        "tipo": tipo,
        "nivel": nivel,
        "mensaje": mensaje,
        "accion_recomendada": accion_recomendada,
    }


def _nivel_riesgo_elaboracion(riesgos: List[str]) -> str:
    texto = " ".join(str(x or "").lower() for x in riesgos)
    if any(token in texto for token in ("sin_margen", "ficha_no_validada", "escandallo_ausente", "stock:", "duracion_no_disponible")):
        return "alta"
    if riesgos:
        return "media"
    return "baja"


def _dependencias_desde_ficha(ficha: Dict[str, Any]) -> List[str]:
    dependencias: List[str] = []
    for fase in list(ficha.get("fases") or []):
        dependencia = str((fase or {}).get("dependencia") or "").strip()
        if dependencia and dependencia not in dependencias:
            dependencias.append(dependencia)
    return dependencias


def _propuesta_produccion_desde_evento(datos_evento: Dict[str, Any], contexto: Dict[str, Any]) -> Dict[str, Any]:
    from SERVICIOS.produccion_automatica_evento_556f import ProduccionAutomaticaEvento556F

    base_dir = Path(str(contexto.get("base_dir") or Path.cwd())).resolve()
    evento = _evento_desde_datos(base_dir, datos_evento)
    evento_ref = str(evento.get("id") or evento.get("nombre") or datos_evento.get("id_evento") or datos_evento.get("evento") or datos_evento.get("nombre") or datos_evento.get("menu") or "").strip()

    resultado_motor = ProduccionAutomaticaEvento556F(base_dir).planificar_evento(
        evento_ref,
        integrar_con_compras=False,
        generar_pedidos_sugeridos=False,
    ) if evento_ref else {
        "estado": "EVENTO_NO_LOCALIZADO",
        "ok": False,
        "evento": {},
        "planes_receta": [],
        "cruces_stock": [],
        "bloqueos": [],
        "compras_propuestas": [],
        "datos_reales_modificados": False,
        "solo_lectura": True,
    }

    evento_info_raw = resultado_motor.get("evento") or {}
    evento_info = dict(evento_info_raw) if isinstance(evento_info_raw, dict) else {}
    if not evento and evento_info:
        evento = {
            "id": evento_info.get("id"),
            "nombre": evento_info.get("nombre"),
            "fecha": evento_info.get("fecha"),
            "pax": evento_info.get("pax"),
            "servicios": [],
        }

    elaboraciones_evento = _extraer_elaboraciones_evento(evento, datos_evento)
    fichas = _indice_fichas_produccion(base_dir)
    planes_existentes = _leer_planes_produccion(base_dir)
    bloqueos_motor = list(resultado_motor.get("bloqueos") or [])
    plan_diario = dict(resultado_motor.get("plan_diario") or {})

    planes_por_receta = {
        _normalizar_texto(plan.get("receta")): dict(plan)
        for plan in list(resultado_motor.get("planes_receta") or [])
        if isinstance(plan, dict) and plan.get("receta")
    }
    recetas_por_nombre = {
        _normalizar_texto(receta.get("nombre")): dict(receta)
        for receta in list(resultado_motor.get("recetas") or [])
        if isinstance(receta, dict) and receta.get("nombre")
    }
    recetas_por_codigo = {
        _normalizar_texto(receta.get("codigo")): dict(receta)
        for receta in list(resultado_motor.get("recetas") or [])
        if isinstance(receta, dict) and receta.get("codigo")
    }
    cruces_por_receta = {
        _normalizar_texto(cruce.get("receta")): dict(cruce)
        for cruce in list(resultado_motor.get("cruces_stock") or [])
        if isinstance(cruce, dict) and cruce.get("receta")
    }

    riesgos: List[Dict[str, Any]] = []
    advertencias: List[str] = []
    elaboraciones: List[Dict[str, Any]] = []
    datos_incompletos = 0
    sugerir_compras = False
    vista_riesgos = set()

    for item in elaboraciones_evento:
        ref = str(item.get("receta_ref") or "").strip()
        ref_norm = _normalizar_texto(ref)
        receta = recetas_por_codigo.get(ref_norm) or recetas_por_nombre.get(ref_norm)
        receta_nombre = str((receta or {}).get("nombre") or ref or "Elaboración").strip()
        plan = planes_por_receta.get(_normalizar_texto(receta_nombre))
        cruce = cruces_por_receta.get(_normalizar_texto(receta_nombre), {})
        ficha = fichas.get(_normalizar_texto(receta_nombre), {})
        bloqueos_item = [
            b for b in bloqueos_motor
            if _normalizar_texto(b.get("receta_ref") or b.get("receta") or "") in {_normalizar_texto(ref), _normalizar_texto(receta_nombre)}
        ]

        minutos_activos = int((plan or {}).get("minutos_activos") or 0)
        minutos_pasivos = int((plan or {}).get("minutos_pasivos") or 0)
        duracion_total = minutos_activos + minutos_pasivos
        hora_servicio = str(item.get("hora_servicio") or datos_evento.get("hora_servicio") or "").strip()
        hora_servicio_min = _hora_a_minutos(hora_servicio)
        inicio_recomendado = ""
        fin_recomendado = hora_servicio
        prioridad = "baja"
        recursos = sorted({str(x) for tarea in list((plan or {}).get("tareas") or []) for x in (tarea.get("recursos") or []) if str(x).strip()})
        riesgos_item: List[str] = []
        dependencias = _dependencias_desde_ficha(ficha)
        dependencias_imposibles: List[str] = []

        if duracion_total > 0 and hora_servicio_min is not None:
            inicio_calc = hora_servicio_min - duracion_total
            inicio_recomendado = _minutos_a_hora(inicio_calc)
            if inicio_calc < 0:
                clave = ("tiempo", receta_nombre, "sin_margen")
                if clave not in vista_riesgos:
                    riesgos.append(_riesgo(
                        "tiempo",
                        "alto",
                        f"{receta_nombre}: la duración estimada supera el margen disponible antes del servicio {hora_servicio}.",
                        "Revisar ficha validada y considerar dividir la producción o adelantar preparación.",
                    ))
                    vista_riesgos.add(clave)
                riesgos_item.append("sin_margen_antes_servicio")
                prioridad = "alta"
            elif inicio_calc < 8 * 60:
                clave = ("tiempo", receta_nombre, "inicio_adelantado")
                if clave not in vista_riesgos:
                    riesgos.append(_riesgo(
                        "tiempo",
                        "medio",
                        f"{receta_nombre}: el inicio recomendado ({inicio_recomendado}) queda antes de una jornada tipo 08:00.",
                        "Validar jornada real, fichas y secuencia operativa antes de ejecutar.",
                    ))
                    vista_riesgos.add(clave)
                riesgos_item.append("inicio_fuera_jornada_tipo")
                prioridad = "media"
            advertencias.append(
                f"{receta_nombre}: inicio/fin recomendados estimados a partir de duración validada y hora de servicio {hora_servicio}."
            )
        else:
            datos_incompletos += 1
            clave = ("dato_faltante", receta_nombre, "duracion")
            if clave not in vista_riesgos:
                riesgos.append(_riesgo(
                    "dato_faltante",
                    "alto",
                    f"{receta_nombre}: no hay duración utilizable para calcular la propuesta temporal.",
                    "Validar ficha de producción o completar tiempos antes de ejecutar la producción.",
                ))
                vista_riesgos.add(clave)
            riesgos_item.append("duracion_no_disponible")
            prioridad = "alta"

        if not plan or not plan.get("puede_planificar"):
            datos_incompletos += 1
            clave = ("dato_faltante", receta_nombre, "ficha")
            if clave not in vista_riesgos:
                riesgos.append(_riesgo(
                    "dato_faltante",
                    "alto",
                    f"{receta_nombre}: no existe una ficha de producción validada reutilizable para planificar con seguridad.",
                    "Crear o validar la ficha antes de ejecutar Producción; no marcar como preparada.",
                ))
                vista_riesgos.add(clave)
            riesgos_item.append("ficha_no_validada")
            prioridad = "alta"

        for bloqueo in bloqueos_item:
            tipo_bloqueo = str(bloqueo.get("tipo") or "")
            if tipo_bloqueo == "RECETA_NO_LOCALIZADA":
                clave = ("dato_faltante", receta_nombre, "escandallo")
                if clave not in vista_riesgos:
                    riesgos.append(_riesgo(
                        "dato_faltante",
                        "alto",
                        f"{receta_nombre}: la receta del evento no existe en escandallos canónicos.",
                        "Registrar o asociar el escandallo antes de preparar Producción.",
                    ))
                    vista_riesgos.add(clave)
                riesgos_item.append("escandallo_ausente")
                prioridad = "alta"

        if dependencias:
            elaboraciones_existentes = {
                _normalizar_texto(str(item.get("receta_ref") or ""))
                for item in elaboraciones_evento
            }
            for dependencia in dependencias:
                dep_norm = _normalizar_texto(dependencia)
                if dep_norm and dep_norm not in elaboraciones_existentes and dep_norm not in {_normalizar_texto(receta_nombre), _normalizar_texto(ref)}:
                    dependencias_imposibles.append(dependencia)
                    clave = ("dependencia", receta_nombre, dependencia)
                    if clave not in vista_riesgos:
                        riesgos.append(_riesgo(
                            "dependencia",
                            "medio",
                            f"{receta_nombre}: la dependencia '{dependencia}' no se puede enlazar con una elaboración conocida del evento.",
                            "Revisar la ficha y enlazar la secuencia antes de ejecutar la producción.",
                        ))
                        vista_riesgos.add(clave)
            if dependencias_imposibles:
                prioridad = "alta"
                riesgos_item.append("dependencias_imposibles")

        for incidencia in list((plan or {}).get("incidencias") or []):
            mensaje = str(incidencia.get("motivo") or "").strip()
            if not mensaje:
                continue
            gravedad = str(incidencia.get("gravedad") or "INFO").upper()
            nivel = "alto" if gravedad in {"ALTO", "CRITICO", "CRÍTICO"} else ("medio" if gravedad == "MEDIO" else "bajo")
            clave = ("dependencia", receta_nombre, mensaje)
            if clave not in vista_riesgos:
                riesgos.append(_riesgo(
                    "dependencia",
                    nivel,
                    f"{receta_nombre}: {mensaje}",
                    "Revisar secuencia real y dependencias antes de ejecutar la preparación.",
                ))
                vista_riesgos.add(clave)
            riesgos_item.append(mensaje)

        for linea in list((cruce or {}).get("lineas") or []):
            estado_stock = str(linea.get("estado") or "")
            faltante = float(linea.get("faltante") or 0)
            if faltante > 0 or estado_stock in {"ARTICULO_NO_LOCALIZADO", "ARTICULO_SIN_INVENTARIO", "UNIDAD_INCOMPATIBLE", "SIN_STOCK", "STOCK_INSUFICIENTE"}:
                sugerir_compras = True
                clave = ("stock", receta_nombre, str(linea.get("articulo_nombre") or linea.get("nombre") or ""), estado_stock)
                if clave not in vista_riesgos:
                    riesgos.append(_riesgo(
                        "stock",
                        "alto" if faltante > 0 or estado_stock in {"SIN_STOCK", "STOCK_INSUFICIENTE", "ARTICULO_NO_LOCALIZADO", "ARTICULO_SIN_INVENTARIO"} else "medio",
                        f"{receta_nombre}: falta stock de {linea.get('articulo_nombre') or linea.get('nombre')} ({estado_stock}).",
                        "No lanzar compras automáticamente; sugerir enlazar con COMPRAS_PREPARAR.",
                    ))
                    vista_riesgos.add(clave)
                riesgos_item.append(f"stock:{estado_stock}")
                prioridad = "alta"

        estado_actual = _estado_produccion_existente(planes_existentes, evento, receta_nombre)
        if estado_actual == "parcial":
            clave = ("dependencia", receta_nombre, "produccion_parcial")
            if clave not in vista_riesgos:
                riesgos.append(_riesgo(
                    "dependencia",
                    "medio",
                    f"{receta_nombre}: existe producción parcial previa para este evento y debe revisarse antes de continuar.",
                    "Cruzar la propuesta con el plan existente antes de marcar tareas como preparadas.",
                ))
                vista_riesgos.add(clave)
            riesgos_item.append("produccion_parcial_existente")
        elif estado_actual == "preparado":
            riesgos_item.append("produccion_preparada_existente")

        elaboraciones.append({
            "codigo": str((receta or {}).get("codigo") or ref or receta_nombre),
            "nombre": receta_nombre,
            "cantidad": float((plan or {}).get("objetivo") or evento_info.get("pax") or evento.get("pax") or datos_evento.get("personas") or 0),
            "unidad": str((plan or {}).get("unidad") or "personas"),
            "servicio": item.get("servicio") or "",
            "pase": item.get("pase") or "",
            "hora_servicio": hora_servicio,
            "duracion_estimada_min": duracion_total,
            "inicio_recomendado": inicio_recomendado,
            "fin_recomendado": fin_recomendado,
            "prioridad": prioridad,
            "dependencias": dependencias,
            "recursos": recursos,
            "estado_actual": estado_actual,
            "riesgos": riesgos_item,
            "nivel_riesgo": _nivel_riesgo_elaboracion(riesgos_item),
        })

    if not elaboraciones and resultado_motor.get("estado") == "EVENTO_NO_LOCALIZADO":
        riesgos.append(_riesgo(
            "dato_faltante",
            "alto",
            "No se ha podido localizar el evento real para construir una propuesta de producción segura.",
            "Verificar evento activo, nombre o ID antes de ejecutar PRODUCCION_PLAN.",
        ))
        datos_incompletos += 1

    if sugerir_compras:
        advertencias.append("Se detectaron faltantes: sugerir enlazar con COMPRAS_PREPARAR. No se ejecutan compras automáticamente.")

    if int(plan_diario.get("dias_necesarios") or 1) > 1:
        riesgos.append(_riesgo(
            "personal",
            "medio",
            f"La planificación diaria requiere {plan_diario.get('dias_necesarios')} jornadas para cubrir las elaboraciones propuestas.",
            "Revisar margen temporal y capacidad de equipo antes de ejecutar la producción.",
        ))
    if str(plan_diario.get("estado_plan") or "") == "ajustar":
        riesgos.append(_riesgo(
            "personal",
            "alto",
            "La carga activa estimada supera la capacidad diaria del equipo teórico.",
            "Reducir alcance, ampliar jornada o dividir elaboraciones antes de ejecutar.",
        ))

    orden_prioridad = {"alta": 0, "media": 1, "baja": 2}
    orden_riesgo = {"alta": 0, "media": 1, "baja": 2}
    elaboraciones.sort(key=lambda x: (
        _hora_a_minutos(str(x.get("hora_servicio") or "99:99")) if _hora_a_minutos(str(x.get("hora_servicio") or "")) is not None else 10 ** 6,
        _hora_a_minutos(str(x.get("inicio_recomendado") or "99:99")) if _hora_a_minutos(str(x.get("inicio_recomendado") or "")) is not None else 10 ** 6,
        len(list(x.get("dependencias") or [])),
        orden_prioridad.get(str(x.get("prioridad") or "baja"), 3),
        orden_riesgo.get(str(x.get("nivel_riesgo") or "baja"), 3),
        _normalizar_texto(x.get("nombre")),
    ))

    plan_trabajo = []
    for orden, elaboracion in enumerate(elaboraciones, start=1):
        plan_trabajo.append({
            "orden": orden,
            "accion": f"Preparar {elaboracion['nombre']} para {elaboracion['servicio']} / {elaboracion['pase']}",
            "inicio_recomendado": elaboracion.get("inicio_recomendado") or "",
            "fin_recomendado": elaboracion.get("fin_recomendado") or elaboracion.get("hora_servicio") or "",
            "motivo": f"Servicio {elaboracion.get('hora_servicio') or 'sin hora'}; prioridad {elaboracion.get('prioridad')}.",
        })

    duracion_total = sum(int(x.get("duracion_estimada_min") or 0) for x in elaboraciones)
    riesgos_altos = sum(1 for x in riesgos if str(x.get("nivel") or "") == "alto")
    riesgos_medios = sum(1 for x in riesgos if str(x.get("nivel") or "") == "medio")

    return {
        "modo": "seguro",
        "estado": "propuesta_produccion_preparada",
        "datos_reales_modificados": False,
        "evento_id": str(evento_info.get("id") or evento.get("id") or datos_evento.get("id_evento") or ""),
        "evento": {
            "nombre": str(evento_info.get("nombre") or evento.get("nombre") or datos_evento.get("evento") or datos_evento.get("nombre") or ""),
            "fecha": str(evento_info.get("fecha") or evento.get("fecha") or datos_evento.get("fecha") or ""),
            "pax": int(evento_info.get("pax") or evento.get("pax") or datos_evento.get("personas") or datos_evento.get("pax") or 0),
        },
        "elaboraciones": elaboraciones,
        "plan_trabajo": plan_trabajo,
        "riesgos": riesgos,
        "resumen": {
            "elaboraciones_totales": len(elaboraciones),
            "duracion_total_estimada_min": duracion_total,
            "riesgos_altos": riesgos_altos,
            "riesgos_medios": riesgos_medios,
            "datos_incompletos": datos_incompletos,
        },
        "advertencias": sorted(set(advertencias)),
        "banderas_seguridad": {
            "datos_reales_modificados": False,
            "no_modificar_produccion": True,
            "no_modificar_stock": True,
            "no_crear_movimientos": True,
            "no_asignar_personal_real": True,
        },
        "sugerir_compras_preparar": bool(sugerir_compras),
        "motor_reutilizado": {
            "servicio": "ProduccionAutomaticaEvento556F",
            "estado": resultado_motor.get("estado"),
            "solo_lectura": bool(resultado_motor.get("solo_lectura", True)),
            "datos_reales_modificados": bool(resultado_motor.get("datos_reales_modificados", False)),
        },
    }


def _stock_para_compras(base_dir: Path) -> Dict[str, float]:
    stock = _leer_json_lista(base_dir / "DATOS" / "db" / "stock_inicial.json")
    salida: Dict[str, float] = {}
    for item in stock:
        nombre = str(item.get("articulo") or item.get("nombre") or "").strip()
        if not nombre:
            continue
        salida[nombre] = float(item.get("stock_actual") or item.get("cantidad") or 0)
    return salida


def _menu_por_nombre(base_dir: Path, nombre_menu: str) -> Dict[str, Any]:
    menus = _leer_json_lista(base_dir / "DATOS" / "db" / "menus.json")
    buscado = str(nombre_menu or "").strip().lower()
    if buscado:
        for menu in menus:
            nombre = str(menu.get("nombre") or "").strip().lower()
            if nombre == buscado:
                return dict(menu)
    return dict(menus[0]) if menus else {}


def _propuesta_desde_menu(base_dir: Path, datos_evento: Dict[str, Any]) -> List[Dict[str, Any]]:
    from SERVICIOS.compras_evento_474 import calcular_necesidades_evento, comparar_con_stock

    menu = _menu_por_nombre(base_dir, str(datos_evento.get("menu") or ""))
    if not menu:
        return []
    evento_ctx = {
        "id_evento": datos_evento.get("id_evento") or datos_evento.get("id"),
        "nombre": datos_evento.get("evento") or datos_evento.get("nombre") or "evento",
        "personas": datos_evento.get("personas") or datos_evento.get("pax") or 0,
        "menus": [menu],
    }
    necesidades = calcular_necesidades_evento(evento_ctx, menu=menu)
    comparadas = comparar_con_stock(necesidades, stock=_stock_para_compras(base_dir))
    salida: List[Dict[str, Any]] = []
    for linea in comparadas:
        cantidad = float(linea.get("cantidad_a_comprar") or 0)
        if cantidad <= 0:
            continue
        salida.append(
            {
                "articulo_id": "",
                "articulo": linea.get("articulo"),
                "unidad": linea.get("unidad", "u"),
                "cantidad": round(cantidad, 4),
                "proveedor": linea.get("proveedor_preferente") or "Sin proveedor",
                "origen": "menu_recetas_stock",
            }
        )
    return salida


def _propuesta_desde_evento_produccion(base_dir: Path, datos_evento: Dict[str, Any]) -> Dict[str, Any]:
    from SERVICIOS.produccion_automatica_evento_556f import ProduccionAutomaticaEvento556F

    candidatos = [
        datos_evento.get("id_evento"),
        datos_evento.get("id"),
        datos_evento.get("evento"),
        datos_evento.get("nombre_evento"),
        datos_evento.get("nombre"),
        datos_evento.get("menu"),
    ]
    motor = ProduccionAutomaticaEvento556F(base_dir)
    for candidato in candidatos:
        ref = str(candidato or "").strip()
        if not ref:
            continue
        resultado = motor.planificar_evento(ref, integrar_con_compras=False, generar_pedidos_sugeridos=False)
        if resultado.get("estado") in {"EVENTO_NO_LOCALIZADO", "EVENTO_AMBIGUO"}:
            continue
        return resultado
    return {
        "estado": "EVENTO_NO_LOCALIZADO",
        "compras_propuestas": [],
        "datos_reales_modificados": False,
        "solo_lectura": True,
    }


def _fusionar_lineas_compra(lineas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[tuple[str, str], Dict[str, Any]] = {}
    for linea in lineas:
        articulo = str(linea.get("articulo") or "").strip()
        unidad = str(linea.get("unidad") or "u").strip() or "u"
        if not articulo:
            continue
        key = (articulo.casefold(), unidad.casefold())
        actual = merged.setdefault(
            key,
            {
                "articulo_id": str(linea.get("articulo_id") or ""),
                "articulo": articulo,
                "unidad": unidad,
                "cantidad": 0.0,
                "proveedor": str(linea.get("proveedor") or "Sin proveedor").strip() or "Sin proveedor",
                "origenes": [],
            },
        )
        actual["cantidad"] = round(float(actual["cantidad"]) + float(linea.get("cantidad") or 0), 4)
        origen = str(linea.get("origen") or "").strip()
        if origen and origen not in actual["origenes"]:
            actual["origenes"].append(origen)
        if not actual.get("articulo_id"):
            actual["articulo_id"] = str(linea.get("articulo_id") or "")
    return [x for x in merged.values() if float(x.get("cantidad") or 0) > 0]


def _generar_propuesta_compra_integrada(datos_evento: Dict[str, Any], contexto: Dict[str, Any]) -> Dict[str, Any]:
    base_dir = Path(str(contexto.get("base_dir") or Path.cwd())).resolve()

    evento_prod = _propuesta_desde_evento_produccion(base_dir, datos_evento)
    lineas_prod = []
    for item in evento_prod.get("compras_propuestas", []) or []:
        lineas_prod.append(
            {
                "articulo_id": item.get("articulo_id") or "",
                "articulo": item.get("articulo") or "",
                "unidad": item.get("unidad") or "u",
                "cantidad": float(item.get("cantidad") or 0),
                "proveedor": item.get("proveedor") or "Sin proveedor",
                "origen": "eventos_servicios_pases_recetas_escandallos_produccion_stock",
            }
        )

    lineas_menu = _propuesta_desde_menu(base_dir, datos_evento)
    propuestas = _fusionar_lineas_compra(lineas_prod + lineas_menu)

    return {
        "modo_seguro": True,
        "datos_reales_modificados": False,
        "no_crear_pedidos_reales": True,
        "no_modificar_stock": True,
        "no_modificar_proveedores": True,
        "no_modificar_produccion": True,
        "no_escribir_movimientos_reales": True,
        "fuentes_calculo": [
            "eventos",
            "servicios",
            "pases",
            "menu",
            "recetas",
            "escandallos",
            "produccion",
            "stock",
        ],
        "lineas": propuestas,
        "total_lineas_propuesta": len(propuestas),
        "evento_produccion": {
            "estado": evento_prod.get("estado"),
            "id_plan_automatico": evento_prod.get("id_plan_automatico", ""),
            "solo_lectura": bool(evento_prod.get("solo_lectura", True)),
            "datos_reales_modificados": bool(evento_prod.get("datos_reales_modificados", False)),
        },
    }


def _ejecutar_paso_simulado(paso: Dict[str, Any], datos: Dict[str, Any], contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
    codigo = paso.get("codigo")
    nombre = paso.get("nombre")
    requiere_confirmacion = bool(paso.get("requiere_confirmacion"))
    modifica_datos = bool(paso.get("modifica_datos"))

    if requiere_confirmacion and modifica_datos:
        estado = "pendiente_confirmacion_especifica"
        detalle = f"{nombre}: requiere confirmación antes de modificar datos reales."
    else:
        estado = "ok_simulado"
        detalle = f"{nombre}: validado en modo seguro."

    # Salidas operativas orientativas, no inventa datos de stock/precio reales.
    propuesta_compra: Dict[str, Any] | None = None
    if codigo == "STOCK_REVISAR":
        detalle = "Stock: revisión preparada. Para datos reales se debe conectar al inventario activo."
    elif codigo == "COMPRAS_PREPARAR":
        propuesta_compra = _generar_propuesta_compra_integrada(datos, contexto or {})
        detalle = (
            "Compras: propuesta integrada generada en modo seguro "
            f"({propuesta_compra.get('total_lineas_propuesta', 0)} líneas)."
        )
    elif codigo == "COSTES_CALCULAR":
        detalle = "Rentabilidad: cálculo preparado pendiente de escandallos/precios reales."
    elif codigo == "PRODUCCION_PLAN":
        propuesta_produccion = _propuesta_produccion_desde_evento(datos, contexto or {})
        detalle = (
            "Producción: propuesta operativa generada en modo seguro "
            f"({len(propuesta_produccion.get('elaboraciones') or [])} elaboraciones)."
        )

    salida = {
        "codigo": codigo,
        "nombre": nombre,
        "estado": estado,
        "detalle": detalle,
        "modo": "seguro",
        "modifico_datos": False,
        "datos_reales_modificados": False,
        "no_crear_pedidos_reales": True,
        "no_modificar_stock": True,
        "no_modificar_proveedores": True,
        "no_modificar_produccion": True,
        "no_escribir_movimientos_reales": True,
    }
    if propuesta_compra is not None:
        salida["propuesta_compra_integrada"] = propuesta_compra
    if codigo == "PRODUCCION_PLAN":
        salida["propuesta_produccion_integrada"] = propuesta_produccion
    return salida


def _puede_ejecutar_paso(paso: Dict[str, Any]) -> Dict[str, Any]:
    requiere_confirmacion = bool(paso.get("requiere_confirmacion"))
    confirmacion_estado = str(((paso.get("confirmacion") or {}).get("estado") or "").lower())
    estado_paso = str(paso.get("estado") or "")
    if estado_paso in {"completado", "cancelado", "rechazado", "preparado_modo_seguro"}:
        return {
            "ok": False,
            "estado": "paso_no_ejecutable",
            "mensaje": "El paso ya está en estado terminal y no puede ejecutarse.",
        }
    if requiere_confirmacion and confirmacion_estado != "confirmada":
        return {
            "ok": False,
            "estado": "confirmacion_requerida",
            "mensaje": "No se puede ejecutar un paso con confirmación pendiente.",
        }
    return {"ok": True, "estado": "paso_ejecutable"}


def ejecutar_paso_operativo_seguro(
    flujo: Dict[str, Any],
    codigo_paso: str,
    confirmar: bool = False,
    contexto: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if "ok" in flujo and not flujo.get("ok"):
        return {
            "ok": False,
            "estado": "no_ejecutado",
            "mensaje": "No se puede ejecutar el flujo porque faltan datos mínimos.",
            "resultados": [],
            "flujo": deepcopy(flujo),
            "modifico_datos_reales": False,
        }

    flujo_trabajo = deepcopy(flujo.get("flujo") or flujo)
    paso_res = obtener_paso(flujo_trabajo, codigo_paso)
    if not paso_res.get("ok"):
        return {
            "ok": False,
            "estado": "paso_no_encontrado",
            "mensaje": paso_res.get("mensaje", "Paso no encontrado."),
            "resultados": [],
            "flujo": deepcopy(flujo_trabajo),
            "modifico_datos_reales": False,
        }

    paso = dict(paso_res.get("paso") or {})
    validacion = _puede_ejecutar_paso(paso)
    if not validacion.get("ok"):
        return {
            "ok": False,
            "estado": validacion.get("estado", "paso_no_ejecutable"),
            "mensaje": validacion.get("mensaje", "No se puede ejecutar el paso."),
            "resultados": [],
            "flujo": deepcopy(flujo_trabajo),
            "paso": paso,
            "modifico_datos_reales": False,
        }

    flujo_trabajo = seleccionar_paso(
        flujo_trabajo,
        str(paso.get("id_paso") or paso.get("codigo") or ""),
        origen="ejecutor_532",
    ).get("flujo", flujo_trabajo)
    flujo_trabajo["estado"] = "en_ejecucion_segura"
    paso_en_ejecucion = dict(paso)
    paso_en_ejecucion["estado"] = "en_ejecucion_segura"

    sim = _ejecutar_paso_simulado(paso_en_ejecucion, flujo_trabajo.get("datos", {}), contexto=contexto)

    if bool(paso.get("requiere_confirmacion")) and not confirmar:
        return {
            "ok": False,
            "estado": "confirmacion_requerida",
            "mensaje": "Debes confirmar explícitamente antes de ejecutar este paso.",
            "resultados": [sim],
            "flujo": deepcopy(flujo_trabajo),
            "paso": paso_en_ejecucion,
            "modifico_datos_reales": False,
        }

    try:
        registrado = registrar_resultado(
            flujo_trabajo,
            str(paso.get("id_paso") or paso.get("codigo") or ""),
            {
                "modo": "seguro",
                "mensaje": sim.get("detalle"),
                "detalle": sim,
                "datos_reales_modificados": False,
            },
            estado_paso_final="preparado_modo_seguro",
        )
        flujo_fin = dict(registrado.get("flujo") or flujo_trabajo)
        flujo_fin = actualizar_estado_general(flujo_fin).get("flujo") or flujo_fin
        flujo_fin = registrar_historial(
            flujo_fin,
            "paso_ejecutado_seguro",
            {
                "id_paso": paso.get("id_paso"),
                "codigo": paso.get("codigo"),
                "modo": "seguro",
                "datos_reales_modificados": False,
            },
        )
        return {
            "ok": True,
            "estado": "paso_ejecutado_modo_seguro",
            "confirmado": confirmar,
            "resultados": [sim],
            "paso": registrado.get("paso"),
            "flujo": flujo_fin,
            "pendientes_confirmacion": [],
            "modifico_datos_reales": False,
            "mensaje": "Paso ejecutado en modo seguro. No se han modificado datos reales.",
        }
    except Exception as exc:  # pragma: no cover - salvaguarda de programación
        error = registrar_error(
            flujo_trabajo,
            str(paso.get("id_paso") or paso.get("codigo") or ""),
            f"Error inesperado en ejecución segura: {exc}",
        )
        flujo_err = dict(error.get("flujo") or flujo_trabajo)
        flujo_err = actualizar_estado_general(flujo_err).get("flujo") or flujo_err
        return {
            "ok": False,
            "estado": "error",
            "confirmado": confirmar,
            "resultados": [],
            "paso": error.get("paso"),
            "flujo": flujo_err,
            "pendientes_confirmacion": [],
            "modifico_datos_reales": False,
            "mensaje": "Falló la ejecución segura del paso.",
        }


def ejecutar_flujo_operativo(
    flujo: Dict[str, Any],
    confirmar: bool = False,
    codigo_paso: str | None = None,
    contexto: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Ejecuta el flujo en modo seguro.

    confirmar=True permite avanzar sobre pasos no destructivos, pero los pasos que
    modifican datos reales siguen quedando marcados para confirmación específica.
    """
    if "ok" in flujo and not flujo.get("ok"):
        return {
            "ok": False,
            "estado": "no_ejecutado",
            "mensaje": "No se puede ejecutar el flujo porque faltan datos mínimos.",
            "resultados": [],
        }

    flujo_base = deepcopy(flujo.get("flujo") or flujo)

    if codigo_paso:
        return ejecutar_paso_operativo_seguro(flujo_base, codigo_paso, confirmar=confirmar, contexto=contexto)

    actual = obtener_paso_actual(flujo_base)
    if actual.get("ok"):
        paso = dict(actual.get("paso") or {})
        if str(paso.get("estado") or "") not in {"completado", "cancelado", "rechazado", "preparado_modo_seguro"}:
            return ejecutar_paso_operativo_seguro(
                flujo_base,
                str(paso.get("id_paso") or paso.get("codigo") or ""),
                confirmar=confirmar,
                contexto=contexto,
            )

    # Modo legacy: ejecutar recorrido simulado completo sin escribir datos.
    resultados: List[Dict[str, Any]] = []
    pendientes: List[Dict[str, Any]] = []
    for paso in flujo_base.get("pasos", []):
        sim = _ejecutar_paso_simulado(paso, flujo_base.get("datos", {}))
        resultados.append(sim)
        if sim["estado"] == "pendiente_confirmacion_especifica":
            pendientes.append(sim)
    return {
        "ok": True,
        "estado": "ejecutado_modo_seguro",
        "confirmado": confirmar,
        "resultados": resultados,
        "pendientes_confirmacion": pendientes,
        "modifico_datos_reales": False,
        "mensaje": "Flujo ejecutado en modo seguro. No se han modificado datos reales.",
        "flujo": flujo_base,
    }


def formatear_ejecucion_flujo(resultado: Dict[str, Any]) -> str:
    lineas: List[str] = []
    lineas.append("HOST AI 5.3.2 - EJECUCIÓN DEL FLUJO")
    lineas.append("-" * 60)
    lineas.append(resultado.get("mensaje", ""))
    lineas.append("")

    for item in resultado.get("resultados", []):
        if item.get("estado") == "pendiente_confirmacion_especifica":
            icono = "!"
        else:
            icono = "OK"
        lineas.append(f"[{icono}] {item.get('detalle')}")

    pendientes = resultado.get("pendientes_confirmacion", [])
    if pendientes:
        lineas.append("")
        lineas.append("Pendiente de confirmación antes de modificar datos reales:")
        for item in pendientes:
            lineas.append(f"- {item.get('nombre')}")

    return "\n".join(lineas)


__all__ = ["ejecutar_flujo_operativo", "ejecutar_paso_operativo_seguro", "formatear_ejecucion_flujo"]
