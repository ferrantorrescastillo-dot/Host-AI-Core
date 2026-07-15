from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from APP.consola_bandeja_trabajo_piloto_11 import ConsolaBandejaTrabajoPiloto11
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

    def ejecutar(self, input_fn: Callable[[str], str] = input, print_fn: Callable[..., None] = print) -> None:
        while True:
            jornada = self.service.construir()
            self._mostrar_portada(jornada, print_fn)
            print_fn("\n¿Qué quieres hacer?")
            print_fn("1. Ver el plan completo del día")
            print_fn("2. Ver tareas agrupadas por área")
            print_fn("3. Abrir la bandeja de trabajo")
            print_fn("4. Recalcular la jornada")
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


__all__ = ["ConsolaJornadaPiloto12"]
