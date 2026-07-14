from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import json

from MODELOS.alertas_stock import AlertaStock


class AlertasInteligentesStock:
    """
    Host AI 3.0.3.6.4

    Genera alertas de stock:
    - stock bajo
    - sin stock
    - sin movimientos
    - exceso potencial
    """

    STOCK_MINIMO_DEFAULT = 5.0
    STOCK_EXCESO_DEFAULT = 50.0

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.facturas_dir / "alertas_stock.json"
        self.alertas: List[Dict[str, Any]] = self._cargar()

    def generar_alertas_articulo(self, articulo_id: str, stock_minimo: float = None, stock_exceso: float = None) -> Dict[str, Any]:
        stock_minimo = self.STOCK_MINIMO_DEFAULT if stock_minimo is None else float(stock_minimo)
        stock_exceso = self.STOCK_EXCESO_DEFAULT if stock_exceso is None else float(stock_exceso)

        actualizador = getattr(self.core, "actualizador_inteligente_stock_factura", None)
        historico = getattr(self.core, "historico_inteligente_stock", None)

        stock_actual = 0.0
        nombre = articulo_id
        unidad = ""
        if actualizador:
            s = actualizador.stock_actual_articulo(articulo_id)
            stock_actual = float(s.get("cantidad", 0) or 0)
            items = s.get("items", [])
            if items:
                nombre = items[-1].get("nombre", nombre) or items[-1].get("nombre_articulo", nombre)
                unidad = items[-1].get("unidad", unidad)

        analisis = None
        if historico:
            analisis = historico.analizar_articulo(articulo_id)
            if analisis.get("encontrado"):
                nombre = analisis.get("nombre_articulo", nombre)
                unidad = analisis.get("unidad_principal", unidad)
                # Si el motor de stock no devuelve cantidad, usa estimación histórica.
                if stock_actual == 0:
                    stock_actual = float(analisis.get("stock_estimado", 0) or 0)

        alertas = []
        if not analisis or not analisis.get("encontrado"):
            alertas.append(AlertaStock(
                articulo_id=articulo_id,
                nombre_articulo=nombre,
                tipo="sin_historico",
                nivel="aviso",
                mensaje="No hay histórico de stock para este artículo.",
                stock_actual=stock_actual,
                unidad=unidad,
                stock_minimo=stock_minimo,
                accion_sugerida="Registrar entradas/salidas para poder analizar.",
            ))

        if stock_actual <= 0:
            alertas.append(AlertaStock(
                articulo_id=articulo_id,
                nombre_articulo=nombre,
                tipo="sin_stock",
                nivel="critico",
                mensaje="Artículo sin stock disponible.",
                stock_actual=stock_actual,
                unidad=unidad,
                stock_minimo=stock_minimo,
                accion_sugerida="Comprar o revisar recuento físico.",
                datos=analisis or {},
            ))
        elif stock_actual < stock_minimo:
            alertas.append(AlertaStock(
                articulo_id=articulo_id,
                nombre_articulo=nombre,
                tipo="stock_bajo",
                nivel="aviso",
                mensaje=f"Stock bajo: {stock_actual} {unidad}.",
                stock_actual=stock_actual,
                unidad=unidad,
                stock_minimo=stock_minimo,
                accion_sugerida="Añadir al próximo pedido.",
                datos=analisis or {},
            ))
        elif stock_actual > stock_exceso:
            alertas.append(AlertaStock(
                articulo_id=articulo_id,
                nombre_articulo=nombre,
                tipo="posible_exceso",
                nivel="info",
                mensaje=f"Stock alto: {stock_actual} {unidad}.",
                stock_actual=stock_actual,
                unidad=unidad,
                stock_minimo=stock_minimo,
                accion_sugerida="Revisar rotación y caducidad.",
                datos=analisis or {},
            ))

        return self._salida(alertas)

    def generar_alertas_todos(self, stock_minimo: float = None, stock_exceso: float = None) -> Dict[str, Any]:
        historico = getattr(self.core, "historico_inteligente_stock", None)
        if not historico:
            return {"alertas": [], "total": 0, "lectura_host_ai": "No existe histórico de stock."}

        articulos = sorted({r.articulo_id for r in historico.registros})
        todas = []
        for aid in articulos:
            r = self.generar_alertas_articulo(aid, stock_minimo=stock_minimo, stock_exceso=stock_exceso)
            todas.extend(r.get("alertas", []))

        self.alertas = todas
        self._guardar()
        return {
            "alertas": todas,
            "total": len(todas),
            "lectura_host_ai": f"Alertas de stock generadas: {len(todas)}.",
        }

    def listar_alertas(self) -> Dict[str, Any]:
        return {
            "alertas": self.alertas,
            "total": len(self.alertas),
            "lectura_host_ai": f"Alertas de stock guardadas: {len(self.alertas)}.",
        }

    def exportar_alertas(self) -> Dict[str, Any]:
        self._guardar()
        return {"archivo": str(self.path), "lectura_host_ai": "Alertas de stock exportadas."}

    def _salida(self, alertas: List[AlertaStock]) -> Dict[str, Any]:
        data = [a.to_dict() for a in alertas]
        self.alertas.extend(data)
        self._guardar()
        return {
            "alertas": data,
            "total": len(data),
            "lectura_host_ai": f"Alertas de stock generadas: {len(data)}.",
        }

    def _cargar(self) -> List[Dict[str, Any]]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8")).get("alertas", [])
            except Exception:
                return []
        return []

    def _guardar(self):
        self.path.write_text(json.dumps({"version": "3.0.3.6.4", "alertas": self.alertas}, ensure_ascii=False, indent=2), encoding="utf-8")
