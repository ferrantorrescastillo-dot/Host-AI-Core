from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineAsistenteConversacional(BasePipeline):
    nombre = "asistente"
    descripcion = "Pipeline conversacional inicial para enrutar lenguaje natural hacia Host AI."
    acciones_soportadas = [
        "responder",
        "detectar_intencion",
        "historial",
    ]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "responder":
            datos = self.core.asistente_conversacional.responder(
                texto=p["texto"],
                contexto=p.get("contexto", {}),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=datos.get("acciones_recomendadas", []),
                requiere_aprobacion=datos.get("requiere_aprobacion", False),
            )

        if solicitud.accion == "detectar_intencion":
            intencion = self.core.asistente_conversacional.detectar_intencion(
                texto=p["texto"],
                contexto=p.get("contexto", {}),
            )
            datos = {"intencion": intencion.to_dict()}
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=f"Intención detectada: {intencion.intencion}.",
                datos=datos,
                acciones_recomendadas=intencion.avisos,
                requiere_aprobacion=bool(intencion.avisos),
            )

        if solicitud.accion == "historial":
            datos = self.core.asistente_conversacional.listar_historial()
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=[],
                requiere_aprobacion=False,
            )

        return ResultadoPipeline(
            ok=False,
            pipeline=self.nombre,
            accion=solicitud.accion,
            mensaje="Acción no implementada.",
            errores=[f"Acción no implementada: {solicitud.accion}"],
        )
