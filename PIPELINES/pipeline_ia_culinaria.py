from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineIACulinaria(BasePipeline):
    nombre = "ia_culinaria"
    descripcion = "Pipeline de IA culinaria: ideas, sobras, platos, escandallos y análisis."
    acciones_soportadas = [
        "proponer_platos_stock",
        "crear_idea",
        "analizar_idea",
        "convertir_idea_escandallo",
    ]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "proponer_platos_stock":
            datos = self.core.ia_culinaria.proponer_platos_con_stock(
                objetivo=p.get("objetivo", "comida_personal"),
                raciones=p.get("raciones", 4),
                estilo=p.get("estilo", ""),
                limitar=p.get("limitar", 3),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=datos.get("posibles_acciones", []),
                requiere_aprobacion=False,
            )

        if solicitud.accion == "crear_idea":
            datos = self.core.ia_culinaria.crear_idea(
                nombre=p["nombre"],
                ingredientes=p.get("ingredientes", []),
                raciones=p.get("raciones", 4),
                objetivo=p.get("objetivo", "plato"),
                tecnica_principal=p.get("tecnica_principal", ""),
                estilo=p.get("estilo", ""),
                fases=p.get("fases"),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Analizar idea o convertirla en escandallo."],
                requiere_aprobacion=False,
            )

        if solicitud.accion == "analizar_idea":
            datos = self.core.ia_culinaria.analizar_idea(
                idea_id=p["idea_id"],
                precio_venta_por_racion=p.get("precio_venta_por_racion", 0.0),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=datos.get("acciones_recomendadas", []),
                requiere_aprobacion=datos.get("estado") != "ok",
            )

        if solicitud.accion == "convertir_idea_escandallo":
            datos = self.core.ia_culinaria.convertir_idea_en_escandallo(
                idea_id=p["idea_id"],
                receta_id=p.get("receta_id", ""),
                raciones_base=p.get("raciones_base"),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Calcular coste o planificar producción."],
                requiere_aprobacion=False,
            )

        return ResultadoPipeline(
            ok=False,
            pipeline=self.nombre,
            accion=solicitud.accion,
            mensaje="Acción no implementada.",
            errores=[f"Acción no implementada: {solicitud.accion}"],
        )
