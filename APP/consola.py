from __future__ import annotations

from datetime import date
from pathlib import Path
from CORE.orquestador import SolicitudHostAI
from SERVICIOS.contexto_global_rr161a import ContextoGlobalRR161A
from SERVICIOS.detector_escandallos_antiguos_i11 import DetectorEscandallosAntiguosI11, formatear_resumen_i11
from SERVICIOS.importador_seguro_escandallos_i12 import ImportadorSeguroEscandallosI12, formatear_previa_i12
from SERVICIOS.detector_limpio_menus_i131 import DetectorLimpioMenusI131, formatear_previa_i131
from SERVICIOS.motor_reconocimiento_menus_i1321 import MotorReconocimientoMenusI1321, formatear_reconocimiento_i1321
from SERVICIOS.constructor_arbol_semantico_menus_i1322 import ConstructorArbolSemanticoMenusI1322, formatear_arbol_semantico_i1322
from SERVICIOS.vista_previa_resolucion_asistida_menus_i1323 import VistaPreviaResolucionAsistidaMenusI1323, formatear_vista_previa_i1323
from SERVICIOS.motor_aprendizaje_culinario_i1324 import MotorAprendizajeCulinarioI1324, formatear_vista_aprendizaje_i1324
from SERVICIOS.preimportador_definitivo_menus_i133 import PreimportadorDefinitivoMenusI133, formatear_preimportacion_i133
from SERVICIOS.resolutor_bloqueos_preimportacion_i1331 import ResolutorBloqueosPreimportacionI1331, formatear_resolucion_i1331
from SERVICIOS.diagnostico_mur_m11 import DiagnosticoMURM11, formatear_diagnostico_m11
from SERVICIOS.diagnostico_resolutor_articulos_m12 import DiagnosticoResolutorArticulosM12, formatear_diagnostico_m12
from SERVICIOS.diagnostico_resolutor_recetas_m13 import DiagnosticoResolutorRecetasM13, formatear_diagnostico_m13
from SERVICIOS.diagnostico_importador_recetas_m131 import DiagnosticoImportadorRecetasM131, formatear_diagnostico_m131
from SERVICIOS.diagnostico_resolucion_ingredientes_m132 import DiagnosticoResolucionIngredientesM132, formatear_diagnostico_m132
from SERVICIOS.diagnostico_validacion_culinaria_m133 import DiagnosticoValidacionCulinariaM133, formatear_diagnostico_m133
from SERVICIOS.simulador_importacion_menus_i13411 import SimuladorImportacionMenusI13411, formatear_simulacion_i13411
from SERVICIOS.detector_multihoja_menus_i13411 import formatear_deteccion_multihoja_i13411
from SERVICIOS.simulador_importacion_menus_i13412 import SimuladorImportacionMenusI13412, formatear_simulacion_i13412
from SERVICIOS.bandeja_revision_i13413 import BandejaRevisionI13413, formatear_bandeja_i13413
from SERVICIOS.bandeja_revision_i13414 import BandejaRevisionI13414, formatear_bandeja_i13414
from SERVICIOS.bandeja_revision_i13415 import BandejaRevisionI13415, formatear_bandeja_i13415
from SERVICIOS.diagnostico_escritura_segura_i1342 import DiagnosticoEscrituraSeguraI1342, formatear_diagnostico_i1342
from SERVICIOS.diagnostico_importacion_menus_i1343 import DiagnosticoImportacionMenusI1343, formatear_diagnostico_i1343
from SERVICIOS.diagnostico_auditoria_postimportacion_i1344 import DiagnosticoAuditoriaPostimportacionI1344, formatear_diagnostico_i1344
from SERVICIOS.auditor_integridad_postimportacion_i1344 import AuditorIntegridadPostimportacionI1344, formatear_auditoria_i1344
from SERVICIOS.diagnostico_bandeja_correccion_i13441 import DiagnosticoBandejaCorreccionI13441, formatear_diagnostico_i13441
from SERVICIOS.bandeja_correccion_postimportacion_i13441 import BandejaCorreccionPostimportacionI13441, formatear_bandeja_i13441
from SERVICIOS.bandeja_correccion_inteligente_i13442 import (
    BandejaCorreccionInteligenteI13442, formatear_navegacion_i13442,
    formatear_grupos_tipo_i13442, formatear_grupos_menu_i13442,
)
from SERVICIOS.diagnostico_correccion_inteligente_i13442 import (
    DiagnosticoCorreccionInteligenteI13442, formatear_diagnostico_i13442,
)
from SERVICIOS.importador_definitivo_menus_i1343 import ImportadorDefinitivoMenusI1343
from SERVICIOS.certificador_final_importador_i135 import CertificadorFinalImportadorI135, formatear_certificacion_i135
from SERVICIOS.host_ai_executive import (
    EXEC_INTENCION_BLOQUEO_PRODUCCION,
    EXEC_INTENCION_DESBLOQUEO,
    EXEC_INTENCION_IMPACTO_COMPRAS,
    EXEC_INTENCION_IMPACTO_GENERAL,
    EXEC_INTENCION_IMPACTO_PRODUCCION,
    EXEC_INTENCION_MOTIVO_PRIORIDAD,
    EXEC_INTENCION_PLAN_DIA,
    EXEC_INTENCION_PLAN_OPERATIVO,
    HostAIExecutive,
    EXEC_INTENCION_RESTAURANTE,
    detectar_intencion_executive,
    formatear_respuesta_executive_conversacional,
    presentar_accion_ejecutiva,
)
from SERVICIOS.produccion_stock_piloto_14 import ProduccionStockPiloto14


class AppConsolaHostAI:
    """
    App Base Ejecutable Host AI 3.0.0.

    Freeze-A1: esta consola no define una ruta de arranque independiente.
    Se reutiliza desde `ConsolaPiloto01` y lanzadores de compatibilidad.

    Primera capa de uso real por terminal.
    No sustituye la futura interfaz gráfica, pero permite usar Host AI como programa.
    """

    def __init__(self, core):
        self.core = core
        self._contexto_global = ContextoGlobalRR161A(getattr(core, "base_dir", None))
        # Permite inicializar la consola con cores parciales usados en tests.
        self._produccion_stock = ProduccionStockPiloto14(core) if hasattr(core, "produccion_real") else None

    @property
    def ultimo_evento_id(self):
        return self._contexto_global.obtener("evento_id")

    @ultimo_evento_id.setter
    def ultimo_evento_id(self, valor):
        self._contexto_global.establecer("evento_id", valor)

    @property
    def ultimo_plan_produccion_id(self):
        return self._contexto_global.obtener("plan_produccion_id")

    @ultimo_plan_produccion_id.setter
    def ultimo_plan_produccion_id(self, valor):
        self._contexto_global.establecer("plan_produccion_id", valor)

    @property
    def ultima_necesidad_compra_id(self):
        return self._contexto_global.obtener("necesidad_compra_id")

    @ultima_necesidad_compra_id.setter
    def ultima_necesidad_compra_id(self, valor):
        self._contexto_global.establecer("necesidad_compra_id", valor)

    @property
    def ultimo_pedido_compra_id(self):
        return self._contexto_global.obtener("pedido_compra_id")

    @ultimo_pedido_compra_id.setter
    def ultimo_pedido_compra_id(self, valor):
        self._contexto_global.establecer("pedido_compra_id", valor)

    @property
    def ultimo_escandallo_id(self):
        return self._contexto_global.obtener("escandallo_id")

    @ultimo_escandallo_id.setter
    def ultimo_escandallo_id(self, valor):
        self._contexto_global.establecer("escandallo_id", valor)

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

    def _seleccionar_con_activo(self, elementos, activo_id, etiqueta, id_key="id"):
        if not elementos:
            return None
        activo = next((e for e in elementos if str(e.get(id_key, "")) == str(activo_id or "")), None)
        if activo:
            print(f"{etiqueta} activo: {activo.get('nombre') or activo.get('proveedor') or activo.get(id_key)} | {activo.get(id_key)}")
            usar = input("Enter=usar activo | número/ID=elegir otro | 0=cancelar: ").strip()
            if not usar:
                return activo
            if usar == "0":
                print("Operación cancelada.")
                return None
            if usar.isdigit() and 1 <= int(usar) <= len(elementos):
                return elementos[int(usar) - 1]
            for elemento in elementos:
                if str(elemento.get(id_key, "")).lower() == usar.lower():
                    return elemento
            print("Selección no válida.")
            return None
        return self._seleccionar_elemento(elementos, prompt="Selecciona número o escribe el ID", permitir_id=True, id_key=id_key, auto_unico=False)

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
            elif opcion == "12":
                self._menu_escandallos_recetas()
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
        print("11. RR1.6.1-D IA contextual (comprender y preparar, no ejecutar)")
        print("12. Escandallos y recetas")
        if self.ultimo_evento_id:
            try:
                evento = self.core.eventos.obtener(self.ultimo_evento_id)
                nombre = evento.nombre if hasattr(evento, "nombre") else evento.get("nombre", self.ultimo_evento_id)
                print(f"Contexto activo: {nombre} | {self.ultimo_evento_id}")
            except Exception:
                self.ultimo_evento_id = None
        print("0. Salir")

    # ------------------------------------------------------------------
    # CHAT
    # ------------------------------------------------------------------
    def _hablar_host_ai(self):
        print("\nHabla con Host AI. Escribe 'salir' para volver.")
        self._mostrar_resumen_proactivo_host_ai()
        while True:
            texto = input("Tú: ").strip()
            if texto.lower() in {"salir", "volver", "0"}:
                break

            intencion_exec = detectar_intencion_executive(texto)
            if intencion_exec is not None:
                executive = HostAIExecutive(getattr(self.core, "base_dir", None))
                intenciones_focus = {
                    EXEC_INTENCION_IMPACTO_GENERAL,
                    EXEC_INTENCION_IMPACTO_PRODUCCION,
                    EXEC_INTENCION_IMPACTO_COMPRAS,
                    EXEC_INTENCION_BLOQUEO_PRODUCCION,
                    EXEC_INTENCION_DESBLOQUEO,
                    EXEC_INTENCION_MOTIVO_PRIORIDAD,
                }
                intenciones_plan = {
                    EXEC_INTENCION_PLAN_OPERATIVO,
                    EXEC_INTENCION_PLAN_DIA,
                }
                if intencion_exec == EXEC_INTENCION_RESTAURANTE:
                    resultado_exec = executive.analizar_restaurante(core=self.core)
                elif intencion_exec in intenciones_plan:
                    if intencion_exec == EXEC_INTENCION_PLAN_DIA:
                        resultado_exec = executive.analizar_restaurante(core=self.core)
                        tipo_plan = "restaurante"
                    else:
                        evento_plan = self._evento_activo_para_executive()
                        if evento_plan:
                            resultado_exec = executive.analizar_evento_para_plan(evento_plan, core=self.core)
                            tipo_plan = "evento"
                        else:
                            resultado_exec = executive.analizar_restaurante(core=self.core)
                            tipo_plan = "restaurante"
                    resultado_exec = dict(resultado_exec)
                    resultado_exec["plan_operativo"] = executive.generar_plan_operativo(resultado_exec, tipo_plan=tipo_plan)
                elif intencion_exec in intenciones_focus:
                    evento_focus = self._evento_activo_para_executive()
                    if evento_focus:
                        resultado_exec = executive.analizar_evento(evento_focus)
                    else:
                        resultado_exec = executive.analizar_restaurante(core=self.core)
                else:
                    evento = self._evento_activo_para_executive()
                    if not evento:
                        print("Host AI: Necesito un evento activo para generar el resumen ejecutivo. Selecciona primero un evento.")
                        continue
                    resultado_exec = executive.analizar_evento(evento)
                print("Host AI:")
                print(formatear_respuesta_executive_conversacional(resultado_exec, intencion_exec))
                continue

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

    def _mostrar_resumen_proactivo_host_ai(self) -> None:
        evento = self._obtener_evento_activo()
        if not evento:
            return

        try:
            evento_id = getattr(evento, "id", "")
            nombre = getattr(evento, "nombre", "evento activo") or "evento activo"
            resumen = self.core.eventos.resumen_ejecutivo(evento_id)
            avisos = list((resumen or {}).get("avisos") or [])
        except Exception:
            return

        tareas: list[str] = []
        if any(a in {"Faltan servicios.", "Hay servicios sin pases.", "Hay pases sin recetas."} for a in avisos):
            tareas.append(presentar_accion_ejecutiva("MENU_ASOCIAR"))

        if not self.ultimo_plan_produccion_id:
            tareas.append(presentar_accion_ejecutiva("PRODUCCION_PLAN"))
        if not self.ultimo_pedido_compra_id:
            tareas.append(presentar_accion_ejecutiva("COMPRAS_PREPARAR"))

        dedup = []
        for t in tareas:
            if t not in dedup:
                dedup.append(t)
        tareas = dedup[:3]

        print("Host AI:")
        print(f"He revisado el evento activo \"{nombre}\".")
        if tareas:
            print("")
            print("Quedan estas tareas:")
            for t in tareas:
                print(f"• {t}.")

            prioridad = tareas[0]
            motivo = "porque desbloquea Producción y Compras" if "menú" in prioridad.lower() or "menu" in prioridad.lower() else "porque desbloquea el siguiente bloque operativo"
            print("")
            print(f"La prioridad ahora es {prioridad.lower()} {motivo}.")
        else:
            print("")
            print("No detecto tareas operativas urgentes en este momento.")

        print("")
        print("Puedes preguntarme:")
        print("- qué falta;")
        print("- qué es lo más urgente;")
        print("- qué riesgos hay;")
        print("- qué me recomiendas.")
        print("")
        print("Modo seguro activado.")

    def _evento_activo_para_executive(self):
        evento = self._obtener_evento_activo()
        if not evento:
            return {}
        return {
            "id": getattr(evento, "id", ""),
            "nombre": getattr(evento, "nombre", ""),
            "tipo": getattr(evento, "tipo", "evento"),
            "personas": getattr(evento, "pax", None),
            "pax": getattr(evento, "pax", None),
            "fecha": getattr(evento, "fecha", ""),
            "hora_servicio": getattr(evento, "hora_inicio", "") or "12:00",
            "menu": getattr(evento, "tipo_menu", "") or "menu operativo",
            "lugar": getattr(evento, "lugar", "") or "lugar operativo",
            "restricciones": "sin restricciones",
            "objetivo": "flujo completo",
        }

    def _probar_comprension_ia11(self):
        print("\nRR1.6.1-D — IA CONTEXTUAL, PROPUESTA SEGURA")
        print("Responde a las preguntas con frases cortas. Escribe 'cancelar' para borrar el contexto o 'salir' para volver.")
        sesion = "consola_base"
        self.core.pulido_ia_rr15.reiniciar(sesion)
        while True:
            texto = input("Tú: ").strip()
            if texto.lower() in {"salir", "volver", "0"}:
                self.core.pulido_ia_rr15.reiniciar(sesion)
                return
            contexto = {}
            if self.ultimo_evento_id:
                contexto["evento_id"] = self.ultimo_evento_id
            if self.ultimo_plan_produccion_id:
                contexto["plan_id"] = self.ultimo_plan_produccion_id
            if self.ultimo_pedido_compra_id:
                contexto["pedido_id"] = self.ultimo_pedido_compra_id
            if self.ultimo_escandallo_id:
                contexto["receta_id"] = self.ultimo_escandallo_id
            resultado = self.core.pulido_ia_rr15.procesar(texto, sesion, contexto)
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
            print("Modo seguro RR1.6.1-D: no se han ejecutado motores ni modificado datos.")

    def _menu_escandallos_recetas(self):
        from SERVICIOS.escandallos_recetas_601 import ModuloEscandallosRecetas601

        ModuloEscandallosRecetas601(getattr(self.core, "base_dir", None)).ejecutar()

    # ------------------------------------------------------------------
    # EVENTOS
    # ------------------------------------------------------------------
    def _menu_eventos(self):
        while True:
            abiertos = self._eventos_abiertos()
            print("\n" + "═" * 62)
            print("EVENTOS")
            print("\n¿Qué quieres hacer?")
            if abiertos:
                proximo = abiertos[0]
                print(f"\n1. Continuar preparando un evento ({len(abiertos)} activos)")
                print(f"   {self._texto_evento_destacado(proximo)}")
                activo = self._obtener_evento_activo()
                if activo:
                    print(f"   EVENTO QUE ESTÁS PREPARANDO: {activo.nombre} · {activo.pax} pax")
                print("   Al continuar: Ver qué falta y seguir desde el punto actual.")
                print("2. Crear un evento nuevo")
                print("3. Buscar un evento")
            else:
                print("1. Crear evento")
                print("2. Buscar o listar eventos")
                print("   Recomendación: empieza creando el evento que acaba de llegar.")
                print("   Siguiente paso: crea el primer evento o busca una reserva existente.")
            print("\n" + "─" * 62)
            print("4. Calendario")
            print("5. Eventos finalizados")
            print("6. Más opciones — Acciones avanzadas")
            print("0. Volver")
            print("═" * 62)
            op = input("Elige una opción: ").strip()

            if op == "0":
                return
            if not abiertos:
                if op == "1":
                    self._crear_evento_rapido()
                elif op == "2":
                    self._buscar_o_listar_eventos()
                elif op == "4": self._ver_calendario_eventos()
                elif op == "5": self._ver_eventos_finalizados()
                elif op == "6": self._mas_opciones_entrada_eventos()
                else: print("No he entendido la opción. Puedes crear un evento, buscarlo o volver.")
            elif op == "1":
                self._elegir_evento_para_continuar(abiertos)
            elif op == "2":
                self._crear_evento_rapido()
            elif op == "3":
                self._buscar_y_seleccionar_evento()
            elif op == "4":
                self._ver_calendario_eventos()
            elif op == "5":
                self._ver_eventos_finalizados()
            elif op == "6":
                self._mas_opciones_entrada_eventos()
            else:
                print("No he entendido la opción. Elige una de las acciones visibles o vuelve con 0.")

    def _todos_los_eventos(self):
        try:
            return list(self.core.eventos.listar_eventos())
        except (AttributeError, TypeError, ValueError):
            activo = self._obtener_evento_activo()
            return [activo] if activo else []

    def _eventos_abiertos(self):
        cerrados = {"finalizado", "facturado", "cancelado", "cerrado"}
        return sorted(
            [e for e in self._todos_los_eventos() if str(e.estado).lower() not in cerrados],
            key=lambda e: (e.fecha or "9999-99-99", e.nombre.lower()),
        )

    @staticmethod
    def _texto_evento_destacado(evento, hoy=None):
        hoy = hoy or date.today()
        fecha_texto = str(getattr(evento, "fecha", "") or "").strip()
        try:
            fecha_evento = date.fromisoformat(fecha_texto)
        except ValueError:
            return f"Evento activo sin fecha confirmada: {evento.nombre} · {evento.pax} pax"
        if fecha_evento < hoy:
            return f"⚠ Evento pasado pendiente de revisar: {evento.nombre} · {fecha_texto} · {evento.pax} pax"
        return f"Próximo: {evento.nombre} · {fecha_texto} · {evento.pax} pax"

    def _elegir_evento_para_continuar(self, eventos):
        if len(eventos) == 1:
            elegido = eventos[0]
        else:
            print("\n¿Con cuál seguimos?")
            for indice, evento in enumerate(eventos, 1):
                print(f"{indice}. {evento.fecha} · {evento.nombre} · {evento.pax} pax")
            valor = input("Elige un evento (0=volver): ").strip()
            if not valor.isdigit() or not 1 <= int(valor) <= len(eventos):
                return
            elegido = eventos[int(valor) - 1]
        self.ultimo_evento_id = elegido.id
        print(f"\nPerfecto. Seguimos con {elegido.nombre}.")
        self._continuar_preparacion_evento("seleccion")

    def _ver_calendario_eventos(self):
        eventos = self._todos_los_eventos()
        print("\nCALENDARIO DE EVENTOS")
        if not eventos:
            print("Todavía no hay fechas reservadas.")
            print("Siguiente paso: crea el primer evento cuando llegue la reserva.")
            return
        for evento in eventos:
            print(f"- {evento.fecha} · {evento.nombre} · {evento.pax} pax · {evento.estado}")

    def _ver_eventos_finalizados(self):
        finales = {"finalizado", "facturado", "cerrado"}
        eventos = [e for e in self._todos_los_eventos() if str(e.estado).lower() in finales]
        print("\nEVENTOS FINALIZADOS")
        if not eventos:
            print("Todavía no hay eventos finalizados.")
            print("Estado actual: los eventos disponibles siguen en preparación.")
            return
        for evento in eventos:
            print(f"- {evento.fecha} · {evento.nombre} · {evento.pax} pax")

    def _mas_opciones_entrada_eventos(self):
        print("\nMÁS OPCIONES")
        print("1. Ver todos los eventos")
        print("2. Buscar por cualquier dato")
        print("0. Volver")
        op = input("Elige una opción: ").strip()
        if op == "1": self._listar_y_seleccionar_eventos()
        elif op == "2": self._buscar_y_seleccionar_evento()

    def _obtener_evento_activo(self):
        if not self.ultimo_evento_id:
            return None
        try:
            return self.core.eventos.obtener(self.ultimo_evento_id)
        except ValueError:
            self.ultimo_evento_id = None
            return None

    def _mostrar_evento_activo(self, evento=None):
        evento = evento or self._obtener_evento_activo()
        if not evento:
            print("No hay un evento activo.")
            print("Siguiente paso: crea uno o busca el evento que quieres preparar.")
            return
        hora = f" · {evento.hora_inicio}" if evento.hora_inicio else ""
        print("\nEVENTO QUE ESTÁS PREPARANDO")
        print(f"{evento.nombre}")
        print(f"{evento.fecha}{hora} · {evento.pax} pax · {evento.estado}")

    def _buscar_o_listar_eventos(self):
        print("\nBUSCAR UN EVENTO")
        print("1. Ver todos los eventos")
        print("2. Buscar por nombre, fecha, cliente o ubicación")
        print("0. Volver")
        op = input("Elige una opción: ").strip()
        if op == "1":
            self._listar_y_seleccionar_eventos()
        elif op == "2":
            self._buscar_y_seleccionar_evento()
        elif op not in {"", "0"}:
            print("Opción no válida. Puedes ver todos los eventos, hacer una búsqueda o volver.")

    def _acciones_avanzadas_evento(self):
        print("\nACCIONES AVANZADAS")
        if not self._obtener_evento_activo():
            print("Para editar, duplicar o eliminar primero debes seleccionar un evento.")
            print("Siguiente paso: vuelve y elige 'Buscar o listar eventos'.")
            return
        print("1. Duplicar evento")
        print("2. Eliminar evento")
        print("0. Volver")
        op = input("Elige una opción: ").strip()
        if op == "1":
            self._duplicar_evento_activo()
        elif op == "2":
            self._eliminar_evento_activo()
        elif op not in {"", "0"}:
            print("Opción no válida. Elige duplicar, eliminar o volver.")

    @staticmethod
    def _imprimir_eventos(eventos):
        if not eventos:
            print("No hay eventos que coincidan con esta consulta.")
            print("Estado actual: no se ha cambiado el evento activo.")
            print("Siguiente paso: prueba otra búsqueda o crea un evento nuevo.")
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
        print(f"Vamos a continuar preparando: {evento['nombre']}.")
        self._continuar_preparacion_evento("seleccion")
        return True

    def _crear_evento_rapido(self):
        print("\nNUEVO EVENTO — DATOS DEL SERVICIO")
        print("Vamos a dejar preparado lo esencial. Puedes completar el resto más tarde.")
        nombre = input("Nombre del evento: ").strip() or "Evento Demo"
        try:
            pax = int(input("Pax: ").strip() or "0")
        except ValueError:
            print("Los pax deben ser un número entero.")
            print("Siguiente paso: vuelve a crear el evento e indica solo el número de comensales.")
            return
        tipo = self._pedir_tipo_evento()
        if tipo is None:
            print("De acuerdo. No se ha creado el evento y podrás retomarlo cuando quieras.")
            return
        fecha_txt = input("Fecha (ej. 22/10/2026, mañana o viernes; vacío=hoy): ").strip()
        print("\nCONTACTO Y LUGAR")
        print("Deja vacío cualquier dato que todavía no tengas.")
        cliente = input("Cliente: ").strip()
        telefono = input("Teléfono: ").strip()
        email = input("Email: ").strip()
        ubicacion = input("Ubicación: ").strip()
        hora_inicio = input("Hora principal HH:MM (opcional): ").strip()
        observaciones = input("Observaciones (opcional): ").strip()
        print("\nESTADO DE PREPARACIÓN")
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
            evento = self.core.eventos.obtener(self.ultimo_evento_id)
            print("\nEVENTO CREADO Y SELECCIONADO")
            self._mostrar_evento_activo(evento)
            self._continuar_tras_crear_evento()
        else:
            print("El evento no se ha creado y no se ha cambiado el evento activo.")
            print("Siguiente paso: revisa los datos indicados y vuelve a intentarlo.")

    def _continuar_tras_crear_evento(self):
        self._mostrar_progreso_evento()
        print("\nPerfecto.\n")
        print("Ya tenemos el evento creado.")
        print("Ahora vamos a preparar los servicios.")
        print("¿Necesitas añadir el primero?")
        print("1. Añadir servicios")
        print("2. Añadir pases")
        print("3. Ver resumen")
        print("4. Abrir ficha")
        print("5. Dejarlo para más tarde")
        op = input("Elige una opción: ").strip()
        if op == "1":
            self._gestionar_servicios_evento_activo()
        elif op == "2":
            self._gestionar_pases_evento_activo()
        elif op == "3":
            self._ver_resumen_rapido_evento_activo()
        elif op == "4":
            self._ver_ficha_evento_activo()
            self._continuar_preparacion_evento("ficha")
        elif op not in {"", "5"}:
            print("No he entendido la opción. El evento queda guardado para continuar después.")

    @staticmethod
    def _pedir_tipo_evento():
        tipos = ("boda", "catering", "evento")
        while True:
            valor = input("¿Qué tipo de evento es? (boda/catering/evento) [evento]: ").strip().lower()
            if not valor:
                return "evento"
            if valor in tipos:
                return valor
            print(f"No reconozco '{valor}' como tipo de evento.")
            print("¿Querías decir?")
            print("1. boda")
            print("2. catering")
            print("3. evento")
            print("0. Cancelar por ahora")
            eleccion = input("Elige una opción: ").strip()
            if eleccion in {"1", "2", "3"}:
                return tipos[int(eleccion) - 1]
            if eleccion in {"", "0"}:
                return None
            print("No he entendido la opción. Vamos a intentarlo otra vez.")

    def _planes_del_evento_activo(self):
        try:
            return [
                plan for plan in self.core.produccion_real.listar_planes()
                if str(plan.get("evento_id") or "") == str(self.ultimo_evento_id)
            ]
        except (AttributeError, TypeError, ValueError):
            return []

    def _estado_preparacion_evento(self):
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        servicios = list(evento.servicios)
        pases = [pase for servicio in servicios for pase in servicio.pases]
        return {
            "evento": evento,
            "servicios": servicios,
            "pases": pases,
            "servicios_sin_pases": [s for s in servicios if not s.pases],
            "planes": self._planes_del_evento_activo(),
        }

    @staticmethod
    def _indicador(completo, activo=False):
        if completo:
            return "✓"
        return "▶" if activo else "□"

    def _mostrar_progreso_evento(self, estado=None):
        estado = estado or self._estado_preparacion_evento()
        servicios_ok = bool(estado["servicios"])
        menu_ok = servicios_ok and not estado["servicios_sin_pases"]
        produccion_ok = bool(estado["planes"])
        completados = 1 + int(servicios_ok) + int(menu_ok) + int(produccion_ok)
        paso = min(completados + 1, 5)
        activos = {
            "servicios": not servicios_ok,
            "menu": servicios_ok and not menu_ok,
            "produccion": menu_ok and not produccion_ok,
            "compras": produccion_ok,
        }
        barra = "██" * completados + "░░" * (5 - completados)
        print("\nPREPARACIÓN DEL EVENTO")
        print(barra)
        print(f"Paso {paso} de 5")
        print("✓ Evento")
        print(f"{self._indicador(servicios_ok, activos['servicios'])} Servicios")
        print(f"{self._indicador(menu_ok, activos['menu'])} Menú")
        print(f"{self._indicador(produccion_ok, activos['produccion'])} Producción")
        print(f"{self._indicador(False, activos['compras'])} Compras")

    def _continuar_preparacion_evento(self, origen="evento"):
        if not self._requiere_evento():
            return
        estado = self._estado_preparacion_evento()
        evento = estado["evento"]
        self._mostrar_progreso_evento(estado)
        if str(evento.estado).lower() == "cancelado":
            print("\nEste evento está cancelado. No voy a proponerte preparar más trabajo.")
            print("1. Ver resumen")
            print("2. Abrir ficha")
            print("0. Dejarlo aquí")
            op = input("Elige una opción: ").strip()
            if op == "1":
                self._ver_resumen_rapido_evento_activo()
            elif op == "2":
                self._ver_ficha_evento_activo()
            return
        if origen == "servicio":
            print("\nPerfecto.\n")
            print("Ya tenemos este servicio preparado.")
            print("Ahora falta preparar sus pases y cerrar el menú.")
            print("¿Qué quieres hacer ahora?")
            print("1. Añadir otro servicio")
            print("2. Preparar el menú del evento")
            print("3. Ver resumen")
            print("4. Revisar o modificar servicios")
            op = input("Elige una opción: ").strip()
            if op in {"1", "4"}:
                self._gestionar_servicios_evento_activo()
            elif op == "2":
                print("\nPerfecto.\nLos servicios del evento ya están preparados.")
                print("Ahora toca preparar el menú del evento.")
                self._gestionar_pases_evento_activo()
            elif op == "3":
                self._ver_resumen_rapido_evento_activo()
            return
        if origen == "pase" and not estado["servicios_sin_pases"]:
            print("\nPerfecto.\n")
            print("El menú del evento ya está preparado.")
            print("El siguiente paso es preparar la producción.")
            print("¿Continuamos?")
            print("1. Sí, preparar la producción")
            print("2. Ver resumen")
            print("3. Revisar el menú")
            print("0. Dejarlo para más tarde")
            op = input("Elige una opción: ").strip()
            if op == "1":
                self._preparar_produccion_evento_activo()
            elif op == "2":
                self._ver_resumen_rapido_evento_activo()
            elif op == "3":
                self._gestionar_pases_evento_activo()
            return
        print("\n¿QUÉ QUIERES HACER AHORA?")
        if not estado["servicios"]:
            fase = "servicios"
            print("FASE SERVICIOS")
            print("El evento todavía no tiene servicios. Vamos a preparar el primero.")
            print("1. Continuar preparando servicios")
            print("2. Ver resumen")
            print("3. Cambiar de fase")
            print("4. Más opciones")
        elif estado["servicios_sin_pases"]:
            fase = "menu"
            print("FASE MENÚ")
            print("Ya tenemos los servicios. Ahora vamos a preparar el menú del evento.")
            print("1. Continuar preparando el menú")
            print("2. Ver resumen")
            print("3. Revisar servicios")
            print("4. Más opciones")
        elif not estado["planes"]:
            fase = "siguiente"
            print("MENÚ PREPARADO")
            print("Perfecto. Ya hemos terminado el menú.")
            print("1. Continuar con el siguiente paso")
            print("2. Ver resumen")
            print("3. Revisar el menú")
            print("4. Más opciones")
        else:
            fase = "produccion"
            print("FASE PRODUCCIÓN")
            print("El evento ya tiene producción preparada.")
            print(f"La producción de {evento.nombre} ya está preparada.")
            print("1. Abrir Producción Viva")
            print("2. Ver resumen")
            print("3. Revisar menú")
            print("4. Más opciones")
        print("0. Salir")
        op = input("Elige una opción: ").strip()
        if op == "1":
            if fase == "servicios":
                self._gestionar_servicios_evento_activo()
            elif fase == "menu":
                self._gestionar_pases_evento_activo()
            elif fase == "siguiente":
                self._preparar_produccion_evento_activo()
            else:
                self._abrir_produccion_viva()
        elif op == "2":
            self._ver_resumen_rapido_evento_activo()
            self._continuar_preparacion_evento("resumen")
        elif op == "3":
            if fase == "servicios": self._cambiar_fase_evento(estado)
            elif fase == "menu": self._gestionar_servicios_evento_activo()
            else: self._gestionar_pases_evento_activo()
        elif op == "4":
            self._mas_opciones_evento(estado)
        elif op not in {"", "0"}:
            print("No he entendido la opción. El evento sigue activo para continuar cuando quieras.")

    def _cambiar_fase_evento(self, estado=None):
        estado = estado or self._estado_preparacion_evento()
        print("\nCAMBIAR DE FASE")
        print("1. Servicios")
        if estado["servicios"]:
            print("2. Menú")
        if estado["planes"]:
            print("3. Producción Viva")
        print("0. Volver")
        op = input("Elige una fase disponible: ").strip()
        if op == "1": self._gestionar_servicios_evento_activo()
        elif op == "2" and estado["servicios"]: self._gestionar_pases_evento_activo()
        elif op == "3" and estado["planes"]: self._abrir_produccion_viva()

    def _mas_opciones_evento(self, estado=None):
        print("\nMÁS OPCIONES DEL EVENTO")
        print("1. Ver cronología")
        print("2. Editar datos del evento")
        print("3. Abrir ficha completa")
        print("4. Acciones avanzadas")
        print("0. Volver")
        op = input("Elige una opción: ").strip()
        if op == "1": self._ver_linea_temporal_evento_activo()
        elif op == "2": self._editar_evento_activo()
        elif op == "3": self._ver_ficha_evento_activo()
        elif op == "4": self._acciones_avanzadas_evento()

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
            print(f"Todavía no hay {etiqueta} para seleccionar.")
            print("Siguiente paso: crea el primero o vuelve a la preparación del evento.")
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
            print("Todavía no has preparado ningún servicio para este evento.")
            print("Siguiente paso: añade el primer servicio, por ejemplo cóctel, comida o cena.")
            return []
        total_pases = 0
        for indice, servicio in enumerate(evento.servicios, start=1):
            total_pases += len(servicio.pases)
            etiqueta_pases = "pase" if len(servicio.pases) == 1 else "pases"
            print(f"{indice}. {servicio.hora_inicio} | {servicio.nombre} | {servicio.duracion_min} min | {len(servicio.pases)} {etiqueta_pases}")
        print(f"Total servicios: {len(evento.servicios)} | Total pases: {total_pases}")
        return evento.servicios

    def _gestionar_servicios_evento_activo(self):
        if not self._requiere_evento():
            return
        while True:
            self._mostrar_progreso_evento()
            print("\nPREPARAR SERVICIOS")
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
                    print("\nPerfecto.\n")
                    print(f"Ya tenemos preparado {servicio.nombre} a las {servicio.hora_inicio}.")
                    self._continuar_evento("servicio")
                    return
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
                    print("Servicio duplicado con pases y platos.")
            else:
                print("Opción no válida.")

    def _seleccionar_servicio_evento_activo(self):
        servicios = self._listar_servicios_evento_activo()
        if len(servicios) == 1:
            return servicios[0]
        return self._seleccionar_por_numero(servicios, "servicios")

    def _listar_pases(self, servicio):
        if not servicio.pases:
            print("No existe ningún pase para este servicio.")
            return []
        for indice, pase in enumerate(servicio.pases, start=1):
            platos_txt = ", ".join(self._nombre_receta(r) for r in pase.recetas) if pase.recetas else "sin platos"
            platos = len([p for p in list(getattr(pase, "platos", []) or []) if isinstance(p, dict)])
            print(f"{indice}. {pase.hora_inicio} | {pase.nombre} | {pase.duracion_min} min | {platos_txt} | platos: {platos}")
        return servicio.pases

    def _catalogo_recetas(self):
        try:
            return self.core.escandallos_inteligente.listar()
        except Exception:
            return []

    def _nombre_receta(self, receta_id):
        for receta in self._catalogo_recetas():
            if str(receta.get("receta_id", "")).lower() == str(receta_id).lower():
                return receta.get("nombre") or receta_id
        return receta_id

    @staticmethod
    def _formatear_valor_busqueda_plato(receta, clave, sufijo=""):
        valor = receta.get(clave)
        if valor in (None, "", 0):
            return None
        if clave == "coste_por_racion":
            try:
                return f"{float(valor):.2f} €/ración"
            except (TypeError, ValueError):
                return None
        if clave == "raciones_base":
            try:
                return f"{int(valor)} raciones"
            except (TypeError, ValueError):
                return None
        return f"{valor}{sufijo}"

    def _imprimir_resultado_busqueda_plato(self, indice, receta):
        print(f"{indice}. {receta.get('nombre')}")
        codigo = receta.get("receta_id")
        if codigo:
            print(f"   {codigo}")
        familia = receta.get("grupo") or receta.get("familia")
        if familia:
            print(f"   {familia}")
        rendimiento = self._formatear_valor_busqueda_plato(receta, "raciones_base")
        if rendimiento:
            print(f"   {rendimiento}")
        coste_racion = self._formatear_valor_busqueda_plato(receta, "coste_por_racion")
        if coste_racion:
            print(f"   {coste_racion}")

    def _buscar_recetas_para_pase(self):
        catalogo = self._catalogo_recetas()
        seleccionadas = []
        if not catalogo:
            texto = input("Platos (escandallos) por ID separados por coma: ").strip()
            return [r.strip() for r in texto.split(",") if r.strip()]
        while True:
            if seleccionadas:
                print("\nPLATOS ACTUALES DEL PASE")
                for receta_id in seleccionadas:
                    print(f"- {self._nombre_receta(receta_id)} ({receta_id})")
            termino = input("Buscar plato (escandallo) por nombre o código (vacío=terminar): ").strip()
            if not termino:
                break
            termino_norm = termino.lower()
            coincidencias = [r for r in catalogo if termino_norm in str(r.get("receta_id", "")).lower() or termino_norm in str(r.get("nombre", "")).lower()]
            if not coincidencias:
                print("No se han encontrado platos. Prueba con otra parte del nombre.")
                continue
            for indice, receta in enumerate(coincidencias[:20], start=1):
                self._imprimir_resultado_busqueda_plato(indice, receta)
            if len(coincidencias) == 1:
                receta_id = coincidencias[0].get("receta_id")
                confirmar = input(f"Añadir plato '{coincidencias[0].get('nombre')}'? (s/n) [s]: ").strip().lower() or "s"
                if confirmar != "s":
                    continue
            else:
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
                print(f"Plato añadido: {self._nombre_receta(receta_id)}")
            else:
                print("Ese plato ya estaba añadido.")
            otra = input("¿Añadir otro plato? (s/n) [n]: ").strip().lower() or "n"
            if otra != "s":
                break
        return seleccionadas

    def _seleccionar_escandallo_para_plato(self):
        catalogo = [r for r in self._catalogo_recetas() if bool(r.get("activo", True))]
        if not catalogo:
            print("No hay escandallos activos disponibles para asociar al plato.")
            return None
        while True:
            termino = input("Buscar plato (escandallo) por nombre o código (vacío=ver lista, 0=cancelar): ").strip()
            if termino == "0":
                return None
            termino_norm = termino.lower()
            if termino_norm:
                coincidencias = [
                    r for r in catalogo
                    if termino_norm in str(r.get("receta_id", "")).lower() or termino_norm in str(r.get("nombre", "")).lower()
                ]
            else:
                coincidencias = catalogo
            if not coincidencias:
                print("No se han encontrado escandallos. Prueba con otro término.")
                continue
            print("\nPLATOS DISPONIBLES")
            for i, receta in enumerate(coincidencias[:30], 1):
                self._imprimir_resultado_busqueda_plato(i, receta)
            sel = input("Selecciona número (0=cancelar): ").strip()
            if sel == "0":
                return None
            try:
                elegido = coincidencias[int(sel)-1]
                return elegido
            except (ValueError, IndexError):
                print("Selección no válida.")

    def _anadir_plato_desde_escandallo_existente(self):
        if not self._requiere_evento():
            return
        servicio = self._seleccionar_servicio_evento_activo()
        if not servicio:
            return
        pases = self._listar_pases(servicio)
        if not pases:
            print("¿Quieres crear uno ahora?")
            print("1. Sí")
            print("0. Cancelar")
            crear = input("Elige una opción: ").strip()
            if crear != "1":
                return
            nombre_pase = input("Nombre del pase [Pase]: ").strip() or "Pase"
            hora_pase = input(f"Hora pase HH:MM [{servicio.hora_inicio or '21:00'}]: ").strip() or (servicio.hora_inicio or "21:00")
            try:
                duracion_pase = int(input("Duración estimada en minutos [35]: ").strip() or "35")
            except ValueError:
                print("La duración debe ser un número entero.")
                return
            try:
                self.core.eventos.agregar_pase(self.ultimo_evento_id, servicio.id, nombre_pase, hora_pase, duracion_pase, [], "")
                servicio = self.core.eventos.obtener_servicio(self.ultimo_evento_id, servicio.id)
                pases = self._listar_pases(servicio)
            except ValueError as exc:
                print(f"No se ha podido crear el pase: {exc}")
                return
        pase = self._seleccionar_por_numero(pases, "pases")
        if not pase:
            return

        esc = self._seleccionar_escandallo_para_plato()
        if not esc:
            return

        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        receta_id = str(esc.get("receta_id") or "").strip().upper()
        print(f"\nUsar las raciones del evento ({evento.pax})?")
        print("1. Sí")
        print("2. No, indicar otra cantidad")
        opcion_raciones = input("Elige una opción: ").strip() or "1"
        if opcion_raciones not in {"1", "2"}:
            print("Opción no válida.")
            return
        usar_pax_evento = opcion_raciones == "1"
        raciones = evento.pax if usar_pax_evento else 0
        if opcion_raciones == "2":
            try:
                raciones = int(input("Raciones para este plato: ").strip() or "0")
            except ValueError:
                print("Raciones no válidas.")
                return

        observaciones = input("Observaciones del plato (opcional): ").strip()
        ajustes = input("Ajustes aprobados (opcional): ").strip()

        coste_preview = None
        try:
            calculo = self.core.escandallos_inteligente.calcular_necesidades_receta(receta_id, int(raciones), origen="Vista previa plato evento")
            coste_preview = {
                "coste_por_racion": calculo.get("coste_por_racion_estimado"),
                "coste_total": calculo.get("coste_total_estimado"),
            }
        except Exception:
            coste_preview = None

        print("\nCONFIRMACIÓN DE PLATO")
        print(f"- Plato: {esc.get('nombre')} ({receta_id})")
        print(f"- Servicio: {servicio.nombre}")
        print(f"- Pase: {pase.nombre}")
        print(f"- Raciones: {raciones}")
        if coste_preview and coste_preview.get("coste_por_racion") not in (None, 0):
            print(f"- Coste por ración: {float(coste_preview['coste_por_racion']):.4f} €")
            print(f"- Coste total: {float(coste_preview['coste_total']):.4f} €")
        else:
            print("- Coste: no disponible (faltan precios o cálculo del escandallo).")
        if observaciones:
            print(f"- Observaciones: {observaciones}")
        if ajustes:
            print(f"- Ajustes aprobados: {ajustes}")

        confirmar = input("¿Guardar este plato en el pase? (s/n): ").strip().lower()
        if confirmar not in {"s", "si", "sí"}:
            print("Operación cancelada.")
            return

        try:
            self.core.orquestador.resolver(SolicitudHostAI("agregar_plato_evento", {
                "evento_id": self.ultimo_evento_id,
                "servicio_id": servicio.id,
                "pase_id": pase.id,
                "escandallo_id": receta_id,
                "usar_pax_evento": bool(usar_pax_evento),
                "raciones": int(raciones),
                "observaciones": observaciones,
                "ajustes_aprobados": ajustes,
            }))
            print("\nPlato añadido correctamente.")
            print("")
            print(f"Servicio: {servicio.nombre}")
            print(f"Pase: {pase.nombre}")
            print(f"Plato: {esc.get('nombre')} ({receta_id})")
            print(f"Raciones: {raciones}")
        except Exception as exc:
            print(f"No se pudo asociar el plato: {exc}")

    def _menu_anadir_plato_evento_activo(self):
        while True:
            print("\nAÑADIR PLATO")
            print("1. Buscar en escandallos existentes")
            print("2. Importar desde archivo — Próximamente")
            print("3. Crear manualmente — Próximamente")
            print("0. Volver")
            op = input("Elige una opción: ").strip()
            if op == "0":
                return
            if op == "1":
                self._anadir_plato_desde_escandallo_existente()
                return
            if op in {"2", "3"}:
                print("Esta opción estará disponible en un sprint posterior.")
                continue
            print("Opción no válida.")

    def _gestionar_pases_evento_activo(self):
        if not self._requiere_evento():
            return
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        if not evento.servicios:
            print("Todavía no puedes preparar pases porque el evento no tiene servicios.")
            print("Siguiente paso: entra en 'Preparar servicios' y añade el primero.")
            return
        while True:
            self._mostrar_progreso_evento()
            print("\nPREPARAR EL MENÚ DEL EVENTO")
            print("1. Añadir pase")
            print("2. Listar pases")
            print("3. Editar pase")
            print("4. Eliminar pase")
            print("5. Duplicar pase")
            print("6. Añadir plato")
            print("0. Volver")
            op = input("Elige una opción: ").strip()
            if op == "0":
                return
            if op == "6":
                self._menu_anadir_plato_evento_activo()
                continue
            servicio = self._seleccionar_servicio_evento_activo()
            if not servicio:
                continue
            print(f"Servicio seleccionado: {servicio.nombre} ({servicio.hora_inicio})")
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
                    print("\nPerfecto.\n")
                    print(f"Ya tenemos preparado {nombre} con {len(recetas)} platos.")
                    self._continuar_evento("pase")
                    return
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
                    cambiar_recetas = input("¿Cambiar platos del pase? (s/n): ").strip().lower()
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
                    print("Pase duplicado con sus platos.")
            else:
                print("Opción no válida.")

    def _continuar_evento(self, origen):
        self._continuar_preparacion_evento(origen)

    def _ver_linea_temporal_evento_activo(self):
        if not self._requiere_evento():
            return
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        print("\n" + "=" * 62)
        print(f"LÍNEA TEMPORAL — {evento.nombre} | {evento.fecha}")
        print("=" * 62)
        if not evento.servicios:
            print("Todavía no hay servicios ni pases programados.")
            print("Siguiente paso: prepara el primer servicio para construir la cronología.")
        total_pases = 0
        total_recetas = 0
        servicios = sorted(evento.servicios, key=lambda s: self.core.eventos._minutos(s.hora_inicio))
        for servicio in servicios:
            print(f"{servicio.hora_inicio}  SERVICIO  {servicio.nombre} ({servicio.duracion_min} min)")
            pases = sorted(servicio.pases, key=lambda p: self.core.eventos._minutos(p.hora_inicio))
            if not pases:
                print("          Falta preparar los pases de este servicio")
            for pase in pases:
                total_pases += 1
                total_recetas += len(pase.recetas)
                print(f"  {pase.hora_inicio}  PASE      {pase.nombre} ({pase.duracion_min} min)")
                if pase.recetas:
                    nombres = [self._nombre_receta(receta_id) for receta_id in pase.recetas]
                    print("          Recetas: " + ", ".join(nombres))
                else:
                    print("          Recetas: sin recetas")
                platos = [p for p in list(getattr(pase, "platos", []) or []) if isinstance(p, dict)]
                if platos:
                    print("          Platos:")
                    for plato in platos:
                        rid = str(plato.get("escandallo_id") or "")
                        nombre = self._nombre_receta(rid) if rid else str(plato.get("nombre") or "Plato")
                        coste_pr = plato.get("coste_por_racion")
                        coste_total = plato.get("coste_total")
                        if coste_pr is not None and coste_total is not None:
                            print(f"          - {nombre} | {plato.get('raciones', 0)} raciones | {float(coste_pr):.4f} €/ración | {float(coste_total):.4f} €")
                        else:
                            print(f"          - {nombre} | {plato.get('raciones', 0)} raciones | coste no disponible")
                if pase.notas:
                    print(f"          Notas: {pase.notas}")
            print("-" * 62)
        print(f"Total servicios: {len(evento.servicios)} | Pases: {total_pases} | Recetas: {total_recetas}")
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
        print(f"Platos: {sum(len(p.recetas) for s in evento.servicios for p in s.pases)}")
        print("=" * 62)

    def _ver_produccion_evento_activo(self, preguntar=False):
        if not self._requiere_evento():
            return
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        planes = self._planes_del_evento_activo()
        print(f"\nPRODUCCIÓN RELACIONADA — {evento.nombre}")
        if not planes:
            print("Estado actual: la producción está pendiente de generar.")
            print("Siguiente paso: prepara el plan de producción del evento.")
            if not preguntar:
                return
            respuesta = input("¿Quieres prepararlo ahora? (s/n) [s]: ").strip().lower() or "s"
            if respuesta in {"s", "si", "sí"}:
                self._preparar_produccion_evento_activo()
            return
        for indice, plan in enumerate(planes, 1):
            print(f"{indice}. {plan.get('nombre') or evento.nombre} · {plan.get('estado') or 'sin estado'}")
        print("Siguiente paso: abre Producción Viva para empezar a trabajar.")
        if not preguntar:
            return
        respuesta = input("¿Quieres abrir Producción Viva? (s/n) [s]: ").strip().lower() or "s"
        if respuesta in {"s", "si", "sí"}:
            self._abrir_produccion_viva()

    def _preparar_produccion_evento_activo(self):
        if not self._requiere_evento():
            return None
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        print(f"\nVAMOS A PREPARAR LA PRODUCCIÓN DE {evento.nombre.upper()}")
        hora = input("¿A qué hora empieza cocina? [08:00]: ").strip() or "08:00"
        try:
            equipo = int(input("¿Cuántas personas hay en cocina? [2]: ").strip() or "2")
        except ValueError:
            print("Indica el equipo con un número entero. No se ha creado producción.")
            print("Siguiente paso: vuelve a preparar la producción cuando tengas ese dato.")
            return None
        r = self.core.orquestador.resolver(SolicitudHostAI(
            "planificar_produccion_real_evento",
            {"evento_id": self.ultimo_evento_id, "hora_inicio": hora, "equipo_cocina": equipo},
        ))
        print(r.mensaje)
        if not r.ok:
            print("La producción no se ha creado. El evento conserva sus servicios y pases.")
            print("Siguiente paso: revisa el aviso y vuelve a intentarlo.")
            return None
        plan_id = r.datos.get("id")
        if plan_id:
            self.ultimo_plan_produccion_id = plan_id
        print("\nPRODUCCIÓN PREPARADA")
        print(f"Plan activo: {r.datos.get('evento') or evento.nombre} | {plan_id or '-'}")
        self._mostrar_progreso_evento()
        print("\nPerfecto.\n")
        print("La producción ya está preparada.")
        print("¿Quieres abrir Producción Viva ahora mismo?")
        print("1. Sí")
        print("2. Ver resumen")
        print("3. Volver al evento")
        abrir = input("Elige una opción: ").strip() or "1"
        if abrir.lower() in {"1", "s", "si", "sí"}:
            self._abrir_produccion_viva()
        elif abrir == "2":
            self._ver_resumen_rapido_evento_activo()
        elif abrir == "3":
            self._continuar_preparacion_evento("produccion")
        else:
            print("El plan queda preparado. Puedes abrirlo después desde Producción Viva.")
        return r.datos

    def _abrir_produccion_viva(self):
        from APP.consola_produccion_guiada_piloto_13 import ConsolaProduccionGuiadaPiloto13

        print("\nABRIENDO PRODUCCIÓN VIVA")
        ConsolaProduccionGuiadaPiloto13(self.core, self._menu_produccion_real).ejecutar()

    def _compras_del_evento_activo(self):
        try:
            necesidades = self.core.compras.listar_necesidades(solo_pendientes=False)
        except (AttributeError, TypeError, ValueError):
            return []
        resultado = []
        for necesidad in necesidades:
            datos = necesidad if isinstance(necesidad, dict) else getattr(necesidad, "to_dict", lambda: {})()
            if str(datos.get("evento_id") or "") == str(self.ultimo_evento_id):
                resultado.append(datos)
        return resultado

    def _ver_resumen_rapido_evento_activo(self):
        if not self._requiere_evento():
            return
        estado = self._estado_preparacion_evento()
        evento = estado["evento"]
        servicios_ok = bool(estado["servicios"])
        menu_ok = servicios_ok and not estado["servicios_sin_pases"]
        produccion_ok = bool(estado["planes"])
        compras = self._compras_del_evento_activo()
        cancelado = str(evento.estado).lower() == "cancelado"
        print("\nRESUMEN RÁPIDO")
        print(f"{'!' if cancelado else '✓'} Evento {'cancelado' if cancelado else 'creado'} — {evento.nombre}")
        print(f"{'✓' if servicios_ok else '□'} Servicios {'preparados' if servicios_ok else 'pendientes'}")
        print(f"{'✓' if menu_ok else '□'} Menú {'preparado' if menu_ok else 'pendiente'}")
        print(f"{'✓' if produccion_ok else '□'} Producción {'preparada' if produccion_ok else 'pendiente'}")
        print(f"{'✓' if compras else '□'} Compras {'relacionadas' if compras else 'pendientes de comprobar'}")
        if cancelado:
            general = "Evento cancelado"
        elif produccion_ok:
            general = "Preparación avanzada; quedan las compras por comprobar"
        elif menu_ok:
            general = "Menú preparado; falta preparar producción"
        elif servicios_ok:
            general = "Servicios preparados; falta cerrar el menú"
        else:
            general = "Evento creado; faltan los servicios"
        print(f"Estado general: {general}")
        print("\n1. Ver resumen completo")
        print("0. Continuar preparando el evento")
        op = input("Elige una opción: ").strip()
        if op == "1":
            self._ver_resumen_ejecutivo_evento_activo()

    def _ver_resumen_ejecutivo_evento_activo(self):
        if not self._requiere_evento():
            return
        resumen = self.core.eventos.resumen_ejecutivo(self.ultimo_evento_id)
        evento = self.core.eventos.obtener(self.ultimo_evento_id)
        totales = resumen["totales"]
        print("\n" + "=" * 62)
        print(f"QUÉ FALTA Y QUÉ ESTÁ LISTO — {evento.nombre}")
        print("=" * 62)
        print(f"Fecha y hora: {evento.fecha} {evento.hora_inicio or ''}".rstrip())
        print(f"Estado: {evento.estado}")
        print(f"Cliente: {evento.cliente or '-'}")
        print(f"Ubicación: {evento.ubicacion or '-'}")
        print(f"Pax: {evento.pax}")
        print("-" * 62)
        print("\nQUÉ FALTA")
        if resumen["avisos"]:
            for aviso in resumen["avisos"]:
                print(f"- {aviso}")
        else:
            print("- Servicios, pases y platos están preparados.")
        print("\nQUÉ ESTÁ LISTO")
        print(f"- {totales['servicios']} servicios preparados")
        print(f"- {totales['pases']} pases preparados")
        print(f"- {totales['recetas']} platos añadidos ({totales['recetas_unicas']} únicos)")
        print("\nSERVICIOS Y PASES")
        if not evento.servicios:
            print("- Todavía no hay servicios preparados.")
        for servicio in evento.servicios:
            print(f"- {servicio.hora_inicio} · {servicio.nombre}")
            for pase in servicio.pases:
                recetas = ", ".join(self._nombre_receta(r) for r in pase.recetas) or "sin platos"
                print(f"  {pase.hora_inicio} · {pase.nombre} · {recetas}")
                platos = [p for p in list(getattr(pase, "platos", []) or []) if isinstance(p, dict)]
                for plato in platos:
                    rid = str(plato.get("escandallo_id") or "")
                    nombre = self._nombre_receta(rid) if rid else str(plato.get("nombre") or "Plato")
                    coste_pr = plato.get("coste_por_racion")
                    coste_total = plato.get("coste_total")
                    if coste_pr is not None and coste_total is not None:
                        print(f"    Plato: {nombre} · {plato.get('raciones', 0)} raciones · {float(coste_pr):.4f} €/ración · {float(coste_total):.4f} €")
                    else:
                        print(f"    Plato: {nombre} · {plato.get('raciones', 0)} raciones · coste no disponible")
        planes = self._planes_del_evento_activo()
        print("\nPRODUCCIÓN QUE DEPENDE DEL EVENTO")
        if planes:
            for plan in planes:
                print(f"- {plan.get('nombre') or evento.nombre} · {plan.get('estado') or 'sin estado'}")
        else:
            print("- Pendiente de generar desde Producción.")
            print("  Siguiente paso: completa el menú antes de generar el plan.")
        compras = self._compras_del_evento_activo()
        print("\nCOMPRAS PENDIENTES / RELACIONADAS")
        if compras:
            for compra in compras:
                print(f"- {compra.get('nombre') or compra.get('articulo') or compra.get('id') or 'Necesidad de compra'} · {compra.get('estado') or 'sin estado'}")
        else:
            print("- No hay compras relacionadas disponibles en el evento.")
        print("\nCRONOLOGÍA")
        if evento.servicios:
            for servicio in evento.servicios:
                print(f"- {servicio.hora_inicio} · {servicio.nombre}")
                for pase in servicio.pases:
                    print(f"  {pase.hora_inicio} · {pase.nombre}")
        else:
            print("- Pendiente de construir cuando se añadan servicios.")
        print("\nOBSERVACIONES")
        print(evento.observaciones or "Sin observaciones añadidas.")
        print("\nRIESGOS")
        if resumen["avisos"]:
            for aviso in resumen["avisos"]:
                print(f"- {aviso}")
        else:
            print("- No hay riesgos estructurales señalados por el evento.")
        print("\nSIGUIENTE ACCIÓN RECOMENDADA")
        if resumen["avisos"]:
            print("Resuelve el primer punto de 'Qué falta'.")
        else:
            print("Revisa el menú y prepara la producción relacionada.")
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
        texto = input("¿Qué artículo quieres consultar? (Enter=ver todo): ").strip().lower()
        ubicacion = familia = ""
        estado = "todos"
        # Si el usuario ya ha escrito un artículo, se consulta directamente.
        # Los filtros avanzados solo aparecen al pedir el listado completo.
        if not texto:
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
            print("No hay existencias que coincidan con la búsqueda.")
            if texto:
                sugerencias = self._buscar_catalogo_articulos(texto)
                if sugerencias:
                    print("Artículos parecidos del catálogo (actualmente sin stock):")
                    for art in sugerencias[:5]:
                        print(f"- {art.get('nombre', '-')} | {art.get('codigo', '-')} | {art.get('proveedor') or 'sin proveedor'}")
                print("Prueba con parte del nombre o pulsa Enter para usar filtros avanzados.")
            return
        for item in sorted(items, key=lambda x: str(x.get("nombre", "")).lower()):
            lotes_positivos = [l for l in item.get("lotes", []) if float(l.get("cantidad", 0)) > 0]
            ubicaciones = sorted({l.get("ubicacion") or "sin ubicación" for l in lotes_positivos})
            valor = sum(float(l.get("cantidad", 0)) * float(l.get("coste_unitario") or 0) for l in lotes_positivos)
            print(f"- {item['nombre']}: {item['cantidad']} {item['unidad']} | {', '.join(ubicaciones)} | {len(lotes_positivos)} lote(s) | {valor:.2f} €")

    def _gestionar_lotes_stock(self):
        texto = input("Buscar lote por artículo, código o ID (vacío=todos): ").strip()
        ubicacion = input("Filtrar ubicación (opcional): ").strip()
        lotes = self.core.stock.lotes_listado(texto=texto, ubicacion=ubicacion)
        if not lotes:
            print("No se encontraron lotes.")
            return
        print("\nLOTES — orden FIFO (consumir primero el más antiguo)")
        for i, lote in enumerate(lotes, 1):
            coste = float(lote.get("coste_unitario") or 0)
            valor = float(lote.get("cantidad") or 0) * coste
            fifo = " | CONSUMIR PRIMERO" if i == 1 else ""
            print(
                f"{i}. {lote['nombre']} | {lote['cantidad']} {lote['unidad']} | "
                f"entrada: {lote.get('fecha_entrada') or '-'} | {lote.get('ubicacion') or 'sin ubicación'} | "
                f"cad: {lote.get('caducidad') or '-'} | {coste:.2f} €/u | {valor:.2f} € | {lote['id']}{fifo}"
            )
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
        print(
            f"Sin precio: {resumen.get('lotes_sin_precio', 0)} | "
            f"Sin ubicación: {resumen.get('lotes_sin_ubicacion', 0)} | "
            f"Stock bajo: {resumen.get('articulos_bajo_minimo', 0)}"
        )
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
            propuestas = self.core.compras.listar_propuestas_compra(solo_pendientes=True)
            proveedores = self.core.compras.listar_proveedores(incluir_inactivos=False)
            compras = self.core.compras.listar_historial_compras()
            print(
                f"\nCENTRO DE COMPRAS INTELIGENTES — {len(propuestas)} propuesta(s) pendiente(s) | "
                f"{len(proveedores)} proveedor(es) activo(s) | {len(compras)} compra(s) registrada(s)"
            )
            print("1. Compras inteligentes")
            print("2. Generar compra manual")
            print("3. Proveedores")
            print("4. Historial de compras")
            print("5. Proveedores habituales por producto")
            print("6. Propuestas agrupadas por proveedor")
            print("0. Volver")
            op = input("Elige una opción: ").strip()

            if op == "0":
                return
            if op == "1":
                self._menu_compras_inteligentes_r41()
            elif op == "2":
                self._registrar_compra_manual_r41()
            elif op == "3":
                self._menu_proveedores_r41()
            elif op == "4":
                self._mostrar_historial_compras_r41()
            elif op == "5":
                self._menu_proveedores_habituales_producto_r42()
            elif op == "6":
                self._ver_propuestas_agrupadas_proveedor_r42()
            else:
                print("Opción no válida.")

    def _menu_compras_inteligentes_r41(self):
        while True:
            pendientes = self.core.compras.listar_propuestas_compra(solo_pendientes=True)
            print(f"\nCOMPRAS INTELIGENTES — {len(pendientes)} propuesta(s) pendiente(s)")
            print("1. Generar propuestas inteligentes")
            print("2. Ver propuestas pendientes")
            print("3. Confirmar propuesta")
            print("4. Cancelar propuesta")
            print("5. Ver recomendación de proveedor")
            print("6. Comparar proveedores para una propuesta")
            print("0. Volver")
            op = input("Elige una opción: ").strip()

            if op == "0":
                return
            if op == "1":
                r = self.core.orquestador.resolver(SolicitudHostAI("generar_propuesta_inteligente_compra", {}))
                print(r.mensaje)
                for p in r.datos.get("propuestas", [])[:20]:
                    print(
                        f"- {p.get('producto', '-')}: comprar {p.get('comprar', 0)} {p.get('unidad', 'u')} "
                        f"(nec {p.get('necesario', 0)} / disp {p.get('disponible', 0)}) [{p.get('prioridad', 'Normal')}]"
                    )
            elif op == "2":
                self._imprimir_propuestas_compra_r41(self.core.compras.listar_propuestas_compra(solo_pendientes=True))
            elif op == "3":
                self._confirmar_propuesta_compra_r41()
            elif op == "4":
                self._cancelar_propuesta_compra_r41()
            elif op == "5":
                self._ver_recomendacion_proveedor_propuesta_r42()
            elif op == "6":
                self._comparar_proveedores_propuesta_r43()
            else:
                print("Opción no válida.")

    def _imprimir_propuestas_compra_r41(self, propuestas):
        if not propuestas:
            print("No hay propuestas pendientes.")
            return
        for i, p in enumerate(propuestas, 1):
            proveedor = p.get("proveedor_sugerido", "") or "Sin recomendación"
            motivo = p.get("motivo_proveedor_sugerido", "")
            print(
                f"{i}. [{p.get('estado', 'pendiente').upper()}] {p.get('producto', '-')} | "
                f"comprar {p.get('comprar', 0)} {p.get('unidad', 'u')} | "
                f"prioridad {p.get('prioridad', 'Normal')}"
            )
            print(f"   Origen: {p.get('origen', 'Host AI')}")
            print(f"   Proveedor recomendado: {proveedor}" + (f" | Motivo: {motivo}" if motivo else ""))

    def _seleccionar_propuesta_compra_r41(self):
        propuestas = self.core.compras.listar_propuestas_compra(solo_pendientes=True)
        if not propuestas:
            print("No hay propuestas pendientes.")
            return None
        self._imprimir_propuestas_compra_r41(propuestas)
        elegido = input("Selecciona propuesta (número): ").strip()
        if elegido.isdigit() and 1 <= int(elegido) <= len(propuestas):
            return propuestas[int(elegido) - 1]
        print("Selección no válida.")
        return None

    def _seleccionar_proveedor_activo_r42(self, texto=""):
        proveedores = self.core.compras.listar_proveedores(incluir_inactivos=False, texto=texto)
        if not proveedores:
            print("No hay proveedores activos para ese filtro.")
            return None
        print("\nPROVEEDORES ACTIVOS")
        for i, p in enumerate(proveedores, 1):
            print(f"{i}. {p.get('nombre', '-')}")
        elegido = input("Selecciona proveedor (número): ").strip()
        if elegido.isdigit() and 1 <= int(elegido) <= len(proveedores):
            return proveedores[int(elegido) - 1]
        print("Selección no válida.")
        return None

    def _crear_proveedor_manual_rapido_r42(self):
        nombre = input("Nombre proveedor: ").strip()
        if not nombre:
            print("Creación cancelada.")
            return ""
        r = self.core.orquestador.resolver(
            SolicitudHostAI(
                "crear_proveedor_manual",
                {
                    "nombre": nombre,
                    "cif": input("CIF (opcional): ").strip(),
                    "telefono": input("Teléfono (opcional): ").strip(),
                    "email": input("Email (opcional): ").strip(),
                    "direccion": input("Dirección (opcional): ").strip(),
                    "comercial": input("Comercial (opcional): ").strip(),
                    "observaciones": input("Observaciones (opcional): ").strip(),
                },
            )
        )
        print(r.mensaje)
        return r.datos.get("proveedor", {}).get("nombre", "") if r.ok else ""

    def _resolver_proveedor_compra_r42(self, producto, recomendado="", familia=""):
        print("\nPROVEEDOR RECOMENDADO")
        print(f"Producto: {producto}")
        print(f"Proveedor recomendado: {recomendado or 'Sin recomendación'}")
        print("1. Confirmar recomendado")
        print("2. Elegir otro proveedor")
        print("3. Crear proveedor manualmente")
        print("4. Continuar sin proveedor")
        print("0. Cancelar")
        while True:
            op = input("Opción: ").strip()
            if op == "1":
                if recomendado:
                    return recomendado
                print("No hay proveedor recomendado. Elige otra opción.")
                continue
            if op == "2":
                texto = input("Buscar proveedor por texto: ").strip()
                seleccionado = self._seleccionar_proveedor_activo_r42(texto)
                if seleccionado:
                    return seleccionado.get("nombre", "")
                continue
            if op == "3":
                creado = self._crear_proveedor_manual_rapido_r42()
                if creado:
                    return creado
                continue
            if op == "4":
                return ""
            if op == "0":
                return None
            print("Opción no válida.")

    def _confirmar_propuesta_compra_r41(self, propuesta=None):
        propuesta = propuesta or self._seleccionar_propuesta_compra_r41()
        if not propuesta:
            return
        rec = self.core.orquestador.resolver(
            SolicitudHostAI("recomendacion_proveedor_propuesta_compra", {"propuesta_id": propuesta["id"]})
        )
        recomendado = rec.datos.get("proveedor_recomendado", "") if rec.ok else propuesta.get("proveedor_sugerido", "")
        if recomendado == "Sin recomendación":
            recomendado = ""
        if rec.ok:
            print(f"Motivo: {rec.datos.get('motivo', 'Sin historial suficiente.')}")
        proveedor = self._resolver_proveedor_compra_r42(propuesta.get("producto", ""), recomendado)
        if proveedor is None:
            print("Confirmación cancelada.")
            return
        observaciones = input("Observaciones (opcional): ").strip()
        r = self.core.orquestador.resolver(
            SolicitudHostAI(
                "confirmar_propuesta_compra",
                {"propuesta_id": propuesta["id"], "proveedor": proveedor, "observaciones": observaciones},
            )
        )
        print(r.mensaje)
        if r.ok:
            compra = r.datos.get("compra", {})
            print(f"Compra registrada: {compra.get('id', '-')} | {compra.get('producto', '-')} | {compra.get('cantidad', 0)} {compra.get('unidad', 'u')}")

    def _cancelar_propuesta_compra_r41(self):
        propuesta = self._seleccionar_propuesta_compra_r41()
        if not propuesta:
            return
        if input("¿Cancelar propuesta? (s/n): ").strip().lower() not in {"s", "si", "sí", "y", "yes"}:
            print("Cancelación abortada.")
            return
        r = self.core.orquestador.resolver(SolicitudHostAI("cancelar_propuesta_compra", {"propuesta_id": propuesta["id"]}))
        print(r.mensaje)

    def _registrar_compra_manual_r41(self):
        producto = input("Producto: ").strip()
        if not producto:
            print("El producto es obligatorio.")
            return
        try:
            cantidad = float((input("Cantidad: ").strip() or "0").replace(",", "."))
        except ValueError:
            print("Cantidad no válida.")
            return
        if cantidad <= 0:
            print("La cantidad debe ser mayor que cero.")
            return
        unidad = input("Unidad [u]: ").strip() or "u"
        rec = self.core.orquestador.resolver(
            SolicitudHostAI("recomendar_proveedor_compra", {"producto": producto})
        )
        recomendado = rec.datos.get("proveedor_nombre", "") if rec.ok else ""
        if rec.ok:
            print(f"Motivo recomendación: {rec.datos.get('motivo', 'Sin historial suficiente.')}")
        proveedor = self._resolver_proveedor_compra_r42(producto, recomendado)
        if proveedor is None:
            print("Compra cancelada.")
            return
        prioridad = input("Prioridad [Normal]: ").strip() or "Normal"
        observaciones = input("Observaciones (opcional): ").strip()
        r = self.core.orquestador.resolver(
            SolicitudHostAI(
                "registrar_compra_manual",
                {
                    "producto": producto,
                    "cantidad": cantidad,
                    "unidad": unidad,
                    "proveedor": proveedor,
                    "prioridad": prioridad,
                    "observaciones": observaciones,
                },
            )
        )
        print(r.mensaje)

    def _ver_recomendacion_proveedor_propuesta_r42(self):
        propuesta = self._seleccionar_propuesta_compra_r41()
        if not propuesta:
            return
        r = self.core.orquestador.resolver(
            SolicitudHostAI("recomendacion_proveedor_propuesta_compra", {"propuesta_id": propuesta["id"]})
        )
        if not r.ok:
            print(r.mensaje)
            return
        print("\nRECOMENDACIÓN DE PROVEEDOR")
        print(f"Producto: {r.datos.get('producto', propuesta.get('producto', '-'))}")
        print(f"Proveedor recomendado: {r.datos.get('proveedor_recomendado', 'Sin recomendación')}")
        print(f"Motivo: {r.datos.get('motivo', 'Sin historial suficiente.')}")

    def _menu_proveedores_habituales_producto_r42(self):
        producto = input("Producto a gestionar: ").strip()
        if not producto:
            print("Producto obligatorio.")
            return
        while True:
            r = self.core.orquestador.resolver(
                SolicitudHostAI("listar_proveedores_producto_compra", {"producto": producto, "solo_activos": False})
            )
            asociaciones = r.datos.get("asociaciones", []) if r.ok else []
            print("\nPROVEEDORES HABITUALES DEL PRODUCTO")
            print(f"Producto: {producto}")
            if not asociaciones:
                print("Sin asociaciones registradas.")
            else:
                for i, a in enumerate(asociaciones, 1):
                    etiqueta = "Preferente" if a.get("preferente") else "Secundario"
                    estado = "Activo" if a.get("activo", True) else "Inactivo"
                    print(f"{i}. {a.get('proveedor_nombre', '-')} — {etiqueta} — {a.get('veces_usado', 0)} compras — {estado}")
            print("1. Marcar preferente")
            print("2. Añadir proveedor")
            print("3. Desactivar asociación")
            print("4. Editar condiciones comerciales de una asociación")
            print("5. Comparar proveedores para este producto")
            print("0. Volver")
            op = input("Opción: ").strip()
            if op == "0":
                return
            if op == "1":
                if not asociaciones:
                    print("No hay asociaciones para marcar preferente.")
                    continue
                sel = input("Selecciona proveedor (número): ").strip()
                if not sel.isdigit() or not (1 <= int(sel) <= len(asociaciones)):
                    print("Selección no válida.")
                    continue
                elegido = asociaciones[int(sel) - 1]
                rr = self.core.orquestador.resolver(
                    SolicitudHostAI(
                        "marcar_proveedor_preferente_compra",
                        {"producto": producto, "proveedor_id": elegido.get("proveedor_id", "")},
                    )
                )
                print(rr.mensaje)
                continue
            if op == "2":
                texto = input("Buscar proveedor (texto): ").strip()
                prov = self._seleccionar_proveedor_activo_r42(texto)
                if not prov:
                    continue
                rr = self.core.orquestador.resolver(
                    SolicitudHostAI(
                        "asociar_producto_proveedor_compra",
                        {"proveedor_id": prov.get("id", ""), "producto": producto},
                    )
                )
                print(rr.mensaje)
                continue
            if op == "3":
                if not asociaciones:
                    print("No hay asociaciones para desactivar.")
                    continue
                sel = input("Selecciona asociación (número): ").strip()
                if not sel.isdigit() or not (1 <= int(sel) <= len(asociaciones)):
                    print("Selección no válida.")
                    continue
                elegido = asociaciones[int(sel) - 1]
                rr = self.core.orquestador.resolver(
                    SolicitudHostAI(
                        "desactivar_asociacion_producto_proveedor_compra",
                        {"asociacion_id": elegido.get("id", "")},
                    )
                )
                print(rr.mensaje)
                continue
            if op == "4":
                if not asociaciones:
                    print("No hay asociaciones para editar.")
                    continue
                self._editar_condiciones_asociacion_producto_r43(producto, asociaciones)
                continue
            if op == "5":
                self._comparar_proveedores_producto_r43(producto)
                continue
            print("Opción no válida.")

    def _ver_propuestas_agrupadas_proveedor_r42(self):
        r = self.core.orquestador.resolver(SolicitudHostAI("agrupar_propuestas_por_proveedor_compra", {}))
        if not r.ok:
            print(r.mensaje)
            return
        grupos = r.datos.get("grupos", [])
        print("\nPROPUESTAS AGRUPADAS POR PROVEEDOR")
        if not grupos:
            print("No hay propuestas pendientes.")
            return
        for i, grupo in enumerate(grupos, 1):
            print(f"\n{i}. {grupo.get('proveedor', 'Sin proveedor recomendado')}")
            for item in grupo.get("propuestas", []):
                print(f"- {item.get('producto', '-')} — {item.get('cantidad', 0)} {item.get('unidad', 'u')}")

        print("\nOpciones")
        print("1. Revisar y confirmar individualmente por proveedor")
        print("0. Volver")
        op = input("Opción: ").strip()
        if op != "1":
            return
        sel = input("Selecciona proveedor (número): ").strip()
        if not sel.isdigit() or not (1 <= int(sel) <= len(grupos)):
            print("Selección no válida.")
            return
        grupo = grupos[int(sel) - 1]
        propuestas = grupo.get("propuestas", [])
        if not propuestas:
            print("No hay propuestas en este grupo.")
            return
        while True:
            print(f"\nProveedor: {grupo.get('proveedor', '-')}")
            for i, item in enumerate(propuestas, 1):
                print(f"{i}. {item.get('producto', '-')} — {item.get('cantidad', 0)} {item.get('unidad', 'u')}")
            print("0. Volver")
            ele = input("Selecciona propuesta a confirmar (número): ").strip()
            if ele == "0":
                return
            if not ele.isdigit() or not (1 <= int(ele) <= len(propuestas)):
                print("Selección no válida.")
                continue
            propuesta_id = propuestas[int(ele) - 1].get("id", "")
            propuesta_sel = next((p for p in self.core.compras.listar_propuestas_compra(solo_pendientes=True) if p.get("id") == propuesta_id), None)
            if not propuesta_sel:
                print("La propuesta ya no está pendiente.")
                return
            self._confirmar_propuesta_compra_r41(propuesta_sel)
            r = self.core.orquestador.resolver(SolicitudHostAI("agrupar_propuestas_por_proveedor_compra", {}))
            grupos = r.datos.get("grupos", []) if r.ok else []
            if not grupos:
                return
            grupo = next((g for g in grupos if g.get("proveedor") == grupo.get("proveedor")), {"propuestas": []})
            propuestas = grupo.get("propuestas", [])
            if not propuestas:
                print("No quedan propuestas pendientes en este proveedor.")
                return

    def _menu_proveedores_r41(self):
        while True:
            print("\nPROVEEDORES")
            print("1. Listar proveedores")
            print("2. Crear proveedor")
            print("3. Editar proveedor")
            print("4. Desactivar proveedor")
            print("5. Asociar producto habitual")
            print("6. Preparar onboarding detectado (sin OCR)")
            print("7. Editar condiciones comerciales")
            print("0. Volver")
            op = input("Elige una opción: ").strip()
            if op == "0":
                return
            if op == "1":
                self._listar_proveedores_r41()
            elif op == "2":
                self._crear_proveedor_r41()
            elif op == "3":
                self._editar_proveedor_r41()
            elif op == "4":
                self._desactivar_proveedor_r41()
            elif op == "5":
                self._asociar_producto_proveedor_r41()
            elif op == "6":
                self._onboarding_proveedor_detectado_r41()
            elif op == "7":
                self._editar_condiciones_comerciales_proveedor_r43()
            else:
                print("Opción no válida.")

    @staticmethod
    def _parse_float_opcional(texto):
        valor = str(texto or "").strip()
        if not valor:
            return None
        return float(valor.replace(",", "."))

    @staticmethod
    def _parse_int_opcional(texto):
        valor = str(texto or "").strip()
        if not valor:
            return None
        return int(valor)

    def _comparar_proveedores_propuesta_r43(self):
        propuesta = self._seleccionar_propuesta_compra_r41()
        if not propuesta:
            return
        r = self.core.orquestador.resolver(
            SolicitudHostAI("comparar_proveedores_propuesta_compra", {"propuesta_id": propuesta["id"]})
        )
        if not r.ok:
            print(r.mensaje)
            return
        print("\nCOMPARATIVA DE PROVEEDORES (PROPUESTA)")
        print(f"Producto: {r.datos.get('producto', propuesta.get('producto', '-'))}")
        print(f"Proveedor recomendado: {r.datos.get('proveedor_recomendado', 'Sin recomendación')}")
        print(f"Motivo principal: {r.datos.get('motivo', 'Sin historial suficiente.')}")
        comparativa = r.datos.get("comparativa", [])
        if not comparativa:
            print("Sin proveedores evaluables para esta propuesta.")
            return
        for i, item in enumerate(comparativa[:10], 1):
            total = item.get("coste_total_estimado")
            total_txt = f"{float(total):.2f} €" if total is not None else "desconocido"
            plazo = item.get("dias_entrega_estimados")
            plazo_txt = str(plazo) if plazo is not None else "desconocido"
            print(
                f"{i}. {item.get('proveedor_nombre', '-')} | puntuación {item.get('puntuacion', 0)} | "
                f"coste total {total_txt} | plazo {plazo_txt} días"
            )
            if item.get("advertencias"):
                print(f"   Advertencias: {'; '.join(item.get('advertencias', [])[:3])}")

    def _comparar_proveedores_producto_r43(self, producto):
        try:
            cantidad = self._parse_float_opcional(input("Cantidad [1]: ").strip())
            cantidad = 1.0 if cantidad is None else float(cantidad)
        except ValueError:
            print("Cantidad no válida.")
            return
        unidad = input("Unidad [u]: ").strip() or "u"
        prioridad = input("Prioridad [Normal]: ").strip() or "Normal"
        fecha_necesaria = input("Fecha necesaria ISO (opcional, ej 2026-07-20): ").strip()
        r = self.core.orquestador.resolver(
            SolicitudHostAI(
                "comparar_proveedores_producto_compra",
                {
                    "producto": producto,
                    "cantidad": cantidad,
                    "unidad": unidad,
                    "prioridad": prioridad,
                    "fecha_necesaria": fecha_necesaria,
                },
            )
        )
        if not r.ok:
            print(r.mensaje)
            return
        comparativa = r.datos.get("comparativa", [])
        print("\nCOMPARATIVA DE PROVEEDORES (PRODUCTO)")
        print(f"Producto: {producto} | Cantidad: {cantidad} {unidad}")
        if not comparativa:
            print("Sin proveedores evaluables para este producto.")
            return
        for i, item in enumerate(comparativa[:10], 1):
            total = item.get("coste_total_estimado")
            total_txt = f"{float(total):.2f} €" if total is not None else "desconocido"
            print(
                f"{i}. {item.get('proveedor_nombre', '-')} | puntuación {item.get('puntuacion', 0)} | "
                f"coste total {total_txt} | mínimo {'sí' if item.get('cumple_pedido_minimo') else 'no'}"
            )
            if item.get("advertencias"):
                print(f"   Advertencias: {'; '.join(item.get('advertencias', [])[:3])}")

    def _editar_condiciones_asociacion_producto_r43(self, producto, asociaciones):
        sel = input("Selecciona asociación (número): ").strip()
        if not sel.isdigit() or not (1 <= int(sel) <= len(asociaciones)):
            print("Selección no válida.")
            return
        elegido = asociaciones[int(sel) - 1]
        print("Pulsa Enter para mantener el valor actual.")
        try:
            precio_habitual = self._parse_float_opcional(input(f"Precio habitual [{elegido.get('precio_habitual', '')}]: ").strip())
            cantidad_minima = self._parse_float_opcional(input(f"Cantidad mínima producto [{elegido.get('cantidad_minima_producto', '')}]: ").strip())
            plazo = self._parse_int_opcional(input(f"Plazo entrega días [{elegido.get('plazo_entrega_dias', '')}]: ").strip())
        except ValueError:
            print("Valor numérico no válido.")
            return
        unidad_precio = input(f"Unidad precio [{elegido.get('unidad_precio', '')}]: ").strip()
        observaciones = input(f"Observaciones [{elegido.get('observaciones', '')}]: ").strip()
        payload = {
            "asociacion_id": elegido.get("id", ""),
            "precio_habitual": precio_habitual,
            "cantidad_minima_producto": cantidad_minima,
            "plazo_entrega_dias": plazo,
            "unidad_precio": unidad_precio if unidad_precio else None,
            "observaciones": observaciones if observaciones else None,
        }
        rr = self.core.orquestador.resolver(SolicitudHostAI("editar_asociacion_producto_proveedor_compra", payload))
        print(rr.mensaje)
        if rr.ok:
            self._comparar_proveedores_producto_r43(producto)

    def _editar_condiciones_comerciales_proveedor_r43(self):
        prov = self._seleccionar_proveedor_r41()
        if not prov:
            return
        print("Pulsa Enter para mantener el valor actual.")
        try:
            pedido_minimo_importe = self._parse_float_opcional(input(f"Pedido mínimo € [{prov.get('pedido_minimo_importe', '')}]: ").strip())
            portes = self._parse_float_opcional(input(f"Portes € [{prov.get('portes', '')}]: ").strip())
            portes_gratis_desde = self._parse_float_opcional(input(f"Portes gratis desde € [{prov.get('portes_gratis_desde', '')}]: ").strip())
            plazo_entrega_general_dias = self._parse_int_opcional(input(f"Plazo entrega general días [{prov.get('plazo_entrega_general_dias', '')}]: ").strip())
        except ValueError:
            print("Valor numérico no válido.")
            return
        dias_reparto_txt = input(f"Días de reparto (coma) [{', '.join(prov.get('dias_reparto', []) or [])}]: ").strip()
        observaciones_comerciales = input(f"Observaciones comerciales [{prov.get('observaciones_comerciales', '')}]: ").strip()
        payload = {
            "proveedor_id": prov.get("id", ""),
            "pedido_minimo_importe": pedido_minimo_importe,
            "portes": portes,
            "portes_gratis_desde": portes_gratis_desde,
            "plazo_entrega_general_dias": plazo_entrega_general_dias,
            "dias_reparto": [x.strip() for x in dias_reparto_txt.split(",") if x.strip()] if dias_reparto_txt else None,
            "observaciones_comerciales": observaciones_comerciales if observaciones_comerciales else None,
        }
        r = self.core.orquestador.resolver(SolicitudHostAI("editar_condiciones_proveedor_compra", payload))
        print(r.mensaje)

    def _listar_proveedores_r41(self):
        texto = input("Filtro (nombre/cif/email, opcional): ").strip()
        proveedores = self.core.compras.listar_proveedores(incluir_inactivos=True, texto=texto)
        if not proveedores:
            print("No hay proveedores.")
            return
        for i, p in enumerate(proveedores, 1):
            print(f"{i}. [{p.get('estado', 'activo').upper()}] {p.get('nombre', '-')} | ID: {p.get('id', '-')}")
            if p.get("productos_habituales"):
                print(f"   Productos: {', '.join(p.get('productos_habituales', [])[:8])}")

    def _seleccionar_proveedor_r41(self):
        proveedores = self.core.compras.listar_proveedores(incluir_inactivos=True)
        if not proveedores:
            print("No hay proveedores.")
            return None
        self._listar_proveedores_r41()
        elegido = input("Selecciona proveedor (número o ID): ").strip()
        if elegido.isdigit() and 1 <= int(elegido) <= len(proveedores):
            return proveedores[int(elegido) - 1]
        for p in proveedores:
            if str(p.get("id", "")).lower() == elegido.lower():
                return p
        print("Selección no válida.")
        return None

    def _crear_proveedor_r41(self):
        nombre = input("Nombre proveedor: ").strip()
        if not nombre:
            print("El nombre es obligatorio.")
            return
        r = self.core.orquestador.resolver(
            SolicitudHostAI(
                "crear_proveedor_manual",
                {
                    "nombre": nombre,
                    "cif": input("CIF (opcional): ").strip(),
                    "telefono": input("Teléfono (opcional): ").strip(),
                    "email": input("Email (opcional): ").strip(),
                    "direccion": input("Dirección (opcional): ").strip(),
                    "comercial": input("Comercial (opcional): ").strip(),
                    "observaciones": input("Observaciones (opcional): ").strip(),
                },
            )
        )
        print(r.mensaje)

    def _editar_proveedor_r41(self):
        prov = self._seleccionar_proveedor_r41()
        if not prov:
            return
        print("Pulsa Enter para mantener el valor actual.")
        cambios = {}
        for campo, etiqueta in (
            ("nombre", "Nombre"),
            ("cif", "CIF"),
            ("telefono", "Teléfono"),
            ("email", "Email"),
            ("direccion", "Dirección"),
            ("comercial", "Comercial"),
            ("observaciones", "Observaciones"),
        ):
            actual = str(prov.get(campo, "") or "")
            nuevo = input(f"{etiqueta} [{actual}]: ").strip()
            if nuevo:
                cambios[campo] = nuevo
        if not cambios:
            print("Sin cambios.")
            return
        r = self.core.orquestador.resolver(
            SolicitudHostAI("editar_proveedor_compra", {"proveedor_id": prov["id"], "cambios": cambios})
        )
        print(r.mensaje)

    def _desactivar_proveedor_r41(self):
        prov = self._seleccionar_proveedor_r41()
        if not prov:
            return
        if input(f"¿Desactivar {prov.get('nombre', '-') }? (s/n): ").strip().lower() not in {"s", "si", "sí", "y", "yes"}:
            print("Operación cancelada.")
            return
        r = self.core.orquestador.resolver(SolicitudHostAI("desactivar_proveedor_compra", {"proveedor_id": prov["id"]}))
        print(r.mensaje)

    def _asociar_producto_proveedor_r41(self):
        prov = self._seleccionar_proveedor_r41()
        if not prov:
            return
        producto = input("Producto habitual a asociar: ").strip()
        if not producto:
            print("Producto obligatorio.")
            return
        r = self.core.orquestador.resolver(
            SolicitudHostAI("asociar_producto_proveedor_compra", {"proveedor_id": prov["id"], "producto": producto})
        )
        print(r.mensaje)

    def _onboarding_proveedor_detectado_r41(self):
        nombre = input("Nombre detectado del proveedor: ").strip()
        if not nombre:
            print("Debes indicar un nombre detectado.")
            return
        r = self.core.orquestador.resolver(
            SolicitudHostAI("preparar_onboarding_proveedor_detectado", {"nombre_detectado": nombre, "datos_detectados": {}})
        )
        print(r.mensaje)
        datos = r.datos
        print(f"OCR implementado: {datos.get('ocr_implementado', False)}")
        print(f"Sugerencia: {datos.get('sugerencia', 'crear_manual')}")

    def _mostrar_historial_compras_r41(self):
        texto = input("Filtro (producto/proveedor/origen, opcional): ").strip()
        r = self.core.orquestador.resolver(SolicitudHostAI("listar_historial_compras", {"texto": texto}))
        compras = r.datos.get("compras", [])
        print(r.mensaje)
        if not compras:
            return
        for i, c in enumerate(compras[:100], 1):
            print(
                f"{i}. {c.get('producto', '-')} | {c.get('cantidad', 0)} {c.get('unidad', 'u')} | "
                f"{c.get('proveedor', 'Sin proveedor')} | {c.get('origen_tipo', 'manual')} | {c.get('id', '-') }"
            )

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
        if r.ok:
            necesidad = r.datos.get("necesidad", {})
            self.ultima_necesidad_compra_id = necesidad.get("id") or self.ultima_necesidad_compra_id
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
        seleccionado = self._seleccionar_con_activo(
            necesidades, self.ultima_necesidad_compra_id, "Necesidad", id_key="id"
        )
        if seleccionado:
            self.ultima_necesidad_compra_id = seleccionado.get("id")
        return seleccionado

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
        necesidad = self.core.compras.obtener(actual["id"])
        sincronizados = getattr(necesidad, "_pedidos_sincronizados", []) if necesidad else []
        if sincronizados:
            print(f"Pedido abierto sincronizado automáticamente: {', '.join(sincronizados)}")

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
        necesidad = self.core.compras.obtener(actual["id"])
        afectados = getattr(necesidad, "_pedidos_afectados", []) if necesidad else []
        if afectados:
            print(f"La línea vinculada se retiró de {len(afectados)} pedido(s) abierto(s).")

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
        generados = r.datos.get("pedidos_sugeridos", [])
        for p in generados:
            self.ultimo_pedido_compra_id = p.get("id") or self.ultimo_pedido_compra_id
            print(f"\nPedido {p.get('id', '-')} | Proveedor: {p['proveedor']} | Estado: {p.get('estado', 'borrador')}")
            lineas = p.get("lineas") or p.get("necesidades") or []
            for n in lineas:
                print(f"- {n['nombre']}: {n['cantidad']} {n['unidad']}")
        if not generados:
            vinculadas = r.datos.get("pendientes_ya_vinculadas", 0)
            abiertos = r.datos.get("pedidos_abiertos", 0)
            if vinculadas:
                print(f"Hay {vinculadas} necesidad(es) pendiente(s) ya incluida(s) en {abiertos} pedido(s) abierto(s).")
                print("Entra en 'Gestionar pedidos' para revisarlas o editarlas; no se duplicarán.")

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
        seleccionado = self._seleccionar_con_activo(
            pedidos, self.ultimo_pedido_compra_id, "Pedido", id_key="id"
        )
        if seleccionado:
            self.ultimo_pedido_compra_id = seleccionado.get("id")
        return seleccionado

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
            activo = self.core.compras.obtener_pedido(self.ultimo_pedido_compra_id) if self.ultimo_pedido_compra_id else None
            cabecera = "PEDIDOS OPERATIVOS"
            if activo:
                cabecera += f" — Activo: {activo.proveedor} [{activo.estado.upper()}]"
            print("\n" + cabecera)
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

    def _ultimo_coste_compra(self, linea, pedido):
        precio_linea = float(linea.get("precio_unitario", 0) or 0)
        if precio_linea > 0:
            return precio_linea
        return float(self.core.stock.ultimo_coste_conocido(
            nombre=linea.get("nombre", ""),
            articulo_id=linea.get("articulo_id", ""),
            proveedor=pedido.get("proveedor", ""),
        ) or 0)

    def _recibir_pedido_compra(self):
        pedido = self._seleccionar_pedido_compra({"borrador", "preparado", "enviado"})
        if not pedido:
            return
        self._imprimir_detalle_pedido(pedido)
        if pedido.get("estado") == "borrador":
            print("AVISO: este pedido todavía está en borrador y no consta como enviado.")
            if not self._preguntar_si_no("¿Recibirlo igualmente?", por_defecto=False):
                print("Recepción cancelada. Puedes marcarlo como preparado o enviado desde la opción 7.")
                return
        ubicacion = input("Ubicación de entrada [almacén]: ").strip() or "almacén"
        caducidades, costes = {}, {}
        for linea in pedido.get("lineas", []):
            cad = input(f"Caducidad de {linea['nombre']} (opcional): ").strip()
            if cad:
                cad_n = self._normalizar_fecha_stock(cad)
                if cad_n is None:
                    return
                caducidades[linea["id"]] = cad_n
            sugerido = self._ultimo_coste_compra(linea, pedido)
            sugerido_txt = f"{sugerido:.4f}".rstrip("0").rstrip(".") if sugerido > 0 else "0.0"
            precio = input(f"Coste unitario de {linea['nombre']} [{sugerido_txt}]: ").strip().replace(",", ".")
            if not precio and sugerido > 0:
                costes[linea["id"]] = sugerido
            elif precio:
                try:
                    costes[linea["id"]] = float(precio)
                except ValueError:
                    print("Coste no válido.")
                    return
        if not self._preguntar_si_no("¿Confirmar recepción y actualizar stock?", por_defecto=False):
            print("Recepción cancelada.")
            return
        try:
            r = self.core.orquestador.resolver(SolicitudHostAI("recibir_pedido_compra", {
                "pedido_id": pedido["id"], "ubicacion": ubicacion,
                "caducidades": caducidades, "costes": costes,
            }))
            print(r.mensaje)
            if r.ok:
                entradas = r.datos.get("entradas_stock", [])
                print("\nRESUMEN DE RECEPCIÓN")
                print("=" * 62)
                importe_total = 0.0
                for entrada in entradas:
                    cantidad = float(entrada.get("cantidad", 0) or 0)
                    coste = float(entrada.get("coste_unitario", 0) or 0)
                    importe = float(entrada.get("importe", cantidad * coste) or 0)
                    importe_total += importe
                    print(f"- {entrada.get('nombre', 'Artículo')}: +{cantidad:g} {entrada.get('unidad', '')}")
                    print(f"  Ubicación: {entrada.get('ubicacion') or ubicacion} | Coste: {coste:.2f} €/{entrada.get('unidad', '')} | Importe: {importe:.2f} €")
                    if entrada.get("caducidad"):
                        print(f"  Caducidad: {entrada['caducidad']}")
                    if entrada.get("lote_id"):
                        print(f"  Lote: {entrada['lote_id']}")
                print(f"Líneas recibidas: {len(entradas)} | Importe recibido: {importe_total:.2f} €")
                print("Pedido: RECIBIDO | Necesidades vinculadas: COMPRADAS | Stock: ACTUALIZADO")
                print("=" * 62)
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
            activos = self.core.escandallos_inteligente.listar(False)
            incompletos = sum(1 for e in activos if not e.get("lineas"))
            print(f"\nESCANDALLOS | Activos: {len(activos)} | Sin ingredientes: {incompletos}")
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
        todos = self.core.escandallos_inteligente.listar(incluir_inactivos)
        activo = next((e for e in todos if str(e.get("receta_id")) == str(self.ultimo_escandallo_id or "")), None)
        if activo:
            print(f"Receta activa: {activo.get('nombre')} | {activo.get('receta_id')}")
            valor = input("Enter=usar activa | texto=buscar otra | 0=cancelar: ").strip()
            if valor == "0":
                print("Operación cancelada.")
                return None
            if not valor:
                return activo
            texto = valor
        else:
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
        seleccionado = self._seleccionar_elemento(
            escandallos,
            prompt="Número de receta",
            permitir_id=True,
            id_key="receta_id",
            auto_unico=True,
        )
        if seleccionado:
            self.ultimo_escandallo_id = seleccionado.get("receta_id")
        return seleccionado

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
            if r.ok:
                self.ultimo_escandallo_id = codigo
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

    @staticmethod
    def _validar_escandallo_economico(esc):
        if not esc.get("lineas"):
            print("No se puede calcular la rentabilidad: la receta no tiene ingredientes.")
            print("Añade al menos un ingrediente desde 'Gestionar ingredientes'.")
            return False
        return True

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
        if not esc or not self._validar_escandallo_economico(esc): return
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
        if not esc or not self._validar_escandallo_economico(esc): return
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
                if len(base['lineas']) == 1:
                    idx = 0
                    print("Se ha seleccionado automáticamente el único ingrediente.")
                else:
                    idx=int(input("Número de ingrediente (0=cancelar): ").strip())-1
                    if idx < 0:
                        print("Simulación cancelada.")
                        return
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
    def _total_precios_disponibles(self):
        """Cuenta precios explícitos y precios embebidos en escandallos."""
        ids = set()
        try:
            datos = self.core.costes_inteligente.listar_precios()
            for precio in datos.get("precios", []):
                clave = precio.get("articulo_id") or precio.get("nombre")
                if clave and float(precio.get("precio_unitario", 0) or 0) > 0:
                    ids.add(str(clave).lower())
        except Exception:
            pass
        try:
            for esc in self.core.escandallos_inteligente.listar(True):
                for linea in esc.get("lineas", []):
                    if float(linea.get("coste_unitario", 0) or 0) > 0:
                        clave = linea.get("articulo_id") or linea.get("elaboracion_id") or linea.get("nombre")
                        if clave:
                            ids.add(str(clave).lower())
        except Exception:
            pass
        return len(ids)

    def _menu_costes(self):
        while True:
            print(f"\nCOSTES | Precios disponibles: {self._total_precios_disponibles()}")
            print("1. Registrar / actualizar precio")
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
                articulo = self._seleccionar_articulo_stock()
                if not articulo:
                    continue
                try:
                    precio = float(input("Precio unitario: ").strip() or "0")
                except ValueError:
                    print("Precio no válido.")
                    continue
                unidad = input(f"Unidad [{articulo.get('unidad') or 'kg'}]: ").strip() or articulo.get('unidad') or "kg"
                proveedor = input(f"Proveedor [{articulo.get('proveedor') or ''}]: ").strip() or articulo.get('proveedor') or ""
                d=self.core.costes_inteligente.registrar_precio(
                    articulo.get('nombre',''), precio, unidad,
                    articulo.get('articulo_id',''), proveedor, articulo.get('familia','')
                )
                self.core.db.guardar("precios", list(self.core.costes_inteligente.listar_precios()["precios"]))
                print(f"Precio registrado: {d['nombre']} — {d['precio_unitario']} €/{d['unidad']}.")
            elif op == "2":
                esc = self._seleccionar_escandallo(False)
                if not esc or not self._validar_escandallo_economico(esc):
                    continue
                try:
                    raciones = int(input(f"Raciones [{esc['raciones_base']}]: ").strip() or esc['raciones_base'])
                    precio = float(input("Precio venta/ración [0]: ").strip() or "0")
                except ValueError:
                    print("Raciones o precio no válidos.")
                    continue
                d=self.core.costes_inteligente.calcular_coste_receta(esc['receta_id'],raciones,precio)
                self._imprimir_resultado_escandallo_operativo(d)
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
                if not d['eventos_analizados']:
                    print("Todavía no hay eventos con rentabilidad calculada.")
                    print("Primero calcula el coste operativo de un evento desde la opción 3 y analiza su rentabilidad desde la opción 6.")
                    continue
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
                    self._preparar_produccion_evento_activo()
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
                        vista=self._produccion_stock.preparar_cierre(plan['id'],tarea['id'])
                        if vista.get('estado')=='SIN_ESCANDALLO':
                            print("No hay escandallo para actualizar stock. La tarea no se ha cerrado.")
                        elif vista.get('estado')=='STOCK_INSUFICIENTE':
                            print("No hay stock suficiente:")
                            for f in vista.get('faltantes',[]):
                                print(f"- {f['nombre']}: faltan {f['faltante']:g} {f['unidad']}")
                            if self._preguntar_si_no("¿Registrar incidencia y dejar la tarea bloqueada? (s/n): "):
                                self._produccion_stock.registrar_incidencia_stock(plan['id'],tarea['id'],"Stock insuficiente para cerrar la producción")
                                print("Incidencia registrada. No se ha modificado el stock.")
                        elif vista.get('estado')=='UNIDAD_INCOMPATIBLE':
                            print(vista.get('mensaje','Hay unidades incompatibles para cerrar la producción.'))
                            for i in vista.get('incompatibilidades',[]):
                                print(f"- {i['nombre']}: requiere {i['cantidad']:g} {i['unidad']}")
                        elif vista.get('estado') in {'RECETA_INCOMPLETA','CANTIDAD_INVALIDA','AP_COMO_MP_NO_PERMITIDO'}:
                            print(vista.get('mensaje','No se pudo validar el cierre de producción.'))
                        elif not vista.get('ok'):
                            print(vista.get('mensaje','No se pudo preparar el cierre.'))
                        else:
                            print("Movimientos previstos:")
                            for c in vista.get('consumos',[]):
                                print(f"- Salida: {c['nombre']} -{c['cantidad']:g} {c['unidad']}")
                            g=vista.get('produccion_generada',{})
                            print(f"- Entrada: {g.get('nombre')} +{g.get('cantidad',0):g} {g.get('unidad','u')}")
                            if self._preguntar_si_no("¿Registrar producción y actualizar stock? (s/n): "):
                                operario=(self.core.produccion_real.obtener_plan(plan['id']).responsable or "cocina").strip() or "cocina"
                                lote=input("Lote (opcional): ").strip()
                                resultado=self._produccion_stock.cerrar_y_actualizar_stock(plan['id'],tarea['id'],operario,lote)
                                print(resultado.get('mensaje'))
                            else:
                                print("No se ha modificado la tarea ni el stock.")
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
        print("9. I1.1 Detectar escandallos antiguos (solo análisis)")
        print("10. I1.2 Vista previa e importación segura de recetas")
        print("11. I1.3.1 Detector limpio de menús (solo vista previa)")
        print("12. I1.3.2.1.1 Catálogo de reconocimiento corregido (solo vista previa)")
        print("13. I1.3.2.2 Constructor del árbol semántico (solo vista previa)")
        print("14. I1.3.2.3 Vista previa inteligente y resolución asistida")
        print("15. I1.3.2.4 Motor de aprendizaje culinario")
        print("16. I1.3.3 Preimportación definitiva de menús")
        print("17. I1.3.3.1 Resolución de bloqueos de preimportación")
        print("18. M1.1 Diagnóstico del núcleo MUR (sin datos de negocio)")
        print("19. M1.2 Diagnóstico del resolutor de artículos")
        print("20. M1.3 Diagnóstico del resolutor de recetas")
        print("21. M1.3.1 Diagnóstico del importador inteligente de recetas")
        print("22. M1.3.2 Diagnóstico de resolución automática de ingredientes")
        print("23. M1.3.3 Diagnóstico de validación culinaria inteligente")
        print("24. I1.3.4.1.1 Detección y simulación multimenú")
        print("25. I1.3.4.1.2 Clasificador gastronómico y simulación multimenú")
        print("26. I1.3.4.1.3 Bandeja de revisión y limpieza masiva")
        print("27. I1.3.4.1.4 Motor de interpretación culinaria")
        print("28. I1.3.4.1.5 Motor de conocimiento gastronómico")
        print("29. I1.3.4.2 Diagnóstico del motor de escritura segura")
        print("30. I1.3.4.3 Diagnóstico de importación definitiva de menús")
        print("31. I1.3.4.4 Auditoría e integridad postimportación")
        print("32. I1.3.4.4.1 Bandeja de corrección postimportación")
        print("33. I1.3.4.4.2 Corrección inteligente masiva y navegación")
        print("34. I1.3.5 Refactorización y certificación final del importador")
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

        elif op == "9":
            ruta = input("Ruta del Excel: ").strip().strip('\"')
            hoja = input("Hoja concreta (vacío=todas): ").strip()
            try:
                detector = DetectorEscandallosAntiguosI11()
                resultado = detector.analizar(
                    ruta,
                    hojas=[hoja] if hoja else None,
                    exportar_json=True,
                )
                print(formatear_resumen_i11(resultado))
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo analizar el Excel: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.1: {exc}")

        elif op == "10":
            ruta = input("Ruta del Excel: ").strip().strip('\"')
            hoja = input("Hoja concreta (vacío=todas): ").strip()
            try:
                catalogo = self._cargar_catalogo_articulos()
                origen_catalogo = "catálogo local de Host AI"
                if not catalogo:
                    print("ERROR I1.2.1.1: el catálogo de artículos está vacío.")
                    print("La importación queda bloqueada para evitar recetas sin vincular.")
                    print("Primero importa o revisa los artículos desde Excel / importaciones.")
                    return
                print(f"Catálogo cargado: {len(catalogo)} artículo(s) | Origen: {origen_catalogo}")
                print("Motor de vinculación inteligente: ACTIVO")
                existentes = self.core.escandallos_inteligente.listar(incluir_inactivos=True)
                importador = ImportadorSeguroEscandallosI12()
                previa = importador.preparar(
                    ruta, hojas=[hoja] if hoja else None,
                    catalogo_articulos=catalogo,
                    escandallos_existentes=existentes,
                )
                print(formatear_previa_i12(previa))
                pendientes = importador.pendientes_revision(previa)
                if pendientes and self._preguntar_si_no(f"¿Revisar ahora {len(pendientes)} vínculo(s) dudoso(s)?", True):
                    for numero, ing in enumerate(pendientes, 1):
                        print("\n" + "-" * 72)
                        print(f"REVISIÓN {numero}/{len(pendientes)} — {ing.get('nombre_excel')}")
                        candidatos = list(ing.get('candidatos') or [])
                        for idx, candidato in enumerate(candidatos, 1):
                            print(f"{idx}. {candidato.get('nombre')} | {candidato.get('articulo_id') or '-'} | {candidato.get('confianza',0):.0%}")
                        print("B. Buscar otro artículo del catálogo")
                        print("N. Crear artículo nuevo")
                        print("O. Omitir y dejar pendiente")
                        eleccion = input("Selecciona opción: ").strip()
                        articulo = None
                        if eleccion.isdigit() and 1 <= int(eleccion) <= len(candidatos):
                            c = candidatos[int(eleccion)-1]
                            articulo = {"articulo_id": c.get("articulo_id", ""), "nombre": c.get("nombre", ""), "proveedor": c.get("proveedor", ""), "familia": c.get("familia", "")}
                        elif eleccion.lower() == "b":
                            termino = input("Buscar artículo: ").strip()
                            encontrados = self._buscar_catalogo_articulos(termino)
                            for idx, art in enumerate(encontrados, 1):
                                print(f"{idx}. {art.get('nombre')} | {art.get('codigo') or art.get('id') or '-'} | {art.get('proveedor') or 'sin proveedor'}")
                            sel = input("Número (Enter=cancelar): ").strip()
                            if sel.isdigit() and 1 <= int(sel) <= len(encontrados):
                                art = encontrados[int(sel)-1]
                                articulo = {"articulo_id": art.get("codigo") or art.get("id") or "", "nombre": art.get("nombre") or art.get("articulo") or "", "proveedor": art.get("proveedor") or "", "familia": art.get("familia") or ""}
                        elif eleccion.lower() == "n":
                            nombre_nuevo = input(f"Nombre del artículo [{ing.get('nombre_excel')}]: ").strip() or ing.get('nombre_excel')
                            familia = input("Familia (opcional): ").strip()
                            proveedor = input("Proveedor habitual (opcional): ").strip()
                            creado = self._crear_articulo_catalogo_stock(nombre_nuevo, familia, proveedor)
                            articulo = {"articulo_id": creado.get("codigo", ""), "nombre": creado.get("nombre", nombre_nuevo), "familia": familia, "proveedor": proveedor}
                            catalogo.append(creado)
                        if articulo:
                            recordar = self._preguntar_si_no("¿Recordar esta equivalencia para futuras importaciones?", True)
                            importador.aplicar_decision(previa, ing.get('nombre_excel'), articulo, recordar=recordar)
                            print(f"Vinculado: {ing.get('nombre_excel')} -> {articulo.get('nombre')}")
                        else:
                            print("Vínculo dejado pendiente.")
                    print("\nVISTA PREVIA ACTUALIZADA")
                    print(formatear_previa_i12(previa))
                if not self._preguntar_si_no("¿Importar únicamente recetas seguras y completamente vinculadas?", False):
                    print("Importación cancelada. No se modificó la base de datos.")
                else:
                    resultado = importador.importar(
                        previa, self.core.escandallos_inteligente,
                        confirmar=True, permitir_probables=False, permitir_sin_resolver=False,
                    )
                    print(f"Importadas: {resultado['resumen']['importadas']} | Omitidas: {resultado['resumen']['omitidas']} | Errores: {resultado['resumen']['errores']}")
                    for r in resultado['omitidas']:
                        print(f"- Omitida {r['nombre']}: {r['motivo']}")
                    for r in resultado['errores']:
                        print(f"- Error {r['nombre']}: {r['error']}")
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo preparar la importación I1.2: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.2: {exc}")

        elif op == "11":
            ruta = input("Ruta del Excel: ").strip().strip('\"')
            hoja = input("Hoja de menú concreta (vacío=detectar hojas MENU): ").strip()
            try:
                detector = DetectorLimpioMenusI131()
                previa = detector.preparar(
                    ruta,
                    hojas=[hoja] if hoja else None,
                )
                print(formatear_previa_i131(previa))
                if not previa["menus"]:
                    print("No se detectaron menús válidos.")
                else:
                    print("I1.3.1 es solo detección: no existe ninguna opción de importación.")
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo preparar la detección I1.3.1: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.1: {exc}")

        elif op == "12":
            ruta = input("Ruta del Excel: ").strip().strip('\"')
            hoja = input("Hoja de menú concreta (vacío=detectar hojas MENU): ").strip()
            try:
                motor = MotorReconocimientoMenusI1321(self.core.base_dir)
                resultado = motor.preparar_desde_excel(
                    ruta,
                    hojas=[hoja] if hoja else None,
                )
                print(formatear_reconocimiento_i1321(resultado))
                print("I1.3.2.1.1 no interpreta componentes ni permite importar.")
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo preparar el reconocimiento I1.3.2.1.1: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.2.1.1: {exc}")

        elif op == "13":
            ruta = input("Ruta del Excel: ").strip().strip('\"')
            hoja = input("Hoja de menú concreta (vacío=detectar hojas MENU): ").strip()
            try:
                constructor = ConstructorArbolSemanticoMenusI1322(self.core.base_dir)
                resultado = constructor.preparar_desde_excel(
                    ruta,
                    hojas=[hoja] if hoja else None,
                )
                print(formatear_arbol_semantico_i1322(resultado))
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo preparar el árbol semántico I1.3.2.2: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.2.2: {exc}")

        elif op == "14":
            ruta = input("Ruta del Excel: ").strip().strip('\"')
            hoja = input("Hoja de menú concreta (vacío=detectar hojas MENU): ").strip()
            try:
                asistente = VistaPreviaResolucionAsistidaMenusI1323(self.core.base_dir)
                resultado = asistente.preparar_desde_excel(ruta, hojas=[hoja] if hoja else None)
                print(formatear_vista_previa_i1323(resultado))
                for pendiente in list(resultado.get("pendientes_revision", [])):
                    print("\n" + "-" * 72)
                    print(f"PENDIENTE: {pendiente['texto']} | Rol sugerido: {pendiente['rol']}")
                    print(f"Plato: {pendiente['plato']}")
                    print("1. Vincular con receta existente")
                    print("2. Proponer nueva receta pendiente de completar")
                    print("3. Vincular con artículo existente")
                    print("4. Mantener sin resolver")
                    print("0. Terminar revisión")
                    eleccion = input("Selecciona opción: ").strip()
                    if eleccion == "0": break
                    destino = None; accion = "MANTENER_PENDIENTE"
                    if eleccion in {"1","3"}:
                        termino = input("Buscar en catálogo: ").strip() or pendiente['texto']
                        grupos = asistente.candidatos(termino)
                        lista = grupos["recetas" if eleccion == "1" else "articulos"]
                        for i,item in enumerate(lista,1): print(f"{i}. {item['nombre']} | {item.get('entidad_id') or '-'}")
                        sel=input("Número (Enter=cancelar): ").strip()
                        if not sel.isdigit() or not (1 <= int(sel) <= len(lista)): continue
                        destino=lista[int(sel)-1]; accion="VINCULAR_RECETA" if eleccion=="1" else "VINCULAR_ARTICULO"
                    elif eleccion == "2":
                        nombre=input(f"Nombre propuesto [{pendiente['texto']}]: ").strip() or pendiente['texto']
                        destino={"nombre":nombre,"tipo":"PROPUESTA_RECETA","entidad_id":""}; accion="PROPONER_NUEVA_RECETA"
                    recordar = False
                    if accion != "MANTENER_PENDIENTE":
                        recordar = self._preguntar_si_no("¿Recordar esta decisión para futuras vistas previas?", False)
                    asistente.aplicar_decision(resultado, pendiente['texto'], pendiente['rol'], accion, destino, recordar=recordar)
                print("\nVISTA PREVIA ACTUALIZADA")
                print(formatear_vista_previa_i1323(resultado))
                print("I1.3.2.3 no permite importar menús.")
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo preparar I1.3.2.3: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.2.3: {exc}")

        elif op == "15":
            ruta = input("Ruta del Excel: ").strip().strip('\"')
            hoja = input("Hoja de menú concreta (vacío=detectar hojas MENU): ").strip()
            try:
                motor_aprendizaje = MotorAprendizajeCulinarioI1324(self.core.base_dir)
                resultado = motor_aprendizaje.preparar_desde_excel(ruta, hojas=[hoja] if hoja else None)
                print(formatear_vista_aprendizaje_i1324(resultado))
                for pendiente in list(resultado.get("pendientes_revision", [])):
                    print("\n" + "-" * 72)
                    print(f"PENDIENTE: {pendiente['texto']} | Rol sugerido: {pendiente['rol']}")
                    print(f"Plato: {pendiente['plato']}")
                    print("1. Vincular con receta existente")
                    print("2. Proponer nueva receta pendiente de completar")
                    print("3. Vincular con artículo existente")
                    print("4. Mantener sin resolver")
                    print("0. Terminar revisión")
                    eleccion = input("Selecciona opción: ").strip()
                    if eleccion == "0":
                        break
                    destino = None
                    accion = "MANTENER_PENDIENTE"
                    if eleccion in {"1", "3"}:
                        termino = input("Buscar en catálogo: ").strip() or pendiente['texto']
                        grupos = motor_aprendizaje.candidatos(termino)
                        lista = grupos["recetas" if eleccion == "1" else "articulos"]
                        for i, item in enumerate(lista, 1):
                            print(f"{i}. {item['nombre']} | {item.get('entidad_id') or '-'}")
                        sel = input("Número (Enter=cancelar): ").strip()
                        if not sel.isdigit() or not (1 <= int(sel) <= len(lista)):
                            continue
                        destino = lista[int(sel)-1]
                        accion = "VINCULAR_RECETA" if eleccion == "1" else "VINCULAR_ARTICULO"
                    elif eleccion == "2":
                        nombre = input(f"Nombre propuesto [{pendiente['texto']}]: ").strip() or pendiente['texto']
                        destino = {"nombre": nombre, "tipo": "PROPUESTA_RECETA", "entidad_id": ""}
                        accion = "PROPONER_NUEVA_RECETA"
                    recordar = False
                    if accion != "MANTENER_PENDIENTE":
                        recordar = self._preguntar_si_no("¿Guardar este aprendizaje culinario para usos futuros?", True)
                    motor_aprendizaje.aplicar_decision(
                        resultado, pendiente['texto'], pendiente['rol'], accion, destino, recordar=recordar
                    )
                print("\nVISTA PREVIA ACTUALIZADA")
                print(formatear_vista_aprendizaje_i1324(resultado))

                aprendizajes = motor_aprendizaje.listar_aprendizajes()
                if aprendizajes:
                    print("\nMEMORIA CULINARIA ACTIVA")
                    for i, ap in enumerate(aprendizajes, 1):
                        print(f"{i}. {ap['texto_origen']} -> {ap.get('nombre_destino') or '-'} | {ap['rol']} | {ap['accion']} | usos {ap.get('usos',0)} | confianza {float(ap.get('confianza',1))*100:.0f}%")
                    print("E. Editar un aprendizaje")
                    print("D. Desactivar un aprendizaje")
                    print("Enter. Continuar")
                    gestion = input("Gestión de memoria: ").strip().lower()
                    if gestion in {"e", "d"}:
                        sel = input("Número del aprendizaje: ").strip()
                        if sel.isdigit() and 1 <= int(sel) <= len(aprendizajes):
                            ap = aprendizajes[int(sel)-1]
                            if gestion == "d":
                                motor_aprendizaje.eliminar_aprendizaje(ap['aprendizaje_id'])
                                print("Aprendizaje desactivado. Se conserva su historial.")
                            else:
                                nombre = input(f"Nombre destino [{ap.get('nombre_destino','')}]: ").strip() or ap.get('nombre_destino','')
                                rol = input(f"Rol [{ap.get('rol','')}]: ").strip().upper() or ap.get('rol','')
                                motor_aprendizaje.editar_aprendizaje(ap['aprendizaje_id'], nombre_destino=nombre, rol=rol)
                                print("Aprendizaje actualizado con historial.")
                print("I1.3.2.4 no permite importar menús ni crear recetas.")
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo preparar I1.3.2.4: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.2.4: {exc}")

        elif op == "16":
            ruta = input("Ruta del Excel: ").strip().strip('\"')
            hoja = input("Hoja de menú concreta (vacío=detectar hojas MENU): ").strip()
            try:
                preimportador = PreimportadorDefinitivoMenusI133(self.core.base_dir)
                resultado = preimportador.preparar(ruta, hojas=[hoja] if hoja else None)
                print(formatear_preimportacion_i133(resultado))
                print("I1.3.3 no permite importar menús.")
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo preparar I1.3.3: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.3: {exc}")

        elif op == "17":
            ruta = input("Ruta del Excel: ").strip().strip('\"')
            hoja = input("Hoja de menú concreta (vacío=detectar hojas MENU): ").strip()
            hojas = [hoja] if hoja else None
            try:
                resolutor = ResolutorBloqueosPreimportacionI1331(self.core.base_dir)
                resultado = resolutor.recalcular(ruta, hojas=hojas)
                print(formatear_resolucion_i1331(resultado))
                while resultado.get("bloqueos"):
                    print("\nRESOLUCIÓN DE BLOQUEOS")
                    for i, b in enumerate(resultado["bloqueos"], 1):
                        print(f"{i}. {b.get('componente')} | {b.get('rol')} | {b.get('plato')}")
                    sel = input("Bloqueo a resolver (0=terminar): ").strip()
                    if sel == "0":
                        break
                    if not sel.isdigit() or not (1 <= int(sel) <= len(resultado["bloqueos"])):
                        print("Selección no válida.")
                        continue
                    bloqueo = resultado["bloqueos"][int(sel)-1]
                    print("1. Crear y completar receta")
                    print("2. Vincular con receta existente")
                    print("3. Mantener pendiente (continúa bloqueada)")
                    accion = input("Acción: ").strip()
                    if accion == "1":
                        nombre = input(f"Nombre de receta [{bloqueo.get('componente')}]: ").strip() or bloqueo.get('componente')
                        rendimiento_txt = input("Rendimiento base (raciones/unidades): ").strip()
                        rendimiento = float(rendimiento_txt.replace(',', '.'))
                        ingredientes = []
                        print("Añade ingredientes existentes. Escribe FIN cuando hayas terminado.")
                        while True:
                            buscar = input("Buscar artículo: ").strip()
                            if buscar.lower() in {"fin", "f", "terminar"}:
                                break
                            candidatos = resolutor.buscar_articulos(buscar)
                            if not candidatos:
                                print("No se encontraron artículos. Prueba otro nombre.")
                                continue
                            for j, art in enumerate(candidatos, 1):
                                print(f"{j}. {art.get('nombre') or art.get('articulo')} | {art.get('unidad','')} | precio {art.get('precio',0)}")
                            n = input("Número (0=cancelar búsqueda): ").strip()
                            if not n.isdigit() or int(n) == 0 or int(n) > len(candidatos):
                                continue
                            art = candidatos[int(n)-1]
                            cantidad = float(input("Cantidad: ").strip().replace(',', '.'))
                            unidad = input(f"Unidad [{art.get('unidad','')}]: ").strip() or art.get('unidad','')
                            ingredientes.append({'articulo_id': art.get('id') or art.get('articulo_id'), 'nombre': art.get('nombre') or art.get('articulo'), 'cantidad': cantidad, 'unidad': unidad})
                        if not ingredientes:
                            print("Cancelado: una receta completa necesita al menos un ingrediente real.")
                            continue
                        confirmar = self._preguntar_si_no(f"¿Crear la receta '{nombre}' con {len(ingredientes)} ingredientes?", False)
                        if not confirmar:
                            print("Creación cancelada. No se modificaron recetas.")
                            continue
                        r = resolutor.crear_receta(bloqueo, {'nombre': nombre, 'raciones_base': rendimiento, 'ingredientes': ingredientes, 'grupo': bloqueo.get('rol')})
                        print(f"Receta creada: {r['receta']['nombre']} | coste/ración {r['receta']['coste_por_racion']:.4f} €")
                        print(f"Copia de seguridad: {r['backup']}")
                    elif accion == "2":
                        texto = input(f"Buscar receta [{bloqueo.get('componente')}]: ").strip() or bloqueo.get('componente')
                        candidatas = resolutor.buscar_recetas(texto)
                        if not candidatas:
                            print("No se encontraron recetas.")
                            continue
                        for j, rec in enumerate(candidatas, 1):
                            print(f"{j}. {rec.get('nombre')} | coste/ración {rec.get('coste_por_racion',0)}")
                        n = input("Número de receta: ").strip()
                        if not n.isdigit() or not (1 <= int(n) <= len(candidatas)):
                            print("Selección no válida.")
                            continue
                        rec = candidatas[int(n)-1]
                        if self._preguntar_si_no(f"¿Vincular con '{rec.get('nombre')}'?", False):
                            resolutor.vincular_receta(bloqueo, rec.get('receta_id') or rec.get('id'))
                            print("Vínculo guardado en la memoria culinaria.")
                    elif accion == "3":
                        print("El componente se mantiene pendiente y la preimportación continúa bloqueada.")
                    else:
                        print("Acción no válida.")
                        continue
                    resultado = resolutor.recalcular(ruta, hojas=hojas)
                    print("\nPREIMPORTACIÓN RECALCULADA")
                    print(formatear_resolucion_i1331(resultado))
                print("I1.3.3.1 no importa menús. La importación definitiva permanece reservada para I1.3.4.")
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo resolver I1.3.3.1: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.3.1: {exc}")

        elif op == "18":
            try:
                diagnostico = DiagnosticoMURM11(self.core.base_dir)
                resultado = diagnostico.ejecutar()
                print(formatear_diagnostico_m11(resultado))
            except Exception as exc:
                print(f"No se pudo completar el diagnóstico M1.1: {exc}")

        elif op == "19":
            try:
                diagnostico = DiagnosticoResolutorArticulosM12(self.core.base_dir)
                resultado = diagnostico.ejecutar()
                print(formatear_diagnostico_m12(resultado))
            except Exception as exc:
                print(f"No se pudo completar el diagnóstico M1.2: {exc}")

        elif op == "20":
            try:
                diagnostico = DiagnosticoResolutorRecetasM13(self.core.base_dir)
                resultado = diagnostico.ejecutar()
                print(formatear_diagnostico_m13(resultado))
            except Exception as exc:
                print(f"No se pudo completar el diagnóstico M1.3: {exc}")

        elif op == "21":
            try:
                diagnostico = DiagnosticoImportadorRecetasM131(self.core.base_dir)
                resultado = diagnostico.ejecutar()
                print(formatear_diagnostico_m131(resultado))
            except Exception as exc:
                print(f"No se pudo completar el diagnóstico M1.3.1: {exc}")

        elif op == "22":
            try:
                diagnostico = DiagnosticoResolucionIngredientesM132(self.core.base_dir)
                resultado = diagnostico.ejecutar()
                print(formatear_diagnostico_m132(resultado))
            except Exception as exc:
                print(f"No se pudo completar el diagnóstico M1.3.2: {exc}")

        elif op == "23":
            try:
                diagnostico = DiagnosticoValidacionCulinariaM133(self.core.base_dir)
                resultado = diagnostico.ejecutar()
                print(formatear_diagnostico_m133(resultado))
            except Exception as exc:
                print(f"No se pudo completar el diagnóstico M1.3.3: {exc}")

        elif op == "24":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            try:
                simulador = SimuladorImportacionMenusI13411(self.core.base_dir)
                deteccion = simulador.detectar_menus(ruta)
                print(formatear_deteccion_multihoja_i13411(deteccion))
                candidatos = deteccion.get("hojas_confirmadas", []) + deteccion.get("hojas_probables", [])
                if not candidatos:
                    print("No hay menús candidatos para simular.")
                    return
                print("\nA. Simular todos los menús confirmados")
                print("N. Seleccionar uno o varios por número (ejemplo: 1,3,5)")
                print("0. Cancelar")
                modo = input("Selección [A]: ").strip().upper() or "A"
                if modo == "0":
                    print("Simulación cancelada.")
                    return
                if modo == "A":
                    hojas = deteccion.get("hojas_confirmadas", [])
                else:
                    entrada = input("Números separados por comas: ").strip()
                    indices = []
                    for parte in entrada.split(","):
                        parte = parte.strip()
                        if parte.isdigit():
                            indices.append(int(parte))
                    hojas = [candidatos[i-1] for i in indices if 1 <= i <= len(candidatos)]
                    if not hojas:
                        print("No se seleccionó ninguna hoja válida.")
                        return
                resultado = simulador.simular(ruta, hojas=hojas)
                print(formatear_simulacion_i13411(resultado))
            except FileNotFoundError as exc:
                print(f"No se encontró el archivo: {exc}")
            except ValueError as exc:
                print(f"No se pudo preparar I1.3.4.1.1: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.4.1.1: {exc}")

        elif op == "25":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            try:
                simulador = SimuladorImportacionMenusI13412(self.core.base_dir)
                deteccion = simulador.detectar_menus(ruta)
                print(formatear_deteccion_multihoja_i13411(deteccion))
                candidatos = deteccion.get("hojas_confirmadas", []) + deteccion.get("hojas_probables", [])
                if not candidatos:
                    print("No hay menús candidatos para simular.")
                    return
                print("\nA. Simular todos los menús confirmados")
                print("N. Seleccionar uno o varios por número (ejemplo: 1,3,5)")
                print("0. Cancelar")
                modo = input("Selección [A]: ").strip().upper() or "A"
                if modo == "0":
                    print("Simulación cancelada.")
                    return
                if modo == "A":
                    hojas = deteccion.get("hojas_confirmadas", [])
                else:
                    entrada = input("Números separados por comas: ").strip()
                    indices = [int(x.strip()) for x in entrada.split(",") if x.strip().isdigit()]
                    hojas = [candidatos[i-1] for i in indices if 1 <= i <= len(candidatos)]
                    if not hojas:
                        print("No se seleccionó ninguna hoja válida.")
                        return
                resultado = simulador.simular(ruta, hojas=hojas)
                print(formatear_simulacion_i13412(resultado))
            except FileNotFoundError as exc:
                print(f"No se encontró el archivo: {exc}")
            except ValueError as exc:
                print(f"No se pudo preparar I1.3.4.1.2: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.4.1.2: {exc}")

        elif op == "26":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            try:
                bandeja = BandejaRevisionI13413(self.core.base_dir)
                deteccion = bandeja.simulador.detectar_menus(ruta)
                print(formatear_deteccion_multihoja_i13411(deteccion))
                candidatos = deteccion.get("hojas_confirmadas", []) + deteccion.get("hojas_probables", [])
                if not candidatos:
                    print("No hay menús candidatos para revisar.")
                    return
                print("\nA. Revisar todos los menús confirmados")
                print("N. Seleccionar uno o varios por número")
                print("0. Cancelar")
                modo = input("Selección [A]: ").strip().upper() or "A"
                if modo == "0": return
                if modo == "A":
                    hojas = deteccion.get("hojas_confirmadas", [])
                else:
                    entrada = input("Números separados por comas: ").strip()
                    indices = [int(x.strip()) for x in entrada.split(",") if x.strip().isdigit()]
                    hojas = [candidatos[i-1] for i in indices if 1 <= i <= len(candidatos)]
                    if not hojas:
                        print("No se seleccionó ninguna hoja válida."); return
                sesion = bandeja.preparar(ruta, hojas=hojas)
                while True:
                    print("\n" + formatear_bandeja_i13413(sesion))
                    if sesion.get("resumen_revision", {}).get("pendientes", 0) == 0:
                        break
                    accion = input("Acción: ").strip().upper()
                    if accion == "0": break
                    if accion in {"E", "C", "M"}:
                        numeros = input("Números separados por comas: ").strip()
                        if accion == "E": sesion = bandeja.aplicar_masiva(sesion, numeros, "ELIMINAR")
                        elif accion == "M": sesion = bandeja.aplicar_masiva(sesion, numeros, "MANTENER")
                        else:
                            print("Clasificaciones: PLATO_RECETA, PLATO_COMPUESTO, APERITIVO_PREPARADO, ARTICULO_DIRECTO, BEBIDA, VINO, CAVA, AGUA, CAFE_INFUSION, PAN, COMPLEMENTO, SERVICIO")
                            clasif = input("Nueva clasificación: ").strip().upper()
                            sesion = bandeja.aplicar_masiva(sesion, numeros, "CLASIFICAR", clasificacion=clasif)
                    elif accion == "R":
                        numero = int(input("Número: ").strip())
                        nuevo = input("Nuevo nombre: ").strip()
                        recordar = self._preguntar_si_no("¿Recordar esta decisión?", False)
                        sesion = bandeja.renombrar(sesion, numero, nuevo, recordar=recordar)
                    elif accion == "V":
                        numero = int(input("Número: ").strip())
                        tipo = input("Vincular con RECETA o ARTICULO: ").strip().upper()
                        destino = input("Nombre exacto de destino: ").strip()
                        recordar = self._preguntar_si_no("¿Recordar esta decisión?", False)
                        sesion = bandeja.vincular(sesion, numero, tipo, destino, recordar=recordar)
                    else:
                        print("Acción no válida.")
                print("\nRESULTADO FINAL DE LA REVISIÓN")
                print(formatear_bandeja_i13413(sesion, solo_pendientes=False))
                print(f"Sesión guardada en: {sesion.get('ruta_sesion', '')}")
                print("I1.3.4.1.3 no importa menús ni modifica datos de negocio.")
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo preparar I1.3.4.1.3: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.4.1.3: {exc}")

        elif op == "27":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            try:
                bandeja = BandejaRevisionI13414(self.core.base_dir)
                deteccion = bandeja.simulador.detectar_menus(ruta)
                print(formatear_deteccion_multihoja_i13411(deteccion))
                candidatos = deteccion.get("hojas_confirmadas", []) + deteccion.get("hojas_probables", [])
                if not candidatos:
                    print("No hay menús candidatos para interpretar."); return
                print("\nA. Interpretar todos los menús confirmados")
                print("N. Seleccionar uno o varios por número")
                print("0. Cancelar")
                modo = input("Selección [A]: ").strip().upper() or "A"
                if modo == "0": return
                if modo == "A":
                    hojas = deteccion.get("hojas_confirmadas", [])
                else:
                    entrada = input("Números separados por comas: ").strip()
                    indices = [int(x.strip()) for x in entrada.split(",") if x.strip().isdigit()]
                    hojas = [candidatos[i-1] for i in indices if 1 <= i <= len(candidatos)]
                    if not hojas:
                        print("No se seleccionó ninguna hoja válida."); return
                sesion = bandeja.preparar(ruta, hojas=hojas)
                print("\n" + formatear_bandeja_i13414(sesion))
                ic = sesion.get("plan", {}).get("interpretacion_culinaria", {})
                print("\nRESUMEN DEL MOTOR")
                print(f"Platos reinterpretados: {ic.get('platos_interpretados', 0)}")
                print(f"Fragmentos antes: {ic.get('fragmentos_pendientes_antes', 0)} | Conceptos después: {ic.get('conceptos_pendientes_despues', 0)} | Reducción: {ic.get('reduccion', 0)}")
                print("I1.3.4.1.4 no importa menús ni modifica datos de negocio.")
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo preparar I1.3.4.1.4: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.4.1.4: {exc}")

        elif op == "28":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            try:
                bandeja = BandejaRevisionI13415(self.core.base_dir)
                deteccion = bandeja.simulador.detectar_menus(ruta)
                print(formatear_deteccion_multihoja_i13411(deteccion))
                candidatos = deteccion.get("hojas_confirmadas", []) + deteccion.get("hojas_probables", [])
                if not candidatos:
                    print("No hay menús candidatos para analizar."); return
                print("\nA. Analizar todos los menús confirmados")
                print("N. Seleccionar uno o varios por número")
                print("0. Cancelar")
                modo = input("Selección [A]: ").strip().upper() or "A"
                if modo == "0": return
                if modo == "A":
                    hojas = deteccion.get("hojas_confirmadas", [])
                else:
                    entrada = input("Números separados por comas: ").strip()
                    indices = [int(x.strip()) for x in entrada.split(",") if x.strip().isdigit()]
                    hojas = [candidatos[i-1] for i in indices if 1 <= i <= len(candidatos)]
                    if not hojas:
                        print("No se seleccionó ninguna hoja válida."); return
                sesion = bandeja.preparar(ruta, hojas=hojas)
                while True:
                    print("\n" + formatear_bandeja_i13415(sesion))
                    accion = input("Acción: ").strip().upper()
                    if accion == "0": break
                    if accion in {"E", "C", "M"}:
                        numeros = input("Números separados por comas: ").strip()
                        if accion == "E": sesion = bandeja.aplicar_masiva(sesion, numeros, "ELIMINAR")
                        elif accion == "M": sesion = bandeja.aplicar_masiva(sesion, numeros, "MANTENER")
                        else:
                            print("Clasificaciones: PLATO_RECETA, PLATO_COMPUESTO, APERITIVO_PREPARADO, ARTICULO_DIRECTO, BEBIDA, VINO, CAVA, AGUA, CAFE_INFUSION, PAN, COMPLEMENTO, SERVICIO")
                            clasif = input("Nueva clasificación: ").strip().upper()
                            sesion = bandeja.aplicar_masiva(sesion, numeros, "CLASIFICAR", clasificacion=clasif)
                    elif accion == "R":
                        numero = int(input("Número: ").strip())
                        nuevo = input("Nuevo nombre: ").strip()
                        recordar = self._preguntar_si_no("¿Recordar esta decisión?", False)
                        sesion = bandeja.renombrar(sesion, numero, nuevo, recordar=recordar)
                    elif accion == "V":
                        numero = int(input("Número: ").strip())
                        tipo = input("Vincular con RECETA o ARTICULO: ").strip().upper()
                        destino = input("Nombre exacto de destino: ").strip()
                        recordar = self._preguntar_si_no("¿Recordar esta decisión?", False)
                        sesion = bandeja.vincular(sesion, numero, tipo, destino, recordar=recordar)
                    else:
                        print("Acción no válida.")
                print("\nRESULTADO FINAL")
                print(formatear_bandeja_i13415(sesion, solo_pendientes=False))
                print(f"Sesión guardada en: {sesion.get('ruta_sesion', '')}")
                print("I1.3.4.1.5 no importa menús ni modifica datos de negocio.")
            except (FileNotFoundError, ValueError) as exc:
                print(f"No se pudo preparar I1.3.4.1.5: {exc}")
            except Exception as exc:
                print(f"Error inesperado durante I1.3.4.1.5: {exc}")

        elif op == "29":
            try:
                diagnostico = DiagnosticoEscrituraSeguraI1342(self.core.base_dir)
                resultado = diagnostico.ejecutar()
                print(formatear_diagnostico_i1342(resultado))
                print("I1.3.4.2 certifica el motor; la importación real de menús sigue deshabilitada.")
            except Exception as exc:
                print(f"Error durante el diagnóstico I1.3.4.2: {exc}")

        elif op == "30":
            try:
                print("\nI1.3.4.3 — IMPORTACIÓN DEFINITIVA DE MENÚS")
                print("D. Ejecutar diagnóstico aislado")
                print("R. Importar una sesión revisada y lista")
                modo = input("Modo [D]: ").strip().upper() or "D"
                if modo == "D":
                    diagnostico = DiagnosticoImportacionMenusI1343(self.core.base_dir)
                    resultado = diagnostico.ejecutar()
                    print(formatear_diagnostico_i1343(resultado))
                    print("El diagnóstico usa un catálogo aislado y no modifica DATOS/db/menus.json.")
                elif modo == "R":
                    ruta_sesion = input("Ruta del JSON de sesión revisada: ").strip().strip('\"')
                    importador = ImportadorDefinitivoMenusI1343(self.core.base_dir)
                    sesion = importador.cargar_sesion_revisada(ruta_sesion)
                    plan = sesion["plan"]
                    resumen = sesion["resumen_revision"]
                    print(
                        f"Plan: {plan.get('plan_id')} | Estado: {plan.get('estado_simulacion')} "
                        f"| Pendientes: {resumen.get('pendientes', 0)} "
                        f"| Bloqueantes: {resumen.get('bloqueantes', 0)}"
                    )
                    print(f"Sesión validada: {sesion.get('_ruta_validada', ruta_sesion)}")
                    confirmacion = input("Escribe IMPORTAR para confirmar la escritura real: ").strip()
                    if confirmacion != "IMPORTAR":
                        print("Importación cancelada. No se modificó ningún dato.")
                    else:
                        resultado = importador.importar(plan, confirmar=True, idempotency_key=plan.get("plan_id"))
                        tx = resultado["resultado_transaccion"]
                        ri = resultado["resumen_importacion"]
                        print(f"Estado: {tx['estado']} | Menús creados: {ri['creados']} | Actualizados: {ri['actualizados']} | Total: {resultado['menus_totales']}")
                        print(f"Backup: {tx['backup_dir']} | Integridad: {'OK' if tx['integridad_ok'] else 'ERROR'}")
                else:
                    print("Modo no válido.")
            except Exception as exc:
                print(f"Error durante I1.3.4.3: {exc}")

        elif op == "31":
            try:
                print("\nI1.3.4.4 — AUDITORÍA E INTEGRIDAD POSTIMPORTACIÓN")
                print("D. Ejecutar diagnóstico aislado")
                print("R. Auditar DATOS/db/menus.json real (solo lectura)")
                modo = input("Modo [D]: ").strip().upper() or "D"
                if modo == "D":
                    resultado = DiagnosticoAuditoriaPostimportacionI1344(self.core.base_dir).ejecutar()
                    print(formatear_diagnostico_i1344(resultado))
                elif modo == "R":
                    resultado = AuditorIntegridadPostimportacionI1344(self.core.base_dir).auditar(guardar_informe=True)
                    print(formatear_auditoria_i1344(resultado, detalle=True))
                else:
                    print("Modo no válido.")
            except Exception as exc:
                print(f"Error durante I1.3.4.4: {exc}")

        elif op == "32":
            try:
                print("\nI1.3.4.4.1 — BANDEJA DE CORRECCIÓN POSTIMPORTACIÓN")
                print("D. Ejecutar diagnóstico aislado")
                print("R. Corregir DATOS/db/menus.json real")
                modo = input("Modo [D]: ").strip().upper() or "D"
                if modo == "D":
                    resultado = DiagnosticoBandejaCorreccionI13441(self.core.base_dir).ejecutar()
                    print(formatear_diagnostico_i13441(resultado))
                elif modo == "R":
                    bandeja = BandejaCorreccionPostimportacionI13441(self.core.base_dir)
                    while True:
                        print(formatear_bandeja_i13441(bandeja))
                        accion = input("Acción: ").strip().upper()
                        if accion == "0":
                            print("Sesión cerrada sin guardar cambios reales.")
                            break
                        if accion in {"E", "S", "M", "A"}:
                            texto = input("Números separados por comas (vacío=todos para A): ").strip()
                            indices = [int(x.strip()) for x in texto.split(',') if x.strip().isdigit()]
                            if accion == "E":
                                print(bandeja.eliminar(indices))
                            elif accion == "S":
                                nueva = input("Nueva sección: ").strip()
                                print(f"Secciones actualizadas: {bandeja.cambiar_seccion(indices, nueva)}")
                            elif accion == "M":
                                bandeja.aceptar(indices); print("Decisión registrada; la incidencia seguirá visible si continúa vigente.")
                            elif accion == "A":
                                print(f"Menús recalculados: {bandeja.recalcular_economia(indices or None)}")
                        elif accion == "R":
                            idx = int(input("Número de incidencia: ").strip())
                            nuevo = input("Nuevo nombre: ").strip()
                            bandeja.renombrar(idx, nuevo)
                        elif accion == "V":
                            idx = int(input("Número de incidencia: ").strip())
                            tipo = input("Vincular con R=receta o A=artículo: ").strip().upper()
                            texto = input("Buscar: ").strip()
                            candidatos = bandeja.buscar_recetas(texto) if tipo == "R" else bandeja.buscar_articulos(texto)
                            if not candidatos:
                                print("No se encontraron candidatos. Crea la entidad desde su módulo oficial y vuelve a intentarlo.")
                                continue
                            for i, c in enumerate(candidatos, 1):
                                print(f"{i}. {c.get('nombre') or c.get('articulo')} | {c.get('receta_id') or c.get('codigo') or c.get('id')}")
                            sel = int(input("Selecciona candidato: ").strip())
                            elegido = candidatos[sel-1]
                            bandeja.vincular_receta(idx, elegido) if tipo == "R" else bandeja.vincular_articulo(idx, elegido)
                        elif accion == "G":
                            print(formatear_bandeja_i13441(bandeja))
                            confirmar = input("Escribe GUARDAR para aplicar los cambios reales: ").strip()
                            if confirmar != "GUARDAR":
                                print("Guardado cancelado. No se modificó el catálogo real.")
                                continue
                            resultado = bandeja.guardar(confirmar=True)
                            tx = resultado["transaccion"]; aud = resultado["auditoria"]
                            print(f"Estado: {tx['estado']} | Backup: {tx['backup_dir']} | Integridad: {'OK' if tx['integridad_ok'] else 'ERROR'}")
                            print(formatear_auditoria_i1344(aud, detalle=True))
                            break
                        else:
                            print("Acción no válida.")
                else:
                    print("Modo no válido.")
            except Exception as exc:
                print(f"Error durante I1.3.4.4.1: {exc}")


        elif op == "33":
            try:
                print("\nI1.3.4.4.2 — CORRECCIÓN INTELIGENTE MASIVA Y NAVEGACIÓN")
                print("D. Ejecutar diagnóstico aislado")
                print("R. Corregir DATOS/db/menus.json real")
                modo = input("Modo [D]: ").strip().upper() or "D"
                if modo == "D":
                    resultado = DiagnosticoCorreccionInteligenteI13442(self.core.base_dir).ejecutar()
                    print(formatear_diagnostico_i13442(resultado))
                elif modo == "R":
                    bandeja = BandejaCorreccionInteligenteI13442(self.core.base_dir)
                    vista, valor = "TODAS", None
                    while True:
                        print(formatear_navegacion_i13442(bandeja, vista=vista, valor=valor))
                        accion = input("Acción: ").strip().upper()
                        if accion == "0":
                            print("Sesión cerrada sin guardar cambios reales.")
                            break
                        if accion == "X":
                            r = bandeja.resolver_automaticamente_univocos()
                            print(f"Resueltas automáticamente: {r['resueltas']} | Omitidas por seguridad: {r['omitidas']}")
                        elif accion == "F":
                            print("1=Todas | 2=Solo errores | 3=Solo avisos | 4=Por tipo | 5=Por menú")
                            sel = input("Filtro: ").strip()
                            if sel == "1": vista, valor = "TODAS", None
                            elif sel == "2": vista, valor = "ERRORES", None
                            elif sel == "3": vista, valor = "AVISOS", None
                            elif sel == "4":
                                valor = input("Código exacto de incidencia: ").strip().upper(); vista = "TIPO"
                            elif sel == "5":
                                valor = input("Texto del nombre del menú: ").strip(); vista = "MENU"
                        elif accion == "T":
                            print(formatear_grupos_tipo_i13442(bandeja))
                        elif accion == "U":
                            print(formatear_grupos_menu_i13442(bandeja))
                        elif accion == "B":
                            print("1=Por tipo | 2=Por menú")
                            modo_m = input("Agrupar acción por: ").strip()
                            if modo_m == "1":
                                clave = input("Código exacto: ").strip().upper()
                                indices = bandeja.indices_por_codigo(clave)
                            else:
                                clave = input("Nombre o parte del menú: ").strip()
                                indices = bandeja.indices_por_menu(clave)
                            print(f"Incidencias seleccionadas: {indices}")
                            if not indices:
                                continue
                            sub = input("Acción E=Eliminar | S=Sección | A=Economía | M=Mantener: ").strip().upper()
                            if sub == "E": print(bandeja.eliminar(indices))
                            elif sub == "S":
                                nueva = input("Nueva sección: ").strip()
                                print(f"Secciones actualizadas: {bandeja.cambiar_seccion(indices, nueva)}")
                            elif sub == "A": print(f"Menús recalculados: {bandeja.recalcular_economia(indices)}")
                            elif sub == "M": bandeja.aceptar(indices); print("Decisiones registradas.")
                        elif accion in {"E", "S", "M", "A"}:
                            texto = input("Números separados por comas (vacío=todos para A): ").strip()
                            indices = [int(x.strip()) for x in texto.split(',') if x.strip().isdigit()]
                            if accion == "E": print(bandeja.eliminar(indices))
                            elif accion == "S":
                                nueva = input("Nueva sección: ").strip()
                                print(f"Secciones actualizadas: {bandeja.cambiar_seccion(indices, nueva)}")
                            elif accion == "M": bandeja.aceptar(indices); print("Decisiones registradas.")
                            elif accion == "A": print(f"Menús recalculados: {bandeja.recalcular_economia(indices or None)}")
                        elif accion == "R":
                            idx = int(input("Número de incidencia: ").strip())
                            nuevo = input("Nuevo nombre: ").strip()
                            bandeja.renombrar(idx, nuevo)
                        elif accion == "V":
                            idx = int(input("Número de incidencia: ").strip())
                            tipo = input("Vincular con R=receta o A=artículo: ").strip().upper()
                            texto = input("Buscar: ").strip()
                            candidatos = bandeja.buscar_recetas(texto) if tipo == "R" else bandeja.buscar_articulos(texto)
                            if not candidatos:
                                print("No se encontraron candidatos. Crea la entidad desde su módulo oficial y vuelve a intentarlo.")
                                continue
                            for i, c in enumerate(candidatos, 1):
                                print(f"{i}. {c.get('nombre') or c.get('articulo')} | {c.get('receta_id') or c.get('codigo') or c.get('id')}")
                            sel = int(input("Selecciona candidato: ").strip())
                            elegido = candidatos[sel-1]
                            bandeja.vincular_receta(idx, elegido) if tipo == "R" else bandeja.vincular_articulo(idx, elegido)
                        elif accion == "G":
                            print(formatear_navegacion_i13442(bandeja, vista="TODAS"))
                            confirmar = input("Escribe GUARDAR para aplicar los cambios reales: ").strip()
                            if confirmar != "GUARDAR":
                                print("Guardado cancelado. No se modificó el catálogo real.")
                                continue
                            resultado = bandeja.guardar(confirmar=True)
                            tx = resultado["transaccion"]; aud = resultado["auditoria"]
                            print(f"Estado: {tx['estado']} | Backup: {tx['backup_dir']} | Integridad: {'OK' if tx['integridad_ok'] else 'ERROR'}")
                            print(formatear_auditoria_i1344(aud, detalle=True))
                            break
                        else:
                            print("Acción no válida.")
                else:
                    print("Modo no válido.")
            except Exception as exc:
                print(f"Error durante I1.3.4.4.2: {exc}")

        elif op == "34":
            try:
                resultado = CertificadorFinalImportadorI135(self.core.base_dir).ejecutar()
                print(formatear_certificacion_i135(resultado))
            except Exception as exc:
                print(f"Error durante I1.3.5: {exc}")

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
            print("No hay un evento seleccionado para preparar.")
            print("Siguiente paso: vuelve a Eventos y elige 'Buscar o listar eventos'.")
            return False
        try:
            self.core.eventos.obtener(self.ultimo_evento_id)
        except Exception:
            self.ultimo_evento_id = None
            print("El evento que estaba seleccionado ya no está disponible.")
            print("Siguiente paso: vuelve a Eventos y busca otro evento.")
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
