from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineRelacionadorAutomaticoArticulosFactura(BasePipeline):
    nombre = "relacionador_automatico_articulos_factura"
    descripcion = "Relaciona automáticamente líneas de factura con artículos internos."
    acciones_soportadas = ["relacionar_linea", "relacionar_bloque", "relacionar_texto", "relacionar_pdf", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "relacionar_linea":
            datos = self.core.relacionador_automatico_articulos_factura.relacionar_linea(
                linea=p["linea"],
                proveedor_id=p.get("proveedor_id", ""),
                limite_candidatos=p.get("limite_candidatos", 5),
            )
            return ResultadoPipeline(
                ok=bool(datos.get("articulo_id")),
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar relación si requiere revisión."],
                requiere_aprobacion=datos.get("requiere_revision", True),
            )

        if solicitud.accion == "relacionar_bloque":
            datos = self.core.relacionador_automatico_articulos_factura.relacionar_bloque(
                bloque=p["bloque"],
                limite_candidatos=p.get("limite_candidatos", 5),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar relaciones pendientes."],
                requiere_aprobacion=datos.get("requieren_revision", 0) > 0 or datos.get("sin_relacion", 0) > 0,
            )

        if solicitud.accion == "relacionar_texto":
            datos = self.core.relacionador_automatico_articulos_factura.relacionar_factura_texto(
                texto=p["texto"],
                proveedor_sugerido=p.get("proveedor_sugerido", ""),
                cif_sugerido=p.get("cif_sugerido", ""),
                numero_factura=p.get("numero_factura", ""),
                fecha_factura=p.get("fecha_factura", ""),
                total_factura_detectado=p.get("total_factura_detectado", 0.0),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, ["Revisar relaciones pendientes."], datos.get("sin_relacion", 0) > 0)

        if solicitud.accion == "relacionar_pdf":
            datos = self.core.relacionador_automatico_articulos_factura.relacionar_factura_pdf(p["ruta_archivo"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, ["Revisar relaciones pendientes."], datos.get("sin_relacion", 0) > 0)

        if solicitud.accion == "exportar":
            datos = self.core.relacionador_automatico_articulos_factura.exportar_informe(p["informe"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
