"""Servicio de predicción inteligente de precios de compras.

Módulo revisado en RC2.5. No altera comportamiento: documenta el contrato
público del servicio y mantiene compatibilidad con los pipelines existentes.
"""

from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
from statistics import mean
import json

from MODELOS.prediccion_precios import PrediccionPrecioArticulo, InformePrediccionPrecios


class PrediccionInteligentePrecios:
    """
    Host AI 3.0.4.4 - Predicción Inteligente de Precios.

    Calcula media móvil, tendencia, predicción del siguiente precio y confianza
    usando el histórico inteligente de precios ya existente en Host AI.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def predecir_precios(self, ventana: int = 3) -> Dict[str, Any]:
        historico = getattr(self.core, "historico_inteligente_precios", None)
        registros = list(getattr(historico, "registros", []) or []) if historico else []
        agrupados: Dict[str, List[Any]] = {}
        for r in registros:
            agrupados.setdefault(getattr(r, "articulo_id", "") or "SIN-ARTICULO", []).append(r)

        predicciones: List[Dict[str, Any]] = []
        resumen_tendencias: Dict[str, int] = {}
        for articulo_id, regs in agrupados.items():
            precios = [float(getattr(r, "precio", 0) or 0) for r in regs if float(getattr(r, "precio", 0) or 0) > 0]
            if not precios:
                continue
            ultimo = precios[-1]
            ventana_real = max(1, min(int(ventana or 3), len(precios)))
            media_movil = mean(precios[-ventana_real:])
            primero = precios[0]
            variacion_total = ((ultimo - primero) / primero) * 100 if primero else 0.0
            if len(precios) >= 2:
                diferencia_media = mean([precios[i] - precios[i - 1] for i in range(1, len(precios))])
            else:
                diferencia_media = 0.0
            prediccion = max(0.0, ultimo + diferencia_media)
            tendencia = self._clasificar_tendencia(variacion_total, diferencia_media, media_movil)
            confianza = self._calcular_confianza(len(precios), precios)
            resumen_tendencias[tendencia] = resumen_tendencias.get(tendencia, 0) + 1
            ultimo_reg = regs[-1]
            predicciones.append(PrediccionPrecioArticulo(
                articulo_id=articulo_id,
                nombre_articulo=getattr(ultimo_reg, "nombre_articulo", articulo_id),
                total_registros=len(precios),
                ultimo_precio=round(ultimo, 4),
                media_movil=round(media_movil, 4),
                tendencia=tendencia,
                variacion_porcentual=round(variacion_total, 2),
                prediccion_siguiente_precio=round(prediccion, 4),
                nivel_confianza=confianza,
                proveedor_id=getattr(ultimo_reg, "proveedor_id", ""),
                unidad=getattr(ultimo_reg, "unidad", ""),
                historico=[r.to_dict() for r in regs],
                datos={"ventana_media_movil": ventana_real, "diferencia_media": round(diferencia_media, 4)},
            ).to_dict())

        predicciones.sort(key=lambda p: (p["nivel_confianza"] != "alta", p["articulo_id"]))
        lectura = f"Predicción precios: {len(predicciones)} artículos analizados."
        return InformePrediccionPrecios(
            total_articulos=len(predicciones),
            predicciones=predicciones,
            resumen_tendencias=resumen_tendencias,
            lectura_host_ai=lectura,
        ).to_dict()

    def predecir_articulo(self, articulo_id: str, ventana: int = 3) -> Dict[str, Any]:
        informe = self.predecir_precios(ventana=ventana)
        for p in informe.get("predicciones", []):
            if p.get("articulo_id") == articulo_id:
                p["encontrado"] = True
                p["lectura_host_ai"] = f"Predicción {p['nombre_articulo']}: {p['prediccion_siguiente_precio']} {p.get('unidad','')} con confianza {p['nivel_confianza']}."
                return p
        return {"encontrado": False, "lectura_host_ai": "No hay histórico suficiente para este artículo."}

    def exportar_prediccion(self, prediccion: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "prediccion_inteligente_precios.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(prediccion, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Predicción de precios exportada: {destino.name}."}

    def _clasificar_tendencia(self, variacion_total: float, diferencia_media: float, media_movil: float) -> str:
        umbral = abs(media_movil) * 0.03
        if variacion_total > 5 and diferencia_media > umbral:
            return "sube"
        if variacion_total < -5 and diferencia_media < -umbral:
            return "baja"
        return "estable"

    def _calcular_confianza(self, total: int, precios: List[float]) -> str:
        if total >= 5:
            media = mean(precios)
            dispersion = (max(precios) - min(precios)) / media if media else 0
            return "alta" if dispersion <= 0.35 else "media"
        if total >= 3:
            return "media"
        return "baja"


__all__ = ["PrediccionInteligentePrecios"]
