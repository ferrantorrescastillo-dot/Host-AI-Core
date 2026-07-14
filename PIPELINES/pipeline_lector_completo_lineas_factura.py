from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineLectorCompletoLineasFactura(BasePipeline):
    nombre = "lector_completo_lineas_factura"
    descripcion = "Pipeline integrado PDF/texto -> proveedor + líneas estructuradas de factura."
    acciones_soportadas = ["leer_pdf_completo", "leer_texto_completo", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "leer_pdf_completo":
            datos = self.core.lector_completo_lineas_factura.leer_factura_pdf_completa(
                ruta_archivo=p["ruta_archivo"],
                exportar_json=p.get("exportar_json", True),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar líneas antes de relacionarlas con artículos."],
                requiere_aprobacion=bool(datos.get("avisos")),
            )

        if solicitud.accion == "leer_texto_completo":
            datos = self.core.lector_completo_lineas_factura.leer_factura_texto_completa(
                texto=p["texto"],
                proveedor_sugerido=p.get("proveedor_sugerido", ""),
                cif_sugerido=p.get("cif_sugerido", ""),
                numero_factura=p.get("numero_factura", ""),
                fecha_factura=p.get("fecha_factura", ""),
                total_factura_detectado=p.get("total_factura_detectado", 0.0),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar líneas antes de relacionarlas con artículos."],
                requiere_aprobacion=bool(datos.get("avisos")),
            )

        if solicitud.accion == "exportar":
            datos = self.core.lector_completo_lineas_factura.exportar_lectura(p["lectura"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
