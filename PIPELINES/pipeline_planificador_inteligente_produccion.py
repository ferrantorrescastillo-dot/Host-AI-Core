"""Pipeline del planificador inteligente de producción.

RC2.8: documentación interna y contrato público sin cambiar comportamiento."""

from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelinePlanificadorInteligenteProduccion(BasePipeline):
    nombre = 'planificador_inteligente_produccion'
    descripcion = 'Planifica producción por prioridades, dependencias, tiempos activos/pasivos y jornada.'
    acciones_soportadas = ['planificar', 'exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'planificar':
            d = self.core.planificador_inteligente_produccion.planificar_produccion(p.get('elaboraciones'), p.get('jornada_horas', 7.5), p.get('cocineros', 3), p.get('hora_inicio', '08:00'))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.planificador_inteligente_produccion.exportar_planificacion(p['planificacion'], p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])

__all__ = ["PipelinePlanificadorInteligenteProduccion"]
