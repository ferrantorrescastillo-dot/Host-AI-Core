from __future__ import annotations

from typing import Any, Callable

from SERVICIOS.produccion_guiada_piloto_13 import ProduccionGuiadaPiloto13


class ConsolaProduccionGuiadaPiloto13:
    def __init__(self, core: Any, consola_avanzada: Any | None = None):
        self.core = core
        self.service = ProduccionGuiadaPiloto13(core)
        self.consola_avanzada = consola_avanzada

    def ejecutar(self, input_fn: Callable[[str], str] = input, print_fn: Callable[..., None] = print) -> None:
        while True:
            planes = self.service.listar_planes_operativos()
            print_fn("\n" + "=" * 78)
            print_fn("PRODUCCIÓN GUIADA")
            print_fn("=" * 78)
            if not planes:
                print_fn("No hay producción preparada para trabajar ahora.")
                print_fn("Siguiente paso: abre la gestión avanzada para revisar o crear el plan.")
                print_fn("1. Abrir gestión avanzada de producción")
                print_fn("0. Volver")
                op = input_fn("Elige una opción: ").strip()
                if op == "1" and self.consola_avanzada:
                    self.consola_avanzada()
                elif op == "0":
                    return
                continue
            for i, p in enumerate(planes, 1):
                print_fn(f"{i}. {p.get('nombre') or p.get('evento')} | {p.get('fecha') or 'sin fecha'} | {p.get('estado','').replace('_',' ')}")
            print_fn("A. Gestión avanzada de producción")
            print_fn("0. Volver")
            op = input_fn("Selecciona el plan que vas a trabajar: ").strip()
            if op == "0": return
            if op.lower() == "a" and self.consola_avanzada:
                self.consola_avanzada(); continue
            if not op.isdigit() or not 1 <= int(op) <= len(planes):
                print_fn("Selección no válida."); continue
            self._trabajar_plan(str(planes[int(op)-1].get("id")), input_fn, print_fn)

    def _trabajar_plan(self, plan_id: str, input_fn, print_fn) -> None:
        while True:
            panel = self.service.construir_panel(plan_id)
            self._mostrar_panel(panel, print_fn)
            print_fn("\n¿Qué acaba de pasar?")
            print_fn("ACCIONES HABITUALES")
            print_fn("1. Voy a empezar una tarea")
            print_fn("2. He terminado una tarea")
            print_fn("3. Necesito pausar o reanudar")
            print_fn("7. He cambiado a la siguiente fase")
            print_fn("\nREGISTRAR LO OCURRIDO")
            print_fn("4. Quiero indicar cuánto llevo")
            print_fn("5. Ha surgido un problema")
            print_fn("6. He resuelto un bloqueo")
            print_fn("8. Registrar merma")
            print_fn("\nOTRAS OPCIONES")
            print_fn("9. Actualizar la pantalla")
            print_fn("0. Volver")
            op = input_fn("Elige una opción: ").strip()
            if op == "0": return
            if op == "9": continue
            if op not in {"1", "2", "3", "4", "5", "6", "7", "8"}:
                print_fn("Opción no válida."); continue
            tarea = self._seleccionar_tarea(panel["tareas"], input_fn, print_fn)
            if not tarea: continue
            try:
                if op == "1":
                    if tarea.get("estado_codigo") == "pausada": self.service.reanudar(plan_id, tarea["id"]); print_fn(f"Tarea reanudada: {tarea['titulo']}.")
                    else: self.service.iniciar(plan_id, tarea["id"]); print_fn(f"Tarea iniciada: {tarea['titulo']}.")
                elif op == "2":
                    pendientes = int(tarea.get("checklist_pendiente", 0) or 0)
                    if pendientes: print_fn(f"Aviso: quedan {pendientes} paso(s) del checklist sin completar.")
                    confirmar = input_fn(f"¿Confirmas que '{tarea['titulo']}' está terminada? (s/n): ").strip().lower()
                    if confirmar in {"s", "si", "sí"}:
                        if self.service.produccion_stock is None:
                            print_fn("No hay módulo de stock disponible en este entorno para cierre transaccional.")
                            continue
                        vista = self.service.produccion_stock.preparar_cierre(plan_id, tarea["id"])
                        if vista.get("estado") == "SIN_ESCANDALLO":
                            print_fn("No hay escandallo para actualizar stock. La tarea no se ha cerrado.")
                        elif vista.get("estado") == "STOCK_INSUFICIENTE":
                            print_fn("No hay stock suficiente:")
                            for f in vista.get("faltantes", []):
                                print_fn(f"- {f['nombre']}: faltan {f['faltante']:g} {f['unidad']}")
                            reg = input_fn("¿Registrar una incidencia y dejar la tarea bloqueada? (s/n): ").strip().lower()
                            if reg in {"s", "si", "sí"}:
                                self.service.produccion_stock.registrar_incidencia_stock(plan_id, tarea["id"], "Stock insuficiente para cerrar la producción")
                                print_fn("Incidencia registrada. No se ha modificado el stock.")
                        elif not vista.get("ok"):
                            print_fn(vista.get("mensaje", "No se pudo preparar el cierre."))
                        else:
                            print_fn("Movimientos previstos:")
                            for c in vista.get("consumos", []): print_fn(f"- Salida: {c['nombre']} -{c['cantidad']:g} {c['unidad']}")
                            g = vista.get("produccion_generada", {})
                            print_fn(f"- Entrada: {g.get('nombre')} +{g.get('cantidad'):g} {g.get('unidad')}")
                            aplicar = input_fn("¿Registrar producción y actualizar stock? (s/n): ").strip().lower()
                            if aplicar in {"s", "si", "sí"}:
                                operario = input_fn("Operario [cocina]: ").strip() or "cocina"
                                lote = input_fn("Lote (opcional): ").strip()
                                resultado = self.service.finalizar_con_stock(plan_id, tarea["id"], operario, lote)
                                print_fn(resultado.get("mensaje"))
                            else: print_fn("No se ha modificado la tarea ni el stock.")
                    else: print_fn("No se ha modificado la tarea.")
                elif op == "3":
                    if tarea.get("estado_codigo") in {"en_curso", "en_preparacion", "en_proceso", "en_espera", "incidencia"}: self.service.pausar(plan_id, tarea["id"]); print_fn("Tarea pausada.")
                    elif tarea.get("estado_codigo") == "pausada": self.service.reanudar(plan_id, tarea["id"]); print_fn("Tarea reanudada.")
                    else: print_fn("Esta tarea no está en marcha ni pausada.")
                elif op == "4":
                    valor = float(input_fn("Porcentaje aproximado completado (0-100): ").strip())
                    self.service.actualizar_avance(plan_id, tarea["id"], valor); print_fn("Avance actualizado.")
                elif op == "5":
                    descripcion = input_fn("Explica el problema: ").strip()
                    bloqueo = input_fn("¿Impide seguir trabajando? (s/n): ").strip().lower() in {"s", "si", "sí"}
                    retraso = int(input_fn("Retraso aproximado en minutos [0]: ").strip() or "0")
                    self.service.registrar_incidencia(plan_id, tarea["id"], descripcion, bloqueo, retraso); print_fn("Problema registrado.")
                elif op == "6":
                    observacion = input_fn("Cómo se ha resuelto (opcional): ").strip()
                    self.service.resolver_bloqueo(plan_id, tarea["id"], observacion); print_fn("Bloqueo resuelto.")
                elif op == "7":
                    fases = list(tarea.get("fases") or [])
                    if not fases:
                        print_fn("La tarea no tiene fases definidas.")
                    else:
                        print_fn("Fases disponibles:")
                        for i, f in enumerate(fases, 1):
                            print_fn(f"{i}. {f.get('nombre')} [{f.get('estado', 'PENDIENTE')}]")
                        sel = input_fn("Elige fase (vacío para siguiente automática): ").strip()
                        fase_id = ""
                        if sel:
                            if sel.isdigit() and 1 <= int(sel) <= len(fases):
                                fase_id = str(fases[int(sel)-1].get("id") or "")
                            else:
                                print_fn("Selección de fase inválida.")
                                continue
                        obs = input_fn("Observación de fase (opcional): ").strip()
                        self.service.cambiar_fase(plan_id, tarea["id"], fase_id=fase_id, observaciones=obs)
                        print_fn("Fase actualizada.")
                elif op == "8":
                    cantidad = float(input_fn("Cantidad de merma: ").strip())
                    unidad = input_fn(f"Unidad [{tarea.get('unidad') or 'u'}]: ").strip() or (tarea.get("unidad") or "u")
                    motivo = input_fn("Motivo de merma (opcional): ").strip()
                    self.service.registrar_merma(plan_id, tarea["id"], cantidad, unidad, motivo=motivo)
                    print_fn("Merma registrada.")
            except Exception as exc:
                print_fn(f"No se pudo completar la acción: {exc}")

    @staticmethod
    def _mostrar_panel(panel: dict[str, Any], print_fn) -> None:
        print_fn("\n" + "=" * 78)
        print_fn("QUÉ DEBO HACER AHORA")
        print_fn("=" * 78)
        accion = panel["siguiente_accion"]
        print_fn(f"> {accion['texto']}")
        print_fn(f"  {accion['explicacion']}")
        recomendacion_motor = panel.get("recomendacion_motor") or {}
        if str(recomendacion_motor.get("explicacion") or "").strip():
            print_fn("\nRECOMENDACIÓN DEL MOTOR")
            print_fn(recomendacion_motor.get("texto") or "")
            print_fn(recomendacion_motor.get("explicacion") or "")

        bloqueadas = [t for t in panel["tareas"] if t.get("bloqueo")]
        if bloqueadas:
            print_fn("\nTE IMPIDE CONTINUAR")
            for tarea in bloqueadas:
                print_fn(f"- {tarea.get('titulo')}: {tarea.get('bloqueo')}")
            alternativa = next(
                (t for t in panel["tareas"] if not t.get("bloqueo") and t.get("puede_iniciar")),
                None,
            )
            if alternativa:
                print_fn(f"> Mientras se resuelve, puedes adelantar {alternativa.get('titulo')}.")
            else:
                espera = next((t for t in panel["tareas"] if t.get("estado_codigo") == "en_espera"), None)
                if espera:
                    print_fn(f"> Aprovecha la espera de {espera.get('titulo')} para revisar el siguiente trabajo.")
                else:
                    print_fn("> Revisa stock, recepciones o compras y vuelve cuando el bloqueo esté resuelto.")
        if panel.get("alertas"):
            print_fn("\nAVISOS")
            for a in panel["alertas"]: print_fn(f"- {a.get('tarea') or 'Producción'}: {a.get('mensaje')}")
        print_fn(f"\n{panel['plan']} | {panel['avance']}% hecho | {panel['pendientes']} por hacer | {panel['en_curso']} en marcha")
        print_fn("\nSIGUIENTE TRABAJO")
        for i, t in enumerate(panel["tareas"], 1):
            print_fn(f"{i}. {t['estado_texto']} {t.get('titulo')} · {t['prioridad_texto']}")
            print_fn(f"   Queda: {t['tiempo_restante_texto']}")
            if t.get("bloqueo"): print_fn(f"   Bloqueo: {t['bloqueo']}")

    @staticmethod
    def _seleccionar_tarea(tareas, input_fn, print_fn):
        sel = input_fn("Número de tarea (0=cancelar): ").strip()
        if sel == "0": return None
        if not sel.isdigit() or not 1 <= int(sel) <= len(tareas):
            print_fn("Selección no válida."); return None
        return tareas[int(sel)-1]


__all__ = ["ConsolaProduccionGuiadaPiloto13"]
