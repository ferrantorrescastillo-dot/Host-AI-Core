from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from APP.consola_bandeja_trabajo_piloto_11 import ConsolaBandejaTrabajoPiloto11
from APP.consola_produccion_guiada_piloto_13 import ConsolaProduccionGuiadaPiloto13
from CORE.host_ai_core import HostAICore
from SERVICIOS.cierre_operativo_rp4 import CierreOperativoRP4, formatear_diagnostico_rp4
from SERVICIOS.incidencias_replanificacion_rp5 import IncidenciasReplanificacionRP5, formatear_diagnostico_rp5
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
        self._rp5 = None

    def ejecutar(self, input_fn: Callable[[str], str] = input, print_fn: Callable[..., None] = print) -> None:
        while True:
            jornada = self.service.construir()
            self._mostrar_portada(jornada, print_fn)
            print_fn("\n¿Qué quieres hacer?")
            print_fn("ACCIONES HABITUALES")
            print_fn("5. Abrir Producción Viva")
            print_fn("6. Cierre operativo y preparar mañana (RP-4)")
            print_fn("7. Incidencias y replanificación (RP-5)")
            print_fn("3. Abrir la bandeja de trabajo")
            print_fn("\nCONSULTAR EL DÍA")
            print_fn("1. Ver el plan completo del día")
            print_fn("2. Ver el trabajo agrupado por área")
            print_fn("4. Actualizar la jornada")
            print_fn("\nOPCIONES TÉCNICAS")
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
            elif op == "7":
                self._menu_rp5(input_fn, print_fn)
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
        print_fn("APERTURA DE COCINA")
        print_fn("=" * 78)
        print_fn(f"{jornada['fecha']} | {r['abiertas']} trabajos abiertos")

        recomendaciones = list(jornada.get("recomendaciones") or [])
        print_fn("\nQUÉ HAGO PRIMERO")
        if recomendaciones:
            principal = recomendaciones[0]
            print_fn(f"> {principal.get('titulo')}")
            print_fn(f"  {principal.get('motivo')}")
        elif briefing.get("mensaje_operativo"):
            print_fn(f"> {briefing.get('mensaje_operativo')}")
        else:
            print_fn("> No hay trabajo abierto. Revisa los eventos y recepciones de hoy antes de empezar.")

        self._mostrar_bloqueos_apertura(briefing, jornada.get("alertas") or [], print_fn)
        self._mostrar_produccion_apertura(briefing, print_fn)
        self._mostrar_adelantables(recomendaciones[1:], briefing, print_fn)
        self._mostrar_eventos_atencion(briefing, print_fn)

        print_fn("\nRESUMEN DEL DÍA")
        print_fn(f"Muy urgente: {r['muy_urgentes']} | Para hoy: {r['hoy']} | Esta semana: {r['esta_semana']}")
        if briefing:
            self._mostrar_briefing_apertura(briefing, print_fn)

        t = jornada["tiempos"]
        print_fn("\nTIEMPO DE COCINA REGISTRADO")
        print_fn(f"Activo conocido: {self._hm(t['activo_conocido_min'])} | Pasivo conocido: {self._hm(t['pasivo_conocido_min'])}")
        if t["tareas_sin_duracion"]:
            print_fn(f"Tareas sin tiempo registrado: {t['tareas_sin_duracion']}")
        if t["fin_estimado_por_trabajo_activo"]:
            hora = datetime.fromisoformat(t["fin_estimado_por_trabajo_activo"]).strftime("%H:%M")
            print_fn(f"Fin aproximado según trabajo activo conocido: {hora}")
        print_fn("Estimación basada solo en tiempos registrados.")

    @staticmethod
    def _mostrar_bloqueos_apertura(briefing: dict, alertas_jornada: list[dict], print_fn) -> None:
        incidencias = list(briefing.get("incidencias") or [])
        alertas = list(briefing.get("alertas") or []) + list(alertas_jornada)
        print_fn("\nQUÉ PUEDE IMPEDIRME TRABAJAR")
        if not incidencias and not alertas:
            print_fn("> Nada crítico detectado. Puedes empezar por la recomendación principal.")
            return
        for item in incidencias[:3]:
            print_fn(f"- {item.get('detalle') or item.get('mensaje') or item.get('titulo') or 'Revisión pendiente'}")
        for item in alertas[:3]:
            print_fn(f"- {item.get('mensaje') or item.get('detalle') or item.get('titulo') or 'Aviso pendiente'}")
        print_fn("> Resuelve primero lo que bloquee el servicio; revisa el resto después de arrancar.")

    @staticmethod
    def _mostrar_produccion_apertura(briefing: dict, print_fn) -> None:
        viva = briefing.get("produccion_viva") or {}
        priorizada = list(briefing.get("produccion_priorizada") or [])
        print_fn("\nQUÉ PRODUCCIÓN EMPIEZA AHORA")
        if str(viva.get("siguiente_accion") or "").strip():
            print_fn(f"> {viva.get('siguiente_accion')}")
        elif priorizada:
            print_fn(f"> Empieza por {priorizada[0].get('titulo')}.")
        else:
            print_fn("> No hay producción preparada. Revisa el plan o crea la producción necesaria.")

    @staticmethod
    def _mostrar_adelantables(recomendaciones: list[dict], briefing: dict, print_fn) -> None:
        print_fn("\nQUÉ PUEDO ADELANTAR")
        if recomendaciones:
            for item in recomendaciones[:2]:
                print_fn(f"- {item.get('titulo')}")
            return
        descongelar = list(briefing.get("productos_descongelar") or [])
        if descongelar:
            print_fn(f"- Deja preparado: {descongelar[0].get('titulo')}.")
        else:
            print_fn("- No hay adelantos registrados. Mantén el foco en la primera acción.")

    @staticmethod
    def _mostrar_eventos_atencion(briefing: dict, print_fn) -> None:
        eventos = list(briefing.get("eventos_hoy") or [])
        print_fn("\nEVENTOS QUE REQUIEREN ATENCIÓN")
        if not eventos:
            print_fn("> No hay eventos hoy. Revisa el plan de mañana al cerrar la jornada.")
            return
        for evento in eventos[:4]:
            print_fn(f"- {evento.get('hora') or 'sin hora'} · {evento.get('nombre')} · {evento.get('pax', 0)} pax")

    def _mostrar_briefing_apertura(self, briefing: dict, print_fn) -> None:
        print_fn("\nINFORMACIÓN DE APOYO")
        print_fn(
            f"Compras críticas: {len(briefing.get('compras_criticas', []))} | "
            f"Recepciones: {len(briefing.get('recepciones_previstas', []))} | "
            f"Descongelaciones: {len(briefing.get('productos_descongelar', []))} | "
            f"Alérgenos: {briefing.get('alergenos', {}).get('estado', 'sin datos')}"
        )

        viva = briefing.get("produccion_viva") or {}
        if viva:
            print_fn(f"Producción: {viva.get('progreso_promedio', 0)}% hecha | {viva.get('tareas_pendientes', 0)} por hacer | {viva.get('tareas_bloqueadas', 0)} bloqueadas")

        rec = briefing.get("recepciones_rp3") or {}
        if rec:
            print_fn("\nRECEPCIONES RP-3")
            print_fn(f"- Recepciones aplicadas hoy: {rec.get('recepciones_hoy', 0)}")
            print_fn(f"- Líneas recibidas hoy: {rec.get('lineas_recibidas_hoy', 0)}")
            print_fn(f"- Incidencias de recepción hoy: {rec.get('incidencias_hoy', 0)}")

        rp5 = briefing.get("incidencias_rp5") or {}
        if rp5.get("incidencias_abiertas", 0):
            print_fn("\nINCIDENCIAS RP-5")
            print_fn(f"- Incidencias abiertas: {rp5.get('incidencias_abiertas', 0)}")
            print_fn(f"- Cambios relevantes en briefing: {len(rp5.get('incidencias', []))}")

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

    def _mostrar_plan(self, jornada: dict, print_fn) -> None:
        print_fn("\nPLAN DEL DÍA")
        if not jornada["tareas"]:
            print_fn("No hay trabajos abiertos. Revisa eventos y recepciones; si están cubiertos, prepara mañana.")
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
            print_fn("No hay trabajos abiertos por área. Revisa eventos y recepciones antes de preparar mañana.")
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
            print_fn("ACCIONES HABITUALES")
            print_fn("2. Preparar el trabajo de mañana")
            print_fn("3. Ver qué queda preparado")
            print_fn("10. Confirmar el plan")
            print_fn("1. Cerrar la jornada de hoy")
            print_fn("\nREVISAR EL PLAN")
            print_fn("4. Ver bloqueos")
            print_fn("5. Ver descongelaciones")
            print_fn("6. Ver compras")
            print_fn("7. Ver cronología")
            print_fn("8. Ver asignación")
            print_fn("9. Editar decisiones")
            print_fn("12. Ver el briefing de mañana")
            print_fn("\nOPCIONES TÉCNICAS")
            print_fn("11. Regenerar la propuesta")
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
                    print_fn("Todavía no hay plan para mañana. Elige 2 para prepararlo con los datos actuales.")
                else:
                    print_fn(f"Plan: {plan.get('id')} | Estado: {plan.get('estado')} | Fecha: {plan.get('fecha_objetivo')}")
                    print_fn(f"Eventos mañana: {len((plan.get('eventos') or {}).get('manana', []))} | Tareas: {len(plan.get('tareas', []))}")
            elif op == "4":
                plan = self.rp4.ver_propuesta()
                bloques = list((plan or {}).get("bloqueos", []))
                if not bloques:
                    print_fn("No hay bloqueos. Puedes revisar compras o confirmar el plan.")
                else:
                    for i, b in enumerate(bloques, 1):
                        print_fn(f"{i}. {b.get('tipo')}: {b.get('detalle')}")
            elif op == "5":
                plan = self.rp4.ver_propuesta()
                items = list((plan or {}).get("descongelaciones", []))
                if not items:
                    print_fn("No hay descongelaciones propuestas. Continúa con compras o confirma el plan.")
                else:
                    for i, d in enumerate(items, 1):
                        print_fn(f"{i}. {d.get('producto')} | límite {d.get('momento_limite')} | estado {d.get('estado')}")
            elif op == "6":
                plan = self.rp4.ver_propuesta()
                items = list(((plan or {}).get("compras") or {}).get("lineas", []))
                if not items:
                    print_fn("No hay compras propuestas. El abastecimiento previsto no exige compras aquí.")
                else:
                    for i, c in enumerate(items, 1):
                        print_fn(f"{i}. {c.get('articulo')} | sin cubrir {c.get('cantidad_sin_cubrir')} {c.get('unidad')} | proveedor {c.get('proveedor_sugerido')}")
            elif op == "7":
                plan = self.rp4.ver_propuesta()
                items = list((plan or {}).get("cronologia", []))
                if not items:
                    print_fn("No hay cronología. Revisa que existan eventos o producciones para mañana.")
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

    def _menu_rp5(self, input_fn, print_fn) -> None:
        service = self._servicio_rp5()
        while True:
            print_fn("\nRP-5 — INCIDENCIAS Y REPLANIFICACIÓN")
            print_fn("1. Registrar incidencia")
            print_fn("2. Ver incidencias abiertas")
            print_fn("3. Ver impacto")
            print_fn("4. Ver alternativas")
            print_fn("5. Seleccionar solución y confirmar replanificación")
            print_fn("6. Ver diferencias entre planes")
            print_fn("7. Deshacer una propuesta no confirmada")
            print_fn("8. Cerrar incidencia")
            print_fn("9. Actualizar briefing")
            print_fn("99. Diagnóstico RP-5")
            print_fn("0. Volver")
            op = input_fn("Elige una opción: ").strip()
            try:
                if op == "1":
                    incidencia = self._capturar_incidencia_rp5(input_fn)
                    out = service.registrar_incidencia(**incidencia)
                    print_fn(f"Incidencia registrada: {out.get('id')} | estado {out.get('estado')}")
                elif op == "2":
                    items = service.listar_incidencias()
                    if not items:
                        print_fn("No hay incidencias registradas.")
                    for i, item in enumerate(items, 1):
                        print_fn(f"{i}. [{item.get('estado')}] {item.get('tipo')} · {item.get('descripcion')}")
                elif op == "3":
                    inc = self._seleccionar_incidencia_rp5(service, input_fn, print_fn)
                    if inc:
                        analisis = service.analizar_impacto(inc.get("id"))
                        self._mostrar_impacto_rp5(analisis, print_fn)
                elif op == "4":
                    inc = self._seleccionar_incidencia_rp5(service, input_fn, print_fn)
                    if inc:
                        alternativas = service.proponer_alternativas(inc.get("id"))
                        self._mostrar_alternativas_rp5(alternativas, print_fn)
                elif op == "5":
                    inc = self._seleccionar_incidencia_rp5(service, input_fn, print_fn)
                    if inc:
                        alternativas = service.proponer_alternativas(inc.get("id"))
                        self._mostrar_alternativas_rp5(alternativas, print_fn)
                        alt_id = input_fn("ID de alternativa (vacío = primera): ").strip()
                        parcial = input_fn("¿Confirmación parcial? (s/n): ").strip().lower() in {"s", "si", "sí"}
                        token = input_fn("Escribe CONFIRMAR: ").strip()
                        out = service.confirmar_replanificacion(inc.get("id"), confirmacion=token, alternativa_id=alt_id, parcial=parcial)
                        print_fn(f"Replanificación confirmada: {out.get('estado')} | versión {out.get('version', {}).get('version')}")
                elif op == "6":
                    inc = self._seleccionar_incidencia_rp5(service, input_fn, print_fn)
                    if inc:
                        dif = service.diferencias_plan(inc.get("id"))
                        print_fn(f"Plan anterior: {dif.get('plan_anterior_id')} | Plan resultante: {dif.get('plan_resultante_id')}")
                        print_fn(f"Tareas: {dif.get('tareas_anteriores')} → {dif.get('tareas_resultantes')}")
                        print_fn(f"Compras: {dif.get('compras_anteriores')} → {dif.get('compras_resultantes')}")
                        print_fn(f"Cronología: {dif.get('cronologia_anterior')} → {dif.get('cronologia_resultante')}")
                elif op == "7":
                    props = self._rp5_propuestas(service)
                    if not props:
                        print_fn("No hay propuestas para deshacer.")
                    else:
                        for i, p in enumerate(props, 1):
                            print_fn(f"{i}. {p.get('id')} | {p.get('estado')} | incidencia {p.get('incidencia_id')}")
                        raw = input_fn("Número de propuesta: ").strip()
                        if raw.isdigit() and 1 <= int(raw) <= len(props):
                            motivo = input_fn("Motivo del descarte: ").strip()
                            out = service.deshacer_propuesta(props[int(raw)-1].get('id'), motivo=motivo)
                            print_fn(f"Propuesta deshecha: {out.get('id')} | estado {out.get('estado')}")
                elif op == "8":
                    inc = self._seleccionar_incidencia_rp5(service, input_fn, print_fn)
                    if inc:
                        motivo = input_fn("Motivo de cierre: ").strip()
                        out = service.cerrar_incidencia(inc.get("id"), motivo=motivo)
                        print_fn(f"Incidencia cerrada: {out.get('id')} | estado {out.get('estado')}")
                elif op == "9":
                    plan = self.rp4.preparar_manana()
                    print_fn(f"Brífing actualizado con RP-5. Plan RP-4 actual: {plan.get('id')}")
                elif op == "99":
                    print_fn(formatear_diagnostico_rp5(service.diagnostico()))
                elif op == "0":
                    return
                else:
                    print_fn("Opción no válida.")
            except Exception as exc:
                print_fn(f"No se pudo completar la acción: {exc}")

    def _servicio_rp5(self) -> IncidenciasReplanificacionRP5:
        if self._rp5 is None:
            self._rp5 = IncidenciasReplanificacionRP5(self.base_dir)
        return self._rp5

    @staticmethod
    def _capturar_incidencia_rp5(input_fn) -> dict:
        print("\nREGISTRO DE INCIDENCIA RP-5")
        tipo = input_fn("Tipo de incidencia: ").strip()
        gravedad = input_fn("Gravedad [media]: ").strip() or "media"
        descripcion = input_fn("Descripción: ").strip()
        origen = input_fn("Origen [operativa]: ").strip() or "operativa"
        evento_id = input_fn("Evento ID (opcional): ").strip()
        tarea_id = input_fn("Tarea ID (opcional): ").strip()
        recurso = input_fn("Recurso (opcional): ").strip()
        articulo = input_fn("Artículo (opcional): ").strip()
        persona = input_fn("Persona (opcional): ").strip()
        cantidad_prevista = input_fn("Cantidad prevista (opcional): ").strip()
        cantidad_real = input_fn("Cantidad real (opcional): ").strip()
        unidad = input_fn("Unidad (opcional): ").strip()
        evidencia = input_fn("Evidencia separada por coma (opcional): ").strip()
        fecha_hora = input_fn("Fecha y hora (opcional, YYYY-MM-DD HH:MM): ").strip()
        nuevo_valor = input_fn("Nuevo valor (opcional): ").strip()
        return {
            "tipo": tipo,
            "gravedad": gravedad,
            "descripcion": descripcion,
            "origen": origen,
            "evento_id": evento_id,
            "tarea_id": tarea_id,
            "recurso": recurso,
            "articulo": articulo,
            "persona": persona,
            "cantidad_prevista": float(cantidad_prevista.replace(",", ".")) if cantidad_prevista else None,
            "cantidad_real": float(cantidad_real.replace(",", ".")) if cantidad_real else None,
            "unidad": unidad,
            "evidencia": [x.strip() for x in evidencia.split(",") if x.strip()] if evidencia else [],
            "fecha_hora": fecha_hora,
            "nuevo_valor": float(nuevo_valor.replace(",", ".")) if nuevo_valor and nuevo_valor.replace(",", ".").replace(".", "", 1).isdigit() else (nuevo_valor or None),
        }

    @staticmethod
    def _mostrar_impacto_rp5(impacto: dict, print_fn) -> None:
        print_fn("\nIMPACTO RP-5")
        print_fn(f"Tipo: {impacto.get('tipo')} | Gravedad: {impacto.get('gravedad')}")
        print_fn(f"Severidad: {impacto.get('severidad')} | Retraso estimado: {impacto.get('retraso_est_min', 0)} min")
        print_fn(f"Bloqueos: {len(impacto.get('bloqueos', []))} | Acciones a recalcular: {', '.join(impacto.get('acciones_recalcular', [])) or '-'}")
        print_fn(f"Cantidades: {impacto.get('cantidades', {})}")
        for e in impacto.get("elementos_afectados", [])[:12]:
            print_fn(f"- {e.get('tipo')}: {e.get('nombre') or e.get('id')}")

    @staticmethod
    def _mostrar_alternativas_rp5(alternativas: list[dict], print_fn) -> None:
        print_fn("\nALTERNATIVAS RP-5")
        if not alternativas:
            print_fn("No hay alternativas disponibles.")
            return
        for i, alt in enumerate(alternativas, 1):
            print_fn(f"{i}. {alt.get('id')} | {alt.get('descripcion')}")
            print_fn(f"   Motivo: {alt.get('motivo')} | Prioridad: {alt.get('prioridad')} | Reversible: {alt.get('reversibilidad')}")

    @staticmethod
    def _seleccionar_incidencia_rp5(service, input_fn, print_fn):
        items = service.listar_incidencias()
        if not items:
            print_fn("No hay incidencias registradas.")
            return None
        for i, item in enumerate(items, 1):
            print_fn(f"{i}. [{item.get('estado')}] {item.get('tipo')} · {item.get('descripcion')}")
        raw = input_fn("Selecciona incidencia (0=cancelar): ").strip()
        if raw == "0":
            return None
        if not raw.isdigit() or not 1 <= int(raw) <= len(items):
            print_fn("Selección no válida.")
            return None
        return items[int(raw) - 1]

    @staticmethod
    def _rp5_propuestas(service) -> list[dict[str, Any]]:
        data = service._load_json(service.path_propuestas, [])
        return [p for p in data if str(p.get("estado")) != "descartada"]


__all__ = ["ConsolaJornadaPiloto12"]
