from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from CORE.host_ai_core import HostAICore
from SERVICIOS.compras_evento_474 import calcular_necesidades_evento, comparar_con_stock
from SERVICIOS.cierre_operativo_rp4 import CierreOperativoRP4
from SERVICIOS.detector_incidencias_537 import detectar_incidencias_operativas
from SERVICIOS.replanificador_inteligente_538 import replanificar_operativa_inteligente
from SERVICIOS.replanificador_inteligente_produccion import ReplanificadorInteligenteProduccion


ESTADOS_INCIDENCIA = {"ABIERTA", "EN_ANALISIS", "PENDIENTE_DECISION", "RESUELTA", "DESCARTADA", "BLOQUEANTE"}
GRAVEDADES = {"baja", "media", "alta", "critica"}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(str(p or "").strip().lower() for p in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12].upper()
    return f"{prefix}-{digest}"


@dataclass
class IncidenciaOperativaRP5:
    id: str
    tipo: str
    gravedad: str
    fecha_hora: str
    origen: str
    evento: str = ""
    servicio: str = ""
    pase: str = ""
    tarea: str = ""
    receta: str = ""
    elaboracion: str = ""
    articulo: str = ""
    recurso: str = ""
    persona: str = ""
    descripcion: str = ""
    evidencia: list[str] = field(default_factory=list)
    estado: str = "ABIERTA"
    impacto_calculado: dict[str, Any] = field(default_factory=dict)
    alternativas: list[dict[str, Any]] = field(default_factory=list)
    decision_humana: dict[str, Any] = field(default_factory=dict)
    plan_anterior: dict[str, Any] = field(default_factory=dict)
    plan_resultante: dict[str, Any] = field(default_factory=dict)
    trazabilidad: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VersionPlanRP5:
    id: str
    plan_id: str
    version: int
    estado: str
    generado_en: str
    fingerprint: str
    plan_anterior: dict[str, Any]
    plan_resultante: dict[str, Any]
    incidencia_id: str
    alternativa_id: str = ""
    usuario: str = "cocina"
    motivo: str = ""
    cambios_aplicados: list[dict[str, Any]] = field(default_factory=list)
    elementos_no_modificados: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IncidenciasReplanificacionRP5:
    """RP-5: incidencias y replanificación segura, explicable e idempotente.

    Reutiliza detector/replanificador existentes y solo persiste propuestas,
    incidencias y versiones de plan en DATOS/piloto/rp5_incidencias_replan.
    No consume stock, no crea pedidos definitivos y no aplica cambios directos
    sobre motores salvo registrar incidencias abiertas cuando procede.
    """

    VERSION = "RP-5"

    def __init__(self, base_dir: Path | str, core: Any | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.core = core or HostAICore(self.base_dir)
        self.rp4 = CierreOperativoRP4(self.base_dir, self.core)
        self.replanificador_produccion = ReplanificadorInteligenteProduccion(self.core)
        self.rp5_dir = self.base_dir / "DATOS" / "piloto" / "rp5_incidencias_replan"
        self.rp5_dir.mkdir(parents=True, exist_ok=True)
        self.path_incidencias = self.rp5_dir / "incidencias.json"
        self.path_propuestas = self.rp5_dir / "propuestas.json"
        self.path_versiones = self.rp5_dir / "versiones.json"

    # ------------------------------------------------------------------
    # Datos base
    # ------------------------------------------------------------------
    def _plan_activo(self, ahora: datetime | None = None) -> dict[str, Any]:
        ahora = ahora or datetime.now()
        fecha = ahora.date().isoformat()
        plan = self.rp4.obtener_plan_confirmado_para_fecha(fecha)
        if plan:
            return deepcopy(plan)
        propuestas = self._load_json(self.rp4.path_confirmados, [])
        if propuestas:
            propuestas.sort(key=lambda x: str(x.get("confirmado_en") or x.get("generado_en") or ""), reverse=True)
            return deepcopy(propuestas[0])
        return {
            "id": _stable_id("PLAN", fecha),
            "version": self.VERSION,
            "fecha_objetivo": fecha,
            "generado_en": _now_iso(),
            "eventos": {"manana": [], "posteriores": []},
            "tareas": [],
            "descongelaciones": [],
            "compras": {"lineas": [], "total": 0, "sin_cubrir": 0},
            "recepciones": [],
            "personal": {"modo": "sin_datos", "disponibles": [], "asignacion": [], "revision_manual": True},
            "alergenos": {},
            "caducidades": [],
            "alertas": [],
            "bloqueos": [],
            "cronologia": [],
            "estado": "propuesto",
            "fingerprint_entradas": _stable_id("FP", fecha),
            "trazabilidad": {"fuentes": []},
            "solo_propuesta": True,
        }

    def _incidencias_raw(self) -> list[dict[str, Any]]:
        return self._load_json(self.path_incidencias, [])

    # ------------------------------------------------------------------
    # Registro
    # ------------------------------------------------------------------
    def registrar_incidencia(
        self,
        *,
        tipo: str,
        gravedad: str = "media",
        descripcion: str,
        origen: str = "",
        evento_id: str = "",
        servicio: str = "",
        pase: str = "",
        tarea_id: str = "",
        receta: str = "",
        elaboracion: str = "",
        articulo: str = "",
        recurso: str = "",
        persona: str = "",
        evidencia: list[str] | None = None,
        fecha_hora: str = "",
        cantidad_prevista: float | None = None,
        cantidad_real: float | None = None,
        unidad: str = "",
        nuevo_valor: Any = None,
        plan_id: str = "",
    ) -> dict[str, Any]:
        descripcion = (descripcion or "").strip()
        if not descripcion:
            raise ValueError("La incidencia necesita una descripción.")
        tipo = self._norm(tipo)
        gravedad = self._norm_gravedad(gravedad)
        if gravedad not in GRAVEDADES:
            raise ValueError("La gravedad no es válida.")
        if cantidad_prevista is not None and _to_float(cantidad_prevista) < 0:
            raise ValueError("La cantidad prevista debe ser positiva.")
        if cantidad_real is not None and _to_float(cantidad_real) < 0:
            raise ValueError("La cantidad real debe ser positiva.")
        if fecha_hora:
            self._parse_datetime(fecha_hora)

        plan = self._plan_activo()
        if plan_id and str(plan.get("id")) != str(plan_id):
            plan = self._plan_por_id(plan_id) or plan

        if evento_id:
            self._asegurar_evento(evento_id)
        if tarea_id:
            self._asegurar_tarea(plan, tarea_id)
        if recurso:
            self._asegurar_recurso(plan, recurso)
        if articulo and unidad:
            self._asegurar_unidad_compatible(articulo, unidad)

        evidencias = [str(e).strip() for e in (evidencia or []) if str(e).strip()]
        momento = fecha_hora or _now_iso()
        fingerprint = self._fingerprint_incidente(plan.get("id"), tipo, descripcion, evento_id, tarea_id, articulo, recurso, persona, cantidad_prevista, cantidad_real, unidad, nuevo_valor)
        existente = next((i for i in self._incidencias_raw() if i.get("fingerprint") == fingerprint), None)
        if existente:
            return {**existente, "duplicada": True}

        incidencia = IncidenciaOperativaRP5(
            id=_stable_id("INC", fingerprint),
            tipo=tipo,
            gravedad=gravedad,
            fecha_hora=momento,
            origen=(origen or "operativa").strip() or "operativa",
            evento=evento_id,
            servicio=servicio,
            pase=pase,
            tarea=tarea_id,
            receta=receta,
            elaboracion=elaboracion,
            articulo=articulo,
            recurso=recurso,
            persona=persona,
            descripcion=descripcion,
            evidencia=evidencias,
            estado=self._estado_inicial(tipo, gravedad),
            fingerprint=fingerprint,
            trazabilidad={
                "plan_id": plan.get("id"),
                "fecha_objetivo": plan.get("fecha_objetivo"),
                "cantidad_prevista": cantidad_prevista,
                "cantidad_real": cantidad_real,
                "unidad": unidad,
                "nuevo_valor": nuevo_valor,
            },
        )
        data = self._incidencias_raw()
        data.append(incidencia.to_dict())
        self._write_json(self.path_incidencias, data)
        return incidencia.to_dict()

    def listar_incidencias(self, estado: str = "") -> list[dict[str, Any]]:
        estado_n = self._norm_estado(estado)
        data = self._incidencias_raw()
        if estado_n:
            data = [i for i in data if self._norm_estado(i.get("estado", "")) == estado_n]
        data.sort(key=lambda x: str(x.get("fecha_hora") or ""), reverse=True)
        return data

    def obtener_incidencia(self, incidencia_id: str) -> dict[str, Any]:
        inc = next((i for i in self._incidencias_raw() if str(i.get("id")) == str(incidencia_id)), None)
        if not inc:
            raise ValueError("No existe la incidencia indicada.")
        if not inc.get("impacto_calculado"):
            inc = self._enriquecer_incidencia(inc)
        return inc

    # ------------------------------------------------------------------
    # Impacto / alternativas
    # ------------------------------------------------------------------
    def analizar_impacto(self, incidencia_id: str) -> dict[str, Any]:
        inc = self.obtener_incidencia(incidencia_id)
        plan = self._plan_por_id(inc.get("trazabilidad", {}).get("plan_id")) or self._plan_activo()
        impacto = self._calcular_impacto(plan, inc)
        alternativas = self._proponer_alternativas(plan, inc, impacto)
        actual = dict(inc)
        actual["impacto_calculado"] = impacto
        actual["alternativas"] = alternativas
        self._sustituir_incidencia(actual)
        return actual

    def proponer_alternativas(self, incidencia_id: str) -> list[dict[str, Any]]:
        return list(self.analizar_impacto(incidencia_id).get("alternativas", []))

    # ------------------------------------------------------------------
    # Replanificación
    # ------------------------------------------------------------------
    def confirmar_replanificacion(
        self,
        incidencia_id: str,
        *,
        confirmacion: str,
        alternativa_id: str = "",
        usuario: str = "cocina",
        parcial: bool = False,
        motivo: str = "",
    ) -> dict[str, Any]:
        if str(confirmacion or "").strip().upper() != "CONFIRMAR":
            raise ValueError("Confirmación inválida. Debes escribir CONFIRMAR.")
        incidencia = self.analizar_impacto(incidencia_id)
        plan = self._plan_por_id(incidencia.get("trazabilidad", {}).get("plan_id")) or self._plan_activo()
        alternativas = incidencia.get("alternativas") or []
        alternativa = next((a for a in alternativas if str(a.get("id")) == str(alternativa_id)), alternativas[0] if alternativas else None)
        if alternativas and alternativa is None:
            raise ValueError("No existe la alternativa seleccionada.")

        version_actual = self._ultima_version_num(plan.get("id"))
        nuevo_plan = deepcopy(plan)
        impacto = incidencia.get("impacto_calculado") or self._calcular_impacto(plan, incidencia)
        cambios = self._aplicar_replanificacion(nuevo_plan, incidencia, alternativa, impacto)
        fingerprint = self._fingerprint_version(plan, incidencia, alternativa, cambios)
        version = VersionPlanRP5(
            id=_stable_id("VER", fingerprint),
            plan_id=str(plan.get("id")),
            version=version_actual + 1,
            estado="confirmada" if not parcial else "confirmada_parcial",
            generado_en=_now_iso(),
            fingerprint=fingerprint,
            plan_anterior=plan,
            plan_resultante=nuevo_plan,
            incidencia_id=str(incidencia_id),
            alternativa_id=str(alternativa.get("id") if alternativa else ""),
            usuario=(usuario or "cocina").strip() or "cocina",
            motivo=(motivo or (alternativa or {}).get("motivo") or incidencia.get("descripcion") or "").strip(),
            cambios_aplicados=cambios,
            elementos_no_modificados=self._elementos_no_modificados(plan, cambios),
            warnings=incidencia.get("warnings", []),
        )

        versiones = self._load_json(self.path_versiones, [])
        versiones.append(version.to_dict())
        self._write_json(self.path_versiones, versiones)

        propuesta = {
            "id": _stable_id("PROP", fingerprint),
            "plan_id": plan.get("id"),
            "incidencia_id": incidencia_id,
            "version": version.version,
            "estado": "confirmada" if not parcial else "confirmada_parcial",
            "creada_en": _now_iso(),
            "usuario": version.usuario,
            "alternativa_id": version.alternativa_id,
            "cambios_aplicados": cambios,
            "fingerprint": fingerprint,
            "plan_anterior": plan,
            "plan_resultante": nuevo_plan,
            "impacto": impacto,
        }
        propuestas = self._load_json(self.path_propuestas, [])
        propuestas = [p for p in propuestas if str(p.get("incidencia_id")) != str(incidencia_id) or str(p.get("estado")) == "descartada"]
        propuestas.append(propuesta)
        self._write_json(self.path_propuestas, propuestas)

        incidencia["estado"] = "PENDIENTE_DECISION" if parcial else "RESUELTA"
        incidencia["decision_humana"] = {
            "confirmada": True,
            "parcial": parcial,
            "usuario": version.usuario,
            "alternativa_id": version.alternativa_id,
            "motivo": version.motivo,
        }
        incidencia["plan_anterior"] = plan
        incidencia["plan_resultante"] = nuevo_plan
        incidencia["impacto_calculado"] = impacto
        incidencia["alternativas"] = alternativas
        self._sustituir_incidencia(incidencia)
        return {"ok": True, "estado": version.estado, "version": version.to_dict(), "propuesta": propuesta}

    def deshacer_propuesta(self, propuesta_id: str, motivo: str = "") -> dict[str, Any]:
        propuestas = self._load_json(self.path_propuestas, [])
        target = next((p for p in propuestas if str(p.get("id")) == str(propuesta_id)), None)
        if not target:
            raise ValueError("No existe la propuesta indicada.")
        if str(target.get("estado")) == "confirmada":
            raise ValueError("No se puede deshacer una propuesta ya confirmada.")
        target["estado"] = "descartada"
        target["motivo_descarte"] = motivo or "Propuesta no confirmada"
        target["deshecha_en"] = _now_iso()
        self._write_json(self.path_propuestas, propuestas)
        return target

    def cerrar_incidencia(self, incidencia_id: str, motivo: str = "") -> dict[str, Any]:
        incidencia = self.obtener_incidencia(incidencia_id)
        incidencia["estado"] = "RESUELTA"
        incidencia["cierre"] = {"motivo": motivo or "Cerrada manualmente", "cerrada_en": _now_iso()}
        self._sustituir_incidencia(incidencia)
        return incidencia

    def diferencias_plan(self, incidencia_id: str) -> dict[str, Any]:
        incidencia = self.obtener_incidencia(incidencia_id)
        plan_anterior = incidencia.get("plan_anterior") or self._plan_activo()
        plan_resultante = incidencia.get("plan_resultante") or plan_anterior
        return {
            "plan_anterior_id": plan_anterior.get("id"),
            "plan_resultante_id": plan_resultante.get("id"),
            "tareas_anteriores": len(plan_anterior.get("tareas", []) or []),
            "tareas_resultantes": len(plan_resultante.get("tareas", []) or []),
            "compras_anteriores": len((plan_anterior.get("compras") or {}).get("lineas", []) or []),
            "compras_resultantes": len((plan_resultante.get("compras") or {}).get("lineas", []) or []),
            "cronologia_anterior": len(plan_anterior.get("cronologia", []) or []),
            "cronologia_resultante": len(plan_resultante.get("cronologia", []) or []),
        }

    def resumen_operativo(self) -> dict[str, Any]:
        incidencias = self._incidencias_raw()
        abiertas = [i for i in incidencias if self._norm_estado(i.get("estado", "")) in {"abierta", "en_analisis", "pendiente_decision", "bloqueante"}]
        propuestas = self._load_json(self.path_propuestas, [])
        versiones = self._load_json(self.path_versiones, [])
        return {
            "incidencias_total": len(incidencias),
            "incidencias_abiertas": len(abiertas),
            "propuestas_total": len(propuestas),
            "versiones_total": len(versiones),
            "ultima_incidencia": abiertas[0] if abiertas else (incidencias[0] if incidencias else {}),
        }

    def vista_previa_briefing(self, plan_id: str = "") -> dict[str, Any]:
        plan = self._plan_por_id(plan_id) or self._plan_activo()
        incidencias = self.listar_incidencias()
        abiertas = [i for i in incidencias if self._norm_estado(i.get("estado", "")) in {"abierta", "en_analisis", "pendiente_decision", "bloqueante"}]
        versiones = [v for v in self._load_json(self.path_versiones, []) if str(v.get("plan_id")) == str(plan.get("id"))]
        versiones.sort(key=lambda x: int(x.get("version") or 0), reverse=True)
        return {
            "plan_id": plan.get("id"),
            "fecha_objetivo": plan.get("fecha_objetivo"),
            "plan_anterior": plan,
            "incidencias_abiertas": abiertas,
            "versiones": versiones,
            "prioridades": self._prioridades_desde_plan(plan, abiertas),
            "alertas": plan.get("alertas", []),
            "bloqueos": plan.get("bloqueos", []),
            "cronologia": plan.get("cronologia", []),
            "compras": plan.get("compras", {}),
            "produccion": {"tareas": plan.get("tareas", [])},
            "descongelaciones": plan.get("descongelaciones", []),
            "solo_propuesta": True,
        }

    def diagnostico(self) -> dict[str, Any]:
        plan = self._plan_activo(datetime(2026, 7, 15, 12, 0))
        if plan.get("eventos"):
            evento = (plan.get("eventos") or {}).get("manana", [])
            if evento:
                e = evento[0]
                incidencia = {
                    "id": _stable_id("INC", "diagnostico", plan.get("id"), e.get("id")),
                    "tipo": "aumento_comensales",
                    "gravedad": "media",
                    "fecha_hora": _now_iso(),
                    "origen": "diagnostico",
                    "evento": str(e.get("id") or ""),
                    "descripcion": "Aumento de comensales de diagnóstico",
                    "evidencia": ["diagnostico"],
                    "estado": "EN_ANALISIS",
                    "trazabilidad": {
                        "plan_id": plan.get("id"),
                        "fecha_objetivo": plan.get("fecha_objetivo"),
                        "cantidad_prevista": float(e.get("pax") or 0),
                        "cantidad_real": float(e.get("pax") or 0) + 12,
                        "unidad": "pax",
                        "nuevo_valor": float(e.get("pax") or 0) + 12,
                    },
                }
                analisis = self._calcular_impacto(plan, incidencia)
                return {
                    "diagnostico": "OK",
                    "incidencias": len(self._incidencias_raw()),
                    "versiones": len(self._load_json(self.path_versiones, [])),
                    "impacto": len(analisis.get("impacto_calculado", {}).get("elementos_afectados", [])),
                    "solo_propuesta": True,
                }
        return {
            "diagnostico": "OK",
            "incidencias": len(self._incidencias_raw()),
            "versiones": len(self._load_json(self.path_versiones, [])),
            "solo_propuesta": True,
        }

    # ------------------------------------------------------------------
    # Impacto y alternativas deterministas
    # ------------------------------------------------------------------
    def _calcular_impacto(self, plan: dict[str, Any], incidencia: dict[str, Any]) -> dict[str, Any]:
        tipo = self._norm(incidencia.get("tipo"))
        gravedad = self._norm_gravedad(incidencia.get("gravedad", "media"))
        evidencia = list(incidencia.get("evidencia") or [])
        elementos_afectados: list[dict[str, Any]] = []
        bloqueos: list[str] = []
        acciones_recalcular: list[str] = []
        retraso_est_min = 0
        cantidades: dict[str, float] = {}
        irreversible: list[str] = []

        evento = self._evento_plan(plan, incidencia)
        if tipo in {"aumento_comensales", "reduccion_comensales", "cambio_menu", "alergeno_nuevo", "cambio_horario", "cancelacion"}:
            elementos_afectados.extend([{"tipo": "evento", "id": evento.get("id"), "nombre": evento.get("nombre")}])
            acciones_recalcular.extend(["produccion", "compras", "cronologia", "alertas", "briefing", "plan_de_manana"])
        if tipo in {"producto_no_recibido", "recepcion_parcial", "producto_rechazado", "stock_inferior_previsto"}:
            elementos_afectados.extend([{"tipo": "compras", "id": "", "nombre": "pedidos abiertos"}, {"tipo": "stock", "id": "", "nombre": incidencia.get("articulo") or "artículo"}])
            acciones_recalcular.extend(["compras", "recepciones", "stock", "produccion", "briefing"])
        if tipo in {"elaboracion_perdida", "merma_superior", "tarea_retrasada"}:
            elementos_afectados.extend([{"tipo": "produccion", "id": incidencia.get("tarea"), "nombre": incidencia.get("elaboracion") or incidencia.get("tarea") or "tarea"}])
            acciones_recalcular.extend(["produccion", "cronologia", "briefing"])
        if tipo in {"fallo_recurso", "ausencia_personal"}:
            elementos_afectados.extend([{"tipo": "recursos", "id": incidencia.get("recurso"), "nombre": incidencia.get("recurso") or "recurso"}, {"tipo": "personal", "id": incidencia.get("persona"), "nombre": incidencia.get("persona") or "persona"}])
            acciones_recalcular.extend(["produccion", "cronologia", "briefing"])

        if tipo == "aumento_comensales":
            anterior = _to_float(incidencia.get("trazabilidad", {}).get("cantidad_prevista"), 0.0)
            nuevo = _to_float(incidencia.get("trazabilidad", {}).get("cantidad_real") or incidencia.get("trazabilidad", {}).get("nuevo_valor"), anterior)
            cantidades = {"anterior": anterior, "nuevo": nuevo, "diferencia": round(max(0.0, nuevo - anterior), 3)}
            retraso_est_min = int(max(0.0, nuevo - anterior) * 2)
            bloqueos.append("Recalcular producción y compras por aumento de comensales.")
        elif tipo == "reduccion_comensales":
            anterior = _to_float(incidencia.get("trazabilidad", {}).get("cantidad_prevista"), 0.0)
            nuevo = _to_float(incidencia.get("trazabilidad", {}).get("cantidad_real") or incidencia.get("trazabilidad", {}).get("nuevo_valor"), anterior)
            cantidades = {"anterior": anterior, "nuevo": nuevo, "sobrante": round(max(0.0, anterior - nuevo), 3)}
            bloqueos.append("Mantener producción ya realizada y valorar sobrante/merma manualmente.")
        elif tipo in {"producto_no_recibido", "recepcion_parcial", "producto_rechazado", "stock_inferior_previsto"}:
            articulo = incidencia.get("articulo") or incidencia.get("elaboracion") or incidencia.get("receta") or "artículo"
            stock = self.core.stock.stock_actual()
            stock_item = next((x for x in stock.get("items", []) if str(x.get("nombre") or "").lower() == str(articulo).lower() or str(x.get("articulo_id") or "").lower() == str(articulo).lower()), None)
            disponible = _to_float(stock_item.get("cantidad"), 0.0) if stock_item else 0.0
            previsto = _to_float(incidencia.get("trazabilidad", {}).get("cantidad_prevista"), 0.0)
            real = _to_float(incidencia.get("trazabilidad", {}).get("cantidad_real"), 0.0)
            cantidades = {"previsto": previsto, "real": real, "disponible": disponible, "faltante": round(max(0.0, previsto - real), 3)}
            if tipo == "stock_inferior_previsto":
                bloqueos.append("Stock real inferior al previsto: revisar pedidos y producción.")
        elif tipo == "cambio_menu":
            bloqueos.append("El cambio de menú obliga a revisar recetas y componentes afectados.")
        elif tipo == "alergeno_nuevo":
            bloqueos.append("El alérgeno nuevo puede invalidar platos y componentes sin equivalencia aprobada.")
        elif tipo == "fallo_recurso":
            retraso_est_min = 30
            bloqueos.append("El recurso no disponible bloquea solo tareas dependientes del recurso.")
        elif tipo == "ausencia_personal":
            retraso_est_min = 20
            bloqueos.append("Ausencia de personal: redistribuir tareas críticas y revisar sobrecarga.")
        elif tipo == "cambio_horario":
            retraso_est_min = 15
            bloqueos.append("Cambio de horario: recalcular cronología y tareas activas.")
        elif tipo == "cancelacion":
            bloqueos.append("Cancelación: el plan anterior queda trazado pero no se ejecuta el bloque afectado.")

        if gravedad == "critica":
            bloqueos.append("Gravedad crítica: requiere confirmación humana antes de aplicar cambios.")

        resumen = {
            "tipo": tipo,
            "gravedad": gravedad,
            "elementos_afectados": elementos_afectados,
            "bloqueos": self._dedupe_texto(bloqueos),
            "retraso_est_min": retraso_est_min,
            "cantidades": cantidades,
            "acciones_recalcular": self._dedupe_texto(acciones_recalcular),
            "irreversible": irreversible,
            "evidencia": evidencia,
            "severidad": self._severidad(tipo, gravedad, retraso_est_min, elementos_afectados),
        }
        return resumen

    def _proponer_alternativas(self, plan: dict[str, Any], incidencia: dict[str, Any], impacto: dict[str, Any]) -> list[dict[str, Any]]:
        tipo = self._norm(incidencia.get("tipo"))
        alternativas: list[dict[str, Any]] = []

        def alt(codigo: str, descripcion: str, riesgos: list[str], bloqueos: list[str], prioridad: int, motivo: str, reversible: bool, cambios: dict[str, Any] | None = None) -> dict[str, Any]:
            return {
                "id": _stable_id("ALT", incidencia.get("id"), codigo),
                "codigo": codigo,
                "descripcion": descripcion,
                "consecuencias": riesgos,
                "elementos_afectados": impacto.get("elementos_afectados", []),
                "riesgos": riesgos,
                "bloqueos": bloqueos,
                "prioridad": prioridad,
                "motivo": motivo,
                "reversibilidad": reversible,
                "cambios": cambios or {},
            }

        if tipo == "aumento_comensales":
            cantidades = impacto.get("cantidades", {})
            alternativas.extend([
                alt("recalcular", "Recalcular cantidades y compras", ["Puede aumentar faltantes"], [], 1, "El aumento exige ajustar producción y compras.", True, {"recalcular": True}),
                alt("compra_urgente", "Activar compra urgente", ["Dependencia de proveedor"], ["Confirmar pedido"], 2, "Permite cubrir faltante sin tocar stock ejecutado.", True, {"compra_urgente": True}),
                alt("reducir_menus", "Reducir guarniciones o extras", ["Sobra menos margen"], ["Validar equivalencias"], 3, "Reduce exposición a faltantes cuando el stock no alcanza.", True, {"reducir": True}),
            ])
        elif tipo == "reduccion_comensales":
            alternativas.extend([
                alt("mantener_y_marcar_sobrante", "Mantener producción ya hecha y marcar sobrante", ["Posible merma"], [], 1, "No se revierte lo ya ejecutado.", True, {"marcar_sobrante": True}),
                alt("ajustar_pendiente", "Ajustar solo producción pendiente", ["Menor producción futura"], [], 2, "Solo se toca lo no ejecutado.", True, {"ajustar_pendiente": True}),
            ])
        elif tipo in {"producto_no_recibido", "recepcion_parcial", "producto_rechazado", "stock_inferior_previsto"}:
            alternativas.extend([
                alt("usar_alternativa", "Usar lote o artículo equivalente aprobado", ["Revisar alérgenos y equivalencias"], [], 1, "Si existe una equivalencia ya aprobada, evita bloquear toda la línea.", True, {"usar_equivalente": True}),
                alt("compra_urgente", "Comprar urgente el faltante", ["Dependencia de proveedor"], ["Confirmar pedido"], 2, "Repite el flujo de compras sin duplicar el pedido definitivo.", True, {"compra_urgente": True}),
                alt("reducir_produccion", "Reducir producción afectada", ["Menor cobertura del servicio"], [], 3, "Reduce el riesgo operativo si no hay cobertura inmediata.", True, {"reducir_produccion": True}),
                alt("bloquear_plato", "Bloquear el plato afectado", ["Se elimina del servicio"], ["Revisar menú"], 4, "Se usa cuando no existe sustitución segura.", True, {"bloquear_plato": True}),
            ])
        elif tipo == "cambio_menu":
            alternativas.extend([
                alt("recalcular_menu", "Recalcular producción y compras del menú", ["Afecta coste y cronología"], [], 1, "El cambio de menú desplaza necesidades y producción.", True, {"recalcular_menu": True}),
                alt("bloquear_plato", "Bloquear plato no resuelto", ["Reduce oferta"], ["Validación manual"], 2, "Si no hay equivalencia aprobada, el plato queda bloqueado.", True, {"bloquear_plato": True}),
            ])
        elif tipo == "alergeno_nuevo":
            alternativas.extend([
                alt("bloquear_platos", "Bloquear platos afectados por el alérgeno", ["Reduce carta"], ["Revisar contaminación cruzada"], 1, "La seguridad alimentaria manda sobre la producción.", True, {"bloquear_platos": True}),
                alt("sustitucion_aprobada", "Usar sustitución ya aprobada", ["Puede cambiar coste"], [], 2, "Solo si ya existe una equivalencia registrada.", True, {"sustitucion_aprobada": True}),
            ])
        elif tipo == "fallo_recurso":
            alternativas.extend([
                alt("recurso_alterno", "Reasignar a otro recurso compatible", ["Requiere disponibilidad real"], [], 1, "Solo si hay recurso equivalente registrado.", True, {"recurso_alterno": True}),
                alt("cambiar_orden", "Cambiar el orden de tareas", ["Puede retrasar servicio"], [], 2, "Aprovecha tareas pasivas o independientes.", True, {"cambiar_orden": True}),
                alt("mover_jornada", "Mover la tarea a otra jornada", ["Aplaza producción"], ["Confirmación humana"], 3, "Útil cuando el recurso no vuelve a tiempo.", True, {"mover_jornada": True}),
            ])
        elif tipo == "ausencia_personal":
            alternativas.extend([
                alt("redistribuir", "Redistribuir tareas entre el personal disponible", ["Sobrecarga"], [], 1, "Mantiene la producción crítica con lo disponible.", True, {"redistribuir": True}),
                alt("aplastar_no_criticas", "Aplazar tareas no críticas", ["Menor avance"], [], 2, "Protege el servicio principal.", True, {"aplazar_no_criticas": True}),
            ])
        elif tipo == "cambio_horario":
            alternativas.extend([
                alt("reordenar", "Reordenar cronología y dependencias", ["Desplaza hitos"], [], 1, "El servicio cambia de hora y la cronología debe seguirlo.", True, {"reordenar": True}),
                alt("adelantar", "Adelantar tareas previas", ["Más carga temprana"], [], 2, "Permite absorber el cambio si hay capacidad.", True, {"adelantar": True}),
            ])
        elif tipo == "cancelacion":
            alternativas.extend([
                alt("cerrar_evento", "Cerrar el evento y cancelar lo no ejecutado", ["Se pierde cobertura"], ["Avisar a cocina"], 1, "La cancelación reduce el plan pero mantiene la trazabilidad.", True, {"cancelar": True}),
                alt("conservar_para_reutilizar", "Conservar producción reusable", ["Puede quedar sobrante"], [], 2, "Solo la producción ya hecha y reutilizable permanece.", True, {"reutilizar": True}),
            ])

        if not alternativas:
            alternativas.append(alt("revisar_manual", "Revisión manual", ["Sin automatización posible"], ["Confirmación humana"], 9, "No hay datos suficientes para una alternativa determinista.", False, {"revisar": True}))
        return alternativas

    def _aplicar_replanificacion(self, plan: dict[str, Any], incidencia: dict[str, Any], alternativa: dict[str, Any] | None, impacto: dict[str, Any]) -> list[dict[str, Any]]:
        cambios: list[dict[str, Any]] = []
        tipo = self._norm(incidencia.get("tipo"))
        plan.setdefault("meta_rp5", {})
        plan["meta_rp5"]["incidencia_id"] = incidencia.get("id")
        plan["meta_rp5"]["version_rp5"] = self._ultima_version_num(plan.get("id")) + 1
        plan["meta_rp5"]["estado"] = "replanificado"

        if tipo in {"aumento_comensales", "reduccion_comensales", "cambio_menu", "alergeno_nuevo", "cambio_horario", "cancelacion"}:
            evento = self._evento_plan(plan, incidencia)
            eventos_manana = (plan.get("eventos") or {}).get("manana", []) or []
            if evento:
                nuevo_valor = incidencia.get("trazabilidad", {}).get("cantidad_real") or incidencia.get("trazabilidad", {}).get("nuevo_valor")
                if tipo in {"aumento_comensales", "reduccion_comensales"} and nuevo_valor is not None:
                    for e in eventos_manana:
                        if str(e.get("id")) == str(evento.get("id")):
                            cambios.append({"tipo": "evento", "id": e.get("id"), "campo": "pax", "anterior": e.get("pax"), "nuevo": nuevo_valor})
                            e["pax"] = int(_to_float(nuevo_valor, _to_float(e.get("pax"), 0.0)))
                if tipo == "cambio_horario" and incidencia.get("trazabilidad", {}).get("nuevo_valor"):
                    for e in eventos_manana:
                        if str(e.get("id")) == str(evento.get("id")):
                            cambios.append({"tipo": "evento", "id": e.get("id"), "campo": "hora", "anterior": e.get("hora"), "nuevo": str(incidencia.get("trazabilidad", {}).get("nuevo_valor"))})
                            e["hora"] = str(incidencia.get("trazabilidad", {}).get("nuevo_valor"))
                if tipo == "cancelacion":
                    for e in eventos_manana:
                        if str(e.get("id")) == str(evento.get("id")):
                            cambios.append({"tipo": "evento", "id": e.get("id"), "campo": "estado", "anterior": e.get("estado"), "nuevo": "cancelado"})
                            e["estado"] = "cancelado"

        if tipo in {"producto_no_recibido", "recepcion_parcial", "producto_rechazado", "stock_inferior_previsto"}:
            articulo = incidencia.get("articulo") or incidencia.get("elaboracion") or ""
            for l in (plan.get("compras") or {}).get("lineas", []):
                if str(l.get("articulo") or "").lower() == str(articulo).lower():
                    cambios.append({"tipo": "compra", "id": l.get("id"), "campo": "decision", "anterior": l.get("decision"), "nuevo": "revisada"})
                    l["decision"] = "revisada"
                    l["impacto_rp5"] = tipo

        if tipo in {"fallo_recurso", "ausencia_personal", "tarea_retrasada", "elaboracion_perdida", "merma_superior"}:
            tarea_id = incidencia.get("tarea")
            for t in plan.get("tareas", []):
                if tarea_id and str(t.get("origen_tarea_id") or t.get("id")) != str(tarea_id):
                    continue
                cambios.append({"tipo": "tarea", "id": t.get("id"), "campo": "prioridad", "anterior": t.get("prioridad"), "nuevo": max(0, int(_to_float(t.get("prioridad"), 50) - 5))})
                t["prioridad"] = max(0, int(_to_float(t.get("prioridad"), 50) - 5))
                if tipo in {"fallo_recurso", "ausencia_personal"}:
                    t["bloqueada"] = True
                    t["bloqueo"] = incidencia.get("descripcion")

        if tipo in {"aumento_comensales", "reduccion_comensales", "cambio_menu", "alergeno_nuevo", "producto_no_recibido", "recepcion_parcial", "producto_rechazado", "stock_inferior_previsto"}:
            nuevos = self._recalcular_compras(plan, incidencia)
            cambios.append({"tipo": "compras", "id": plan.get("id"), "campo": "lineas", "nuevo": len(nuevos)})
            plan["compras"]["lineas"] = nuevos
            plan["compras"]["total"] = len(nuevos)
            plan["compras"]["sin_cubrir"] = len([x for x in nuevos if _to_float(x.get("cantidad_sin_cubrir"), 0.0) > 0])

        if tipo in {"fallo_recurso", "ausencia_personal", "tarea_retrasada", "cambio_horario"}:
            plan["cronologia"] = self._recalcular_cronologia(plan, incidencia)
            cambios.append({"tipo": "cronologia", "id": plan.get("id"), "campo": "cronologia", "nuevo": len(plan.get("cronologia", []))})

        plan["alertas"] = self._recalcular_alertas(plan, incidencia)
        plan["bloqueos"] = self._recalcular_bloqueos(plan, incidencia)
        plan["estado"] = "replanificado"
        plan["fingerprint_entradas"] = _stable_id("FP", plan.get("id"), incidencia.get("fingerprint"), plan["meta_rp5"].get("version_rp5"))
        plan["trazabilidad"] = {**(plan.get("trazabilidad") or {}), "rp5": {"incidencia_id": incidencia.get("id"), "alternativa_id": (alternativa or {}).get("id", ""), "version": plan["meta_rp5"]["version_rp5"]}}
        return cambios

    def _recalcular_compras(self, plan: dict[str, Any], incidencia: dict[str, Any]) -> list[dict[str, Any]]:
        eventos = (plan.get("eventos") or {}).get("manana", []) or []
        menu = (self._menus()[0] if self._menus() else {})
        stock = self._stock_map()
        lineas: list[dict[str, Any]] = []
        for evento in eventos:
            pax = int(evento.get("pax") or 0)
            if self._norm(incidencia.get("tipo")) == "reduccion_comensales":
                nuevo = _to_float(incidencia.get("trazabilidad", {}).get("cantidad_real") or incidencia.get("trazabilidad", {}).get("nuevo_valor"), pax)
                pax = int(nuevo)
            if self._norm(incidencia.get("tipo")) == "aumento_comensales":
                nuevo = _to_float(incidencia.get("trazabilidad", {}).get("cantidad_real") or incidencia.get("trazabilidad", {}).get("nuevo_valor"), pax)
                pax = int(nuevo)
            evento_ctx = {"id_evento": evento.get("id"), "nombre": evento.get("nombre"), "personas": pax, "menus": [menu] if menu else []}
            necesidades = calcular_necesidades_evento(evento_ctx, menu=menu if menu else None)
            comparadas = comparar_con_stock(necesidades, stock=stock)
            for nec in comparadas:
                faltante = _to_float(nec.get("cantidad_a_comprar"), 0.0)
                if faltante <= 0:
                    continue
                lineas.append({
                    "id": _stable_id("RPCOMP", evento.get("id"), nec.get("articulo"), incidencias_key(self._norm(incidencia.get("tipo")))),
                    "evento": evento.get("nombre"),
                    "evento_id": evento.get("id"),
                    "articulo": nec.get("articulo"),
                    "unidad": nec.get("unidad"),
                    "cantidad_faltante": round(faltante, 3),
                    "cantidad_sin_cubrir": round(faltante, 3),
                    "proveedor_sugerido": nec.get("proveedor_preferente") or "Sin proveedor",
                    "estado": "pendiente",
                    "urgente": True,
                    "decision": "pendiente",
                    "dia": int(evento.get("dias") or 0),
                })
        return self._dedupe_by_id(lineas)

    def _recalcular_cronologia(self, plan: dict[str, Any], incidencia: dict[str, Any]) -> list[dict[str, Any]]:
        cronologia = list(plan.get("cronologia", []) or [])
        evento = self._evento_plan(plan, incidencia)
        if not evento:
            return cronologia
        extra = []
        if self._norm(incidencia.get("tipo")) in {"cambio_horario", "cancelacion"}:
            extra.append({"id": _stable_id("CRONO", incidencia.get("id"), "briefing"), "hora": "09:30", "titulo": "Briefing revisado por incidencia", "tipo": "briefing", "responsable": "jefe_cocina"})
        elif self._norm(incidencia.get("tipo")) in {"aumento_comensales", "reduccion_comensales", "cambio_menu", "alergeno_nuevo"}:
            extra.append({"id": _stable_id("CRONO", incidencia.get("id"), "recalculo"), "hora": "09:45", "titulo": f"Recalcular servicio {evento.get('nombre')}", "tipo": "replanificacion", "responsable": "jefe_cocina"})
        else:
            extra.append({"id": _stable_id("CRONO", incidencia.get("id"), "resolucion"), "hora": "10:00", "titulo": f"Resolver incidencia {incidencia.get('tipo')}", "tipo": "incidencia", "responsable": incidencia.get("persona") or "jefe_cocina"})
        return self._dedupe_by_id(extra + cronologia)

    def _recalcular_alertas(self, plan: dict[str, Any], incidencia: dict[str, Any]) -> list[dict[str, Any]]:
        alertas = list(plan.get("alertas", []) or [])
        tipo = self._norm(incidencia.get("tipo"))
        if tipo == "aumento_comensales":
            alertas.append({"id": _stable_id("ALT", incidencia.get("id"), "comensales"), "tipo": "aumento_comensales", "nivel": "alto", "detalle": "Aumento de comensales: revisar producción y compras."})
        elif tipo == "reduccion_comensales":
            alertas.append({"id": _stable_id("ALT", incidencia.get("id"), "comensales"), "tipo": "reduccion_comensales", "nivel": "medio", "detalle": "Reducción de comensales: puede quedar sobrante."})
        elif tipo in {"producto_no_recibido", "recepcion_parcial", "producto_rechazado", "stock_inferior_previsto"}:
            alertas.append({"id": _stable_id("ALT", incidencia.get("id"), "stock"), "tipo": tipo, "nivel": "alto", "detalle": "Recepción/stock afecta a producción y compras."})
        elif tipo in {"fallo_recurso", "ausencia_personal"}:
            alertas.append({"id": _stable_id("ALT", incidencia.get("id"), "recurso"), "tipo": tipo, "nivel": "alto", "detalle": "Recurso o personal insuficiente: revisar cronología."})
        elif tipo in {"cancelacion"}:
            alertas.append({"id": _stable_id("ALT", incidencia.get("id"), "cancelacion"), "tipo": tipo, "nivel": "medio", "detalle": "Evento cancelado: conservar trazabilidad y revisar sobrantes."})
        return self._dedupe_by_id(alertas)

    def _recalcular_bloqueos(self, plan: dict[str, Any], incidencia: dict[str, Any]) -> list[dict[str, Any]]:
        bloqueos = list(plan.get("bloqueos", []) or [])
        tipo = self._norm(incidencia.get("tipo"))
        if tipo in {"fallo_recurso", "ausencia_personal", "cambio_menu", "alergeno_nuevo", "producto_no_recibido", "recepcion_parcial", "producto_rechazado", "stock_inferior_previsto", "cancelacion"}:
            bloqueos.append({"id": _stable_id("BLOQ", incidencia.get("id"), tipo), "tipo": tipo, "detalle": incidencia.get("descripcion")})
        return self._dedupe_by_id(bloqueos)

    def _prioridades_desde_plan(self, plan: dict[str, Any], abiertas: list[dict[str, Any]]) -> list[dict[str, Any]]:
        prioridades = []
        for item in plan.get("cronologia", []) or []:
            prioridades.append({"titulo": item.get("titulo"), "tipo": item.get("tipo"), "prioridad": 100 if item.get("tipo") == "briefing" else 70})
        for inc in abiertas[:5]:
            prioridades.append({"titulo": f"Incidencia {inc.get('tipo')}", "tipo": "INCIDENCIA", "prioridad": 90})
        return prioridades[:10]

    def _elementos_no_modificados(self, plan: dict[str, Any], cambios: list[dict[str, Any]]) -> list[str]:
        mutados = {f"{c.get('tipo')}:{c.get('id')}:{c.get('campo')}" for c in cambios}
        inventario = [
            f"evento:{e.get('id')}:pax" for e in (plan.get("eventos") or {}).get("manana", []) or []
        ] + [
            f"tarea:{t.get('id')}:estado" for t in plan.get("tareas", []) or []
        ]
        return [x for x in inventario if x not in mutados]

    @staticmethod
    def _dedupe_by_id(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        vistos = set()
        salida = []
        for item in items:
            ident = str(item.get("id") or "").strip()
            if ident and ident in vistos:
                continue
            if ident:
                vistos.add(ident)
            salida.append(item)
        return salida

    # ------------------------------------------------------------------
    # Validaciones y helpers
    # ------------------------------------------------------------------
    def _asegurar_evento(self, evento_id: str) -> None:
        try:
            self.core.eventos.obtener(evento_id)
        except Exception as exc:
            raise ValueError(f"El evento no existe: {evento_id}") from exc

    def _asegurar_tarea(self, plan: dict[str, Any], tarea_id: str) -> None:
        tareas = list(plan.get("tareas", []) or [])
        if not any(str(t.get("id")) == str(tarea_id) or str(t.get("origen_tarea_id")) == str(tarea_id) for t in tareas):
            raise ValueError(f"La tarea no existe en el plan activo: {tarea_id}")

    def _asegurar_recurso(self, plan: dict[str, Any], recurso: str) -> None:
        recurso_n = str(recurso or "").strip().lower()
        if not recurso_n:
            raise ValueError("El recurso es obligatorio.")
        recursos = {str(t.get("recurso") or "").strip().lower() for t in (plan.get("tareas", []) or [])}
        recursos.update({str(b.get("recurso") or "").strip().lower() for b in (plan.get("cronologia", []) or [])})
        if recurso_n not in recursos:
            raise ValueError(f"El recurso no existe en el plan: {recurso}")

    def _asegurar_unidad_compatible(self, articulo: str, unidad: str) -> None:
        articulo_n = str(articulo or "").strip().lower()
        unidad_n = str(unidad or "").strip().lower()
        stock = self.core.stock.stock_actual().get("items", [])
        compatibles = [x for x in stock if str(x.get("nombre") or "").strip().lower() == articulo_n or str(x.get("articulo_id") or "").strip().lower() == articulo_n]
        if compatibles and any(str(x.get("unidad") or "").strip().lower() != unidad_n for x in compatibles):
            raise ValueError("La unidad no es compatible con el stock existente.")

    def _asegurar_personal(self, persona: str) -> None:
        if persona and not str(persona).strip():
            raise ValueError("La persona no es válida.")

    def _plan_por_id(self, plan_id: str) -> dict[str, Any] | None:
        if not plan_id:
            return None
        for p in self._load_json(self.rp4.path_confirmados, []):
            if str(p.get("id")) == str(plan_id):
                return deepcopy(p)
        for p in self._load_json(self.rp4.path_propuestas, []):
            if str(p.get("id")) == str(plan_id):
                return deepcopy(p)
        return None

    def _evento_plan(self, plan: dict[str, Any], incidencia: dict[str, Any]) -> dict[str, Any]:
        evento_id = str(incidencia.get("evento") or "")
        for e in (plan.get("eventos") or {}).get("manana", []) or []:
            if str(e.get("id")) == evento_id:
                return e
        if (plan.get("eventos") or {}).get("manana"):
            return (plan.get("eventos") or {}).get("manana", [])[0]
        return {}

    def _menus(self) -> list[dict[str, Any]]:
        return self._load_json(self.base_dir / "DATOS" / "db" / "menus.json", [])

    def _stock_map(self) -> dict[str, float]:
        stock = self.core.stock.stock_actual().get("items", [])
        out = {}
        for item in stock:
            nombre = str(item.get("nombre") or "").strip().lower()
            if not nombre:
                continue
            out[nombre] = _to_float(item.get("cantidad"), 0.0)
        return out

    def _replan_detector(self, plan: dict[str, Any], incidencia: dict[str, Any], impacto: dict[str, Any]) -> dict[str, Any]:
        contexto = {
            "stock": [{"nombre": i.get("nombre"), "disponible": i.get("cantidad"), "necesario": i.get("cantidad") + 1, "imprescindible": True} for i in impacto.get("elementos_afectados", []) if i.get("tipo") == "stock"],
            "tareas": [{"codigo": t.get("id"), "nombre": t.get("titulo"), "retrasada": t.get("bloqueada") or False, "bloquea_servicio": t.get("bloqueada") or False} for t in plan.get("tareas", []) or []],
            "personal": {"disponibles": len((plan.get("personal") or {}).get("disponibles", [])), "necesarios": len((plan.get("personal") or {}).get("disponibles", []))},
        }
        planning = {"ok": True, "plan": [{"codigo": t.get("id"), "nombre": t.get("titulo"), "bloqueado_por": ["INCIDENCIA"] if t.get("bloqueada") else []} for t in plan.get("tareas", []) or []]}
        return detectar_incidencias_operativas(planning, prioridades={}, contexto=contexto)

    def _fingerprint_incidente(self, *parts: Any) -> str:
        raw = json.dumps(parts, ensure_ascii=False, sort_keys=False, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _fingerprint_version(self, plan: dict[str, Any], incidencia: dict[str, Any], alternativa: dict[str, Any] | None, cambios: list[dict[str, Any]]) -> str:
        raw = json.dumps({"plan_id": plan.get("id"), "incidencia_id": incidencia.get("id"), "alternativa_id": (alternativa or {}).get("id", ""), "cambios": cambios, "fingerprint_base": plan.get("fingerprint_entradas")}, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _ultima_version_num(self, plan_id: str) -> int:
        versiones = [v for v in self._load_json(self.path_versiones, []) if str(v.get("plan_id")) == str(plan_id)]
        if not versiones:
            return 0
        return max(int(v.get("version") or 0) for v in versiones)

    def _sustituir_incidencia(self, incidencia: dict[str, Any]) -> None:
        data = self._incidencias_raw()
        for idx, item in enumerate(data):
            if str(item.get("id")) == str(incidencia.get("id")):
                data[idx] = incidencia
                self._write_json(self.path_incidencias, data)
                return
        data.append(incidencia)
        self._write_json(self.path_incidencias, data)

    def _enriquecer_incidencia(self, incidencia: dict[str, Any]) -> dict[str, Any]:
        plan = self._plan_por_id(incidencia.get("trazabilidad", {}).get("plan_id")) or self._plan_activo()
        impacto = self._calcular_impacto(plan, incidencia)
        alternativas = self._proponer_alternativas(plan, incidencia, impacto)
        incidencia = deepcopy(incidencia)
        incidencia["impacto_calculado"] = impacto
        incidencia["alternativas"] = alternativas
        incidencia["plan_anterior"] = plan
        incidencia.setdefault("warnings", [])
        return incidencia

    def _estado_inicial(self, tipo: str, gravedad: str) -> str:
        if gravedad == "critica" or tipo in {"fallo_recurso", "cancelacion", "producto_no_recibido"}:
            return "BLOQUEANTE"
        if tipo in {"aumento_comensales", "reduccion_comensales", "cambio_menu", "alergeno_nuevo", "producto_no_recibido", "recepcion_parcial", "producto_rechazado", "stock_inferior_previsto", "tarea_retrasada"}:
            return "PENDIENTE_DECISION"
        return "EN_ANALISIS"

    def _severidad(self, tipo: str, gravedad: str, retraso_min: int, elementos_afectados: list[dict[str, Any]]) -> str:
        if gravedad == "critica" or tipo in {"cancelacion", "fallo_recurso"}:
            return "alta"
        if retraso_min >= 30 or len(elementos_afectados) >= 4:
            return "alta"
        if retraso_min > 0:
            return "media"
        return gravedad

    @staticmethod
    def _norm(valor: Any) -> str:
        return str(valor or "").strip().lower()

    @staticmethod
    def _norm_gravedad(valor: Any) -> str:
        texto = str(valor or "").strip().lower()
        return {"critico": "critica", "crítico": "critica"}.get(texto, texto)

    @staticmethod
    def _norm_estado(valor: Any) -> str:
        texto = str(valor or "").strip().lower()
        return {
            "abierta": "abierta",
            "en_analisis": "en_analisis",
            "pendiente_decision": "pendiente_decision",
            "resuelta": "resuelta",
            "descartada": "descartada",
            "bloqueante": "bloqueante",
        }.get(texto, texto)

    @staticmethod
    def _dedupe_texto(items: list[str]) -> list[str]:
        seen = set()
        out = []
        for item in items:
            txt = str(item or "").strip()
            if not txt or txt in seen:
                continue
            seen.add(txt)
            out.append(txt)
        return out

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        texto = str(value or "").strip()
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%d/%m/%Y %H:%M"):
            try:
                return datetime.strptime(texto, fmt)
            except ValueError:
                continue
        raise ValueError("La fecha/hora no tiene un formato válido.")

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return deepcopy(default)

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))
        tmp.replace(path)


def incidencias_key(tipo: str) -> str:
    return _stable_id("K", tipo or "rp5")


def formatear_diagnostico_rp5(d: dict[str, Any]) -> str:
    return "\n".join([
        "RP-5 — INCIDENCIAS Y REPLANIFICACIÓN",
        "=" * 78,
        f"Diagnóstico: {d.get('diagnostico')} | Incidencias: {d.get('incidencias', 0)} | Versiones: {d.get('versiones', 0)}",
        f"Impacto: {d.get('impacto', 0)} | Solo propuesta: {'SÍ' if d.get('solo_propuesta') else 'NO'}",
    ])


__all__ = [
    "IncidenciasReplanificacionRP5",
    "IncidenciaOperativaRP5",
    "VersionPlanRP5",
    "formatear_diagnostico_rp5",
]
