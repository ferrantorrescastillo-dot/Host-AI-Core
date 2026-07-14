from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime


class ActualizadorInteligenteStockFactura:
    """
    Host AI 3.0.3.6.2

    Aplica entradas de stock desde facturas.
    - Valida movimientos.
    - Suma stock en el motor de stock.
    - Guarda log.
    - Puede preparar informe desde relaciones y aplicarlo.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.facturas_dir / "log_actualizaciones_stock.json"
        self.log = self._cargar_log()

    def aplicar_movimiento(self, movimiento: Dict[str, Any], forzar: bool = False) -> Dict[str, Any]:
        articulo_id = movimiento.get("articulo_id", "")
        nombre = movimiento.get("nombre_articulo", "")
        cantidad = float(movimiento.get("cantidad", 0) or 0)
        unidad = movimiento.get("unidad", "") or "ud"
        proveedor_id = movimiento.get("proveedor_id", "")
        requiere_revision = bool(movimiento.get("requiere_revision", False))

        errores = []
        avisos = []

        if not articulo_id:
            errores.append("No hay articulo_id.")
        if not nombre:
            errores.append("No hay nombre de artículo.")
        if cantidad <= 0:
            errores.append("Cantidad inválida.")
        if requiere_revision and not forzar:
            errores.append("Movimiento requiere revisión. Usa forzar=True para aplicarlo.")

        if errores:
            resultado = {
                "aplicado": False,
                "errores": errores,
                "avisos": avisos,
                "movimiento": movimiento,
                "lectura_host_ai": f"No se aplicó stock: {', '.join(errores)}",
            }
            self._registrar_log(resultado)
            return resultado

        stock = getattr(self.core, "stock", None)
        if stock is None:
            resultado = {
                "aplicado": False,
                "errores": ["No existe motor de stock."],
                "avisos": avisos,
                "movimiento": movimiento,
                "lectura_host_ai": "No se aplicó stock: no existe motor de stock.",
            }
            self._registrar_log(resultado)
            return resultado

        try:
            stock.registrar_entrada(
                nombre=nombre,
                cantidad=cantidad,
                unidad=unidad,
                articulo_id=articulo_id,
                familia=movimiento.get("familia", ""),
                ubicacion=movimiento.get("ubicacion", ""),
                proveedor=proveedor_id,
                caducidad=movimiento.get("caducidad", ""),
                motivo=f"Entrada factura {movimiento.get('numero_factura', '')}".strip(),
            )
        except TypeError:
            try:
                stock.registrar_entrada(nombre, cantidad, unidad, articulo_id)
            except TypeError:
                stock.registrar_entrada(nombre=nombre, cantidad=cantidad, unidad=unidad)

        resultado = {
            "aplicado": True,
            "articulo_id": articulo_id,
            "nombre_articulo": nombre,
            "cantidad": cantidad,
            "unidad": unidad,
            "proveedor_id": proveedor_id,
            "numero_factura": movimiento.get("numero_factura", ""),
            "fecha_factura": movimiento.get("fecha_factura", ""),
            "fecha_aplicacion": datetime.now().isoformat(timespec="seconds"),
            "forzado": forzar,
            "errores": [],
            "avisos": avisos,
            "movimiento": movimiento,
            "lectura_host_ai": f"Stock actualizado: {nombre} +{cantidad} {unidad}.",
        }
        self._registrar_log(resultado)
        hist = getattr(self.core, "historico_inteligente_stock", None)
        if hist is not None and resultado.get("aplicado"):
            resultado["historico"] = hist.registrar_desde_aplicacion(resultado)

        if hasattr(self.core, "persistencia"):
            try:
                self.core.persistencia.guardar_todo()
            except Exception:
                pass

        return resultado

    def aplicar_informe(self, informe: Dict[str, Any], forzar: bool = False) -> Dict[str, Any]:
        resultados = []
        for mov in informe.get("movimientos", []):
            resultados.append(self.aplicar_movimiento(mov, forzar=forzar))

        aplicados = sum(1 for r in resultados if r.get("aplicado"))
        bloqueados = len(resultados) - aplicados
        return {
            "resultados": resultados,
            "total": len(resultados),
            "aplicados": aplicados,
            "bloqueados": bloqueados,
            "lectura_host_ai": f"Actualización stock: {aplicados} aplicados, {bloqueados} bloqueados.",
        }

    def preparar_y_aplicar(self, informe_relaciones: Dict[str, Any], forzar: bool = False) -> Dict[str, Any]:
        informe_stock = self.core.base_actualizacion_stock_factura.preparar_informe(informe_relaciones)
        aplicacion = self.aplicar_informe(informe_stock, forzar=forzar)
        aplicacion["informe_stock"] = informe_stock
        return aplicacion

    def stock_actual_articulo(self, articulo_id: str) -> Dict[str, Any]:
        stock = getattr(self.core, "stock", None)
        if stock is None:
            return {"encontrado": False, "cantidad": 0.0, "lectura_host_ai": "No existe motor de stock."}
        try:
            datos = stock.stock_actual()
            items = datos.get("items", [])
            cantidad = 0.0
            encontrados = []
            for item in items:
                if item.get("articulo_id") == articulo_id:
                    cantidad += float(item.get("cantidad", 0) or 0)
                    encontrados.append(item)
            return {
                "encontrado": bool(encontrados),
                "articulo_id": articulo_id,
                "cantidad": round(cantidad, 4),
                "items": encontrados,
                "lectura_host_ai": f"Stock {articulo_id}: {round(cantidad, 4)}.",
            }
        except Exception as exc:
            return {"encontrado": False, "cantidad": 0.0, "error": str(exc), "lectura_host_ai": "No se pudo consultar stock."}

    def listar_log(self) -> Dict[str, Any]:
        return {
            "log": self.log,
            "total": len(self.log),
            "lectura_host_ai": f"Log de actualizaciones de stock: {len(self.log)} registros.",
        }

    def exportar_log(self) -> Dict[str, Any]:
        self._guardar_log()
        return {
            "archivo": str(self.log_path),
            "lectura_host_ai": "Log de actualizaciones de stock exportado.",
        }

    def _registrar_log(self, resultado: Dict[str, Any]):
        self.log.append(resultado)
        self._guardar_log()

    def _cargar_log(self) -> List[Dict[str, Any]]:
        if self.log_path.exists():
            try:
                return json.loads(self.log_path.read_text(encoding="utf-8")).get("log", [])
            except Exception:
                return []
        return []

    def _guardar_log(self):
        self.log_path.write_text(json.dumps({"version": "3.0.3.6.2", "log": self.log}, ensure_ascii=False, indent=2), encoding="utf-8")
