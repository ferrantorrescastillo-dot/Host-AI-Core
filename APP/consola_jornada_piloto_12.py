from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from APP.consola_bandeja_trabajo_piloto_11 import ConsolaBandejaTrabajoPiloto11
from APP.consola_produccion_guiada_piloto_13 import ConsolaProduccionGuiadaPiloto13
from CORE.host_ai_core import HostAICore
from SERVICIOS.cierre_operativo_rp4 import CierreOperativoRP4, formatear_diagnostico_rp4
from SERVICIOS.jornada_piloto_12 import JornadaPiloto12, formatear_diagnostico_piloto12


ICONOS = {
    "MUY_URGENTE": "[MUY URGENTE]",
    "HOY": "[HOY]",
    "ESTA_SEMANA": "[ESTA SEMANA]",
    "CUANDO_PUEDAS": "[CUANDO PUEDAS]",
}

TIPOS_TEXTO = {
    "PRODUCCION": "Producción",
    "RECEPCION": "Recepciones",
    "EVENTO": "Eventos",
    "PEDIDO": "Compras / pedidos",
    "STOCK": "Stock",
    "INCIDENCIA_PROVEEDOR": "Incidencias de proveedor",
    "DOCUMENTO": "Documentos",
    "GENERAL": "Otras tareas",
}


class ConsolaJornadaPiloto12:
    def __init__(self, base_dir: Path | str):
        self.base_dir = Path(base_dir)
        self.service = JornadaPiloto12(self.base_dir)
        self.rp4 = CierreOperativoRP4(self.base_dir)

    def ejecutar(self, input_fn: Callable[[str], str] = input, print_fn: Callable[..., None] = print) -> None:
        while True:
            jornada = self.service.construir()
            self._mostrar_portada(jornada, print_fn)
            print_fn("\n¿Qué quieres hacer?")
            print_fn("1. Ver el plan completo del día")
            print_fn("2. Ver tareas agrupadas por área")
            print_fn("3. Abrir la bandeja de trabajo")
            print_fn("4. Recalcular la jornada")
            print_fn("5. Abrir Producción Viva")
            print_fn("6. Cierre operativo y preparar mañana (RP-4)")
            print_fn("9. Diagnóstico aislado")
            print_fn("0. Volver")
            op = input_fn("Elige una opción: ").strip()
            if op == "1":
                self._mostrar_plan(jornada, print_fn)
            elif op == "2":
                self._mostrar_grupos(jornada, print_fn)
            elif op == "3":
                ConsolaBandejaTrabajoPiloto11(self.base_dir).ejecutar(input_fn=input_fn, print_fn=print_fn)
            elif op == "4":
                print_fn("Jornada recalculada con el estado actual de la bandeja.")
            elif op == "5":
                core = HostAICore(self.base_dir)
                ConsolaProduccionGuiadaPiloto13(core).ejecutar(input_fn=input_fn, print_fn=print_fn)
            elif op == "6":
                self._menu_rp4(input_fn, print_fn)
            elif op == "9":
                print_fn(formatear_diagnostico_piloto12(self.service.diagnostico()))
            elif op == "0":
                return
            else:
                print_fn("Opción no válida.")

    def _mostrar_portada(self, jornada: dict, print_fn) -> None:
        briefing = jornada.get("briefing_apertura", {})
        r = jornada["resumen"]
        print_fn("\n" + "=" * 78)
        print_fn("APERTURA RESTAURANTE — BRIEFING OPERATIVO")
        print_fn("=" * 78)
        print_fn(f"Fecha: {jornada['fecha']} | Tareas abiertas: {r['abiertas']}")
        if briefing:
            print_fn(briefing.get("pregunta", ""))
            print_fn(f"Respuesta: {briefing.get('mensaje_operativo', '')}")
        print_fn(f"Muy urgentes: {r['muy_urgentes']} | Para hoy: {r['hoy']} | Esta semana: {r['esta_semana']} | Cuando puedas: {r['cuando_puedas']}")

        if briefing:
            self._mostrar_briefing_apertura(briefing, print_fn)

        if jornada["alertas"]:
            print_fn("\nAVISOS")
            for alerta in jornada["alertas"]:
                print_fn(f"- [{alerta['nivel']}] {alerta['mensaje']}")

        print_fn("\nQUÉ HARÍA PRIMERO")
        recomendaciones = jornada["recomendaciones"][:5]
        if not recomendaciones:
            print_fn("No hay trabajo pendiente registrado.")
        else:
            for i, rec in enumerate(recomendaciones, 1):
                print_fn(f"{i}. {rec['titulo']} · {rec['prioridad']}")
                print_fn(f"   Motivo: {rec['motivo']}")

        t = jornada["tiempos"]
        print_fn("\nTIEMPO REGISTRADO")
        print_fn(f"Activo conocido: {self._hm(t['activo_conocido_min'])} | Pasivo conocido: {self._hm(t['pasivo_conocido_min'])}")
        if t["tareas_sin_duracion"]:
            print_fn(f"Tareas sin tiempo registrado: {t['tareas_sin_duracion']}")
        if t["fin_estimado_por_trabajo_activo"]:
            hora = datetime.fromisoformat(t["fin_estimado_por_trabajo_activo"]).strftime("%H:%M")
            print_fn(f"Fin aproximado según trabajo activo conocido: {hora}")
        print_fn("Nota: no se inventan tiempos; la estimación usa únicamente datos registrados.")

    def _mostrar_briefing_apertura(self, briefing: dict, print_fn) -> None:
        print_fn("\nSECCIONES DE APERTURA")
        print_fn(f"- Eventos de hoy: {len(briefing.get('eventos_hoy', []))}")
        print_fn(f"- Cronología: {len(briefing.get('cronologia', []))} hitos")
        print_fn(f"- Producción priorizada: {len(briefing.get('produccion_priorizada', []))}")
        print_fn(f"- Compras críticas: {len(briefing.get('compras_criticas', []))}")
        print_fn(f"- Recepciones previstas: {len(briefing.get('recepciones_previstas', []))}")
        print_fn(f"- Productos a descongelar: {len(briefing.get('productos_descongelar', []))}")
        print_fn(f"- Alertas: {len(briefing.get('alertas', []))}")
        print_fn(f"- Personal: {len(briefing.get('personal', []))} evento(s)")
        print_fn(f"- Alérgenos: {briefing.get('alergenos', {}).get('estado', 'sin datos')}")
        print_fn(f"- Incidencias: {len(briefing.get('incidencias', []))}")
        print_fn(f"- Prioridades: {len(briefing.get('prioridades', []))}")

        viva = briefing.get("produccion_viva") or {}
        if viva:
            print_fn("\nPRODUCCIÓN VIVA")
            print_fn(f"- Planes activos: {viva.get('planes_activos', 0)}")
            print_fn(f"- Tareas: {viva.get('tareas_total', 0)} | Activas: {viva.get('tareas_activas', 0)} | Completadas: {viva.get('tareas_completadas', 0)} | Pendientes: {viva.get('tareas_pendientes', 0)}")
            print_fn(f"- Bloqueadas: {viva.get('tareas_bloqueadas', 0)} | Incidencias: {viva.get('incidencias_abiertas', 0)} | Retraso acumulado: {viva.get('retraso_min_total', 0)} min")
            print_fn(f"- Progreso global: {viva.get('progreso_promedio', 0)}%")
            print_fn(f"- Siguiente acción: {viva.get('siguiente_accion', 'Sin acciones')}")

        rec = briefing.get("recepciones_rp3") or {}
        if rec:
            print_fn("\nRECEPCIONES RP-3")
            print_fn(f"- Recepciones aplicadas hoy: {rec.get('recepciones_hoy', 0)}")
            print_fn(f"- Líneas recibidas hoy: {rec.get('lineas_recibidas_hoy', 0)}")
            print_fn(f"- Incidencias de recepción hoy: {rec.get('incidencias_hoy', 0)}")

        rp4 = briefing.get("plan_manana_rp4") or {}
        if rp4.get("disponible"):
            print_fn("\nPLAN CONFIRMADO RP-4 (PREPARADO AYER)")
            print_fn(f"- Fecha objetivo: {rp4.get('fecha_objetivo')}")
            print_fn(f"- Estado: {rp4.get('estado')}")
            print_fn(f"- Eventos: {rp4.get('eventos', 0)} | Tareas: {rp4.get('tareas', 0)}")
            print_fn(f"- Compras: {rp4.get('compras', 0)} | Recepciones: {rp4.get('recepciones', 0)} | Descongelaciones: {rp4.get('descongelaciones', 0)}")
            print_fn(f"- Cronología: {rp4.get('cronologia', 0)} hitos | Alertas: {rp4.get('alertas', 0)} | Bloqueos: {rp4.get('bloqueos', 0)}")
            if rp4.get("personal_revision_manual"):
                print_fn("- Personal: revisión manual pendiente")

        prioridades = briefing.get("prioridades", [])[:5]
        if prioridades:
            print_fn("\nPRIORIDADES AUTOMÁTICAS (próximos minutos)")
            for i, item in enumerate(prioridades, 1):
                etiqueta = ICONOS.get(item.get("prioridad_codigo", ""), "")
                print_fn(f"{i}. {etiqueta} {item.get('titulo')} | {TIPOS_TEXTO.get(item.get('tipo'), item.get('tipo'))}")

    def _mostrar_plan(self, jornada: dict, print_fn) -> None:
        print_fn("\nPLAN DEL DÍA")
        if not jornada["tareas"]:
            print_fn("No hay tareas abiertas.")
            return
        for i, tarea in enumerate(jornada["tareas"], 1):
            etiqueta = ICONOS.get(tarea["prioridad_codigo"], "")
            tiempo = self._hm(tarea.get("duracion_total_min"))
            print_fn(f"{i}. {etiqueta} {tarea['titulo']} | {TIPOS_TEXTO.get(tarea.get('tipo'), tarea.get('tipo'))} | {tiempo}")
            if tarea.get("descripcion"):
                print_fn(f"   {tarea['descripcion']}")
            if tarea.get("evento"):
                evt = tarea["evento"]
                print_fn(f"   Evento: {evt.get('nombre')} | Fecha: {evt.get('fecha')} | {evt.get('pax', 0)} pax")

    def _mostrar_grupos(self, jornada: dict, print_fn) -> None:
        print_fn("\nTRABAJO POR ÁREAS")
        if not jornada["grupos"]:
            print_fn("No hay tareas abiertas.")
            return
        orden = ["PRODUCCION", "RECEPCION", "EVENTO", "PEDIDO", "STOCK", "INCIDENCIA_PROVEEDOR", "DOCUMENTO", "GENERAL"]
        for tipo in orden:
            tareas = jornada["grupos"].get(tipo, [])
            if not tareas:
                continue
            print_fn(f"\n{TIPOS_TEXTO.get(tipo, tipo)} ({len(tareas)})")
            for tarea in tareas:
                print_fn(f"- {ICONOS.get(tarea['prioridad_codigo'], '')} {tarea['titulo']}")

    @staticmethod
    def _hm(minutes):
        if minutes is None:
            return "sin tiempo"
        h, m = divmod(int(minutes), 60)
        if h and m: return f"{h} h {m} min"
        if h: return f"{h} h"
        return f"{m} min"

    def _menu_rp4(self, input_fn, print_fn) -> None:
        while True:
            print_fn("\nRP-4 — PREPARAR MAÑANA")
            print_fn("1. Cerrar jornada")
            print_fn("2. Preparar mañana")
            print_fn("3. Ver propuesta")
            print_fn("4. Ver bloqueos")
            print_fn("5. Ver descongelaciones")
            print_fn("6. Ver compras")
            print_fn("7. Ver cronología")
            print_fn("8. Ver asignación")
            print_fn("9. Editar decisiones")
            print_fn("10. Confirmar plan")
            print_fn("11. Regenerar")
            print_fn("12. Abrir briefing de mañana en modo vista previa")
            print_fn("99. Diagnóstico RP-4")
            print_fn("0. Volver")
            op = input_fn("Elige una opción: ").strip()
            if op == "1":
                cierre = self.rp4.cerrar_jornada()
                print_fn(f"Cierre: {cierre.get('estado')} | Producción abierta: {cierre.get('tareas_produccion_abiertas', 0)} | Incidencias: {cierre.get('incidencias_abiertas', 0)}")
            elif op == "2":
                plan = self.rp4.preparar_manana()
                print_fn(f"Propuesta generada: {plan.get('id')} | Fecha objetivo: {plan.get('fecha_objetivo')} | Alertas: {len(plan.get('alertas', []))} | Bloqueos: {len(plan.get('bloqueos', []))}")
            elif op == "3":
                plan = self.rp4.ver_propuesta()
                if not plan:
                    print_fn("No hay propuesta RP-4.")
                else:
                    print_fn(f"Plan: {plan.get('id')} | Estado: {plan.get('estado')} | Fecha: {plan.get('fecha_objetivo')}")
                    print_fn(f"Eventos mañana: {len((plan.get('eventos') or {}).get('manana', []))} | Tareas: {len(plan.get('tareas', []))}")
            elif op == "4":
                plan = self.rp4.ver_propuesta()
                bloques = list((plan or {}).get("bloqueos", []))
                if not bloques:
                    print_fn("No hay bloqueos en la propuesta actual.")
                else:
                    for i, b in enumerate(bloques, 1):
                        print_fn(f"{i}. {b.get('tipo')}: {b.get('detalle')}")
            elif op == "5":
                plan = self.rp4.ver_propuesta()
                items = list((plan or {}).get("descongelaciones", []))
                if not items:
                    print_fn("No hay descongelaciones propuestas.")
                else:
                    for i, d in enumerate(items, 1):
                        print_fn(f"{i}. {d.get('producto')} | límite {d.get('momento_limite')} | estado {d.get('estado')}")
            elif op == "6":
                plan = self.rp4.ver_propuesta()
                items = list(((plan or {}).get("compras") or {}).get("lineas", []))
                if not items:
                    print_fn("No hay compras propuestas.")
                else:
                    for i, c in enumerate(items, 1):
                        print_fn(f"{i}. {c.get('articulo')} | sin cubrir {c.get('cantidad_sin_cubrir')} {c.get('unidad')} | proveedor {c.get('proveedor_sugerido')}")
            elif op == "7":
                plan = self.rp4.ver_propuesta()
                items = list((plan or {}).get("cronologia", []))
                if not items:
                    print_fn("No hay cronología propuesta.")
                else:
                    for i, c in enumerate(items, 1):
                        print_fn(f"{i}. {c.get('hora')} {c.get('titulo')} ({c.get('tipo')})")
            elif op == "8":
                plan = self.rp4.ver_propuesta()
                personal = (plan or {}).get("personal", {})
                print_fn(f"Modo personal: {personal.get('modo', 'sin datos')}")
                for i, a in enumerate(personal.get("asignacion", []), 1):
                    if isinstance(a, dict):
                        print_fn(f"{i}. {a.get('evento', 'evento')} -> {a.get('responsable', a.get('roles', {}))}")
            elif op == "9":
                plan = self.rp4.ver_propuesta()
                if not plan:
                    print_fn("No hay propuesta para editar.")
                    continue
                target = input_fn("Target (tareas/compras/descongelaciones/cronologia/recepciones): ").strip().lower()
                item_id = input_fn("ID del elemento: ").strip()
                action = input_fn("Acción (confirmar/excluir/urgente/aplazar/prioridad/reasignar/adelantar/bloqueo_revisado): ").strip().lower()
                value = input_fn("Valor opcional: ").strip()
                edit = {"target": target, "id": item_id, "action": action, "value": value}
                nuevo = self.rp4.confirmar_plan(plan.get("id"), confirmacion="CONFIRMAR", parcial=True, decisiones=[edit])
                print_fn(f"Decisión aplicada sobre {target}:{item_id}. Estado: {nuevo.get('estado')}")
            elif op == "10":
                plan = self.rp4.ver_propuesta()
                if not plan:
                    print_fn("No hay propuesta para confirmar.")
                    continue
                parcial = input_fn("¿Confirmación parcial? (s/n): ").strip().lower() in {"s", "si", "sí"}
                token = input_fn("Escribe CONFIRMAR: ").strip()
                confirmado = self.rp4.confirmar_plan(plan.get("id"), confirmacion=token, parcial=parcial)
                print_fn(f"Plan confirmado: {confirmado.get('id')} | Estado: {confirmado.get('estado')}")
            elif op == "11":
                plan = self.rp4.preparar_manana()
                print_fn(f"Plan regenerado: {plan.get('id')} | fingerprint: {str(plan.get('fingerprint_entradas'))[:12]}")
            elif op == "12":
                plan = self.rp4.ver_propuesta()
                if not plan:
                    print_fn("No hay plan para vista previa.")
                    continue
                vista = self.rp4.vista_previa_briefing(plan.get("id"))
                print_fn("VISTA PREVIA BRIEFING DE MAÑANA")
                print_fn(f"Fecha: {vista.get('fecha_objetivo')} | Eventos: {len(vista.get('eventos', []))} | Cronología: {len(vista.get('cronologia', []))}")
                print_fn(f"Producción: {vista.get('produccion', {}).get('pendientes', 0)} pendientes | Compras: {vista.get('compras', {}).get('total', 0)}")
                print_fn(f"Recepciones: {len(vista.get('recepciones', []))} | Descongelaciones: {len(vista.get('descongelaciones', []))}")
                print_fn(f"Alertas: {len(vista.get('alertas', []))} | Bloqueos: {len(vista.get('bloqueos', []))}")
            elif op == "99":
                print_fn(formatear_diagnostico_rp4(self.rp4.diagnostico()))
            elif op == "0":
                return
            else:
                print_fn("Opción no válida.")


__all__ = ["ConsolaJornadaPiloto12"]
