from __future__ import annotations

"""
Módulo: motor_produccion_real

Contiene `MotorProduccionReal`, el motor operativo que genera planes
de producción reales, cronogramas y herramientas de ejecución.

Este archivo fue auditado y solo se añadieron docstrings/comentarios
para mejorar la comprensión; no se cambió la lógica funcional.
"""

from typing import Dict, List, Any, Optional
from MODELOS.produccion_real import FaseProduccionReal, TareaProduccionReal, BloqueProduccionReal, PlanProduccionReal
from datetime import datetime
import copy


class MotorProduccionReal:
    """
    Motor de Producción Real v2.0.7.

    Convierte un evento y sus escandallos en un plan operativo:
    - tareas reales de cocina
    - fases
    - recursos
    - responsables básicos
    - cronograma secuencial
    - avisos iniciales de producción
    """

    ESTADOS = ("borrador", "pendiente", "planificado", "en_produccion", "pausado", "finalizado", "cancelado")

    def __init__(self, core):
        self.core = core
        self.planes: Dict[str, PlanProduccionReal] = {}
        self._cargar_desde_db()

    def _cargar_desde_db(self) -> None:
        for datos in self.core.db.cargar("planes_produccion"):
            try:
                plan = PlanProduccionReal.from_dict(datos)
                self.planes[plan.id] = plan
            except Exception:
                continue

    def _persistir(self) -> None:
        self.core.db.guardar("planes_produccion", [p.to_dict() for p in self.planes.values()])

    def obtener_plan(self, plan_id: str) -> PlanProduccionReal:
        if plan_id not in self.planes:
            raise ValueError(f"No existe plan de producción: {plan_id}")
        return self.planes[plan_id]

    def crear_plan_manual(self, nombre: str, fecha: str = "", responsable: str = "", observaciones: str = "", estado: str = "borrador") -> Dict[str, Any]:
        estado = estado.strip().lower() or "borrador"
        if estado not in self.ESTADOS:
            raise ValueError(f"Estado no válido: {estado}")
        plan = PlanProduccionReal(nombre=nombre.strip() or "Plan de producción", fecha=fecha.strip(), responsable=responsable.strip(), observaciones=observaciones.strip(), estado=estado)
        self.planes[plan.id] = plan
        self._persistir()
        return plan.to_dict()

    def buscar_planes(self, texto: str = "") -> List[Dict[str, Any]]:
        q=(texto or "").strip().lower()
        planes=self.listar_planes()
        if not q: return planes
        return [p for p in planes if q in " ".join(str(p.get(k,"")) for k in ("id","nombre","evento","fecha","responsable","estado","observaciones")).lower()]

    def editar_plan(self, plan_id: str, cambios: Dict[str, Any]) -> Dict[str, Any]:
        plan=self.obtener_plan(plan_id)
        for campo in ("nombre","fecha","responsable","observaciones","estado"):
            if campo not in cambios or cambios[campo] is None: continue
            valor=str(cambios[campo]).strip()
            if campo=="estado":
                valor=valor.lower() or plan.estado
                if valor not in self.ESTADOS: raise ValueError(f"Estado no válido: {valor}")
            setattr(plan,campo,valor)
        plan.actualizado_en=datetime.now().isoformat(timespec="seconds")
        self._persistir()
        return plan.to_dict()

    def duplicar_plan(self, plan_id: str, nombre: Optional[str] = None, fecha: Optional[str] = None) -> Dict[str, Any]:
        original=self.obtener_plan(plan_id)
        datos=copy.deepcopy(original.to_dict())
        datos["id"]=""
        datos["nombre"]=nombre or f"{original.nombre} (copia)"
        if fecha is not None: datos["fecha"]=fecha
        datos["estado"]="borrador"
        datos["creado_en"]=""; datos["actualizado_en"]=""
        for t in datos.get("tareas",[]):
            t["id"]=""
            for f in t.get("fases",[]): f["id"]=""
        for b in datos.get("cronograma",[]): b["id"]=""
        duplicado=PlanProduccionReal.from_dict(datos)
        self.planes[duplicado.id]=duplicado
        self._persistir()
        return duplicado.to_dict()

    def eliminar_plan(self, plan_id: str) -> Dict[str, Any]:
        plan=self.obtener_plan(plan_id)
        del self.planes[plan_id]
        self._persistir()
        return plan.to_dict()

    def planificar_evento(
        self,
        evento_id: str,
        hora_inicio: str = "08:00",
        equipo_cocina: int = 2,
        incluir_logistica: bool = True,
    ) -> Dict[str, Any]:
        evento = self.core.eventos.obtener(evento_id).to_dict()
        tareas = self._crear_tareas_desde_evento(evento)
        avisos = self._diagnosticar_tareas(tareas, equipo_cocina)

        if incluir_logistica:
            tareas.append(self._tarea_logistica())
            tareas.append(self._tarea_cierre())

        cronograma = self._construir_cronograma(tareas, hora_inicio)

        plan = PlanProduccionReal(
            evento_id=evento_id,
            evento=evento.get("nombre", ""),
            pax=int(evento.get("pax", 0) or 0),
            tareas=tareas,
            cronograma=cronograma,
            avisos=avisos,
            estado="revisar" if avisos else "ok",
        )
        self.planes[plan.id] = plan
        self._persistir()

        return {**plan.to_dict(), "lectura_host_ai": self._lectura(plan)}

    def listar_planes(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in sorted(self.planes.values(), key=lambda x: (x.fecha or "9999-99-99", x.nombre.lower()))]

    def diagnosticar_plan(self, plan_id: str) -> Dict[str, Any]:
        if plan_id not in self.planes:
            raise ValueError(f"No existe plan de producción real: {plan_id}")
        plan = self.planes[plan_id]
        avisos = list(plan.avisos)

        recursos = {}
        for bloque in plan.cronograma:
            if bloque.recurso:
                recursos.setdefault(bloque.recurso, 0)
                recursos[bloque.recurso] += 1

        if plan.duracion_total_min() > 720:
            avisos.append("La producción supera 12 horas de trabajo secuencial.")

        return {
            "plan_id": plan_id,
            "evento": plan.evento,
            "duracion_total_min": plan.duracion_total_min(),
            "recursos_usados": recursos,
            "avisos": avisos,
            "estado": "revisar" if avisos else "ok",
            "lectura_host_ai": "Plan de producción sin avisos críticos." if not avisos else f"Plan de producción con {len(avisos)} avisos.",
        }

    def sugerir_trabajo_por_responsable(self, plan_id: str) -> Dict[str, Any]:
        if plan_id not in self.planes:
            raise ValueError(f"No existe plan de producción real: {plan_id}")
        plan = self.planes[plan_id]
        reparto: Dict[str, List[Dict[str, Any]]] = {}
        for bloque in plan.cronograma:
            responsable = bloque.responsable or "cocina"
            reparto.setdefault(responsable, []).append(bloque.to_dict())
        return {
            "plan_id": plan_id,
            "evento": plan.evento,
            "reparto": reparto,
            "lectura_host_ai": f"Trabajo repartido entre {len(reparto)} responsables.",
        }

    def anadir_tarea_manual(self, plan_id: str, titulo: str, prioridad: int = 50, receta_id: str = "", receta: str = "", cantidad: float = 0.0, unidad: str = "", origen: str = "manual") -> Dict[str, Any]:
        plan = self.obtener_plan(plan_id)
        tarea = TareaProduccionReal(titulo=titulo.strip() or "Tarea", receta_id=receta_id.strip(), receta=receta.strip(), cantidad=float(cantidad or 0), unidad=unidad.strip(), prioridad=max(0,min(100,int(prioridad))), origen=origen)
        plan.tareas.append(tarea); plan.actualizado_en=datetime.now().isoformat(timespec="seconds"); self._persistir(); return tarea.to_dict()

    def anadir_fase_manual(self, plan_id: str, tarea_id: str, nombre: str, duracion_min: int, tipo: str = "activo", recurso: str = "mesa_trabajo", responsable: str = "cocina", dependencia: str = "", notas: str = "") -> Dict[str, Any]:
        plan=self.obtener_plan(plan_id); tarea=next((t for t in plan.tareas if t.id==tarea_id),None)
        if not tarea: raise ValueError(f"No existe tarea: {tarea_id}")
        fase=FaseProduccionReal(nombre=nombre.strip() or "Fase",duracion_min=max(1,int(duracion_min)),tipo=tipo.strip().lower() or "activo",recurso=recurso.strip() or "mesa_trabajo",responsable=responsable.strip() or "cocina",dependencia=dependencia.strip(),receta_id=tarea.receta_id,notas=notas.strip())
        tarea.fases.append(fase); plan.actualizado_en=datetime.now().isoformat(timespec="seconds"); self._persistir(); return fase.to_dict()

    def eliminar_tarea(self, plan_id: str, tarea_id: str) -> Dict[str, Any]:
        plan=self.obtener_plan(plan_id); tarea=next((t for t in plan.tareas if t.id==tarea_id),None)
        if not tarea: raise ValueError(f"No existe tarea: {tarea_id}")
        plan.tareas=[t for t in plan.tareas if t.id!=tarea_id]; self._persistir(); return tarea.to_dict()

    def planificar_inteligente(self, plan_id: str, jornada_horas: float = 7.5, cocineros: int = 3, hora_inicio: str = "08:00") -> Dict[str, Any]:
        plan=self.obtener_plan(plan_id)
        if not plan.tareas: raise ValueError("El plan no tiene tareas. Añade tareas o créalo desde un evento.")
        pasivos={"pasivo","reposo","coccion_lenta","cocción_lenta","fermentacion","fermentación","enfriado","abatido"}
        elaboraciones=[]
        for t in plan.tareas:
            activo=sum(f.duracion_min for f in t.fases if f.tipo.lower() not in pasivos)
            pasivo=sum(f.duracion_min for f in t.fases if f.tipo.lower() in pasivos)
            deps=[]; recursos=[]
            for f in t.fases:
                if f.dependencia and f.dependencia not in deps: deps.append(f.dependencia)
                if f.recurso and f.recurso not in recursos: recursos.append(f.recurso)
            prioridad='critica' if t.prioridad>=90 else ('alta' if t.prioridad>=70 else ('normal' if t.prioridad>=40 else 'baja'))
            elaboraciones.append({"id":t.id,"clave":t.id,"nombre":t.titulo,"prioridad":prioridad,"dependencias":deps,"recursos":recursos,"tiempo_activo_min":activo,"tiempo_pasivo_min":pasivo,"tiempo_total_min":activo+pasivo,"tarea_id":t.id})
        planificacion=self.core.planificador_inteligente_produccion.planificar_produccion(elaboraciones,jornada_horas,cocineros,hora_inicio)
        asignacion=self.core.asignador_recursos_produccion.asignar_recursos(elaboraciones,planificacion,cocineros,jornada_horas)
        plan.configuracion_planificacion={"jornada_horas":float(jornada_horas),"cocineros":int(cocineros),"hora_inicio":hora_inicio}
        plan.planificacion_inteligente=planificacion; plan.asignacion_recursos=asignacion; plan.estado="planificado"; plan.actualizado_en=datetime.now().isoformat(timespec="seconds"); self._persistir()
        return {"plan":plan.to_dict(),"planificacion":planificacion,"asignacion":asignacion}


    ESTADOS_EJECUCION = (
        "pendiente", "bloqueada", "lista", "en_preparacion", "en_proceso",
        "en_espera", "pausada", "finalizada", "incidencia", "cancelada",
        # Compatibilidad histórica
        "en_curso",
    )

    TRANSICIONES_VALIDAS = {
        "pendiente": {"lista", "bloqueada", "cancelada"},
        "bloqueada": {"lista", "cancelada"},
        "lista": {"en_preparacion", "en_proceso", "bloqueada", "cancelada"},
        "en_preparacion": {"en_proceso", "pausada", "bloqueada", "cancelada"},
        "en_proceso": {"en_espera", "pausada", "incidencia", "bloqueada", "finalizada", "cancelada"},
        "en_espera": {"en_proceso", "pausada", "bloqueada", "cancelada"},
        "pausada": {"en_proceso", "bloqueada", "cancelada"},
        "incidencia": {"en_proceso", "pausada", "bloqueada", "cancelada"},
        "finalizada": set(),
        "cancelada": set(),
        # Compatibilidad con estado legado
        "en_curso": {"pausada", "finalizada", "en_espera", "bloqueada", "incidencia", "cancelada"},
    }

    ESTADOS_EQUIVALENTES = {
        "en_curso": "en_proceso",
    }

    def _obtener_tarea(self, plan_id: str, tarea_id: str):
        plan = self.obtener_plan(plan_id)
        tarea = next((t for t in plan.tareas if t.id == tarea_id), None)
        if not tarea:
            raise ValueError(f"No existe tarea: {tarea_id}")
        return plan, tarea

    @classmethod
    def _normalizar_estado_ejecucion(cls, estado: str) -> str:
        return cls.ESTADOS_EQUIVALENTES.get(str(estado or "").lower(), str(estado or "").lower())

    @staticmethod
    def _ahora() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _registrar_historial_estado(self, tarea, estado_anterior: str, estado_nuevo: str, usuario: str = "", motivo: str = "") -> None:
        tarea.historial_estados.append({
            "id": f"EST-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "fecha": self._ahora(),
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado_nuevo,
            "usuario": (usuario or "cocina").strip() or "cocina",
            "motivo": (motivo or "").strip(),
        })

    def _dependencias_tarea(self, plan, tarea_id: str) -> list[str]:
        deps: list[str] = []
        planif = plan.planificacion_inteligente or {}
        for bloque in planif.get("bloques", []) or []:
            clave = str(bloque.get("clave") or "")
            if clave and clave.replace("_pasivo", "") != str(tarea_id):
                continue
            data = bloque.get("datos") or {}
            for d in data.get("dependencias", []) or []:
                dd = str(d or "").strip()
                if dd and dd not in deps:
                    deps.append(dd)
        return deps

    def _validar_inicio(self, plan, tarea, autorizar_dependencias: bool = False) -> None:
        estado = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
        if estado == "finalizada":
            raise ValueError("La tarea ya está finalizada y no puede iniciarse de nuevo.")
        if estado == "bloqueada" or str(tarea.bloqueo or "").strip():
            raise ValueError("La tarea está bloqueada y no puede iniciarse.")
        if estado not in {"pendiente", "lista", "en_preparacion", "en_espera", "pausada", "incidencia"}:
            raise ValueError("La tarea no está en un estado válido para iniciar.")
        deps = self._dependencias_tarea(plan, tarea.id)
        pendientes = []
        for dep_id in deps:
            dep = next((x for x in plan.tareas if x.id == dep_id), None)
            if dep and self._normalizar_estado_ejecucion(dep.estado_ejecucion) != "finalizada":
                pendientes.append(dep_id)
        if pendientes and not autorizar_dependencias:
            raise ValueError("La tarea tiene dependencias pendientes y no puede iniciarse todavía.")

    @staticmethod
    def _segundos_desde(iso: str) -> int:
        if not iso:
            return 0
        try:
            return max(0, int((datetime.now() - datetime.fromisoformat(iso)).total_seconds()))
        except (TypeError, ValueError):
            return 0

    def tiempo_real_tarea_segundos(self, tarea) -> int:
        total = int(tarea.segundos_acumulados or 0)
        estado = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
        if estado in {"en_proceso", "en_preparacion", "en_espera", "incidencia"} and tarea.cronometro_iniciado_en:
            total += self._segundos_desde(tarea.cronometro_iniciado_en)
        return total

    def iniciar_tarea(self, plan_id: str, tarea_id: str, usuario: str = "", autorizar_dependencias: bool = False, motivo_autorizacion: str = "") -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        estado = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
        if estado in {"en_proceso", "en_preparacion"}:
            raise ValueError("La tarea ya está en curso.")
        self._validar_inicio(plan, tarea, autorizar_dependencias=autorizar_dependencias)
        ahora = self._ahora()
        if not tarea.iniciado_en:
            tarea.iniciado_en = ahora
        estado_anterior = estado
        nuevo = "en_preparacion" if tarea.fases else "en_proceso"
        tarea.estado_ejecucion = nuevo
        tarea.cronometro_iniciado_en = ahora
        tarea.pausado_en = ""
        if tarea.fases and not tarea.fase_activa_id:
            primera = tarea.fases[0]
            primera.estado = "EN_CURSO"
            primera.hora_inicio_real = ahora
            tarea.fase_activa_id = primera.id
        self._registrar_historial_estado(
            tarea,
            estado_anterior,
            nuevo,
            usuario=usuario,
            motivo=(motivo_autorizacion if autorizar_dependencias else "Inicio de tarea"),
        )
        plan.estado = "en_produccion"
        plan.actualizado_en = ahora
        self._persistir()
        return self.estado_tarea(plan_id, tarea_id)

    def pausar_tarea(self, plan_id: str, tarea_id: str, motivo: str = "", usuario: str = "") -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        estado = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
        if estado not in {"en_proceso", "en_preparacion", "en_espera", "en_curso", "incidencia"}:
            raise ValueError("Solo se puede pausar una tarea en curso.")
        ahora = self._ahora()
        tarea.segundos_acumulados = self.tiempo_real_tarea_segundos(tarea)
        tarea.cronometro_iniciado_en = ""
        tarea.estado_ejecucion = "pausada"
        tarea.pausado_en = ahora
        if motivo.strip():
            tarea.observaciones_ejecucion = (tarea.observaciones_ejecucion + " | " + motivo.strip()).strip(" |")
        self._registrar_historial_estado(tarea, estado, "pausada", usuario=usuario, motivo=motivo or "Pausa operativa")
        plan.estado = "pausado" if not any(self._normalizar_estado_ejecucion(t.estado_ejecucion) in {"en_proceso", "en_preparacion", "en_espera", "incidencia"} for t in plan.tareas) else "en_produccion"
        plan.actualizado_en = ahora
        self._persistir()
        return self.estado_tarea(plan_id, tarea_id)

    def reanudar_tarea(self, plan_id: str, tarea_id: str, usuario: str = "") -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        estado = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
        if estado != "pausada":
            raise ValueError("Solo se puede reanudar una tarea pausada.")
        ahora = self._ahora()
        tarea.estado_ejecucion = "en_espera" if self._fase_activa_pasiva(tarea) else "en_proceso"
        tarea.cronometro_iniciado_en = ahora
        tarea.pausado_en = ""
        self._registrar_historial_estado(tarea, estado, self._normalizar_estado_ejecucion(tarea.estado_ejecucion), usuario=usuario, motivo="Reanudación")
        plan.estado = "en_produccion"
        plan.actualizado_en = ahora
        self._persistir()
        return self.estado_tarea(plan_id, tarea_id)

    def finalizar_tarea(self, plan_id: str, tarea_id: str) -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        estado = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
        if estado == "finalizada":
            raise ValueError("La tarea ya está finalizada.")
        if estado == "bloqueada":
            raise ValueError("La tarea está bloqueada y no puede finalizarse.")
        ahora = self._ahora()
        if estado in {"en_proceso", "en_preparacion", "en_espera", "en_curso", "incidencia"}:
            tarea.segundos_acumulados = self.tiempo_real_tarea_segundos(tarea)
        tarea.cronometro_iniciado_en = ""
        tarea.estado_ejecucion = "finalizada"
        tarea.progreso_manual = 100.0
        tarea.finalizado_en = ahora
        tarea.pausado_en = ""
        if tarea.fase_activa_id:
            fase = next((f for f in tarea.fases if f.id == tarea.fase_activa_id), None)
            if fase:
                fase.estado = "FINALIZADA"
                if not fase.hora_inicio_real:
                    fase.hora_inicio_real = tarea.iniciado_en or ahora
                fase.hora_fin_real = ahora
        tarea.fase_activa_id = ""
        self._registrar_historial_estado(tarea, estado, "finalizada", motivo="Finalización")
        if plan.tareas and all(self._normalizar_estado_ejecucion(t.estado_ejecucion) == "finalizada" for t in plan.tareas):
            plan.estado = "finalizado"
        elif any(self._normalizar_estado_ejecucion(t.estado_ejecucion) in {"en_proceso", "en_preparacion", "en_espera", "incidencia"} for t in plan.tareas):
            plan.estado = "en_produccion"
        else:
            plan.estado = "pausado"
        plan.actualizado_en = ahora
        self._persistir()
        return self.estado_tarea(plan_id, tarea_id)

    def estado_tarea(self, plan_id: str, tarea_id: str) -> Dict[str, Any]:
        _plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        d = tarea.to_dict()
        d["estado_ejecucion"] = self._normalizar_estado_ejecucion(d.get("estado_ejecucion", "pendiente"))
        d["tiempo_real_segundos"] = self.tiempo_real_tarea_segundos(tarea)
        d["tiempo_real_min"] = round(d["tiempo_real_segundos"] / 60, 2)
        previsto = max(0, tarea.duracion_total_min())
        progreso_tiempo = min(99.0, (d["tiempo_real_min"] / previsto) * 100) if previsto and tarea.estado_ejecucion != "finalizada" else 0.0
        estado_tarea = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
        if estado_tarea == "finalizada":
            d["porcentaje_avance"] = 100.0
        else:
            d["porcentaje_avance"] = round(max(float(tarea.progreso_manual or 0), progreso_tiempo), 1)
        d["tiempo_previsto_min"] = previsto
        d["tiempo_restante_estimado_min"] = max(0.0, round(previsto - d["tiempo_real_min"], 1)) if previsto else 0.0
        d["checklist_total"] = len(tarea.checklist)
        d["checklist_completado"] = sum(1 for x in tarea.checklist if x.get("completado"))
        d["checklist_pendiente"] = d["checklist_total"] - d["checklist_completado"]
        d["fase_activa_id"] = tarea.fase_activa_id
        d["fases"] = [f.to_dict() for f in tarea.fases]
        d["historial_estados"] = list(tarea.historial_estados)
        d["mermas"] = list(tarea.mermas)
        return d

    def resumen_ejecucion(self, plan_id: str) -> Dict[str, Any]:
        plan = self.obtener_plan(plan_id)
        estados = {e: 0 for e in self.ESTADOS_EJECUCION}
        tareas = []
        for tarea in plan.tareas:
            estado = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
            estados[estado] = estados.get(estado, 0) + 1
            tareas.append(self.estado_tarea(plan_id, tarea.id))
        estados["en_curso"] = estados.get("en_proceso", 0) + estados.get("en_preparacion", 0) + estados.get("en_espera", 0)
        total = len(plan.tareas)
        finalizadas = estados.get("finalizada", 0)
        return {
            "plan_id": plan.id,
            "plan": plan.nombre,
            "estado_plan": plan.estado,
            "total_tareas": total,
            "estados": estados,
            "porcentaje_completado": round(sum(float(t.get("porcentaje_avance", 0)) for t in tareas) / total, 1) if total else 0.0,
            "tareas": tareas,
            "alertas": self.alertas_ejecucion(plan_id),
            "tareas_pendientes": [t for t in tareas if t.get("estado_ejecucion") != "finalizada"],
        }

    def actualizar_progreso_tarea(self, plan_id: str, tarea_id: str, porcentaje: float) -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        porcentaje = max(0.0, min(100.0, float(porcentaje)))
        tarea.progreso_manual = porcentaje
        if porcentaje >= 100 and tarea.estado_ejecucion != "finalizada":
            tarea.progreso_manual = 99.0
        plan.actualizado_en = self._ahora()
        self._persistir()
        return self.estado_tarea(plan_id, tarea_id)

    def registrar_incidencia_tarea(self, plan_id: str, tarea_id: str, tipo: str, descripcion: str, minutos_retraso: int = 0, gravedad: str = "media", efecto_operativo: str = "no_bloquea", accion_tomada: str = "", usuario: str = "") -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        tipo = (tipo or "incidencia").strip().lower()
        descripcion = (descripcion or "").strip()
        if not descripcion:
            raise ValueError("La incidencia necesita una descripción.")
        estado_actual = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
        incidencia = {
            "id": f"INC-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "tipo": tipo,
            "gravedad": str(gravedad or "media").lower(),
            "descripcion": descripcion,
            "minutos_retraso": max(0, int(minutos_retraso or 0)),
            "efecto_operativo": str(efecto_operativo or "no_bloquea").lower(),
            "accion_tomada": str(accion_tomada or "").strip(),
            "usuario": (usuario or "cocina").strip() or "cocina",
            "estado": "abierta",
            "creado_en": self._ahora(),
        }
        tarea.incidencias.append(incidencia)
        tarea.retraso_min += incidencia["minutos_retraso"]
        if tipo in {"bloqueo", "bloqueada", "bloqueado"}:
            tarea.bloqueo = descripcion
            tarea.estado_ejecucion = "bloqueada"
            tarea.cronometro_iniciado_en = ""
            self._registrar_historial_estado(tarea, estado_actual, "bloqueada", usuario=usuario, motivo=descripcion)
        elif incidencia["efecto_operativo"] == "pausa":
            tarea.estado_ejecucion = "pausada"
            tarea.cronometro_iniciado_en = ""
            self._registrar_historial_estado(tarea, estado_actual, "pausada", usuario=usuario, motivo=descripcion)
        elif incidencia["efecto_operativo"] == "cancelar":
            tarea.estado_ejecucion = "cancelada"
            tarea.cronometro_iniciado_en = ""
            self._registrar_historial_estado(tarea, estado_actual, "cancelada", usuario=usuario, motivo=descripcion)
        elif estado_actual in {"en_proceso", "en_preparacion", "en_espera"}:
            tarea.estado_ejecucion = "incidencia"
            self._registrar_historial_estado(tarea, estado_actual, "incidencia", usuario=usuario, motivo=descripcion)
        plan.actualizado_en = self._ahora()
        self._persistir()
        return incidencia

    def registrar_merma_tarea(self, plan_id: str, tarea_id: str, cantidad: float, unidad: str, motivo: str = "", merma_prevista: float | None = None, usuario: str = "") -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        cantidad = float(cantidad or 0)
        if cantidad <= 0:
            raise ValueError("La merma debe ser mayor que cero.")
        unidad = (unidad or tarea.unidad or "u").strip()
        if not unidad:
            raise ValueError("La merma requiere unidad.")
        prevista = None if merma_prevista is None else float(merma_prevista)
        registro = {
            "id": f"MER-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "cantidad": round(cantidad, 6),
            "unidad": unidad,
            "motivo": (motivo or "Merma operativa").strip(),
            "merma_prevista": None if prevista is None else round(prevista, 6),
            "merma_real": round(cantidad, 6),
            "diferencia": None if prevista is None else round(cantidad - prevista, 6),
            "usuario": (usuario or "cocina").strip() or "cocina",
            "creado_en": self._ahora(),
        }
        tarea.mermas.append(registro)
        plan.actualizado_en = self._ahora()
        self._persistir()
        return registro

    def cambiar_fase_tarea(self, plan_id: str, tarea_id: str, fase_id: str = "", usuario: str = "", observaciones: str = "") -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        if self._normalizar_estado_ejecucion(tarea.estado_ejecucion) in {"finalizada", "cancelada", "bloqueada"}:
            raise ValueError("La tarea no permite cambio de fase en su estado actual.")
        if not tarea.fases:
            raise ValueError("La tarea no tiene fases definidas.")
        ahora = self._ahora()

        actual = next((f for f in tarea.fases if f.id == tarea.fase_activa_id), None)
        if actual:
            actual.estado = "FINALIZADA"
            if not actual.hora_inicio_real:
                actual.hora_inicio_real = tarea.iniciado_en or ahora
            actual.hora_fin_real = ahora

        siguiente = None
        if fase_id:
            siguiente = next((f for f in tarea.fases if f.id == fase_id), None)
            if not siguiente:
                raise ValueError("La fase indicada no existe en la tarea.")
        else:
            for f in tarea.fases:
                if f.estado.upper() not in {"FINALIZADA"} and f.id != (actual.id if actual else ""):
                    siguiente = f
                    break

        if not siguiente:
            # Sin fase siguiente: no falla, pero deja rastro claro.
            tarea.fase_activa_id = ""
            if observaciones.strip():
                tarea.observaciones_ejecucion = (tarea.observaciones_ejecucion + " | " + observaciones.strip()).strip(" |")
            plan.actualizado_en = ahora
            self._persistir()
            return self.estado_tarea(plan_id, tarea_id)

        siguiente.hora_inicio_real = ahora
        es_pasiva = int(siguiente.duracion_pasiva_min or 0) > 0 or str(siguiente.tipo or "").lower() in {
            "reposo", "fermentacion", "fermentación", "enfriado", "abatido", "abatimiento", "descongelacion", "descongelación", "marinado", "espera"
        }
        siguiente.estado = "EN_ESPERA" if es_pasiva else "EN_CURSO"
        tarea.fase_activa_id = siguiente.id
        estado_anterior = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
        tarea.estado_ejecucion = "en_espera" if es_pasiva else "en_proceso"
        if observaciones.strip():
            tarea.observaciones_ejecucion = (tarea.observaciones_ejecucion + " | " + observaciones.strip()).strip(" |")
        self._registrar_historial_estado(tarea, estado_anterior, self._normalizar_estado_ejecucion(tarea.estado_ejecucion), usuario=usuario, motivo=f"Cambio de fase a {siguiente.nombre}")
        plan.actualizado_en = ahora
        self._persistir()
        return self.estado_tarea(plan_id, tarea_id)

    def siguiente_tarea_recomendada(self, plan_id: str) -> Dict[str, Any]:
        panel = self.panel_produccion(plan_id)
        tareas = list(panel.get("tareas_pendientes", []))
        if not tareas:
            return {"codigo": "SIN_TAREAS", "texto": "No hay tareas pendientes.", "motivo": "El plan está completado."}

        def orden(t):
            estado = self._normalizar_estado_ejecucion(t.get("estado_ejecucion", "pendiente"))
            bloqueada = 1 if str(t.get("bloqueo") or "").strip() else 0
            servicio_en = t.get("servicio_en_min")
            if not isinstance(servicio_en, (int, float)):
                servicio_en = 999999
            pasiva = sum(int(f.get("duracion_pasiva_min", 0) or 0) for f in (t.get("fases") or []))
            deps = sum(1 for f in (t.get("fases") or []) if str(f.get("dependencia") or "").strip())
            estado_rank = {"en_proceso": 0, "en_preparacion": 1, "en_espera": 2, "pausada": 3, "lista": 4, "pendiente": 5}.get(estado, 6)
            return (bloqueada, estado_rank, -int(t.get("prioridad", 50) or 50), int(servicio_en), -pasiva, -deps, str(t.get("titulo") or ""))

        candidata = sorted(tareas, key=orden)[0]
        pasiva = sum(int(f.get("duracion_pasiva_min", 0) or 0) for f in (candidata.get("fases") or []))
        deps = sum(1 for f in (candidata.get("fases") or []) if str(f.get("dependencia") or "").strip())
        return {
            "codigo": "SUGERIDA",
            "tarea_id": candidata.get("id"),
            "texto": f"Empieza ahora: {candidata.get('titulo')}",
            "motivo": f"Prioridad {int(candidata.get('prioridad',50))}, dependencias {deps}, tiempo pasivo {pasiva} min.",
            "tarea": candidata,
        }

    def liberar_tareas_dependientes(self, plan_id: str, tarea_finalizada_id: str) -> Dict[str, Any]:
        plan = self.obtener_plan(plan_id)
        liberadas = []
        for tarea in plan.tareas:
            estado = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
            if estado not in {"pendiente", "bloqueada"}:
                continue
            deps = self._dependencias_tarea(plan, tarea.id)
            if not deps:
                if estado == "pendiente":
                    tarea.estado_ejecucion = "lista"
                    liberadas.append(tarea.id)
                continue
            if tarea_finalizada_id not in deps:
                continue
            pendientes = []
            for dep_id in deps:
                dep = next((x for x in plan.tareas if x.id == dep_id), None)
                if dep and self._normalizar_estado_ejecucion(dep.estado_ejecucion) != "finalizada":
                    pendientes.append(dep_id)
            if not pendientes:
                tarea.estado_ejecucion = "lista"
                tarea.bloqueo = ""
                liberadas.append(tarea.id)
        if liberadas:
            plan.actualizado_en = self._ahora()
            self._persistir()
        return {"ok": True, "liberadas": liberadas, "total": len(liberadas)}

    @staticmethod
    def _fase_activa_pasiva(tarea) -> bool:
        if not tarea.fase_activa_id:
            return False
        fase = next((f for f in tarea.fases if f.id == tarea.fase_activa_id), None)
        if not fase:
            return False
        if int(fase.duracion_pasiva_min or 0) > 0:
            return True
        return str(fase.tipo or "").lower() in {"reposo", "fermentacion", "fermentación", "enfriado", "abatido", "abatimiento", "descongelacion", "descongelación", "marinado", "espera"}

    def resolver_bloqueo_tarea(self, plan_id: str, tarea_id: str, observacion: str = "") -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        estado_anterior = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
        anterior = tarea.bloqueo
        tarea.bloqueo = ""
        if estado_anterior == "bloqueada":
            tarea.estado_ejecucion = "lista"
            self._registrar_historial_estado(tarea, estado_anterior, "lista", motivo="Bloqueo resuelto")
        if observacion.strip():
            tarea.observaciones_ejecucion = observacion.strip()
        plan.actualizado_en = self._ahora()
        self._persistir()
        return {"ok": True, "bloqueo_anterior": anterior, "tarea": self.estado_tarea(plan_id, tarea_id)}

    def actualizar_observaciones_ejecucion(self, plan_id: str, tarea_id: str, observaciones: str) -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        tarea.observaciones_ejecucion = (observaciones or "").strip()
        plan.actualizado_en = self._ahora()
        self._persistir()
        return self.estado_tarea(plan_id, tarea_id)

    def anadir_item_checklist(self, plan_id: str, tarea_id: str, texto: str) -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        texto = (texto or "").strip()
        if not texto:
            raise ValueError("El paso del checklist no puede estar vacío.")
        item = {
            "id": f"CHK-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "texto": texto,
            "completado": False,
            "completado_en": "",
        }
        tarea.checklist.append(item)
        plan.actualizado_en = self._ahora()
        self._persistir()
        return item

    def marcar_item_checklist(self, plan_id: str, tarea_id: str, item_id: str, completado: bool = True) -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        item = next((x for x in tarea.checklist if x.get("id") == item_id), None)
        if not item:
            raise ValueError(f"No existe paso de checklist: {item_id}")
        item["completado"] = bool(completado)
        item["completado_en"] = self._ahora() if completado else ""
        plan.actualizado_en = self._ahora()
        self._persistir()
        return dict(item)

    def eliminar_item_checklist(self, plan_id: str, tarea_id: str, item_id: str) -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        item = next((x for x in tarea.checklist if x.get("id") == item_id), None)
        if not item:
            raise ValueError(f"No existe paso de checklist: {item_id}")
        tarea.checklist = [x for x in tarea.checklist if x.get("id") != item_id]
        plan.actualizado_en = self._ahora()
        self._persistir()
        return dict(item)

    def replanificar_tarea_manual(self, plan_id: str, tarea_id: str, prioridad: Optional[int] = None, responsable: Optional[str] = None, notas: Optional[str] = None) -> Dict[str, Any]:
        plan, tarea = self._obtener_tarea(plan_id, tarea_id)
        if prioridad is not None:
            tarea.prioridad = max(0, min(100, int(prioridad)))
        if responsable is not None:
            for fase in tarea.fases:
                fase.responsable = responsable.strip() or fase.responsable
        if notas is not None:
            tarea.observaciones_ejecucion = notas.strip()
        plan.actualizado_en = self._ahora()
        self._persistir()
        return self.estado_tarea(plan_id, tarea_id)

    def alertas_ejecucion(self, plan_id: str) -> List[Dict[str, Any]]:
        plan = self.obtener_plan(plan_id)
        alertas: List[Dict[str, Any]] = []
        for tarea in plan.tareas:
            real_min = self.tiempo_real_tarea_segundos(tarea) / 60.0
            previsto = max(0, tarea.duracion_total_min())
            if tarea.bloqueo:
                alertas.append({"tipo": "bloqueo", "tarea_id": tarea.id, "tarea": tarea.titulo, "mensaje": tarea.bloqueo})
            if tarea.retraso_min > 0:
                alertas.append({"tipo": "retraso", "tarea_id": tarea.id, "tarea": tarea.titulo, "mensaje": f"Retraso acumulado: {tarea.retraso_min} min"})
            estado = self._normalizar_estado_ejecucion(tarea.estado_ejecucion)
            if previsto and estado in {"en_proceso", "en_preparacion", "en_espera", "pausada", "incidencia"} and real_min > previsto:
                alertas.append({"tipo": "tiempo_excedido", "tarea_id": tarea.id, "tarea": tarea.titulo, "mensaje": f"Supera el tiempo previsto en {round(real_min-previsto,1)} min"})
        return alertas

    def panel_produccion(self, plan_id: str) -> Dict[str, Any]:
        """Construye una vista operativa única del turno de producción."""
        plan = self.obtener_plan(plan_id)
        resumen = self.resumen_ejecucion(plan_id)
        asignaciones = list((plan.asignacion_recursos or {}).get("asignaciones", []) or [])

        tarea_por_id = {t.get("id"): t for t in resumen.get("tareas", [])}
        cocineros: Dict[str, Dict[str, Any]] = {}

        for asignacion in asignaciones:
            nombre = str(asignacion.get("cocinero") or "Sin asignar")
            cocinero = cocineros.setdefault(nombre, {
                "cocinero": nombre,
                "tareas": [],
                "minutos_asignados": 0,
                "pendientes": 0,
                "en_curso": 0,
                "pausadas": 0,
                "finalizadas": 0,
                "bloqueadas": 0,
            })
            tarea_id = str(asignacion.get("datos", {}).get("tarea_id") or asignacion.get("clave") or "")
            tarea = tarea_por_id.get(tarea_id)
            if not tarea:
                continue
            entrada = {
                "tarea_id": tarea_id,
                "titulo": tarea.get("titulo", asignacion.get("elaboracion", "Tarea")),
                "estado": tarea.get("estado_ejecucion", "pendiente"),
                "avance": tarea.get("porcentaje_avance", 0),
                "tiempo_real_min": tarea.get("tiempo_real_min", 0),
                "tiempo_restante_min": tarea.get("tiempo_restante_estimado_min", 0),
                "inicio_planificado_min": asignacion.get("inicio_min", 0),
                "fin_planificado_min": asignacion.get("fin_min", 0),
                "recurso": asignacion.get("recurso", ""),
                "bloqueo": tarea.get("bloqueo", ""),
                "prioridad": tarea.get("prioridad", 50),
            }
            cocinero["tareas"].append(entrada)
            cocinero["minutos_asignados"] += int(asignacion.get("duracion_min", 0) or 0)
            estado = self._normalizar_estado_ejecucion(entrada["estado"])
            if estado in {"en_proceso", "en_preparacion", "en_espera", "incidencia"}: cocinero["en_curso"] += 1
            elif estado == "pausada": cocinero["pausadas"] += 1
            elif estado == "finalizada": cocinero["finalizadas"] += 1
            else: cocinero["pendientes"] += 1
            if entrada["bloqueo"]: cocinero["bloqueadas"] += 1

        # Los planes manuales pueden no tener reparto P2. No ocultamos sus tareas.
        asignadas = {x["tarea_id"] for c in cocineros.values() for x in c["tareas"]}
        sin_asignar = [t for t in resumen.get("tareas", []) if t.get("id") not in asignadas]
        if sin_asignar:
            bloque = cocineros.setdefault("Sin asignar", {
                "cocinero": "Sin asignar", "tareas": [], "minutos_asignados": 0,
                "pendientes": 0, "en_curso": 0, "pausadas": 0,
                "finalizadas": 0, "bloqueadas": 0,
            })
            for tarea in sin_asignar:
                entrada = {
                    "tarea_id": tarea.get("id"), "titulo": tarea.get("titulo"),
                    "estado": tarea.get("estado_ejecucion", "pendiente"),
                    "avance": tarea.get("porcentaje_avance", 0),
                    "tiempo_real_min": tarea.get("tiempo_real_min", 0),
                    "tiempo_restante_min": tarea.get("tiempo_restante_estimado_min", 0),
                    "inicio_planificado_min": None, "fin_planificado_min": None,
                    "recurso": "", "bloqueo": tarea.get("bloqueo", ""),
                    "prioridad": tarea.get("prioridad", 50),
                }
                bloque["tareas"].append(entrada)
                estado = self._normalizar_estado_ejecucion(entrada["estado"])
                if estado in {"en_proceso", "en_preparacion", "en_espera", "incidencia"}: bloque["en_curso"] += 1
                elif estado == "pausada": bloque["pausadas"] += 1
                elif estado == "finalizada": bloque["finalizadas"] += 1
                else: bloque["pendientes"] += 1
                if entrada["bloqueo"]: bloque["bloqueadas"] += 1

        total_real = round(sum(float(t.get("tiempo_real_min", 0) or 0) for t in resumen.get("tareas", [])), 2)
        total_previsto = sum(int(t.get("tiempo_previsto_min", 0) or 0) for t in resumen.get("tareas", []))
        incidencias = sum(len(t.get("incidencias", []) or []) for t in resumen.get("tareas", []))
        bloqueadas = sum(1 for t in resumen.get("tareas", []) if t.get("bloqueo"))
        en_curso = [
            t for t in resumen.get("tareas", [])
            if self._normalizar_estado_ejecucion(t.get("estado_ejecucion")) in {"en_proceso", "en_preparacion", "en_espera", "incidencia"}
        ]
        pausadas = [t for t in resumen.get("tareas", []) if t.get("estado_ejecucion") == "pausada"]

        return {
            "plan_id": plan.id,
            "plan": plan.nombre,
            "fecha": plan.fecha,
            "estado_plan": plan.estado,
            "responsable": plan.responsable,
            "porcentaje_completado": resumen.get("porcentaje_completado", 0),
            "total_tareas": resumen.get("total_tareas", 0),
            "estados": resumen.get("estados", {}),
            "tareas_en_curso": en_curso,
            "tareas_pausadas": pausadas,
            "tareas_pendientes": resumen.get("tareas_pendientes", []),
            "alertas": resumen.get("alertas", []),
            "cocineros": sorted(cocineros.values(), key=lambda x: x["cocinero"]),
            "metricas_turno": {
                "minutos_previstos": total_previsto,
                "minutos_reales": total_real,
                "incidencias": incidencias,
                "bloqueos_activos": bloqueadas,
                "checklist_total": sum(int(t.get("checklist_total", 0) or 0) for t in resumen.get("tareas", [])),
                "checklist_completado": sum(int(t.get("checklist_completado", 0) or 0) for t in resumen.get("tareas", [])),
            },
            "actualizado_en": self._ahora(),
        }

    def estadisticas_turno(self, plan_id: str) -> Dict[str, Any]:
        """Resumen compacto reutilizable para cierre y futuras comparativas."""
        panel = self.panel_produccion(plan_id)
        estados = panel.get("estados", {})
        total = int(panel.get("total_tareas", 0) or 0)
        finalizadas = int(estados.get("finalizada", 0) or 0)
        return {
            "plan_id": panel["plan_id"],
            "plan": panel["plan"],
            "total_tareas": total,
            "finalizadas": finalizadas,
            "pendientes": max(0, total - finalizadas),
            "avance": panel.get("porcentaje_completado", 0),
            "alertas": len(panel.get("alertas", [])),
            "incidencias": panel["metricas_turno"]["incidencias"],
            "bloqueos_activos": panel["metricas_turno"]["bloqueos_activos"],
            "minutos_previstos": panel["metricas_turno"]["minutos_previstos"],
            "minutos_reales": panel["metricas_turno"]["minutos_reales"],
            "estado": "cerrado" if total and finalizadas == total else "en_curso",
        }

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------

    def _elaboraciones_desde_plan(self, plan) -> List[Dict[str, Any]]:
        pasivos={"pasivo","reposo","coccion_lenta","cocción_lenta","fermentacion","fermentación","enfriado","abatido"}
        out=[]
        for t in plan.tareas:
            activo=sum(f.duracion_min for f in t.fases if f.tipo.lower() not in pasivos)
            pasivo=sum(f.duracion_min for f in t.fases if f.tipo.lower() in pasivos)
            deps=[]; recursos=[]
            for f in t.fases:
                if f.dependencia and f.dependencia not in deps: deps.append(f.dependencia)
                if f.recurso and f.recurso not in recursos: recursos.append(f.recurso)
            prioridad='critica' if t.prioridad>=90 else ('alta' if t.prioridad>=70 else ('normal' if t.prioridad>=40 else 'baja'))
            out.append({"id":t.id,"clave":t.id,"nombre":t.titulo,"prioridad":prioridad,"prioridad_num":t.prioridad,"dependencias":deps,"recursos":recursos,"tiempo_activo_min":activo,"tiempo_pasivo_min":pasivo,"tiempo_total_min":activo+pasivo,"tarea_id":t.id})
        return out

    @staticmethod
    def _duracion_planificacion_min(planificacion: Dict[str, Any], capacidad_dia: int) -> int:
        bloques=list((planificacion or {}).get("bloques",[]) or [])
        if not bloques: return 0
        return max((max(0,int(b.get("dia",1))-1)*capacidad_dia + int(b.get("fin_min",0) or 0)) for b in bloques)

    def _crear_planificacion_optimizada(self, elaboraciones: List[Dict[str, Any]], jornada_horas: float, cocineros: int, hora_inicio: str) -> Dict[str, Any]:
        capacidad=max(1,int(float(jornada_horas)*60*max(1,int(cocineros))))
        pendientes={e["clave"]:dict(e) for e in elaboraciones}
        completadas={}; orden=[]; cursor=0; bloques=[]
        peso={"critica":0,"alta":1,"normal":2,"baja":3}
        guard=0
        while pendientes and guard<10000:
            guard+=1
            disponibles=[]
            for clave,e in pendientes.items():
                deps=[str(x) for x in e.get("dependencias",[]) if str(x)]
                if all(d in completadas or not d in pendientes for d in deps): disponibles.append(e)
            if not disponibles: disponibles=list(pendientes.values())
            e=sorted(disponibles,key=lambda x:(peso.get(x.get("prioridad","normal"),2),-int(x.get("tiempo_pasivo_min",0)),-int(x.get("tiempo_activo_min",0)),x.get("nombre","")))[0]
            clave=e["clave"]; deps=[str(x) for x in e.get("dependencias",[]) if str(x)]
            dep_fin=max([completadas.get(d,0) for d in deps] or [0])
            inicio_abs=max(cursor,dep_fin); activo=int(e.get("tiempo_activo_min",0)); pasivo=int(e.get("tiempo_pasivo_min",0)); fin_act=inicio_abs+activo; fin_total=fin_act+pasivo
            recurso=(e.get("recursos") or ["mesa_trabajo"])[0]
            dia=inicio_abs//capacidad+1; inicio=inicio_abs%capacidad
            bloques.append({"clave":clave,"nombre":e["nombre"],"dia":dia,"inicio_min":inicio,"fin_min":inicio+activo,"duracion_min":activo,"tipo_tiempo":"activo","recurso":recurso,"prioridad":e.get("prioridad","normal"),"dependencias":deps,"datos":e,"orden_optimizado":len(orden)+1})
            if pasivo>0:
                bloques.append({"clave":clave+"_pasivo","nombre":e["nombre"],"dia":fin_act//capacidad+1,"inicio_min":fin_act%capacidad,"fin_min":fin_act%capacidad+pasivo,"duracion_min":pasivo,"tipo_tiempo":"pasivo","recurso":recurso,"prioridad":e.get("prioridad","normal"),"dependencias":deps,"datos":e,"orden_optimizado":len(orden)+1})
            cursor=fin_act; completadas[clave]=fin_total; orden.append(clave); pendientes.pop(clave,None)
        dur=max(completadas.values(),default=0)
        return {"version":"6.0.4-P4.1","total_elaboraciones":len(elaboraciones),"total_bloques":len(bloques),"dias":max([b["dia"] for b in bloques],default=0),"minutos_activos":sum(int(e.get("tiempo_activo_min",0)) for e in elaboraciones),"minutos_pasivos":sum(int(e.get("tiempo_pasivo_min",0)) for e in elaboraciones),"duracion_total_min":dur,"bloques":bloques,"orden_tareas":orden,"resumen":{"jornada_horas":float(jornada_horas),"cocineros":int(cocineros),"hora_inicio":hora_inicio,"capacidad_activa_dia_min":capacidad},"lectura_host_ai":f"Plan optimizado básico: {len(elaboraciones)} tareas y {dur} min de duración estimada."}

    def proponer_optimizacion_basica(self, plan_id: str) -> Dict[str, Any]:
        plan=self.obtener_plan(plan_id)
        if not plan.planificacion_inteligente: raise ValueError("El plan todavía no tiene una planificación inteligente. Ejecuta primero P2.")
        cfg=plan.configuracion_planificacion or {}; jornada=float(cfg.get("jornada_horas",7.5)); cocineros=int(cfg.get("cocineros",3)); hora=str(cfg.get("hora_inicio","08:00"))
        elaboraciones=self._elaboraciones_desde_plan(plan)
        optimizada=self._crear_planificacion_optimizada(elaboraciones,jornada,cocineros,hora)
        capacidad=max(1,int(jornada*60*max(1,cocineros)))
        original_min=self._duracion_planificacion_min(plan.planificacion_inteligente,capacidad)
        optimizado_min=int(optimizada.get("duracion_total_min",0))
        if original_min and optimizado_min>original_min:
            optimizada=copy.deepcopy(plan.planificacion_inteligente); optimizado_min=original_min
        ahorro=max(0,original_min-optimizado_min)
        orden_original=[]
        for b in plan.planificacion_inteligente.get("bloques",[]):
            k=str(b.get("clave","")).replace("_pasivo","")
            if k and k not in orden_original: orden_original.append(k)
        orden_nuevo=list(optimizada.get("orden_tareas",[])) or [str(b.get("clave","")).replace("_pasivo","") for b in optimizada.get("bloques",[]) if b.get("tipo_tiempo")=="activo"]
        cambios=[]
        for i,k in enumerate(orden_nuevo):
            if i>=len(orden_original) or orden_original[i]!=k:
                t=next((x for x in plan.tareas if x.id==k),None)
                cambios.append({"tarea_id":k,"tarea":t.titulo if t else k,"motivo":"adelantada para aprovechar tiempos pasivos y reducir espera"})
        propuesta={"id":f"OPT-{datetime.now().strftime('%Y%m%d%H%M%S%f')}","creado_en":self._ahora(),"estado":"propuesta","duracion_original_min":original_min,"duracion_optimizada_min":optimizado_min,"ahorro_min":ahorro,"orden_original":orden_original,"orden_optimizado":orden_nuevo,"cambios":cambios,"planificacion_original":copy.deepcopy(plan.planificacion_inteligente),"asignacion_original":copy.deepcopy(plan.asignacion_recursos),"planificacion_optimizada":optimizada}
        plan.propuesta_optimizacion=propuesta; plan.actualizado_en=self._ahora(); self._persistir(); return copy.deepcopy(propuesta)

    def aplicar_optimizacion_basica(self, plan_id: str) -> Dict[str, Any]:
        plan=self.obtener_plan(plan_id); p=dict(plan.propuesta_optimizacion or {})
        if not p or p.get("estado")!="propuesta": raise ValueError("No hay una propuesta de optimización pendiente.")
        plan.planificacion_inteligente=copy.deepcopy(p["planificacion_optimizada"])
        cfg=plan.configuracion_planificacion or {}; elaboraciones=self._elaboraciones_desde_plan(plan)
        plan.asignacion_recursos=self.core.asignador_recursos_produccion.asignar_recursos(elaboraciones,plan.planificacion_inteligente,int(cfg.get("cocineros",3)),float(cfg.get("jornada_horas",7.5)))
        p["estado"]="aplicada"; p["aplicada_en"]=self._ahora(); plan.historial_optimizacion.append(copy.deepcopy(p)); plan.propuesta_optimizacion={}; plan.actualizado_en=self._ahora(); self._persistir(); return copy.deepcopy(p)

    def deshacer_ultima_optimizacion(self, plan_id: str) -> Dict[str, Any]:
        plan=self.obtener_plan(plan_id)
        aplicada=next((x for x in reversed(plan.historial_optimizacion) if x.get("estado")=="aplicada" and not x.get("deshecha_en")),None)
        if not aplicada: raise ValueError("No hay una optimización aplicada que pueda deshacerse.")
        plan.planificacion_inteligente=copy.deepcopy(aplicada.get("planificacion_original",{})); plan.asignacion_recursos=copy.deepcopy(aplicada.get("asignacion_original",{})); aplicada["deshecha_en"]=self._ahora(); aplicada["estado"]="deshecha"; plan.actualizado_en=self._ahora(); self._persistir(); return copy.deepcopy(aplicada)

    @staticmethod
    def _solapa_intervalos(a1: int, a2: int, b1: int, b2: int) -> bool:
        return max(a1, b1) < min(a2, b2)

    def _analizar_ocupacion_recursos(self, planificacion: Dict[str, Any], capacidades: Dict[str, int] | None = None) -> Dict[str, Any]:
        capacidades={str(k):max(1,int(v)) for k,v in (capacidades or {}).items()}
        bloques=[copy.deepcopy(b) for b in (planificacion or {}).get("bloques",[]) if b.get("tipo_tiempo")=="activo"]
        por_recurso={}; conflictos=[]; saturacion=[]; huecos=[]
        for b in bloques:
            recurso=str(b.get("recurso") or "mesa_trabajo")
            por_recurso.setdefault(recurso,[]).append(b)
            capacidades.setdefault(recurso,1)
        for recurso,items in por_recurso.items():
            items=sorted(items,key=lambda x:(int(x.get("dia",1)),int(x.get("inicio_min",0))))
            cap=capacidades[recurso]
            dias=sorted({int(x.get("dia",1)) for x in items})
            for dia in dias:
                di=[x for x in items if int(x.get("dia",1))==dia]
                puntos=sorted({int(x.get("inicio_min",0)) for x in di}|{int(x.get("fin_min",0)) for x in di})
                max_demanda=0
                for a,b in zip(puntos,puntos[1:]):
                    activos=[x for x in di if self._solapa_intervalos(a,b,int(x.get("inicio_min",0)),int(x.get("fin_min",0)))]
                    max_demanda=max(max_demanda,len(activos))
                    if len(activos)>cap:
                        conflictos.append({"recurso":recurso,"dia":dia,"inicio_min":a,"fin_min":b,"capacidad":cap,"demanda":len(activos),"tareas":[x.get("nombre") for x in activos]})
                saturacion.append({"recurso":recurso,"dia":dia,"capacidad":cap,"demanda_maxima":max_demanda,"estado":"saturado" if max_demanda>cap else ("alto" if max_demanda==cap else "disponible")})
                for prev,nxt in zip(di,di[1:]):
                    gap=int(nxt.get("inicio_min",0))-int(prev.get("fin_min",0))
                    if gap>=30: huecos.append({"recurso":recurso,"dia":dia,"inicio_min":int(prev.get("fin_min",0)),"fin_min":int(nxt.get("inicio_min",0)),"duracion_min":gap})
        return {"capacidades":capacidades,"conflictos":conflictos,"saturacion":saturacion,"huecos":huecos,"recursos":sorted(por_recurso)}

    def _optimizar_plan_por_recursos(self, planificacion: Dict[str, Any], capacidades: Dict[str, int]) -> Dict[str, Any]:
        resultado=copy.deepcopy(planificacion)
        bloques=list(resultado.get("bloques",[]) or [])
        activos=[b for b in bloques if b.get("tipo_tiempo")=="activo"]
        pasivos=[b for b in bloques if b.get("tipo_tiempo")!="activo"]
        ocupacion={}
        movimientos=[]
        for b in sorted(activos,key=lambda x:(int(x.get("dia",1)),int(x.get("inicio_min",0)),-int((x.get("datos") or {}).get("prioridad_num",50)))):
            recurso=str(b.get("recurso") or "mesa_trabajo"); cap=max(1,int(capacidades.get(recurso,1)))
            dia=max(1,int(b.get("dia",1))); dur=max(1,int(b.get("duracion_min",0))); inicio=max(0,int(b.get("inicio_min",0)))
            original=(dia,inicio,int(b.get("fin_min",inicio+dur)))
            while True:
                slots=ocupacion.setdefault((dia,recurso),[])
                sol=[x for x in slots if self._solapa_intervalos(inicio,inicio+dur,x[0],x[1])]
                if len(sol)<cap: break
                inicio=max(x[1] for x in sol)
                if inicio+dur>24*60:
                    dia+=1; inicio=0
            b["dia"]=dia; b["inicio_min"]=inicio; b["fin_min"]=inicio+dur
            ocupacion.setdefault((dia,recurso),[]).append((inicio,inicio+dur,b.get("clave")))
            if original!=(dia,inicio,inicio+dur):
                movimientos.append({"tarea":b.get("nombre"),"clave":b.get("clave"),"recurso":recurso,"dia_original":original[0],"inicio_original_min":original[1],"dia_nuevo":dia,"inicio_nuevo_min":inicio,"motivo":f"desplazada para evitar saturación de {recurso}"})
        # Los pasivos siguen inmediatamente al bloque activo de su tarea cuando existe.
        activos_por_clave={str(b.get("clave")):b for b in activos}
        for p in pasivos:
            base=str(p.get("clave","")).replace("_pasivo","")
            a=activos_por_clave.get(base)
            if a:
                dur=max(1,int(p.get("duracion_min",0)))
                p["dia"]=a["dia"]; p["inicio_min"]=a["fin_min"]; p["fin_min"]=a["fin_min"]+dur
        resultado["bloques"]=sorted(activos+pasivos,key=lambda x:(int(x.get("dia",1)),int(x.get("inicio_min",0)),0 if x.get("tipo_tiempo")=="activo" else 1))
        resultado["version"]="6.0.4-P4.2"
        resultado["movimientos_recursos"]=movimientos
        return resultado

    def proponer_optimizacion_recursos(self, plan_id: str, capacidades: Dict[str, int] | None = None) -> Dict[str, Any]:
        plan=self.obtener_plan(plan_id)
        if not plan.planificacion_inteligente: raise ValueError("El plan todavía no tiene planificación. Ejecuta primero P2.")
        original=copy.deepcopy(plan.planificacion_inteligente)
        analisis_original=self._analizar_ocupacion_recursos(original,capacidades)
        optimizada=self._optimizar_plan_por_recursos(original,analisis_original["capacidades"])
        analisis_optimizado=self._analizar_ocupacion_recursos(optimizada,analisis_original["capacidades"])
        cfg=plan.configuracion_planificacion or {}; elaboraciones=self._elaboraciones_desde_plan(plan)
        asignacion_opt=self.core.asignador_recursos_produccion.asignar_recursos(elaboraciones,optimizada,int(cfg.get("cocineros",3)),float(cfg.get("jornada_horas",7.5)))
        propuesta={"id":f"OPTREC-{datetime.now().strftime('%Y%m%d%H%M%S%f')}","creado_en":self._ahora(),"estado":"propuesta","capacidades":analisis_original["capacidades"],"conflictos_originales":analisis_original["conflictos"],"conflictos_optimizados":analisis_optimizado["conflictos"],"saturacion_original":analisis_original["saturacion"],"saturacion_optimizada":analisis_optimizado["saturacion"],"huecos_originales":analisis_original["huecos"],"huecos_optimizados":analisis_optimizado["huecos"],"movimientos":optimizada.get("movimientos_recursos",[]),"planificacion_original":original,"asignacion_original":copy.deepcopy(plan.asignacion_recursos),"planificacion_optimizada":optimizada,"asignacion_optimizada":asignacion_opt}
        plan.propuesta_optimizacion_recursos=propuesta; plan.actualizado_en=self._ahora(); self._persistir(); return copy.deepcopy(propuesta)

    def aplicar_optimizacion_recursos(self, plan_id: str) -> Dict[str, Any]:
        plan=self.obtener_plan(plan_id); p=copy.deepcopy(plan.propuesta_optimizacion_recursos or {})
        if not p or p.get("estado")!="propuesta": raise ValueError("No hay una propuesta de recursos pendiente.")
        plan.planificacion_inteligente=copy.deepcopy(p["planificacion_optimizada"]); plan.asignacion_recursos=copy.deepcopy(p["asignacion_optimizada"])
        p["estado"]="aplicada"; p["aplicada_en"]=self._ahora(); plan.historial_optimizacion_recursos.append(copy.deepcopy(p)); plan.propuesta_optimizacion_recursos={}; plan.actualizado_en=self._ahora(); self._persistir(); return p

    def deshacer_ultima_optimizacion_recursos(self, plan_id: str) -> Dict[str, Any]:
        plan=self.obtener_plan(plan_id)
        p=next((x for x in reversed(plan.historial_optimizacion_recursos) if x.get("estado")=="aplicada" and not x.get("deshecha_en")),None)
        if not p: raise ValueError("No hay una optimización de recursos aplicada que pueda deshacerse.")
        plan.planificacion_inteligente=copy.deepcopy(p.get("planificacion_original",{})); plan.asignacion_recursos=copy.deepcopy(p.get("asignacion_original",{})); p["estado"]="deshecha"; p["deshecha_en"]=self._ahora(); plan.actualizado_en=self._ahora(); self._persistir(); return copy.deepcopy(p)

    def _crear_tareas_desde_evento(self, evento: Dict[str, Any]) -> List[TareaProduccionReal]:
        tareas: List[TareaProduccionReal] = []

        # Primero intenta usar escandallos reales.
        if hasattr(self.core, "escandallos_inteligente"):
            calculo = self.core.escandallos_inteligente.calcular_necesidades_evento(evento)
            for item in calculo.get("necesidades_agregadas", []):
                tareas.append(self._tarea_desde_necesidad(item))
            if tareas:
                return tareas

        # Fallback si no hay escandallos.
        pax = int(evento.get("pax", 0) or 0)
        factor = max(1, round(pax / 10))
        for servicio in evento.get("servicios", []):
            for pase in servicio.get("pases", []):
                for receta_id in pase.get("recetas", []):
                    nombre = receta_id.replace("REC-", "").replace("-", " ").title()
                    tareas.append(TareaProduccionReal(
                        titulo=f"Producir {nombre}",
                        receta_id=receta_id,
                        receta=nombre,
                        cantidad=factor,
                        unidad="ud",
                        fases=self._fases_genericas(nombre, receta_id, factor),
                        prioridad=80,
                        origen=f"Pase {pase.get('nombre', '')}",
                    ))
        return tareas

    def _tarea_desde_necesidad(self, item: Dict[str, Any]) -> TareaProduccionReal:
        nombre = item.get("nombre", "Producto")
        cantidad = float(item.get("cantidad_bruta", item.get("cantidad", 0)) or 0)
        unidad = item.get("unidad", "")
        receta_id = item.get("receta_id", item.get("articulo_id", ""))
        tipo = item.get("tipo", "articulo")

        fases = self._fases_por_tipo(nombre, receta_id, cantidad, unidad, tipo)

        return TareaProduccionReal(
            titulo=f"Producir / preparar {nombre}",
            receta_id=receta_id,
            receta=nombre,
            cantidad=cantidad,
            unidad=unidad,
            fases=fases,
            prioridad=90,
            origen="escandallo_evento",
        )

    # ------------------------------------------------------------------
    # P4.3 — Recomendaciones inteligentes de producción
    # ------------------------------------------------------------------
    @staticmethod
    def _nivel_recomendacion(puntuacion: int) -> str:
        if puntuacion >= 90:
            return "critica"
        if puntuacion >= 70:
            return "alta"
        if puntuacion >= 40:
            return "media"
        return "baja"

    def generar_recomendaciones_inteligentes(self, plan_id: str) -> Dict[str, Any]:
        plan = self.obtener_plan(plan_id)
        recomendaciones: List[Dict[str, Any]] = []
        panel = self.panel_produccion(plan_id)

        def agregar(tipo: str, titulo: str, explicacion: str, puntuacion: int, tarea=None, accion=None, cambios=None):
            recomendaciones.append({
                "id": f"REC-{datetime.now().strftime('%Y%m%d%H%M%S%f')}-{len(recomendaciones)+1}",
                "tipo": tipo, "titulo": titulo, "explicacion": explicacion,
                "prioridad": self._nivel_recomendacion(puntuacion), "puntuacion": puntuacion,
                "tarea_id": getattr(tarea, "id", "") if tarea else "",
                "tarea": getattr(tarea, "titulo", "") if tarea else "",
                "accion": accion or "informativa", "cambios": cambios or {},
                "aplicable": bool(accion and accion != "informativa"), "estado": "pendiente",
            })

        for tarea in plan.tareas:
            previsto = max(0, tarea.duracion_total_min())
            real = self.tiempo_real_tarea_segundos(tarea) / 60.0
            pendientes = sum(1 for item in tarea.checklist if not item.get("completado"))
            pasivo = sum(int(f.duracion_min or 0) for f in tarea.fases if str(f.tipo).lower() in {"pasivo", "reposo", "espera", "coccion_pasiva"})
            total = max(1, previsto)
            if tarea.bloqueo:
                nueva = min(100, int(tarea.prioridad) + 20)
                agregar("cuello_botella", f"Resolver bloqueo en {tarea.titulo}", f"La tarea está bloqueada: {tarea.bloqueo}. Conviene elevarla y resolverla antes de que retrase tareas dependientes.", 100, tarea, "subir_prioridad", {"prioridad_anterior": tarea.prioridad, "prioridad_nueva": nueva})
            if tarea.retraso_min >= 15:
                nueva = min(100, int(tarea.prioridad) + 10)
                agregar("retraso", f"Repriorizar {tarea.titulo}", f"Acumula {tarea.retraso_min} minutos de retraso. Subir su prioridad reduce el riesgo de arrastre.", 85, tarea, "subir_prioridad", {"prioridad_anterior": tarea.prioridad, "prioridad_nueva": nueva})
            if previsto and real > previsto and tarea.estado_ejecucion != "finalizada":
                agregar("tiempo_excedido", f"Revisar duración de {tarea.titulo}", f"El tiempo real supera el previsto en {round(real-previsto,1)} minutos. Revisa cantidad, método o dotación.", 80, tarea)
            if pendientes and float(tarea.progreso_manual or 0) >= 75:
                agregar("checklist", f"Completar checklist de {tarea.titulo}", f"La tarea está al {round(float(tarea.progreso_manual or 0),1)}% pero quedan {pendientes} pasos sin completar.", 70, tarea)
            if pasivo >= 45 and pasivo / total >= 0.35:
                agregar("tiempo_pasivo", f"Aprovechar espera de {tarea.titulo}", f"La tarea contiene {pasivo} minutos pasivos. Durante ese hueco pueden adelantarse tareas compatibles.", 55, tarea)
            if not tarea.fases:
                agregar("definicion_incompleta", f"Definir fases de {tarea.titulo}", "La tarea no tiene fases; no puede planificarse ni optimizarse con fiabilidad.", 90, tarea)

        cargas = [(c.get("cocinero"), int(c.get("minutos_asignados", 0) or 0)) for c in panel.get("cocineros", []) if c.get("cocinero") != "Sin asignar"]
        if len(cargas) >= 2:
            max_c = max(cargas, key=lambda x: x[1]); min_c = min(cargas, key=lambda x: x[1])
            if max_c[1] - min_c[1] >= 60:
                agregar("carga_equipo", "Reequilibrar carga entre cocineros", f"{max_c[0]} tiene {max_c[1]} min y {min_c[0]} {min_c[1]} min. Diferencia: {max_c[1]-min_c[1]} min.", 75)

        if plan.planificacion_inteligente:
            capacidades = dict((plan.propuesta_optimizacion_recursos or {}).get("capacidades", {}) or {})
            analisis = self._analizar_ocupacion_recursos(plan.planificacion_inteligente, capacidades or None)
            for conflicto in analisis.get("conflictos", [])[:10]:
                agregar("recurso", f"Descongestionar {conflicto.get('recurso')}", f"Día {conflicto.get('dia')}: demanda {conflicto.get('demanda')} para capacidad {conflicto.get('capacidad')}. Ejecuta P4.2 o aumenta capacidad.", 90)
            for hueco in analisis.get("huecos", [])[:5]:
                if int(hueco.get("duracion_min", 0)) >= 60:
                    agregar("recurso_infrautilizado", f"Aprovechar hueco de {hueco.get('recurso')}", f"Hay un hueco de {hueco.get('duracion_min')} min el día {hueco.get('dia')}.", 35)

        recomendaciones.sort(key=lambda x: (-int(x.get("puntuacion", 0)), x.get("titulo", "")))
        propuesta = {
            "id": f"RECOM-{datetime.now().strftime('%Y%m%d%H%M%S%f')}", "version": "6.0.4-P4.3",
            "creado_en": self._ahora(), "estado": "propuesta", "total": len(recomendaciones),
            "criticas": sum(1 for r in recomendaciones if r["prioridad"] == "critica"),
            "altas": sum(1 for r in recomendaciones if r["prioridad"] == "alta"),
            "aplicables": sum(1 for r in recomendaciones if r["aplicable"]),
            "recomendaciones": recomendaciones,
            "snapshot_tareas": {t.id: {"prioridad": t.prioridad, "observaciones_ejecucion": t.observaciones_ejecucion} for t in plan.tareas},
        }
        plan.propuesta_recomendaciones = propuesta
        plan.actualizado_en = self._ahora()
        self._persistir()
        return copy.deepcopy(propuesta)

    def aplicar_recomendaciones(self, plan_id: str, recomendacion_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        plan = self.obtener_plan(plan_id)
        propuesta = copy.deepcopy(plan.propuesta_recomendaciones or {})
        if not propuesta or propuesta.get("estado") != "propuesta":
            raise ValueError("No hay recomendaciones pendientes.")
        seleccion = set(recomendacion_ids or [])
        aplicadas = []
        for rec in propuesta.get("recomendaciones", []):
            if seleccion and rec.get("id") not in seleccion: continue
            if not rec.get("aplicable"): continue
            tarea = next((t for t in plan.tareas if t.id == rec.get("tarea_id")), None)
            if not tarea: continue
            if rec.get("accion") == "subir_prioridad":
                tarea.prioridad = int((rec.get("cambios") or {}).get("prioridad_nueva", tarea.prioridad))
                nota = f"P4.3: {rec.get('titulo')}"
                if nota not in tarea.observaciones_ejecucion:
                    tarea.observaciones_ejecucion = (tarea.observaciones_ejecucion + " | " + nota).strip(" |")
                rec["estado"] = "aplicada"; rec["aplicada_en"] = self._ahora(); aplicadas.append(copy.deepcopy(rec))
        propuesta["estado"] = "aplicada"; propuesta["aplicada_en"] = self._ahora(); propuesta["recomendaciones_aplicadas"] = aplicadas
        plan.historial_recomendaciones.append(copy.deepcopy(propuesta)); plan.propuesta_recomendaciones = {}; plan.actualizado_en = self._ahora(); self._persistir()
        return {"propuesta_id": propuesta.get("id"), "aplicadas": aplicadas, "total_aplicadas": len(aplicadas)}

    def descartar_recomendaciones(self, plan_id: str) -> Dict[str, Any]:
        plan = self.obtener_plan(plan_id); propuesta = copy.deepcopy(plan.propuesta_recomendaciones or {})
        if not propuesta: raise ValueError("No hay recomendaciones pendientes.")
        propuesta["estado"] = "descartada"; propuesta["descartada_en"] = self._ahora(); plan.historial_recomendaciones.append(propuesta); plan.propuesta_recomendaciones = {}; plan.actualizado_en = self._ahora(); self._persistir(); return propuesta

    def deshacer_ultimas_recomendaciones(self, plan_id: str) -> Dict[str, Any]:
        plan = self.obtener_plan(plan_id)
        aplicada = next((x for x in reversed(plan.historial_recomendaciones) if x.get("estado") == "aplicada" and not x.get("deshecha_en")), None)
        if not aplicada: raise ValueError("No hay recomendaciones aplicadas que puedan deshacerse.")
        snapshot = aplicada.get("snapshot_tareas", {}) or {}
        for tarea in plan.tareas:
            if tarea.id in snapshot:
                tarea.prioridad = int(snapshot[tarea.id].get("prioridad", tarea.prioridad))
                tarea.observaciones_ejecucion = str(snapshot[tarea.id].get("observaciones_ejecucion", tarea.observaciones_ejecucion))
        aplicada["estado"] = "deshecha"; aplicada["deshecha_en"] = self._ahora(); plan.actualizado_en = self._ahora(); self._persistir(); return copy.deepcopy(aplicada)

    def _fases_por_tipo(self, nombre: str, receta_id: str, cantidad: float, unidad: str, tipo: str) -> List[FaseProduccionReal]:
        nombre_l = nombre.lower()

        if tipo == "elaboracion" or "glace" in nombre_l or "salsa" in nombre_l or "fondo" in nombre_l:
            return [
                FaseProduccionReal("Preparar base", 30, "preparacion", "mesa_trabajo", "cocinero", receta_id=receta_id, notas=f"{cantidad} {unidad}"),
                FaseProduccionReal("Cocinar / reducir", 120, "coccion", "fuego", "cocinero", receta_id=receta_id),
                FaseProduccionReal("Colar y abatir", 30, "abatido", "abatidor", "cocinero", receta_id=receta_id),
                FaseProduccionReal("Envasar y etiquetar", 20, "envasado", "mesa_trabajo", "ayudante", receta_id=receta_id),
            ]

        if "carrillera" in nombre_l or "carne" in nombre_l:
            return [
                FaseProduccionReal("Limpiar y racionar", 45, "preparacion", "mesa_trabajo", "cocinero", receta_id=receta_id, notas=f"{cantidad} {unidad}"),
                FaseProduccionReal("Marcar / preparar cocción", 40, "coccion", "fuego", "cocinero", receta_id=receta_id),
                FaseProduccionReal("Cocción lenta", 180, "coccion", "horno", "cocinero", receta_id=receta_id),
                FaseProduccionReal("Abatir", 45, "abatido", "abatidor", "ayudante", receta_id=receta_id),
                FaseProduccionReal("Porcionar y envasar", 45, "envasado", "mesa_trabajo", "ayudante", receta_id=receta_id),
            ]

        return self._fases_genericas(nombre, receta_id, cantidad)

    def _fases_genericas(self, nombre: str, receta_id: str, cantidad: float) -> List[FaseProduccionReal]:
        return [
            FaseProduccionReal("Preparar mise en place", 30, "preparacion", "mesa_trabajo", "cocinero", receta_id=receta_id, notas=f"{cantidad}"),
            FaseProduccionReal("Cocinar / elaborar", 60, "produccion", "fuego", "cocinero", receta_id=receta_id),
            FaseProduccionReal("Envasar / guardar", 20, "envasado", "mesa_trabajo", "ayudante", receta_id=receta_id),
        ]

    def _tarea_logistica(self) -> TareaProduccionReal:
        return TareaProduccionReal(
            titulo="Carga, transporte y montaje",
            receta="Logística",
            fases=[
                FaseProduccionReal("Preparar cajas y etiquetado final", 30, "logistica", "mesa_trabajo", "ayudante"),
                FaseProduccionReal("Cargar vehículo", 30, "logistica", "transporte", "equipo"),
                FaseProduccionReal("Montaje cocina evento", 60, "logistica", "evento", "equipo"),
            ],
            prioridad=70,
            origen="logistica",
        )

    def _tarea_cierre(self) -> TareaProduccionReal:
        return TareaProduccionReal(
            titulo="Cierre y retorno",
            receta="Cierre",
            fases=[
                FaseProduccionReal("Recoger material", 40, "cierre", "evento", "equipo"),
                FaseProduccionReal("Limpieza y retorno", 50, "cierre", "transporte", "equipo"),
            ],
            prioridad=40,
            origen="cierre",
        )

    def _construir_cronograma(self, tareas: List[TareaProduccionReal], hora_inicio: str) -> List[BloqueProduccionReal]:
        cronograma: List[BloqueProduccionReal] = []
        cursor = hora_inicio

        tareas_ordenadas = sorted(tareas, key=lambda t: t.prioridad, reverse=True)

        for tarea in tareas_ordenadas:
            for fase in tarea.fases:
                inicio = cursor
                fin = self._sumar_minutos(inicio, fase.duracion_min)
                cronograma.append(BloqueProduccionReal(
                    inicio=inicio,
                    fin=fin,
                    titulo=f"{tarea.titulo} - {fase.nombre}",
                    tipo=fase.tipo,
                    recurso=fase.recurso,
                    responsable=fase.responsable,
                    tarea_id=tarea.id,
                    fase_id=fase.id,
                    receta_id=tarea.receta_id,
                    notas=fase.notas,
                ))
                cursor = fin

        return cronograma

    def _diagnosticar_tareas(self, tareas: List[TareaProduccionReal], equipo_cocina: int) -> List[str]:
        avisos = []
        total_min = sum(t.duracion_total_min() for t in tareas)
        if equipo_cocina <= 0:
            avisos.append("No hay equipo de cocina asignado.")
        elif total_min / equipo_cocina > 480:
            avisos.append("La carga de trabajo por cocinero supera 8 horas.")

        if not tareas:
            avisos.append("No se han generado tareas de producción.")
        return avisos

    def _sumar_minutos(self, hora: str, minutos: int) -> str:
        h, m = [int(x) for x in hora.split(":")]
        total = h * 60 + m + int(minutos)
        return f"{(total // 60) % 24:02d}:{total % 60:02d}"

    def _lectura(self, plan: PlanProduccionReal) -> str:
        if plan.avisos:
            return f"Plan de producción real para '{plan.evento}' generado con {len(plan.tareas)} tareas y {len(plan.avisos)} avisos."
        return f"Plan de producción real para '{plan.evento}' generado con {len(plan.tareas)} tareas y {len(plan.cronograma)} bloques."
