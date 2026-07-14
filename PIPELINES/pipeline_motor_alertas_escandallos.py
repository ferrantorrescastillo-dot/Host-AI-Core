from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineMotorAlertasEscandallos(BasePipeline):
    nombre='motor_alertas_escandallos'
    descripcion='Genera alertas de escandallos: pérdidas, ingredientes sin precio, duplicados, mermas y recetas incompletas.'
    acciones_soportadas=['generar','exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p=solicitud.parametros
        if solicitud.accion=='generar':
            d=self.core.motor_alertas_escandallos.generar_alertas(p.get('analisis'), p.get('escandallos'))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        if solicitud.accion=='exportar':
            d=self.core.motor_alertas_escandallos.exportar_alertas(p['alertas'], p.get('nombre',''))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        return ResultadoPipeline(False,self.nombre,solicitud.accion,'Acción no implementada.',errores=[f'Acción no implementada: {solicitud.accion}'])
