from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineImportadorInventarioExcel(BasePipeline):
    nombre = "importador_inventario_excel"
    descripcion = "Pipeline para importar inventario/stock desde Excel."
    acciones_soportadas = ["vista_previa", "importar", "comparar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "vista_previa":
            datos = self.core.importador_inventario_excel.vista_previa(
                ruta_archivo=p["ruta_archivo"],
                filas_preview=p.get("filas_preview", 100),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar cambios antes de importar."],
                requiere_aprobacion=bool(datos.get("errores")),
            )

        if solicitud.accion == "importar":
            datos = self.core.importador_inventario_excel.importar(
                ruta_archivo=p["ruta_archivo"],
                filas_preview=p.get("filas_preview", 1000),
                crear_articulos=p.get("crear_articulos", True),
                actualizar_stock=p.get("actualizar_stock", True),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar stock actual después de importar."],
                requiere_aprobacion=bool(datos.get("errores")),
            )

        if solicitud.accion == "comparar":
            datos = self.core.importador_inventario_excel.comparar_inventario(
                ruta_archivo=p["ruta_archivo"],
                filas_preview=p.get("filas_preview", 1000),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Importar si los cambios son correctos."],
                requiere_aprobacion=False,
            )

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
