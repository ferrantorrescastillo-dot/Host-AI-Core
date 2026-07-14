from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineProduccionCompleta(BasePipeline):
    nombre = "produccion_completa"
    descripcion = "Pipeline inicial que conecta evento, stock, compras y simulación."
    acciones_soportadas = ["analizar_evento", "generar_pedidos_desde_evento", "listar_informes"]
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "analizar_evento":
            datos = self.core.produccion_completa.analizar_evento(
                evento_id=p["evento_id"],
                hora_inicio_produccion=p.get("hora_inicio_produccion", "08:00"),
                margen_seguridad_min=p.get("margen_seguridad_min", 60),
                generar_compras=p.get("generar_compras", True),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, datos.get("avisos", []) or ["Revisar informe de producción completa."], datos.get("estado") != "ok")
        if solicitud.accion == "generar_pedidos_desde_evento":
            datos = self.core.produccion_completa.generar_pedidos_desde_evento(p["evento_id"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, ["Revisar pedidos sugeridos antes de enviar."], True)
        if solicitud.accion == "listar_informes":
            informes = self.core.produccion_completa.listar_informes()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, f"Informes de producción completa: {len(informes)}.", {"informes": informes}, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
