from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineAprendizajeRelacionProveedor(BasePipeline):
    nombre = "aprendizaje_relacion_proveedor"
    descripcion = "Aprendizaje de relaciones artículo-proveedor para facturas."
    acciones_soportadas = ["aprender", "buscar", "aplicar_linea", "aplicar_bloque", "listar", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "aprender":
            datos = self.core.aprendizaje_relacion_proveedor.aprender(
                proveedor_id=p["proveedor_id"],
                texto_proveedor=p["texto_proveedor"],
                articulo_id=p["articulo_id"],
                nombre_articulo=p["nombre_articulo"],
                confianza=p.get("confianza", 100.0),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "buscar":
            datos = self.core.aprendizaje_relacion_proveedor.buscar_aprendizaje(
                proveedor_id=p["proveedor_id"],
                texto_proveedor=p["texto_proveedor"],
            )
            return ResultadoPipeline(datos.get("encontrado", False), self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], not datos.get("encontrado", False))

        if solicitud.accion == "aplicar_linea":
            datos = self.core.aprendizaje_relacion_proveedor.aplicar_a_linea(
                linea=p["linea"],
                proveedor_id=p.get("proveedor_id", ""),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "aplicar_bloque":
            datos = self.core.aprendizaje_relacion_proveedor.aplicar_a_bloque(
                bloque=p["bloque"],
                proveedor_id=p.get("proveedor_id", ""),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "listar":
            datos = self.core.aprendizaje_relacion_proveedor.listar()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "exportar":
            datos = self.core.aprendizaje_relacion_proveedor.exportar()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
