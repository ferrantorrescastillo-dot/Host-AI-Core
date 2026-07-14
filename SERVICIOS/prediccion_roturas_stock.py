"""Servicio de predicción de roturas de stock.

Módulo revisado en RC2.5. No altera comportamiento: documenta el contrato
público del servicio y mantiene compatibilidad con los pipelines existentes.
"""

from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
from statistics import mean
from datetime import datetime, timedelta
import json
from MODELOS.roturas_stock import PrediccionRoturaStock, InformeRoturasStock

class PrediccionRoturasStock:
    """Host AI 3.0.4.6 - Predicción de Roturas de Stock."""
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def predecir_roturas(self, horizonte_dias: int = 14) -> Dict[str, Any]:
        historico = getattr(self.core, "historico_inteligente_stock", None)
        registros = list(getattr(historico, "registros", []) or []) if historico else []
        agrupados: Dict[str, List[Any]] = {}
        for r in registros:
            aid = getattr(r, "articulo_id", "") or "SIN-ARTICULO"
            agrupados.setdefault(aid, []).append(r)
        predicciones=[]; criticas=avisos=estables=0
        hoy = datetime.now()
        for aid, regs in agrupados.items():
            entradas=[]; salidas=[]; stock=0.0
            for r in regs:
                cant=float(getattr(r,"cantidad",0) or 0)
                tipo=(getattr(r,"tipo","") or "").lower()
                if tipo == "entrada":
                    entradas.append(cant); stock += cant
                elif tipo in ("salida", "consumo", "produccion"):
                    salidas.append(cant); stock -= cant
            consumo = mean(salidas) if salidas else (mean(entradas) * 0.35 if entradas else 0)
            dias = 999.0 if consumo <= 0 else max(0.0, stock / consumo)
            if dias <= 3:
                riesgo="critica"; criticas += 1; rec="Comprar de forma urgente o revisar stock físico."
            elif dias <= horizonte_dias:
                riesgo="aviso"; avisos += 1; rec="Planificar compra antes de la próxima producción."
            else:
                riesgo="estable"; estables += 1; rec="No comprar todavía salvo precio especial o evento confirmado."
            fecha = (hoy + timedelta(days=dias if dias < 365 else 365)).date().isoformat()
            ultimo=regs[-1]
            confianza = "alta" if len(salidas) >= 4 else "media" if len(regs) >= 4 else "baja"
            predicciones.append(PrediccionRoturaStock(
                articulo_id=aid, nombre_articulo=getattr(ultimo,"nombre_articulo",aid), stock_actual=round(stock,4),
                consumo_medio=round(consumo,4), dias_hasta_rotura=round(dias,2), fecha_estimada_rotura=fecha,
                nivel_riesgo=riesgo, recomendacion=rec, unidad=getattr(ultimo,"unidad",""), proveedor_id=getattr(ultimo,"proveedor_id",""),
                confianza=confianza, datos={"entradas": entradas, "salidas": salidas, "horizonte_dias": horizonte_dias}).to_dict())
        orden={"critica":0,"aviso":1,"estable":2}
        predicciones.sort(key=lambda x: (orden.get(x["nivel_riesgo"],9), x["dias_hasta_rotura"]))
        return InformeRoturasStock(len(predicciones), criticas, avisos, estables, predicciones, f"Predicción roturas stock: {len(predicciones)} artículos analizados.").to_dict()

    def predecir_articulo(self, articulo_id: str, horizonte_dias: int = 14) -> Dict[str, Any]:
        informe = self.predecir_roturas(horizonte_dias)
        for p in informe.get("predicciones", []):
            if p.get("articulo_id") == articulo_id:
                p["encontrado"] = True
                p["lectura_host_ai"] = f"Rotura {p['nombre_articulo']}: {p['nivel_riesgo']} en {p['dias_hasta_rotura']} días."
                return p
        return {"encontrado": False, "lectura_host_ai": "No hay datos suficientes para este artículo."}

    def exportar_prediccion(self, prediccion: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        destino = self.facturas_dir / (nombre or "prediccion_roturas_stock.json")
        destino.write_text(json.dumps(prediccion, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Predicción de roturas exportada: {destino.name}."}


__all__ = ["PrediccionRoturasStock"]
