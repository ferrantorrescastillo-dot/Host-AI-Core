from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineMotorConversacional308(BasePipeline):
    nombre = 'motor_conversacional_308'
    descripcion = 'Gestiona conversación, contexto operativo, turnos y respuesta natural sobre Host AI.'
    acciones_soportadas = ['responder', 'historial', 'limpiar', 'exportar']

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros or {}
        if solicitud.accion == 'responder':
            d = self.core.motor_conversacional_308.responder(p.get('texto',''), p.get('contexto'), p.get('ejecutar_motor', False))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], d.get('requiere_aprobacion', False))
        if solicitud.accion == 'historial':
            d = self.core.motor_conversacional_308.historial_conversacion()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'limpiar':
            d = self.core.motor_conversacional_308.limpiar()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.motor_conversacional_308.exportar_conversacion(p.get('conversacion'), p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
