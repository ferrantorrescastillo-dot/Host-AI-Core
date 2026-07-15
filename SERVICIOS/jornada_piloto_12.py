from __future__ import annotations

import json
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from SERVICIOS.alertas_stock_bajo_434 import AlertasStockBajo434
from SERVICIOS.bandeja_trabajo_piloto_11 import BandejaTrabajoPiloto11
from SERVICIOS.compras_evento_474 import calcular_necesidades_evento, comparar_con_stock
from SERVICIOS.cronograma_evento_477 import generar_cronograma_evento
from SERVICIOS.detector_incidencias_537 import detectar_incidencias_operativas
from SERVICIOS.personal_evento_475 import calcular_personal_evento
from SERVICIOS.produccion_evento_473 import generar_produccion_evento


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

    VERSION = "PILOTO-1.2"

    def __init__(self, base_dir: Path | str, bandeja: BandejaTrabajoPiloto11 | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.bandeja = bandeja or BandejaTrabajoPiloto11(self.base_dir)
        self.planes_path = self.base_dir / "DATOS" / "db" / "planes_produccion.json"
        self.eventos_path = self.base_dir / "DATOS" / "db" / "eventos.json"
        self.pedidos_path = self.base_dir / "DATOS" / "db" / "compras_pedidos.json"
        self.recepciones_rp3_path = self.base_dir / "DATOS" / "piloto" / "recepciones_rp3" / "registros.json"
        self.menus_path = self.base_dir / "DATOS" / "db" / "menus.json"
        self.articulos_path = self.base_dir / "DATOS" / "db" / "articulos.json"
        self.stock_path = self.base_dir / "DATOS" / "db" / "stock_inicial.json"

    def construir(self, ahora: datetime | None = None) -> dict[str, Any]:
        ahora = ahora or datetime.now()
        self.bandeja.sincronizar_fuentes()
        tareas = self.bandeja.listar()
        planes_raw = self._load_json(self.planes_path, [])
        planes = self._indexar_produccion()
        eventos = self._indexar_eventos()
        pedidos = self._load_json(self.pedidos_path, [])
        menus = self._load_json(self.menus_path, [])
        articulos = self._load_json(self.articulos_path, [])
        stock = self._load_json(self.stock_path, [])

        items: list[dict[str, Any]] = []
        for tarea in tareas:
            duracion = self._duracion_tarea(tarea, planes)
            prioridad = self._prioridad_humana(int(tarea.get("prioridad", 50)))
            evento_info = self._evento_tarea(tarea, eventos, ahora.date())
            factores = self._factores_operativos(tarea, planes, evento_info, ahora)
            score = self._score(tarea, evento_info, factores)
            items.append({
                **tarea,
                "prioridad_codigo": prioridad[0],
                "prioridad_texto": prioridad[1],
                "duracion_total_min": duracion.total_min,
                "duracion_activa_min": duracion.activo_min,
                "duracion_pasiva_min": duracion.pasivo_min,
                "duracion_fuente": duracion.fuente,
                "evento": evento_info,
                "dependencias": factores["dependencias"],
                "reposo_min": factores["reposo_min"],
                "abatimiento_min": factores["abatimiento_min"],
                "descongelacion_min": factores["descongelacion_min"],
                "servicio_en_min": factores["servicio_en_min"],
                "orden_score": score,
                "orden_score_operativo": score,
            })

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

        briefing = self._briefing_apertura(
            items=items,
            eventos=eventos,
            menus=menus if isinstance(menus, list) else [],
            pedidos=pedidos if isinstance(pedidos, list) else [],
            stock=stock if isinstance(stock, list) else [],
            articulos=articulos if isinstance(articulos, list) else [],
            planes=planes,
            planes_raw=planes_raw if isinstance(planes_raw, list) else [],
            ahora=ahora,
            alertas_jornada=alertas,
        )

        return {
            "version": self.VERSION,
            "generado_en": ahora.isoformat(timespec="seconds"),
            "fecha": ahora.date().isoformat(),
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
            "alertas": alertas,
            "briefing_apertura": briefing,
            "solo_lectura": True,
        }

    def _prioridad_humana(self, prioridad: int) -> tuple[str, str]:
        for limite, codigo, texto in PRIORIDAD_HUMANA:
            if prioridad >= limite:
                return codigo, texto
        return "CUANDO_PUEDAS", "Cuando puedas"

    def _score(self, tarea: dict[str, Any], evento_info: dict[str, Any], factores: dict[str, int | None]) -> int:
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
        servicio_en = factores.get("servicio_en_min")
        if isinstance(servicio_en, int):
            if servicio_en <= 0:
                score += 280
            elif servicio_en <= 120:
                score += 220
            elif servicio_en <= 360:
                score += 170
            elif servicio_en <= 720:
                score += 120
            elif servicio_en <= 1440:
                score += 80
        score += int(min(max(0, int(factores.get("dependencias") or 0)), 8) * 25)
        score += int(min(max(0, int(factores.get("reposo_min") or 0)), 240) / 4)
        score += int(min(max(0, int(factores.get("abatimiento_min") or 0)), 240) / 3)
        score += int(min(max(0, int(factores.get("descongelacion_min") or 0)), 480) / 2)
        return score

    def _factores_operativos(
        self,
        tarea: dict[str, Any],
        planes: dict[str, dict[str, Any]],
        evento_info: dict[str, Any],
        ahora: datetime,
    ) -> dict[str, int | None]:
        out: dict[str, int | None] = {
            "dependencias": 0,
            "reposo_min": 0,
            "abatimiento_min": 0,
            "descongelacion_min": 0,
            "servicio_en_min": None,
        }
        if tarea.get("tipo") == "PRODUCCION":
            tarea_id = str(tarea.get("metadatos", {}).get("tarea_id") or "")
            original = planes.get(tarea_id) or {}
            fases = original.get("fases") or []
            dependencias = 0
            reposo = 0
            abatimiento = 0
            descongelado = 0
            for fase in fases:
                dependencia = str(fase.get("dependencia") or "").strip()
                if dependencia:
                    dependencias += 1
                tipo = str(fase.get("tipo") or "").lower()
                dur = self._int(fase.get("duracion_min"))
                if tipo == "reposo":
                    reposo += dur
                elif tipo in {"abatido", "abatimiento"}:
                    abatimiento += dur
                elif tipo in {"descongelacion", "descongelado", "descongelar"}:
                    descongelado += dur
            if str(original.get("bloqueo") or "").strip():
                dependencias += 1
            out["dependencias"] = dependencias
            out["reposo_min"] = reposo
            out["abatimiento_min"] = abatimiento
            out["descongelacion_min"] = descongelado

        servicio = self._fecha_hora_evento(evento_info.get("fecha"), evento_info.get("hora"))
        if servicio is not None:
            out["servicio_en_min"] = int((servicio - ahora).total_seconds() // 60)
        return out

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
            "hora": evento.get("hora") or evento.get("hora_inicio") or "",
            "pax": evento.get("pax", 0),
            "dias_restantes": dias,
        }

    def _briefing_apertura(
        self,
        *,
        items: list[dict[str, Any]],
        eventos: dict[str, dict[str, Any]],
        menus: list[dict[str, Any]],
        pedidos: list[dict[str, Any]],
        stock: list[dict[str, Any]],
        articulos: list[dict[str, Any]],
        planes: dict[str, dict[str, Any]],
        planes_raw: list[dict[str, Any]],
        ahora: datetime,
        alertas_jornada: list[dict[str, str]],
    ) -> dict[str, Any]:
        eventos_hoy = self._eventos_hoy(eventos, ahora.date())
        cronologia = self._cronologia(eventos_hoy)
        produccion_priorizada = [x for x in items if x.get("tipo") == "PRODUCCION"][:8]
        compras_criticas = self._compras_criticas(eventos_hoy, menus, stock, pedidos)
        recepciones_previstas = self._recepciones_previstas(pedidos)
        descongelaciones = self._descongelaciones(items)
        personal = self._personal_eventos(eventos_hoy, menus)
        alertas_stock = self._alertas_stock()
        incidencias = self._incidencias(items, compras_criticas, recepciones_previstas, personal, eventos_hoy)
        recepciones_rp3 = self._resumen_recepciones_rp3()
        incidencias = incidencias + list(recepciones_rp3.get("incidencias", []))
        alergenos = self._alergenos(eventos_hoy, articulos, menus)
        produccion_viva = self._resumen_produccion_viva(planes_raw)
        prioridades = [
            {
                "tarea_id": x.get("id"),
                "titulo": x.get("titulo"),
                "tipo": x.get("tipo"),
                "prioridad_codigo": x.get("prioridad_codigo"),
                "prioridad": x.get("prioridad_texto"),
                "orden_score": x.get("orden_score_operativo"),
                "servicio_en_min": x.get("servicio_en_min"),
            }
            for x in items[:10]
        ]
        contexto = {
            "eventos_hoy": len(eventos_hoy),
            "cronologia_items": len(cronologia),
            "produccion_priorizada": len(produccion_priorizada),
            "compras_criticas": len(compras_criticas),
            "recepciones_previstas": len(recepciones_previstas),
            "descongelaciones": len(descongelaciones),
            "alertas": len(alertas_jornada) + len(alertas_stock),
            "incidencias": len(incidencias),
            "produccion_viva_planes": int(produccion_viva.get("planes_activos", 0)),
            "recepciones_rp3_hoy": int(recepciones_rp3.get("recepciones_hoy", 0)),
        }
        return {
            "pregunta": "¿Qué tiene que hacer el jefe de cocina durante los próximos minutos?",
            "mensaje_operativo": self._mensaje_operativo(prioridades, contexto),
            "eventos_hoy": eventos_hoy,
            "cronologia": cronologia,
            "produccion_priorizada": produccion_priorizada,
            "compras_criticas": compras_criticas,
            "recepciones_previstas": recepciones_previstas,
            "productos_descongelar": descongelaciones,
            "alertas": alertas_jornada + alertas_stock,
            "personal": personal,
            "alergenos": alergenos,
            "incidencias": incidencias,
            "recepciones_rp3": recepciones_rp3,
            "produccion_viva": produccion_viva,
            "prioridades": prioridades,
            "orden_automatico": {
                "criterios": [
                    "hora del evento",
                    "duración",
                    "dependencias",
                    "tiempos de reposo",
                    "tiempos de abatimiento",
                    "tiempos de descongelación",
                ],
                "fuente": "JornadaPiloto12 + servicios operativos existentes",
            },
            "solo_lectura": True,
        }

    def _eventos_hoy(self, eventos: dict[str, dict[str, Any]], hoy: date) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for evt in eventos.values():
            f = self._parse_fecha(evt.get("fecha"))
            if f != hoy:
                continue
            estado = str(evt.get("estado") or "pendiente")
            out.append({
                "id": evt.get("id") or evt.get("id_evento"),
                "nombre": evt.get("nombre", ""),
                "fecha": evt.get("fecha", ""),
                "hora": evt.get("hora") or evt.get("hora_inicio") or "13:00",
                "pax": int(evt.get("pax") or evt.get("personas") or 0),
                "estado": estado,
            })
        out.sort(key=lambda x: (x.get("hora") or "23:59", x.get("nombre") or ""))
        return out

    def _cronologia(self, eventos_hoy: list[dict[str, Any]]) -> list[dict[str, Any]]:
        timeline: list[dict[str, Any]] = []
        for evento in eventos_hoy:
            cronograma = generar_cronograma_evento(
                {
                    "id_evento": evento.get("id"),
                    "fecha": evento.get("fecha"),
                    "hora": evento.get("hora"),
                    "personas": evento.get("pax"),
                },
                produccion=[],
            )
            for tarea in (cronograma.get("tareas") or [])[:4]:
                timeline.append({
                    "evento_id": evento.get("id"),
                    "evento": evento.get("nombre"),
                    "inicio": tarea.get("inicio"),
                    "fin": tarea.get("fin"),
                    "titulo": tarea.get("titulo"),
                    "area": tarea.get("area"),
                })
        timeline.sort(key=lambda x: x.get("inicio") or "")
        return timeline[:20]

    def _compras_criticas(
        self,
        eventos_hoy: list[dict[str, Any]],
        menus: list[dict[str, Any]],
        stock: list[dict[str, Any]],
        pedidos: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        stock_dict: dict[str, float] = {}
        for item in stock:
            nombre = str(item.get("articulo") or item.get("nombre") or "").strip()
            if not nombre:
                continue
            stock_dict[nombre] = float(item.get("stock_actual") or item.get("cantidad") or 0)

        abiertos = [
            p for p in pedidos
            if str(p.get("estado") or "").lower() not in {"recibido", "cerrado", "cancelado"}
        ]

        out: list[dict[str, Any]] = []
        menu = menus[0] if menus else {}
        for evento in eventos_hoy:
            evento_ctx = {
                "id_evento": evento.get("id"),
                "nombre": evento.get("nombre"),
                "personas": evento.get("pax"),
                "menus": [menu] if menu else [],
            }
            necesidades = calcular_necesidades_evento(evento_ctx, menu=menu if menu else None)
            faltantes = [x for x in comparar_con_stock(necesidades, stock=stock_dict) if x.get("estado") == "comprar"]
            for faltante in faltantes:
                out.append({
                    "evento": evento.get("nombre"),
                    "articulo": faltante.get("articulo"),
                    "cantidad_a_comprar": faltante.get("cantidad_a_comprar"),
                    "unidad": faltante.get("unidad"),
                    "stock_disponible": faltante.get("stock_disponible"),
                    "estado": "critico" if float(faltante.get("cantidad_a_comprar") or 0) > 0 else "ok",
                })
        for pedido in abiertos:
            out.append({
                "evento": "sin_evento",
                "articulo": f"Pedido pendiente {pedido.get('id')}",
                "cantidad_a_comprar": pedido.get("total_lineas", len(pedido.get("lineas", []))),
                "unidad": "líneas",
                "stock_disponible": 0,
                "estado": "critico",
            })
        return out[:20]

    def _recepciones_previstas(self, pedidos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        previstas = []
        for pedido in pedidos:
            estado = str(pedido.get("estado") or "").lower()
            if estado in {"recibido", "cerrado", "cancelado"}:
                continue
            previstas.append({
                "pedido_id": pedido.get("id"),
                "proveedor": pedido.get("proveedor", ""),
                "estado": pedido.get("estado", ""),
                "lineas": pedido.get("total_lineas", len(pedido.get("lineas", []))),
                "fecha_prevista": pedido.get("entrega_prevista") or pedido.get("enviado_en") or pedido.get("creado_en") or "",
            })
        return previstas

    def _descongelaciones(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for item in items:
            minutos = int(item.get("descongelacion_min") or 0)
            if minutos <= 0:
                continue
            out.append({
                "tarea_id": item.get("id"),
                "titulo": item.get("titulo"),
                "minutos_descongelacion": minutos,
                "servicio_en_min": item.get("servicio_en_min"),
                "prioridad": item.get("prioridad_texto"),
            })
        out.sort(key=lambda x: (x.get("servicio_en_min") if isinstance(x.get("servicio_en_min"), int) else 999999, -int(x.get("minutos_descongelacion") or 0)))
        return out

    def _personal_eventos(self, eventos_hoy: list[dict[str, Any]], menus: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        menu = menus[0] if menus else None
        for evento in eventos_hoy:
            plan = calcular_personal_evento(
                {
                    "id_evento": evento.get("id"),
                    "personas": evento.get("pax"),
                    "tipo": evento.get("nombre"),
                },
                menu=menu,
                tipo_servicio="catering",
                complejidad="media",
            )
            if not plan.get("ok"):
                continue
            out.append({
                "evento": evento.get("nombre"),
                "total_equipo": plan.get("total_personas_equipo"),
                "roles": plan.get("personal", {}),
            })
        return out

    def _alertas_stock(self) -> list[dict[str, str]]:
        informe = AlertasStockBajo434(self.stock_path).generar()
        alertas = []
        for alerta in informe.alertas[:8]:
            nivel = "ALTA" if alerta.prioridad in {"critica", "alta"} else "MEDIA"
            alertas.append({
                "nivel": nivel,
                "codigo": "STOCK_BAJO",
                "mensaje": f"{alerta.articulo}: faltan {alerta.diferencia} {alerta.unidad} para mínimo.",
            })
        return alertas

    def _incidencias(
        self,
        items: list[dict[str, Any]],
        compras_criticas: list[dict[str, Any]],
        recepciones_previstas: list[dict[str, Any]],
        personal: list[dict[str, Any]],
        eventos_hoy: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        planning = {
            "ok": True,
            "plan": [
                {
                    "codigo": x.get("id"),
                    "nombre": x.get("titulo"),
                    "bloqueado_por": ["BLOQUEO"] if x.get("estado") == "BLOQUEADA" else [],
                }
                for x in items
            ],
        }
        contexto = {
            "stock": [
                {
                    "nombre": c.get("articulo"),
                    "disponible": c.get("stock_disponible"),
                    "necesario": (float(c.get("stock_disponible") or 0) + float(c.get("cantidad_a_comprar") or 0)),
                    "imprescindible": True,
                }
                for c in compras_criticas
            ],
            "tareas": [
                {
                    "codigo": x.get("id"),
                    "nombre": x.get("titulo"),
                    "retrasada": x.get("estado") == "BLOQUEADA",
                    "bloquea_servicio": bool(isinstance(x.get("servicio_en_min"), int) and x.get("servicio_en_min") <= 180),
                }
                for x in items
            ],
            "personal": {
                "disponibles": sum(int(p.get("total_equipo") or 0) for p in personal),
                "necesarios": sum(int(p.get("total_equipo") or 0) for p in personal),
            },
            "conflictos": [
                {
                    "tipo": "recepcion_pendiente",
                    "nivel": "alto",
                    "titulo": f"Recepción pendiente: {r.get('proveedor')}",
                    "detalle": f"Pedido {r.get('pedido_id')} pendiente con estado {r.get('estado')}",
                }
                for r in recepciones_previstas
            ],
        }
        resultado = detectar_incidencias_operativas(planning, prioridades={}, contexto=contexto)
        return resultado.get("incidencias", [])[:12]

    def _alergenos(
        self,
        eventos_hoy: list[dict[str, Any]],
        articulos: list[dict[str, Any]],
        menus: list[dict[str, Any]],
    ) -> dict[str, Any]:
        observaciones = []
        for evento in eventos_hoy:
            texto = str(evento.get("nombre") or "")
            if texto:
                pass
        for evento in eventos_hoy:
            # El campo de observaciones puede contener recordatorios de alérgenos.
            origen = next((e for e in self._indexar_eventos().values() if str(e.get("id") or e.get("id_evento")) == str(evento.get("id"))), None)
            obs = str((origen or {}).get("observaciones") or "")
            if "alergen" in obs.lower() or "alérgen" in obs.lower():
                observaciones.append({"evento": evento.get("nombre"), "mensaje": obs})

        articulos_con_alergenos = []
        for art in articulos:
            alerg = art.get("alergenos")
            if alerg:
                articulos_con_alergenos.append({
                    "articulo": art.get("nombre") or art.get("articulo") or art.get("codigo"),
                    "alergenos": alerg,
                })
        menus_con_componentes = sum(len(m.get("platos", [])) for m in menus)
        return {
            "pendientes_revision_evento": observaciones,
            "articulos_con_alergenos": articulos_con_alergenos[:12],
            "menus_componentes_revisar": menus_con_componentes,
            "estado": "revisar" if observaciones or articulos_con_alergenos else "sin_alertas",
        }

    @staticmethod
    def _mensaje_operativo(prioridades: list[dict[str, Any]], contexto: dict[str, int]) -> str:
        if not prioridades:
            return "No hay tareas abiertas en la bandeja. Validar eventos y recepciones de hoy."
        top = prioridades[0]
        return (
            f"Empieza por {top.get('titulo')} y mantén el foco en servicio próximo. "
            f"Eventos hoy: {contexto.get('eventos_hoy', 0)}, compras críticas: {contexto.get('compras_criticas', 0)}, "
            f"recepciones previstas: {contexto.get('recepciones_previstas', 0)}, recepciones aplicadas hoy: {contexto.get('recepciones_rp3_hoy', 0)}, planes vivos: {contexto.get('produccion_viva_planes', 0)}."
        )

    def _resumen_recepciones_rp3(self) -> dict[str, Any]:
        data = self._load_json(self.recepciones_rp3_path, [])
        if not isinstance(data, list):
            return {"recepciones_hoy": 0, "lineas_recibidas_hoy": 0, "incidencias_hoy": 0, "incidencias": []}
        hoy = date.today().isoformat()
        regs_hoy = []
        for r in data:
            fecha = str(r.get("creado_en") or "")[:10]
            if fecha == hoy:
                regs_hoy.append(r)
        incidencias = []
        for r in regs_hoy:
            for inc in r.get("incidencias", []) or []:
                incidencias.append({
                    "tipo": "recepcion_rp3",
                    "nivel": "medio",
                    "titulo": f"Recepción {r.get('pedido_id', '')}",
                    "detalle": f"{inc.get('tipo')}: {inc.get('detalle')}",
                })
        return {
            "recepciones_hoy": len(regs_hoy),
            "lineas_recibidas_hoy": sum(len(r.get("entradas_stock", []) or []) for r in regs_hoy),
            "incidencias_hoy": sum(len(r.get("incidencias", []) or []) for r in regs_hoy),
            "incidencias": incidencias[:20],
        }

    @staticmethod
    def _resumen_produccion_viva(planes_raw: list[dict[str, Any]]) -> dict[str, Any]:
        estados_activos = {"en_curso", "en_preparacion", "en_proceso", "en_espera", "incidencia"}
        totales = {
            "planes_activos": 0,
            "tareas_total": 0,
            "tareas_activas": 0,
            "tareas_completadas": 0,
            "tareas_pendientes": 0,
            "tareas_bloqueadas": 0,
            "incidencias_abiertas": 0,
            "retraso_min_total": 0,
            "progreso_promedio": 0.0,
            "siguiente_accion": "Sin planes activos de producción.",
            "siguiente_tarea_id": "",
        }
        if not planes_raw:
            return totales

        planes_uso = [
            p for p in planes_raw
            if str(p.get("estado") or "").lower() not in {"finalizado", "cancelado"}
        ]
        if not planes_uso:
            return totales

        totales["planes_activos"] = len(planes_uso)
        acumulado_progreso = 0.0
        acumulado_tareas = 0
        candidatas: list[tuple[int, int, str, dict[str, Any]]] = []

        for plan in planes_uso:
            for tarea in plan.get("tareas", []) or []:
                acumulado_tareas += 1
                estado = str(tarea.get("estado_ejecucion") or "pendiente").lower()
                prioridad = int(tarea.get("prioridad") or 50)
                progreso = float(tarea.get("progreso_manual") or 0)
                retraso = int(tarea.get("retraso_min") or 0)
                bloqueo = str(tarea.get("bloqueo") or "").strip()
                incidencias = list(tarea.get("incidencias") or [])

                acumulado_progreso += progreso
                totales["retraso_min_total"] += max(0, retraso)
                totales["incidencias_abiertas"] += len(incidencias)

                if estado == "finalizada":
                    totales["tareas_completadas"] += 1
                else:
                    totales["tareas_pendientes"] += 1
                if estado in estados_activos:
                    totales["tareas_activas"] += 1
                if bloqueo:
                    totales["tareas_bloqueadas"] += 1

                if estado != "finalizada" and not bloqueo:
                    estado_rank = {"en_proceso": 0, "en_preparacion": 1, "en_espera": 2, "pausada": 3, "lista": 4, "pendiente": 5}.get(estado, 6)
                    candidatas.append((estado_rank, -prioridad, str(tarea.get("titulo") or ""), tarea))

        totales["tareas_total"] = acumulado_tareas
        totales["progreso_promedio"] = round(acumulado_progreso / acumulado_tareas, 1) if acumulado_tareas else 0.0
        if candidatas:
            _, _, _, tarea = sorted(candidatas)[0]
            totales["siguiente_tarea_id"] = str(tarea.get("id") or "")
            totales["siguiente_accion"] = f"Seguir con {tarea.get('titulo') or 'tarea prioritaria'}"
        return totales

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
                return f"Producción prioritaria con {pasivo} min de tiempo pasivo aprovechable."
            return "Producción pendiente ordenada por la prioridad registrada."
        if item.get("tipo") == "INCIDENCIA_PROVEEDOR":
            return "Conviene dejar registrada la incidencia antes de cerrar el día."
        if item.get("tipo") == "EVENTO":
            dias = item.get("evento", {}).get("dias_restantes")
            if dias is not None:
                return f"Evento a {dias} día(s); revisar antes de generar producción o compras."
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
        out: dict[str, dict[str, Any]] = {}
        if not isinstance(data, list):
            return out
        for item in data:
            if not isinstance(item, dict):
                continue
            key = str(item.get("id") or item.get("id_evento") or "")
            if key:
                out[key] = item
        return out

    @staticmethod
    def _fecha_hora_evento(fecha: Any, hora: Any) -> datetime | None:
        fecha_txt = str(fecha or "").strip()
        hora_txt = str(hora or "13:00").strip()[:5]
        if not fecha_txt:
            return None
        for fmt in ("%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M"):
            try:
                return datetime.strptime(f"{fecha_txt} {hora_txt}", fmt)
            except ValueError:
                continue
        return None

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
        "PILOTO-1.2 — MI JORNADA",
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
