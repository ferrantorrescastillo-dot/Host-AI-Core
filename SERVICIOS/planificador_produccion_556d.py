from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List

from SERVICIOS.cruce_stock_produccion_556c import CruceStockProduccion556C


class PlanificadorProduccion556D:
    VERSION = "5.5.6D"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.cruce = CruceStockProduccion556C(self.base_dir)

    @staticmethod
    def _fases(nombre: str, ingredientes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        n = nombre.lower()
        tareas: List[Dict[str, Any]] = [
            {"orden": 1, "fase": "Preparar", "descripcion": "Reunir, pesar y verificar todos los ingredientes.", "tipo_tiempo": "activo", "duracion_min": max(15, min(60, len(ingredientes) * 4))},
        ]
        if any(p in n for p in ("crema", "salsa", "romesco", "vinagreta", "mayonesa")):
            tareas += [
                {"orden": 2, "fase": "Elaborar", "descripcion": "Procesar y mezclar según la ficha técnica.", "tipo_tiempo": "activo", "duracion_min": 35},
                {"orden": 3, "fase": "Reposar/Enfriar", "descripcion": "Reposar o enfriar hasta la temperatura de conservación.", "tipo_tiempo": "pasivo", "duracion_min": 45},
            ]
        elif any(p in n for p in ("ensaladilla", "ensalada", "tartar", "ceviche")):
            tareas += [
                {"orden": 2, "fase": "Cocinar bases", "descripcion": "Cocer o preparar las bases que lo requieran.", "tipo_tiempo": "activo", "duracion_min": 45},
                {"orden": 3, "fase": "Enfriar", "descripcion": "Enfriar con seguridad antes de mezclar.", "tipo_tiempo": "pasivo", "duracion_min": 60},
                {"orden": 4, "fase": "Mezclar y ajustar", "descripcion": "Mezclar, sazonar y verificar textura.", "tipo_tiempo": "activo", "duracion_min": 30},
            ]
        elif any(p in n for p in ("parrill", "chuleta", "cordero", "butifarra", "pulpo")):
            tareas += [
                {"orden": 2, "fase": "Preelaborar", "descripcion": "Limpiar, porcionar, sazonar y preparar para cocción.", "tipo_tiempo": "activo", "duracion_min": 45},
                {"orden": 3, "fase": "Cocinar", "descripcion": "Ejecutar la cocción principal y controlar puntos.", "tipo_tiempo": "activo", "duracion_min": 60},
            ]
        else:
            tareas += [
                {"orden": 2, "fase": "Elaborar", "descripcion": "Ejecutar la elaboración según ficha técnica.", "tipo_tiempo": "activo", "duracion_min": 45},
            ]
        siguiente = len(tareas) + 1
        tareas += [
            {"orden": siguiente, "fase": "Porcionar", "descripcion": "Dividir según rendimiento y servicio previsto.", "tipo_tiempo": "activo", "duracion_min": 25},
            {"orden": siguiente + 1, "fase": "Envasar y etiquetar", "descripcion": "Envasar, fechar, identificar lote y condiciones de conservación.", "tipo_tiempo": "activo", "duracion_min": 20},
            {"orden": siguiente + 2, "fase": "Guardar", "descripcion": "Ubicar en cámara, congelación o zona seca según corresponda.", "tipo_tiempo": "activo", "duracion_min": 10},
            {"orden": siguiente + 3, "fase": "Control final", "descripcion": "Verificar cantidades, etiquetado, seguridad y pendientes.", "tipo_tiempo": "activo", "duracion_min": 10},
        ]
        return tareas

    def generar(self, termino: str, objetivo: float, unidad_objetivo: str = "personas") -> Dict[str, Any]:
        cruce = self.cruce.cruzar(termino, objetivo, unidad_objetivo)
        tareas = self._fases(cruce["receta"], cruce["explosion"]["ingredientes_finales"])
        minutos_activos = sum(t["duracion_min"] for t in tareas if t["tipo_tiempo"] == "activo")
        minutos_pasivos = sum(t["duracion_min"] for t in tareas if t["tipo_tiempo"] == "pasivo")
        faltantes = [x for x in cruce["lineas"] if x["faltante"] > 0 or x["estado"] in ("SIN_REGISTRO_STOCK", "UNIDAD_INCOMPATIBLE")]
        return {
            "version": self.VERSION, "receta": cruce["receta"], "objetivo": objetivo, "unidad_objetivo": unidad_objetivo,
            "tareas": tareas, "minutos_activos_estimados": minutos_activos, "minutos_pasivos_estimados": minutos_pasivos,
            "duracion_total_teorica_min": minutos_activos + minutos_pasivos, "faltantes": faltantes,
            "estado": "BLOQUEADO_POR_FALTANTES" if faltantes else "PLAN_PRELIMINAR_PREPARADO",
            "requiere_confirmacion": True, "orden_creada": False, "solo_lectura": True, "datos_reales_modificados": False,
            "cruce_stock": cruce,
        }


def formatear_plan_556d(resultado: Dict[str, Any]) -> str:
    lines = [
        f"PLAN PRELIMINAR DE PRODUCCIÓN — {resultado['receta']}",
        f"- Objetivo: {resultado['objetivo']:g} {resultado['unidad_objetivo']}",
        f"- Estado: {resultado['estado']}",
        f"- Tiempo activo estimado: {resultado['minutos_activos_estimados']} min",
        f"- Tiempo pasivo estimado: {resultado['minutos_pasivos_estimados']} min",
        "", "SECUENCIA DE TRABAJO",
    ]
    for t in resultado["tareas"]:
        lines.append(f"{t['orden']}. {t['fase']} — {t['descripcion']} ({t['duracion_min']} min, {t['tipo_tiempo']})")
    if resultado["faltantes"]:
        lines += ["", "BLOQUEOS ANTES DE PRODUCIR"]
        for x in resultado["faltantes"]:
            lines.append(f"- {x['nombre']}: faltan {x['faltante']:g} {x['unidad']} ({x['estado']})")
    lines += [
        "", "SIGUIENTE PASO PROFESIONAL",
        "- Resolver faltantes y revisar tiempos antes de convertir este plan en una orden real.",
        "- La creación y confirmación de órdenes corresponde a la 5.5.6F.",
        "", "SEGURIDAD", "- Plan preliminar en modo solo lectura.", "- No se ha descontado stock ni creado una orden.", "- Datos reales modificados: NO.",
    ]
    return "\n".join(lines)


__all__ = ["PlanificadorProduccion556D", "formatear_plan_556d"]
