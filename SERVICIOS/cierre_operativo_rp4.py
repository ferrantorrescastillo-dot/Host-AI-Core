from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from SERVICIOS.compras_evento_474 import calcular_necesidades_evento, comparar_con_stock
from SERVICIOS.personal_evento_475 import calcular_personal_evento


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


class CierreOperativoRP4:
    """RP-4: cierre operativo y preparación automática del día siguiente.

    No ejecuta acciones irreversibles: no consume stock, no crea pedidos definitivos,
    no cambia eventos ni planes de producción. Solo genera propuestas revisables y
    persistidas en DATOS/piloto/rp4_preparar_manana.
    """

    VERSION = "RP-4"

    def __init__(self, base_dir: Path | str, core: Any | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.core = core
        self.db_dir = self.base_dir / "DATOS" / "db"
        self.rp4_dir = self.base_dir / "DATOS" / "piloto" / "rp4_preparar_manana"
        self.rp4_dir.mkdir(parents=True, exist_ok=True)
        self.path_cierres = self.rp4_dir / "cierres.json"
        self.path_propuestas = self.rp4_dir / "propuestas.json"
        self.path_confirmados = self.rp4_dir / "confirmados.json"

    # ------------------------------------------------------------------
    # Flujo principal
    # ------------------------------------------------------------------
    def cerrar_jornada(self, ahora: datetime | None = None) -> dict[str, Any]:
        ahora = ahora or datetime.now()
        target = (ahora.date() + timedelta(days=1)).isoformat()
        planes = self._load_json(self.db_dir / "planes_produccion.json", [])
        pedidos = self._load_json(self.db_dir / "compras_pedidos.json", [])
        incidencias = self._collect_incidencias_produccion(planes)
        abiertas = self._count_tareas_abiertas(planes)
        resumen = {
            "id": _stable_id("CIERRE", ahora.date().isoformat(), ahora.strftime("%H:%M")),
            "version": self.VERSION,
            "fecha": ahora.date().isoformat(),
            "hora": ahora.strftime("%H:%M"),
            "objetivo_plan": target,
            "tareas_produccion_abiertas": abiertas,
            "pedidos_abiertos": len([p for p in pedidos if str(p.get("estado") or "").lower() not in {"recibido", "cancelado"}]),
            "incidencias_abiertas": len(incidencias),
            "incidencias": incidencias[:20],
            "estado": "CERRADA_CON_AVISOS" if incidencias else "CERRADA",
            "generado_en": ahora.isoformat(timespec="seconds"),
            "solo_propuesta": True,
        }
        cierres = self._load_json(self.path_cierres, [])
        cierres.append(resumen)
        self._write_json(self.path_cierres, cierres)
        return resumen

    def preparar_manana(self, ahora: datetime | None = None, horizonte_dias: int = 3) -> dict[str, Any]:
        ahora = ahora or datetime.now()
        horizonte_dias = max(2, int(horizonte_dias or 3))
        fecha_obj = ahora.date() + timedelta(days=1)

        eventos_raw = self._load_json(self.db_dir / "eventos.json", [])
        menus = self._load_json(self.db_dir / "menus.json", [])
        planes = self._load_json(self.db_dir / "planes_produccion.json", [])
        pedidos = self._load_json(self.db_dir / "compras_pedidos.json", [])
        articulos = self._load_json(self.db_dir / "articulos.json", [])
        stock_lotes = self._load_json(self.db_dir / "stock_lotes.json", [])
        stock_inicial = self._load_json(self.db_dir / "stock_inicial.json", [])
        personal_turnos = self._load_json(self.db_dir / "personal_turnos.json", [])
        incidencias_ext = self._load_json(self.db_dir / "incidencias_abiertas.json", [])

        eventos_horizonte = self._eventos_en_horizonte(eventos_raw, fecha_obj, horizonte_dias)
        eventos_manana = [e for e in eventos_horizonte if e.get("dias") == 0]
        eventos_posteriores = [e for e in eventos_horizonte if e.get("dias") > 0]

        stock_map = self._stock_map(stock_lotes, stock_inicial)
        produccion = self._plan_produccion(planes, eventos_horizonte, fecha_obj)
        descongelaciones = self._plan_descongelaciones(produccion.get("tareas", []), fecha_obj)
        compras = self._plan_compras(eventos_horizonte, menus, stock_map, pedidos, fecha_obj)
        recepciones = self._plan_recepciones(pedidos, compras.get("lineas", []), fecha_obj)
        personal = self._plan_personal(eventos_manana, menus, personal_turnos)
        alergenos = self._plan_alergenos(eventos_horizonte, articulos)
        caducidades = self._plan_caducidades(stock_lotes, fecha_obj)
        cronologia = self._plan_cronologia(eventos_manana, produccion.get("tareas", []), recepciones, personal)
        alertas, bloqueos = self._plan_alertas_bloqueos(
            produccion=produccion,
            descongelaciones=descongelaciones,
            compras=compras,
            recepciones=recepciones,
            personal=personal,
            alergenos=alergenos,
            caducidades=caducidades,
            incidencias_ext=incidencias_ext,
            eventos_manana=eventos_manana,
        )

        entradas_fingerprint = {
            "fecha_objetivo": fecha_obj.isoformat(),
            "horizonte_dias": horizonte_dias,
            "eventos": self._safe_dump(eventos_horizonte),
            "menus": self._safe_dump(menus),
            "planes": self._safe_dump(planes),
            "stock": self._safe_dump(stock_map),
            "pedidos": self._safe_dump(pedidos),
            "personal_turnos": self._safe_dump(personal_turnos),
        }
        fingerprint = hashlib.sha256(json.dumps(entradas_fingerprint, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        plan_id = _stable_id("TMPLAN", fecha_obj.isoformat())

        previous = self._latest_confirmado(plan_id) or self._latest_propuesta(plan_id)
        plan = {
            "id": plan_id,
            "version": self.VERSION,
            "fecha_objetivo": fecha_obj.isoformat(),
            "generado_en": ahora.isoformat(timespec="seconds"),
            "horizonte_dias": horizonte_dias,
            "eventos": {
                "manana": eventos_manana,
                "posteriores": eventos_posteriores,
            },
            "tareas": produccion.get("tareas", []),
            "descongelaciones": descongelaciones,
            "compras": compras,
            "recepciones": recepciones,
            "personal": personal,
            "alergenos": alergenos,
            "caducidades": caducidades,
            "alertas": alertas,
            "bloqueos": bloqueos,
            "cronologia": cronologia,
            "acciones_hoy": self._clasificar_acciones_hoy(produccion, compras, descongelaciones),
            "estado": "propuesto",
            "fingerprint_entradas": fingerprint,
            "trazabilidad": {
                "fuentes": [
                    "DATOS/db/eventos.json",
                    "DATOS/db/menus.json",
                    "DATOS/db/planes_produccion.json",
                    "DATOS/db/compras_pedidos.json",
                    "DATOS/db/stock_lotes.json",
                    "DATOS/db/stock_inicial.json",
                    "DATOS/db/articulos.json",
                ],
                "warnings": self._warnings_fuentes(personal_turnos),
            },
            "solo_propuesta": True,
        }
        if previous:
            plan = self._preservar_decisiones(previous, plan)

        propuestas = self._load_json(self.path_propuestas, [])
        propuestas = [p for p in propuestas if str(p.get("id")) != plan_id]
        propuestas.append(plan)
        self._write_json(self.path_propuestas, propuestas)
        return plan

    def confirmar_plan(
        self,
        plan_id: str,
        *,
        confirmacion: str,
        parcial: bool = False,
        decisiones: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if str(confirmacion or "").strip().upper() != "CONFIRMAR":
            raise ValueError("Confirmación inválida. Debes escribir CONFIRMAR.")
        plan = self._latest_propuesta(plan_id)
        if not plan:
            raise ValueError("No existe propuesta para ese plan.")
        actualizado = deepcopy(plan)
        for dec in decisiones or []:
            self._aplicar_decision(actualizado, dec)
        actualizado["estado"] = "confirmado_parcial" if parcial else "confirmado"
        actualizado["confirmado_en"] = _now_iso()
        actualizado["confirmacion_humana"] = {
            "tipo": "parcial" if parcial else "completa",
            "decisiones": list(decisiones or []),
        }

        confirmados = self._load_json(self.path_confirmados, [])
        confirmados = [p for p in confirmados if str(p.get("id")) != str(plan_id)]
        confirmados.append(actualizado)
        self._write_json(self.path_confirmados, confirmados)
        return actualizado

    def ver_propuesta(self, fecha_objetivo: str = "") -> dict[str, Any] | None:
        propuestas = self._load_json(self.path_propuestas, [])
        if not propuestas:
            return None
        if fecha_objetivo:
            propuestas = [p for p in propuestas if str(p.get("fecha_objetivo")) == fecha_objetivo]
            if not propuestas:
                return None
        propuestas.sort(key=lambda x: str(x.get("generado_en") or ""), reverse=True)
        return propuestas[0]

    def obtener_plan_confirmado_para_fecha(self, fecha_objetivo: str) -> dict[str, Any] | None:
        confirmados = self._load_json(self.path_confirmados, [])
        encontrados = [p for p in confirmados if str(p.get("fecha_objetivo")) == str(fecha_objetivo)]
        if not encontrados:
            return None
        encontrados.sort(key=lambda x: str(x.get("confirmado_en") or x.get("generado_en") or ""), reverse=True)
        return encontrados[0]

    def vista_previa_briefing(self, plan_id: str) -> dict[str, Any]:
        plan = self._latest_confirmado(plan_id) or self._latest_propuesta(plan_id)
        if not plan:
            raise ValueError("No existe plan para vista previa.")
        return {
            "fecha_objetivo": plan.get("fecha_objetivo"),
            "eventos": list((plan.get("eventos") or {}).get("manana", [])),
            "cronologia": list(plan.get("cronologia") or []),
            "prioridades": [
                {
                    "id": t.get("id"),
                    "titulo": t.get("titulo"),
                    "prioridad": t.get("prioridad"),
                    "estado": t.get("estado"),
                }
                for t in (plan.get("tareas") or [])[:8]
            ],
            "personal": plan.get("personal", {}),
            "produccion": {
                "total_tareas": len(plan.get("tareas") or []),
                "pendientes": len([t for t in plan.get("tareas") or [] if str(t.get("estado") or "").lower() != "finalizada"]),
            },
            "compras": plan.get("compras", {}),
            "recepciones": plan.get("recepciones", []),
            "descongelaciones": plan.get("descongelaciones", []),
            "alergenos": plan.get("alergenos", {}),
            "alertas": plan.get("alertas", []),
            "bloqueos": plan.get("bloqueos", []),
            "estado": plan.get("estado"),
            "solo_propuesta": True,
        }

    def diagnostico(self) -> dict[str, Any]:
        plan = self.preparar_manana(datetime(2026, 7, 15, 21, 0), horizonte_dias=3)
        ok = isinstance(plan.get("fingerprint_entradas"), str) and bool(plan.get("id"))
        return {
            "diagnostico": "OK" if ok else "ERROR",
            "version": self.VERSION,
            "fecha_objetivo": plan.get("fecha_objetivo"),
            "tareas": len(plan.get("tareas") or []),
            "compras": len((plan.get("compras") or {}).get("lineas") or []),
            "descongelaciones": len(plan.get("descongelaciones") or []),
            "alertas": len(plan.get("alertas") or []),
            "bloqueos": len(plan.get("bloqueos") or []),
            "solo_propuesta": True,
        }

    # ------------------------------------------------------------------
    # Construcción de secciones
    # ------------------------------------------------------------------
    def _eventos_en_horizonte(self, eventos_raw: list[dict[str, Any]], fecha_obj: date, horizonte_dias: int) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for evt in eventos_raw if isinstance(eventos_raw, list) else []:
            fecha = self._parse_fecha(evt.get("fecha"))
            if not fecha:
                continue
            dias = (fecha - fecha_obj).days
            if dias < 0 or dias > horizonte_dias - 1:
                continue
            out.append({
                "id": str(evt.get("id") or evt.get("id_evento") or ""),
                "nombre": str(evt.get("nombre") or "Evento"),
                "fecha": fecha.isoformat(),
                "hora": str(evt.get("hora") or evt.get("hora_inicio") or ""),
                "pax": int(evt.get("pax") or evt.get("personas") or 0),
                "estado": str(evt.get("estado") or "pendiente"),
                "dias": dias,
                "observaciones": str(evt.get("observaciones") or ""),
            })
        out.sort(key=lambda x: (x.get("fecha"), x.get("hora") or "23:59", x.get("nombre")))
        return out

    def _stock_map(self, stock_lotes: list[dict[str, Any]], stock_inicial: list[dict[str, Any]]) -> dict[str, float]:
        out: dict[str, float] = {}
        for lote in stock_lotes if isinstance(stock_lotes, list) else []:
            nombre = str(lote.get("nombre") or "").strip()
            if not nombre:
                continue
            out[nombre.lower()] = out.get(nombre.lower(), 0.0) + _to_float(lote.get("cantidad"), 0.0)
        if out:
            return out
        for item in stock_inicial if isinstance(stock_inicial, list) else []:
            nombre = str(item.get("articulo") or item.get("nombre") or "").strip()
            if not nombre:
                continue
            out[nombre.lower()] = _to_float(item.get("stock_actual") or item.get("cantidad"), 0.0)
        return out

    def _plan_produccion(self, planes: list[dict[str, Any]], eventos_horizonte: list[dict[str, Any]], fecha_obj: date) -> dict[str, Any]:
        event_map = {str(e.get("id")): e for e in eventos_horizonte}
        tareas: list[dict[str, Any]] = []
        for plan in planes if isinstance(planes, list) else []:
            evento = event_map.get(str(plan.get("evento_id") or ""), {})
            for tarea in plan.get("tareas", []) or []:
                estado = str(tarea.get("estado_ejecucion") or "pendiente").lower()
                fases = list(tarea.get("fases") or [])
                total_activo = 0
                total_pasivo = 0
                descongelacion = 0
                tiene_fase_descongelacion = False
                for fase in fases:
                    dur = int(_to_float(fase.get("duracion_min"), 0))
                    tipo = str(fase.get("tipo") or "").lower()
                    if tipo in {"reposo", "fermentacion", "coccion", "coccion_lenta", "cocción_lenta", "enfriado", "abatido", "abatimiento", "descongelacion", "descongelación", "marinado", "espera"}:
                        total_pasivo += dur
                    else:
                        total_activo += dur
                    if tipo in {"descongelacion", "descongelación", "descongelar"}:
                        tiene_fase_descongelacion = True
                        descongelacion += dur

                dias_evento = evento.get("dias") if isinstance(evento.get("dias"), int) else None
                debe_hoy = bool(dias_evento == 0 and (total_pasivo >= 180 or descongelacion > 0))
                puede_manana = bool(dias_evento == 0 and not debe_hoy)
                bloqueada = bool(str(tarea.get("bloqueo") or "").strip())
                dep_recepcion = bool("recepcion" in str(tarea.get("bloqueo") or "").lower())
                dep_descongel = tiene_fase_descongelacion and estado not in {"finalizada", "completada"}
                tarea_id = _stable_id("RPTASK", plan.get("id"), tarea.get("id"), fecha_obj.isoformat())
                tareas.append({
                    "id": tarea_id,
                    "origen_tarea_id": str(tarea.get("id") or ""),
                    "plan_id": str(plan.get("id") or ""),
                    "titulo": str(tarea.get("titulo") or "Tarea"),
                    "estado": estado,
                    "evento_id": str(evento.get("id") or ""),
                    "evento": str(evento.get("nombre") or plan.get("evento") or ""),
                    "fecha_objetivo": fecha_obj.isoformat(),
                    "produccion_terminada": estado in {"finalizada", "completada"},
                    "produccion_pendiente": estado not in {"finalizada", "completada", "cancelada"},
                    "debe_empezar_hoy": debe_hoy,
                    "puede_hacerse_manana": puede_manana,
                    "bloqueada": bloqueada,
                    "dependiente_recepcion": dep_recepcion,
                    "dependiente_descongelacion": dep_descongel,
                    "duracion_activa_min": total_activo,
                    "duracion_pasiva_min": total_pasivo,
                    "descongelacion_min": descongelacion,
                    "recurso": self._primero_no_vacio([f.get("recurso") for f in fases]),
                    "responsable": self._primero_no_vacio([f.get("responsable") for f in fases]),
                    "prioridad": int(tarea.get("prioridad") or 50),
                    "decision": "pendiente",
                })
        tareas.sort(key=lambda x: (not x.get("debe_empezar_hoy"), x.get("bloqueada"), -int(x.get("prioridad") or 0), x.get("titulo")))
        return {"tareas": self._dedupe_by_id(tareas)}

    def _plan_descongelaciones(self, tareas: list[dict[str, Any]], fecha_obj: date) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for t in tareas:
            if not t.get("dependiente_descongelacion"):
                continue
            mins = int(t.get("descongelacion_min") or 0)
            limite = datetime.combine(fecha_obj, datetime.min.time()).replace(hour=9, minute=0)
            if mins > 0:
                limite = limite - timedelta(minutes=mins)
            item_id = _stable_id("DESCONG", t.get("origen_tarea_id"), t.get("evento_id"), fecha_obj.isoformat())
            out.append({
                "id": item_id,
                "producto": t.get("titulo"),
                "cantidad": t.get("cantidad") or 1,
                "unidad": t.get("unidad") or "ud",
                "evento": t.get("evento"),
                "receta": t.get("titulo"),
                "momento_limite": limite.isoformat(timespec="minutes"),
                "duracion_estimada_min": mins,
                "ubicacion": "camara_fria",
                "estado": "revision_manual" if mins <= 0 else "pendiente",
                "motivo": "Requerida por planificación de producción",
                "ya_confirmada": False,
                "decision": "pendiente",
            })
        return self._dedupe_by_id(out)

    def _plan_compras(
        self,
        eventos_horizonte: list[dict[str, Any]],
        menus: list[dict[str, Any]],
        stock_map: dict[str, float],
        pedidos: list[dict[str, Any]],
        fecha_obj: date,
    ) -> dict[str, Any]:
        lineas: list[dict[str, Any]] = []
        abiertos = [p for p in pedidos if str(p.get("estado") or "").lower() not in {"recibido", "cancelado", "cerrado"}]
        menu = menus[0] if isinstance(menus, list) and menus else {}
        for evento in eventos_horizonte:
            entrada_evento = {
                "id_evento": evento.get("id"),
                "nombre": evento.get("nombre"),
                "personas": evento.get("pax"),
                "menus": [menu] if menu else [],
            }
            necesidades = calcular_necesidades_evento(entrada_evento, menu=menu if menu else None)
            comparadas = comparar_con_stock(necesidades, stock=stock_map)
            for nec in comparadas:
                faltante = _to_float(nec.get("cantidad_a_comprar"), 0.0)
                if faltante <= 0:
                    continue
                articulo = str(nec.get("articulo") or "").strip()
                cobertura = self._cobertura_por_pedidos(abiertos, articulo)
                uncovered = max(0.0, faltante - cobertura.get("cantidad_cubierta", 0.0))
                line_id = _stable_id("RPCOMP", evento.get("id"), articulo, evento.get("fecha"))
                lineas.append({
                    "id": line_id,
                    "evento_id": evento.get("id"),
                    "evento": evento.get("nombre"),
                    "dia": int(evento.get("dias") or 0),
                    "articulo": articulo,
                    "unidad": nec.get("unidad") or "ud",
                    "cantidad_faltante": round(faltante, 3),
                    "cantidad_cubierta_pedidos_abiertos": round(cobertura.get("cantidad_cubierta", 0.0), 3),
                    "cantidad_sin_cubrir": round(uncovered, 3),
                    "proveedor_sugerido": nec.get("proveedor_preferente") or cobertura.get("proveedor") or "Sin proveedor",
                    "fecha_limite_pedido": (fecha_obj if int(evento.get("dias") or 0) == 0 else fecha_obj + timedelta(days=max(0, int(evento.get("dias") or 0) - 1))).isoformat(),
                    "recepcion_prevista": cobertura.get("recepcion_prevista") or "sin_confirmar",
                    "linea_bloqueada": bool(not articulo),
                    "motivo_bloqueo": "Artículo sin nombre" if not articulo else "",
                    "estado": "cubierta" if uncovered <= 0 else "pendiente",
                    "urgente": int(evento.get("dias") or 0) == 0 and uncovered > 0,
                    "decision": "pendiente",
                })
        lineas = self._dedupe_by_id(lineas)
        return {
            "lineas": lineas,
            "total": len(lineas),
            "sin_cubrir": len([l for l in lineas if _to_float(l.get("cantidad_sin_cubrir"), 0.0) > 0]),
        }

    def _plan_recepciones(self, pedidos: list[dict[str, Any]], compras_lineas: list[dict[str, Any]], fecha_obj: date) -> list[dict[str, Any]]:
        dependencias = {}
        for c in compras_lineas:
            if _to_float(c.get("cantidad_sin_cubrir"), 0.0) <= 0:
                continue
            dependencias.setdefault(str(c.get("articulo") or "").lower(), []).append(str(c.get("evento") or ""))

        out: list[dict[str, Any]] = []
        for pedido in pedidos if isinstance(pedidos, list) else []:
            estado = str(pedido.get("estado") or "").lower()
            if estado in {"recibido", "cancelado", "cerrado"}:
                continue
            entrega_prevista = str(pedido.get("entrega_prevista") or "")
            fecha_prev = str(entrega_prevista or pedido.get("enviado_en") or pedido.get("creado_en") or "")
            fecha_simple = fecha_prev[:10] if fecha_prev else ""
            hora_prev = fecha_prev[11:16] if len(fecha_prev) >= 16 else ""
            no_hora = not bool(hora_prev)
            sin_confirmacion = not bool(entrega_prevista)
            riesgo_retraso = False
            if fecha_simple:
                d = self._parse_fecha(fecha_simple)
                riesgo_retraso = bool(d and d > fecha_obj)
            lines = pedido.get("lineas") or []
            criticos: list[str] = []
            for l in lines:
                nombre = str(l.get("nombre") or l.get("articulo") or "").lower()
                criticos.extend(dependencias.get(nombre, []))
            rec_id = _stable_id("RECPREV", pedido.get("id"), fecha_simple or "sin_fecha")
            out.append({
                "id": rec_id,
                "proveedor": pedido.get("proveedor") or "",
                "pedido_id": pedido.get("id") or "",
                "fecha_prevista": fecha_simple or "sin_fecha",
                "hora_prevista": hora_prev or "no_confirmada",
                "hora_confirmada": (not no_hora) and (not sin_confirmacion),
                "productos_criticos": sorted(set(criticos)),
                "tareas_bloqueadas_hasta_recepcion": len(set(criticos)),
                "riesgo_retraso": riesgo_retraso,
                "datos_incompletos": (not bool(fecha_simple)) or sin_confirmacion,
            })
        out.sort(key=lambda x: (x.get("fecha_prevista") or "9999-12-31", x.get("hora_prevista") or "23:59"))
        return out

    def _plan_personal(self, eventos_manana: list[dict[str, Any]], menus: list[dict[str, Any]], personal_turnos: list[dict[str, Any]]) -> dict[str, Any]:
        menu = menus[0] if isinstance(menus, list) and menus else None
        if personal_turnos:
            disponibles = []
            for p in personal_turnos:
                disponibles.append({
                    "id": str(p.get("id") or _stable_id("PER", p.get("nombre"), p.get("turno"))),
                    "nombre": str(p.get("nombre") or "puesto"),
                    "turno": str(p.get("turno") or "sin_turno"),
                    "horas": str(p.get("horas") or ""),
                    "area": str(p.get("area") or p.get("capacidad") or "general"),
                    "carga": _to_float(p.get("carga"), 0.0),
                })
            return {
                "modo": "datos_reales",
                "disponibles": disponibles,
                "asignacion": self._asignar_personal_generico(eventos_manana, disponibles),
                "revision_manual": False,
            }

        estimado = []
        for evt in eventos_manana:
            plan = calcular_personal_evento(
                {"id_evento": evt.get("id"), "personas": evt.get("pax"), "tipo": evt.get("nombre")},
                menu=menu,
                tipo_servicio="catering",
                complejidad="media",
            )
            estimado.append({
                "evento": evt.get("nombre"),
                "roles": plan.get("personal", {}) if plan.get("ok") else {},
                "total": int(plan.get("total_personas_equipo") or 0),
            })
        return {
            "modo": "asignacion_generica",
            "disponibles": [],
            "asignacion": estimado,
            "revision_manual": True,
            "warning": "No existe fuente de personal/turnos. Se propone asignación genérica por puesto.",
        }

    def _plan_alergenos(self, eventos_horizonte: list[dict[str, Any]], articulos: list[dict[str, Any]]) -> dict[str, Any]:
        relevantes = []
        for evt in eventos_horizonte:
            obs = str(evt.get("observaciones") or "")
            if "alerg" in obs.lower():
                relevantes.append({"evento": evt.get("nombre"), "detalle": obs})
        catalogo = [a for a in articulos if a.get("alergenos")]
        return {
            "eventos": relevantes,
            "catalogo_con_alergenos": len(catalogo),
            "catalogo_incompleto": len(catalogo) == 0,
        }

    def _plan_caducidades(self, stock_lotes: list[dict[str, Any]], fecha_obj: date) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        lim = fecha_obj + timedelta(days=2)
        for lote in stock_lotes if isinstance(stock_lotes, list) else []:
            cad = self._parse_fecha(lote.get("caducidad"))
            if not cad:
                continue
            if cad <= lim:
                out.append({
                    "lote_id": lote.get("id") or "",
                    "producto": lote.get("nombre") or "",
                    "caducidad": cad.isoformat(),
                    "dias": (cad - fecha_obj).days,
                    "cantidad": _to_float(lote.get("cantidad"), 0.0),
                })
        out.sort(key=lambda x: x.get("caducidad") or "9999-12-31")
        return out

    def _plan_cronologia(
        self,
        eventos_manana: list[dict[str, Any]],
        tareas: list[dict[str, Any]],
        recepciones: list[dict[str, Any]],
        personal: dict[str, Any],
    ) -> list[dict[str, Any]]:
        agenda: list[dict[str, Any]] = [
            {"id": _stable_id("CRONO", "apertura", "09:30"), "hora": "09:30", "titulo": "Apertura y briefing", "tipo": "briefing", "responsable": "jefe_cocina", "recurso": "sala"},
        ]

        for t in tareas:
            if str(t.get("estado") or "").lower() in {"finalizada", "completada", "cancelada"}:
                continue
            base = "09:35" if t.get("debe_empezar_hoy") else "10:00"
            agenda.append({
                "id": _stable_id("CRONO", t.get("id"), base),
                "hora": base,
                "titulo": str(t.get("titulo") or "Tarea"),
                "tipo": "produccion",
                "responsable": t.get("responsable") or "cocina",
                "recurso": t.get("recurso") or "general",
                "duracion_activa_min": int(t.get("duracion_activa_min") or 0),
                "duracion_pasiva_min": int(t.get("duracion_pasiva_min") or 0),
            })

        for r in recepciones:
            hora = str(r.get("hora_prevista") or "no_confirmada")
            agenda.append({
                "id": _stable_id("CRONO", r.get("id"), "recepcion"),
                "hora": hora if hora != "no_confirmada" else "10:00",
                "titulo": f"Recepción {r.get('proveedor')}",
                "tipo": "recepcion",
                "responsable": "almacen",
                "recurso": "muelle",
                "hora_no_confirmada": hora == "no_confirmada",
            })

        agenda.sort(key=lambda x: x.get("hora") or "23:59")
        agenda = self._dedupe_by_id(agenda)
        self._marcar_sobrecarga(agenda, personal)
        return agenda

    def _plan_alertas_bloqueos(
        self,
        *,
        produccion: dict[str, Any],
        descongelaciones: list[dict[str, Any]],
        compras: dict[str, Any],
        recepciones: list[dict[str, Any]],
        personal: dict[str, Any],
        alergenos: dict[str, Any],
        caducidades: list[dict[str, Any]],
        incidencias_ext: list[dict[str, Any]],
        eventos_manana: list[dict[str, Any],
        ],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        alertas: list[dict[str, Any]] = []
        bloqueos: list[dict[str, Any]] = []

        tareas = produccion.get("tareas") or []
        for t in tareas:
            if t.get("bloqueada"):
                bloqueos.append({
                    "id": _stable_id("BLOQ", t.get("id"), "produccion"),
                    "tipo": "produccion_bloqueada",
                    "detalle": f"Producción bloqueada: {t.get('titulo')}",
                })
        if not eventos_manana:
            alertas.append({"id": _stable_id("ALT", "sin_eventos"), "tipo": "sin_eventos", "nivel": "bajo", "detalle": "No hay eventos mañana."})
        if personal.get("revision_manual"):
            alertas.append({"id": _stable_id("ALT", "personal"), "tipo": "personal_insuficiente", "nivel": "alto", "detalle": personal.get("warning") or "Personal sin confirmar."})
            if eventos_manana:
                bloqueos.append({
                    "id": _stable_id("BLOQ", "personal", len(eventos_manana)),
                    "tipo": "personal_no_confirmado",
                    "detalle": "Hay eventos mañana sin base de turnos confirmada.",
                })

        for d in descongelaciones:
            if int(d.get("duracion_estimada_min") or 0) <= 0:
                alertas.append({"id": _stable_id("ALT", d.get("id"), "descong"), "tipo": "descongelacion_tiempo_desconocido", "nivel": "medio", "detalle": f"Descongelación sin tiempo definido: {d.get('producto')}"})

        for l in compras.get("lineas", []):
            if l.get("linea_bloqueada"):
                bloqueos.append({"id": _stable_id("BLOQ", l.get("id"), "compra"), "tipo": "linea_compra_bloqueada", "detalle": l.get("motivo_bloqueo") or "Línea de compra bloqueada."})
            if l.get("urgente") and _to_float(l.get("cantidad_sin_cubrir"), 0.0) > 0:
                alertas.append({"id": _stable_id("ALT", l.get("id"), "compra"), "tipo": "pedido_no_confirmado", "nivel": "alto", "detalle": f"Compra urgente pendiente: {l.get('articulo')}"})

        for r in recepciones:
            if r.get("riesgo_retraso"):
                alertas.append({"id": _stable_id("ALT", r.get("id"), "recepcion"), "tipo": "recepcion_tardia", "nivel": "alto", "detalle": f"Riesgo de retraso en recepción {r.get('pedido_id')}"})
            if r.get("datos_incompletos"):
                alertas.append({"id": _stable_id("ALT", r.get("id"), "recepcion_datos"), "tipo": "recepcion_datos_incompletos", "nivel": "medio", "detalle": f"Recepción sin fecha/hora confirmada: {r.get('pedido_id')}"})

        if alergenos.get("catalogo_incompleto"):
            alertas.append({"id": _stable_id("ALT", "alergenos"), "tipo": "catalogo_alergenos_incompleto", "nivel": "medio", "detalle": "Catálogo de alérgenos incompleto."})
        for x in alergenos.get("eventos", []):
            alertas.append({"id": _stable_id("ALT", x.get("evento"), "alergeno"), "tipo": "alergeno_registrado", "nivel": "alto", "detalle": f"{x.get('evento')}: {x.get('detalle')}"})

        for c in caducidades:
            if int(c.get("dias") or 0) <= 1:
                alertas.append({"id": _stable_id("ALT", c.get("lote_id"), "caducidad"), "tipo": "producto_proximo_caducar", "nivel": "medio", "detalle": f"{c.get('producto')} caduca el {c.get('caducidad')}"})

        for inc in incidencias_ext if isinstance(incidencias_ext, list) else []:
            alertas.append({"id": _stable_id("ALT", inc.get("id") or inc.get("titulo"), "inc"), "tipo": "incidencia_abierta", "nivel": "alto", "detalle": str(inc.get("detalle") or inc.get("titulo") or "Incidencia abierta")})

        return self._dedupe_by_id(alertas), self._dedupe_by_id(bloqueos)

    # ------------------------------------------------------------------
    # Decisiones humanas e idempotencia
    # ------------------------------------------------------------------
    def _preservar_decisiones(self, previo: dict[str, Any], nuevo: dict[str, Any]) -> dict[str, Any]:
        out = deepcopy(nuevo)
        for key in ["tareas", "descongelaciones", "cronologia", "recepciones"]:
            out[key] = self._merge_decisions_list(previo.get(key, []), out.get(key, []))
        out["compras"]["lineas"] = self._merge_decisions_list(
            (previo.get("compras") or {}).get("lineas", []),
            (out.get("compras") or {}).get("lineas", []),
        )
        out["regenerado_desde"] = {
            "plan_id": previo.get("id"),
            "fingerprint_anterior": previo.get("fingerprint_entradas"),
        }
        return out

    @staticmethod
    def _merge_decisions_list(prev: list[dict[str, Any]], new: list[dict[str, Any]]) -> list[dict[str, Any]]:
        prev_map = {str(x.get("id")): x for x in prev if x.get("id")}
        out = []
        for item in new:
            old = prev_map.get(str(item.get("id")))
            merged = dict(item)
            if old:
                for field in ["decision", "prioridad", "responsable", "estado"]:
                    if old.get(field) not in (None, "") and field in merged:
                        merged[field] = old.get(field)
                if old.get("ejecutada"):
                    merged["ejecutada"] = True
            out.append(merged)
        return out

    def _aplicar_decision(self, plan: dict[str, Any], decision: dict[str, Any]) -> None:
        target = str(decision.get("target") or "").lower()
        item_id = str(decision.get("id") or "")
        action = str(decision.get("action") or "").lower()
        value = decision.get("value")

        listas = []
        if target == "compras":
            listas.append((plan.get("compras") or {}).get("lineas", []))
        elif target in {"tareas", "descongelaciones", "cronologia", "recepciones"}:
            listas.append(plan.get(target, []))

        for lst in listas:
            for item in lst:
                if str(item.get("id")) != item_id:
                    continue
                if action == "confirmar":
                    item["decision"] = "confirmada"
                elif action == "excluir":
                    item["decision"] = "excluida"
                    if isinstance(value, str) and value.strip():
                        item["motivo_exclusion"] = value.strip()
                elif action == "urgente":
                    item["urgente"] = True
                elif action == "aplazar":
                    item["decision"] = "aplazada"
                    item["aplazada_a"] = str(value or "")
                elif action == "prioridad":
                    item["prioridad"] = int(_to_float(value, item.get("prioridad") or 50))
                elif action == "reasignar":
                    item["responsable"] = str(value or item.get("responsable") or "")
                elif action == "adelantar":
                    item["decision"] = "adelantada"
                    item["adelantada_a"] = str(value or "")
                elif action == "bloqueo_revisado":
                    item["bloqueo_revisado"] = True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _clasificar_acciones_hoy(self, produccion: dict[str, Any], compras: dict[str, Any], descongelaciones: list[dict[str, Any]]) -> dict[str, Any]:
        obligatorias = [
            {"tipo": "produccion", "titulo": t.get("titulo"), "id": t.get("id")}
            for t in produccion.get("tareas", [])
            if t.get("debe_empezar_hoy") and not t.get("produccion_terminada")
        ]
        obligatorias.extend([
            {"tipo": "compra", "titulo": c.get("articulo"), "id": c.get("id")}
            for c in (compras.get("lineas") or [])
            if c.get("urgente") and _to_float(c.get("cantidad_sin_cubrir"), 0.0) > 0
        ])
        recomendadas = [
            {"tipo": "descongelacion", "titulo": d.get("producto"), "id": d.get("id")}
            for d in descongelaciones if not d.get("ya_confirmada")
        ]
        pueden_esperar = [
            {"tipo": "compra", "titulo": c.get("articulo"), "id": c.get("id")}
            for c in (compras.get("lineas") or [])
            if int(c.get("dia") or 0) > 0
        ]
        return {
            "obligatorias_hoy": self._dedupe_by_id(obligatorias),
            "recomendadas_hoy": self._dedupe_by_id(recomendadas),
            "pueden_esperar": self._dedupe_by_id(pueden_esperar),
        }

    def _warnings_fuentes(self, personal_turnos: list[dict[str, Any]]) -> list[str]:
        warns = []
        if not personal_turnos:
            warns.append("Fuente de personal/turnos no disponible: se usa asignación genérica.")
        if not (self.db_dir / "incidencias_abiertas.json").exists():
            warns.append("No existe incidencias_abiertas.json: alertas de incidencias externas limitadas.")
        return warns

    @staticmethod
    def _asignar_personal_generico(eventos: list[dict[str, Any]], disponibles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not disponibles:
            return []
        asignacion = []
        for idx, evento in enumerate(eventos):
            persona = disponibles[idx % len(disponibles)]
            asignacion.append({
                "evento": evento.get("nombre"),
                "responsable": persona.get("nombre"),
                "turno": persona.get("turno"),
                "area": persona.get("area"),
            })
        return asignacion

    @staticmethod
    def _primero_no_vacio(values: list[Any]) -> str:
        for v in values:
            txt = str(v or "").strip()
            if txt:
                return txt
        return ""

    @staticmethod
    def _mark_key(item: dict[str, Any]) -> str:
        return str(item.get("id") or "")

    def _dedupe_by_id(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        out = []
        for it in items:
            key = self._mark_key(it)
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(it)
        return out

    def _marcar_sobrecarga(self, agenda: list[dict[str, Any]], personal: dict[str, Any]) -> None:
        activos = [a for a in agenda if a.get("tipo") in {"produccion", "recepcion"}]
        capacidad = len(personal.get("disponibles") or [])
        if personal.get("revision_manual"):
            capacidad = 1
        if capacidad <= 0:
            capacidad = 1
        if len(activos) > capacidad * 8:
            agenda.append({
                "id": _stable_id("CRONO", "sobrecarga", len(activos)),
                "hora": "17:30",
                "titulo": "Sobrecarga detectada: mover tareas a jornada posterior",
                "tipo": "alerta",
                "responsable": "jefe_cocina",
                "recurso": "planificacion",
            })

    def _count_tareas_abiertas(self, planes: list[dict[str, Any]]) -> int:
        abiertas = 0
        for p in planes if isinstance(planes, list) else []:
            for t in p.get("tareas", []) or []:
                if str(t.get("estado_ejecucion") or "pendiente").lower() not in {"finalizada", "completada", "cancelada"}:
                    abiertas += 1
        return abiertas

    def _collect_incidencias_produccion(self, planes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for p in planes if isinstance(planes, list) else []:
            for t in p.get("tareas", []) or []:
                for inc in t.get("incidencias") or []:
                    out.append({
                        "plan_id": p.get("id"),
                        "tarea_id": t.get("id"),
                        "titulo": t.get("titulo"),
                        "detalle": inc.get("descripcion") or inc.get("detalle") or "incidencia",
                    })
                if str(t.get("bloqueo") or "").strip():
                    out.append({
                        "plan_id": p.get("id"),
                        "tarea_id": t.get("id"),
                        "titulo": t.get("titulo"),
                        "detalle": str(t.get("bloqueo")),
                    })
        return out

    def _cobertura_por_pedidos(self, pedidos_abiertos: list[dict[str, Any]], articulo: str) -> dict[str, Any]:
        articulo_n = str(articulo or "").strip().lower()
        cub = 0.0
        proveedor = ""
        recep = ""
        for p in pedidos_abiertos:
            for line in p.get("lineas", []) or []:
                nombre = str(line.get("nombre") or line.get("articulo") or "").strip().lower()
                if nombre != articulo_n:
                    continue
                cub += _to_float(line.get("cantidad"), 0.0)
                proveedor = proveedor or str(p.get("proveedor") or "")
                recep = recep or str(p.get("entrega_prevista") or p.get("enviado_en") or p.get("creado_en") or "")
        return {
            "cantidad_cubierta": cub,
            "proveedor": proveedor,
            "recepcion_prevista": (recep[:10] if recep else ""),
        }

    @staticmethod
    def _safe_dump(value: Any) -> Any:
        try:
            json.dumps(value, ensure_ascii=False, sort_keys=True)
            return value
        except TypeError:
            return str(value)

    def _latest_propuesta(self, plan_id: str) -> dict[str, Any] | None:
        props = [p for p in self._load_json(self.path_propuestas, []) if str(p.get("id")) == str(plan_id)]
        if not props:
            return None
        props.sort(key=lambda x: str(x.get("generado_en") or ""), reverse=True)
        return props[0]

    def _latest_confirmado(self, plan_id: str) -> dict[str, Any] | None:
        confs = [p for p in self._load_json(self.path_confirmados, []) if str(p.get("id")) == str(plan_id)]
        if not confs:
            return None
        confs.sort(key=lambda x: str(x.get("confirmado_en") or x.get("generado_en") or ""), reverse=True)
        return confs[0]

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

    @staticmethod
    def _parse_fecha(value: Any) -> date | None:
        text = str(value or "").strip()
        if not text:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None


def formatear_diagnostico_rp4(d: dict[str, Any]) -> str:
    return "\n".join([
        "RP-4 — PREPARAR MAÑANA 1.0",
        "=" * 78,
        f"Diagnóstico: {d.get('diagnostico')} | Fecha objetivo: {d.get('fecha_objetivo')}",
        f"Tareas: {d.get('tareas', 0)} | Compras: {d.get('compras', 0)} | Descongelaciones: {d.get('descongelaciones', 0)}",
        f"Alertas: {d.get('alertas', 0)} | Bloqueos: {d.get('bloqueos', 0)}",
        f"Modo: {'Solo propuesta' if d.get('solo_propuesta') else 'Operativo'}",
    ])


__all__ = ["CierreOperativoRP4", "formatear_diagnostico_rp4"]
