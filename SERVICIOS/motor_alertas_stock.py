from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, date
import json
from MODELOS.alertas_inteligentes_stock_305 import AlertaGestionStock, InformeAlertasGestionStock

class MotorAlertasStock:
    """Host AI 3.0.5.2 - Motor de Alertas de Stock."""
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.stock_dir = self.base_dir / "DATOS" / "stock"
        self.stock_dir.mkdir(parents=True, exist_ok=True)

    def generar_alertas(self, dias_caducidad_alerta: int = 3, dias_sin_movimiento: int = 30) -> Dict[str, Any]:
        analisis = self.core.analizador_inteligente_stock.analizar_stock(dias_sin_movimiento=dias_sin_movimiento)
        alertas: List[Dict[str, Any]] = []
        for item in analisis.get("items", []):
            cantidad = float(item.get("cantidad", 0) or 0); minimo = float(item.get("stock_minimo", 0) or 0)
            if cantidad <= 0:
                alertas.append(self._alerta("stock_sin_existencias", "critica", f"{item['nombre']} no tiene stock disponible.", item, minimo, "Comprar o sustituir inmediatamente.").to_dict())
            elif minimo and cantidad < minimo:
                gravedad = "critica" if cantidad <= minimo * 0.25 else "aviso"
                alertas.append(self._alerta("stock_bajo", gravedad, f"{item['nombre']} está bajo mínimo: {cantidad} {item.get('unidad','')} < {minimo}.", item, minimo, "Revisar compra recomendada.").to_dict())
            if item.get("stock_maximo") and cantidad > float(item.get("stock_maximo", 0) or 0):
                alertas.append(self._alerta("exceso_stock", "aviso", f"{item['nombre']} tiene exceso de stock.", item, float(item.get("stock_maximo", 0)), "Priorizar consumo antes de comprar más.").to_dict())
            if item.get("dias_sin_movimiento", 0) >= dias_sin_movimiento:
                alertas.append(self._alerta("producto_parado", "informativa", f"{item['nombre']} lleva {item.get('dias_sin_movimiento')} días sin movimiento.", item, dias_sin_movimiento, "Revisar si sigue siendo necesario.").to_dict())
            if not item.get("ubicaciones"):
                alertas.append(self._alerta("sin_ubicacion", "informativa", f"{item['nombre']} no tiene ubicación registrada.", item, 0, "Asignar cámara, seco, congelador o almacén.").to_dict())

        for alerta in self._alertas_caducidad(dias_caducidad_alerta):
            alertas.append(alerta)
        # eliminar duplicados exactos tipo+clave+mensaje manteniendo orden crítico
        alertas.sort(key=lambda a: ({"critica":0,"aviso":1,"informativa":2}.get(a.get("gravedad"),3), a.get("nombre","")))
        criticas = sum(1 for a in alertas if a.get("gravedad") == "critica")
        avisos = sum(1 for a in alertas if a.get("gravedad") == "aviso")
        informativas = sum(1 for a in alertas if a.get("gravedad") == "informativa")
        lectura = "Stock sin alertas." if not alertas else f"Motor de alertas de stock: {len(alertas)} alertas ({criticas} críticas, {avisos} avisos, {informativas} informativas)."
        return InformeAlertasGestionStock(len(alertas), criticas, avisos, informativas, alertas, {"estado": "critico" if criticas else "revisar" if avisos else "ok"}, lectura).to_dict()

    def exportar_alertas(self, alertas: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        destino = self.stock_dir / (nombre or "alertas_gestion_stock.json")
        destino.write_text(json.dumps(alertas, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Alertas de stock exportadas: {destino.name}."}

    def _alerta(self, tipo: str, gravedad: str, mensaje: str, item: Dict[str, Any], umbral: float, accion: str) -> AlertaGestionStock:
        return AlertaGestionStock(tipo=tipo, gravedad=gravedad, mensaje=mensaje, clave=item.get("clave", ""), nombre=item.get("nombre", ""), articulo_id=item.get("articulo_id", ""), unidad=item.get("unidad", ""), cantidad=float(item.get("cantidad", 0) or 0), umbral=float(umbral or 0), accion_recomendada=accion, datos={"estado": item.get("estado"), "motivos": item.get("motivos", [])})

    def _alertas_caducidad(self, dias_alerta: int) -> List[Dict[str, Any]]:
        salida=[]; hoy=date.today()
        for lote in getattr(self.core.stock, "lotes", {}).values():
            cad = getattr(lote, "caducidad", "")
            if not cad: continue
            try:
                dias=(datetime.fromisoformat(cad).date()-hoy).days
            except Exception:
                salida.append(AlertaGestionStock("caducidad_invalida", "aviso", f"{lote.nombre} tiene caducidad inválida.", lote.articulo_id or lote.nombre.lower().strip(), lote.nombre, lote.articulo_id, lote.unidad, float(lote.cantidad), 0, "Corregir fecha de caducidad.").to_dict()); continue
            if dias < 0:
                salida.append(AlertaGestionStock("producto_caducado", "critica", f"{lote.nombre} caducó hace {abs(dias)} días.", lote.articulo_id or lote.nombre.lower().strip(), lote.nombre, lote.articulo_id, lote.unidad, float(lote.cantidad), 0, "Bloquear uso y revisar merma.").to_dict())
            elif dias <= dias_alerta:
                salida.append(AlertaGestionStock("caducidad_cercana", "aviso", f"{lote.nombre} caduca en {dias} días.", lote.articulo_id or lote.nombre.lower().strip(), lote.nombre, lote.articulo_id, lote.unidad, float(lote.cantidad), dias_alerta, "Priorizar consumo o producción.").to_dict())
        return salida
