from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelinePDFFacturas(BasePipeline):
    nombre = "pdf_facturas"
    descripcion = "Pipeline lector de PDF y detección básica de facturas."
    acciones_soportadas = ["analizar_pdf", "detectar_factura_texto", "exportar_analisis_pdf"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "analizar_pdf":
            datos = self.core.lector_pdf_facturas.analizar_pdf(
                ruta_archivo=p["ruta_archivo"],
                exportar_json=p.get("exportar_json", True),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar detección antes de importar factura."],
                requiere_aprobacion=datos.get("deteccion_factura", {}).get("confianza", 0) < 70,
            )

        if solicitud.accion == "detectar_factura_texto":
            datos = self.core.lector_pdf_facturas.detectar_factura_desde_texto(p["texto"])
            datos["lectura_host_ai"] = f"Factura detectada con confianza {datos.get('confianza', 0)}%."
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=[],
                requiere_aprobacion=datos.get("confianza", 0) < 70,
            )

        if solicitud.accion == "exportar_analisis_pdf":
            datos = self.core.lector_pdf_facturas.exportar_analisis_json(
                analisis=p["analisis"],
                nombre=p.get("nombre", ""),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
