from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineMotorAlertasProduccion(BasePipeline):
    nombre = 'motor_alertas_produccion'
    descripcion = 'Genera alertas inteligentes de producción a partir de tiempos, recursos, dependencias y capacidad.'
    acciones_soportadas = ['generar', 'exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'generar':
            d = self.core.motor_alertas_produccion.generar_alertas(p.get('elaboraciones'), p.get('jornada_horas', 7.5), p.get('cocineros', 3))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.motor_alertas_produccion.exportar_alertas(p['alertas'], p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
