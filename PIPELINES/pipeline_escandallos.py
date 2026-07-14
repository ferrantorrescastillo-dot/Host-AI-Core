from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineEscandallos(BasePipeline):
    nombre = "escandallos"
    descripcion = "Pipeline inicial de escandallos inteligentes."
    acciones_soportadas = [
        "registrar_escandallo",
        "listar_escandallos",
        "buscar_escandallos",
        "editar_escandallo",
        "agregar_linea",
        "editar_linea",
        "eliminar_linea",
        "duplicar_escandallo",
        "eliminar_escandallo",
        "calcular_receta",
        "calcular_evento",
    ]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "registrar_escandallo":
            datos = self.core.escandallos_inteligente.registrar_escandallo(
                receta_id=p["receta_id"],
                nombre=p["nombre"],
                raciones_base=p["raciones_base"],
                lineas=p.get("lineas", []),
                grupo=p.get("grupo", ""),
                subgrupo=p.get("subgrupo", ""),
                observaciones=p.get("observaciones", ""),
                activo=p.get("activo", True),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=f"Escandallo registrado: {datos['nombre']}.",
                datos={"escandallo": datos},
                acciones_recomendadas=["Calcular necesidades de receta o evento."],
                requiere_aprobacion=False,
            )

        if solicitud.accion == "listar_escandallos":
            datos = {"escandallos": self.core.escandallos_inteligente.listar()}
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=f"Escandallos registrados: {len(datos['escandallos'])}.",
                datos=datos,
                acciones_recomendadas=[],
                requiere_aprobacion=False,
            )


        if solicitud.accion == "buscar_escandallos":
            escandallos = self.core.escandallos_inteligente.buscar(
                p.get("texto", ""), p.get("incluir_inactivos", True)
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion,
                f"Escandallos encontrados: {len(escandallos)}.",
                {"escandallos": escandallos}, [], False)

        if solicitud.accion == "editar_escandallo":
            datos = self.core.escandallos_inteligente.editar_escandallo(p["receta_id"], **p.get("cambios", {}))
            return ResultadoPipeline(True, self.nombre, solicitud.accion,
                f"Escandallo actualizado: {datos['nombre']}.", {"escandallo": datos}, [], False)

        if solicitud.accion == "agregar_linea":
            datos = self.core.escandallos_inteligente.agregar_linea(p["receta_id"], p["linea"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion,
                f"Ingrediente añadido: {datos['nombre']}.", {"linea": datos}, [], False)

        if solicitud.accion == "editar_linea":
            datos = self.core.escandallos_inteligente.editar_linea(p["receta_id"], p["linea_id"], **p.get("cambios", {}))
            return ResultadoPipeline(True, self.nombre, solicitud.accion,
                f"Ingrediente actualizado: {datos['nombre']}.", {"linea": datos}, [], False)

        if solicitud.accion == "eliminar_linea":
            ok = self.core.escandallos_inteligente.eliminar_linea(p["receta_id"], p["linea_id"])
            return ResultadoPipeline(ok, self.nombre, solicitud.accion,
                "Ingrediente eliminado." if ok else "No se encontró el ingrediente.", {"eliminado": ok}, [], False)

        if solicitud.accion == "duplicar_escandallo":
            datos = self.core.escandallos_inteligente.duplicar(p["receta_id"], p["nuevo_id"], p.get("nuevo_nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion,
                f"Escandallo duplicado: {datos['nombre']}.", {"escandallo": datos}, [], False)

        if solicitud.accion == "eliminar_escandallo":
            ok = self.core.escandallos_inteligente.eliminar(p["receta_id"])
            return ResultadoPipeline(ok, self.nombre, solicitud.accion,
                "Escandallo eliminado." if ok else "No se encontró el escandallo.", {"eliminado": ok}, [], False)

        if solicitud.accion == "calcular_receta":
            datos = self.core.escandallos_inteligente.calcular_necesidades_receta(
                receta_id=p["receta_id"],
                raciones=p["raciones"],
                origen=p.get("origen", ""),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Enviar necesidades a stock/compras."],
                requiere_aprobacion=False,
            )

        if solicitud.accion == "calcular_evento":
            evento = self.core.eventos.obtener(p["evento_id"]).to_dict()
            datos = self.core.escandallos_inteligente.calcular_necesidades_evento(evento)
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=[] if not datos.get("recetas_sin_escandallo") else ["Crear escandallos faltantes."],
                requiere_aprobacion=bool(datos.get("recetas_sin_escandallo")),
            )

        return ResultadoPipeline(
            ok=False,
            pipeline=self.nombre,
            accion=solicitud.accion,
            mensaje="Acción no implementada.",
            errores=[f"Acción no implementada: {solicitud.accion}"],
        )
