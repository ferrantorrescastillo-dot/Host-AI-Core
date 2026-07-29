from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Callable
import logging
import os

from APP.consola import AppConsolaHostAI
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.contexto_activo_host_ai import ServicioContextoActivoHostAI
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService


LOGGER = logging.getLogger("host_ai.app.shell")


@dataclass
class NotificacionShell:
    tipo: str
    texto: str


@dataclass
class ActivityItem:
    activity_type: str
    message: str
    timestamp: str
    module: str = ""
    status: str = "ok"
    navigation_target: str = ""
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_chat(cls, raw: dict[str, Any]) -> "ActivityItem | None":
        if not isinstance(raw, dict):
            return None
        message = str(raw.get("mensaje") or raw.get("texto") or "").strip()
        if not message:
            return None
        tipo = str(raw.get("tipo_mensaje") or raw.get("tipo") or raw.get("rol") or "ACTIVIDAD").upper()
        timestamp = str(raw.get("timestamp") or datetime.now().isoformat(timespec="seconds"))
        datos = dict(raw.get("datos") or {})
        nav = dict(datos.get("navigation_request") or {})
        return cls(
            activity_type=tipo,
            message=message,
            timestamp=timestamp,
            module=str(nav.get("target_module") or ""),
            status="ok" if bool(raw.get("ok", True)) else "error",
            navigation_target=str(nav.get("target_module") or ""),
            metadata={"rol": str(raw.get("rol") or "")},
        )


class AppShellHostAI:
    """Shell visual de transicion para la aplicacion definitiva.

    Reutiliza modulos existentes por delegacion y no implementa logica de
    negocio nueva.
    """

    SIDEBAR_ITEMS = [
        "1. Inicio / Host AI",
        "2. Eventos",
        "3. Produccion",
        "4. Compras",
        "5. Stock",
        "6. Recetas y Escandallos",
        "7. Menus",
        "8. Catalogo",
        "9. Importaciones",
        "10. Incidencias",
        "11. Estadisticas",
        "12. Configuracion",
        "0. Volver",
    ]

    QUICK_ACTIONS = {
        "1": "Revisar incidencias",
        "2": "Buscar receta",
        "3": "Ver escandallos desactualizados",
        "4": "Ver produccion",
        "5": "Revisar compras",
        "6": "Importar documento",
        "0": "Volver",
    }

    MODULE_TO_SIDEBAR = {
        "HOME": "1",
        "EVENTOS": "2",
        "PRODUCCION": "3",
        "COMPRAS": "4",
        "STOCK": "5",
        "RECETAS_ESCANDALLOS": "6",
        "MENUS": "7",
        "CATALOGO": "8",
        "IMPORTACIONES": "9",
        "INCIDENCIAS": "10",
        "ESTADISTICAS": "11",
        "CONFIGURACION": "12",
    }

    SIDEBAR_TO_CONTEXT = {
        "1": "HOME",
        "2": "EVENTO",
        "3": "PRODUCCION",
        "4": "COMPRAS",
        "5": "STOCK",
        "6": "RECETA",
        "7": "MENU",
        "8": "CATALOGO",
        "9": "IMPORTACIONES",
        "10": "INCIDENCIAS",
        "11": "ESTADISTICAS",
        "12": "CONFIGURACION",
    }

    def __init__(self, core, app: AppConsolaHostAI | None = None):
        self.core = core
        self.app = app or AppConsolaHostAI(core)
        self.contexto = ServicioContextoActivoHostAI()
        self.home_read = HostAIHomeReadService(self.core)
        self.chat = ServicioChatHostAIShell(self.core.orquestador, home_read_service=self.home_read)
        self.notificaciones: list[NotificacionShell] = []
        self._home_cache: dict[str, object] = {}
        self._active_sidebar = "1"
        self._ultima_accion_navegacion = ""
        self._pending_navigation_request: dict[str, Any] | None = None
        self._dev_mode = str(os.getenv("HOST_AI_DEV_MODE", "1")).strip() in {"1", "true", "TRUE", "yes", "YES"}

    def ejecutar(self, input_fn: Callable[[str], str] = input, print_fn: Callable[..., None] = print) -> None:
        while True:
            self._render_shell(print_fn)
            opcion = input_fn("Navegacion (0-12, c=chat, q=acciones): ").strip().lower()
            if opcion == "0":
                print_fn("Saliendo del shell de aplicacion.")
                return
            if opcion == "c":
                self._chat_panel(input_fn, print_fn)
                self._procesar_navegacion_pendiente(print_fn)
                continue
            if opcion == "q":
                self._acciones_rapidas(input_fn, print_fn)
                continue
            self._navegar(opcion, print_fn)

    def _render_shell(self, print_fn) -> None:
        self._home_cache = self.home_read.cargar_home()
        print_fn("\n" + "=" * 88)
        print_fn("HOST AI APP SHELL - APP-01.5")
        print_fn("Modulo de apoyo dentro de la ruta oficial de arranque")
        print_fn("=" * 88)
        print_fn(self._header_status())
        print_fn("-" * 88)
        print_fn("SIDEBAR")
        for item in self.SIDEBAR_ITEMS:
            codigo = item.split(".", 1)[0]
            marca = "*" if codigo == self._active_sidebar else " "
            print_fn(f"{marca} {item}")
        print_fn("-" * 88)
        print_fn("MAIN CONTENT - HOST AI HOME")
        self._render_home(print_fn)
        print_fn("-" * 88)
        print_fn("HOST AI PANEL")
        self._render_chat_preview(print_fn)
        print_fn("-" * 88)
        print_fn("NOTIFICATIONS")
        if not self.notificaciones:
            print_fn("- Sin notificaciones")
        else:
            for n in self.notificaciones[-5:]:
                print_fn(f"- [{n.tipo}] {n.texto}")

    def _header_status(self) -> str:
        contexto = self.contexto.obtener()
        proveedor = "SIMULADO"
        entorno = "PILOTO_PRIVADO"
        estado_home = str((self._home_cache or {}).get("estado_global") or "sin_cargar")
        return (
            f"Entorno: {entorno} | Proveedor IA: {proveedor} | "
            f"Contexto activo: {contexto.etiqueta} | Home: {estado_home}"
        )

    def _render_home(self, print_fn) -> None:
        print_fn("Saludo: Bienvenido. Estado general estable para operativa diaria.")
        print_fn("Caja de entrada: usa 'c' para conversar con Host AI.")
        print_fn("Bandeja Inteligente (determinista):")
        bandeja = list((self._home_cache.get("bandeja") or []))
        if not bandeja:
            print_fn("- Sin alertas operativas en este momento.")
        else:
            for idx, item in enumerate(bandeja[:6], 1):
                print_fn(
                    f"- [{idx}] ({item.get('severidad')}) {item.get('titulo')}"
                    f" -> ir {item.get('accion_navegacion')}"
                )
        print_fn("Acciones rapidas: usa 'q' para abrirlas.")
        print_fn("Actividad reciente:")
        historial = self.chat.historial()
        if not historial:
            print_fn("- Sin actividad conversacional en esta sesion.")
        else:
            items: list[ActivityItem] = []
            for m in historial[-3:]:
                item = ActivityItem.from_chat(m)
                if item is None:
                    LOGGER.warning("activity_malformed %s", {"item": str(m)[:200]})
                    continue
                items.append(item)
            if not items:
                print_fn("- Actividad no disponible.")
            else:
                for item in items:
                    print_fn(f"- {item.activity_type}: {item.message}")
        print_fn("Indicadores de Home (solo lectura):")
        indicadores = list((self._home_cache.get("indicadores") or []))
        for ind in indicadores:
            print_fn(
                f"- {ind.get('titulo')}: {ind.get('cantidad')} | "
                f"estado={ind.get('estado')} | ir {ind.get('accion_navegacion')}"
            )
        if (self._home_cache.get("errores") or []):
            print_fn("Estado parcial: algunos modulos no estan disponibles.")
        sesion = self.chat.estado_sesion()
        contexto_lineas = []
        receta = dict(sesion.get("receta_activa") or {})
        escandallo = dict(sesion.get("escandallo_activo") or {})
        evento = dict(sesion.get("evento_activo") or {})
        menu = dict(sesion.get("menu_activo") or {})
        if receta:
            contexto_lineas.append(f"Receta: {receta.get('nombre') or receta.get('codigo') or receta.get('id')}")
        if escandallo:
            contexto_lineas.append(f"Escandallo: {escandallo.get('nombre') or escandallo.get('codigo') or escandallo.get('id')}")
        if evento:
            contexto_lineas.append(f"Evento: {evento.get('nombre') or evento.get('id')}")
        if menu:
            contexto_lineas.append(f"Menu: {menu.get('nombre') or menu.get('codigo') or menu.get('id')}")
        if contexto_lineas:
            print_fn("Contexto actual:")
            for linea in contexto_lineas:
                print_fn(f"- {linea}")

        if self._dev_mode:
            stats = dict(self.chat.platform_stats() or {})
            print_fn("Host AI Platform (dev):")
            print_fn(f"- Herramientas registradas: {stats.get('total', 0)}")
            tipos = dict(stats.get("por_tipo") or {})
            for key in ["READ", "WRITE", "NAVIGATION", "ANALYSIS", "IMPORT", "SYSTEM"]:
                print_fn(f"- {key}: {int(tipos.get(key, 0))}")

    def _render_chat_preview(self, print_fn) -> None:
        historial = self.chat.historial()
        sesion = self.chat.estado_sesion()
        if not historial:
            print_fn("- Sin mensajes. Abre el chat con 'c'.")
        else:
            ultimo = historial[-1]
            tipo = str(ultimo.get("tipo_mensaje") or ultimo.get("tipo") or "ACTIVIDAD")
            texto = str(ultimo.get("mensaje") or ultimo.get("texto") or "Actividad no disponible")
            print_fn(f"- Ultimo mensaje ({tipo}): {texto}")
        print_fn(f"- Procesando: {'si' if self.chat.esta_procesando() else 'no'}")
        print_fn(f"- Contexto activo: {sesion.get('contexto_activo') or 'HOME'}")
        print_fn(f"- Ultimo modulo: {sesion.get('ultimo_modulo') or '-'}")
        ultimo_objeto = dict(sesion.get("ultimo_elemento_seleccionado") or {})
        objeto_label = ultimo_objeto.get("nombre") or ultimo_objeto.get("codigo") or ultimo_objeto.get("id") or "-"
        print_fn(f"- Ultimo objeto: {objeto_label}")
        print_fn(f"- Ultima busqueda: {sesion.get('ultima_busqueda') or '-'}")
        print_fn(f"- Ultima accion de navegacion: {self._ultima_accion_navegacion or 'ninguna'}")
        print_fn(f"- Ultima intencion: {sesion.get('ultima_intencion') or '-'}")
        print_fn("- Proveedor activo: SIMULADO")

    def _chat_panel(self, input_fn, print_fn) -> None:
        print_fn("\nCHAT HOST AI (simulado). Enter vacio para volver. '/clear' limpia sesion. '/volver' o '/salir' para volver al shell.")
        while True:
            texto = input_fn("Tu: ")
            if not texto.strip():
                return
            comando = texto.strip().lower()
            if comando in {"/volver", "/salir"}:
                return
            if comando == "/clear":
                self.chat.limpiar()
                self.contexto.establecer_general()
                self.notificaciones.append(NotificacionShell("SISTEMA", "Conversacion limpiada en sesion."))
                print_fn("Host AI: Conversacion limpiada.")
                continue
            respuesta = self.chat.enviar(texto, contexto=self.contexto.obtener().to_dict())
            print_fn(f"Host AI [{respuesta['tipo_mensaje']}]: {respuesta['mensaje']}")
            if self._gestionar_respuesta_chat(respuesta, input_fn, print_fn):
                return
            if not respuesta.get("ok"):
                self.notificaciones.append(NotificacionShell("ERROR", "No se pudo completar la consulta solicitada."))

    def _acciones_rapidas(self, input_fn, print_fn) -> None:
        print_fn("\nACCIONES RAPIDAS")
        for k, v in self.QUICK_ACTIONS.items():
            print_fn(f"{k}. {v}")
        op = input_fn("Elige accion: ").strip()
        if op == "1":
            self._navegar("10", print_fn)
        elif op == "2":
            self.chat.enviar("muestrame las recetas pendientes", contexto=self.contexto.obtener().to_dict())
            self._navegar("6", print_fn)
        elif op == "3":
            self.chat.enviar("qué escandallos están desactualizados", contexto=self.contexto.obtener().to_dict())
            self._navegar("6", print_fn)
        elif op == "4":
            self._navegar("3", print_fn)
        elif op == "5":
            self._navegar("4", print_fn)
        elif op == "6":
            self._navegar("9", print_fn)

    def _navegar(self, opcion: str, print_fn) -> None:
        if opcion == "1":
            self._active_sidebar = "1"
            self.contexto.establecer("HOME", etiqueta="Contexto home", origen="shell")
            self.chat.actualizar_contexto_activo("HOME")
            return

        previa = self._active_sidebar
        contexto_previo = self.contexto.obtener()
        self._active_sidebar = opcion
        contexto_objetivo = str(self.SIDEBAR_TO_CONTEXT.get(opcion) or "HOME")
        self.contexto.establecer(contexto_objetivo, etiqueta=f"Contexto {contexto_objetivo.lower()}", origen="shell")
        self.chat.actualizar_contexto_activo(contexto_objetivo)
        try:
            self._abrir_modulo(opcion, print_fn)
        except Exception as exc:
            self.notificaciones.append(NotificacionShell("ERROR", f"No se pudo abrir el modulo: {opcion}."))
            LOGGER.exception("open_module_error %s", {"opcion": opcion, "error": str(exc)})
            print_fn("No se pudo abrir el modulo solicitado.")
        finally:
            self._active_sidebar = previa
            self.contexto.establecer(
                contexto_previo.tipo,
                entidad_id=contexto_previo.entidad_id,
                etiqueta=contexto_previo.etiqueta,
                origen=contexto_previo.origen,
                metadatos=contexto_previo.metadatos,
            )
            self.chat.actualizar_contexto_activo(str(self.SIDEBAR_TO_CONTEXT.get(previa) or "HOME"))

    def _abrir_modulo(self, opcion: str, print_fn) -> None:
        if opcion == "2":
            self.app._menu_eventos()
            return
        if opcion == "3":
            self.app._menu_produccion_real()
            return
        if opcion == "4":
            self.app._menu_compras()
            return
        if opcion == "5":
            self.app._menu_stock()
            return
        if opcion == "6":
            self.app._menu_escandallos_recetas()
            return
        if opcion == "7":
            self._fallback_pendiente("Menus", "Acceso temporal por Recetas y Escandallos.", print_fn)
            self.app._menu_escandallos_recetas()
            return
        if opcion == "8":
            self._fallback_pendiente("Catalogo", "Pendiente de integracion visual directa.", print_fn)
            return
        if opcion == "9":
            self.app._menu_excel()
            return
        if opcion == "10":
            self._fallback_pendiente("Incidencias", "Pendiente de panel dedicado.", print_fn)
            return
        if opcion == "11":
            self._fallback_pendiente("Estadisticas", "Usa paneles actuales por modulo.", print_fn)
            return
        if opcion == "12":
            from APP.consola_configuracion_restaurante import ConsolaConfiguracionRestaurante

            ConsolaConfiguracionRestaurante(self.app.core.base_dir).ejecutar()
            return
        print_fn("Opcion no valida.")

    def _fallback_pendiente(self, modulo: str, mensaje: str, print_fn) -> None:
        texto = f"{modulo}: {mensaje}"
        self.notificaciones.append(NotificacionShell("ADVERTENCIA", texto))
        print_fn(texto)

    def _gestionar_respuesta_chat(self, respuesta: dict[str, Any], input_fn, print_fn) -> bool:
        datos = dict(respuesta.get("datos") or {})
        nav = dict(datos.get("navigation_request") or {})
        if nav:
            self._pending_navigation_request = nav
            destino = str(nav.get("target_module") or "modulo")
            self._ultima_accion_navegacion = destino
            self.notificaciones.append(NotificacionShell("SISTEMA", f"Navegacion solicitada desde chat a {destino}."))
            print_fn("Host AI: Vuelvo al shell para ejecutar la navegacion solicitada.")
            return True

        acciones = list(datos.get("suggested_actions") or [])
        if not acciones:
            return False

        print_fn("Acciones disponibles:")
        for idx, accion in enumerate(acciones, 1):
            print_fn(f"{idx}. {accion.get('label') or 'Accion'}")
        print_fn("0. Seguir conversando")
        seleccion = input_fn("Elige accion: ").strip().lower()
        if seleccion == "0" or not seleccion:
            return False
        if not seleccion.isdigit():
            print_fn("Host AI: Accion no valida. Seguimos conversando.")
            return False

        idx = int(seleccion) - 1
        if idx < 0 or idx >= len(acciones):
            print_fn("Host AI: Accion no disponible. Seguimos conversando.")
            return False
        nav_sel = dict((acciones[idx] or {}).get("navigation_request") or {})
        if not nav_sel:
            print_fn("Host AI: Esta accion todavia no esta disponible.")
            return False

        self._pending_navigation_request = nav_sel
        destino = str(nav_sel.get("target_module") or "modulo")
        self._ultima_accion_navegacion = destino
        self.notificaciones.append(NotificacionShell("SISTEMA", f"Navegacion solicitada desde chat a {destino}."))
        print_fn("Host AI: De acuerdo. Vuelvo al shell para abrir el modulo.")
        return True

    def _procesar_navegacion_pendiente(self, print_fn) -> None:
        req = dict(self._pending_navigation_request or {})
        self._pending_navigation_request = None
        if not req:
            return
        self.chat.aplicar_navigation_request(req)
        destino = str(req.get("target_module") or "").upper()
        sidebar = str(self.MODULE_TO_SIDEBAR.get(destino) or "")
        if not sidebar:
            self.notificaciones.append(NotificacionShell("ADVERTENCIA", "No se pudo resolver el destino de navegacion."))
            LOGGER.warning("navigation_request_invalid %s", {"request": req})
            return
        self._navegar(sidebar, print_fn)


__all__ = ["AppShellHostAI", "NotificacionShell"]
