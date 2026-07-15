from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict

from SERVICIOS.escalador_explosion_recetas_556ab import (
    MotorEscaladoExplosion556AB,
    extraer_consulta_556ab,
    formatear_escalado_556ab,
    formatear_explosion_556ab,
)
from SERVICIOS.cruce_stock_produccion_556c import CruceStockProduccion556C, formatear_cruce_stock_556c
from SERVICIOS.planificador_produccion_556d import PlanificadorProduccion556D, formatear_plan_556d
from SERVICIOS.produccion_automatica_evento_556f import (
    ProduccionAutomaticaEvento556F,
    es_consulta_produccion_automatica_evento_556f,
    extraer_consulta_evento_556f,
    formatear_produccion_automatica_evento_556f,
)


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def es_consulta_produccion_real_556(texto: str) -> bool:
    t = _norm(texto)
    return es_consulta_produccion_automatica_evento_556f(texto) or any(p in t for p in (
        "planifica la produccion", "prepara la produccion", "produccion de", "que tengo que producir",
        "calcula la produccion", "plan de produccion", "calcula la receta", "escala la receta", "desglosa", "explota",
        "incluyendo elaboraciones", "elaboraciones internas", "con el stock actual", "stock necesario", "puedo producir",
    ))


def procesar_consulta_produccion_real_556(texto: str, base_dir: Path) -> Dict[str, Any]:
    if not es_consulta_produccion_real_556(texto):
        return {"gestionado": False}
    if es_consulta_produccion_automatica_evento_556f(texto):
        entrada_evento = extraer_consulta_evento_556f(texto)
        if not entrada_evento.get("evento"):
            return {
                "gestionado": True,
                "ok": False,
                "version": "5.5.6F",
                "intencion": "planificar_produccion_automatica_evento",
                "estado": "FALTA_EVENTO",
                "mensaje": "PRODUCCIÓN AUTOMÁTICA\n- Indica el evento (nombre o ID EVT-...).\n- Ejemplo: Planifica la producción automática del evento BoronatX con 3 cocineros.\n\nSEGURIDAD\n- Datos reales modificados: NO.",
                "datos": entrada_evento,
                "pasos": [],
            }
        datos = ProduccionAutomaticaEvento556F(base_dir).planificar_evento(
            entrada_evento["evento"],
            cocineros=int(entrada_evento.get("cocineros", 3)),
            inicio_jornada=str(entrada_evento.get("inicio_jornada") or "08:00"),
            fin_jornada=str(entrada_evento.get("fin_jornada") or "15:30"),
        )
        return {
            "gestionado": True,
            "ok": bool(datos.get("ok", False)),
            "version": "5.5.6F",
            "intencion": "planificar_produccion_automatica_evento",
            "estado": datos.get("estado"),
            "mensaje": formatear_produccion_automatica_evento_556f(datos),
            "datos": datos,
            "pasos": [],
        }
    entrada = extraer_consulta_556ab(texto)
    termino_limpio = re.sub(r"^(?:el\s+)?plan\s+de\s+produccion\s+de\s+", "", str(entrada.get("termino") or ""), flags=re.I).strip()
    entrada["termino"] = termino_limpio
    if not entrada.get("objetivo"):
        return {"gestionado": True, "ok": True, "version": "5.5.6CD", "estado": "falta_objetivo", "mensaje": "PRODUCCIÓN REAL\n- Necesito saber para cuántas personas, raciones o unidades debo calcular.\n\nSEGURIDAD\n- Datos reales modificados: NO.", "datos": entrada, "pasos": []}
    t = _norm(texto)
    try:
        if any(p in t for p in ("plan de produccion", "planifica la produccion", "prepara la produccion")):
            datos = PlanificadorProduccion556D(base_dir).generar(entrada["termino"], entrada["objetivo"], entrada["unidad"])
            return {"gestionado": True, "ok": True, "version": "5.5.6D", "intencion": "planificar_produccion_real", "estado": datos["estado"], "mensaje": formatear_plan_556d(datos), "datos": datos, "pasos": []}
        if any(p in t for p in ("con el stock actual", "que puedo producir", "stock necesario", "cruza", "faltantes")):
            datos = CruceStockProduccion556C(base_dir).cruzar(entrada["termino"], entrada["objetivo"], entrada["unidad"])
            return {"gestionado": True, "ok": True, "version": "5.5.6C", "intencion": "cruzar_produccion_stock", "estado": "stock_cruzado", "mensaje": formatear_cruce_stock_556c(datos), "datos": datos, "pasos": []}
        motor = MotorEscaladoExplosion556AB(Path(base_dir))
        if entrada.get("explotar"):
            datos = motor.explotar(entrada["termino"], entrada["objetivo"], entrada["unidad"])
            mensaje = formatear_explosion_556ab(datos)
            estado = "explosion_elaboraciones_generada"
        else:
            datos = motor.escalar(entrada["termino"], entrada["objetivo"], entrada["unidad"])
            mensaje = formatear_escalado_556ab(datos)
            estado = "receta_escalada"
        return {"gestionado": True, "ok": True, "version": "5.5.6AB", "intencion": "produccion_real", "estado": estado, "mensaje": mensaje, "datos": datos, "pasos": []}
    except (LookupError, ValueError) as exc:
        return {"gestionado": True, "ok": False, "version": "5.5.6CD", "estado": "receta_no_localizada", "mensaje": f"PRODUCCIÓN REAL\n- {exc}\n- No inventaré cantidades ni elaboraciones.\n\nSEGURIDAD\n- Datos reales modificados: NO.", "datos": entrada, "pasos": []}


class ConectorProduccionReal556:
    VERSION = "5.5.6CD"
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.motor = MotorEscaladoExplosion556AB(base_dir)
    def planificar(self, termino: str, personas: int | None) -> Dict[str, Any]:
        if not personas:
            return {"ok": True, "encontrado": False, "requiere_personas": True, "solo_lectura": True}
        try:
            return {"ok": True, "encontrado": True, "requiere_personas": False, "planes": [PlanificadorProduccion556D(self.base_dir).generar(termino, personas, "personas")], "solo_lectura": True}
        except LookupError:
            return {"ok": True, "encontrado": False, "requiere_personas": False, "planes": [], "solo_lectura": True}


__all__ = ["ConectorProduccionReal556", "es_consulta_produccion_real_556", "procesar_consulta_produccion_real_556"]
