from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.optimizacion_stock import RecomendacionOptimizacionStock, InformeOptimizacionStock

class OptimizadorStock:
    """Host AI 3.0.5.6 - Optimizador de Stock.

    Convierte análisis, alertas, reconciliación y predicción en acciones operativas: comprar,
    no comprar, reducir, consumir primero o revisar ubicación/descuadres.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.stock_dir = self.base_dir / "DATOS" / "stock"
        self.stock_dir.mkdir(parents=True, exist_ok=True)

    def optimizar_stock(self, horizonte_dias: int = 14) -> Dict[str, Any]:
        analisis = self.core.analizador_inteligente_stock.analizar_stock()
        pred = self.core.prediccion_necesidades_stock.predecir_necesidades(horizonte_dias=horizonte_dias)
        alertas = self.core.motor_alertas_stock.generar_alertas()
        acciones: List[Dict[str, Any]] = []

        for item in pred.get("items", []):
            if item.get("cantidad_a_reponer", 0) > 0:
                prioridad = "critica" if item.get("prioridad") == "critica" else "aviso"
                acciones.append(RecomendacionOptimizacionStock(
                    clave=item["clave"], nombre=item["nombre"], articulo_id=item.get("articulo_id", ""), tipo="compra_recomendada",
                    prioridad=prioridad, accion="comprar", cantidad_sugerida=item.get("cantidad_a_reponer", 0), unidad=item.get("unidad", ""),
                    impacto_estimado=round(float(item.get("cantidad_a_reponer",0))*float(item.get("datos",{}).get("coste_medio",0)),4),
                    motivo="Reposición sugerida por predicción de necesidades y cobertura de stock.", datos={"origen":"prediccion_necesidades", "fecha_rotura_estimada": item.get("fecha_rotura_estimada", "")}
                ).to_dict())

        for item in analisis.get("items", []):
            estado = item.get("estado")
            if estado == "exceso_stock":
                exceso = max(0.0, float(item.get("cantidad",0))-float(item.get("stock_maximo",0)))
                acciones.append(RecomendacionOptimizacionStock(item["clave"], item["nombre"], item.get("articulo_id",""), "reducir_exceso", "aviso", "no_comprar_y_consumir_antes", round(exceso,4), item.get("unidad",""), item.get("valor_estimado",0), "Artículo por encima del máximo recomendado; evitar compra y priorizar consumo.", {"estado":estado}).to_dict())
            if estado == "sin_movimiento":
                acciones.append(RecomendacionOptimizacionStock(item["clave"], item["nombre"], item.get("articulo_id",""), "producto_parado", "aviso", "revisar_uso_o_baja", 0, item.get("unidad",""), item.get("valor_estimado",0), "Producto sin movimiento; revisar carta, producción o baja de stock.", {"dias_sin_movimiento": item.get("dias_sin_movimiento")}).to_dict())
            if not item.get("ubicaciones"):
                acciones.append(RecomendacionOptimizacionStock(item["clave"], item["nombre"], item.get("articulo_id",""), "ubicacion", "informativa", "asignar_ubicacion", 0, item.get("unidad",""), 0, "Artículo sin ubicación registrada.", {}).to_dict())

        for alerta in alertas.get("alertas", []):
            if alerta.get("tipo") in {"caducidad_cercana", "caducado"}:
                prioridad = "critica" if alerta.get("tipo") == "caducado" else "aviso"
                item = alerta.get("item") or alerta.get("lote") or {}
                acciones.append(RecomendacionOptimizacionStock(item.get("articulo_id") or item.get("nombre", "").lower().strip(), item.get("nombre", "Artículo"), item.get("articulo_id", ""), "caducidad", prioridad, "consumir_o_retirar", float(item.get("cantidad",0) or 0), item.get("unidad", ""), 0, alerta.get("mensaje", "Revisar caducidad."), {"origen":"alertas_stock"}).to_dict())

        acciones = self._deduplicar(acciones)
        acciones.sort(key=lambda x: (self._orden(x["prioridad"]), x["tipo"], x["nombre"]))
        ahorro = round(sum(float(a.get("impacto_estimado",0) or 0) for a in acciones if a.get("tipo") in {"reducir_exceso", "producto_parado"}), 4)
        criticas = len([a for a in acciones if a.get("prioridad") == "critica"])
        avisos = len([a for a in acciones if a.get("prioridad") == "aviso"])
        resumen = {"estado_general": "critico" if criticas else ("revisar" if acciones else "ok"), "compras_recomendadas": len([a for a in acciones if a.get("accion") == "comprar"]), "acciones_no_compra": len([a for a in acciones if a.get("accion") != "comprar"])}
        lectura = f"Optimización de stock: {len(acciones)} acciones recomendadas, {criticas} críticas y {avisos} avisos."
        return InformeOptimizacionStock(len(acciones), criticas, avisos, ahorro, acciones, resumen, lectura).to_dict()

    def exportar_optimizacion(self, optimizacion: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        destino = self.stock_dir / (nombre or "optimizacion_stock.json")
        destino.write_text(json.dumps(optimizacion, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Optimización de stock exportada: {destino.name}."}

    def _deduplicar(self, acciones):
        vistos=set(); out=[]
        for a in acciones:
            k=(a.get("clave"), a.get("tipo"), a.get("accion"))
            if k in vistos: continue
            vistos.add(k); out.append(a)
        return out
    def _orden(self, p): return {"critica":0,"aviso":1,"informativa":2,"normal":3}.get(p,9)
