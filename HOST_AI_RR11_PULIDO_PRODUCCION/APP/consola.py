from __future__ import annotations

from datetime import date
from CORE.orquestador import SolicitudHostAI


class AppConsolaHostAI:
    """
    App Base Ejecutable Host AI 3.0.0.

    Primera capa de uso real por terminal.
    No sustituye la futura interfaz gráfica, pero permite usar Host AI como programa.
    """

    def __init__(self, core):
        self.core = core
        self.ultimo_evento_id = None
        self.ultimo_plan_produccion_id = None

    @staticmethod
    def _preguntar_si_no(mensaje, por_defecto=None):
        sufijo = " [s/n]"
        if por_defecto is True:
            sufijo = " [S/n]"
        elif por_defecto is False:
            sufijo = " [s/N]"
        while True:
            valor = input(mensaje + sufijo + ": ").strip().lower()
            if not valor and por_defecto is not None:
                return por_defecto
            if valor in {"s", "si", "sí", "y", "yes"}:
                return True
            if valor in {"n", "no"}:
                return False
            print("Responde 's' para sí, 'n' para no o pulsa Enter para cancelar cuando se indique.")

    @staticmethod
    def _seleccionar_elemento(elementos, prompt="Selecciona número o ID", permitir_id=True, id_key="id", auto_unico=False):
        if not elementos:
            return None
        if auto_unico and len(elementos) == 1:
            print("Se ha seleccionado automáticamente el único resultado.")
            return elementos[0]
        while True:
            eleccion = input(f"{prompt} (Enter=cancelar): ").strip()
            if not eleccion or eleccion == "0":
                print("Operación cancelada.")
                return None
            if eleccion.isdigit() and 1 <= int(eleccion) <= len(elementos):
                return elementos[int(eleccion) - 1]
            if permitir_id:
                for elemento in elementos:
                    if str(elemento.get(id_key, "")).lower() == eleccion.lower():
                        return elemento
            print(f"Selección no válida. Escribe un número entre 1 y {len(elementos)}" + (" o un ID válido." if permitir_id else "."))

    def ejecutar(self):
        self._cabecera()
        while True:
            self._menu_principal()
            opcion = input("Elige una opción: ").strip()

            if opcion == "1":
                self._hablar_host_ai()
            elif opcion == "2":
                self._menu_eventos()
            elif opcion == "3":
                self._menu_stock()
            elif opcion == "4":
                self._menu_compras()
            elif opcion == "5":
                self._menu_escandallos()
            elif opcion == "6":
                self._menu_costes()
            elif opcion == "7":
                self._menu_produccion_real()
            elif opcion == "8":
                self._estado_sistema()
            elif opcion == "9":
                self._menu_base_datos()
            elif opcion == "10":
                self._menu_excel()
            elif opcion == "11":
                self._probar_comprension_ia11()
            elif opcion == "0":
                print("Saliendo de Host AI.")
                break
            else:
                print("Opción no válida.")

    def _cabecera(self):
        print("=" * 70)
        print("HOST AI 3.0.0 - APP BASE EJECUTABLE")
        print("=" * 70)

    def _menu_principal(self):
        print("\nMENÚ PRINCIPAL")
        print("1. Hablar con Host AI")
        print("2. Eventos")
        print("3. Stock")
        print("4. Compras")
        print("5. Escandallos")
        print("6. Costes")
        print("7. Producción real")
        print("8. Estado del sistema")
        print("9. Base de datos local")
        print("10. Excel / importaciones")
        print("11. IA1.4 Integración con motores (propuesta segura, no ejecutar)")
        print("0. Salir")

    # ------------------------------------------------------------------
    # CHAT
    # ------------------------------------------------------------------
    def _hablar_host_ai(self):
        print("\nHabla con Host AI. Escribe 'salir' para volver.")
        while True:
            texto = input("Tú: ").strip()
            if texto.lower() in {"salir", "volver", "0"}:
                break

            contexto = {}
            if self.ultimo_evento_id:
                contexto["evento_id"] = self.ultimo_evento_id

            r = self.core.orquestador.resolver(SolicitudHostAI("chat_host_ai", {
                "texto": texto,
                "contexto": contexto,
            }))
            print("Host AI:", r.mensaje)

            # Guarda último evento si el chat crea uno.
            try:
                evento = r.datos["resultado"]["datos"]["evento"]
                self.ultimo_evento_id = evento["id"]
                print(f"Evento activo: {self.ultimo_evento_id}")
            except Exception:
                pass

    def _probar_comprension_ia11(self):
        print("\nIA1.4 — INTEGRACIÓN CON MOTORES, PROPUESTA SEGURA")
        print("Responde a las preguntas con frases cortas. Escribe 'cancelar' para borrar el contexto o 'salir' para volver.")
        sesion = "consola_base"
        self.core.comprension_conversacional_ia13.reiniciar(sesion)
        while True:
            texto = input("Tú: ").strip()
            if texto.lower() in {"salir", "volver", "0"}:
                self.core.comprension_conversacional_ia13.reiniciar(sesion)
                return
            contexto = {"evento_id": self.ultimo_evento_id} if self.ultimo_evento_id else {}
            resultado = self.core.integracion_motores_ia14.analizar(texto, sesion, contexto)
            print("Host AI:", resultado["respuesta"])
            interpretacion = resultado.get("interpretacion", {})
            if resultado.get("intent") != "conversacion_general":
                print(f"Intención: {resultado['intent']}")
            if resultado.get("pipeline"):
                print(f"Contrato: {resultado['pipeline']} -> {resultado['accion']}")
            if resultado.get("parametros"):
                print("Parámetros propuestos:")
                for clave, valor in resultado["parametros"].items():
                    print(f"- {clave}: {valor}")
            if interpretacion.get("faltan"):
                print("Pendiente conversacional: " + ", ".join(interpretacion["faltan"]))
            if resultado.get("faltan_motor"):
                print("Pendiente técnico: " + ", ".join(resultado["faltan_motor"]))
            if resultado.get("propuesta_valida"):
                confirmacion = "sí" if resultado.get("requiere_confirmacion") else "no"
                print(f"Propuesta validada | Riesgo: {resultado['riesgo']} | Requiere confirmación: {confirmacion}")
            print("Modo seguro IA1.4: no se han ejecutado motores ni modificado datos.")

    # ------------------------------------------------------------------
    # EVENTOS
    # ------------------------------------------------------------------
    def _menu_eventos(self):
        while True:
            print("\nEVENTOS")
            print("1. Crear evento rápido")
            print("2. Listar y seleccionar eventos")
            print("3. Buscar evento")
            print("4. Editar evento activo")
            print("5. Eliminar evento activo")
            print("6. Duplicar evento activo")
            print("7. Gestionar servicios del evento activo")
            print("8. Gestionar pases y recetas")
            print("9. Ver línea temporal del evento activo")
            print("10. Ver ficha completa del evento activo")
            print("11. Ver resumen ejecutivo")
            print("0. Volver")
            self._mostrar_evento_activo()
            op = input("Elige una opción: ").strip()

            if op == "0":
                return
            if op == "1":
                self._crear_evento_rapido()
            elif op == "2":
                self._listar_y_seleccionar_eventos()
            elif op == "3":
                self._buscar_y_seleccionar_evento()
            elif op == "4":
                self._editar_evento_activo()
            elif op == "5":
                self._eliminar_evento_activo()
            elif op == "6":
                self._duplicar_evento_activo()
            elif op == "7":
                self._gestionar_servicios_evento_activo()
            elif op == "8":
                self._gestionar_pases_evento_activo()
            elif op == "9":
                self._ver_linea_temporal_evento_activo()
            elif op == "10":
                self._ver_ficha_evento_activo()
            elif op == "11":
                self._ver_resumen_ejecutivo_evento_activo()
            else:
                print("Opción no válida.")

    def _mostrar_evento_activo(self):
        if not self.ultimo_evento_id:
            print("Evento activo: ninguno")
            return
        try:
            evento = self.core.eventos.obtener(self.ultimo_evento_id)
            hora = f" {evento.hora_inicio}" if evento.hora_inicio else ""
            print(f"Evento activo: {evento.nombre} | {evento.fecha}{hora} | {evento.pax} pax | {evento.estado} | {evento.id}")
        except ValueError:
            self.ultimo_evento_id = None
            print("Evento activo: ninguno")

    @staticmethod
    def _imprimir_eventos(eventos):
        if not eventos:
            print("No hay eventos para mostrar.")
            return
        for indice, evento in enumerate(eventos, start=1):
            cliente = f" | Cliente: {evento.get('cliente')}" if evento.get("cliente") else ""
            hora = f" {evento.get('hora_inicio')}" if evento.get("hora_inicio") else ""
            print(f"{indice}. {evento['fecha']}{hora} | {evento['nombre']} | {evento['pax']} pax | {evento.get('estado', 'pendiente')} | {evento['tipo']}{cliente} | {evento['id']}")

    def _seleccionar_evento_de_lista(self, eventos):
        if not eventos:
            return False
        seleccion = input("Número del evento para activarlo (vacío=cancelar): ").strip()
        if not seleccion:
            return False
        try:
            indice = int(seleccion) - 1
            evento = eventos[indice]
        except (ValueError, IndexError):
            print("Selección no válida.")
            return False
        self.ultimo_evento_id = evento["id"]
        print(f"Evento activo: {evento['nombre']} ({evento['id']}).")
        return True

    def _crear_evento_rapido(self):
        print("Deja vacíos los datos opcionales que no conozcas todavía.")
        nombre = input("Nombre del evento: ").strip() or "Evento Demo"
        try:
            pax = int(input("Pax: ").strip() or "0")
        except ValueError:
            print("Los pax deben ser un número entero.")
            return
        tipo = input("Tipo (boda/catering/evento): ").strip() or "evento"
        fecha_txt = input("Fecha (ej. 22/10/2026, mañana o viernes; vacío=hoy): ").strip()
        cliente = input("Cliente: ").strip()
        telefono = input("Teléfono: ").strip()
        email = input("Email: ").strip()
        ubicacion = input("Ubicación: ").strip()
        hora_inicio = input("Hora principal HH:MM (opcional): ").strip()
        observaciones = input("Observaciones (opcional): ").strip()
        estado = self._pedir_estado("pendiente")
        r = self.core.orquestador.resolver(SolicitudHostAI("crear_evento", {
            "nombre": nombre,
            "fecha": fecha_txt or date.today().isoformat(),
            "pax": pax,
            "tipo": tipo,
            "cliente": cliente,
            "telefono": telefono,
            "email": email,
            "ubicacion": ubicacion,
            "hora_inicio": hora_inicio,
            "observaciones": observaciones,
            "estado": estado,
        }))
        print(r.mensaje)
        if r.ok:
            self.ultimo_evento_id = r.datos["evento"]["id"]
            print(f"Evento activo: {self.ultimo_evento_id}")

    def _pedir_estado(self, actual="pendiente"):
        estados = list(self.core.eventos.ESTADOS)
        print("Estados: " + ", ".join(estados))
        valor = input(f"Estado [{actual}]: ").strip()
        return valor or actual

    @staticmethod
    def _valor_editable(etiqueta, actual):
        mostrado = actual if actual not in (None, "") else "-"
        return input(f"{etiqueta} [{mostrado}] (vacío=mantener, -=borrar): ").strip()


    def _listar_y_seleccionar_eventos(self):
        r = self.core.orquestador.resolver(SolicitudHostAI("listar_eventos", {}))
        print(r.mensaje)
        eventos = r.datos.get("eventos", [])
        self._imprimir_eventos(eventos)
        self._seleccionar_evento_de_lista(eventos)

    def _buscar_y_seleccionar_evento(self):
        texto = input("Buscar por nombre, fecha, cliente, tipo, ubicación o ID: ").strip()
        r = self.core.orquestador.resolver(SolicitudHostAI("buscar_eventos", {"texto": texto}))
        print(r.mensaje)
        eventos = r.datos.get("eventos", [])
        self._imprimir_eventos(eventos)
        self._seleccionar_evento_de_lista(eventos)

    def _editar_evento_activo(self):
        if not self._requiere_evento():
            return
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        print("Deja un campo vacío para conservarlo. Escribe - para borrar un dato opcional.")
        entradas = {
            "nombre": self._valor_editable("Nombre", evento.nombre),
            "fecha": self._valor_editable("Fecha", evento.fecha),
            "pax": self._valor_editable("Pax", evento.pax),
            "tipo": self._valor_editable("Tipo", evento.tipo),
            "cliente": self._valor_editable("Cliente", evento.cliente),
            "telefono": self._valor_editable("Teléfono", evento.telefono),
            "email": self._valor_editable("Email", evento.email),
            "ubicacion": self._valor_editable("Ubicación", evento.ubicacion),
            "hora_inicio": self._valor_editable("Hora principal HH:MM", evento.hora_inicio),
            "observaciones": self._valor_editable("Observaciones", evento.observaciones),
        }
        estado = self._pedir_estado(evento.estado)
        cambios = {}
        opcionales = {"cliente", "telefono", "email", "ubicacion", "hora_inicio", "observaciones"}
        for campo, valor in entradas.items():
            if not valor:
                continue
            if valor == "-" and campo in opcionales:
                cambios[campo] = ""
            else:
                cambios[campo] = valor
        if "pax" in cambios:
            try:
                cambios["pax"] = int(cambios["pax"])
            except ValueError:
                print("Los pax deben ser un número entero. No se ha modificado el evento.")
                return
        if estado != evento.estado:
            cambios["estado"] = estado
        if not cambios:
            print("No se han indicado cambios.")
            return
        r = self.core.orquestador.resolver(SolicitudHostAI("editar_evento", {
            "evento_id": self.ultimo_evento_id,
            "cambios": cambios,
        }))
        print(r.mensaje)


    def _eliminar_evento_activo(self):
        if not self._requiere_evento():
            return
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        confirmacion = input(f"Escribe ELIMINAR para borrar '{evento.nombre}': ").strip()
        if confirmacion != "ELIMINAR":
            print("Eliminación cancelada.")
            return
        r = self.core.orquestador.resolver(SolicitudHostAI("eliminar_evento", {
            "evento_id": self.ultimo_evento_id,
        }))
        print(r.mensaje)
        if r.ok:
            self.ultimo_evento_id = None

    def _duplicar_evento_activo(self):
        if not self._requiere_evento():
            return
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        nombre = input(f"Nombre del duplicado [{evento.nombre} (copia)]: ").strip() or None
        fecha = input(f"Fecha del duplicado [{evento.fecha}]: ").strip() or None
        r = self.core.orquestador.resolver(SolicitudHostAI("duplicar_evento", {
            "evento_id": self.ultimo_evento_id,
            "nombre": nombre,
            "fecha": fecha,
        }))
        print(r.mensaje)
        if r.ok:
            self.ultimo_evento_id = r.datos["evento"]["id"]
            print(f"Evento activo: {self.ultimo_evento_id}")

    @staticmethod
    def _seleccionar_por_numero(elementos, etiqueta):
        if not elementos:
            print(f"No hay {etiqueta}.")
            return None
        valor = input(f"Número de {etiqueta[:-1] if etiqueta.endswith('s') else etiqueta} (vacío=cancelar): ").strip()
        if not valor:
            return None
        try:
            return elementos[int(valor) - 1]
        except (ValueError, IndexError):
            print("Selección no válida.")
            return None

    def _listar_servicios_evento_activo(self):
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        if not evento.servicios:
            print("El evento no tiene servicios.")
            return []
        for indice, servicio in enumerate(evento.servicios, start=1):
            print(f"{indice}. {servicio.hora_inicio} | {servicio.nombre} | {servicio.duracion_min} min | {len(servicio.pases)} pases")
        return evento.servicios

    def _gestionar_servicios_evento_activo(self):
        if not self._requiere_evento():
            return
        while True:
            print("\nSERVICIOS DEL EVENTO")
            print("1. Añadir servicio")
            print("2. Listar servicios")
            print("3. Editar servicio")
            print("4. Eliminar servicio")
            print("5. Duplicar servicio")
            print("0. Volver")
            op = input("Elige una opción: ").strip()
            if op == "0":
                return
            if op == "1":
                nombre = input("Nombre servicio: ").strip() or "Servicio"
                tipo = input(f"Tipo [{nombre.lower()}]: ").strip() or nombre.lower()
                hora = input("Hora inicio HH:MM: ").strip() or "20:00"
                try:
                    duracion = int(input("Duración estimada en minutos [180]: ").strip() or "180")
                    evento = self.core.eventos.agregar_servicio(self.ultimo_evento_id, nombre, tipo, hora, duracion)
                    servicio = evento.servicios[-1]
                    print(f"Servicio añadido: {servicio.nombre} a las {servicio.hora_inicio}.")
                    self._continuar_evento("servicio")
                except (ValueError, TypeError) as exc:
                    print(f"No se ha podido añadir el servicio: {exc}")
            elif op == "2":
                self._listar_servicios_evento_activo()
            elif op in {"3", "4", "5"}:
                servicios = self._listar_servicios_evento_activo()
                servicio = self._seleccionar_por_numero(servicios, "servicios")
                if not servicio:
                    continue
                if op == "3":
                    cambios = {}
                    nombre = self._valor_editable("Nombre", servicio.nombre)
                    tipo = self._valor_editable("Tipo", servicio.tipo)
                    hora = self._valor_editable("Hora HH:MM", servicio.hora_inicio)
                    duracion = self._valor_editable("Duración min", servicio.duracion_min)
                    if nombre and nombre != "-": cambios["nombre"] = nombre
                    if tipo and tipo != "-": cambios["tipo"] = tipo
                    if hora and hora != "-": cambios["hora_inicio"] = hora
                    if duracion and duracion != "-": cambios["duracion_min"] = int(duracion)
                    if cambios:
                        self.core.eventos.editar_servicio(self.ultimo_evento_id, servicio.id, cambios)
                        print("Servicio actualizado.")
                elif op == "4":
                    confirmar = input(f"Escribe ELIMINAR para borrar '{servicio.nombre}' y sus pases: ").strip()
                    if confirmar == "ELIMINAR":
                        self.core.eventos.eliminar_servicio(self.ultimo_evento_id, servicio.id)
                        print("Servicio eliminado.")
                    else:
                        print("Eliminación cancelada.")
                else:
                    nombre = input(f"Nombre del duplicado [{servicio.nombre} (copia)]: ").strip() or None
                    self.core.eventos.duplicar_servicio(self.ultimo_evento_id, servicio.id, nombre)
                    print("Servicio duplicado con pases y recetas.")
            else:
                print("Opción no válida.")

    def _seleccionar_servicio_evento_activo(self):
        servicios = self._listar_servicios_evento_activo()
        if len(servicios) == 1:
            return servicios[0]
        return self._seleccionar_por_numero(servicios, "servicios")

    def _listar_pases(self, servicio):
        if not servicio.pases:
            print(f"El servicio '{servicio.nombre}' no tiene pases.")
            return []
        for indice, pase in enumerate(servicio.pases, start=1):
            recetas = ", ".join(pase.recetas) if pase.recetas else "sin recetas"
            print(f"{indice}. {pase.hora_inicio} | {pase.nombre} | {pase.duracion_min} min | {recetas}")
        return servicio.pases

    def _catalogo_recetas(self):
        try:
            return self.core.escandallos_inteligente.listar()
        except Exception:
            return []

    def _buscar_recetas_para_pase(self):
        catalogo = self._catalogo_recetas()
        seleccionadas = []
        if not catalogo:
            texto = input("Recetas por ID separadas por coma: ").strip()
            return [r.strip() for r in texto.split(",") if r.strip()]
        while True:
            termino = input("Buscar receta por nombre o ID (vacío=terminar): ").strip()
            if not termino:
                break
            termino_norm = termino.lower()
            coincidencias = [r for r in catalogo if termino_norm in str(r.get("receta_id", "")).lower() or termino_norm in str(r.get("nombre", "")).lower()]
            if not coincidencias:
                print("No se han encontrado recetas.")
                continue
            for indice, receta in enumerate(coincidencias[:20], start=1):
                print(f"{indice}. {receta.get('nombre')} | {receta.get('receta_id')}")
            eleccion = input("Número para añadir (vacío=otra búsqueda): ").strip()
            if not eleccion:
                continue
            try:
                receta_id = coincidencias[int(eleccion)-1]["receta_id"]
            except (ValueError, IndexError, KeyError):
                print("Selección no válida.")
                continue
            if receta_id not in seleccionadas:
                seleccionadas.append(receta_id)
                print(f"Añadida: {receta_id}")
        return seleccionadas

    def _gestionar_pases_evento_activo(self):
        if not self._requiere_evento():
            return
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        if not evento.servicios:
            print("Primero añade un servicio.")
            return
        while True:
            print("\nPASES Y RECETAS")
            print("1. Añadir pase")
            print("2. Listar pases")
            print("3. Editar pase")
            print("4. Eliminar pase")
            print("5. Duplicar pase")
            print("0. Volver")
            op = input("Elige una opción: ").strip()
            if op == "0":
                return
            servicio = self._seleccionar_servicio_evento_activo()
            if not servicio:
                continue
            if op == "1":
                nombre = input("Nombre pase: ").strip() or "Pase"
                hora = input("Hora pase HH:MM: ").strip() or servicio.hora_inicio
                try:
                    duracion = int(input("Duración estimada en minutos [35]: ").strip() or "35")
                except ValueError:
                    print("La duración debe ser un número entero.")
                    continue
                recetas = self._buscar_recetas_para_pase()
                notas = input("Notas (opcional): ").strip()
                try:
                    evento = self.core.eventos.agregar_pase(self.ultimo_evento_id, servicio.id, nombre, hora, duracion, recetas, notas)
                    print(f"Pase añadido: {nombre} con {len(recetas)} recetas.")
                    self._continuar_evento("pase")
                except ValueError as exc:
                    print(f"No se ha podido añadir el pase: {exc}")
            elif op == "2":
                self._listar_pases(servicio)
            elif op in {"3", "4", "5"}:
                pases = self._listar_pases(servicio)
                pase = self._seleccionar_por_numero(pases, "pases")
                if not pase:
                    continue
                if op == "3":
                    cambios = {}
                    nombre = self._valor_editable("Nombre", pase.nombre)
                    hora = self._valor_editable("Hora HH:MM", pase.hora_inicio)
                    duracion = self._valor_editable("Duración min", pase.duracion_min)
                    if nombre and nombre != "-": cambios["nombre"] = nombre
                    if hora and hora != "-": cambios["hora_inicio"] = hora
                    if duracion and duracion != "-": cambios["duracion_min"] = int(duracion)
                    cambiar_recetas = input("¿Cambiar recetas? (s/n): ").strip().lower()
                    if cambiar_recetas == "s": cambios["recetas"] = self._buscar_recetas_para_pase()
                    notas = self._valor_editable("Notas", pase.notas)
                    if notas == "-": cambios["notas"] = ""
                    elif notas: cambios["notas"] = notas
                    if cambios:
                        self.core.eventos.editar_pase(self.ultimo_evento_id, servicio.id, pase.id, cambios)
                        print("Pase actualizado.")
                elif op == "4":
                    confirmar = input(f"Escribe ELIMINAR para borrar '{pase.nombre}': ").strip()
                    if confirmar == "ELIMINAR":
                        self.core.eventos.eliminar_pase(self.ultimo_evento_id, servicio.id, pase.id)
                        print("Pase eliminado.")
                    else:
                        print("Eliminación cancelada.")
                else:
                    nombre = input(f"Nombre del duplicado [{pase.nombre} (copia)]: ").strip() or None
                    self.core.eventos.duplicar_pase(self.ultimo_evento_id, servicio.id, pase.id, nombre)
                    print("Pase duplicado con sus recetas.")
            else:
                print("Opción no válida.")

    def _continuar_evento(self, origen):
        print("\n¿QUÉ QUIERES HACER AHORA?")
        print("1. Seguir en este apartado")
        print("2. Ver línea temporal")
        print("3. Ver resumen ejecutivo")
        print("0. Volver al menú de Eventos")
        op = input("Elige una opción: ").strip()
        if op == "2":
            self._ver_linea_temporal_evento_activo()
        elif op == "3":
            self._ver_resumen_ejecutivo_evento_activo()

    def _ver_linea_temporal_evento_activo(self):
        if not self._requiere_evento():
            return
        datos = self.core.eventos.construir_linea_temporal(self.ultimo_evento_id)
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        print("\n" + "=" * 62)
        print(f"LÍNEA TEMPORAL — {evento.nombre} | {evento.fecha}")
        print("=" * 62)
        if not datos["linea_temporal"]:
            print("Todavía no hay servicios ni pases programados.")
        for item in datos["linea_temporal"]:
            if item["tipo"] == "servicio":
                print(f"{item['hora']}  SERVICIO  {item['nombre']} ({item['duracion_min']} min)")
            else:
                recetas = ", ".join(item.get("recetas", [])) or "sin recetas"
                print(f"{item['hora']}    PASE    {item['nombre']} — {item['servicio']}")
                print(f"          Recetas: {recetas}")
        print("=" * 62)

    def _ver_ficha_evento_activo(self):
        if not self._requiere_evento():
            return
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        print("\n" + "=" * 62)
        print(f"FICHA DEL EVENTO — {evento.nombre}")
        print("=" * 62)
        print(f"ID: {evento.id}")
        print(f"Estado: {evento.estado}")
        print(f"Fecha: {evento.fecha}")
        print(f"Hora principal: {evento.hora_inicio or '-'}")
        print(f"Pax: {evento.pax}")
        print(f"Tipo: {evento.tipo}")
        print(f"Cliente: {evento.cliente or '-'}")
        print(f"Teléfono: {evento.telefono or '-'}")
        print(f"Email: {evento.email or '-'}")
        print(f"Ubicación: {evento.ubicacion or '-'}")
        print(f"Observaciones: {evento.observaciones or '-'}")
        print(f"Servicios: {len(evento.servicios)}")
        print(f"Pases: {sum(len(s.pases) for s in evento.servicios)}")
        print(f"Recetas: {sum(len(p.recetas) for s in evento.servicios for p in s.pases)}")
        print("=" * 62)

    def _ver_resumen_ejecutivo_evento_activo(self):
        if not self._requiere_evento():
            return
        resumen = self.core.eventos.resumen_ejecutivo(self.ultimo_evento_id)
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        totales = resumen["totales"]
        print("\n" + "=" * 62)
        print(f"RESUMEN DEL EVENTO — {evento.nombre}")
        print("=" * 62)
        print(f"Fecha y hora: {evento.fecha} {evento.hora_inicio or ''}".rstrip())
        print(f"Estado: {evento.estado}")
        print(f"Cliente: {evento.cliente or '-'}")
        print(f"Ubicación: {evento.ubicacion or '-'}")
        print(f"Pax: {evento.pax}")
        print("-" * 62)
        print(f"Servicios: {totales['servicios']}")
        print(f"Pases: {totales['pases']}")
        print(f"Recetas añadidas: {totales['recetas']} ({totales['recetas_unicas']} únicas)")
        print("Producción: pendiente de generar")
        print("Stock: pendiente de comprobar")
        print("Compras: pendientes de generar")
        print("Costes: pendientes de calcular")
        if resumen["avisos"]:
            print("-" * 62)
            print("REVISAR:")
            for aviso in resumen["avisos"]:
                print(f"- {aviso}")
        else:
            print("Estado operativo: estructura del evento completa.")
        print("=" * 62)

    # ------------------------------------------------------------------
    # STOCK
    # ------------------------------------------------------------------
    def _menu_stock(self):
        while True:
            print("\nSTOCK OPERATIVO")
            print("1. Registrar entrada")
            print("2. Registrar varias entradas")
            print("3. Ver / filtrar stock actual")
            print("4. Gestionar lotes, ubicaciones y caducidades")
            print("5. Registrar merma")
            print("6. Ajustar inventario físico")
            print("7. Historial de movimientos")
            print("8. Diagnosticar stock")
            print("9. Resumen operativo")
            print("10. Corregir última entrada")
            print("0. Volver")
            op = input("Elige una opción: ").strip()

            if op == "0":
                return
            if op == "1":
                self._registrar_entrada_stock()
            elif op == "2":
                self._registrar_varias_entradas_stock()
            elif op == "3":
                self._ver_stock_actual_con_filtros()
            elif op == "4":
                self._gestionar_lotes_stock()
            elif op == "5":
                self._registrar_merma_stock()
            elif op == "6":
                self._ajustar_inventario_stock()
            elif op == "7":
                self._historial_movimientos_stock()
            elif op == "8":
                self._diagnosticar_stock_operativo()
            elif op == "9":
                self._resumen_operativo_stock()
            elif op == "10":
                self._corregir_ultima_entrada_stock()
            else:
                print("Opción no válida.")

    def _cargar_catalogo_articulos(self):
        try:
            return self.core.db.cargar("articulos")
        except Exception:
            import json
            ruta = self.core.base_dir / "DATOS" / "db" / "articulos.json"
            try:
                datos = json.loads(ruta.read_text(encoding="utf-8"))
                return datos if isinstance(datos, list) else []
            except Exception:
                return []

    def _guardar_catalogo_articulos(self, articulos):
        import json
        ruta = self.core.base_dir / "DATOS" / "db" / "articulos.json"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

    def _crear_articulo_catalogo_stock(self, nombre, familia="", proveedor=""):
        from datetime import datetime
        articulos = self._cargar_catalogo_articulos()
        existentes = {str(a.get("codigo") or "") for a in articulos}
        numero = 1
        while f"ART{numero:06d}" in existentes:
            numero += 1
        articulo = {
            "codigo": f"ART{numero:06d}",
            "nombre": nombre,
            "observaciones": "Creado desde entrada de stock",
            "proveedor": proveedor or None,
            "familia": familia or None,
            "precio": None,
            "activo": True,
            "origen": "stock_manual",
            "fecha_importacion": datetime.now().isoformat(timespec="seconds"),
        }
        articulos.append(articulo)
        self._guardar_catalogo_articulos(articulos)
        return articulo

    def _buscar_catalogo_articulos(self, texto):
        texto = (texto or "").strip().lower()
        if not texto:
            return []
        candidatos = []
        for art in self._cargar_catalogo_articulos():
            nombre = str(art.get("nombre") or art.get("articulo") or "")
            codigo = str(art.get("codigo") or art.get("id") or "")
            proveedor = str(art.get("proveedor") or "")
            if texto in nombre.lower() or texto in codigo.lower() or texto in proveedor.lower():
                candidatos.append(art)
        candidatos.sort(key=lambda x: (0 if str(x.get("nombre", "")).lower().startswith(texto) else 1, str(x.get("nombre", "")).lower()))
        return candidatos[:10]

    def _seleccionar_articulo_stock(self):
        termino = input("Artículo o parte del nombre (Enter/0=cancelar): ").strip()
        if not termino or termino == "0":
            print("Selección de artículo cancelada.")
            return None
        candidatos = self._buscar_catalogo_articulos(termino)
        if candidatos:
            print("\nARTÍCULOS ENCONTRADOS")
            for i, art in enumerate(candidatos, 1):
                print(f"{i}. {art.get('nombre', '-')} | {art.get('codigo', '-')} | {art.get('proveedor') or 'sin proveedor'}")
            print("0. Escribir como artículo nuevo")
            eleccion = input("Selecciona artículo: ").strip()
            if eleccion.isdigit() and 1 <= int(eleccion) <= len(candidatos):
                art = candidatos[int(eleccion) - 1]
                return {
                    "nombre": art.get("nombre") or termino,
                    "articulo_id": art.get("codigo") or art.get("id") or "",
                    "familia": art.get("familia") or "",
                    "proveedor": art.get("proveedor") or "",
                }
        confirmar = self._preguntar_si_no(
            f"No se ha seleccionado un artículo existente. ¿Crear '{termino}' como artículo nuevo?",
            por_defecto=False,
        )
        if not confirmar:
            return None
        familia = input("Familia (opcional): ").strip()
        proveedor = input("Proveedor habitual (opcional): ").strip()
        creado = self._crear_articulo_catalogo_stock(termino, familia, proveedor)
        print(f"Artículo creado: {creado['nombre']} ({creado['codigo']}).")
        return {"nombre": creado["nombre"], "articulo_id": creado["codigo"], "familia": familia, "proveedor": proveedor}

    def _normalizar_fecha_stock(self, texto):
        from datetime import datetime
        texto = (texto or "").strip()
        if not texto:
            return ""
        for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
            try:
                return datetime.strptime(texto, formato).date().isoformat()
            except ValueError:
                pass
        print("Fecha no reconocida. Usa DD/MM/AAAA o AAAA-MM-DD.")
        return None

    def _registrar_entrada_stock(self):
        articulo = self._seleccionar_articulo_stock()
        if not articulo:
            print("Entrada cancelada.")
            return False
        try:
            cantidad = float(input("Cantidad: ").strip() or "0")
        except ValueError:
            print("Cantidad no válida.")
            return False
        if cantidad <= 0:
            print("La cantidad debe ser mayor que cero.")
            return False
        unidad = input("Unidad: ").strip() or "kg"
        ubicacion = input("Ubicación (cámara/congelador/seco/producción/otra, opcional): ").strip()
        caducidad_txt = input("Caducidad (DD/MM/AAAA, opcional): ").strip()
        caducidad = self._normalizar_fecha_stock(caducidad_txt)
        if caducidad is None:
            return False
        coste_txt = input("Coste unitario (opcional): ").strip().replace(",", ".")
        try:
            coste_unitario = float(coste_txt) if coste_txt else 0.0
        except ValueError:
            print("Coste no válido.")
            return False
        r = self.core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {
            **articulo,
            "cantidad": cantidad,
            "unidad": unidad,
            "ubicacion": ubicacion,
            "caducidad": caducidad,
            "coste_unitario": coste_unitario,
        }))
        print(r.mensaje)
        return bool(r.ok)

    def _registrar_varias_entradas_stock(self):
        total = 0
        while True:
            if self._registrar_entrada_stock():
                total += 1
            seguir = input("¿Registrar otro artículo? (s/n): ").strip().lower()
            if seguir not in {"s", "si", "sí", "y", "yes"}:
                break
        print(f"Recepción terminada: {total} entradas registradas.")

    def _ver_stock_actual_con_filtros(self):
        texto = input("Buscar artículo (vacío=todos): ").strip().lower()
        ubicacion = input("Filtrar ubicación (vacío=todas): ").strip().lower()
        familia = input("Filtrar familia (vacío=todas): ").strip().lower()
        estado = input("Estado [todos/con stock/sin stock/caduca pronto]: ").strip().lower() or "todos"
        r = self.core.orquestador.resolver(SolicitudHostAI("stock_actual", {}))
        items = []
        for item in r.datos.get("items", []):
            lotes = item.get("lotes", [])
            if texto and texto not in str(item.get("nombre", "")).lower() and texto not in str(item.get("articulo_id", "")).lower():
                continue
            if familia and familia not in str(item.get("familia", "")).lower():
                continue
            if ubicacion and not any(ubicacion in str(l.get("ubicacion", "")).lower() for l in lotes):
                continue
            if estado == "con stock" and float(item.get("cantidad", 0)) <= 0:
                continue
            if estado == "sin stock" and float(item.get("cantidad", 0)) > 0:
                continue
            if estado == "caduca pronto":
                alertas_ids = {a.get("lote", {}).get("id") for a in self.core.stock.diagnosticar_stock(7).get("avisos", []) if a.get("tipo") in {"caducado", "caducidad_cercana"}}
                if not any(l.get("id") in alertas_ids for l in lotes):
                    continue
            items.append(item)
        print(f"\nStock encontrado: {len(items)} artículo(s).")
        if not items:
            print("No hay resultados con esos filtros.")
            return
        for item in sorted(items, key=lambda x: str(x.get("nombre", "")).lower()):
            ubicaciones = sorted({l.get("ubicacion") or "sin ubicación" for l in item.get("lotes", []) if float(l.get("cantidad", 0)) > 0})
            print(f"- {item['nombre']}: {item['cantidad']} {item['unidad']} | {', '.join(ubicaciones)} | {len(item.get('lotes', []))} lote(s)")

    def _gestionar_lotes_stock(self):
        texto = input("Buscar lote por artículo, código o ID (vacío=todos): ").strip()
        ubicacion = input("Filtrar ubicación (opcional): ").strip()
        lotes = self.core.stock.lotes_listado(texto=texto, ubicacion=ubicacion)
        if not lotes:
            print("No se encontraron lotes.")
            return
        print("\nLOTES")
        for i, lote in enumerate(lotes, 1):
            print(f"{i}. {lote['nombre']} | {lote['cantidad']} {lote['unidad']} | {lote.get('ubicacion') or 'sin ubicación'} | cad: {lote.get('caducidad') or '-'} | {lote['id']}")
        eleccion = input("Selecciona lote para editar (0=volver): ").strip()
        if not eleccion.isdigit() or not (1 <= int(eleccion) <= len(lotes)):
            return
        lote = lotes[int(eleccion) - 1]
        nueva_ubicacion = input(f"Ubicación [{lote.get('ubicacion') or '-'}] (Enter=mantener, '-'=vaciar): ").strip()
        cad_txt = input(f"Caducidad [{lote.get('caducidad') or '-'}] (Enter=mantener, '-'=vaciar): ").strip()
        ubicacion_val = None if nueva_ubicacion == "" else ("" if nueva_ubicacion == "-" else nueva_ubicacion)
        if cad_txt == "":
            cad_val = None
        elif cad_txt == "-":
            cad_val = ""
        else:
            cad_val = self._normalizar_fecha_stock(cad_txt)
            if cad_val is None:
                return
        resultado = self.core.stock.actualizar_lote(lote["id"], ubicacion=ubicacion_val, caducidad=cad_val)
        print(resultado.get("mensaje"))

    def _seleccionar_item_stock_actual(self):
        termino = input("Artículo en stock: ").strip().lower()
        items = self.core.stock.stock_actual().get("items", [])
        encontrados = [x for x in items if termino in str(x.get("nombre", "")).lower() or termino in str(x.get("articulo_id", "")).lower()]
        if not encontrados:
            print("No se encontró ese artículo en stock.")
            return None
        for i, item in enumerate(encontrados[:10], 1):
            print(f"{i}. {item['nombre']} | {item['cantidad']} {item['unidad']} | {item.get('articulo_id') or '-'}")
        eleccion = input("Selecciona artículo: ").strip()
        if not eleccion.isdigit() or not (1 <= int(eleccion) <= min(len(encontrados), 10)):
            print("Selección cancelada.")
            return None
        return encontrados[int(eleccion) - 1]

    def _registrar_merma_stock(self):
        item = self._seleccionar_item_stock_actual()
        if not item:
            return
        try:
            cantidad = float(input(f"Cantidad de merma ({item['unidad']}): ").strip() or "0")
        except ValueError:
            print("Cantidad no válida.")
            return
        motivo = input("Motivo de la merma: ").strip() or "merma"
        resultado = self.core.stock.registrar_merma(item["nombre"], cantidad, item["unidad"], motivo=motivo, articulo_id=item.get("articulo_id", ""))
        print(resultado["lectura_host_ai"])
        if resultado.get("cantidad_faltante", 0):
            print(f"No se pudo descontar todo. Faltan {resultado['cantidad_faltante']} {item['unidad']}.")

    def _ajustar_inventario_stock(self):
        item = self._seleccionar_item_stock_actual()
        if not item:
            return
        try:
            cantidad_fisica = float(input(f"Cantidad física real ({item['unidad']}): ").strip())
        except ValueError:
            print("Cantidad no válida.")
            return
        motivo = input("Motivo del ajuste: ").strip() or "inventario físico"
        ubicacion = input("Ubicación para ajuste positivo (opcional): ").strip()
        resultado = self.core.stock.ajustar_inventario(
            item["nombre"], cantidad_fisica, item["unidad"], articulo_id=item.get("articulo_id", ""),
            familia=item.get("familia", ""), ubicacion=ubicacion, motivo=motivo,
        )
        print(resultado["lectura_host_ai"])
        print(f"Anterior: {resultado.get('cantidad_anterior', item['cantidad'])} {item['unidad']} | Real: {cantidad_fisica} {item['unidad']}")

    def _historial_movimientos_stock(self):
        termino = input("Artículo, código o tipo de movimiento (vacío=todos): ").strip()
        movimientos = self.core.stock.movimientos_articulo(termino)
        if not movimientos:
            print("No hay movimientos para ese filtro.")
            return
        print(f"\nMOVIMIENTOS: {len(movimientos)}")
        for mov in movimientos[:100]:
            signo = "+" if mov.get("tipo") in {"entrada", "ajuste_positivo"} else "-"
            print(f"- {mov.get('creado_en', '-')} | {mov.get('tipo', '-')} | {mov.get('nombre', '-')} | {signo}{mov.get('cantidad', 0)} {mov.get('unidad', '')} | {mov.get('motivo') or '-'}")

    def _diagnosticar_stock_operativo(self):
        dias_txt = input("Avisar caducidades dentro de cuántos días [3]: ").strip()
        try:
            dias = int(dias_txt or "3")
        except ValueError:
            dias = 3
        resultado = self.core.stock.diagnosticar_stock(dias)
        print(resultado["lectura_host_ai"])
        if not resultado["avisos"]:
            return
        orden = {"alto": 0, "medio": 1, "bajo": 2}
        for aviso in sorted(resultado["avisos"], key=lambda x: orden.get(x.get("nivel"), 9)):
            print(f"- [{aviso.get('nivel', '').upper()}] {aviso.get('mensaje')}")

    def _resumen_operativo_stock(self):
        resumen = self.core.stock.resumen_operativo(7)
        print("\n" + "=" * 62)
        print("RESUMEN OPERATIVO DE STOCK")
        print("=" * 62)
        print(f"Artículos: {resumen['total_articulos']}")
        print(f"Lotes: {resumen['total_lotes']}")
        print(f"Valor estimado: {resumen['valor_total']:.2f} €")
        print(f"Avisos: {resumen['total_avisos']}")
        print(f"Caducados: {resumen['lotes_caducados']} | Caducan pronto: {resumen['lotes_caducan_pronto']}")
        print("\nPOR UBICACIÓN")
        if not resumen["ubicaciones"]:
            print("- Sin stock registrado.")
        for ubic in resumen["ubicaciones"]:
            print(f"- {ubic['ubicacion']}: {ubic['articulos']} artículo(s), {ubic['lotes']} lote(s), {ubic['valor']:.2f} €")
        if resumen["avisos"]:
            print("\nATENCIÓN")
            for aviso in resumen["avisos"][:10]:
                print(f"- {aviso['mensaje']}")
        print("=" * 62)

    def _corregir_ultima_entrada_stock(self):
        ultima = self.core.stock.ultima_entrada()
        if not ultima or not ultima.get("lote"):
            print("No hay entradas de stock para corregir.")
            return
        lote = ultima["lote"]
        print(f"Última entrada: {lote['nombre']} — {lote['cantidad']} {lote['unidad']}")
        confirmar = input("¿Eliminar esta entrada y su movimiento? (s/n): ").strip().lower()
        if confirmar not in {"s", "si", "sí", "y", "yes"}:
            print("Corrección cancelada.")
            return
        resultado = self.core.stock.corregir_ultima_entrada()
        print(resultado["mensaje"])

    # ------------------------------------------------------------------
    # COMPRAS
    # ------------------------------------------------------------------
    def _menu_compras(self):
        while True:
            print("\nGESTIÓN DE COMPRAS")
            print("1. Registrar necesidad de compra")
            print("2. Registrar varias necesidades")
            print("3. Listar / buscar necesidades")
            print("4. Editar necesidad")
            print("5. Marcar como comprada, cancelada o pendiente")
            print("6. Eliminar necesidad")
            print("7. Generar pedidos desde necesidades pendientes")
            print("8. Gestionar pedidos")
            print("9. Diagnóstico de compras")
            print("0. Volver")
            op = input("Elige una opción: ").strip()

            if op == "0":
                return
            if op == "1":
                self._registrar_necesidad_compra()
            elif op == "2":
                self._registrar_varias_necesidades_compra()
            elif op == "3":
                self._listar_buscar_necesidades_compra()
            elif op == "4":
                self._editar_necesidad_compra()
            elif op == "5":
                self._cambiar_estado_necesidad_compra()
            elif op == "6":
                self._eliminar_necesidad_compra()
            elif op == "7":
                self._generar_pedidos_sugeridos_compra()
            elif op == "8":
                self._menu_pedidos_compra()
            elif op == "9":
                self._diagnosticar_compras()
            else:
                print("Opción no válida.")

    def _seleccionar_articulo_compra(self):
        articulo = self._seleccionar_articulo_stock()
        if not articulo:
            return None
        proveedor = articulo.get("proveedor") or ""
        return {
            "nombre": articulo.get("nombre", ""),
            "articulo_id": articulo.get("articulo_id", ""),
            "familia": articulo.get("familia", ""),
            "proveedor": proveedor,
        }

    def _normalizar_prioridad_compra(self, texto):
        texto = (texto or "").strip().lower()
        mapa = {"baja": 30, "normal": 50, "media": 60, "alta": 80, "urgente": 95}
        if texto in mapa:
            return mapa[texto]
        try:
            valor = int(texto or "50")
            return max(0, min(100, valor))
        except ValueError:
            return 50

    def _registrar_necesidad_compra(self):
        articulo = self._seleccionar_articulo_compra()
        if not articulo:
            print("Registro cancelado.")
            return False
        try:
            cantidad = float(input("Cantidad necesaria: ").strip() or "0")
        except ValueError:
            print("Cantidad no válida.")
            return False
        if cantidad <= 0:
            print("La cantidad debe ser mayor que cero.")
            return False
        unidad = input("Unidad: ").strip() or "kg"
        proveedor_defecto = articulo.get("proveedor") or ""
        proveedor = input(f"Proveedor preferente [{proveedor_defecto or 'sin asignar'}]: ").strip() or proveedor_defecto
        motivo = input("Motivo (opcional): ").strip()
        fecha = self._normalizar_fecha_stock(input("Fecha necesaria (opcional): ").strip())
        if fecha is None:
            return False
        prioridad = self._normalizar_prioridad_compra(input("Prioridad (baja/normal/alta/urgente) [normal]: ").strip())
        r = self.core.orquestador.resolver(SolicitudHostAI("registrar_necesidad_compra", {
            "nombre": articulo["nombre"],
            "cantidad": cantidad,
            "unidad": unidad,
            "familia": articulo.get("familia", ""),
            "proveedor_preferente": proveedor,
            "motivo": motivo,
            "prioridad": prioridad,
            "articulo_id": articulo.get("articulo_id", ""),
            "fecha_necesaria": fecha or "",
        }))
        print(r.mensaje)
        return bool(r.ok)

    def _registrar_varias_necesidades_compra(self):
        total = 0
        while True:
            print(f"\nNecesidades registradas en esta sesión: {total}")
            if self._registrar_necesidad_compra():
                total += 1
            seguir = input("¿Añadir otra necesidad? (s/n): ").strip().lower()
            if seguir not in {"s", "si", "sí", "y", "yes"}:
                break
        print(f"Sesión finalizada: {total} necesidad(es) registrada(s).")

    def _imprimir_necesidades_compra(self, necesidades):
        if not necesidades:
            print("No hay necesidades que mostrar.")
            return
        for i, n in enumerate(necesidades, 1):
            fecha = n.get("fecha_necesaria") or "sin fecha"
            proveedor = n.get("proveedor_preferente") or "sin proveedor"
            print(f"{i}. [{n.get('estado', 'pendiente').upper()}] {n['nombre']} — {n['cantidad']} {n['unidad']} | {proveedor} | prioridad {n.get('prioridad', 50)} | {fecha}")
            print(f"   ID: {n['id']}" + (f" | Motivo: {n.get('motivo')}" if n.get('motivo') else ""))

    def _listar_buscar_necesidades_compra(self):
        print("\n1. Solo pendientes")
        print("2. Todas")
        print("3. Compradas")
        print("4. Canceladas")
        filtro = input("Filtro [1]: ").strip() or "1"
        estado = {"3": "comprada", "4": "cancelada"}.get(filtro, "")
        solo_pendientes = filtro == "1"
        texto = input("Buscar por artículo, proveedor, motivo o ID (vacío=todas): ").strip()
        if texto:
            r = self.core.orquestador.resolver(SolicitudHostAI("buscar_necesidades_compra", {"texto": texto, "estado": estado or ("pendiente" if solo_pendientes else "")}))
        else:
            r = self.core.orquestador.resolver(SolicitudHostAI("listar_necesidades_compra", {"solo_pendientes": solo_pendientes, "estado": estado}))
        print(r.mensaje)
        self._imprimir_necesidades_compra(r.datos.get("necesidades", []))

    def _seleccionar_necesidad_compra(self, solo_pendientes=False):
        necesidades = self.core.compras.listar_necesidades(solo_pendientes=solo_pendientes)
        if not necesidades:
            print("No hay necesidades disponibles.")
            return None
        self._imprimir_necesidades_compra(necesidades)
        return self._seleccionar_elemento(
            necesidades,
            prompt="Selecciona número o escribe el ID",
            permitir_id=True,
            id_key="id",
            auto_unico=False,
        )

    def _editar_necesidad_compra(self):
        actual = self._seleccionar_necesidad_compra(False)
        if not actual:
            return
        print("Pulsa Enter para conservar el valor actual.")
        nombre = input(f"Artículo [{actual['nombre']}]: ").strip()
        cantidad_txt = input(f"Cantidad [{actual['cantidad']}]: ").strip()
        unidad = input(f"Unidad [{actual['unidad']}]: ").strip()
        proveedor = input(f"Proveedor [{actual.get('proveedor_preferente', '')}]: ").strip()
        motivo = input(f"Motivo [{actual.get('motivo', '')}]: ").strip()
        fecha_txt = input(f"Fecha necesaria [{actual.get('fecha_necesaria', '')}]: ").strip()
        prioridad_txt = input(f"Prioridad [{actual.get('prioridad', 50)}]: ").strip()
        cambios = {}
        if nombre:
            cambios["nombre"] = nombre
        if cantidad_txt:
            try:
                cambios["cantidad"] = float(cantidad_txt)
            except ValueError:
                print("Cantidad no válida.")
                return
        if unidad:
            cambios["unidad"] = unidad
        if proveedor:
            cambios["proveedor_preferente"] = proveedor
        if motivo:
            cambios["motivo"] = motivo
        if fecha_txt:
            fecha = self._normalizar_fecha_stock(fecha_txt)
            if fecha is None:
                return
            cambios["fecha_necesaria"] = fecha
        if prioridad_txt:
            cambios["prioridad"] = self._normalizar_prioridad_compra(prioridad_txt)
        if not cambios:
            print("No se han realizado cambios.")
            return
        r = self.core.orquestador.resolver(SolicitudHostAI("editar_necesidad_compra", {"necesidad_id": actual["id"], "cambios": cambios}))
        print(r.mensaje)

    def _cambiar_estado_necesidad_compra(self):
        actual = self._seleccionar_necesidad_compra(False)
        if not actual:
            return
        print("1. Pendiente")
        print("2. Comprada")
        print("3. Cancelada")
        estado = {"1": "pendiente", "2": "comprada", "3": "cancelada"}.get(input("Nuevo estado: ").strip())
        if not estado:
            print("Estado no válido.")
            return
        r = self.core.orquestador.resolver(SolicitudHostAI("cambiar_estado_necesidad_compra", {"necesidad_id": actual["id"], "estado": estado}))
        print(r.mensaje)

    def _eliminar_necesidad_compra(self):
        actual = self._seleccionar_necesidad_compra(False)
        if not actual:
            return
        confirmar = input(f"¿Eliminar definitivamente '{actual['nombre']}'? (s/n): ").strip().lower()
        if confirmar not in {"s", "si", "sí", "y", "yes"}:
            print("Eliminación cancelada.")
            return
        r = self.core.orquestador.resolver(SolicitudHostAI("eliminar_necesidad_compra", {"necesidad_id": actual["id"]}))
        print(r.mensaje)

    def _generar_pedidos_sugeridos_compra(self):
        r = self.core.orquestador.resolver(SolicitudHostAI("generar_pedidos_sugeridos", {}))
        print(r.mensaje)
        for p in r.datos.get("pedidos_sugeridos", []):
            print(f"\nProveedor: {p['proveedor']}")
            for n in p["necesidades"]:
                print(f"- {n['nombre']}: {n['cantidad']} {n['unidad']}")

    def _diagnosticar_compras(self):
        r = self.core.orquestador.resolver(SolicitudHostAI("diagnosticar_compras", {}))
        datos = r.datos
        print("\nRESUMEN DE COMPRAS")
        print(f"Pendientes: {datos.get('pendientes', 0)}")
        print(f"Compradas: {datos.get('compradas', 0)}")
        print(f"Canceladas: {datos.get('canceladas', 0)}")
        print(f"Sin proveedor: {datos.get('sin_proveedor', 0)}")
        print(f"Urgentes: {datos.get('urgentes', 0)}")
        for aviso in datos.get("avisos", []):
            print(f"- {aviso}")


    def _imprimir_pedidos_compra(self, pedidos):
        if not pedidos:
            print("No hay pedidos que mostrar.")
            return
        for i, p in enumerate(pedidos, 1):
            print(f"{i}. [{p['estado'].upper()}] {p['proveedor']} — {p['total_lineas']} línea(s) — {p.get('importe_estimado', 0):.2f} €")
            print(f"   ID: {p['id']} | Actualizado: {p.get('actualizado_en', '')}")

    def _seleccionar_pedido_compra(self, estados=None):
        pedidos = self.core.compras.listar_pedidos()
        if estados:
            pedidos = [p for p in pedidos if p.get("estado") in set(estados)]
        if not pedidos:
            print("No hay pedidos disponibles.")
            return None
        self._imprimir_pedidos_compra(pedidos)
        return self._seleccionar_elemento(
            pedidos,
            prompt="Selecciona número o ID",
            permitir_id=True,
            id_key="id",
            auto_unico=False,
        )

    def _imprimir_detalle_pedido(self, pedido):
        print("\n" + "=" * 62)
        print(f"PEDIDO {pedido['id']} — {pedido['estado'].upper()}")
        print(f"Proveedor: {pedido['proveedor']}")
        if pedido.get("observaciones"):
            print(f"Observaciones: {pedido['observaciones']}")
        for i, linea in enumerate(pedido.get("lineas", []), 1):
            precio = linea.get("precio_unitario", 0)
            print(f"{i}. {linea['nombre']}: {linea['cantidad']} {linea['unidad']} | {precio:.2f} €/u | {linea['id']}")
        print(f"Importe estimado: {pedido.get('importe_estimado', 0):.2f} €")
        print("=" * 62)

    def _menu_pedidos_compra(self):
        while True:
            print("\nPEDIDOS OPERATIVOS")
            print("1. Listar / buscar pedidos")
            print("2. Ver detalle de pedido")
            print("3. Editar cabecera")
            print("4. Añadir línea")
            print("5. Editar línea")
            print("6. Eliminar línea")
            print("7. Cambiar estado")
            print("8. Recibir pedido y actualizar stock")
            print("9. Ver historial")
            print("0. Volver")
            op = input("Elige una opción: ").strip()
            if op == "0":
                return
            if op == "1":
                estado = input("Estado (vacío=todos): ").strip().lower()
                texto = input("Buscar por proveedor, artículo o ID: ").strip()
                pedidos = self.core.compras.listar_pedidos(estado, texto)
                self._imprimir_pedidos_compra(pedidos)
            elif op == "2":
                pedido = self._seleccionar_pedido_compra()
                if pedido:
                    self._imprimir_detalle_pedido(pedido)
            elif op == "3":
                self._editar_cabecera_pedido_compra()
            elif op == "4":
                self._agregar_linea_pedido_compra()
            elif op == "5":
                self._editar_linea_pedido_compra()
            elif op == "6":
                self._eliminar_linea_pedido_compra()
            elif op == "7":
                self._cambiar_estado_pedido_compra()
            elif op == "8":
                self._recibir_pedido_compra()
            elif op == "9":
                self._ver_historial_pedido_compra()
            else:
                print("Opción no válida.")

    def _editar_cabecera_pedido_compra(self):
        pedido = self._seleccionar_pedido_compra({"borrador", "preparado"})
        if not pedido:
            return
        proveedor = input(f"Proveedor [{pedido['proveedor']}]: ").strip() or None
        observaciones = input(f"Observaciones [{pedido.get('observaciones', '')}]: ").strip()
        r = self.core.orquestador.resolver(SolicitudHostAI("editar_pedido_compra", {
            "pedido_id": pedido["id"], "proveedor": proveedor, "observaciones": observaciones,
        }))
        print(r.mensaje)

    def _agregar_linea_pedido_compra(self):
        pedido = self._seleccionar_pedido_compra({"borrador", "preparado"})
        if not pedido:
            return
        articulo = self._seleccionar_articulo_compra()
        if not articulo:
            return
        try:
            cantidad = float(input("Cantidad: ").strip())
            precio = float(input("Precio unitario [0]: ").strip() or "0")
        except ValueError:
            print("Cantidad o precio no válido.")
            return
        unidad = input("Unidad [kg]: ").strip() or "kg"
        obs = input("Observaciones (opcional): ").strip()
        r = self.core.orquestador.resolver(SolicitudHostAI("agregar_linea_pedido_compra", {
            "pedido_id": pedido["id"], "nombre": articulo["nombre"], "cantidad": cantidad,
            "unidad": unidad, "articulo_id": articulo.get("articulo_id", ""),
            "familia": articulo.get("familia", ""), "precio_unitario": precio, "observaciones": obs,
        }))
        print(r.mensaje)

    def _seleccionar_linea_pedido_compra(self, pedido):
        lineas = pedido.get("lineas", [])
        if not lineas:
            print("El pedido no tiene líneas.")
            return None
        for i, l in enumerate(lineas, 1):
            print(f"{i}. {l['nombre']} — {l['cantidad']} {l['unidad']} — {l['id']}")
        eleccion = input("Selecciona línea: ").strip()
        if eleccion.isdigit() and 1 <= int(eleccion) <= len(lineas):
            return lineas[int(eleccion) - 1]
        for linea in lineas:
            if linea["id"].lower() == eleccion.lower():
                return linea
        print("Selección no válida.")
        return None

    def _editar_linea_pedido_compra(self):
        pedido = self._seleccionar_pedido_compra({"borrador", "preparado"})
        if not pedido:
            return
        linea = self._seleccionar_linea_pedido_compra(pedido)
        if not linea:
            return
        cambios = {}
        nombre = input(f"Artículo [{linea['nombre']}]: ").strip()
        cantidad = input(f"Cantidad [{linea['cantidad']}]: ").strip()
        unidad = input(f"Unidad [{linea['unidad']}]: ").strip()
        precio = input(f"Precio unitario [{linea.get('precio_unitario', 0)}]: ").strip()
        obs = input(f"Observaciones [{linea.get('observaciones', '')}]: ").strip()
        if nombre: cambios["nombre"] = nombre
        if cantidad:
            try: cambios["cantidad"] = float(cantidad)
            except ValueError: print("Cantidad no válida."); return
        if unidad: cambios["unidad"] = unidad
        if precio:
            try: cambios["precio_unitario"] = float(precio)
            except ValueError: print("Precio no válido."); return
        if obs: cambios["observaciones"] = obs
        if not cambios:
            print("No se han realizado cambios.")
            return
        r = self.core.orquestador.resolver(SolicitudHostAI("editar_linea_pedido_compra", {
            "pedido_id": pedido["id"], "linea_id": linea["id"], "cambios": cambios,
        }))
        print(r.mensaje)

    def _eliminar_linea_pedido_compra(self):
        pedido = self._seleccionar_pedido_compra({"borrador", "preparado"})
        if not pedido:
            return
        linea = self._seleccionar_linea_pedido_compra(pedido)
        if not linea:
            return
        if input(f"¿Eliminar '{linea['nombre']}'? (s/n): ").strip().lower() not in {"s", "si", "sí", "y", "yes"}:
            print("Eliminación cancelada.")
            return
        r = self.core.orquestador.resolver(SolicitudHostAI("eliminar_linea_pedido_compra", {
            "pedido_id": pedido["id"], "linea_id": linea["id"],
        }))
        print(r.mensaje)

    def _cambiar_estado_pedido_compra(self):
        pedido = self._seleccionar_pedido_compra()
        if not pedido:
            return
        print("1. Borrador\n2. Preparado\n3. Enviado\n4. Cancelado")
        estado = {"1": "borrador", "2": "preparado", "3": "enviado", "4": "cancelado"}.get(input("Nuevo estado: ").strip())
        if not estado:
            print("Estado no válido.")
            return
        if estado in {"enviado", "cancelado"}:
            if input(f"¿Confirmar estado '{estado}'? (s/n): ").strip().lower() not in {"s", "si", "sí", "y", "yes"}:
                print("Cambio cancelado.")
                return
        try:
            r = self.core.orquestador.resolver(SolicitudHostAI("cambiar_estado_pedido_compra", {"pedido_id": pedido["id"], "estado": estado}))
            print(r.mensaje)
        except Exception as exc:
            print(f"No se pudo cambiar el estado: {exc}")

    def _recibir_pedido_compra(self):
        pedido = self._seleccionar_pedido_compra({"borrador", "preparado", "enviado"})
        if not pedido:
            return
        self._imprimir_detalle_pedido(pedido)
        ubicacion = input("Ubicación de entrada [almacén]: ").strip() or "almacén"
        caducidades, costes = {}, {}
        for linea in pedido.get("lineas", []):
            cad = input(f"Caducidad de {linea['nombre']} (opcional): ").strip()
            if cad:
                cad_n = self._normalizar_fecha_stock(cad)
                if cad_n is None: return
                caducidades[linea["id"]] = cad_n
            precio = input(f"Coste unitario de {linea['nombre']} [{linea.get('precio_unitario', 0)}]: ").strip()
            if precio:
                try: costes[linea["id"]] = float(precio)
                except ValueError: print("Coste no válido."); return
        if input("¿Confirmar recepción y actualizar stock? (s/n): ").strip().lower() not in {"s", "si", "sí", "y", "yes"}:
            print("Recepción cancelada.")
            return
        try:
            r = self.core.orquestador.resolver(SolicitudHostAI("recibir_pedido_compra", {
                "pedido_id": pedido["id"], "ubicacion": ubicacion,
                "caducidades": caducidades, "costes": costes,
            }))
            print(r.mensaje)
        except Exception as exc:
            print(f"No se pudo recibir el pedido: {exc}")

    def _ver_historial_pedido_compra(self):
        pedido = self._seleccionar_pedido_compra()
        if not pedido:
            return
        r = self.core.orquestador.resolver(SolicitudHostAI("historial_pedido_compra", {"pedido_id": pedido["id"]}))
        print(r.mensaje)
        for item in r.datos.get("historial", []):
            print(f"- {item.get('fecha', '')} | {item.get('accion', '')} | {item.get('detalle', '')}")

    # ------------------------------------------------------------------
    # ESCANDALLOS (ES1)
    # ------------------------------------------------------------------
    def _menu_escandallos(self):
        while True:
            print("\nESCANDALLOS")
            print("1. Crear escandallo")
            print("2. Listar escandallos")
            print("3. Buscar escandallo")
            print("4. Ver detalle")
            print("5. Editar ficha")
            print("6. Gestionar ingredientes")
            print("7. Duplicar escandallo")
            print("8. Activar / desactivar")
            print("9. Eliminar escandallo")
            print("10. Calcular escandallo receta")
            print("11. Escandallo operativo / rentabilidad")
            print("12. Simular cambio de precios")
            print("13. Historial económico")
            print("0. Volver")
            op = input("Elige una opción: ").strip()
            if op == "0":
                return
            if op == "1": self._crear_escandallo()
            elif op == "2": self._listar_escandallos()
            elif op == "3": self._buscar_escandallo()
            elif op == "4": self._ver_detalle_escandallo()
            elif op == "5": self._editar_ficha_escandallo()
            elif op == "6": self._gestionar_ingredientes_escandallo()
            elif op == "7": self._duplicar_escandallo()
            elif op == "8": self._cambiar_estado_escandallo()
            elif op == "9": self._eliminar_escandallo()
            elif op == "10": self._calcular_escandallo()
            elif op == "11": self._escandallo_operativo()
            elif op == "12": self._simular_escandallo()
            elif op == "13": self._historial_economico_escandallo()
            else: print("Opción no válida.")

    @staticmethod
    def _imprimir_escandallos(escandallos):
        if not escandallos:
            print("No hay escandallos para mostrar.")
            return
        for i, e in enumerate(escandallos, 1):
            estado = "activo" if e.get("activo", True) else "inactivo"
            print(f"{i}. {e['receta_id']} | {e['nombre']} | {e['raciones_base']} raciones | {len(e.get('lineas', []))} ingredientes | {estado}")

    def _seleccionar_escandallo(self, incluir_inactivos=True):
        texto = input("Nombre o código de receta (Enter=mostrar todas, 0=cancelar): ").strip()
        if texto == "0":
            print("Operación cancelada.")
            return None
        r = self.core.orquestador.resolver(SolicitudHostAI("buscar_escandallos", {
            "texto": texto, "incluir_inactivos": incluir_inactivos
        }))
        escandallos = r.datos.get("escandallos", [])
        self._imprimir_escandallos(escandallos)
        if not escandallos:
            return None
        return self._seleccionar_elemento(
            escandallos,
            prompt="Número de receta",
            permitir_id=True,
            id_key="receta_id",
            auto_unico=True,
        )

    def _crear_escandallo(self):
        codigo = input("Código receta (ej. REC-CROQUETAS): ").strip().upper()
        nombre = input("Nombre: ").strip()
        try:
            raciones = int(input("Raciones base: ").strip() or "1")
        except ValueError:
            print("Raciones no válidas."); return
        grupo = input("Grupo/familia (opcional): ").strip()
        subgrupo = input("Subgrupo (opcional): ").strip()
        observaciones = input("Observaciones (opcional): ").strip()
        try:
            r = self.core.orquestador.resolver(SolicitudHostAI("registrar_escandallo", {
                "receta_id": codigo, "nombre": nombre, "raciones_base": raciones,
                "grupo": grupo, "subgrupo": subgrupo, "observaciones": observaciones, "lineas": []
            }))
            print(r.mensaje)
            if r.ok and self._preguntar_si_no("¿Añadir ingredientes ahora?", por_defecto=False):
                self._bucle_agregar_ingredientes(codigo)
        except Exception as exc:
            print(f"No se pudo crear el escandallo: {exc}")

    def _listar_escandallos(self):
        incluir = input("¿Incluir inactivos? (s/n): ").strip().lower() in {"s","si","sí"}
        datos = self.core.escandallos_inteligente.listar(incluir)
        print(f"Escandallos registrados: {len(datos)}.")
        self._imprimir_escandallos(datos)

    def _buscar_escandallo(self):
        texto = input("Buscar: ").strip()
        r = self.core.orquestador.resolver(SolicitudHostAI("buscar_escandallos", {"texto": texto, "incluir_inactivos": True}))
        print(r.mensaje); self._imprimir_escandallos(r.datos.get("escandallos", []))

    def _ver_detalle_escandallo(self):
        esc = self._seleccionar_escandallo()
        if not esc: return
        print(f"\n{esc['receta_id']} | {esc['nombre']}")
        print(f"Raciones base: {esc['raciones_base']} | Grupo: {esc.get('grupo') or '-'} | Estado: {'activo' if esc.get('activo', True) else 'inactivo'}")
        if esc.get("observaciones"): print(f"Observaciones: {esc['observaciones']}")
        print("Ingredientes:")
        if not esc.get("lineas"): print("- Sin ingredientes.")
        for i, l in enumerate(esc.get("lineas", []), 1):
            print(f"{i}. {l['nombre']}: {l['cantidad']} {l['unidad']} | merma {l.get('merma_porcentaje',0)}% | {l.get('articulo_id') or l.get('elaboracion_id') or '-'}")

    def _editar_ficha_escandallo(self):
        esc = self._seleccionar_escandallo()
        if not esc: return
        nombre = input(f"Nombre [{esc['nombre']}]: ").strip()
        raciones_txt = input(f"Raciones base [{esc['raciones_base']}]: ").strip()
        grupo = input(f"Grupo [{esc.get('grupo','')}]: ").strip()
        subgrupo = input(f"Subgrupo [{esc.get('subgrupo','')}]: ").strip()
        obs = input(f"Observaciones [{esc.get('observaciones','')}]: ").strip()
        cambios = {}
        if nombre: cambios["nombre"] = nombre
        if raciones_txt:
            try: cambios["raciones_base"] = int(raciones_txt)
            except ValueError: print("Raciones no válidas."); return
        if grupo: cambios["grupo"] = grupo
        if subgrupo: cambios["subgrupo"] = subgrupo
        if obs: cambios["observaciones"] = obs
        try:
            r = self.core.orquestador.resolver(SolicitudHostAI("editar_escandallo", {"receta_id": esc["receta_id"], "cambios": cambios}))
            print(r.mensaje)
        except Exception as exc: print(f"No se pudo editar: {exc}")

    def _gestionar_ingredientes_escandallo(self):
        esc = self._seleccionar_escandallo()
        if not esc: return
        receta_id = esc["receta_id"]
        while True:
            actual = self.core.escandallos_inteligente.obtener(receta_id).to_dict()
            print(f"\nINGREDIENTES — {actual['nombre']}")
            for i,l in enumerate(actual.get("lineas",[]),1): print(f"{i}. {l['nombre']} | {l['cantidad']} {l['unidad']} | {l['id']}")
            print("1. Añadir ingrediente")
            print("2. Editar ingrediente")
            print("3. Eliminar ingrediente")
            print("0. Volver")
            op=input("Elige una opción: ").strip()
            if op=="0": return
            if op=="1": self._agregar_ingrediente_escandallo(receta_id)
            elif op=="2": self._editar_ingrediente_escandallo(receta_id, actual.get("lineas",[]))
            elif op=="3": self._eliminar_ingrediente_escandallo(receta_id, actual.get("lineas",[]))

    def _bucle_agregar_ingredientes(self, receta_id):
        while True:
            agregado = self._agregar_ingrediente_escandallo(receta_id)
            if not agregado:
                print("No se añadió ningún ingrediente.")
            if not self._preguntar_si_no("¿Añadir otro ingrediente?", por_defecto=False):
                return

    def _agregar_ingrediente_escandallo(self, receta_id):
        articulo = self._seleccionar_articulo_stock()
        if not articulo:
            return False
        try:
            cantidad = float(input("Cantidad neta: ").strip())
            merma = float(input("Merma % [0]: ").strip() or "0")
            coste = float(input("Coste unitario [0]: ").strip() or "0")
        except ValueError:
            print("Cantidad, merma o coste no válidos.")
            return False
        unidad = input("Unidad (kg/L/u): ").strip() or "kg"
        notas = input("Notas (opcional): ").strip()
        linea = {"nombre": articulo["nombre"], "cantidad": cantidad, "unidad": unidad,
                 "articulo_id": articulo.get("articulo_id", ""), "familia": articulo.get("familia", ""),
                 "proveedor_preferente": articulo.get("proveedor", ""), "merma_porcentaje": merma,
                 "coste_unitario": coste, "notas": notas, "tipo": "articulo"}
        try:
            r=self.core.orquestador.resolver(SolicitudHostAI("agregar_linea_escandallo", {"receta_id":receta_id,"linea":linea}))
            print(r.mensaje)
            return bool(r.ok)
        except Exception as exc:
            print(f"No se pudo añadir: {exc}")
            return False

    @staticmethod
    def _elegir_linea(lineas):
        if not lineas: print("No hay ingredientes."); return None
        valor=input("Número de ingrediente: ").strip()
        try: return lineas[int(valor)-1]
        except (ValueError,IndexError): print("Selección no válida."); return None

    def _editar_ingrediente_escandallo(self, receta_id, lineas):
        linea=self._elegir_linea(lineas)
        if not linea: return
        cambios={}
        nombre=input(f"Nombre [{linea['nombre']}]: ").strip()
        cantidad=input(f"Cantidad [{linea['cantidad']}]: ").strip()
        unidad=input(f"Unidad [{linea['unidad']}]: ").strip()
        merma=input(f"Merma % [{linea.get('merma_porcentaje',0)}]: ").strip()
        notas=input(f"Notas [{linea.get('notas','')}]: ").strip()
        if nombre: cambios['nombre']=nombre
        if cantidad:
            try: cambios['cantidad']=float(cantidad)
            except ValueError: print("Cantidad no válida."); return
        if unidad: cambios['unidad']=unidad
        if merma:
            try: cambios['merma_porcentaje']=float(merma)
            except ValueError: print("Merma no válida."); return
        if notas: cambios['notas']=notas
        try:
            r=self.core.orquestador.resolver(SolicitudHostAI("editar_linea_escandallo", {"receta_id":receta_id,"linea_id":linea['id'],"cambios":cambios}))
            print(r.mensaje)
        except Exception as exc: print(f"No se pudo editar: {exc}")

    def _eliminar_ingrediente_escandallo(self, receta_id, lineas):
        linea=self._elegir_linea(lineas)
        if not linea: return
        if input(f"¿Eliminar {linea['nombre']}? (s/n): ").strip().lower() not in {"s","si","sí"}: return
        r=self.core.orquestador.resolver(SolicitudHostAI("eliminar_linea_escandallo", {"receta_id":receta_id,"linea_id":linea['id']}))
        print(r.mensaje)

    def _duplicar_escandallo(self):
        esc=self._seleccionar_escandallo()
        if not esc: return
        nuevo_id=input("Nuevo código: ").strip().upper()
        nuevo_nombre=input(f"Nuevo nombre [{esc['nombre']} (copia)]: ").strip()
        try:
            r=self.core.orquestador.resolver(SolicitudHostAI("duplicar_escandallo", {"receta_id":esc['receta_id'],"nuevo_id":nuevo_id,"nuevo_nombre":nuevo_nombre}))
            print(r.mensaje)
        except Exception as exc: print(f"No se pudo duplicar: {exc}")

    def _cambiar_estado_escandallo(self):
        esc=self._seleccionar_escandallo()
        if not esc: return
        nuevo=not esc.get("activo",True)
        r=self.core.orquestador.resolver(SolicitudHostAI("editar_escandallo", {"receta_id":esc['receta_id'],"cambios":{"activo":nuevo}}))
        print(r.mensaje + f" Estado: {'activo' if nuevo else 'inactivo'}.")

    def _eliminar_escandallo(self):
        esc=self._seleccionar_escandallo()
        if not esc: return
        if input(f"¿Eliminar definitivamente {esc['nombre']}? (s/n): ").strip().lower() not in {"s","si","sí"}: return
        r=self.core.orquestador.resolver(SolicitudHostAI("eliminar_escandallo", {"receta_id":esc['receta_id']}))
        print(r.mensaje)

    def _calcular_escandallo(self):
        esc=self._seleccionar_escandallo(False)
        if not esc: return
        try: raciones=int(input(f"Raciones [{esc['raciones_base']}]: ").strip() or esc['raciones_base'])
        except ValueError: print("Raciones no válidas."); return
        r=self.core.orquestador.resolver(SolicitudHostAI("calcular_escandallo_receta", {"receta_id":esc['receta_id'],"raciones":raciones}))
        print(r.mensaje)
        for n in r.datos.get("necesidades",[]): print(f"- {n['nombre']}: {n['cantidad_bruta']} {n['unidad']}")

    def _imprimir_resultado_escandallo_operativo(self, d):
        print("\n" + "=" * 68)
        print(f"ESCANDALLO OPERATIVO — {d.get('receta','')}")
        print("=" * 68)
        print(f"Raciones: {d.get('raciones', 0)}")
        print(f"Coste total: {float(d.get('coste_total',0)):.2f} €")
        print(f"Coste por ración: {float(d.get('coste_por_racion',0)):.3f} €")
        if float(d.get('precio_venta_por_racion',0) or 0) > 0:
            venta_total=float(d.get('precio_venta_por_racion',0))*int(d.get('raciones',0) or 0)
            beneficio=float(d.get('margen_bruto',0))
            margen_pct=(beneficio/venta_total*100) if venta_total else 0
            print(f"Precio venta/ración: {float(d.get('precio_venta_por_racion',0)):.2f} €")
            print(f"Venta total: {venta_total:.2f} €")
            print(f"Beneficio bruto: {beneficio:.2f} €")
            print(f"Margen bruto: {margen_pct:.2f}%")
            print(f"Food cost: {float(d.get('food_cost_porcentaje',0)):.2f}%")
        print("\nDETALLE POR INGREDIENTE")
        for l in d.get('lineas',[]):
            marca=' ⚠ SIN PRECIO' if float(l.get('precio_unitario',0) or 0)<=0 else ''
            print(f"- {l.get('nombre')}: {l.get('cantidad')} {l.get('unidad')} × {float(l.get('precio_unitario',0)):.4f} € = {float(l.get('coste_total',0)):.3f} €{marca}")
        if d.get('avisos'):
            print("\nAVISOS")
            for a in d['avisos']: print(f"- {a}")
        print("=" * 68)

    def _escandallo_operativo(self):
        esc=self._seleccionar_escandallo(False)
        if not esc: return
        try:
            raciones=int(input(f"Raciones [{esc['raciones_base']}]: ").strip() or esc['raciones_base'])
            precio=float(input("Precio venta por ración [0]: ").strip() or '0')
        except ValueError:
            print("Raciones o precio no válidos."); return
        try:
            d=self.core.costes_inteligente.calcular_coste_receta(esc['receta_id'], raciones, precio)
            self._imprimir_resultado_escandallo_operativo(d)
        except Exception as exc: print(f"No se pudo calcular: {exc}")

    def _simular_escandallo(self):
        esc=self._seleccionar_escandallo(False)
        if not esc: return
        print("1. Variación general porcentual")
        print("2. Cambiar precio de un ingrediente")
        op=input("Elige una opción (1 o 2; 0=cancelar): ").strip()
        if op == "0" or not op:
            print("Simulación cancelada.")
            return
        if op not in {"1", "2"}:
            print("Opción no válida. Debes elegir 1 o 2.")
            return
        try:
            raciones=int(input(f"Raciones [{esc['raciones_base']}]: ").strip() or esc['raciones_base'])
            venta=float(input("Precio venta por ración [0]: ").strip() or '0')
            if op=='1':
                pct=float(input("Variación de precios % (ej. 10 o -5): ").strip())
                d=self.core.costes_inteligente.simular_variacion_precio_receta(esc['receta_id'],raciones,pct,venta)
                antes,despues=d['antes'],d['despues']
                print(f"Antes: {antes['coste_total']:.2f} € | Después: {despues['coste_total']:.2f} €")
                print(f"Impacto/ración: {d['impacto']['diferencia_coste_por_racion']:+.3f} € | Impacto margen: {d['impacto']['diferencia_margen']:+.2f} €")
                print(f"Food cost nuevo: {despues['food_cost_porcentaje']:.2f}%")
            elif op=='2':
                base=self.core.costes_inteligente.calcular_coste_receta(esc['receta_id'],raciones,venta,registrar_historial=False)
                for i,l in enumerate(base['lineas'],1): print(f"{i}. {l['nombre']} — {l['precio_unitario']:.4f} €/{l['unidad']}")
                idx=int(input("Ingrediente: ").strip())-1
                linea=base['lineas'][idx]
                nuevo=float(input("Nuevo precio unitario: ").strip())
                d=self.core.costes_inteligente.simular_precio_linea_receta(esc['receta_id'],raciones,linea['nombre'],nuevo,venta)
                print(f"Coste total: {d['antes']['coste_total']:.2f} € → {d['despues']['coste_total']:.2f} €")
                print(f"Coste/ración: {d['antes']['coste_por_racion']:.3f} € → {d['despues']['coste_por_racion']:.3f} €")
                print(f"Food cost: {d['antes']['food_cost_porcentaje']:.2f}% → {d['despues']['food_cost_porcentaje']:.2f}%")
        except (ValueError,IndexError) as exc: print(f"Datos no válidos: {exc}")
        except Exception as exc: print(f"No se pudo simular: {exc}")

    def _historial_economico_escandallo(self):
        esc=self._seleccionar_escandallo(True)
        if not esc: return
        datos=self.core.costes_inteligente.listar_historial_escandallo(esc['receta_id'])
        if not datos:
            print("No existe historial económico para esta receta."); return
        print(f"\nHISTORIAL ECONÓMICO — {esc['nombre']}")
        for h in datos[:30]:
            print(f"- {h.get('fecha')} | {h.get('raciones')} rac. | total {float(h.get('coste_total',0)):.2f} € | ración {float(h.get('coste_por_racion',0)):.3f} € | FC {float(h.get('food_cost_porcentaje',0)):.2f}%")

    # ------------------------------------------------------------------
    # COSTES
    # ------------------------------------------------------------------
    def _menu_costes(self):
        while True:
            print("\nCOSTES")
            print("1. Registrar precio")
            print("2. Calcular coste receta")
            print("3. Calcular coste operativo del último evento")
            print("4. Ver histórico de costes de eventos")
            print("5. Resumen ejecutivo del último evento")
            print("6. Analizar rentabilidad del último evento")
            print("7. Simular rentabilidad del último evento")
            print("8. Rankings de rentabilidad")
            print("9. Resumen global de rentabilidad")
            print("10. Histórico de rentabilidad")
            print("0. Volver")
            op = input("Elige una opción: ").strip()
            if op == "0":
                return
            if op == "1":
                nombre = input("Artículo: ").strip()
                precio = float(input("Precio unitario: ").strip() or "0")
                unidad = input("Unidad: ").strip() or "kg"
                articulo_id = input("Artículo ID (opcional): ").strip()
                proveedor = input("Proveedor (opcional): ").strip()
                d=self.core.costes_inteligente.registrar_precio(nombre,precio,unidad,articulo_id,proveedor)
                self.core.db.guardar("precios", list(self.core.costes_inteligente.listar_precios()["precios"]))
                print(f"Precio registrado: {d['nombre']} — {d['precio_unitario']} €/{d['unidad']}.")
            elif op == "2":
                receta_id = input("Receta ID: ").strip() or "REC-CARRILLERA"
                raciones = int(input("Raciones: ").strip() or "10")
                precio = float(input("Precio venta/ración: ").strip() or "0")
                d=self.core.costes_inteligente.calcular_coste_receta(receta_id,raciones,precio)
                print(d["lectura_host_ai"])
                for a in d.get("avisos",[]): print(f"AVISO: {a}")
            elif op == "3":
                if not self._requiere_evento(): continue
                venta=float(input("Precio venta por pax [0]: ").strip() or "0")
                horas=float(input("Horas totales de personal [0]: ").strip() or "0")
                coste_hora=float(input("Coste por hora [0]: ").strip() or "0")
                indirectos=float(input("Costes indirectos [0]: ").strip() or "0")
                otros=float(input("Otros costes [0]: ").strip() or "0")
                real_txt=input("Coste real de materia prima (vacío=previsto): ").strip()
                real=float(real_txt) if real_txt else None
                d=self.core.costes_inteligente.calcular_coste_evento_operativo(self.ultimo_evento_id,venta,horas,coste_hora,indirectos,otros,real)
                self._imprimir_resumen_costes_evento(d)
            elif op == "4":
                datos=self.core.costes_inteligente.listar_historial_costes_eventos()
                print(f"Registros de costes de eventos: {len(datos)}")
                for h in datos[:30]:
                    print(f"- {h.get('fecha')} | {h.get('evento')} | previsto {float(h.get('coste_total_previsto',0)):.2f} € | real {float(h.get('coste_total_real',0)):.2f} € | desviación {float(h.get('desviacion',0)):+.2f} €")
            elif op == "5":
                if not self._requiere_evento(): continue
                datos=self.core.costes_inteligente.listar_historial_costes_eventos(self.ultimo_evento_id)
                if not datos:
                    print("Todavía no hay cálculos operativos para este evento.")
                else:
                    self._imprimir_resumen_costes_evento(datos[0])
            elif op == "6":
                if not self._requiere_evento(): continue
                try:
                    d=self.core.costes_inteligente.analizar_rentabilidad_evento(self.ultimo_evento_id)
                    self._imprimir_rentabilidad_evento(d)
                except Exception as exc: print(f"No se pudo analizar la rentabilidad: {exc}")
            elif op == "7":
                if not self._requiere_evento(): continue
                try:
                    pvp=input("Nuevo precio venta/pax (vacío=actual): ").strip()
                    pax=input("Nuevos pax (vacío=actual): ").strip()
                    mat=float(input("Variación materia prima % [0]: ").strip() or "0")
                    mano=float(input("Variación mano de obra % [0]: ").strip() or "0")
                    d=self.core.costes_inteligente.simular_rentabilidad_evento(self.ultimo_evento_id,float(pvp) if pvp else None,int(pax) if pax else None,mat,mano)
                    self._imprimir_rentabilidad_evento(d)
                    print(f"Impacto beneficio: {float(d.get('impacto_beneficio',0)):+.2f} €")
                except Exception as exc: print(f"No se pudo simular: {exc}")
            elif op == "8":
                d=self.core.costes_inteligente.rankings_rentabilidad()
                print("\nEVENTOS MÁS RENTABLES")
                for x in d['eventos'][:10]: print(f"- {x.get('evento')} | beneficio {float(x.get('beneficio',0)):.2f} € | margen {float(x.get('margen_porcentaje',0)):.2f}%")
                print("\nRECETAS MÁS RENTABLES")
                for x in d['recetas'][:10]: print(f"- {x.get('receta')} | margen {float(x.get('margen_bruto',0)):.2f} € | FC {float(x.get('food_cost_porcentaje',0)):.2f}%")
                print("\nCLIENTES MÁS RENTABLES")
                for x in d['clientes'][:10]: print(f"- {x.get('cliente')} | {x.get('eventos')} eventos | beneficio {float(x.get('beneficio',0)):.2f} €")
            elif op == "9":
                d=self.core.costes_inteligente.resumen_rentabilidad_global()
                print(f"Eventos analizados: {d['eventos_analizados']}")
                print(f"Venta total: {d['venta_total']:.2f} € | Coste total: {d['coste_total']:.2f} €")
                print(f"Beneficio: {d['beneficio_total']:.2f} € | Margen: {d['margen_global_porcentaje']:.2f}% | Food cost: {d['food_cost_global_porcentaje']:.2f}%")
                for a in d.get('alertas',[]): print(f"AVISO: {a}")
            elif op == "10":
                datos=list(reversed(self.core.costes_inteligente.historial_rentabilidad))
                print(f"Registros de rentabilidad: {len(datos)}")
                for x in datos[:30]: print(f"- {x.get('fecha')} | {x.get('evento')} | beneficio {float(x.get('beneficio',0)):.2f} € | margen {float(x.get('margen_porcentaje',0)):.2f}%")
            else:
                print("Opción no válida.")


    def _imprimir_rentabilidad_evento(self,d):
        print(f"\nRENTABILIDAD — {d.get('evento','')}")
        print(f"Pax: {d.get('pax',0)} | Venta: {float(d.get('venta_total',0)):.2f} € | Coste: {float(d.get('coste_total_real',d.get('coste_total',0))):.2f} €")
        print(f"Beneficio: {float(d.get('beneficio',0)):.2f} € | Beneficio/pax: {float(d.get('beneficio_por_pax',0)):.2f} €")
        print(f"Margen: {float(d.get('margen_porcentaje',0)):.2f}% | Food cost: {float(d.get('food_cost_porcentaje',0)):.2f}%")
        for a in d.get('alertas',[]): print(f"AVISO: {a}")

    def _imprimir_resumen_costes_evento(self,d):
        print(f"\nRESUMEN DE COSTES — {d.get('evento','')}")
        print(f"Pax: {d.get('pax',0)}")
        print(f"Materia prevista: {float(d.get('coste_materia_previsto',0)):.2f} €")
        print(f"Materia real: {float(d.get('coste_materia_real',0)):.2f} €")
        print(f"Mano de obra: {float(d.get('coste_mano_obra',0)):.2f} €")
        print(f"Indirectos: {float(d.get('costes_indirectos',0)):.2f} €")
        print(f"Otros: {float(d.get('otros_costes',0)):.2f} €")
        print(f"Coste previsto: {float(d.get('coste_total_previsto',0)):.2f} €")
        print(f"Coste real: {float(d.get('coste_total_real',0)):.2f} €")
        print(f"Desviación: {float(d.get('desviacion',0)):+.2f} €")
        print(f"Coste real/pax: {float(d.get('coste_real_por_pax',0)):.2f} €")
        if float(d.get('precio_venta_total',0)):
            print(f"Venta total: {float(d.get('precio_venta_total',0)):.2f} €")
            print(f"Beneficio real: {float(d.get('beneficio_real',0)):.2f} €")
            print(f"Margen real: {float(d.get('margen_real_porcentaje',0)):.2f}%")
    # ------------------------------------------------------------------
    # PRODUCCIÓN REAL
    # ------------------------------------------------------------------
    def _menu_produccion_real(self):
        while True:
            print("\nGESTIÓN DE PRODUCCIÓN")
            print("1. Crear plan manual")
            print("2. Planificar último evento")
            print("3. Listar / buscar planes")
            print("4. Ver detalle")
            print("5. Editar plan")
            print("6. Duplicar plan")
            print("7. Eliminar plan")
            print("8. Gestionar tareas y fases")
            print("9. Generar planificación inteligente")
            print("10. Ver planificación y reparto")
            print("11. Ejecutar producción")
            print("12. Panel de producción")
            print("13. Optimización automática básica")
            print("14. Optimización de recursos")
            print("15. Recomendaciones inteligentes")
            print("0. Volver")
            op=input("Elige una opción: ").strip()
            if op=="0": return
            try:
                if op=="1":
                    nombre=input("Nombre del plan: ").strip()
                    if not nombre: print("Creación cancelada."); continue
                    fecha=input("Fecha (opcional): ").strip()
                    responsable=input("Responsable (opcional): ").strip()
                    observaciones=input("Observaciones (opcional): ").strip()
                    d=self.core.produccion_real.crear_plan_manual(nombre,fecha,responsable,observaciones)
                    self.ultimo_plan_produccion_id=d['id']
                    print(f"Plan creado: {d['nombre']} | {d['id']}")
                elif op=="2":
                    if not self._requiere_evento(): continue
                    hora=input("Hora inicio producción [08:00]: ").strip() or "08:00"
                    equipo=int(input("Equipo cocina [2]: ").strip() or "2")
                    r=self.core.orquestador.resolver(SolicitudHostAI("planificar_produccion_real_evento",{"evento_id":self.ultimo_evento_id,"hora_inicio":hora,"equipo_cocina":equipo}))
                    print(r.mensaje)
                    try:
                        nombre_evento=self.core.eventos.obtener(self.ultimo_evento_id).nombre
                        planes=self.core.produccion_real.buscar_planes(nombre_evento)
                        if planes:
                            self.ultimo_plan_produccion_id=planes[-1].get("id")
                            print(f"Plan activo: {planes[-1].get('nombre')} | {self.ultimo_plan_produccion_id}")
                    except Exception:
                        pass
                elif op=="3":
                    q=input("Buscar (vacío=todos): ").strip()
                    planes=self.core.produccion_real.buscar_planes(q)
                    print(f"Planes encontrados: {len(planes)}")
                    for i,p in enumerate(planes,1): print(f"{i}. [{p.get('estado','').upper()}] {p.get('nombre') or p.get('evento')} | {p.get('fecha') or 'sin fecha'} | {p.get('responsable') or 'sin responsable'} | {p.get('id')}")
                elif op in {"4","5","6","7","8","9","10","11","12","13","14","15"}:
                    plan=self._seleccionar_plan_produccion()
                    if not plan: continue
                    if op=="4": self._imprimir_plan_produccion(plan)
                    elif op=="8": self._gestionar_tareas_plan(plan)
                    elif op=="9":
                        jornada=float(input("Jornada por cocinero [7.5]: ").strip() or "7.5")
                        cocineros=int(input("Número de cocineros [3]: ").strip() or "3")
                        hora=input("Hora de inicio [08:00]: ").strip() or "08:00"
                        d=self.core.produccion_real.planificar_inteligente(plan['id'],jornada,cocineros,hora)
                        self.ultimo_plan_produccion_id=plan['id']
                        print(d['planificacion'].get('lectura_host_ai','Planificación generada.'))
                        print(d['asignacion'].get('lectura_host_ai','Reparto generado.'))
                        self._mostrar_conflictos_produccion(d.get('asignacion') or {})
                    elif op=="10": self._imprimir_planificacion_inteligente(self.core.produccion_real.obtener_plan(plan['id']).to_dict())
                    elif op=="11": self._menu_ejecucion_produccion(plan)
                    elif op=="12": self._menu_panel_produccion(plan)
                    elif op=="13": self._menu_optimizacion_basica(plan)
                    elif op=="14": self._menu_optimizacion_recursos(plan)
                    elif op=="15": self._menu_recomendaciones_inteligentes(plan)
                    elif op=="5":
                        print("Pulsa Enter para conservar el valor actual.")
                        cambios={}
                        for campo,etiqueta in (("nombre","Nombre"),("fecha","Fecha"),("responsable","Responsable"),("observaciones","Observaciones"),("estado",f"Estado {self.core.produccion_real.ESTADOS}")):
                            actual=plan.get(campo,"")
                            valor=input(f"{etiqueta} [{actual}]: ").strip()
                            if valor: cambios[campo]=valor
                        if cambios:
                            d=self.core.produccion_real.editar_plan(plan['id'],cambios); print(f"Plan actualizado: {d['nombre']}.")
                        else: print("No se han realizado cambios.")
                    elif op=="6":
                        nombre=input(f"Nombre copia [{plan.get('nombre','')} (copia)]: ").strip() or None
                        fecha=input(f"Fecha [{plan.get('fecha','')}]: ").strip() or None
                        d=self.core.produccion_real.duplicar_plan(plan['id'],nombre,fecha)
                        print(f"Plan duplicado: {d['nombre']} | {d['id']}")
                    else:
                        if self._preguntar_si_no(f"¿Eliminar '{plan.get('nombre')}'? (s/n): "):
                            d=self.core.produccion_real.eliminar_plan(plan['id']); print(f"Plan eliminado: {d['nombre']}.")
                        else: print("Eliminación cancelada.")
                else: print("Opción no válida.")
            except Exception as exc:
                print(f"No se pudo completar la operación: {exc}")

    def _seleccionar_plan_produccion(self, usar_activo: bool = True):
        if usar_activo and self.ultimo_plan_produccion_id:
            try:
                plan=self.core.produccion_real.obtener_plan(self.ultimo_plan_produccion_id).to_dict()
                print(f"Plan activo: {plan.get('nombre')} | {plan.get('id')}")
                return plan
            except Exception:
                self.ultimo_plan_produccion_id=None
        q=input("Nombre, fecha, responsable, estado o ID (vacío=último plan): ").strip()
        if not q:
            planes=self.core.produccion_real.listar_planes()
            if not planes:
                print("No hay planes de producción.")
                return None
            plan=planes[-1]
            self.ultimo_plan_produccion_id=plan.get('id')
            print(f"Seleccionado: {plan.get('nombre')} | {plan.get('id')}")
            return plan
        planes=self.core.produccion_real.buscar_planes(q)
        if not planes:
            from difflib import get_close_matches
            todos=self.core.produccion_real.listar_planes()
            nombres=[str(x.get('nombre') or x.get('evento') or '') for x in todos]
            similares=get_close_matches(q,nombres,n=3,cutoff=0.45)
            candidatos=[x for nombre in similares for x in todos if (x.get('nombre') or x.get('evento'))==nombre]
            if candidatos:
                print("No hay coincidencia exacta. ¿Querías decir?")
                for i,x in enumerate(candidatos,1): print(f"{i}. {x.get('nombre')} | {x.get('id')}")
                plan=self._seleccionar_elemento(candidatos,"Selecciona el plan",auto_unico=True)
                if plan:
                    self.ultimo_plan_produccion_id=plan.get('id')
                return plan
            print("No se encontraron planes.")
            return None
        if len(planes)==1:
            plan=planes[0]
            self.ultimo_plan_produccion_id=plan.get('id')
            print(f"Seleccionado: {plan.get('nombre')} | {plan.get('id')}")
            return plan
        for i,x in enumerate(planes,1): print(f"{i}. [{x.get('estado','').upper()}] {x.get('nombre')} | {x.get('fecha') or 'sin fecha'} | {x.get('id')}")
        plan=self._seleccionar_elemento(planes,"Selecciona el plan")
        if plan:
            self.ultimo_plan_produccion_id=plan.get('id')
        return plan

    @staticmethod
    def _mostrar_conflictos_produccion(asignacion):
        conflictos=asignacion.get('conflictos',[]) or []
        if not conflictos:
            print("Sin conflictos de recursos.")
            return
        print(f"CONFLICTOS DETECTADOS: {len(conflictos)}")
        for i,c in enumerate(conflictos,1):
            print(f"{i}. {c.get('lectura_host_ai') or c.get('mensaje') or str(c)}")
        print("Usa la opción 14 para proponer una optimización de recursos.")

    def _imprimir_plan_produccion(self,p):
        print("\n"+"="*64)
        print(f"{p.get('nombre') or p.get('evento')} — {p.get('estado','').upper()}")
        print(f"ID: {p.get('id')} | Fecha: {p.get('fecha') or '-'} | Responsable: {p.get('responsable') or '-'}")
        if p.get('evento'): print(f"Evento: {p.get('evento')} | Pax: {p.get('pax',0)}")
        print(f"Tareas: {len(p.get('tareas',[]))} | Duración: {p.get('duracion_total_min',0)} min")
        if p.get('observaciones'): print(f"Observaciones: {p.get('observaciones')}")
        print("="*64)


    def _gestionar_tareas_plan(self, plan):
        while True:
            actual=self.core.produccion_real.obtener_plan(plan['id']).to_dict()
            print("\nTAREAS DEL PLAN")
            for i,t in enumerate(actual.get('tareas',[]),1): print(f"{i}. [{t.get('prioridad',50)}] {t.get('titulo')} | {len(t.get('fases',[]))} fase(s) | {t.get('id')}")
            print("1. Añadir tarea")
            print("2. Añadir fase a tarea")
            print("3. Eliminar tarea")
            print("0. Volver")
            op=input("Elige una opción: ").strip()
            if op=='0': return
            if op=='1':
                titulo=input("Título tarea: ").strip(); prioridad=int(input("Prioridad 0-100 [50]: ").strip() or '50')
                d=self.core.produccion_real.anadir_tarea_manual(plan['id'],titulo,prioridad); print(f"Tarea añadida: {d['titulo']}")
            elif op in {'2','3'}:
                tareas=actual.get('tareas',[])
                if not tareas: print("No hay tareas."); continue
                sel=input("Número de tarea: ").strip()
                if not sel.isdigit() or not 1<=int(sel)<=len(tareas): print("Selección no válida."); continue
                t=tareas[int(sel)-1]
                if op=='3':
                    if self._preguntar_si_no(f"¿Eliminar '{t['titulo']}'? (s/n): "): self.core.produccion_real.eliminar_tarea(plan['id'],t['id']); print("Tarea eliminada.")
                else:
                    nombre=input("Nombre fase: ").strip(); dur=int(input("Duración min: ").strip()); tipo=input("Tipo [activo/pasivo/reposo/coccion]: ").strip() or 'activo'; recurso=input("Recurso [mesa_trabajo]: ").strip() or 'mesa_trabajo'; responsable=input("Responsable [cocina]: ").strip() or 'cocina'; dependencia=input("Dependencia (opcional): ").strip()
                    self.core.produccion_real.anadir_fase_manual(plan['id'],t['id'],nombre,dur,tipo,recurso,responsable,dependencia); print("Fase añadida.")
            else: print("Opción no válida.")


    def _menu_ejecucion_produccion(self, plan):
        while True:
            resumen=self.core.produccion_real.resumen_ejecucion(plan['id'])
            print("\n"+"="*76)
            print(f"SEGUIMIENTO DE PRODUCCIÓN — {resumen['plan']} | {resumen['estado_plan'].upper()}")
            print(f"Avance global: {resumen['porcentaje_completado']}% | Tareas: {resumen['total_tareas']} | Alertas: {len(resumen.get('alertas',[]))}")
            for i,t in enumerate(resumen['tareas'],1):
                min_reales=t.get('tiempo_real_min',0)
                restante=t.get('tiempo_restante_estimado_min',0)
                chk=f" | checklist {t.get('checklist_completado',0)}/{t.get('checklist_total',0)}" if t.get('checklist_total') else ""
                bloqueo=f" | BLOQUEADA: {t.get('bloqueo')}" if t.get('bloqueo') else ""
                plan_actual=self.core.produccion_real.obtener_plan(plan['id']).to_dict()
                asignaciones=(plan_actual.get('asignacion_recursos') or {}).get('asignaciones',[])
                asignacion=next((a for a in asignaciones if str(a.get('elaboracion','')).lower()==str(t.get('titulo','')).lower()),{})
                responsable=asignacion.get('cocinero') or next((f.get('responsable') for f in t.get('fases',[]) if f.get('responsable')), 'sin asignar')
                recurso=str(asignacion.get('recurso') or next((f.get('recurso') for f in t.get('fases',[]) if f.get('recurso')), '-')).replace('_',' ')
                print(f"{i}. [{t.get('estado_ejecucion','pendiente').upper()}] {t.get('titulo')} | {t.get('porcentaje_avance',0)}% | {min_reales} min reales | quedan {restante} min | {responsable} | {recurso} | prioridad {t.get('prioridad',50)}{chk}{bloqueo}")
            for a in resumen.get('alertas',[]): print(f"AVISO: {a.get('tarea')} — {a.get('mensaje')}")
            print("="*76)
            print("1. Iniciar tarea")
            print("2. Pausar tarea")
            print("3. Reanudar tarea")
            print("4. Finalizar tarea")
            print("5. Actualizar porcentaje de avance")
            print("6. Registrar incidencia / retraso / bloqueo")
            print("7. Resolver bloqueo")
            print("8. Gestionar checklist")
            print("9. Añadir observaciones o replanificar tarea")
            print("10. Ver solo tareas pendientes y alertas")
            print("11. Actualizar vista")
            print("0. Volver")
            op=input("Elige una opción: ").strip()
            if op=='0': return
            if op=='11': continue
            if op=='10':
                pendientes=resumen.get('tareas_pendientes',[])
                print(f"\nTAREAS PENDIENTES: {len(pendientes)}")
                for t in pendientes: print(f"- [{t.get('estado_ejecucion','').upper()}] {t.get('titulo')} | {t.get('porcentaje_avance',0)}% | prioridad {t.get('prioridad',50)}")
                if not resumen.get('alertas'): print("Sin alertas activas.")
                continue
            if op not in {'1','2','3','4','5','6','7','8','9'}:
                print("Opción no válida."); continue
            tareas=resumen['tareas']
            if not tareas:
                print("El plan no tiene tareas."); continue
            sel=input("Número de tarea o 0 para cancelar: ").strip()
            if not sel or sel=='0':
                print("Operación cancelada."); continue
            if not sel.isdigit() or not 1<=int(sel)<=len(tareas):
                print("Selección no válida."); continue
            tarea=tareas[int(sel)-1]
            try:
                if op=='1':
                    d=self.core.produccion_real.iniciar_tarea(plan['id'],tarea['id']); print(f"Tarea iniciada: {d['titulo']}.")
                elif op=='2':
                    d=self.core.produccion_real.pausar_tarea(plan['id'],tarea['id']); print(f"Tarea pausada: {d['titulo']}.")
                elif op=='3':
                    d=self.core.produccion_real.reanudar_tarea(plan['id'],tarea['id']); print(f"Tarea reanudada: {d['titulo']}.")
                elif op=='4':
                    pendientes=tarea.get('checklist_pendiente',0)
                    if pendientes:
                        print(f"AVISO: quedan {pendientes} paso(s) del checklist sin completar.")
                    if self._preguntar_si_no(f"¿Finalizar '{tarea['titulo']}'? (s/n): "):
                        d=self.core.produccion_real.finalizar_tarea(plan['id'],tarea['id']); print(f"Tarea finalizada: {d['titulo']}.")
                    else: print("Finalización cancelada.")
                elif op=='5':
                    valor=float(input(f"Porcentaje de avance [{tarea.get('porcentaje_avance',0)}]: ").strip())
                    d=self.core.produccion_real.actualizar_progreso_tarea(plan['id'],tarea['id'],valor); print(f"Avance actualizado: {d['porcentaje_avance']}%.")
                elif op=='6':
                    print("Tipos: incidencia, retraso, bloqueo, observación")
                    tipo=input("Tipo [incidencia]: ").strip() or 'incidencia'
                    descripcion=input("Descripción: ").strip()
                    retraso=int(input("Minutos de retraso [0]: ").strip() or '0')
                    d=self.core.produccion_real.registrar_incidencia_tarea(plan['id'],tarea['id'],tipo,descripcion,retraso); print(f"Incidencia registrada: {d['tipo']}.")
                elif op=='7':
                    if not tarea.get('bloqueo'): print("La tarea no tiene un bloqueo activo."); continue
                    obs=input("Cómo se ha resuelto (opcional): ").strip()
                    self.core.produccion_real.resolver_bloqueo_tarea(plan['id'],tarea['id'],obs); print("Bloqueo resuelto.")
                elif op=='8':
                    self._gestionar_checklist_tarea(plan['id'],tarea['id'])
                elif op=='9':
                    prioridad_txt=input(f"Prioridad [{tarea.get('prioridad',50)}]: ").strip()
                    responsable=input("Nuevo responsable para sus fases (vacío=conservar): ").strip()
                    notas=input(f"Observaciones [{tarea.get('observaciones_ejecucion','')}]: ").strip()
                    prioridad=int(prioridad_txt) if prioridad_txt else None
                    d=self.core.produccion_real.replanificar_tarea_manual(plan['id'],tarea['id'],prioridad,responsable or None,notas or None)
                    print(f"Tarea actualizada: prioridad {d.get('prioridad')}.")
            except Exception as exc:
                print(f"No se pudo completar el seguimiento: {exc}")


    def _menu_optimizacion_basica(self, plan):
        while True:
            actual=self.core.produccion_real.obtener_plan(plan['id'])
            propuesta=dict(actual.propuesta_optimizacion or {})
            print("\n"+"="*76)
            print(f"OPTIMIZACIÓN BÁSICA — {actual.nombre}")
            if propuesta:
                print(f"Propuesta: {propuesta.get('id')} | Estado: {propuesta.get('estado','propuesta')}")
                print(f"Duración original: {propuesta.get('duracion_original_min',0)} min")
                print(f"Duración optimizada: {propuesta.get('duracion_optimizada_min',0)} min")
                print(f"Ahorro estimado: {propuesta.get('ahorro_min',0)} min")
                if propuesta.get('cambios'):
                    print("Cambios propuestos:")
                    for c in propuesta['cambios']:
                        print(f"- {c.get('tarea')}: {c.get('motivo')}")
                else:
                    print("No hace falta reordenar tareas: el plan ya está bien ajustado.")
            else:
                print("No hay propuesta pendiente.")
            print("="*76)
            print("1. Analizar y generar propuesta")
            print("2. Aplicar propuesta")
            print("3. Deshacer última optimización aplicada")
            print("4. Ver historial de optimizaciones")
            print("0. Volver")
            op=input("Elige una opción: ").strip()
            if op=='0': return
            try:
                if op=='1':
                    p=self.core.produccion_real.proponer_optimizacion_basica(plan['id'])
                    print(f"Propuesta generada: ahorro estimado {p.get('ahorro_min',0)} min.")
                elif op=='2':
                    if not propuesta:
                        print("No hay una propuesta pendiente."); continue
                    if self._preguntar_si_no("¿Aplicar esta optimización? (s/n): "):
                        p=self.core.produccion_real.aplicar_optimizacion_basica(plan['id'])
                        print(f"Optimización aplicada. Ahorro estimado: {p.get('ahorro_min',0)} min.")
                    else:
                        print("No se ha modificado la planificación.")
                elif op=='3':
                    if self._preguntar_si_no("¿Restaurar la planificación anterior? (s/n): "):
                        p=self.core.produccion_real.deshacer_ultima_optimizacion(plan['id'])
                        print(f"Planificación restaurada desde {p.get('id')}.")
                    else:
                        print("Restauración cancelada.")
                elif op=='4':
                    hist=actual.historial_optimizacion
                    print(f"Historial: {len(hist)} optimización(es).")
                    for h in hist:
                        print(f"- {h.get('id')} | {h.get('estado')} | ahorro {h.get('ahorro_min',0)} min | {h.get('aplicada_en') or h.get('creado_en')}")
                else:
                    print("Opción no válida.")
            except Exception as exc:
                print(f"No se pudo completar la optimización: {exc}")

    def _menu_optimizacion_recursos(self, plan):
        while True:
            actual=self.core.produccion_real.obtener_plan(plan['id'])
            propuesta=dict(actual.propuesta_optimizacion_recursos or {})
            print("\n"+"="*78)
            print(f"OPTIMIZACIÓN DE RECURSOS — {actual.nombre}")
            if propuesta:
                print(f"Propuesta: {propuesta.get('id')} | Estado: {propuesta.get('estado','propuesta')}")
                print(f"Conflictos antes: {len(propuesta.get('conflictos_originales',[]))} | después: {len(propuesta.get('conflictos_optimizados',[]))}")
                print(f"Movimientos propuestos: {len(propuesta.get('movimientos',[]))}")
                for m in propuesta.get('movimientos',[])[:20]:
                    print(f"- {m.get('tarea')} | {m.get('recurso')} | día {m.get('dia_original')} min {m.get('inicio_original_min')} → día {m.get('dia_nuevo')} min {m.get('inicio_nuevo_min')}")
                if propuesta.get('conflictos_optimizados'):
                    print("AVISO: todavía quedan conflictos que requieren revisión manual.")
                else:
                    print("La propuesta elimina los conflictos detectados con las capacidades indicadas.")
            else:
                print("No hay propuesta pendiente.")
            print("="*78)
            print("1. Analizar recursos y generar propuesta")
            print("2. Aplicar propuesta")
            print("3. Deshacer última optimización de recursos")
            print("4. Ver historial")
            print("0. Volver")
            op=input("Elige una opción: ").strip()
            if op=='0': return
            try:
                if op=='1':
                    plan_actual=self.core.produccion_real.obtener_plan(plan['id'])
                    recursos=sorted({str(b.get('recurso') or 'mesa_trabajo') for b in (plan_actual.planificacion_inteligente or {}).get('bloques',[]) if b.get('tipo_tiempo')=='activo'})
                    capacidades={}
                    print("Indica cuántas unidades reales hay de cada recurso.")
                    for r in recursos:
                        capacidades[r]=int(input(f"Capacidad de {r} [1]: ").strip() or '1')
                    p=self.core.produccion_real.proponer_optimizacion_recursos(plan['id'],capacidades)
                    print(f"Propuesta creada: {len(p.get('conflictos_originales',[]))} conflicto(s) antes y {len(p.get('conflictos_optimizados',[]))} después.")
                elif op=='2':
                    if not propuesta: print("No hay una propuesta pendiente."); continue
                    if self._preguntar_si_no("¿Aplicar esta optimización de recursos? (s/n): "):
                        p=self.core.produccion_real.aplicar_optimizacion_recursos(plan['id']); print(f"Optimización aplicada: {p.get('id')}.")
                    else: print("No se ha modificado la planificación.")
                elif op=='3':
                    if self._preguntar_si_no("¿Restaurar la planificación anterior? (s/n): "):
                        p=self.core.produccion_real.deshacer_ultima_optimizacion_recursos(plan['id']); print(f"Planificación restaurada desde {p.get('id')}.")
                    else: print("Restauración cancelada.")
                elif op=='4':
                    hist=actual.historial_optimizacion_recursos
                    print(f"Historial: {len(hist)} optimización(es) de recursos.")
                    for h in hist: print(f"- {h.get('id')} | {h.get('estado')} | conflictos {len(h.get('conflictos_originales',[]))}→{len(h.get('conflictos_optimizados',[]))} | {h.get('aplicada_en') or h.get('creado_en')}")
                else: print("Opción no válida.")
            except Exception as exc:
                print(f"No se pudo completar la optimización de recursos: {exc}")

    def _menu_recomendaciones_inteligentes(self, plan):
        while True:
            actual = self.core.produccion_real.obtener_plan(plan['id'])
            propuesta = dict(actual.propuesta_recomendaciones or {})
            print("\n" + "=" * 78)
            print(f"RECOMENDACIONES INTELIGENTES — {actual.nombre}")
            if propuesta:
                print(f"Análisis: {propuesta.get('id')} | {propuesta.get('total',0)} recomendación(es)")
                print(f"Críticas: {propuesta.get('criticas',0)} | Altas: {propuesta.get('altas',0)} | Aplicables: {propuesta.get('aplicables',0)}")
                for i, rec in enumerate(propuesta.get('recomendaciones', []), 1):
                    marca = "APLICABLE" if rec.get('aplicable') else "CONSEJO"
                    print(f"{i}. [{rec.get('prioridad','').upper()}] [{marca}] {rec.get('titulo')}")
                    print(f"   {rec.get('explicacion')}")
            else:
                print("No hay un análisis pendiente.")
            print("=" * 78)
            print("1. Analizar y generar recomendaciones")
            print("2. Aplicar todas las recomendaciones seguras")
            print("3. Aplicar recomendaciones seleccionadas")
            print("4. Descartar propuesta")
            print("5. Deshacer últimas recomendaciones aplicadas")
            print("6. Ver historial")
            print("0. Volver")
            op = input("Elige una opción: ").strip()
            if op == '0': return
            try:
                if op == '1':
                    d = self.core.produccion_real.generar_recomendaciones_inteligentes(plan['id'])
                    print(f"Análisis completado: {d.get('total',0)} recomendación(es).")
                elif op == '2':
                    if not propuesta: print("No hay recomendaciones pendientes."); continue
                    if self._preguntar_si_no("¿Aplicar todas las recomendaciones seguras?", por_defecto=False):
                        d = self.core.produccion_real.aplicar_recomendaciones(plan['id'])
                        print(f"Recomendaciones aplicadas: {d.get('total_aplicadas',0)}.")
                    else: print("No se han realizado cambios.")
                elif op == '3':
                    if not propuesta: print("No hay recomendaciones pendientes."); continue
                    aplicables = [r for r in propuesta.get('recomendaciones', []) if r.get('aplicable')]
                    if not aplicables: print("No hay recomendaciones aplicables automáticamente."); continue
                    for i, r in enumerate(aplicables, 1): print(f"{i}. {r.get('titulo')} | {r.get('prioridad')}")
                    texto = input("Números separados por coma (Enter=cancelar): ").strip()
                    if not texto: print("Operación cancelada."); continue
                    indices = []
                    for parte in texto.split(','):
                        parte = parte.strip()
                        if parte.isdigit() and 1 <= int(parte) <= len(aplicables): indices.append(int(parte)-1)
                    ids = [aplicables[i]['id'] for i in sorted(set(indices))]
                    if not ids: print("No se seleccionaron recomendaciones válidas."); continue
                    if self._preguntar_si_no(f"¿Aplicar {len(ids)} recomendación(es)?", por_defecto=False):
                        d = self.core.produccion_real.aplicar_recomendaciones(plan['id'], ids)
                        print(f"Recomendaciones aplicadas: {d.get('total_aplicadas',0)}.")
                elif op == '4':
                    if not propuesta: print("No hay recomendaciones pendientes."); continue
                    if self._preguntar_si_no("¿Descartar esta propuesta?", por_defecto=False):
                        self.core.produccion_real.descartar_recomendaciones(plan['id']); print("Propuesta descartada.")
                elif op == '5':
                    if self._preguntar_si_no("¿Restaurar los valores anteriores?", por_defecto=False):
                        d = self.core.produccion_real.deshacer_ultimas_recomendaciones(plan['id']); print(f"Cambios restaurados desde {d.get('id')}.")
                elif op == '6':
                    hist = actual.historial_recomendaciones
                    print(f"Historial: {len(hist)} análisis.")
                    for h in hist:
                        print(f"- {h.get('id')} | {h.get('estado')} | {h.get('total',0)} recomendaciones | {h.get('aplicada_en') or h.get('descartada_en') or h.get('creado_en')}")
                else: print("Opción no válida.")
            except Exception as exc:
                print(f"No se pudo completar la recomendación: {exc}")

    def _menu_recomendaciones_inteligentes(self, plan):
        while True:
            actual = self.core.produccion_real.obtener_plan(plan['id'])
            propuesta = dict(actual.propuesta_recomendaciones or {})
            print("\n" + "=" * 78)
            print(f"RECOMENDACIONES INTELIGENTES — {actual.nombre}")
            if propuesta:
                print(f"Análisis: {propuesta.get('id')} | {propuesta.get('total',0)} recomendación(es)")
                print(f"Críticas: {propuesta.get('criticas',0)} | Altas: {propuesta.get('altas',0)} | Aplicables: {propuesta.get('aplicables',0)}")
                for i, rec in enumerate(propuesta.get('recomendaciones', []), 1):
                    marca = "APLICABLE" if rec.get('aplicable') else "CONSEJO"
                    print(f"{i}. [{rec.get('prioridad','').upper()}] [{marca}] {rec.get('titulo')}")
                    print(f"   {rec.get('explicacion')}")
            else: print("No hay un análisis pendiente.")
            print("=" * 78)
            print("1. Analizar y generar recomendaciones")
            print("2. Aplicar todas las recomendaciones seguras")
            print("3. Aplicar recomendaciones seleccionadas")
            print("4. Descartar propuesta")
            print("5. Deshacer últimas recomendaciones aplicadas")
            print("6. Ver historial")
            print("0. Volver")
            op = input("Elige una opción: ").strip()
            if op == '0': return
            try:
                if op == '1':
                    d = self.core.produccion_real.generar_recomendaciones_inteligentes(plan['id']); print(f"Análisis completado: {d.get('total',0)} recomendación(es).")
                elif op == '2':
                    if not propuesta: print("No hay recomendaciones pendientes."); continue
                    if self._preguntar_si_no("¿Aplicar todas las recomendaciones seguras?", por_defecto=False):
                        d = self.core.produccion_real.aplicar_recomendaciones(plan['id']); print(f"Recomendaciones aplicadas: {d.get('total_aplicadas',0)}.")
                    else: print("No se han realizado cambios.")
                elif op == '3':
                    if not propuesta: print("No hay recomendaciones pendientes."); continue
                    aplicables = [r for r in propuesta.get('recomendaciones', []) if r.get('aplicable')]
                    if not aplicables: print("No hay recomendaciones aplicables automáticamente."); continue
                    for i, r in enumerate(aplicables, 1): print(f"{i}. {r.get('titulo')} | {r.get('prioridad')}")
                    texto = input("Números separados por coma (Enter=cancelar): ").strip()
                    if not texto: print("Operación cancelada."); continue
                    indices = [int(x.strip())-1 for x in texto.split(',') if x.strip().isdigit() and 1 <= int(x.strip()) <= len(aplicables)]
                    ids = [aplicables[i]['id'] for i in sorted(set(indices))]
                    if not ids: print("No se seleccionaron recomendaciones válidas."); continue
                    if self._preguntar_si_no(f"¿Aplicar {len(ids)} recomendación(es)?", por_defecto=False):
                        d = self.core.produccion_real.aplicar_recomendaciones(plan['id'], ids); print(f"Recomendaciones aplicadas: {d.get('total_aplicadas',0)}.")
                elif op == '4':
                    if not propuesta: print("No hay recomendaciones pendientes."); continue
                    if self._preguntar_si_no("¿Descartar esta propuesta?", por_defecto=False): self.core.produccion_real.descartar_recomendaciones(plan['id']); print("Propuesta descartada.")
                elif op == '5':
                    if self._preguntar_si_no("¿Restaurar los valores anteriores?", por_defecto=False):
                        d = self.core.produccion_real.deshacer_ultimas_recomendaciones(plan['id']); print(f"Cambios restaurados desde {d.get('id')}.")
                elif op == '6':
                    hist = actual.historial_recomendaciones; print(f"Historial: {len(hist)} análisis.")
                    for h in hist: print(f"- {h.get('id')} | {h.get('estado')} | {h.get('total',0)} recomendaciones | {h.get('aplicada_en') or h.get('descartada_en') or h.get('creado_en')}")
                else: print("Opción no válida.")
            except Exception as exc: print(f"No se pudo completar la recomendación: {exc}")

    def _menu_panel_produccion(self, plan):
        while True:
            panel=self.core.produccion_real.panel_produccion(plan['id'])
            metricas=panel.get('metricas_turno',{})
            estados=panel.get('estados',{})
            print("\n"+"="*78)
            print(f"PANEL DE PRODUCCIÓN — {panel.get('plan')} | {panel.get('estado_plan','').upper()}")
            print(f"Fecha: {panel.get('fecha') or '-'} | Responsable: {panel.get('responsable') or '-'}")
            print(f"AVANCE: {panel.get('porcentaje_completado',0)}% | Tareas {panel.get('total_tareas',0)} | Alertas {len(panel.get('alertas',[]))}")
            print(f"Pendientes {estados.get('pendiente',0)} | En curso {estados.get('en_curso',0)} | Pausadas {estados.get('pausada',0)} | Finalizadas {estados.get('finalizada',0)}")
            print(f"Tiempo previsto {metricas.get('minutos_previstos',0)} min | Real {metricas.get('minutos_reales',0)} min | Incidencias {metricas.get('incidencias',0)} | Bloqueos {metricas.get('bloqueos_activos',0)}")
            print(f"Checklist: {metricas.get('checklist_completado',0)}/{metricas.get('checklist_total',0)}")
            print("-"*78)
            for cocinero in panel.get('cocineros',[]):
                print(f"\n{cocinero.get('cocinero')} — {cocinero.get('minutos_asignados',0)} min asignados")
                if not cocinero.get('tareas'): print("  Sin tareas.")
                for tarea in cocinero.get('tareas',[]):
                    bloqueo=f" | BLOQUEO: {tarea.get('bloqueo')}" if tarea.get('bloqueo') else ''
                    recurso=f" | {tarea.get('recurso')}" if tarea.get('recurso') else ''
                    print(f"  [{tarea.get('estado','').upper()}] {tarea.get('titulo')} — {tarea.get('avance',0)}% | {tarea.get('tiempo_real_min',0)} min reales | quedan {tarea.get('tiempo_restante_min',0)} min{recurso}{bloqueo}")
            if panel.get('alertas'):
                print("\nALERTAS")
                for alerta in panel['alertas']:
                    print(f"- {alerta.get('tarea')}: {alerta.get('mensaje')}")
            print("="*78)
            print("1. Actualizar panel")
            print("2. Abrir ejecución de tareas")
            print("3. Ver resumen de cierre del turno")
            print("0. Volver")
            op=input("Elige una opción: ").strip()
            if op=='0': return
            if op=='1': continue
            if op=='2': self._menu_ejecucion_produccion(plan); continue
            if op=='3':
                d=self.core.produccion_real.estadisticas_turno(plan['id'])
                print(f"\nCIERRE DE TURNO — {d['plan']}")
                print(f"Estado: {d['estado']} | Avance: {d['avance']}%")
                print(f"Finalizadas: {d['finalizadas']}/{d['total_tareas']} | Pendientes: {d['pendientes']}")
                print(f"Previsto: {d['minutos_previstos']} min | Real: {d['minutos_reales']} min")
                print(f"Incidencias: {d['incidencias']} | Alertas: {d['alertas']} | Bloqueos: {d['bloqueos_activos']}")
                continue
            print("Opción no válida.")

    def _gestionar_checklist_tarea(self, plan_id, tarea_id):
        while True:
            tarea=self.core.produccion_real.estado_tarea(plan_id,tarea_id)
            print(f"\nCHECKLIST — {tarea.get('titulo')}")
            for i,item in enumerate(tarea.get('checklist',[]),1):
                marca='OK' if item.get('completado') else 'PENDIENTE'
                print(f"{i}. [{marca}] {item.get('texto')} | {item.get('id')}")
            print("1. Añadir paso")
            print("2. Marcar / desmarcar paso")
            print("3. Eliminar paso")
            print("0. Volver")
            op=input("Elige una opción: ").strip()
            if op=='0': return
            if op=='1':
                texto=input("Nuevo paso: ").strip()
                try:
                    d=self.core.produccion_real.anadir_item_checklist(plan_id,tarea_id,texto); print(f"Paso añadido: {d['texto']}.")
                except Exception as exc: print(f"No se pudo añadir: {exc}")
                continue
            items=tarea.get('checklist',[])
            if not items: print("No hay pasos en el checklist."); continue
            sel=input("Número de paso o 0 para cancelar: ").strip()
            if not sel or sel=='0': print("Operación cancelada."); continue
            if not sel.isdigit() or not 1<=int(sel)<=len(items): print("Selección no válida."); continue
            item=items[int(sel)-1]
            try:
                if op=='2':
                    nuevo=not bool(item.get('completado'))
                    d=self.core.produccion_real.marcar_item_checklist(plan_id,tarea_id,item['id'],nuevo)
                    print(f"Paso {'completado' if d['completado'] else 'pendiente'}.")
                elif op=='3':
                    if self._preguntar_si_no(f"¿Eliminar '{item.get('texto')}'? (s/n): "):
                        self.core.produccion_real.eliminar_item_checklist(plan_id,tarea_id,item['id']); print("Paso eliminado.")
                else: print("Opción no válida.")
            except Exception as exc: print(f"No se pudo actualizar el checklist: {exc}")

    @staticmethod
    def _hora_desde_minutos(minutos, hora_inicio="08:00"):
        try:
            h,m=[int(x) for x in hora_inicio.split(":")[:2]]
        except Exception:
            h,m=8,0
        total=h*60+m+int(minutos or 0)
        return f"{(total//60)%24:02d}:{total%60:02d}"

    def _imprimir_planificacion_inteligente(self,p):
        pl=p.get('planificacion_inteligente') or {}; asig=p.get('asignacion_recursos') or {}
        if not pl:
            print("Este plan todavía no tiene planificación inteligente. Usa primero la opción 9.")
            return
        cfg=p.get('configuracion_planificacion') or {}
        hora_inicio=cfg.get('hora_inicio','08:00')
        bloques=pl.get('bloques',[]) or []
        asignaciones=asig.get('asignaciones',[]) or []
        dias=[int(pl.get('dias_necesarios',0) or 0)]
        dias += [int(x.get('dia',1) or 1) for x in bloques]
        dias += [int(x.get('dia',1) or 1) for x in asignaciones]
        dias_reales=max(dias or [1])
        print("\n"+"="*78)
        print(f"PLANIFICACIÓN — {p.get('nombre')}")
        print(f"Días reales: {dias_reales} | Activo: {pl.get('minutos_activos',0)} min | Pasivo: {pl.get('minutos_pasivos',0)} min | Ocupación: {pl.get('ocupacion_pct',0)}%")
        print(f"Inicio: {hora_inicio} | Cocineros: {cfg.get('cocineros','-')} | Jornada: {cfg.get('jornada_horas','-')} h")
        print("\nBLOQUES CON HORARIO")
        acumulado={}
        for b in bloques:
            dia=int(b.get('dia',1) or 1)
            inicio=int(b.get('inicio_min',acumulado.get(dia,0)) or 0)
            dur=int(b.get('duracion_min',0) or 0)
            fin=int(b.get('fin_min',inicio+dur) or inicio+dur)
            acumulado[dia]=max(acumulado.get(dia,0),fin)
            nombre=str(b.get('nombre',''))
            asignacion=next((a for a in asignaciones if str(a.get('elaboracion','')).lower()==nombre.lower()),{})
            responsable=asignacion.get('cocinero') or ('Maquinaria / pasivo' if b.get('tipo_tiempo')=='pasivo' else 'Sin asignar')
            recurso=str(b.get('recurso') or '-').replace('_',' ').title()
            print(f"- Día {dia} | {self._hora_desde_minutos(inicio,hora_inicio)}-{self._hora_desde_minutos(fin,hora_inicio)} | {responsable} | {nombre} | {b.get('tipo_tiempo')} | {recurso}")
        print("\nREPARTO Y CARGA")
        cargas={}
        for a in asignaciones:
            cocinero=str(a.get('cocinero') or 'Sin asignar')
            cargas[cocinero]=cargas.get(cocinero,0)+int(a.get('duracion_min',0) or 0)
            recurso=str(a.get('recurso') or '-').replace('_',' ').title()
            print(f"- Día {a.get('dia',1)} | {cocinero} | {a.get('elaboracion')} | {a.get('duracion_min')} min | {recurso} | riesgo {a.get('riesgo','normal')}")
        if cargas:
            print("Carga total: " + " | ".join(f"{c}: {m} min" for c,m in sorted(cargas.items())))
        self._mostrar_conflictos_produccion(asig)
        print("="*78)

    # ------------------------------------------------------------------
    # ESTADO
    # ------------------------------------------------------------------
    def _estado_sistema(self):
        r = self.core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
        print(r.mensaje)
        for p in r.datos.get("pipelines", []):
            print(f"- {p['nombre']}: {p['descripcion']}")



    def _menu_excel(self):
        print("\nEXCEL / IMPORTACIONES")
        print("1. Analizar archivo Excel")
        print("2. Detectar tipo de documento Excel")
        print("3. Vista previa escandallos Excel")
        print("4. Importar escandallos Excel")
        print("5. Vista previa artículos Excel")
        print("6. Importar artículos Excel")
        print("7. Vista previa inventario Excel")
        print("8. Importar inventario Excel")
        print("0. Volver")
        op = input("Elige una opción: ").strip()
        if op == "1":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("analizar_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 10,
                "exportar_json": True,
            }))
            print(r.mensaje)
            for h in r.datos.get("hojas", []):
                print(f"- {h['nombre']}: {h['filas']} filas, {h['columnas']} columnas")
                for c in h.get("columnas_detectadas", [])[:8]:
                    print(f"  · {c['letra']} {c['nombre_detectado']} | {c['tipo_detectado']} | vacío {c['porcentaje_vacio']}%")

        elif op == "2":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("detectar_documento_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 10,
                "exportar_json": True,
            }))
            print(r.mensaje)
            for h in r.datos.get("hojas", []):
                print(f"- {h['hoja']}: {h['tipo_principal']} ({h['confianza']}%)")
                for aviso in h.get("avisos", []):
                    print(f"  Aviso: {aviso}")

        elif op == "3":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("vista_previa_escandallos_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 50,
            }))
            print(r.mensaje)
            for e in r.datos.get("escandallos", []):
                print(f"- {e['receta_id']} | {e['nombre']} | {len(e['lineas'])} líneas")

        elif op == "4":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("importar_escandallos_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 200,
                "reemplazar": True,
            }))
            print(r.mensaje)
            for e in r.datos.get("escandallos", []):
                print(f"- Importado: {e['receta_id']} | {e['nombre']}")

        elif op == "5":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("vista_previa_articulos_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 100,
            }))
            print(r.mensaje)
            for a in r.datos.get("articulos", [])[:20]:
                print(f"- {a['articulo_id']} | {a['nombre']} | {a['unidad']} | {a['precio_unitario']}")

        elif op == "6":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("importar_articulos_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 500,
                "actualizar_existentes": True,
            }))
            print(r.mensaje)
            for a in r.datos.get("articulos", [])[:20]:
                print(f"- Importado: {a['articulo_id']} | {a['nombre']}")

        elif op == "7":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("vista_previa_inventario_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 200,
            }))
            print(r.mensaje)
            for l in r.datos.get("lineas", [])[:20]:
                print(f"- {l['articulo_id']} | {l['nombre']} | {l['cantidad']} {l['unidad']} | {l['ubicacion']}")

        elif op == "8":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("importar_inventario_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 1000,
                "crear_articulos": True,
                "actualizar_stock": True,
            }))
            print(r.mensaje)
            for c in r.datos.get("cambios", [])[:20]:
                print(f"- {c['nombre']}: {c['anterior']} -> {c['nuevo']} {c['unidad']}")

    def _menu_base_datos(self):
        print("\nBASE DE DATOS LOCAL")
        print("1. Guardar todo")
        print("2. Ver resumen")
        print("3. Crear snapshot")
        print("0. Volver")
        op = input("Elige una opción: ").strip()
        if op == "1":
            r = self.core.orquestador.resolver(SolicitudHostAI("guardar_todo_db", {}))
            print(r.mensaje)
        elif op == "2":
            r = self.core.orquestador.resolver(SolicitudHostAI("resumen_db", {}))
            print(r.mensaje)
            for c in r.datos.get("colecciones", []):
                print(f"- {c['coleccion']}: {c['total']} registros")
        elif op == "3":
            nombre = input("Nombre snapshot (opcional): ").strip()
            r = self.core.orquestador.resolver(SolicitudHostAI("snapshot_db", {"nombre": nombre}))
            print(r.mensaje)

    def _requiere_evento(self):
        if not self.ultimo_evento_id:
            print("No hay evento activo. Crea uno primero.")
            return False
        return True

    def _escandallo_demo(self):
        return {
            "receta_id": "REC-CARRILLERA",
            "nombre": "Carrillera melosa",
            "raciones_base": 10,
            "grupo": "Carnes",
            "lineas": [
                {
                    "nombre": "Carrillera de ternera",
                    "cantidad": 1.8,
                    "unidad": "kg",
                    "tipo": "articulo",
                    "articulo_id": "ART-CARRILLERA",
                    "merma_porcentaje": 10,
                    "familia": "carnes",
                    "proveedor_preferente": "Proveedor Carnes",
                    "coste_unitario": 8.5,
                },
                {
                    "nombre": "Demi-glace",
                    "cantidad": 0.8,
                    "unidad": "L",
                    "tipo": "elaboracion",
                    "elaboracion_id": "ELAB-DEMI",
                    "merma_porcentaje": 0,
                    "familia": "salsas",
                    "proveedor_preferente": "Producción interna",
                    "coste_unitario": 3.0,
                },
            ],
        }
