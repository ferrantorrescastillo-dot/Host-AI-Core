from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from APP.consola_bandeja_trabajo_piloto_11 import ConsolaBandejaTrabajoPiloto11
from SERVICIOS.jornada_piloto_12 import JornadaPiloto12, formatear_diagnostico_piloto12

TIPOS_TEXTO = {
    "PRODUCCION": "Producción", "RECEPCION": "Recepciones", "EVENTO": "Eventos",
    "PEDIDO": "Compras / pedidos", "STOCK": "Stock",
    "INCIDENCIA_PROVEEDOR": "Incidencias de proveedor", "DOCUMENTO": "Documentos",
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
            if op == "1": self._mostrar_plan(jornada, print_fn)
            elif op == "2": self._mostrar_grupos(jornada, print_fn)
            elif op == "3": ConsolaBandejaTrabajoPiloto11(self.base_dir).ejecutar(input_fn=input_fn, print_fn=print_fn)
            elif op == "4": print_fn("He recalculado la jornada con el estado actual de la bandeja.")
            elif op == "9": print_fn(formatear_diagnostico_piloto12(self.service.diagnostico()))
            elif op == "0": return
            else: print_fn("Opción no válida.")

    def _mostrar_portada(self, jornada: dict, print_fn) -> None:
        r = jornada["resumen"]
        print_fn("\n" + "=" * 78)
        print_fn("MI JORNADA")
        print_fn("=" * 78)
        print_fn(jornada["saludo"])
        print_fn(jornada["resumen_humano"])
        print_fn(f"Fecha: {self._fecha_legible(jornada['fecha'])} | Tareas abiertas: {r['abiertas']}")

        if jornada["alertas"]:
            print_fn("\nAVISOS IMPORTANTES")
            for alerta in jornada["alertas"]:
                icono = {"ALTA": "🔴", "MEDIA": "🟠", "BAJA": "🟡"}.get(alerta["nivel"], "⚪")
                print_fn(f"{icono} {alerta['mensaje']}")

        print_fn("\nQUÉ HARÍA PRIMERO")
        recomendaciones = jornada["recomendaciones"][:5]
        if not recomendaciones:
            print_fn("No hay trabajo pendiente registrado.")
        else:
            for i, rec in enumerate(recomendaciones, 1):
                print_fn(f"{i}. {rec['titulo']} · {self._prioridad_texto(rec['prioridad'])}")
                print_fn(f"   {rec.get('motivo_humano', rec['motivo'])}")

        print_fn("\nCRONOGRAMA ORIENTATIVO")
        if not jornada["cronograma"]:
            print_fn("No hay tareas para colocar en el cronograma.")
        for bloque in jornada["cronograma"]:
            print_fn(f"{bloque['franja']}  {bloque['prioridad']}  {bloque['titulo']}")

        t = jornada["tiempos"]
        print_fn("\nTIEMPO CONOCIDO")
        print_fn(f"Trabajo activo: {self._hm(t['activo_conocido_min'])} | Esperas aprovechables: {self._hm(t['pasivo_conocido_min'])}")
        if t["tareas_sin_duracion"]:
            print_fn(f"Hay {t['tareas_sin_duracion']} tarea(s) sin tiempo registrado.")
        if t["fin_estimado_por_trabajo_activo"]:
            hora = datetime.fromisoformat(t["fin_estimado_por_trabajo_activo"]).strftime("%H:%M")
            print_fn(f"Con los tiempos activos conocidos, terminarías aproximadamente a las {hora}.")
        print_fn("La previsión es orientativa y solo utiliza tiempos registrados.")

    def _mostrar_plan(self, jornada: dict, print_fn) -> None:
        print_fn("\nPLAN COMPLETO DEL DÍA")
        if not jornada["tareas"]:
            print_fn("No hay tareas abiertas.")
            return
        for i, tarea in enumerate(jornada["tareas"], 1):
            area = TIPOS_TEXTO.get(tarea.get("tipo"), tarea.get("tipo"))
            print_fn(f"\n{i}. {tarea['prioridad_humana']} — {tarea['titulo']}")
            print_fn(f"   Área: {area} | Tiempo: {tarea['duracion_humana']}")
            print_fn(f"   Por qué: {tarea['explicacion']}")
            if tarea.get("descripcion"): print_fn(f"   Nota: {tarea['descripcion']}")
            if tarea.get("evento_mensaje"): print_fn(f"   {tarea['evento_mensaje']}")

    def _mostrar_grupos(self, jornada: dict, print_fn) -> None:
        print_fn("\nTRABAJO POR ÁREAS")
        if not jornada["grupos"]:
            print_fn("No hay tareas abiertas.")
            return
        orden = ["PRODUCCION", "RECEPCION", "EVENTO", "PEDIDO", "STOCK", "INCIDENCIA_PROVEEDOR", "DOCUMENTO", "GENERAL"]
        for tipo in orden:
            tareas = jornada["grupos"].get(tipo, [])
            if not tareas: continue
            print_fn(f"\n{TIPOS_TEXTO.get(tipo, tipo)} ({len(tareas)})")
            for tarea in tareas:
                print_fn(f"- {tarea['prioridad_humana']} — {tarea['titulo']} ({tarea['duracion_humana']})")

    @staticmethod
    def _prioridad_texto(texto: str) -> str:
        return {"Muy urgente": "🔴 Muy urgente", "Hoy": "🟠 Conviene hacerlo hoy", "Esta semana": "🟡 Esta semana", "Cuando puedas": "🟢 Puede esperar"}.get(texto, texto)

    @staticmethod
    def _fecha_legible(fecha: str) -> str:
        try: return datetime.strptime(fecha, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError: return fecha

    @staticmethod
    def _hm(minutes):
        if minutes is None: return "sin tiempo registrado"
        h, m = divmod(int(minutes), 60)
        if h and m: return f"{h} h {m} min"
        if h: return f"{h} h"
        return f"{m} min"


__all__ = ["ConsolaJornadaPiloto12"]
