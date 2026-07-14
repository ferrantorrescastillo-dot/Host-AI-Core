from MODELOS.api_interna import ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline
class PipelineMotorRecomendacionesCompras(BasePipeline):
    nombre="motor_recomendaciones_compras"
    descripcion="Genera recomendaciones inteligentes de compras."
    acciones_soportadas=["generar","exportar"]
    def _ejecutar(self, solicitud):
        p=solicitud.parametros
        if solicitud.accion=="generar":
            d=self.core.motor_recomendaciones_compras.generar_recomendaciones()
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d["lectura_host_ai"],d,[],False)
        if solicitud.accion=="exportar":
            d=self.core.motor_recomendaciones_compras.exportar_recomendaciones(p["recomendaciones"],p.get("nombre",""))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d["lectura_host_ai"],d,[],False)
        return ResultadoPipeline(False,self.nombre,solicitud.accion,"Acción no implementada.",errores=[f"Acción no implementada: {solicitud.accion}"])
