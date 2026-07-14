from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
from datetime import date, datetime, timedelta
import json
from MODELOS.prediccion_necesidades_stock import NecesidadStockPredicha, InformePrediccionNecesidadesStock

class PrediccionNecesidadesStock:
    """Host AI 3.0.5.5 - Predicción de Necesidades de Stock.

    Cruza stock actual, mínimos, movimientos, consumos, producción prevista y eventos para estimar
    necesidades futuras sin depender de IA externa. La IA conversacional podrá usar este servicio
    como motor de decisión en fases posteriores.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.stock_dir = self.base_dir / "DATOS" / "stock"
        self.stock_dir.mkdir(parents=True, exist_ok=True)

    def predecir_necesidades(self, horizonte_dias: int = 14, produccion_prevista: List[Dict[str, Any]] | None = None, eventos_previstos: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        stock = getattr(self.core, "stock", None)
        actual = stock.stock_actual() if stock else {"items": [], "total_items": 0}
        movimientos = stock.movimientos_listado() if stock else []
        produccion_prevista = produccion_prevista or []
        eventos_previstos = eventos_previstos or []

        salidas = self._agrupar_salidas(movimientos)
        necesidades_extra = self._agrupar_necesidades_previstas(produccion_prevista, eventos_previstos)
        items: List[Dict[str, Any]] = []
        total_valor = 0.0
        criticas = 0
        avisos = 0

        for item in actual.get("items", []):
            clave = item.get("articulo_id") or item.get("clave") or item.get("nombre", "").lower().strip()
            nombre = item.get("nombre", clave)
            unidad = item.get("unidad", "")
            cantidad = float(item.get("cantidad", 0) or 0)
            minimo = float(getattr(stock, "stock_minimos", {}).get(clave, 0) or 0)
            consumo_diario = self._consumo_diario_estimado(clave, salidas, horizonte_dias)
            extra = float(necesidades_extra.get(clave, 0) or 0)
            necesidad_periodo = consumo_diario * horizonte_dias + extra
            cobertura = 999.0 if consumo_diario <= 0 else cantidad / consumo_diario
            cantidad_objetivo = max(necesidad_periodo, minimo * 1.5 if minimo else 0.0)
            reponer = max(0.0, cantidad_objetivo - cantidad)
            fecha_rotura = ""
            if consumo_diario > 0:
                fecha_rotura = (date.today() + timedelta(days=int(cobertura))).isoformat()
            prioridad, motivos = self._prioridad(cantidad, minimo, cobertura, reponer, extra)
            if prioridad == "critica": criticas += 1
            elif prioridad == "aviso": avisos += 1
            valor_unitario = self._coste_medio(item.get("lotes", []) or [])
            total_valor += reponer * valor_unitario
            confianza = self._confianza(clave, salidas, consumo_diario, extra)
            if reponer > 0 or prioridad != "normal":
                items.append(NecesidadStockPredicha(
                    clave=clave, nombre=nombre, articulo_id=item.get("articulo_id", ""), unidad=unidad,
                    stock_actual=round(cantidad, 4), consumo_diario_estimado=round(consumo_diario, 4), dias_cobertura=round(cobertura, 2),
                    necesidad_periodo=round(necesidad_periodo, 4), cantidad_a_reponer=round(reponer, 4), fecha_rotura_estimada=fecha_rotura,
                    prioridad=prioridad, confianza=confianza, motivos=motivos,
                    datos={"stock_minimo": minimo, "necesidad_extra_prevista": extra, "coste_medio": valor_unitario}
                ).to_dict())
        items.sort(key=lambda x: (self._orden(x["prioridad"]), x["dias_cobertura"], -x["cantidad_a_reponer"], x["nombre"]))
        resumen = {"estado_general": "critico" if criticas else ("revisar" if avisos or items else "ok"), "articulos_con_reposicion": len([i for i in items if i["cantidad_a_reponer"] > 0])}
        lectura = f"Predicción de necesidades de stock: {len(items)} artículos con necesidad o riesgo en {horizonte_dias} días."
        return InformePrediccionNecesidadesStock(len(actual.get("items", [])), len(items), criticas, avisos, round(total_valor, 4), horizonte_dias, items, resumen, lectura).to_dict()

    def exportar_prediccion(self, prediccion: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        destino = self.stock_dir / (nombre or "prediccion_necesidades_stock.json")
        destino.write_text(json.dumps(prediccion, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Predicción de necesidades de stock exportada: {destino.name}."}

    def _agrupar_salidas(self, movimientos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        out: Dict[str, List[Dict[str, Any]]] = {}
        for m in movimientos:
            if (m.get("tipo") or "").lower() != "salida": continue
            clave = m.get("articulo_id") or m.get("nombre", "").lower().strip()
            out.setdefault(clave, []).append(m)
        return out
    def _consumo_diario_estimado(self, clave: str, salidas: Dict[str, List[Dict[str, Any]]], horizonte: int) -> float:
        movs = salidas.get(clave, [])
        if not movs: return 0.0
        total = sum(float(m.get("cantidad", 0) or 0) for m in movs)
        fechas=[]
        for m in movs:
            try: fechas.append(datetime.fromisoformat(m.get("fecha") or m.get("creado_en") or "").date())
            except Exception: pass
        if fechas:
            dias=max(1,(max(fechas)-min(fechas)).days+1)
            return total / min(max(dias, 1), max(horizonte, 1))
        return total / max(horizonte, 1)
    def _agrupar_necesidades_previstas(self, produccion: List[Dict[str, Any]], eventos: List[Dict[str, Any]]) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for origen in (produccion or []) + (eventos or []):
            for ing in origen.get("ingredientes", origen.get("articulos", [])) or []:
                clave = ing.get("articulo_id") or ing.get("nombre", "").lower().strip()
                out[clave] = out.get(clave, 0.0) + float(ing.get("cantidad", 0) or 0)
        return out
    def _prioridad(self, cantidad: float, minimo: float, cobertura: float, reponer: float, extra: float):
        motivos=[]; prioridad="normal"
        if cantidad <= 0: prioridad="critica"; motivos.append("Artículo sin stock actual.")
        if minimo and cantidad < minimo: prioridad="critica" if cantidad <= minimo*0.25 else "aviso"; motivos.append("Stock actual por debajo del mínimo.")
        if cobertura < 3: prioridad="critica"; motivos.append("Cobertura inferior a 3 días.")
        elif cobertura < 7 and prioridad != "critica": prioridad="aviso"; motivos.append("Cobertura inferior a 7 días.")
        if extra > 0 and reponer > 0: motivos.append("Producción o eventos previstos aumentan la necesidad.")
        if reponer > 0 and not motivos: prioridad="aviso"; motivos.append("Conviene reponer para cubrir el horizonte previsto.")
        return prioridad, motivos
    def _coste_medio(self, lotes):
        unidades=sum(float(l.get("cantidad",0) or 0) for l in lotes)
        valor=sum(float(l.get("cantidad",0) or 0)*float(l.get("coste_unitario",0) or 0) for l in lotes)
        return round(valor/unidades,4) if unidades>0 else 0.0
    def _confianza(self, clave, salidas, consumo, extra):
        n=len(salidas.get(clave, [])); conf=0.35
        if n>=3: conf+=0.25
        if consumo>0: conf+=0.20
        if extra>0: conf+=0.10
        return round(min(0.95, conf), 2)
    def _orden(self, p): return {"critica":0,"aviso":1,"normal":2}.get(p,9)
