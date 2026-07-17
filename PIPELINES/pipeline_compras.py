from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineCompras(BasePipeline):
    nombre = "compras"
    descripcion = "Gestión manual de necesidades, pedidos y recepción de compras."
    acciones_soportadas = [
        "registrar_necesidad", "listar_necesidades", "buscar_necesidades",
        "editar_necesidad", "cambiar_estado_necesidad", "eliminar_necesidad",
        "generar_pedidos_sugeridos", "listar_pedidos", "editar_pedido",
        "agregar_linea_pedido", "editar_linea_pedido", "eliminar_linea_pedido",
        "cambiar_estado_pedido", "recibir_pedido", "historial_pedido", "diagnosticar",
        "generar_propuesta_inteligente", "listar_propuestas", "confirmar_propuesta",
        "cancelar_propuesta",
        "registrar_compra_manual", "listar_historial_compras",
        "listar_proveedores", "crear_proveedor_manual", "editar_proveedor", "desactivar_proveedor",
        "asociar_producto_proveedor", "preparar_onboarding_proveedor_detectado",
    ]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "registrar_necesidad":
            necesidad = self.core.compras.registrar_necesidad(
                nombre=p["nombre"], cantidad=p["cantidad"], unidad=p["unidad"],
                familia=p.get("familia", ""), proveedor_preferente=p.get("proveedor_preferente", ""),
                motivo=p.get("motivo", ""), prioridad=p.get("prioridad", 50),
                articulo_id=p.get("articulo_id", ""), fecha_necesaria=p.get("fecha_necesaria", ""),
            )
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Necesidad de compra registrada: {necesidad.nombre}.",
                datos={"necesidad": necesidad.to_dict()},
                acciones_recomendadas=["Revisar el resto de necesidades pendientes."], requiere_aprobacion=False)

        if solicitud.accion == "listar_necesidades":
            necesidades = self.core.compras.listar_necesidades(solo_pendientes=p.get("solo_pendientes", True), estado=p.get("estado", ""))
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Necesidades de compra: {len(necesidades)}.", datos={"necesidades": necesidades})

        if solicitud.accion == "buscar_necesidades":
            necesidades = self.core.compras.buscar_necesidades(p.get("texto", ""), p.get("estado", ""))
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Coincidencias encontradas: {len(necesidades)}.", datos={"necesidades": necesidades})

        if solicitud.accion == "editar_necesidad":
            necesidad = self.core.compras.editar_necesidad(p["necesidad_id"], **p.get("cambios", {}))
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Necesidad actualizada: {necesidad.nombre}.", datos={"necesidad": necesidad.to_dict()})

        if solicitud.accion == "cambiar_estado_necesidad":
            necesidad = self.core.compras.cambiar_estado(p["necesidad_id"], p["estado"])
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Necesidad marcada como {necesidad.estado}: {necesidad.nombre}.", datos={"necesidad": necesidad.to_dict()})

        if solicitud.accion == "eliminar_necesidad":
            eliminado = self.core.compras.eliminar_necesidad(p["necesidad_id"])
            return ResultadoPipeline(ok=eliminado, pipeline=self.nombre, accion=solicitud.accion,
                mensaje="Necesidad eliminada." if eliminado else "Necesidad no encontrada.",
                datos={"eliminado": eliminado}, requiere_aprobacion=True)

        if solicitud.accion == "generar_pedidos_sugeridos":
            datos = self.core.compras.generar_pedidos_sugeridos()
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"], datos=datos,
                acciones_recomendadas=["Revisar y preparar los pedidos antes de enviarlos."], requiere_aprobacion=True)

        if solicitud.accion == "listar_pedidos":
            pedidos = self.core.compras.listar_pedidos(p.get("estado", ""), p.get("texto", ""))
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Pedidos encontrados: {len(pedidos)}.", datos={"pedidos": pedidos})

        if solicitud.accion == "editar_pedido":
            pedido = self.core.compras.editar_pedido(p["pedido_id"], p.get("proveedor"), p.get("observaciones"))
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Pedido actualizado: {pedido.id}.", datos={"pedido": pedido.to_dict()})

        if solicitud.accion == "agregar_linea_pedido":
            linea = self.core.compras.agregar_linea_pedido(p["pedido_id"], p["nombre"], p["cantidad"], p["unidad"],
                p.get("articulo_id", ""), p.get("familia", ""), p.get("necesidad_id", ""),
                p.get("precio_unitario", 0), p.get("observaciones", ""))
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Línea añadida: {linea.nombre}.", datos={"linea": linea.to_dict()})

        if solicitud.accion == "editar_linea_pedido":
            linea = self.core.compras.editar_linea_pedido(p["pedido_id"], p["linea_id"], **p.get("cambios", {}))
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Línea actualizada: {linea.nombre}.", datos={"linea": linea.to_dict()})

        if solicitud.accion == "eliminar_linea_pedido":
            eliminado = self.core.compras.eliminar_linea_pedido(p["pedido_id"], p["linea_id"])
            return ResultadoPipeline(ok=eliminado, pipeline=self.nombre, accion=solicitud.accion,
                mensaje="Línea eliminada." if eliminado else "Línea no encontrada.", datos={"eliminado": eliminado}, requiere_aprobacion=True)

        if solicitud.accion == "cambiar_estado_pedido":
            pedido = self.core.compras.cambiar_estado_pedido(p["pedido_id"], p["estado"])
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Pedido marcado como {pedido.estado}: {pedido.id}.", datos={"pedido": pedido.to_dict()}, requiere_aprobacion=p["estado"] in {"enviado", "cancelado"})

        if solicitud.accion == "recibir_pedido":
            datos = self.core.compras.recibir_pedido(p["pedido_id"], self.core.stock, p.get("ubicacion", ""), p.get("caducidades", {}), p.get("costes", {}))
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"], datos=datos, requiere_aprobacion=True)

        if solicitud.accion == "historial_pedido":
            historial = self.core.compras.historial_pedido(p["pedido_id"])
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Historial del pedido: {len(historial)} movimientos.", datos={"historial": historial})

        if solicitud.accion == "diagnosticar":
            datos = self.core.compras.diagnosticar_compras()
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"], datos=datos,
                acciones_recomendadas=datos.get("avisos", []), requiere_aprobacion=datos.get("estado") != "ok")

        if solicitud.accion == "generar_propuesta_inteligente":
            datos = self.core.compras.generar_propuesta_compra_inteligente(self.core, p.get("plan_id", ""))
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos.get("lectura_host_ai", "Propuestas generadas."),
                datos=datos,
                acciones_recomendadas=["Revisar propuestas antes de confirmar compras."],
                requiere_aprobacion=True,
            )

        if solicitud.accion == "listar_propuestas":
            propuestas = self.core.compras.listar_propuestas_compra(solo_pendientes=bool(p.get("solo_pendientes", True)))
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Propuestas de compra: {len(propuestas)}.", datos={"propuestas": propuestas})

        if solicitud.accion == "confirmar_propuesta":
            compra = self.core.compras.confirmar_propuesta_compra(
                p["propuesta_id"],
                proveedor=p.get("proveedor", ""),
                observaciones=p.get("observaciones", ""),
            )
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje="Propuesta confirmada y registrada como compra.", datos={"compra": compra.to_dict()}, requiere_aprobacion=True)

        if solicitud.accion == "cancelar_propuesta":
            propuesta = self.core.compras.cancelar_propuesta_compra(p["propuesta_id"])
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje="Propuesta cancelada.", datos={"propuesta": propuesta.to_dict()}, requiere_aprobacion=True)

        if solicitud.accion == "registrar_compra_manual":
            compra = self.core.compras.registrar_compra_manual(
                producto=p["producto"],
                cantidad=p["cantidad"],
                unidad=p["unidad"],
                proveedor=p.get("proveedor", ""),
                observaciones=p.get("observaciones", ""),
                prioridad=p.get("prioridad", "Normal"),
                articulo_id=p.get("articulo_id", ""),
            )
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje="Compra manual registrada.", datos={"compra": compra.to_dict()}, requiere_aprobacion=True)

        if solicitud.accion == "listar_historial_compras":
            compras = self.core.compras.listar_historial_compras(p.get("texto", ""))
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Historial de compras: {len(compras)}.", datos={"compras": compras})

        if solicitud.accion == "listar_proveedores":
            proveedores = self.core.compras.listar_proveedores(
                incluir_inactivos=bool(p.get("incluir_inactivos", True)),
                texto=p.get("texto", ""),
            )
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=f"Proveedores encontrados: {len(proveedores)}.", datos={"proveedores": proveedores})

        if solicitud.accion == "crear_proveedor_manual":
            proveedor = self.core.compras.crear_proveedor_manual(
                nombre=p["nombre"],
                cif=p.get("cif", ""),
                telefono=p.get("telefono", ""),
                email=p.get("email", ""),
                direccion=p.get("direccion", ""),
                comercial=p.get("comercial", ""),
                observaciones=p.get("observaciones", ""),
            )
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje="Proveedor creado.", datos={"proveedor": proveedor.to_dict()}, requiere_aprobacion=True)

        if solicitud.accion == "editar_proveedor":
            proveedor = self.core.compras.editar_proveedor(p["proveedor_id"], **p.get("cambios", {}))
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje="Proveedor actualizado.", datos={"proveedor": proveedor.to_dict()}, requiere_aprobacion=True)

        if solicitud.accion == "desactivar_proveedor":
            proveedor = self.core.compras.desactivar_proveedor(p["proveedor_id"])
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje="Proveedor desactivado.", datos={"proveedor": proveedor.to_dict()}, requiere_aprobacion=True)

        if solicitud.accion == "asociar_producto_proveedor":
            proveedor = self.core.compras.asociar_producto_proveedor(p["proveedor_id"], p["producto"])
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje="Producto asociado al proveedor.", datos={"proveedor": proveedor.to_dict()}, requiere_aprobacion=True)

        if solicitud.accion == "preparar_onboarding_proveedor_detectado":
            datos = self.core.compras.preparar_onboarding_proveedor_detectado(
                p.get("nombre_detectado", ""),
                p.get("datos_detectados", {}),
            )
            return ResultadoPipeline(ok=True, pipeline=self.nombre, accion=solicitud.accion,
                mensaje=datos.get("mensaje", "Onboarding preparado."), datos=datos)

        return ResultadoPipeline(ok=False, pipeline=self.nombre, accion=solicitud.accion,
            mensaje="Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
