from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineCostes(BasePipeline):
    nombre = "costes"
    descripcion = "Pipeline de costes inteligentes para recetas, eventos, márgenes y simulaciones."
    acciones_soportadas = [
        "registrar_precio",
        "listar_precios",
        "calcular_receta",
        "calcular_evento",
        "simular_variacion_precio_receta",
        "diagnosticar_evento",
    ]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "registrar_precio":
            datos = self.core.costes_inteligente.registrar_precio(
                nombre=p["nombre"],
                precio_unitario=p["precio_unitario"],
                unidad=p["unidad"],
                articulo_id=p.get("articulo_id", ""),
                proveedor=p.get("proveedor", ""),
                familia=p.get("familia", ""),
                fecha=p.get("fecha", ""),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=f"Precio registrado: {datos['nombre']} a {datos['precio_unitario']} €/{datos['unidad']}.",
                datos={"precio": datos},
                acciones_recomendadas=["Recalcular escandallos afectados."],
                requiere_aprobacion=False,
            )

        if solicitud.accion == "listar_precios":
            datos = self.core.costes_inteligente.listar_precios()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "calcular_receta":
            datos = self.core.costes_inteligente.calcular_coste_receta(
                receta_id=p["receta_id"],
                raciones=p["raciones"],
                precio_venta_por_racion=p.get("precio_venta_por_racion", 0.0),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=datos.get("avisos", []),
                requiere_aprobacion=datos.get("estado") != "ok",
            )

        if solicitud.accion == "calcular_evento":
            datos = self.core.costes_inteligente.calcular_coste_evento(
                evento_id=p["evento_id"],
                precio_venta_por_pax=p.get("precio_venta_por_pax", 0.0),
                extras=p.get("extras", []),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=datos.get("avisos", []),
                requiere_aprobacion=datos.get("estado") != "ok",
            )

        if solicitud.accion == "simular_variacion_precio_receta":
            datos = self.core.costes_inteligente.simular_variacion_precio_receta(
                receta_id=p["receta_id"],
                raciones=p["raciones"],
                variacion_porcentaje=p["variacion_porcentaje"],
                precio_venta_por_racion=p.get("precio_venta_por_racion", 0.0),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar impacto en margen y food cost."],
                requiere_aprobacion=False,
            )

        if solicitud.accion == "diagnosticar_evento":
            datos = self.core.costes_inteligente.diagnosticar_evento_costes(
                evento_id=p["evento_id"],
                food_cost_objetivo=p.get("food_cost_objetivo", 30.0),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=datos.get("avisos", []),
                requiere_aprobacion=datos.get("estado") != "ok",
            )

        return ResultadoPipeline(
            ok=False,
            pipeline=self.nombre,
            accion=solicitud.accion,
            mensaje="Acción no implementada.",
            errores=[f"Acción no implementada: {solicitud.accion}"],
        )
