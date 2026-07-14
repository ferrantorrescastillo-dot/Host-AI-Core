from __future__ import annotations

"""
Pipeline: produccion_real

Enlaza `MotorProduccionReal` con la infraestructura de pipelines del proyecto.
Solo docstrings añadidos durante la auditoría para mejorar trazabilidad.
"""

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineProduccionReal(BasePipeline):
    nombre = "produccion_real"
    descripcion = "Pipeline de producción real: tareas, fases, cronograma y reparto operativo."
    acciones_soportadas = [
        "planificar_evento",
        "listar_planes",
        "diagnosticar_plan",
        "repartir_trabajo",
    ]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "planificar_evento":
            datos = self.core.produccion_real.planificar_evento(
                evento_id=p["evento_id"],
                hora_inicio=p.get("hora_inicio", "08:00"),
                equipo_cocina=p.get("equipo_cocina", 2),
                incluir_logistica=p.get("incluir_logistica", True),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=datos.get("avisos", []) or ["Revisar cronograma antes del servicio."],
                requiere_aprobacion=datos.get("estado") != "ok",
            )

        if solicitud.accion == "listar_planes":
            planes = self.core.produccion_real.listar_planes()
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=f"Planes de producción real: {len(planes)}.",
                datos={"planes": planes},
                acciones_recomendadas=[],
                requiere_aprobacion=False,
            )

        if solicitud.accion == "diagnosticar_plan":
            datos = self.core.produccion_real.diagnosticar_plan(p["plan_id"])
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=datos.get("avisos", []),
                requiere_aprobacion=datos.get("estado") != "ok",
            )

        if solicitud.accion == "repartir_trabajo":
            datos = self.core.produccion_real.sugerir_trabajo_por_responsable(p["plan_id"])
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Asignar responsables reales si hace falta."],
                requiere_aprobacion=False,
            )

        return ResultadoPipeline(
            ok=False,
            pipeline=self.nombre,
            accion=solicitud.accion,
            mensaje="Acción no implementada.",
            errores=[f"Acción no implementada: {solicitud.accion}"],
        )
