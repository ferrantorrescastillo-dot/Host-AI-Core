from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime
import uuid

def nuevo_id(prefijo: str) -> str:
    return f"{prefijo.upper()}-{uuid.uuid4().hex[:10].upper()}"

@dataclass
class FaseProduccionReal:
    nombre: str
    duracion_min: int
    tipo: str = "produccion"
    recurso: str = ""
    responsable: str = "cocina"
    dependencia: str = ""
    receta_id: str = ""
    notas: str = ""
    id: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("FASEPR")
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls,d):
        return cls(nombre=str(d.get("nombre","Fase")),duracion_min=int(d.get("duracion_min",0) or 0),tipo=str(d.get("tipo","produccion")),recurso=str(d.get("recurso","")),responsable=str(d.get("responsable","cocina")),dependencia=str(d.get("dependencia","")),receta_id=str(d.get("receta_id","")),notas=str(d.get("notas","")),id=str(d.get("id") or nuevo_id("FASEPR")))

@dataclass
class TareaProduccionReal:
    titulo: str
    receta_id: str = ""
    receta: str = ""
    cantidad: float = 0.0
    unidad: str = ""
    fases: List[FaseProduccionReal] = field(default_factory=list)
    prioridad: int = 50
    origen: str = ""
    estado_ejecucion: str = "pendiente"
    iniciado_en: str = ""
    pausado_en: str = ""
    finalizado_en: str = ""
    cronometro_iniciado_en: str = ""
    segundos_acumulados: int = 0
    progreso_manual: float = 0.0
    retraso_min: int = 0
    bloqueo: str = ""
    observaciones_ejecucion: str = ""
    incidencias: List[Dict[str, Any]] = field(default_factory=list)
    checklist: List[Dict[str, Any]] = field(default_factory=list)
    id: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("TAREAPR")
    def duracion_total_min(self): return int(sum(f.duracion_min for f in self.fases))
    def to_dict(self): return {**asdict(self),"fases":[f.to_dict() for f in self.fases],"duracion_total_min":self.duracion_total_min()}
    @classmethod
    def from_dict(cls,d):
        return cls(titulo=str(d.get("titulo","Tarea")),receta_id=str(d.get("receta_id","")),receta=str(d.get("receta","")),cantidad=float(d.get("cantidad",0) or 0),unidad=str(d.get("unidad","")),fases=[FaseProduccionReal.from_dict(x) for x in d.get("fases",[]) or []],prioridad=int(d.get("prioridad",50) or 50),origen=str(d.get("origen","")),estado_ejecucion=str(d.get("estado_ejecucion","pendiente") or "pendiente"),iniciado_en=str(d.get("iniciado_en","") or ""),pausado_en=str(d.get("pausado_en","") or ""),finalizado_en=str(d.get("finalizado_en","") or ""),cronometro_iniciado_en=str(d.get("cronometro_iniciado_en","") or ""),segundos_acumulados=int(d.get("segundos_acumulados",0) or 0),progreso_manual=float(d.get("progreso_manual",0) or 0),retraso_min=int(d.get("retraso_min",0) or 0),bloqueo=str(d.get("bloqueo","") or ""),observaciones_ejecucion=str(d.get("observaciones_ejecucion","") or ""),incidencias=list(d.get("incidencias",[]) or []),checklist=list(d.get("checklist",[]) or []),id=str(d.get("id") or nuevo_id("TAREAPR")))

@dataclass
class BloqueProduccionReal:
    inicio: str
    fin: str
    titulo: str
    tipo: str
    recurso: str = ""
    responsable: str = ""
    tarea_id: str = ""
    fase_id: str = ""
    receta_id: str = ""
    notas: str = ""
    id: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("BLOQPR")
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls,d):
        return cls(**{k:d.get(k,"") for k in ["inicio","fin","titulo","tipo","recurso","responsable","tarea_id","fase_id","receta_id","notas"]},id=str(d.get("id") or nuevo_id("BLOQPR")))

@dataclass
class PlanProduccionReal:
    evento_id: str = ""
    evento: str = ""
    pax: int = 0
    nombre: str = ""
    fecha: str = ""
    responsable: str = ""
    observaciones: str = ""
    tareas: List[TareaProduccionReal] = field(default_factory=list)
    cronograma: List[BloqueProduccionReal] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    configuracion_planificacion: Dict[str, Any] = field(default_factory=dict)
    planificacion_inteligente: Dict[str, Any] = field(default_factory=dict)
    asignacion_recursos: Dict[str, Any] = field(default_factory=dict)
    propuesta_optimizacion: Dict[str, Any] = field(default_factory=dict)
    historial_optimizacion: List[Dict[str, Any]] = field(default_factory=list)
    propuesta_optimizacion_recursos: Dict[str, Any] = field(default_factory=dict)
    historial_optimizacion_recursos: List[Dict[str, Any]] = field(default_factory=list)
    propuesta_recomendaciones: Dict[str, Any] = field(default_factory=dict)
    historial_recomendaciones: List[Dict[str, Any]] = field(default_factory=list)
    estado: str = "borrador"
    id: str = ""
    creado_en: str = ""
    actualizado_en: str = ""
    def __post_init__(self):
        if not self.id: self.id = nuevo_id("PLANPR")
        if not self.creado_en: self.creado_en = datetime.now().isoformat(timespec="seconds")
        if not self.actualizado_en: self.actualizado_en = self.creado_en
        if not self.nombre: self.nombre = self.evento or "Plan de producción"
    def duracion_total_min(self): return sum(t.duracion_total_min() for t in self.tareas)
    def to_dict(self): return {**asdict(self),"tareas":[t.to_dict() for t in self.tareas],"cronograma":[b.to_dict() for b in self.cronograma],"duracion_total_min":self.duracion_total_min()}
    @classmethod
    def from_dict(cls,d):
        return cls(evento_id=str(d.get("evento_id","")),evento=str(d.get("evento","")),pax=int(d.get("pax",0) or 0),nombre=str(d.get("nombre",d.get("evento","Plan de producción"))),fecha=str(d.get("fecha","")),responsable=str(d.get("responsable","")),observaciones=str(d.get("observaciones","")),tareas=[TareaProduccionReal.from_dict(x) for x in d.get("tareas",[]) or []],cronograma=[BloqueProduccionReal.from_dict(x) for x in d.get("cronograma",[]) or []],avisos=list(d.get("avisos",[]) or []),configuracion_planificacion=dict(d.get("configuracion_planificacion",{}) or {}),planificacion_inteligente=dict(d.get("planificacion_inteligente",{}) or {}),asignacion_recursos=dict(d.get("asignacion_recursos",{}) or {}),propuesta_optimizacion=dict(d.get("propuesta_optimizacion",{}) or {}),historial_optimizacion=list(d.get("historial_optimizacion",[]) or []),propuesta_optimizacion_recursos=dict(d.get("propuesta_optimizacion_recursos",{}) or {}),historial_optimizacion_recursos=list(d.get("historial_optimizacion_recursos",[]) or []),propuesta_recomendaciones=dict(d.get("propuesta_recomendaciones",{}) or {}),historial_recomendaciones=list(d.get("historial_recomendaciones",[]) or []),estado=str(d.get("estado","borrador")),id=str(d.get("id") or nuevo_id("PLANPR")),creado_en=str(d.get("creado_en","") or ""),actualizado_en=str(d.get("actualizado_en","") or ""))
