from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import json

from MODELOS.historico_stock import RegistroHistoricoStock, AnalisisHistoricoStock


class HistoricoInteligenteStock:
    """
    Host AI 3.0.3.6.3

    Guarda histórico de entradas/salidas/ajustes de stock.
    En esta fase se integra especialmente con entradas de factura.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.facturas_dir / "historico_stock.json"
        self.registros: List[RegistroHistoricoStock] = self._cargar()

    def registrar_movimiento(self, movimiento: Dict[str, Any]) -> Dict[str, Any]:
        articulo_id = movimiento.get("articulo_id", "")
        nombre = movimiento.get("nombre_articulo", "")
        cantidad = float(movimiento.get("cantidad", 0) or 0)
        unidad = movimiento.get("unidad", "")

        if not articulo_id or not nombre or cantidad == 0:
            return {
                "registrado": False,
                "errores": ["Falta articulo_id, nombre o cantidad."],
                "lectura_host_ai": "No se registró histórico de stock.",
            }

        stock_resultante = self._stock_actual_articulo(articulo_id)
        reg = RegistroHistoricoStock(
            articulo_id=articulo_id,
            nombre_articulo=nombre,
            tipo=movimiento.get("tipo", "entrada"),
            cantidad=cantidad,
            unidad=unidad,
            stock_resultante=stock_resultante,
            proveedor_id=movimiento.get("proveedor_id", ""),
            numero_factura=movimiento.get("numero_factura", ""),
            fecha_factura=movimiento.get("fecha_factura", ""),
            motivo=movimiento.get("motivo", "Entrada factura"),
            origen=movimiento.get("origen", "factura"),
            datos=movimiento,
        )
        self.registros.append(reg)
        self._guardar()
        return {
            "registrado": True,
            "registro": reg.to_dict(),
            "lectura_host_ai": f"Histórico stock registrado: {nombre} {cantidad} {unidad}.",
        }

    def registrar_desde_aplicacion(self, resultado_aplicacion: Dict[str, Any]) -> Dict[str, Any]:
        if not resultado_aplicacion.get("aplicado"):
            return {
                "registrado": False,
                "errores": ["La aplicación de stock no fue aplicada."],
                "lectura_host_ai": "No se registró histórico de stock.",
            }
        mov = dict(resultado_aplicacion.get("movimiento", {}))
        mov.setdefault("articulo_id", resultado_aplicacion.get("articulo_id", ""))
        mov.setdefault("nombre_articulo", resultado_aplicacion.get("nombre_articulo", ""))
        mov.setdefault("cantidad", resultado_aplicacion.get("cantidad", 0))
        mov.setdefault("unidad", resultado_aplicacion.get("unidad", ""))
        mov.setdefault("proveedor_id", resultado_aplicacion.get("proveedor_id", ""))
        mov.setdefault("numero_factura", resultado_aplicacion.get("numero_factura", ""))
        mov.setdefault("fecha_factura", resultado_aplicacion.get("fecha_factura", ""))
        mov["tipo"] = "entrada"
        mov["origen"] = "actualizacion_factura"
        return self.registrar_movimiento(mov)

    def analizar_articulo(self, articulo_id: str) -> Dict[str, Any]:
        regs = [r for r in self.registros if r.articulo_id == articulo_id]
        if not regs:
            return {"encontrado": False, "lectura_host_ai": "No hay histórico de stock para este artículo."}

        entradas = sum(r.cantidad for r in regs if r.tipo == "entrada")
        salidas = sum(r.cantidad for r in regs if r.tipo == "salida")
        ajustes = sum(r.cantidad for r in regs if r.tipo == "ajuste")
        analisis = AnalisisHistoricoStock(
            articulo_id=articulo_id,
            nombre_articulo=regs[-1].nombre_articulo,
            total_registros=len(regs),
            entradas_totales=round(entradas, 4),
            salidas_totales=round(salidas, 4),
            ajustes_totales=round(ajustes, 4),
            stock_estimado=round(entradas - salidas + ajustes, 4),
            unidad_principal=regs[-1].unidad,
            registros=[r.to_dict() for r in regs],
        )
        datos = analisis.to_dict()
        datos["encontrado"] = True
        datos["lectura_host_ai"] = f"Histórico stock {analisis.nombre_articulo}: {analisis.total_registros} movimientos."
        return datos

    def listar_historico(self) -> Dict[str, Any]:
        data = [r.to_dict() for r in self.registros]
        return {
            "registros": data,
            "total": len(data),
            "lectura_host_ai": f"Histórico de stock: {len(data)} registros.",
        }

    def exportar(self) -> Dict[str, Any]:
        self._guardar()
        return {"archivo": str(self.path), "lectura_host_ai": "Histórico de stock exportado."}

    def _stock_actual_articulo(self, articulo_id: str) -> float:
        actualizador = getattr(self.core, "actualizador_inteligente_stock_factura", None)
        if actualizador:
            try:
                return float(actualizador.stock_actual_articulo(articulo_id).get("cantidad", 0) or 0)
            except Exception:
                return 0.0
        return 0.0

    def _cargar(self) -> List[RegistroHistoricoStock]:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                return [RegistroHistoricoStock(**r) for r in raw.get("registros", [])]
            except Exception:
                return []
        return []

    def _guardar(self):
        self.path.write_text(
            json.dumps({"version": "3.0.3.6.3", "registros": [r.to_dict() for r in self.registros]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
