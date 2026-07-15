from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from SERVICIOS.cruce_stock_produccion_556c import CruceStockProduccion556C
from SERVICIOS.motor_planificacion_recetas_reales_556e31 import MotorPlanificacionRecetasReales556E31
from SERVICIOS.planificador_diario_produccion_461 import PlanificadorDiarioProduccion461


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip(" .")


def _load_list(path: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("items", "registros", "eventos", "escandallos"):
            if isinstance(data.get(key), list):
                return [x for x in data[key] if isinstance(x, dict)]
    return []


def es_consulta_produccion_automatica_evento_556f(texto: str) -> bool:
    t = _norm(texto)
    patrones = (
        "produccion automatica",
        "produccion del evento",
        "plan de produccion del evento",
        "planificar evento",
        "evento",
    )
    return "produccion" in t and any(p in t for p in patrones)


def extraer_consulta_evento_556f(texto: str) -> Dict[str, Any]:
    raw = str(texto or "").strip()
    t = _norm(raw)

    evento_id = None
    match_id = re.search(r"\bEVT-[A-Z0-9]+\b", raw, flags=re.I)
    if match_id:
        evento_id = match_id.group(0).upper()

    cocineros = 3
    match_coc = re.search(r"(\d+)\s*cociner", t)
    if match_coc:
        cocineros = max(1, int(match_coc.group(1)))

    inicio_jornada = "08:00"
    fin_jornada = "15:30"
    match_inicio = re.search(r"inicio\s+(\d{1,2}:\d{2})", t)
    match_fin = re.search(r"fin\s+(\d{1,2}:\d{2})", t)
    if match_inicio:
        inicio_jornada = match_inicio.group(1)
    if match_fin:
        fin_jornada = match_fin.group(1)

    evento_ref = ""
    if evento_id:
        evento_ref = evento_id
    else:
        match_evento = re.search(r"evento\s+(.+?)(?:\s+con\s+\d+\s*cociner|\s+inicio\s+\d{1,2}:\d{2}|\s+fin\s+\d{1,2}:\d{2}|$)", t)
        if match_evento:
            evento_ref = match_evento.group(1).strip(" .")

    return {
        "evento": evento_ref,
        "cocineros": cocineros,
        "inicio_jornada": inicio_jornada,
        "fin_jornada": fin_jornada,
    }


class ProduccionAutomaticaEvento556F:
    VERSION = "5.5.6F"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.db_dir = self.base_dir / "DATOS" / "db"
        self.motor_plan = MotorPlanificacionRecetasReales556E31(self.base_dir)
        self.cruce_stock = CruceStockProduccion556C(self.base_dir)
        self.planificador_dia = PlanificadorDiarioProduccion461(self.base_dir, create_output_dir=False)

    def planificar_evento(
        self,
        evento_ref: str,
        cocineros: int = 3,
        inicio_jornada: str = "08:00",
        fin_jornada: str = "15:30",
    ) -> Dict[str, Any]:
        evento, metodo, ambiguos = self._resolver_evento(evento_ref)
        if ambiguos:
            return {
                "version": self.VERSION,
                "estado": "EVENTO_AMBIGUO",
                "ok": False,
                "evento": evento_ref,
                "opciones": ambiguos,
                "solo_lectura": True,
                "datos_reales_modificados": False,
            }
        if not evento:
            return {
                "version": self.VERSION,
                "estado": "EVENTO_NO_LOCALIZADO",
                "ok": False,
                "evento": evento_ref,
                "solo_lectura": True,
                "datos_reales_modificados": False,
            }

        pax = int(evento.get("pax") or evento.get("personas") or 0)
        if pax <= 0:
            return {
                "version": self.VERSION,
                "estado": "EVENTO_SIN_PAX",
                "ok": False,
                "evento": evento.get("nombre") or evento_ref,
                "solo_lectura": True,
                "datos_reales_modificados": False,
            }

        refs_receta = self._extraer_recetas_evento(evento)
        if not refs_receta:
            return {
                "version": self.VERSION,
                "estado": "EVENTO_SIN_RECETAS",
                "ok": False,
                "evento": evento.get("nombre") or evento_ref,
                "solo_lectura": True,
                "datos_reales_modificados": False,
            }

        indice = self._indice_recetas_canonicas()
        recetas = []
        bloqueos: List[Dict[str, Any]] = []
        elaboraciones = []
        planes_receta = []
        cruces_stock = []
        compras_idx: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

        for ref in refs_receta:
            receta = self._resolver_receta(ref, indice)
            if not receta:
                bloqueos.append({
                    "tipo": "RECETA_NO_LOCALIZADA",
                    "receta_ref": ref,
                    "motivo": "La receta del evento no existe en escandallos canónicos.",
                })
                continue
            recetas.append(receta)

            plan = self.motor_plan.planificar(receta["nombre"], pax, "personas", cocineros, inicio_jornada, fin_jornada)
            cruce = self.cruce_stock.cruzar(receta["nombre"], pax, "personas")

            planes_receta.append(plan)
            cruces_stock.append(cruce)

            if not plan.get("puede_planificar"):
                bloqueos.append({
                    "tipo": "FALTA_FICHA_PRODUCCION",
                    "receta": receta["nombre"],
                    "motivo": plan.get("motivo") or "No existe ficha validada.",
                })

            for linea in cruce.get("lineas", []):
                estado_linea = str(linea.get("estado") or "")
                faltante = float(linea.get("faltante") or 0)
                if faltante > 0 or estado_linea in ("ARTICULO_NO_LOCALIZADO", "ARTICULO_SIN_INVENTARIO", "UNIDAD_INCOMPATIBLE", "SIN_STOCK", "STOCK_INSUFICIENTE"):
                    bloqueos.append({
                        "tipo": "BLOQUEO_STOCK",
                        "receta": receta["nombre"],
                        "articulo": linea.get("articulo_nombre") or linea.get("nombre"),
                        "estado": estado_linea,
                        "faltante": round(faltante, 4),
                        "unidad": linea.get("unidad"),
                    })
                if faltante > 0:
                    key = (
                        str(linea.get("articulo_id") or ""),
                        str(linea.get("articulo_nombre") or linea.get("nombre") or ""),
                        str(linea.get("unidad") or "u"),
                    )
                    compra = compras_idx.setdefault(
                        key,
                        {
                            "articulo_id": key[0] or None,
                            "articulo": key[1],
                            "unidad": key[2],
                            "cantidad": 0.0,
                            "proveedor": linea.get("proveedor"),
                            "motivo": "FALTANTE_PARA_PRODUCCION_EVENTO",
                        },
                    )
                    compra["cantidad"] += faltante

            elaboraciones.append({
                "clave": receta["codigo"] or _norm(receta["nombre"]).replace(" ", "_"),
                "nombre": receta["nombre"],
                "prioridad": "alta" if cruce.get("total_faltantes", 0) else "normal",
                "tiempo_activo_min": int(plan.get("minutos_activos") or 0),
                "tiempo_pasivo_min": int(plan.get("minutos_pasivos") or 0),
                "recursos": sorted({r for t in plan.get("tareas", []) for r in (t.get("recursos") or [])}),
            })

        servicio = self._hora_servicio_evento(evento)
        plan_dia = self.planificador_dia.planificar_dia(
            elaboraciones,
            fecha=str(evento.get("fecha") or ""),
            hora_servicio=servicio,
            cocineros=int(cocineros),
            jornada_horas=max(0.5, (self._minutos(fin_jornada) - self._minutos(inicio_jornada)) / 60.0),
            hora_inicio=inicio_jornada,
        )

        compras = []
        for item in sorted(compras_idx.values(), key=lambda x: (str(x.get("articulo") or "").casefold(), str(x.get("unidad") or ""))):
            item["cantidad"] = round(float(item["cantidad"]), 4)
            compras.append(item)

        plan_id = self._id_determinista(
            evento_id=str(evento.get("id") or ""),
            pax=pax,
            recetas=[r["codigo"] or r["nombre"] for r in recetas],
            cocineros=int(cocineros),
            inicio_jornada=inicio_jornada,
            fin_jornada=fin_jornada,
        )

        estado = "PLAN_PRELIMINAR_OK" if not bloqueos else "PLAN_BLOQUEADO"
        return {
            "version": self.VERSION,
            "ok": not bloqueos,
            "estado": estado,
            "id_plan_automatico": plan_id,
            "evento": {
                "id": evento.get("id"),
                "nombre": evento.get("nombre"),
                "fecha": evento.get("fecha"),
                "pax": pax,
                "metodo_localizacion": metodo,
            },
            "parametros": {
                "cocineros": int(cocineros),
                "inicio_jornada": inicio_jornada,
                "fin_jornada": fin_jornada,
                "hora_servicio": servicio,
            },
            "recetas": recetas,
            "planes_receta": planes_receta,
            "cruces_stock": cruces_stock,
            "plan_diario": plan_dia,
            "bloqueos": bloqueos,
            "compras_propuestas": compras,
            "solo_lectura": True,
            "datos_reales_modificados": False,
            "fuentes": [
                "DATOS/db/eventos.json",
                "DATOS/db/escandallos_canonicos.json",
                "DATOS/db/fichas_produccion_reales.json",
                "DATOS/db/articulos.json",
                "DATOS/db/stock_inicial.json",
                "DATOS/db/stock_movimientos.json",
            ],
        }

    def _resolver_evento(self, evento_ref: str) -> Tuple[Optional[Dict[str, Any]], str, List[str]]:
        eventos = _load_list(self.db_dir / "eventos.json")
        objetivo = _norm(evento_ref)
        if not objetivo:
            return None, "SIN_REFERENCIA", []

        exacto_id = [e for e in eventos if str(e.get("id") or "").casefold() == str(evento_ref).casefold()]
        if len(exacto_id) == 1:
            return exacto_id[0], "ID_EXACTO", []

        exacto_nombre = [e for e in eventos if _norm(e.get("nombre")) == objetivo]
        if len(exacto_nombre) == 1:
            return exacto_nombre[0], "NOMBRE_EXACTO", []
        if len(exacto_nombre) > 1:
            return None, "NOMBRE_AMBIGUO", [str(e.get("nombre") or "") for e in exacto_nombre]

        parciales = [e for e in eventos if objetivo and (objetivo in _norm(e.get("nombre")) or _norm(e.get("nombre")) in objetivo)]
        if len(parciales) == 1:
            return parciales[0], "NOMBRE_PARCIAL", []
        if len(parciales) > 1:
            return None, "NOMBRE_AMBIGUO", [str(e.get("nombre") or "") for e in parciales]

        return None, "NO_LOCALIZADO", []

    def _extraer_recetas_evento(self, evento: Dict[str, Any]) -> List[str]:
        refs: List[str] = []
        for servicio in evento.get("servicios", []) or []:
            for pase in servicio.get("pases", []) or []:
                for receta in pase.get("recetas", []) or []:
                    txt = str(receta).strip()
                    if txt and txt not in refs:
                        refs.append(txt)
        for campo in ("menu", "receta"):
            txt = str(evento.get(campo) or "").strip()
            if txt and txt not in refs:
                refs.append(txt)
        return refs

    def _indice_recetas_canonicas(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        raws = _load_list(self.db_dir / "escandallos_canonicos.json")
        por_codigo: Dict[str, Dict[str, str]] = {}
        por_nombre: Dict[str, Dict[str, str]] = {}
        for item in raws:
            receta = item.get("receta") if isinstance(item.get("receta"), dict) else item
            if not isinstance(receta, dict):
                continue
            codigo = str(receta.get("codigo") or receta.get("receta_id") or receta.get("id") or "").strip()
            nombre = str(receta.get("nombre") or receta.get("receta") or "").strip()
            if not nombre:
                continue
            data = {"codigo": codigo, "nombre": nombre}
            if codigo:
                por_codigo[codigo.casefold()] = data
            por_nombre[_norm(nombre)] = data
        return {"por_codigo": por_codigo, "por_nombre": por_nombre}

    def _resolver_receta(self, ref: str, indice: Dict[str, Dict[str, Dict[str, str]]]) -> Optional[Dict[str, str]]:
        txt = str(ref or "").strip()
        if not txt:
            return None
        by_code = indice["por_codigo"].get(txt.casefold())
        if by_code:
            return by_code
        n = _norm(txt)
        by_name = indice["por_nombre"].get(n)
        if by_name:
            return by_name
        parciales = [v for k, v in indice["por_nombre"].items() if n and (n in k or k in n)]
        if len(parciales) == 1:
            return parciales[0]
        return None

    def _hora_servicio_evento(self, evento: Dict[str, Any]) -> str:
        for servicio in evento.get("servicios", []) or []:
            hora = str(servicio.get("hora_inicio") or "").strip()
            if re.fullmatch(r"\d{1,2}:\d{2}", hora):
                return hora
        hora = str(evento.get("hora_inicio") or evento.get("hora") or "").strip()
        if re.fullmatch(r"\d{1,2}:\d{2}", hora):
            return hora
        return "13:30"

    @staticmethod
    def _minutos(hora: str) -> int:
        try:
            h, m = str(hora).split(":", 1)
            return int(h) * 60 + int(m)
        except Exception:
            return 0

    @staticmethod
    def _id_determinista(
        *,
        evento_id: str,
        pax: int,
        recetas: List[str],
        cocineros: int,
        inicio_jornada: str,
        fin_jornada: str,
    ) -> str:
        semilla = {
            "evento_id": evento_id,
            "pax": pax,
            "recetas": sorted(str(x) for x in recetas),
            "cocineros": cocineros,
            "inicio_jornada": inicio_jornada,
            "fin_jornada": fin_jornada,
        }
        payload = json.dumps(semilla, ensure_ascii=True, sort_keys=True)
        return "PLAN-AUTO-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12].upper()


def formatear_produccion_automatica_evento_556f(resultado: Dict[str, Any]) -> str:
    estado = resultado.get("estado")
    if estado == "EVENTO_AMBIGUO":
        opciones = resultado.get("opciones") or []
        return "\n".join([
            "PRODUCCIÓN AUTOMÁTICA EVENTO",
            "- Hay varios eventos coincidentes.",
            *[f"- Opción: {x}" for x in opciones],
            "- Indica el nombre exacto o el ID EVT-...",
            "",
            "SEGURIDAD",
            "- Datos reales modificados: NO.",
        ])
    if estado in ("EVENTO_NO_LOCALIZADO", "EVENTO_SIN_PAX", "EVENTO_SIN_RECETAS"):
        return "\n".join([
            "PRODUCCIÓN AUTOMÁTICA EVENTO",
            f"- Estado: {estado}",
            "- Revisa evento, personas y recetas asociadas.",
            "",
            "SEGURIDAD",
            "- Datos reales modificados: NO.",
        ])

    evento = resultado.get("evento") or {}
    bloqueos = resultado.get("bloqueos") or []
    compras = resultado.get("compras_propuestas") or []
    plan = resultado.get("plan_diario") or {}

    lines = [
        "PRODUCCIÓN AUTOMÁTICA EVENTO",
        f"- Evento: {evento.get('nombre')} ({evento.get('id')})",
        f"- Pax: {evento.get('pax')}",
        f"- Estado: {resultado.get('estado')}",
        f"- Plan automático: {resultado.get('id_plan_automatico')}",
        f"- Elaboraciones en plan diario: {plan.get('total_elaboraciones', 0)}",
        f"- Minutos activos: {plan.get('minutos_activos', 0)}",
        f"- Días necesarios: {plan.get('dias_necesarios', 0)}",
    ]

    if bloqueos:
        lines += ["", "BLOQUEOS"]
        for b in bloqueos[:25]:
            receta = f"[{b.get('receta')}] " if b.get("receta") else ""
            art = f"{b.get('articulo')} " if b.get("articulo") else ""
            lines.append(f"- {b.get('tipo')}: {receta}{art}{b.get('motivo') or b.get('estado') or ''}".strip())

    if compras:
        lines += ["", "COMPRAS PROPUESTAS (PRELIMINAR)"]
        for c in compras:
            lines.append(f"- {c.get('articulo')}: {c.get('cantidad'):g} {c.get('unidad')}")

    lines += [
        "",
        "SEGURIDAD",
        "- Flujo en modo solo lectura.",
        "- No se ha descontado stock.",
        "- No se han creado pedidos finales.",
        "- Datos reales modificados: NO.",
    ]
    return "\n".join(lines)


__all__ = [
    "ProduccionAutomaticaEvento556F",
    "es_consulta_produccion_automatica_evento_556f",
    "extraer_consulta_evento_556f",
    "formatear_produccion_automatica_evento_556f",
]