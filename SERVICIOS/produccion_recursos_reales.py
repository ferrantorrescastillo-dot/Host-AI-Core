from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from SERVICIOS.configuracion_restaurante import ServicioConfiguracionRestaurante
from SERVICIOS.recursos_restaurante import ServicioRecursosRestaurante


ESTADOS_DIAGNOSTICO = {
    "sin_requisitos",
    "disponible",
    "disponible_con_avisos",
    "recursos_insuficientes",
    "configuracion_invalida",
}


@dataclass(frozen=True)
class IntervaloTarea:
    tarea_id: str
    inicio_min: int
    fin_min: int


class ServicioProduccionRecursosReales:
    """Diagnostica y valida recursos reales para tareas y planes de produccion."""

    VERSION = "R3"

    def __init__(self, base_dir: Any):
        self.base_dir = base_dir
        self.srv_r1 = ServicioConfiguracionRestaurante(base_dir)
        self.srv_r2 = ServicioRecursosRestaurante(base_dir)

    def normalizar_requisitos_recursos(self, requisitos: dict[str, Any] | None) -> dict[str, Any]:
        raw = dict(requisitos or {})
        equip = self._normalizar_lista_ids(raw.get("equipamiento_ids") or [])
        personas = raw.get("personas_necesarias", 0)
        try:
            personas_necesarias = int(personas)
        except (TypeError, ValueError):
            personas_necesarias = -1

        duracion = raw.get("duracion_minutos")
        duracion_out: int | None
        if duracion in (None, ""):
            duracion_out = None
        else:
            try:
                duracion_out = int(duracion)
            except (TypeError, ValueError):
                duracion_out = -1

        partida_id = str(raw.get("partida_id") or "").strip().lower()
        turno_id = str(raw.get("turno_id") or "").strip().lower()

        out = {
            "partida_id": partida_id,
            "equipamiento_ids": equip,
            "personas_necesarias": personas_necesarias,
            "turno_id": turno_id,
            "duracion_minutos": duracion_out,
        }
        return out

    def normalizar_recursos_asignados(self, asignados: dict[str, Any] | None) -> dict[str, Any]:
        raw = dict(asignados or {})
        return {
            "persona_ids": self._normalizar_lista_ids(raw.get("persona_ids") or []),
            "equipamiento_ids": self._normalizar_lista_ids(raw.get("equipamiento_ids") or []),
            "partida_id": str(raw.get("partida_id") or "").strip().lower(),
            "turno_id": str(raw.get("turno_id") or "").strip().lower(),
        }

    def validar_requisitos_recursos(self, tarea: dict[str, Any], contexto: dict[str, Any] | None = None) -> dict[str, Any]:
        req = self.normalizar_requisitos_recursos(tarea.get("requisitos_recursos") or {})
        if self._sin_requisitos(req):
            return {
                "ok": True,
                "bloqueante": False,
                "problemas": [],
                "avisos": [],
                "estado": "sin_requisitos",
                "requisitos": req,
            }

        ctx = contexto or self._cargar_contexto()
        problemas: list[str] = []
        avisos: list[str] = []

        partida_id = req.get("partida_id") or ""
        if partida_id:
            partida = ctx["partidas_por_id"].get(partida_id)
            if not partida:
                problemas.append(f"Partida requerida inexistente: {partida_id}")
            elif not bool(partida.get("activa", True)):
                problemas.append(f"Partida inactiva: {partida_id}")

        equip_ids = list(req.get("equipamiento_ids") or [])
        if len(equip_ids) != len(set(equip_ids)):
            problemas.append("Equipamiento repetido en requisitos")
        for eq_id in equip_ids:
            equipo = ctx["equipamiento_por_id"].get(eq_id)
            if not equipo:
                problemas.append(f"Equipamiento inexistente: {eq_id}")
            elif not bool(equipo.get("activo", True)):
                problemas.append(f"Equipamiento inactivo: {eq_id}")

        personas_necesarias = int(req.get("personas_necesarias", -1) or -1)
        if personas_necesarias < 0:
            problemas.append("personas_necesarias debe ser un entero mayor o igual a 0")

        if req.get("duracion_minutos") is not None:
            dur = int(req.get("duracion_minutos", -1) or -1)
            if dur <= 0:
                problemas.append("duracion_minutos debe ser mayor que 0 cuando se indica")

        turno_id = req.get("turno_id") or ""
        if turno_id:
            turno = ctx["turnos_por_id"].get(turno_id)
            if not turno:
                problemas.append(f"Turno inexistente: {turno_id}")
            else:
                avisos.append("Disponibilidad individual por turnos no confirmada con datos actuales")

        capacidades = dict(ctx["capacidades"])
        cap_cocineros = int(capacidades.get("cocineros_simultaneos", 0) or 0)
        if personas_necesarias > 0 and cap_cocineros > 0 and personas_necesarias > cap_cocineros:
            problemas.append("La tarea supera cocineros_simultaneos configurados")

        if capacidades.get("produccion_maxima_turno") not in (None, ""):
            avisos.append("produccion_maxima_turno configurada pero no aplicable automaticamente en R3")

        estado = self._estado_desde_listas(problemas, avisos)
        return {
            "ok": len(problemas) == 0,
            "bloqueante": len(problemas) > 0,
            "problemas": problemas,
            "avisos": avisos,
            "estado": estado,
            "requisitos": req,
        }

    def obtener_personal_candidato(self, tarea: dict[str, Any], contexto: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        req = self.normalizar_requisitos_recursos(tarea.get("requisitos_recursos") or {})
        ctx = contexto or self._cargar_contexto()
        partida_id = str(req.get("partida_id") or "").strip().lower()

        out: list[dict[str, Any]] = []
        for p in list(ctx["personal"]):
            if not bool(p.get("activo", False)):
                continue
            rol_id = str(p.get("rol") or "").strip().lower()
            if rol_id not in ctx["roles_por_id"]:
                continue
            partidas = [str(x or "").strip().lower() for x in list(p.get("partidas") or [])]
            if partida_id and partida_id not in partidas:
                continue
            out.append(
                {
                    "id": str(p.get("id") or "").strip().lower(),
                    "nombre": str(p.get("nombre") or ""),
                    "rol_id": rol_id,
                    "rol_nombre": str((ctx["roles_por_id"].get(rol_id) or {}).get("nombre") or rol_id),
                    "partidas": partidas,
                }
            )

        vistos: set[str] = set()
        unicos: list[dict[str, Any]] = []
        for c in out:
            cid = c.get("id")
            if not cid or cid in vistos:
                continue
            vistos.add(cid)
            unicos.append(c)
        return unicos

    def validar_asignacion_recursos(
        self,
        plan: dict[str, Any],
        tarea: dict[str, Any],
        asignados: dict[str, Any],
        confirmar_exceso_personas: bool = False,
    ) -> dict[str, Any]:
        ctx = self._cargar_contexto()
        req_val = self.validar_requisitos_recursos(tarea, contexto=ctx)
        req = req_val["requisitos"]
        raw_asignados = dict(asignados or {})
        personas_raw = [str(x or "").strip().lower() for x in list(raw_asignados.get("persona_ids") or []) if str(x or "").strip()]
        equipos_raw = [str(x or "").strip().lower() for x in list(raw_asignados.get("equipamiento_ids") or []) if str(x or "").strip()]
        asi = self.normalizar_recursos_asignados(asignados)

        problemas: list[str] = []
        avisos: list[str] = []

        personas_ids = list(asi.get("persona_ids") or [])
        if len(personas_raw) != len(set(personas_raw)):
            problemas.append("No se puede asignar la misma persona dos veces")

        if len(equipos_raw) != len(set(equipos_raw)):
            problemas.append("No se puede asignar el mismo equipamiento dos veces")

        candidatos = {c["id"]: c for c in self.obtener_personal_candidato({"requisitos_recursos": req}, contexto=ctx)}
        for pid in personas_ids:
            if pid not in candidatos:
                problemas.append(f"Persona no compatible o inexistente: {pid}")

        personas_necesarias = int(req.get("personas_necesarias", 0) or 0)
        if personas_necesarias > 0 and len(personas_ids) > personas_necesarias and not confirmar_exceso_personas:
            problemas.append("Asignacion supera personas_necesarias sin confirmacion")

        for eq_id in list(asi.get("equipamiento_ids") or []):
            eq = ctx["equipamiento_por_id"].get(eq_id)
            if not eq:
                problemas.append(f"Equipamiento inexistente en asignacion: {eq_id}")
            elif not bool(eq.get("activo", True)):
                problemas.append(f"Equipamiento inactivo en asignacion: {eq_id}")

        tarea_temp = dict(tarea)
        tarea_temp["recursos_asignados"] = asi
        diag_tarea = self.diagnosticar_recursos_tarea(tarea_temp, contexto=ctx)
        if diag_tarea.get("bloqueante"):
            problemas.extend([p for p in diag_tarea.get("problemas", []) if p not in problemas])

        plan_temp = dict(plan)
        tareas_temp = []
        for t in list(plan_temp.get("tareas") or []):
            if str(t.get("id") or "") == str(tarea.get("id") or ""):
                t2 = dict(t)
                t2["recursos_asignados"] = asi
                tareas_temp.append(t2)
            else:
                tareas_temp.append(dict(t))
        plan_temp["tareas"] = tareas_temp
        conflictos = self.detectar_conflictos_recursos(plan_temp, contexto=ctx)
        if conflictos.get("bloqueante"):
            for c in conflictos.get("conflictos", []):
                texto = str(c.get("descripcion") or "").strip()
                if texto and texto not in problemas:
                    problemas.append(texto)

        estado = self._estado_desde_listas(problemas, avisos)
        return {
            "ok": len(problemas) == 0,
            "estado": estado,
            "bloqueante": len(problemas) > 0,
            "problemas": problemas,
            "avisos": avisos,
            "asignados": asi,
        }

    def diagnosticar_recursos_tarea(self, tarea: dict[str, Any], contexto: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = contexto or self._cargar_contexto()
        req_val = self.validar_requisitos_recursos(tarea, contexto=ctx)
        req = req_val["requisitos"]

        if req_val["estado"] == "sin_requisitos":
            return {
                "estado": "sin_requisitos",
                "bloqueante": False,
                "problemas": [],
                "avisos": [],
                "candidatos_personal": [],
                "equipamiento_disponible": [],
            }

        candidatos = self.obtener_personal_candidato({"requisitos_recursos": req}, contexto=ctx)
        equip_disp: list[str] = []
        for eq_id in list(req.get("equipamiento_ids") or []):
            eq = ctx["equipamiento_por_id"].get(eq_id)
            if eq and bool(eq.get("activo", True)):
                equip_disp.append(eq_id)

        problemas = list(req_val["problemas"])
        avisos = list(req_val["avisos"])

        personas_necesarias = int(req.get("personas_necesarias", 0) or 0)
        if personas_necesarias > 0 and len(candidatos) < personas_necesarias:
            problemas.append(
                f"Personal insuficiente: se necesitan {personas_necesarias} y hay {len(candidatos)} compatible(s)"
            )

        estado = self._estado_desde_listas(problemas, avisos)
        return {
            "estado": estado,
            "bloqueante": len(problemas) > 0,
            "problemas": problemas,
            "avisos": avisos,
            "candidatos_personal": [c["id"] for c in candidatos],
            "equipamiento_disponible": equip_disp,
        }

    def detectar_conflictos_recursos(self, plan: dict[str, Any], contexto: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = contexto or self._cargar_contexto()
        tareas = [dict(t) for t in list(plan.get("tareas") or []) if isinstance(t, dict)]

        intervalos: dict[str, IntervaloTarea] = {}
        avisos: list[str] = []
        for tarea in tareas:
            itv, aviso = self._intervalo_tarea(tarea)
            if aviso:
                avisos.append(aviso)
            if itv:
                intervalos[str(tarea.get("id") or "")] = itv

        conflictos: list[dict[str, Any]] = []

        # Conflicto de equipamiento por solapamiento.
        for i in range(len(tareas)):
            for j in range(i + 1, len(tareas)):
                ta = tareas[i]
                tb = tareas[j]
                ida = str(ta.get("id") or "")
                idb = str(tb.get("id") or "")
                ia = intervalos.get(ida)
                ib = intervalos.get(idb)
                if not ia or not ib:
                    continue
                if not self._solapan(ia.inicio_min, ia.fin_min, ib.inicio_min, ib.fin_min):
                    continue

                eq_a = set(self._equipos_tarea(ta))
                eq_b = set(self._equipos_tarea(tb))
                for eq_id in sorted(eq_a & eq_b):
                    conflictos.append(
                        {
                            "tipo": "equipamiento",
                            "bloqueante": True,
                            "tareas": [ida, idb],
                            "recurso_id": eq_id,
                            "descripcion": f"Conflicto de equipamiento {eq_id} entre tareas {ida} y {idb}",
                        }
                    )

                personas_a = set(self._personas_asignadas_tarea(ta))
                personas_b = set(self._personas_asignadas_tarea(tb))
                for pid in sorted(personas_a & personas_b):
                    conflictos.append(
                        {
                            "tipo": "personal",
                            "bloqueante": True,
                            "tareas": [ida, idb],
                            "recurso_id": pid,
                            "descripcion": f"Conflicto de personal {pid} entre tareas {ida} y {idb}",
                        }
                    )

        # Capacidad simultanea de elaboraciones/personas.
        tramos = self._tramos_temporales(intervalos)
        cap_elab = int((ctx["capacidades"] or {}).get("elaboraciones_simultaneas", 0) or 0)
        cap_coc = int((ctx["capacidades"] or {}).get("cocineros_simultaneos", 0) or 0)

        for a, b in tramos:
            activas = [tid for tid, itv in intervalos.items() if self._solapan(itv.inicio_min, itv.fin_min, a, b)]
            if cap_elab > 0 and len(activas) > cap_elab:
                conflictos.append(
                    {
                        "tipo": "capacidad_elaboraciones",
                        "bloqueante": True,
                        "tareas": activas,
                        "descripcion": f"Capacidad de elaboraciones simultaneas superada ({len(activas)} > {cap_elab})",
                    }
                )

            demanda_personas = 0
            for t in tareas:
                tid = str(t.get("id") or "")
                if tid not in activas:
                    continue
                req = self.normalizar_requisitos_recursos(t.get("requisitos_recursos") or {})
                n = int(req.get("personas_necesarias", 0) or 0)
                demanda_personas += max(0, n)
            if cap_coc > 0 and demanda_personas > cap_coc:
                conflictos.append(
                    {
                        "tipo": "capacidad_personas",
                        "bloqueante": True,
                        "tareas": activas,
                        "descripcion": f"Capacidad de cocineros simultaneos superada ({demanda_personas} > {cap_coc})",
                    }
                )

        return {
            "bloqueante": any(bool(c.get("bloqueante")) for c in conflictos),
            "conflictos": conflictos,
            "avisos": avisos,
        }

    def diagnosticar_recursos_plan(self, plan: dict[str, Any], contexto: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = contexto or self._cargar_contexto()
        tareas = [dict(t) for t in list(plan.get("tareas") or []) if isinstance(t, dict)]

        diagnosticos: dict[str, dict[str, Any]] = {}
        for tarea in tareas:
            tid = str(tarea.get("id") or "")
            diagnosticos[tid] = self.diagnosticar_recursos_tarea(tarea, contexto=ctx)

        conflictos = self.detectar_conflictos_recursos(plan, contexto=ctx)
        conflicto_por_tarea: dict[str, list[str]] = defaultdict(list)
        for c in conflictos.get("conflictos", []):
            for tid in list(c.get("tareas") or []):
                conflicto_por_tarea[str(tid)].append(str(c.get("descripcion") or ""))

        resumen = {
            "tareas_totales": len(tareas),
            "sin_requisitos": 0,
            "disponibles": 0,
            "con_avisos": 0,
            "bloqueadas": 0,
        }
        for tarea in tareas:
            tid = str(tarea.get("id") or "")
            diag = dict(diagnosticos.get(tid) or {})
            if conflicto_por_tarea.get(tid):
                for cdesc in conflicto_por_tarea[tid]:
                    if cdesc and cdesc not in diag.setdefault("problemas", []):
                        diag["problemas"].append(cdesc)
                diag["bloqueante"] = True
                diag["estado"] = "recursos_insuficientes"
            diagnosticos[tid] = diag

            estado = str(diag.get("estado") or "sin_requisitos")
            if estado == "sin_requisitos":
                resumen["sin_requisitos"] += 1
            elif bool(diag.get("bloqueante")):
                resumen["bloqueadas"] += 1
            elif estado == "disponible_con_avisos":
                resumen["con_avisos"] += 1
            else:
                resumen["disponibles"] += 1

        problemas_bloqueantes = []
        for tarea in tareas:
            tid = str(tarea.get("id") or "")
            if not bool((diagnosticos.get(tid) or {}).get("bloqueante")):
                continue
            titulo = str(tarea.get("titulo") or tid)
            for p in list((diagnosticos.get(tid) or {}).get("problemas") or []):
                problemas_bloqueantes.append({"tarea_id": tid, "tarea": titulo, "problema": p})

        avisos = list(conflictos.get("avisos") or [])
        for tid, diag in diagnosticos.items():
            for a in list(diag.get("avisos") or []):
                if a not in avisos:
                    avisos.append(a)

        return {
            "resumen": resumen,
            "diagnostico_tareas": diagnosticos,
            "problemas_bloqueantes": problemas_bloqueantes,
            "avisos": avisos,
            "conflictos": list(conflictos.get("conflictos") or []),
        }

    @staticmethod
    def _normalizar_lista_ids(values: list[Any]) -> list[str]:
        out: list[str] = []
        vistos: set[str] = set()
        for value in values:
            v = str(value or "").strip().lower()
            if not v or v in vistos:
                continue
            vistos.add(v)
            out.append(v)
        return out

    @staticmethod
    def _sin_requisitos(req: dict[str, Any]) -> bool:
        return (
            not str(req.get("partida_id") or "").strip()
            and not list(req.get("equipamiento_ids") or [])
            and int(req.get("personas_necesarias", 0) or 0) == 0
            and not str(req.get("turno_id") or "").strip()
            and req.get("duracion_minutos") in (None, "")
        )

    @staticmethod
    def _estado_desde_listas(problemas: list[str], avisos: list[str]) -> str:
        if problemas:
            if any("inexistente" in p or "inval" in p or "configur" in p for p in problemas):
                return "configuracion_invalida"
            return "recursos_insuficientes"
        if avisos:
            return "disponible_con_avisos"
        return "disponible"

    def _cargar_contexto(self) -> dict[str, Any]:
        cfg_r1 = self.srv_r1.obtener_configuracion()
        cfg_r2 = self.srv_r2.obtener_configuracion()

        partidas = list(cfg_r1.get("partidas") or [])
        equipamiento = list(cfg_r1.get("equipamiento") or [])
        roles = list(cfg_r2.get("roles") or [])
        turnos = list(cfg_r2.get("turnos") or [])
        personal = list(cfg_r2.get("personal") or [])

        return {
            "partidas": partidas,
            "partidas_por_id": {str(x.get("id") or "").strip().lower(): x for x in partidas if isinstance(x, dict)},
            "equipamiento": equipamiento,
            "equipamiento_por_id": {str(x.get("id") or "").strip().lower(): x for x in equipamiento if isinstance(x, dict)},
            "roles": roles,
            "roles_por_id": {str(x.get("id") or "").strip().lower(): x for x in roles if isinstance(x, dict)},
            "turnos": turnos,
            "turnos_por_id": {str(x.get("id") or "").strip().lower(): x for x in turnos if isinstance(x, dict)},
            "personal": personal,
            "capacidades": dict(cfg_r2.get("capacidades") or {}),
        }

    @staticmethod
    def _equipos_tarea(tarea: dict[str, Any]) -> list[str]:
        asign = dict(tarea.get("recursos_asignados") or {})
        req = dict(tarea.get("requisitos_recursos") or {})
        equipos = list(asign.get("equipamiento_ids") or req.get("equipamiento_ids") or [])
        return [str(x or "").strip().lower() for x in equipos if str(x or "").strip()]

    @staticmethod
    def _personas_asignadas_tarea(tarea: dict[str, Any]) -> list[str]:
        asign = dict(tarea.get("recursos_asignados") or {})
        return [str(x or "").strip().lower() for x in list(asign.get("persona_ids") or []) if str(x or "").strip()]

    @staticmethod
    def _parse_hora(hora_texto: str) -> int | None:
        texto = str(hora_texto or "").strip()
        if not texto:
            return None
        try:
            hh, mm = texto.split(":", 1)
            h = int(hh)
            m = int(mm)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                return None
            return h * 60 + m
        except Exception:
            return None

    def _intervalo_tarea(self, tarea: dict[str, Any]) -> tuple[IntervaloTarea | None, str | None]:
        tid = str(tarea.get("id") or "")
        inicio = self._parse_hora(str(tarea.get("hora_inicio") or ""))
        fin = self._parse_hora(str(tarea.get("hora_fin") or ""))

        if inicio is not None and fin is not None and fin > inicio:
            return IntervaloTarea(tid, inicio, fin), None

        req = self.normalizar_requisitos_recursos(tarea.get("requisitos_recursos") or {})
        dur = req.get("duracion_minutos")
        if inicio is not None and isinstance(dur, int) and dur > 0:
            return IntervaloTarea(tid, inicio, inicio + dur), None

        return None, f"No se pudo comprobar simultaneidad de la tarea {tid}: datos temporales incompletos"

    @staticmethod
    def _solapan(a_ini: int, a_fin: int, b_ini: int, b_fin: int) -> bool:
        return a_ini < b_fin and b_ini < a_fin

    @staticmethod
    def _tramos_temporales(intervalos: dict[str, IntervaloTarea]) -> list[tuple[int, int]]:
        puntos = sorted({x for itv in intervalos.values() for x in (itv.inicio_min, itv.fin_min)})
        return [(a, b) for a, b in zip(puntos, puntos[1:]) if b > a]


__all__ = ["ServicioProduccionRecursosReales", "ESTADOS_DIAGNOSTICO"]
