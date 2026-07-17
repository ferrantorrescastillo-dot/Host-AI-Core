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
            print_fn("A. Ver detalle de clasificación")
            print_fn("B. Ver detalle de cuellos previstos")
            print_fn("C. Ver detalle de cronología prevista")
            print_fn("D. Ver inventario de recursos")
            print_fn("E. Ver ocupación de recursos")
            print_fn("F. Ver simultaneidad de recursos")
            print_fn("G. Ver conflictos de recursos")
            print_fn("9. Actualizar la pantalla")
            print_fn("0. Volver")
            op = input_fn("Elige una opción: ").strip()
            if op == "0": return
            if op == "9": continue
            if op.lower() == "a":
                self._mostrar_detalle_clasificacion(panel, print_fn)
                input_fn("Pulsa Enter para volver al panel: ")
                continue
            if op.lower() == "b":
                self._mostrar_detalle_cuellos(panel, print_fn)
                input_fn("Pulsa Enter para volver al panel: ")
                continue
            if op.lower() == "c":
                self._mostrar_detalle_cronologia(panel, print_fn)
                input_fn("Pulsa Enter para volver al panel: ")
                continue
            if op.lower() == "d":
                self._mostrar_inventario_recursos(panel, print_fn)
                input_fn("Pulsa Enter para volver al panel: ")
                continue
            if op.lower() == "e":
                self._mostrar_ocupacion_recursos(panel, print_fn)
                input_fn("Pulsa Enter para volver al panel: ")
                continue
            if op.lower() == "f":
                self._mostrar_simultaneidad_recursos(panel, print_fn)
                input_fn("Pulsa Enter para volver al panel: ")
                continue
            if op.lower() == "g":
                self._mostrar_conflictos_recursos(panel, print_fn)
                input_fn("Pulsa Enter para volver al panel: ")
                continue
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
            if str(recomendacion_motor.get("mientras_tanto") or "").strip():
                print_fn("\nMientras tanto:")
                print_fn(f"- {recomendacion_motor.get('mientras_tanto')}")
            if str(recomendacion_motor.get("atencion_intervalo") or "").strip():
                print_fn("\nAtención durante el intervalo:")
                print_fn(f"- {recomendacion_motor.get('atencion_intervalo')}")
            if str(recomendacion_motor.get("siguiente_movimiento") or "").strip():
                print_fn("\nDespués:")
                print_fn(f"- {recomendacion_motor.get('siguiente_movimiento')}")

        fase_actual = panel.get("fase_actual") or {}
        propiedades_fase = [p for p in (fase_actual.get("propiedades") or []) if str(p).strip()]
        if str(fase_actual.get("nombre") or "").strip() and propiedades_fase:
            print_fn("\nFASE ACTUAL")
            print_fn(fase_actual.get("nombre"))
            for propiedad in propiedades_fase:
                print_fn(f"- {propiedad}")

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
        resumen_jornada = panel.get("resumen_jornada") or {}
        if any(int(resumen_jornada.get(clave, 0) or 0) > 0 for clave in ("criticas", "largas", "medias", "rapidas")):
            print_fn("\nRESUMEN DE LA JORNADA")
            print_fn(f"- Críticas: {int(resumen_jornada.get('criticas', 0) or 0)}")
            print_fn(f"- Largas: {int(resumen_jornada.get('largas', 0) or 0)}")
            print_fn(f"- Medias: {int(resumen_jornada.get('medias', 0) or 0)}")
            print_fn(f"- Rápidas: {int(resumen_jornada.get('rapidas', 0) or 0)}")
        resumen_cuellos = panel.get("resumen_cuellos") or {}
        if int(resumen_cuellos.get("total", 0) or 0) > 0:
            print_fn("\nCUELLOS PREVISTOS")
            print_fn(f"- Recursos: {int(resumen_cuellos.get('recursos', 0) or 0)}")
            print_fn(f"- Personal: {int(resumen_cuellos.get('personal', 0) or 0)}")
            print_fn(f"- Dependencias: {int(resumen_cuellos.get('dependencias', 0) or 0)}")
        resumen_cronologia = panel.get("resumen_cronologia") or {}
        if int(resumen_cronologia.get("total_tramos", 0) or 0) > 0:
            print_fn("\nCRONOLOGÍA PREVISTA")
            base = panel.get("cronologia_base_horaria") or {}
            if str(base.get("texto") or "").strip():
                print_fn(f"- Base horaria: {base.get('texto')}")
            print_fn(f"- Tramos: {int(resumen_cronologia.get('total_tramos', 0) or 0)}")
            print_fn(f"- Estimados: {int(resumen_cronologia.get('tramos_estimados', 0) or 0)}")
            print_fn(f"- Reales: {int(resumen_cronologia.get('tramos_reales', 0) or 0)}")
            print_fn(f"- Indeterminados: {int(resumen_cronologia.get('tramos_indeterminados', 0) or 0)}")
        ConsolaProduccionGuiadaPiloto13._mostrar_resumen_recursos(panel, print_fn)
        print_fn("\nSIGUIENTE TRABAJO")
        for i, t in enumerate(panel["tareas"], 1):
            print_fn(f"{i}. {t['estado_texto']} {t.get('titulo')} · {t['prioridad_texto']}")
            print_fn(f"   Queda: {t['tiempo_restante_texto']}")
            if t.get("bloqueo"): print_fn(f"   Bloqueo: {t['bloqueo']}")

    @staticmethod
    def _mostrar_resumen_recursos(panel: dict[str, Any], print_fn) -> None:
        inventario = dict(panel.get("inventario_recursos") or {})
        ocupacion = dict(panel.get("ocupacion_recursos") or panel.get("ocupacion_temporal_recursos") or {})
        simultaneidad = dict(panel.get("simultaneidad_recursos") or {})
        conflictos = dict(panel.get("conflictos_recursos") or {})

        hay_datos = any(bool(x) for x in (inventario, ocupacion, simultaneidad, conflictos))
        print_fn("\nDIAGNÓSTICO DE RECURSOS")
        if not hay_datos:
            print_fn("- Sin información de recursos disponible")
            return

        recursos_conocidos = len(list(inventario.get("recursos_fisicos") or []))
        ocupaciones_registradas = int((ocupacion.get("resumen") or {}).get("total_bloques", len(list(ocupacion.get("bloques") or []))) or 0)
        maxima_simultaneidad = int((simultaneidad.get("resumen") or {}).get("maximo_nivel_simultaneidad", 0) or 0)
        conflictos_detectados = int((conflictos.get("resumen") or {}).get("total", len(list(conflictos.get("conflictos") or []))) or 0)

        print_fn(f"- Recursos conocidos: {recursos_conocidos}")
        print_fn(f"- Ocupaciones registradas: {ocupaciones_registradas}")
        print_fn(f"- Máxima simultaneidad: {maxima_simultaneidad}")
        print_fn(f"- Conflictos detectados: {conflictos_detectados}")

    @staticmethod
    def _mostrar_detalle_clasificacion(panel: dict[str, Any], print_fn) -> None:
        detalle = list(panel.get("clasificacion_detalle") or [])
        print_fn("\nDETALLE DE CLASIFICACIÓN")
        if not detalle:
            print_fn("No hay elaboraciones clasificadas para mostrar ahora mismo.")
            return
        for item in detalle:
            print_fn(f"- {item.get('resumen')}")
            for razon in item.get("razones", []) or []:
                print_fn(f"  · {razon}")

    @staticmethod
    def _mostrar_detalle_cuellos(panel: dict[str, Any], print_fn) -> None:
        detalle = list(panel.get("cuellos_detalle") or [])
        print_fn("\nDETALLE DE CUELLOS PREVISTOS")
        if not detalle:
            print_fn("No hay cuellos de botella previstos con datos suficientes.")
            return
        for item in detalle:
            print_fn(f"- {item.get('titulo')}")
            print_fn(f"  Momento: {item.get('momento')}")
            print_fn(f"  Riesgo: {item.get('riesgo')}")
            print_fn(f"  Consecuencia: {item.get('consecuencia')}")
            for razon in item.get("explicacion", []) or []:
                print_fn(f"  · {razon}")

    @staticmethod
    def _mostrar_detalle_cronologia(panel: dict[str, Any], print_fn) -> None:
        tramos = list(panel.get("cronologia_tramos") or [])
        print_fn("\nDETALLE DE CRONOLOGÍA PREVISTA")
        if not tramos:
            print_fn("No hay tramos cronológicos con datos suficientes.")
            return
        base = panel.get("cronologia_base_horaria") or {}
        if str(base.get("texto") or "").strip():
            print_fn(f"Base horaria: {base.get('texto')}")
        for tramo in tramos:
            inicio = tramo.get("inicio") or {}
            fin = tramo.get("fin") or {}
            print_fn(f"\n- {inicio.get('texto', 'sin hora')} -> {fin.get('texto', 'sin hora')}")
            print_fn(f"  Tarea: {tramo.get('tarea')}")
            print_fn(f"  Fase: {tramo.get('fase')}")
            if str(tramo.get("recurso") or "").strip():
                print_fn(f"  Recurso: {tramo.get('recurso')}")
            print_fn(f"  Por qué empieza aquí: {tramo.get('inicio_razon')}")
            reales = ", ".join(tramo.get("informacion_real") or []) or "ninguna"
            estimadas = ", ".join(tramo.get("informacion_estimada") or []) or "ninguna"
            print_fn(f"  Información real: {reales}")
            print_fn(f"  Información estimada: {estimadas}")
        alertas = list(panel.get("cronologia_alertas") or [])
        if alertas:
            print_fn("\nAvisos de cronología:")
            for alerta in alertas:
                print_fn(f"- {alerta}")

    @staticmethod
    def _mostrar_inventario_recursos(panel: dict[str, Any], print_fn) -> None:
        inventario = dict(panel.get("inventario_recursos") or {})
        recursos = list(inventario.get("recursos_fisicos") or [])
        print_fn("\nDETALLE DE INVENTARIO DE RECURSOS")
        if not inventario:
            print_fn("Sin información de inventario disponible.")
            return
        if not recursos:
            print_fn("No hay recursos en inventario para mostrar.")
        for item in recursos:
            nombre = str(item.get("nombre") or item.get("id_normalizado") or "recurso sin identificar")
            print_fn(f"- Recurso: {nombre}")
            print_fn(f"  Tipo: {item.get('tipo') or 'no indicado'}")
            capacidad = item.get("capacidad")
            print_fn(f"  Capacidad: {capacidad if capacidad not in (None, '') else 'no indicado'}")
            unidad = item.get("unidad") or item.get("capacidad_unidad") or "no indicado"
            print_fn(f"  Unidad: {unidad}")
            origen = item.get("capacidad_origen") or ("real" if item.get("capacidad_confirmada") else "estimada")
            print_fn(f"  Origen: {origen}")
            nombres_origen = ", ".join(list(item.get("nombres_origen") or []))
            if nombres_origen:
                print_fn(f"  Observaciones: variantes detectadas -> {nombres_origen}")
        incompletos = list(inventario.get("datos_incompletos") or [])
        if incompletos:
            print_fn("\nDatos incompletos en inventario:")
            for dato in incompletos:
                print_fn(f"- {dato.get('tipo') or 'dato_incompleto'}")

    @staticmethod
    def _mostrar_ocupacion_recursos(panel: dict[str, Any], print_fn) -> None:
        ocupacion = dict(panel.get("ocupacion_recursos") or panel.get("ocupacion_temporal_recursos") or {})
        bloques = list(ocupacion.get("bloques") or [])
        print_fn("\nDETALLE DE OCUPACIÓN DE RECURSOS")
        if not ocupacion:
            print_fn("Sin información de ocupación disponible.")
            return
        if not bloques:
            print_fn("No hay ocupaciones registradas.")
        bloques_ordenados = sorted(
            [dict(b) for b in bloques],
            key=lambda b: (
                int(b.get("dia", 1) or 1),
                int(b.get("inicio_min", 0) or 0),
                str(b.get("recurso") or ""),
                str(b.get("tarea") or ""),
            ),
        )
        for bloque in bloques_ordenados:
            recurso = bloque.get("recurso") or "recurso no indicado"
            tarea = bloque.get("tarea") or "tarea no indicada"
            responsable = bloque.get("responsable") or "no indicado"
            inicio = (bloque.get("inicio") or {}).get("texto") or f"{bloque.get('inicio_min', 'no indicado')} min"
            fin = (bloque.get("fin") or {}).get("texto") or f"{bloque.get('fin_min', 'no indicado')} min"
            inicio_min = bloque.get("inicio_min")
            fin_min = bloque.get("fin_min")
            if isinstance(inicio_min, int) and isinstance(fin_min, int) and fin_min > inicio_min:
                duracion = str(fin_min - inicio_min)
            else:
                duracion = "información incompleta"
            origen = bloque.get("origen_dato") or "no indicado"
            estado = bloque.get("estado") or "no indicado"
            print_fn(f"- {recurso} | {tarea}")
            print_fn(f"  Responsable: {responsable}")
            print_fn(f"  Inicio: {inicio} | Fin: {fin} | Duración: {duracion}")
            print_fn(f"  Carácter: {origen} | Estado: {estado}")
        incompletos = list(ocupacion.get("datos_incompletos") or [])
        if incompletos:
            print_fn("\nIncidencias de datos de ocupación:")
            for dato in incompletos:
                print_fn(f"- {dato.get('tipo') or 'dato_incompleto'}")

    @staticmethod
    def _mostrar_simultaneidad_recursos(panel: dict[str, Any], print_fn) -> None:
        simultaneidad = dict(panel.get("simultaneidad_recursos") or {})
        tramos = list(simultaneidad.get("tramos") or [])
        print_fn("\nDETALLE DE SIMULTANEIDAD DE RECURSOS")
        if not simultaneidad:
            print_fn("Sin información de simultaneidad disponible.")
            return
        if not tramos:
            print_fn("No hay tramos de simultaneidad registrados.")
        for tramo in tramos:
            recurso = ", ".join(list(tramo.get("recursos_fisicos_activos") or [])) or "no indicado"
            intervalo = tramo.get("intervalo") or "intervalo no indicado"
            cantidad = int(tramo.get("cantidad_total_ocupaciones", 0) or 0)
            tareas = ", ".join(list(tramo.get("tareas_activas") or [])) or "no indicado"
            responsables = ", ".join(list(tramo.get("responsables_activos") or [])) or "no indicado"
            capacidad = tramo.get("capacidad")
            umbral = capacidad if capacidad not in (None, "") else "no indicado"
            print_fn(f"- Recurso(s): {recurso}")
            print_fn(f"  Intervalo: {intervalo}")
            print_fn(f"  Ocupaciones simultáneas: {cantidad}")
            print_fn(f"  Tareas implicadas: {tareas}")
            print_fn(f"  Responsables implicados: {responsables}")
            print_fn(f"  Umbral/capacidad: {umbral}")
            print_fn("  Nota: simultaneidad detectada; no implica conflicto confirmado por sí sola.")
        incompletos = list(simultaneidad.get("datos_incompletos") or [])
        if incompletos:
            print_fn("\nIncidencias de datos de simultaneidad:")
            for dato in incompletos:
                print_fn(f"- {dato.get('tipo') or 'dato_incompleto'}")

    @staticmethod
    def _mostrar_conflictos_recursos(panel: dict[str, Any], print_fn) -> None:
        conflictos = dict(panel.get("conflictos_recursos") or {})
        items = list(conflictos.get("conflictos") or [])
        print_fn("\nDETALLE DE CONFLICTOS DE RECURSOS")
        if not conflictos:
            print_fn("Sin información de conflictos disponible.")
            return
        if not items:
            print_fn("No se detectan conflictos de recursos en este plan.")
            return
        for conflicto in items:
            tareas = ", ".join(list(conflicto.get("tareas_afectadas") or [])) or "no indicado"
            temporal = "real" if conflicto.get("datos_reales") else ("estimado" if conflicto.get("datos_estimados") else "no indicado")
            print_fn(f"- ID: {conflicto.get('id') or 'no indicado'}")
            print_fn(f"  Severidad: {conflicto.get('severidad') or 'no indicado'}")
            print_fn(f"  Recurso: {conflicto.get('recurso') or 'no indicado'}")
            print_fn(f"  Responsable: {conflicto.get('responsable') or 'no indicado'}")
            print_fn(f"  Tareas: {tareas}")
            print_fn(f"  Intervalo: {conflicto.get('intervalo') or 'no indicado'}")
            print_fn(f"  Descripción: {conflicto.get('descripcion') or 'no indicado'}")
            print_fn(f"  Origen: {conflicto.get('origen') or 'no indicado'}")
            print_fn(f"  Carácter temporal: {temporal}")

    @staticmethod
    def _seleccionar_tarea(tareas, input_fn, print_fn):
        sel = input_fn("Número de tarea (0=cancelar): ").strip()
        if sel == "0": return None
        if not sel.isdigit() or not 1 <= int(sel) <= len(tareas):
            print_fn("Selección no válida."); return None
        return tareas[int(sel)-1]


__all__ = ["ConsolaProduccionGuiadaPiloto13"]
