from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineProveedoresPDF(BasePipeline):
    nombre = "proveedores_pdf"
    descripcion = "Pipeline de detección y aprendizaje de proveedores en PDFs/facturas."
    acciones_soportadas = ["detectar_en_pdf", "detectar_desde_texto", "aprender", "listar", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "detectar_en_pdf":
            d = self.core.detector_proveedores_pdf.detectar_en_pdf(p["ruta_archivo"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, ["Aprender proveedor si la confianza es baja."], d.get("requiere_aprendizaje", False))
        if solicitud.accion == "detectar_desde_texto":
            d = self.core.detector_proveedores_pdf.detectar_desde_texto(p["texto"], p.get("proveedor_sugerido",""), p.get("cif_sugerido",""), p.get("contexto",{}))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, ["Aprender proveedor si la confianza es baja."], d.get("requiere_aprendizaje", False))
        if solicitud.accion == "aprender":
            d = self.core.detector_proveedores_pdf.aprender_proveedor(p["nombre"], p.get("proveedor_id",""), p.get("cif",""), p.get("dominio",""), p.get("palabras_clave",[]), p.get("categoria",""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "listar":
            d = self.core.detector_proveedores_pdf.listar_proveedores()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.detector_proveedores_pdf.exportar_diccionario()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
