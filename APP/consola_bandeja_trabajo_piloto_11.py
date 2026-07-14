from __future__ import annotations

from pathlib import Path
from typing import Callable

from SERVICIOS.bandeja_trabajo_piloto_11 import BandejaTrabajoPiloto11, formatear_diagnostico_piloto11


class ConsolaBandejaTrabajoPiloto11:
    def __init__(self, base_dir: Path | str):
        self.base_dir = Path(base_dir)
        self.service = BandejaTrabajoPiloto11(self.base_dir)

    def ejecutar(self, input_fn: Callable[[str], str] = input, print_fn: Callable[..., None] = print) -> None:
        while True:
            self.service.sincronizar_fuentes()
            self._mostrar_resumen(print_fn)
            print_fn("\n¿Qué quieres hacer?")
            print_fn("1. Ver tareas pendientes")
            print_fn("2. Añadir una tarea o incidencia")
            print_fn("3. Empezar o retomar una tarea")
            print_fn("4. Marcar una tarea como terminada")
            print_fn("5. Aplazar una tarea")
            print_fn("6. Ver tareas terminadas")
            print_fn("7. Eliminar una tarea manual")
            print_fn("9. Diagnóstico aislado")
            print_fn("0. Volver")
            op = input_fn("Elige una opción: ").strip()
            if op == "1": self._listar(False, print_fn)
            elif op == "2": self._crear(input_fn, print_fn)
            elif op == "3": self._estado("EN_CURSO", input_fn, print_fn)
            elif op == "4": self._estado("COMPLETADA", input_fn, print_fn)
            elif op == "5": self._aplazar(input_fn, print_fn)
            elif op == "6": self._listar(True, print_fn)
            elif op == "7": self._eliminar(input_fn, print_fn)
            elif op == "9": print_fn(formatear_diagnostico_piloto11(self.service.diagnostico()))
            elif op == "0": return
            else: print_fn("Opción no válida.")

    def _mostrar_resumen(self, print_fn) -> None:
        r = self.service.resumen()
        print_fn("\n" + "=" * 70)
        print_fn("BANDEJA DE TRABAJO — LO QUE QUEDA POR HACER")
        print_fn("=" * 70)
        print_fn(f"Abiertas: {r['abiertas']} | Pendientes: {r['pendientes']} | En curso: {r['en_curso']} | Aplazadas: {r['aplazadas']} | Bloqueadas: {r['bloqueadas']}")
        top = self.service.listar()[:5]
        if not top:
            print_fn("No tienes tareas pendientes.")
        else:
            print_fn("\nPRIORIDADES")
            for i, t in enumerate(top, 1):
                print_fn(f"{i}. [{t['estado']}] {t['titulo']} · {t['tipo']} · prioridad {t['prioridad']}")

    def _listar(self, completadas: bool, print_fn) -> list[dict]:
        tareas = self.service.listar(estados={"COMPLETADA"} if completadas else None, incluir_completadas=completadas)
        if completadas:
            tareas = [x for x in tareas if x.get("estado") == "COMPLETADA"]
        print_fn("\nTAREAS TERMINADAS" if completadas else "\nTAREAS ABIERTAS")
        if not tareas:
            print_fn("No hay tareas.")
            return []
        for i, t in enumerate(tareas, 1):
            detail = f" | {t.get('descripcion')}" if t.get("descripcion") else ""
            print_fn(f"{i}. [{t['estado']}] {t['titulo']} | {t['tipo']} | prioridad {t['prioridad']}{detail}")
        return tareas

    def _crear(self, input_fn, print_fn) -> None:
        print_fn("Tipos: 1 Recepción | 2 Stock | 3 Producción | 4 Evento | 5 Pedido | 6 Incidencia proveedor | 7 General")
        mapping = {"1":"RECEPCION","2":"STOCK","3":"PRODUCCION","4":"EVENTO","5":"PEDIDO","6":"INCIDENCIA_PROVEEDOR","7":"GENERAL"}
        tipo = mapping.get(input_fn("Tipo [7]: ").strip() or "7", "GENERAL")
        titulo = input_fn("¿Qué queda por hacer?: ").strip()
        descripcion = input_fn("Nota breve [opcional]: ").strip()
        raw = input_fn("Prioridad 0-100 [50]: ").strip()
        prioridad = int(raw) if raw.isdigit() else 50
        task = self.service.crear_tarea(titulo, tipo, prioridad, descripcion)
        print_fn(f"Tarea añadida: {task['id']}")

    def _seleccionar(self, input_fn, print_fn) -> dict | None:
        tareas = self._listar(False, print_fn)
        if not tareas: return None
        raw = input_fn("Número de tarea: ").strip()
        if not raw.isdigit() or not 1 <= int(raw) <= len(tareas):
            print_fn("Selección no válida.")
            return None
        return tareas[int(raw)-1]

    def _estado(self, estado, input_fn, print_fn) -> None:
        task = self._seleccionar(input_fn, print_fn)
        if not task: return
        nota = input_fn("Nota [opcional]: ").strip()
        self.service.cambiar_estado(task["id"], estado, nota)
        print_fn(f"Tarea actualizada: {estado}")
        if estado == "EN_CURSO" and task.get("tipo") == "RECEPCION" and task.get("referencia"):
            print_fn(f"Recepción vinculada: {task['referencia']}")
            print_fn("Ábrela desde Recepciones para revisar o aplicar el stock.")

    def _aplazar(self, input_fn, print_fn) -> None:
        task = self._seleccionar(input_fn, print_fn)
        if not task: return
        hasta = input_fn("¿Hasta cuándo? (ej. final del día, viernes): ").strip()
        nota = input_fn("Motivo [opcional]: ").strip()
        self.service.cambiar_estado(task["id"], "APLAZADA", nota, hasta)
        print_fn("Tarea aplazada.")

    def _eliminar(self, input_fn, print_fn) -> None:
        task = self._seleccionar(input_fn, print_fn)
        if not task: return
        if task.get("origen") != "manual":
            print_fn("Las tareas sincronizadas no se eliminan; márcalas como completadas o canceladas.")
            return
        if input_fn("Escribe ELIMINAR para confirmar: ").strip().upper() == "ELIMINAR":
            self.service.eliminar(task["id"])
            print_fn("Tarea eliminada.")


__all__ = ["ConsolaBandejaTrabajoPiloto11"]
