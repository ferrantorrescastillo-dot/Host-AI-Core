from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineStock(BasePipeline):
    nombre = "stock"
    descripcion = "Pipeline inicial de stock inteligente."
    acciones_soportadas = ["registrar_entrada", "consumir", "stock_actual", "diagnosticar", "ajustar_minimo", "predecir_necesidad", "movimientos"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "registrar_entrada":
            datos = self.core.stock.registrar_entrada(nombre=p["nombre"], cantidad=p["cantidad"], unidad=p["unidad"], familia=p.get("familia", ""), ubicacion=p.get("ubicacion", ""), proveedor=p.get("proveedor", ""), articulo_id=p.get("articulo_id", ""), caducidad=p.get("caducidad", ""), coste_unitario=p.get("coste_unitario", 0.0), motivo=p.get("motivo", "entrada mercancía"))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, f"Entrada registrada: {p['nombre']}.", datos, ["Revisar ubicación, caducidad y lote."], False)
        if solicitud.accion == "consumir":
            datos = self.core.stock.consumir(nombre=p["nombre"], cantidad=p["cantidad"], unidad=p["unidad"], motivo=p.get("motivo", "consumo producción"), articulo_id=p.get("articulo_id", ""))
            return ResultadoPipeline(datos["ok"], self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [] if datos["ok"] else ["Generar necesidad de compra por faltante."], not datos["ok"])
        if solicitud.accion == "stock_actual":
            datos = self.core.stock.stock_actual()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, ["Revisar mínimos y caducidades."], False)
        if solicitud.accion == "diagnosticar":
            datos = self.core.stock.diagnosticar_stock(dias_caducidad_alerta=p.get("dias_caducidad_alerta", 3))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [a["mensaje"] for a in datos.get("avisos", [])], datos["estado"] != "ok")
        if solicitud.accion == "ajustar_minimo":
            datos = self.core.stock.ajustar_minimo(nombre=p["nombre"], cantidad_minima=p["cantidad_minima"], articulo_id=p.get("articulo_id", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, f"Stock mínimo ajustado para {p['nombre']}.", datos, ["Diagnosticar stock para comprobar mínimos."], False)
        if solicitud.accion == "predecir_necesidad":
            datos = self.core.stock.predecir_necesidad(nombre=p["nombre"], cantidad_necesaria=p["cantidad_necesaria"], unidad=p["unidad"], articulo_id=p.get("articulo_id", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [] if datos["estado"] == "ok" else ["Registrar necesidad de compra."], datos["estado"] != "ok")
        if solicitud.accion == "movimientos":
            datos = {"movimientos": self.core.stock.movimientos_listado()}
            return ResultadoPipeline(True, self.nombre, solicitud.accion, f"Movimientos de stock: {len(datos['movimientos'])}.", datos, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
