from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineEventoAPI(BasePipeline):
    nombre = "evento"
    descripcion = "Pipeline API estándar para eventos gastronómicos."
    acciones_soportadas = ["crear", "agregar_servicio", "agregar_pase", "linea_temporal", "diagnosticar", "simular_produccion", "detectar_conflictos", "replanificar", "simular_tiempo_real"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        a = solicitud.accion
        if a == "crear":
            ev = self.core.eventos.crear_evento(p["nombre"], p["fecha"], p["pax"], p.get("tipo", "evento"), p.get("cliente", ""), p.get("ubicacion", ""))
            return ResultadoPipeline(True, self.nombre, a, f"Evento creado: {ev.nombre}.", {"evento": ev.to_dict()}, ["Añadir servicios y pases al evento."])
        if a == "agregar_servicio":
            ev = self.core.eventos.agregar_servicio(p["evento_id"], p["nombre"], p.get("tipo", "servicio"), p.get("hora_inicio", "20:00"), p.get("duracion_min", 240))
            return ResultadoPipeline(True, self.nombre, a, "Servicio añadido al evento.", {"evento": ev.to_dict()}, ["Añadir pases al servicio."])
        if a == "agregar_pase":
            ev = self.core.eventos.agregar_pase(p["evento_id"], p["servicio_id"], p["nombre"], p["hora_inicio"], p.get("duracion_min", 30), p.get("recetas", []), p.get("notas", ""))
            return ResultadoPipeline(True, self.nombre, a, "Pase añadido al servicio.", {"evento": ev.to_dict()}, ["Construir línea temporal del evento."])
        if a == "linea_temporal":
            d = self.core.eventos.construir_linea_temporal(p["evento_id"])
            return ResultadoPipeline(True, self.nombre, a, d["lectura_host_ai"], d, ["Revisar línea temporal antes de simular producción."])
        if a == "diagnosticar":
            d = self.core.eventos.diagnosticar_evento(p["evento_id"])
            return ResultadoPipeline(True, self.nombre, a, d["lectura_host_ai"], d, d.get("avisos", []), d.get("estado_diagnostico") != "ok")
        if a == "simular_produccion":
            ev = self.core.eventos.obtener(p["evento_id"]).to_dict()
            d = self.core.simulador_produccion_evento.simular_evento(ev, p.get("hora_inicio_produccion", "08:00"), int(p.get("margen_seguridad_min", 60)))
            return ResultadoPipeline(True, self.nombre, a, d["lectura_host_ai"], d, d.get("avisos", []) or ["Revisar cronograma de producción simulado."], d.get("estado_simulacion") != "ok")
        if a == "detectar_conflictos":
            ev = self.core.eventos.obtener(p["evento_id"]).to_dict()
            sim = self.core.simulador_produccion_evento.simular_evento(ev, p.get("hora_inicio_produccion", "08:00"), int(p.get("margen_seguridad_min", 60)))
            d = self.core.detector_conflictos_evento.detectar_conflictos(sim, p.get("capacidades_recursos", {}))
            return ResultadoPipeline(True, self.nombre, a, d["lectura_host_ai"], {"simulacion": sim, "conflictos": d}, d.get("recomendaciones", []), d.get("estado_conflictos") != "ok")
        if a == "replanificar":
            ev = self.core.eventos.obtener(p["evento_id"]).to_dict()
            sim = self.core.simulador_produccion_evento.simular_evento(ev, p.get("hora_inicio_produccion", "08:00"), int(p.get("margen_seguridad_min", 60)))
            conf = self.core.detector_conflictos_evento.detectar_conflictos(sim, p.get("capacidades_recursos", {}))
            d = self.core.replanificador_evento.replanificar(sim, conf, p.get("capacidades_recursos", {}), int(p.get("margen_seguridad_min", 60)))
            return ResultadoPipeline(True, self.nombre, a, d["lectura_host_ai"], {"simulacion": sim, "conflictos": conf, "replanificacion": d}, d.get("recomendaciones", []) + d.get("avisos", []), d.get("estado_replanificacion") != "ok")
        if a == "simular_tiempo_real":
            ev = self.core.eventos.obtener(p["evento_id"]).to_dict()
            sim = self.core.simulador_produccion_evento.simular_evento(ev, p.get("hora_inicio_produccion", "08:00"), int(p.get("margen_seguridad_min", 60)))
            conf = self.core.detector_conflictos_evento.detectar_conflictos(sim, p.get("capacidades_recursos", {}))
            repl = None
            if p.get("usar_replanificacion", True):
                repl = self.core.replanificador_evento.replanificar(sim, conf, p.get("capacidades_recursos", {}), int(p.get("margen_seguridad_min", 60)))
            d = self.core.simulacion_tiempo_real.simular(simulacion=sim, replanificacion=repl, capacidades_recursos=p.get("capacidades_recursos", {}), resolucion_min=int(p.get("resolucion_min", 1)), ventana_proximas_min=int(p.get("ventana_proximas_min", 15)), max_estados=int(p.get("max_estados", 1500)))
            return ResultadoPipeline(True, self.nombre, a, d["lectura_host_ai"], {"simulacion_base": sim, "conflictos": conf, "replanificacion": repl, "simulacion_tiempo_real": d}, d.get("avisos", []) or ["Revisar estados minuto a minuto del servicio."], d.get("estado_global") != "ok")
        return ResultadoPipeline(False, self.nombre, a, "Acción no implementada.", errores=[f"Acción no implementada: {a}"])
