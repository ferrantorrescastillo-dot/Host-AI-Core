from MODELOS.api_interna import ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineEvento(BasePipeline):
    nombre = "evento"
    descripcion = "Pipeline de eventos."
    acciones_soportadas = [
        "crear", "listar", "buscar", "editar", "eliminar", "duplicar",
        "agregar_servicio", "agregar_pase", "linea_temporal",
        "diagnosticar", "simular_produccion",
    ]

    def _ejecutar(self, solicitud):
        p = solicitud.parametros
        if solicitud.accion == "crear":
            e = self.core.eventos.crear_evento(
                p["nombre"], p["fecha"], p["pax"], p.get("tipo", "evento"),
                p.get("cliente", ""), p.get("telefono", ""), p.get("email", ""),
                p.get("ubicacion", ""), p.get("hora_inicio", ""),
                p.get("observaciones", ""), p.get("estado", "pendiente"),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, f"Evento creado: {e.nombre}.", {"evento": e.to_dict()}, ["Añadir servicios."])
        if solicitud.accion == "listar":
            eventos = [e.to_dict() for e in self.core.eventos.listar_eventos()]
            return ResultadoPipeline(True, self.nombre, solicitud.accion, f"Eventos registrados: {len(eventos)}.", {"eventos": eventos}, [])
        if solicitud.accion == "buscar":
            eventos = [e.to_dict() for e in self.core.eventos.buscar_eventos(p.get("texto", ""))]
            return ResultadoPipeline(True, self.nombre, solicitud.accion, f"Eventos encontrados: {len(eventos)}.", {"eventos": eventos}, [])
        if solicitud.accion == "editar":
            e = self.core.eventos.editar_evento(p["evento_id"], p.get("cambios", {}))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, f"Evento actualizado: {e.nombre}.", {"evento": e.to_dict()}, [])
        if solicitud.accion == "eliminar":
            e = self.core.eventos.eliminar_evento(p["evento_id"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, f"Evento eliminado: {e.nombre}.", {"evento": e.to_dict()}, [])
        if solicitud.accion == "duplicar":
            e = self.core.eventos.duplicar_evento(p["evento_id"], p.get("nombre"), p.get("fecha"))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, f"Evento duplicado: {e.nombre}.", {"evento": e.to_dict()}, ["Revisar fecha y datos del duplicado."])
        if solicitud.accion == "agregar_servicio":
            e = self.core.eventos.agregar_servicio(p["evento_id"], p["nombre"], p.get("tipo", "servicio"), p.get("hora_inicio", "20:00"), p.get("duracion_min", 240))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, "Servicio añadido.", {"evento": e.to_dict()}, ["Añadir pases."])
        if solicitud.accion == "agregar_pase":
            e = self.core.eventos.agregar_pase(p["evento_id"], p["servicio_id"], p["nombre"], p["hora_inicio"], p.get("duracion_min", 30), p.get("recetas", []), p.get("notas", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, "Pase añadido.", {"evento": e.to_dict()}, [])
        if solicitud.accion == "linea_temporal":
            d = self.core.eventos.construir_linea_temporal(p["evento_id"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [])
        if solicitud.accion == "diagnosticar":
            d = self.core.eventos.diagnosticar_evento(p["evento_id"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, d.get("avisos", []), d.get("estado_diagnostico") != "ok")
        if solicitud.accion == "simular_produccion":
            e = self.core.eventos.obtener(p["evento_id"]).to_dict()
            d = self.core.simulador_produccion_evento.simular_evento(e, p.get("hora_inicio_produccion", "08:00"), p.get("margen_seguridad_min", 60))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, d.get("avisos", []), d.get("estado_simulacion") != "ok")
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.")
