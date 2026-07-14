from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


CASOS_CRITICOS = [
    {
        "id": "recepcion_mercancia_texto",
        "frase": "Han llegado 25 kg de arroz bomba de Makro a 2,15 €/kg.",
        "esperado": "recepcion_mercancia",
        "modulos_objetivo": [
            "APP/interpretar_recepcion_texto_441.py",
            "APP/recepcion_mercancia_texto_442.py",
            "APP/aplicar_recepcion_mercancia_443.py",
            "SERVICIOS/interpretar_recepcion_texto_441.py",
            "SERVICIOS/recepcion_mercancia_texto_442.py",
            "SERVICIOS/aplicar_recepcion_mercancia_443.py",
        ],
        "deberia_hacer": "Interpretar recepción, validar artículo, actualizar stock/precio y registrar movimiento.",
    },
    {
        "id": "evento_boda",
        "frase": "Necesito preparar una boda para 180 personas el sábado.",
        "esperado": "crear_evento",
        "modulos_objetivo": ["APP/gestion_eventos_471.py", "SERVICIOS/gestion_eventos_471.py"],
        "deberia_hacer": "Crear evento y dejarlo como contexto activo.",
    },
    {
        "id": "compras_manana",
        "frase": "¿Qué tengo que comprar para mañana?",
        "esperado": "compras",
        "modulos_objetivo": [
            "APP/compras_evento_474.py",
            "SERVICIOS/compras_evento_474.py",
            "APP/pedido_sugerido_stock_bajo_435.py",
            "SERVICIOS/generador_pedido_stock_bajo_435.py",
        ],
        "deberia_hacer": "Cruzar producción/eventos/stock y proponer necesidades de compra.",
    },
    {
        "id": "rentabilidad_plato",
        "frase": "¿Cuál es el plato que menos beneficio me deja?",
        "esperado": "rentabilidad",
        "modulos_objetivo": [
            "APP/rentabilidad_carta_483.py",
            "SERVICIOS/rentabilidad_carta_483.py",
            "APP/margen_plato_menu_482.py",
            "SERVICIOS/margen_plato_menu_482.py",
        ],
        "deberia_hacer": "Activar rentabilidad de carta y detectar el plato con peor margen/beneficio.",
    },
    {
        "id": "produccion_evento_contexto",
        "frase": "Planifica la producción del evento.",
        "esperado": "produccion",
        "modulos_objetivo": [
            "APP/planificador_diario_produccion_461.py",
            "APP/produccion_evento_473.py",
            "SERVICIOS/planificador_diario_produccion_461.py",
            "SERVICIOS/produccion_evento_473.py",
        ],
        "deberia_hacer": "Usar evento activo y generar planificación de producción.",
        "contexto": {"evento_id": "EVT-DEMO"},
    },
]


def _raiz_proyecto(ruta: Optional[str | Path] = None) -> Path:
    if ruta:
        return Path(ruta).resolve()
    return Path.cwd().resolve()


def _existe_alguno(raiz: Path, rutas: List[str]) -> bool:
    return any((raiz / r).exists() for r in rutas)


def _detectar_con_motor_actual(frase: str, contexto: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Ejecuta solo la detección actual del asistente, sin llamar pipelines reales."""
    try:
        from MOTORES.motor_asistente_conversacional import MotorAsistenteConversacional

        class _CoreFalso:
            pass

        motor = MotorAsistenteConversacional(_CoreFalso())
        intencion = motor.detectar_intencion(frase, contexto or {})
        return {
            "ok": True,
            "intencion_actual": getattr(intencion, "intencion", ""),
            "pipeline_actual": getattr(intencion, "pipeline", ""),
            "accion_actual": getattr(intencion, "accion", ""),
            "confianza_actual": getattr(intencion, "confianza", 0),
            "avisos": getattr(intencion, "avisos", []),
        }
    except Exception as exc:
        return {
            "ok": False,
            "intencion_actual": "error_motor",
            "pipeline_actual": "",
            "accion_actual": "",
            "confianza_actual": 0,
            "avisos": [str(exc)],
        }


def _coincide_esperado(caso: Dict[str, Any], deteccion: Dict[str, Any]) -> bool:
    esperado = caso["esperado"]
    actual = (deteccion.get("intencion_actual") or "").lower()
    pipeline = (deteccion.get("pipeline_actual") or "").lower()
    accion = (deteccion.get("accion_actual") or "").lower()
    texto = " ".join([actual, pipeline, accion])

    if esperado == "recepcion_mercancia":
        return any(p in texto for p in ["recepcion", "mercancia", "mercancía", "entrada_stock", "registrar_entrada"])
    if esperado == "compras":
        return any(p in texto for p in ["compra", "pedido", "necesidad"])
    if esperado == "rentabilidad":
        return any(p in texto for p in ["rentabilidad", "margen", "coste", "escandallo"])
    if esperado == "produccion":
        return any(p in texto for p in ["produccion", "producción", "planificar"])
    return esperado.lower() in texto


def auditar_cobertura_nucleo_ia(ruta_raiz: Optional[str | Path] = None) -> Dict[str, Any]:
    """Audita el cuello de botella real: detección de intención del chat.

    No modifica código. Comprueba si la opción `Hablar con Host AI` puede entender
    frases reales y relacionarlas con módulos ya existentes.
    """
    raiz = _raiz_proyecto(ruta_raiz)
    resultados: List[Dict[str, Any]] = []

    for caso in CASOS_CRITICOS:
        deteccion = _detectar_con_motor_actual(caso["frase"], caso.get("contexto", {}))
        modulos_disponibles = _existe_alguno(raiz, caso["modulos_objetivo"])
        cubierto = _coincide_esperado(caso, deteccion)
        resultados.append({
            "id": caso["id"],
            "frase": caso["frase"],
            "esperado": caso["esperado"],
            "intencion_actual": deteccion["intencion_actual"],
            "pipeline_actual": deteccion["pipeline_actual"],
            "accion_actual": deteccion["accion_actual"],
            "confianza_actual": deteccion["confianza_actual"],
            "avisos": deteccion.get("avisos", []),
            "modulos_disponibles": modulos_disponibles,
            "cubierto_por_chat": cubierto,
            "brecha": modulos_disponibles and not cubierto,
            "deberia_hacer": caso["deberia_hacer"],
        })

    total = len(resultados)
    cubiertos = sum(1 for r in resultados if r["cubierto_por_chat"])
    brechas = [r for r in resultados if r["brecha"]]

    return {
        "version": "5.0.1",
        "tipo": "auditoria_nucleo_ia",
        "estado": "ok" if cubiertos >= 1 else "revision",
        "raiz": str(raiz),
        "total_casos": total,
        "casos_cubiertos": cubiertos,
        "casos_con_brecha": len(brechas),
        "resultados": resultados,
        "conclusion": _construir_conclusion(resultados),
        "recomendaciones": generar_recomendaciones_nucleo(resultados),
    }


def _construir_conclusion(resultados: List[Dict[str, Any]]) -> str:
    brechas = [r for r in resultados if r["brecha"]]
    if not brechas:
        return "El chat cubre los casos críticos auditados."
    ids = ", ".join(r["id"] for r in brechas)
    return (
        "El cuello de botella no está en la existencia de módulos, sino en la detección "
        f"de intención del chat. Brechas detectadas: {ids}."
    )


def generar_recomendaciones_nucleo(resultados: List[Dict[str, Any]]) -> List[str]:
    recomendaciones: List[str] = []
    ids_brecha = {r["id"] for r in resultados if r["brecha"]}

    if "recepcion_mercancia_texto" in ids_brecha:
        recomendaciones.append(
            "Añadir intención de recepción de mercancía al chat: patrones 'han llegado', 'ha venido', 'me ha traído', 'albarán', 'factura', proveedor + cantidad."
        )
    if "compras_manana" in ids_brecha:
        recomendaciones.append(
            "Añadir intención de compras/necesidades: 'qué tengo que comprar', 'qué falta', 'pedido para mañana', conectando stock + eventos + producción."
        )
    if "rentabilidad_plato" in ids_brecha:
        recomendaciones.append(
            "Añadir intención de rentabilidad: 'beneficio', 'margen', 'plato que menos deja', conectando módulos 4.8."
        )
    recomendaciones.append(
        "No crear otro motor paralelo: ampliar MOTORES/motor_asistente_conversacional.py y reutilizar orquestador/pipelines existentes."
    )
    recomendaciones.append(
        "Crear después un parche 5.0.2 con corrección de intenciones críticas y tests conversacionales reales."
    )
    return recomendaciones


def formatear_auditoria_nucleo(auditoria: Dict[str, Any]) -> str:
    lineas = [
        "=== HOST AI 5.0.1 - AUDITORIA DEL NUCLEO IA ===",
        f"Raiz analizada: {auditoria['raiz']}",
        f"Estado: {auditoria['estado']}",
        f"Casos cubiertos por chat: {auditoria['casos_cubiertos']} / {auditoria['total_casos']}",
        f"Brechas detectadas: {auditoria['casos_con_brecha']}",
        "",
        "Casos auditados:",
    ]
    for r in auditoria["resultados"]:
        marca = "OK" if r["cubierto_por_chat"] else "FALTA"
        lineas.append(f"- [{marca}] {r['id']}")
        lineas.append(f"  Frase: {r['frase']}")
        lineas.append(f"  Esperado: {r['esperado']}")
        lineas.append(f"  Actual: {r['intencion_actual']} | {r['pipeline_actual']}.{r['accion_actual']} | confianza {r['confianza_actual']}")
        lineas.append(f"  Modulos disponibles: {'SI' if r['modulos_disponibles'] else 'NO'}")
        if r.get("avisos"):
            lineas.append(f"  Avisos: {' '.join(r['avisos'])}")
    lineas.extend(["", "Conclusion:", auditoria["conclusion"], "", "Recomendaciones:"])
    lineas.extend([f"- {rec}" for rec in auditoria["recomendaciones"]])
    return "\n".join(lineas)


def ejecutar_auditoria_nucleo_ia(ruta_raiz: Optional[str | Path] = None) -> Dict[str, Any]:
    auditoria = auditar_cobertura_nucleo_ia(ruta_raiz)
    auditoria["informe_texto"] = formatear_auditoria_nucleo(auditoria)
    return auditoria
