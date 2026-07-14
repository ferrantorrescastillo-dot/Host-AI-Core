from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.reconciliacion_stock_305 import DiferenciaReconciliacionStock, InformeReconciliacionStock

class ReconciliadorInteligenteStock:
    """Host AI 3.0.5.4 - Reconciliador Inteligente de Stock."""
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.stock_dir = self.base_dir / "DATOS" / "stock"
        self.stock_dir.mkdir(parents=True, exist_ok=True)

    def reconciliar_stock(self, inventario_fisico: List[Dict[str, Any]] | None = None, tolerancia: float = 0.01) -> Dict[str, Any]:
        stock = getattr(self.core, "stock", None)
        actual = stock.stock_actual() if stock else {"items": []}
        teorico: Dict[str, Dict[str, Any]] = {}
        for item in actual.get("items", []):
            clave = item.get("articulo_id") or item.get("clave") or item.get("nombre", "").lower().strip()
            teorico[clave] = {"clave": clave, "nombre": item.get("nombre", clave), "articulo_id": item.get("articulo_id", ""), "unidad": item.get("unidad", ""), "cantidad": float(item.get("cantidad", 0) or 0), "lotes": item.get("lotes", [])}

        fisico = self._normalizar_inventario(inventario_fisico, teorico)
        claves = sorted(set(teorico.keys()) | set(fisico.keys()))
        diferencias: List[Dict[str, Any]] = []
        valor_diff = 0.0
        for clave in claves:
            t = teorico.get(clave, {"clave": clave, "nombre": fisico.get(clave, {}).get("nombre", clave), "articulo_id": fisico.get(clave, {}).get("articulo_id", ""), "unidad": fisico.get(clave, {}).get("unidad", ""), "cantidad": 0.0, "lotes": []})
            f = fisico.get(clave, {"cantidad": t["cantidad"], "nombre": t["nombre"], "articulo_id": t["articulo_id"], "unidad": t["unidad"]})
            stock_teorico = round(float(t.get("cantidad", 0) or 0), 4)
            stock_real = round(float(f.get("cantidad", 0) or 0), 4)
            diff = round(stock_real - stock_teorico, 4)
            if abs(diff) <= tolerancia:
                continue
            pct = round((abs(diff) / stock_teorico * 100), 2) if stock_teorico else 100.0
            gravedad = "critica" if pct >= 30 or abs(diff) >= 10 else "aviso" if pct >= 10 or abs(diff) >= 2 else "informativa"
            causa = self._causa_probable(diff, t, f)
            accion = "Recontar físicamente y registrar ajuste de stock." if gravedad == "critica" else "Revisar movimientos y corregir si procede."
            coste = self._coste_medio(t.get("lotes", []))
            valor_diff += abs(diff) * coste
            diferencias.append(DiferenciaReconciliacionStock(
                clave=clave, nombre=t.get("nombre", f.get("nombre", clave)), articulo_id=t.get("articulo_id", f.get("articulo_id", "")), unidad=t.get("unidad", f.get("unidad", "")),
                stock_teorico=stock_teorico, stock_real=stock_real, diferencia=diff, porcentaje_diferencia=pct, gravedad=gravedad,
                causa_probable=causa, accion_recomendada=accion, datos={"coste_medio_estimado": coste}).to_dict())
        diferencias.sort(key=lambda d: ({"critica":0,"aviso":1,"informativa":2}.get(d["gravedad"],3), -abs(d["diferencia"]), d["nombre"]))
        criticas = sum(1 for d in diferencias if d.get("gravedad") == "critica")
        avisos = sum(1 for d in diferencias if d.get("gravedad") == "aviso")
        infos = sum(1 for d in diferencias if d.get("gravedad") == "informativa")
        estado = "critico" if criticas else "revisar" if avisos or infos else "ok"
        lectura = "Reconciliación de stock sin diferencias." if not diferencias else f"Reconciliación inteligente de stock: {len(diferencias)} diferencias detectadas ({criticas} críticas, {avisos} avisos)."
        return InformeReconciliacionStock(len(claves), len(diferencias), criticas, avisos, infos, round(valor_diff, 4), diferencias, {"estado": estado, "tolerancia": tolerancia}, lectura).to_dict()

    def exportar_reconciliacion(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        destino = self.stock_dir / (nombre or "reconciliacion_inteligente_stock.json")
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Reconciliación inteligente de stock exportada: {destino.name}."}

    def _normalizar_inventario(self, inventario_fisico, teorico):
        if inventario_fisico is None:
            return {k: {"cantidad": v["cantidad"], "nombre": v["nombre"], "articulo_id": v["articulo_id"], "unidad": v["unidad"]} for k, v in teorico.items()}
        salida={}
        for item in inventario_fisico:
            clave = item.get("articulo_id") or item.get("clave") or item.get("nombre", "").lower().strip()
            if not clave: continue
            salida[clave] = {"cantidad": float(item.get("cantidad", item.get("stock_real", 0)) or 0), "nombre": item.get("nombre", clave), "articulo_id": item.get("articulo_id", ""), "unidad": item.get("unidad", "")}
        return salida

    def _coste_medio(self, lotes):
        total=sum(float(l.get("cantidad",0) or 0)*float(l.get("coste_unitario",0) or 0) for l in lotes)
        qty=sum(float(l.get("cantidad",0) or 0) for l in lotes)
        return round(total/qty, 4) if qty else 0.0

    def _causa_probable(self, diff, teorico, fisico):
        if diff < 0:
            return "Falta stock físico: posible merma, consumo no registrado, error de inventario o salida pendiente."
        return "Sobra stock físico: posible entrada no registrada, devolución, error de conteo o lote sin actualizar."
