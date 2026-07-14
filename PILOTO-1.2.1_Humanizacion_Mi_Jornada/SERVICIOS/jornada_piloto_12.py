from __future__ import annotations

import json
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from SERVICIOS.bandeja_trabajo_piloto_11 import BandejaTrabajoPiloto11


PRIORIDAD_HUMANA = (
    (90, "MUY_URGENTE", "Muy urgente"),
    (70, "HOY", "Hoy"),
    (50, "ESTA_SEMANA", "Esta semana"),
    (0, "CUANDO_PUEDAS", "Cuando puedas"),
)

DURACION_DEFECTO = {
    "RECEPCION": 30,
    "STOCK": 20,
    "EVENTO": 20,
    "PEDIDO": 15,
    "INCIDENCIA_PROVEEDOR": 15,
    "DOCUMENTO": 15,
    "GENERAL": 30,
}

FASES_PASIVAS = {
    "coccion", "reposo", "fermentacion", "abatido", "enfriado",
    "marinado", "secado", "congelacion", "descongelacion",
}


@dataclass(frozen=True)
class DuracionTarea:
    total_min: int | None
    activo_min: int | None
    pasivo_min: int | None
    fuente: str


class JornadaPiloto12:
    """Orquestador determinista de la jornada del piloto.

    No usa IA ni modifica datos operativos. Lee la bandeja y los módulos de
    producción/eventos/compras para presentar un plan comprensible y explicable.
    """

    VERSION = "PILOTO-1.2.1"

    def __init__(self, base_dir: Path | str, bandeja: BandejaTrabajoPiloto11 | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.bandeja = bandeja or BandejaTrabajoPiloto11(self.base_dir)
        self.planes_path = self.base_dir / "DATOS" / "db" / "planes_produccion.json"
        self.eventos_path = self.base_dir / "DATOS" / "db" / "eventos.json"
        self.pedidos_path = self.base_dir / "DATOS" / "db" / "compras_pedidos.json"

    def construir(self, ahora: datetime | None = None) -> dict[str, Any]:
        ahora = ahora or datetime.now()
        self.bandeja.sincronizar_fuentes()
        tareas = self.bandeja.listar()
        planes = self._indexar_produccion()
        eventos = self._indexar_eventos()

        items: list[dict[str, Any]] = []
        for tarea in tareas:
            duracion = self._duracion_tarea(tarea, planes)
            prioridad = self._prioridad_humana(int(tarea.get("prioridad", 50)))
            evento_info = self._evento_tarea(tarea, eventos, ahora.date())
            score = self._score(tarea, evento_info)
            items.append({
                **tarea,
                "prioridad_codigo": prioridad[0],
                "prioridad_texto": prioridad[1],
                "duracion_total_min": duracion.total_min,
                "duracion_activa_min": duracion.activo_min,
                "duracion_pasiva_min": duracion.pasivo_min,
                "duracion_fuente": duracion.fuente,
                "evento": evento_info,
                "orden_score": score,
            })

        for item in items:
            item["prioridad_humana"] = self._etiqueta_prioridad(item.get("prioridad_codigo"))
            item["duracion_humana"] = self._hm(item.get("duracion_total_min"))
            item["duracion_activa_humana"] = self._hm(item.get("duracion_activa_min"))
            item["duracion_pasiva_humana"] = self._hm(item.get("duracion_pasiva_min"))
            item["evento_mensaje"] = self._mensaje_evento(item.get("evento", {}))
            item["explicacion"] = self._motivo(item)

        items.sort(key=lambda x: (-x["orden_score"], x.get("creado_en", ""), x.get("titulo", "")))
        grupos: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            grupos[item.get("tipo", "GENERAL")].append(item)

        total_conocido = sum(x["duracion_total_min"] or 0 for x in items)
        activo_conocido = sum(x["duracion_activa_min"] or 0 for x in items)
        pasivo_conocido = sum(x["duracion_pasiva_min"] or 0 for x in items)
        sin_duracion = sum(1 for x in items if x["duracion_total_min"] is None)

        fin_estimado = None
        if activo_conocido > 0:
            fin_estimado = (ahora.timestamp() + activo_conocido * 60)
            fin_estimado = datetime.fromtimestamp(fin_estimado).isoformat(timespec="minutes")

        alertas = self._alertas(items, ahora)
        recomendaciones = self._recomendaciones(items)
        counts = Counter(x["prioridad_codigo"] for x in items)

        saludo = self._saludo(ahora)
        resumen_humano = self._resumen_humano(items, counts, alertas)
        cronograma = self._cronograma(items, ahora)

        return {
            "version": self.VERSION,
            "generado_en": ahora.isoformat(timespec="seconds"),
            "fecha": ahora.date().isoformat(),
            "saludo": saludo,
            "resumen_humano": resumen_humano,
            "resumen": {
                "abiertas": len(items),
                "muy_urgentes": counts.get("MUY_URGENTE", 0),
                "hoy": counts.get("HOY", 0),
                "esta_semana": counts.get("ESTA_SEMANA", 0),
                "cuando_puedas": counts.get("CUANDO_PUEDAS", 0),
                "por_tipo": dict(Counter(x.get("tipo", "GENERAL") for x in items)),
            },
            "tiempos": {
                "total_conocido_min": total_conocido,
                "activo_conocido_min": activo_conocido,
                "pasivo_conocido_min": pasivo_conocido,
                "tareas_sin_duracion": sin_duracion,
                "fin_estimado_por_trabajo_activo": fin_estimado,
                "nota": "La hora estimada usa solo tiempos activos registrados; no sustituye la planificación de producción.",
            },
            "tareas": items,
            "grupos": dict(grupos),
            "recomendaciones": recomendaciones,
            "cronograma": cronograma,
            "alertas": alertas,
            "solo_lectura": True,
        }

    def _prioridad_humana(self, prioridad: int) -> tuple[str, str]:
        for limite, codigo, texto in PRIORIDAD_HUMANA:
            if prioridad >= limite:
                return codigo, texto
        return "CUANDO_PUEDAS", "Cuando puedas"

    def _score(self, tarea: dict[str, Any], evento_info: dict[str, Any]) -> int:
        score = int(tarea.get("prioridad", 50)) * 10
        estado = tarea.get("estado", "PENDIENTE")
        score += {"EN_CURSO": 300, "BLOQUEADA": 180, "PENDIENTE": 100, "APLAZADA": -100}.get(estado, 0)
        tipo = tarea.get("tipo", "GENERAL")
        score += {"RECEPCION": 120, "PRODUCCION": 100, "INCIDENCIA_PROVEEDOR": 90,
                  "PEDIDO": 60, "STOCK": 50, "EVENTO": 40}.get(tipo, 0)
        dias = evento_info.get("dias_restantes")
        if isinstance(dias, int):
            if dias < 0: score += 250
            elif dias == 0: score += 240
            elif dias <= 2: score += 180
            elif dias <= 7: score += 80
        return score

    def _duracion_tarea(self, tarea: dict[str, Any], planes: dict[str, dict[str, Any]]) -> DuracionTarea:
        if tarea.get("tipo") != "PRODUCCION":
            minutos = DURACION_DEFECTO.get(tarea.get("tipo", "GENERAL"))
            return DuracionTarea(minutos, minutos, 0, "estimación operativa fija") if minutos else DuracionTarea(None, None, None, "sin datos")

        tarea_id = str(tarea.get("metadatos", {}).get("tarea_id") or "")
        original = planes.get(tarea_id)
        if not original:
            return DuracionTarea(None, None, None, "producción sin tarea vinculada")

        fases = original.get("fases") or []
        if fases:
            activo = 0
            pasivo = 0
            for fase in fases:
                minutos = self._int(fase.get("duracion_min"))
                if str(fase.get("tipo", "")).lower() in FASES_PASIVAS:
                    pasivo += minutos
                else:
                    activo += minutos
            return DuracionTarea(activo + pasivo, activo, pasivo, "fases de producción")

        total = self._int(original.get("duracion_total_min"))
        return DuracionTarea(total or None, total or None, 0 if total else None, "duración total de producción")

    def _evento_tarea(self, tarea: dict[str, Any], eventos: dict[str, dict[str, Any]], hoy: date) -> dict[str, Any]:
        evento_id = str(tarea.get("metadatos", {}).get("evento_id") or "")
        evento = eventos.get(evento_id)
        if not evento:
            return {}
        fecha = self._parse_fecha(evento.get("fecha"))
        dias = (fecha - hoy).days if fecha else None
        return {
            "id": evento_id,
            "nombre": evento.get("nombre", ""),
            "fecha": evento.get("fecha", ""),
            "pax": evento.get("pax", 0),
            "dias_restantes": dias,
        }

    def _recomendaciones(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in items[:5]:
            motivo = self._motivo(item)
            out.append({
                "tarea_id": item.get("id"),
                "titulo": item.get("titulo"),
                "tipo": item.get("tipo"),
                "prioridad": item.get("prioridad_texto"),
                "motivo": motivo,
                "motivo_humano": motivo,
            })
        # Recomendación paralela simple y explicable.
        pasiva = next((x for x in items if (x.get("duracion_pasiva_min") or 0) >= 45), None)
        otra = next((x for x in items if pasiva and x.get("id") != pasiva.get("id") and x.get("tipo") != "EVENTO"), None)
        if pasiva and otra:
            out.append({
                "tarea_id": otra.get("id"),
                "titulo": otra.get("titulo"),
                "tipo": otra.get("tipo"),
                "prioridad": otra.get("prioridad_texto"),
                "motivo": f"Puede hacerse durante los {pasiva.get('duracion_pasiva_min')} min pasivos de {pasiva.get('titulo')}.",
                "motivo_humano": f"Puede hacerse durante las {self._hm(pasiva.get('duracion_pasiva_min'))} de espera de {pasiva.get('titulo')}.",
                "paralela_con": pasiva.get("id"),
            })
        return out

    def _motivo(self, item: dict[str, Any]) -> str:
        if item.get("estado") == "EN_CURSO":
            return "Ya está en curso; conviene terminarla antes de abrir otra tarea."
        if item.get("tipo") == "RECEPCION":
            return "Una recepción pendiente afecta a stock, precios y compras."
        if item.get("tipo") == "PRODUCCION":
            pasivo = item.get("duracion_pasiva_min") or 0
            if pasivo:
                return f"Producción prioritaria con {self._hm(pasivo)} de espera que puedes aprovechar para otra tarea."
            return "Producción pendiente ordenada por la prioridad registrada."
        if item.get("tipo") == "INCIDENCIA_PROVEEDOR":
            return "Conviene dejar registrada la incidencia antes de cerrar el día."
        if item.get("tipo") == "EVENTO":
            dias = item.get("evento", {}).get("dias_restantes")
            if dias is not None:
                return self._mensaje_evento(item.get("evento", {}))
            return "Evento abierto sin fecha utilizable o sin cerrar."
        if item.get("tipo") == "PEDIDO":
            return "Pedido abierto que puede afectar a la disponibilidad de producto."
        return "Ordenada por estado y prioridad de la bandeja."

    def _alertas(self, items: list[dict[str, Any]], ahora: datetime) -> list[dict[str, str]]:
        alertas: list[dict[str, str]] = []
        bloqueadas = [x for x in items if x.get("estado") == "BLOQUEADA"]
        if bloqueadas:
            alertas.append({"nivel": "ALTA", "codigo": "TAREAS_BLOQUEADAS", "mensaje": f"Hay {len(bloqueadas)} tarea(s) bloqueada(s)."})
        vencidos = [x for x in items if isinstance(x.get("evento", {}).get("dias_restantes"), int) and x["evento"]["dias_restantes"] < 0]
        if vencidos:
            alertas.append({"nivel": "ALTA", "codigo": "EVENTOS_VENCIDOS", "mensaje": f"Hay {len(vencidos)} tarea(s) asociada(s) a eventos con fecha pasada."})
        sin_duracion = [x for x in items if x.get("tipo") == "PRODUCCION" and x.get("duracion_total_min") is None]
        if sin_duracion:
            alertas.append({"nivel": "MEDIA", "codigo": "PRODUCCION_SIN_TIEMPO", "mensaje": f"Hay {len(sin_duracion)} producción(es) sin duración registrada."})
        aplazadas = [x for x in items if x.get("estado") == "APLAZADA"]
        if aplazadas:
            alertas.append({"nivel": "BAJA", "codigo": "TAREAS_APLAZADAS", "mensaje": f"Hay {len(aplazadas)} tarea(s) aplazada(s) pendientes de revisar."})
        return alertas


    @staticmethod
    def _hm(minutes: int | None) -> str:
        if minutes is None:
            return "sin tiempo registrado"
        h, m = divmod(int(minutes), 60)
        if h and m:
            return f"{h} h {m} min"
        if h:
            return f"{h} h"
        return f"{m} min"

    @staticmethod
    def _etiqueta_prioridad(codigo: str | None) -> str:
        return {
            "MUY_URGENTE": "🔴 Muy urgente",
            "HOY": "🟠 Conviene hacerlo hoy",
            "ESTA_SEMANA": "🟡 Puede organizarse esta semana",
            "CUANDO_PUEDAS": "🟢 Puede esperar",
        }.get(str(codigo or ""), "⚪ Sin prioridad definida")

    @staticmethod
    def _saludo(ahora: datetime) -> str:
        if ahora.hour < 12:
            return "Buenos días. Vamos a organizar la jornada."
        if ahora.hour < 20:
            return "Buenas tardes. Revisemos qué queda por hacer hoy."
        return "Buenas noches. Revisemos lo pendiente antes de cerrar el día."

    def _mensaje_evento(self, evento: dict[str, Any]) -> str:
        if not evento:
            return ""
        dias = evento.get("dias_restantes")
        nombre = evento.get("nombre") or "Este evento"
        if not isinstance(dias, int):
            return f"{nombre}: revisa la fecha, porque no se ha podido interpretar."
        if dias < 0:
            return f"{nombre} ya ha pasado. Comprueba que todo quedó cerrado."
        if dias == 0:
            return f"{nombre} es hoy. Revisa ahora producción, compras y pendientes."
        if dias == 1:
            return f"{nombre} es mañana. Deja hoy todo lo importante preparado."
        if dias <= 3:
            return f"{nombre} es dentro de {dias} días. Conviene avanzar producción y compras."
        return f"{nombre} es dentro de {dias} días. Aún hay margen, pero no lo pierdas de vista."

    def _resumen_humano(self, items: list[dict[str, Any]], counts: Counter, alertas: list[dict[str, str]]) -> str:
        total = len(items)
        if total == 0:
            return "No tienes trabajo pendiente registrado. La jornada está limpia."
        urgentes = counts.get("MUY_URGENTE", 0)
        hoy = counts.get("HOY", 0)
        if urgentes:
            base = f"Tienes {total} tarea(s) abierta(s), con {urgentes} muy urgente(s). Empieza por resolver esas primero."
        elif hoy:
            base = f"Tienes {total} tarea(s) abierta(s). Hay {hoy} que conviene dejar terminada(s) hoy."
        else:
            base = f"Tienes {total} tarea(s) abierta(s), pero ninguna aparece como crítica ahora mismo."
        if alertas:
            base += f" Además, hay {len(alertas)} aviso(s) que deberías revisar."
        return base

    def _cronograma(self, items: list[dict[str, Any]], ahora: datetime) -> list[dict[str, Any]]:
        cursor = ahora
        bloques: list[dict[str, Any]] = []
        for item in items[:8]:
            minutos = item.get("duracion_activa_min")
            inicio = cursor.strftime("%H:%M")
            if isinstance(minutos, int) and minutos > 0:
                cursor = datetime.fromtimestamp(cursor.timestamp() + minutos * 60)
                fin = cursor.strftime("%H:%M")
                franja = f"{inicio}–{fin}"
            else:
                fin = None
                franja = f"Desde las {inicio}"
            bloques.append({
                "tarea_id": item.get("id"),
                "franja": franja,
                "inicio": inicio,
                "fin": fin,
                "titulo": item.get("titulo"),
                "prioridad": item.get("prioridad_humana"),
                "explicacion": item.get("explicacion"),
                "estimado": True,
            })
        return bloques

    def diagnostico(self) -> dict[str, Any]:
        diag = self.base_dir / "DATOS" / "mur" / "diagnostico_piloto12"
        if diag.exists():
            shutil.rmtree(diag)
        (diag / "DATOS" / "db").mkdir(parents=True)
        (diag / "DATOS" / "piloto" / "bandeja_trabajo").mkdir(parents=True)

        planes = [{
            "id": "PLAN-DIAG", "evento_id": "EVT-DIAG", "evento": "Boda diagnóstico",
            "tareas": [
                {"id": "TAREA-PROD-1", "titulo": "Preparar demi-glace", "estado_ejecucion": "pendiente", "prioridad": 90,
                 "fases": [
                     {"nombre": "Preparar base", "duracion_min": 30, "tipo": "preparacion"},
                     {"nombre": "Reducir", "duracion_min": 120, "tipo": "coccion"},
                 ]},
                {"id": "TAREA-PROD-2", "titulo": "Preparar carrillera", "estado_ejecucion": "pendiente", "prioridad": 80,
                 "fases": [{"nombre": "Preparar", "duracion_min": 45, "tipo": "preparacion"}]},
            ],
        }]
        eventos = [{"id": "EVT-DIAG", "nombre": "Boda diagnóstico", "fecha": "14/07/2026", "pax": 100, "estado": "pendiente"}]
        (diag / "DATOS" / "db" / "planes_produccion.json").write_text(json.dumps(planes, ensure_ascii=False, indent=2), encoding="utf-8")
        (diag / "DATOS" / "db" / "eventos.json").write_text(json.dumps(eventos, ensure_ascii=False, indent=2), encoding="utf-8")
        (diag / "DATOS" / "db" / "compras_pedidos.json").write_text("[]", encoding="utf-8")

        bandeja = BandejaTrabajoPiloto11(diag)
        bandeja.crear_tarea("Finalizar recepción Makro", "RECEPCION", 90, "Stock pendiente", metadatos={"clave_origen": "diag:recepcion"})
        jornada = JornadaPiloto12(diag, bandeja=bandeja)
        resultado = jornada.construir(datetime(2026, 7, 13, 8, 0))
        tareas = resultado["tareas"]
        ok = (
            len(tareas) == 4
            and tareas[0]["prioridad_codigo"] == "MUY_URGENTE"
            and any((x.get("duracion_pasiva_min") or 0) == 120 for x in tareas)
            and len(resultado["recomendaciones"]) >= 3
            and resultado["solo_lectura"] is True
        )
        return {
            "diagnostico": "OK" if ok else "ERROR",
            "tareas": len(tareas),
            "muy_urgentes": resultado["resumen"]["muy_urgentes"],
            "tiempo_activo_min": resultado["tiempos"]["activo_conocido_min"],
            "tiempo_pasivo_min": resultado["tiempos"]["pasivo_conocido_min"],
            "recomendaciones": len(resultado["recomendaciones"]),
            "alertas": len(resultado["alertas"]),
            "archivo_aislado": str(diag),
            "solo_lectura": True,
        }

    def _indexar_produccion(self) -> dict[str, dict[str, Any]]:
        data = self._load_json(self.planes_path, [])
        out: dict[str, dict[str, Any]] = {}
        for plan in data if isinstance(data, list) else []:
            for tarea in plan.get("tareas", []):
                if tarea.get("id"):
                    out[str(tarea["id"])] = tarea
        return out

    def _indexar_eventos(self) -> dict[str, dict[str, Any]]:
        data = self._load_json(self.eventos_path, [])
        return {str(x.get("id")): x for x in data if isinstance(x, dict) and x.get("id")} if isinstance(data, list) else {}

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return default

    @staticmethod
    def _int(value: Any) -> int:
        try:
            return max(0, int(float(value or 0)))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_fecha(value: Any) -> date | None:
        text = str(value or "").strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None


def _hm(minutes: int | None) -> str:
    if minutes is None:
        return "sin tiempo registrado"
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h} h {m} min"
    if h:
        return f"{h} h"
    return f"{m} min"


def formatear_diagnostico_piloto12(d: dict[str, Any]) -> str:
    return "\n".join([
        "PILOTO-1.2.1 — HUMANIZACIÓN DE MI JORNADA",
        "=" * 78,
        f"Diagnóstico: {d['diagnostico']} | Solo lectura: {'SÍ' if d['solo_lectura'] else 'NO'}",
        f"Tareas: {d['tareas']} | Muy urgentes: {d['muy_urgentes']} | Recomendaciones: {d['recomendaciones']} | Alertas: {d['alertas']}",
        f"Tiempo activo conocido: {_hm(d['tiempo_activo_min'])} | Tiempo pasivo conocido: {_hm(d['tiempo_pasivo_min'])}",
        f"Entorno aislado: {d['archivo_aislado']}",
        "-" * 78,
        "Se validaron agrupación, prioridades humanas, tiempos registrados, orden del día y trabajo paralelo.",
        "El diagnóstico no modifica bandeja, producción, eventos, compras, stock ni recepciones reales.",
    ])


__all__ = ["JornadaPiloto12", "DuracionTarea", "formatear_diagnostico_piloto12"]
