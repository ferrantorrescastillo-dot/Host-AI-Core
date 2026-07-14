from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineBuscadorArticulosParecidos(BasePipeline):
    nombre = "buscador_articulos_parecidos"
    descripcion = "Busca artículos internos parecidos a descripciones de factura."
    acciones_soportadas = ["buscar", "buscar_lote", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "buscar":
            datos = self.core.buscador_articulos_parecidos.buscar(
                descripcion=p["descripcion"],
                limite=p.get("limite", 5),
                proveedor_id=p.get("proveedor_id", ""),
            )
            return ResultadoPipeline(
                ok=datos["total_candidatos"] > 0,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar candidato si la confianza es baja."],
                requiere_aprobacion=(not datos.get("mejor_candidato") or datos["mejor_candidato"]["confianza"] < 80),
            )

        if solicitud.accion == "buscar_lote":
            datos = self.core.buscador_articulos_parecidos.buscar_lote(
                lineas=p["lineas"],
                limite=p.get("limite", 5),
                proveedor_id=p.get("proveedor_id", ""),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "exportar":
            datos = self.core.buscador_articulos_parecidos.exportar_busqueda(p["resultado"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
