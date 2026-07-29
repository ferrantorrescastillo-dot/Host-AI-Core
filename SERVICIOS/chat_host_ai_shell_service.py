from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import logging
import time
import unicodedata

from SERVICIOS.host_ai_deterministic_intent_router import (
    HostAIDeterministicIntentRouter,
    INTENT_ABRIR_REFERENCIA_RESULTADO,
    INTENT_AYUDA,
    INTENT_ABRIR_MODULO,
    INTENT_BUSCAR_RECETA,
    INTENT_CONSULTAR_MARGEN_ACTUAL,
    INTENT_DESCONOCIDA,
    INTENT_LISTAR_ESCANDALLOS_DESACTUALIZADOS,
    INTENT_LISTAR_INCIDENCIAS,
    INTENT_LISTAR_RECETAS_PENDIENTES,
    INTENT_MOSTRAR_ESCANDALLO_ACTUAL,
    INTENT_MOSTRAR_ESTADO_GENERAL,
    INTENT_MOSTRAR_EVENTOS_PROXIMOS,
    INTENT_MOSTRAR_MENU_ACTUAL,
)
from SERVICIOS.host_ai_session_context import HostAISessionContext
from SERVICIOS.host_ai_executive import (
    HostAIExecutive,
    EXEC_INTENCION_BLOQUEO_PRODUCCION,
    EXEC_INTENCION_DESBLOQUEO,
    EXEC_INTENCION_IMPACTO_COMPRAS,
    EXEC_INTENCION_IMPACTO_GENERAL,
    EXEC_INTENCION_IMPACTO_PRODUCCION,
    EXEC_INTENCION_MOTIVO_PRIORIDAD,
    EXEC_INTENCION_PLAN_DIA,
    EXEC_INTENCION_PLAN_OPERATIVO,
    EXEC_INTENCION_RESTAURANTE,
    detectar_intencion_executive,
    formatear_respuesta_executive_conversacional,
)
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.host_ai_tool_resolver import HostAIToolResolver


LOGGER = logging.getLogger("host_ai.app.chat")


TIPO_USUARIO = "USUARIO"
TIPO_HOST_AI = "HOST_AI"
TIPO_EXPLICACION = "EXPLICACION"
TIPO_AYUDA = "AYUDA"
TIPO_ADVERTENCIA = "ADVERTENCIA"
TIPO_INCIDENCIA = "INCIDENCIA"
TIPO_PROPUESTA = "PROPUESTA"
TIPO_CONFIRMACION = "CONFIRMACION"
TIPO_RESULTADO = "RESULTADO"
TIPO_ERROR = "ERROR"
TIPO_SISTEMA = "SISTEMA"


@dataclass
class MensajeChatHostAI:
    rol: str
    tipo: str
    texto: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    datos: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NavigationRequest:
    target_module: str
    target_view: str = ""
    filter_data: dict[str, Any] = field(default_factory=dict)
    entity_id: str = ""
    source: str = "chat_host_ai"
    preserve_chat_session: bool = True
    message: str = ""
    context_update: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ServicioChatHostAIShell:
    """Servicio de chat para APP shell.

    La UI no habla con proveedores directamente. Toda peticion pasa por
    Orquestador -> Host AI Engine -> proveedor SIMULADO.
    """

    def __init__(self, orquestador: Any, home_read_service: Any | None = None):
        self.orquestador = orquestador
        self.home_read_service = home_read_service
        self.router = HostAIDeterministicIntentRouter()
        self.tool_registry = build_default_tool_registry()
        self.tool_resolver = HostAIToolResolver()
        self.tool_executor = HostAIToolExecutor(self.tool_registry, home_read_service=self.home_read_service)
        self._mensajes: list[MensajeChatHostAI] = []
        self._procesando = False
        self._session = HostAISessionContext()
        self._sidebar_to_module = {
            "1": "HOME",
            "2": "EVENTOS",
            "3": "PRODUCCION",
            "4": "COMPRAS",
            "5": "STOCK",
            "6": "RECETAS_ESCANDALLOS",
            "7": "MENUS",
            "8": "CATALOGO",
            "9": "IMPORTACIONES",
            "10": "INCIDENCIAS",
            "11": "ESTADISTICAS",
            "12": "CONFIGURACION",
        }
        self._module_to_sidebar = {v: k for k, v in self._sidebar_to_module.items()}

    def historial(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._mensajes]

    def limpiar(self) -> None:
        self._mensajes.clear()
        self._procesando = False
        self._session.reset()

    def esta_procesando(self) -> bool:
        return self._procesando

    def enviar(self, texto: str, contexto: dict[str, Any] | None = None) -> dict[str, Any]:
        inicio = time.perf_counter()
        contenido = str(texto or "").strip()
        if not contenido:
            msg = MensajeChatHostAI(rol="sistema", tipo=TIPO_SISTEMA, texto="Escribe un mensaje para continuar.")
            self._mensajes.append(msg)
            return self._normalizar(msg)

        self._mensajes.append(MensajeChatHostAI(rol="usuario", tipo=TIPO_USUARIO, texto=contenido))
        self._procesando = True
        try:
            engine = self._consultar_engine_simulado(contenido, contexto)
            if str(engine.get("estado") or "") == "ERROR":
                # Executive conversacional no depende de proveedor generativo; mantener ruta determinista local.
                if detectar_intencion_executive(contenido) is not None:
                    engine = {"estado": "OK", "proveedor": "SIMULADO", "respuesta": {}, "errores": []}
                else:
                    msg = self._mensaje_engine(engine)
                    salida = MensajeChatHostAI(rol="host_ai", tipo=TIPO_ERROR, texto=msg, datos={"engine": engine})
                    self._mensajes.append(salida)
                    return self._normalizar(salida)

            respuesta = self._resolver_intencion(contenido, dict(contexto or {}), engine)
            salida = MensajeChatHostAI(
                rol="host_ai",
                tipo=str(respuesta.get("tipo_mensaje") or TIPO_RESULTADO),
                texto=str(respuesta.get("mensaje") or ""),
                datos=dict(respuesta.get("datos") or {}),
            )
            self._mensajes.append(salida)
            self._registrar_log(contenido, respuesta, inicio)
            return self._normalizar(salida)
        except Exception as exc:
            error = MensajeChatHostAI(rol="host_ai", tipo=TIPO_ERROR, texto=f"No he podido procesar la consulta: {exc}", datos={"error": repr(exc)})
            self._mensajes.append(error)
            self._registrar_log(contenido, {"tipo_mensaje": TIPO_ERROR, "mensaje": str(exc)}, inicio, error=str(exc))
            return self._normalizar(error)
        finally:
            self._procesando = False

    def estado_sesion(self) -> dict[str, Any]:
        return self._session.to_dict()

    def actualizar_contexto_activo(self, contexto: str) -> None:
        self._session.actualizar_contexto_activo(contexto=contexto)

    def aplicar_navigation_request(self, nav_request: dict[str, Any]) -> None:
        self._session.actualizar_desde_navegacion(nav_request)

    def platform_stats(self) -> dict[str, Any]:
        return dict(self.tool_registry.stats())

    def _resolver_intencion(self, texto: str, contexto: dict[str, Any], engine: dict[str, Any]) -> dict[str, Any]:
        ejecutivo = self._resolver_host_ai_executive(texto, contexto, engine)
        if ejecutivo is not None:
            return ejecutivo

        match = self.router.detectar(texto)
        self._session.ultima_intencion = match.intent
        self._session.registrar_accion("INTENCION", f"{match.intent}")

        if match.intent == INTENT_ABRIR_REFERENCIA_RESULTADO:
            return self._resolver_referencia_resultado(match=match, engine=engine)

        if match.intent == INTENT_MOSTRAR_ESCANDALLO_ACTUAL:
            receta = dict(self._session.receta_activa or {})
            escandallo = dict(self._session.escandallo_activo or {})
            if not receta and not escandallo:
                return {
                    "tipo_mensaje": TIPO_ADVERTENCIA,
                    "mensaje": "No tengo una receta o escandallo activos. Indica primero una receta concreta o abre un escandallo.",
                    "datos": {"engine": engine, "intent": match.to_dict()},
                }
            base = receta or escandallo
            nombre = str(base.get("nombre") or base.get("codigo") or "seleccionado")
            tr = self.tool_executor.execute(
                "abrir_escandallo",
                params={"item": base},
                session_context=self._session.to_dict(),
            )
            self._session.registrar_accion("NAV_REQUEST", f"Escandallo de {nombre}", module="RECETAS_ESCANDALLOS")
            return {
                "tipo_mensaje": TIPO_RESULTADO,
                "mensaje": f"De acuerdo, salgo al shell para mostrar el escandallo de {nombre}.",
                "datos": {"engine": engine, "intent": match.to_dict(), "navigation_request": dict(tr.navegacion or {})},
            }

        if match.intent == INTENT_MOSTRAR_MENU_ACTUAL:
            menu = dict(self._session.menu_activo or {})
            evento = dict(self._session.evento_activo or {})
            receta = dict(self._session.receta_activa or {})
            if not menu and not evento and not receta:
                return {
                    "tipo_mensaje": TIPO_ADVERTENCIA,
                    "mensaje": "No tengo contexto suficiente para abrir un menu. Indica un evento, una receta o un menu concreto.",
                    "datos": {"engine": engine, "intent": match.to_dict()},
                }
            filtro = menu or evento or receta
            tr = self.tool_executor.execute(
                "abrir_menus",
                params={"item": filtro},
                session_context=self._session.to_dict(),
            )
            nav = dict(tr.navegacion or {})
            nav["context_update"] = {"contexto_activo": "MENU", "menu_activo": menu or filtro}
            self._session.registrar_accion("NAV_REQUEST", "Abrir menu contextual", module="MENUS")
            return {
                "tipo_mensaje": TIPO_RESULTADO,
                "mensaje": "De acuerdo, salgo al shell para abrir el menu relacionado.",
                "datos": {"engine": engine, "intent": match.to_dict(), "navigation_request": nav},
            }

        if match.intent == INTENT_CONSULTAR_MARGEN_ACTUAL:
            if not any([self._session.receta_activa, self._session.escandallo_activo, self._session.menu_activo]):
                return {
                    "tipo_mensaje": TIPO_ADVERTENCIA,
                    "mensaje": "No tengo contexto activo para consultar margen. Selecciona primero una receta, un escandallo o un menu.",
                    "datos": {"engine": engine, "intent": match.to_dict()},
                }
            return {
                "tipo_mensaje": TIPO_ADVERTENCIA,
                "mensaje": "En APP-02 no calculo margen automaticamente. Puedo llevarte al modulo correspondiente para revisarlo con datos reales.",
                "datos": {"engine": engine, "intent": match.to_dict()},
            }

        if match.intent == INTENT_AYUDA:
            return {
                "tipo_mensaje": TIPO_AYUDA,
                "mensaje": "Puedo buscar recetas, listar pendientes, mostrar escandallos desactualizados, ver incidencias, consultar eventos proximos, abrir modulos y usar referencias de contexto como 'la primera' o 'la ultima'.",
                "datos": {"engine": engine, "intent": match.to_dict()},
            }

        if match.intent == INTENT_MOSTRAR_ESTADO_GENERAL:
            tr = self.tool_executor.execute(
                "mostrar_estado_general",
                params={},
                session_context=self._session.to_dict(),
            )
            modelo = dict((tr.datos or {}).get("home") or {})
            return {
                "tipo_mensaje": TIPO_RESULTADO,
                "mensaje": tr.mensaje,
                "datos": {"engine": engine, "intent": match.to_dict(), "home": modelo},
            }

        tool_id = self.tool_resolver.resolve(match.intent, terms=match.terms, session_context=self._session.to_dict())
        if tool_id:
            params: dict[str, Any] = {}
            if match.intent == INTENT_BUSCAR_RECETA:
                params["termino"] = str((match.terms or {}).get("termino") or "")

            tr = self.tool_executor.execute(tool_id, params=params, session_context=self._session.to_dict())
            self._aplicar_resultado_tool_en_sesion(tr.to_dict())

            datos_out: dict[str, Any] = {
                "engine": engine,
                "intent": match.to_dict(),
                "tool": {"id": tool_id, "estado": tr.estado, "duracion_ms": tr.duracion_ms},
            }
            resultados = list((tr.datos or {}).get("resultados") or [])
            if resultados:
                datos_out["resultados"] = resultados
            nav = dict(tr.navegacion or {})
            if nav:
                datos_out["navigation_request"] = nav
                modulo_nav = str(nav.get("target_module") or "")
                sidebar_nav = str(self._module_to_sidebar.get(modulo_nav) or "")
                if sidebar_nav:
                    datos_out["accion_navegacion"] = {"sidebar": sidebar_nav, "tipo": "abrir_modulo"}

            acciones = []
            for accion in list(tr.acciones or []):
                a = dict(accion or {})
                code = str(a.get("code") or "")
                if code == "abrir_eventos":
                    a["navigation_request"] = self.tool_executor.execute("abrir_evento", session_context=self._session.to_dict()).navegacion
                elif code == "abrir_recetas":
                    a["navigation_request"] = self.tool_executor.execute("abrir_receta", session_context=self._session.to_dict()).navegacion
                elif code == "abrir_escandallos":
                    a["navigation_request"] = self.tool_executor.execute("abrir_escandallo", session_context=self._session.to_dict()).navegacion
                elif code == "abrir_incidencias":
                    a["navigation_request"] = self.tool_executor.execute("abrir_incidencias", session_context=self._session.to_dict()).navegacion
                acciones.append(a)
            if acciones:
                datos_out["suggested_actions"] = acciones

            tipo_msg = TIPO_RESULTADO if tr.estado in {"OK"} else TIPO_ADVERTENCIA
            if tr.estado == "ERROR":
                tipo_msg = TIPO_ERROR

            return {
                "tipo_mensaje": tipo_msg,
                "mensaje": tr.mensaje,
                "datos": datos_out,
            }

        return {
            "tipo_mensaje": TIPO_ADVERTENCIA,
            "mensaje": "Todavia no puedo interpretar esa peticion. Puedo buscar recetas, mostrar incidencias, consultar eventos proximos o abrir modulos.",
            "datos": {"engine": engine, "intent": match.to_dict()},
        }

    def _resolver_host_ai_executive(self, texto: str, contexto: dict[str, Any], engine: dict[str, Any]) -> dict[str, Any] | None:
        intencion_exec = detectar_intencion_executive(texto)
        if intencion_exec is None:
            return None

        base_dir = Path(getattr(getattr(self.orquestador, "core", None), "base_dir", Path.cwd())).resolve()
        executive = HostAIExecutive(base_dir)
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
            resultado_rest = executive.analizar_restaurante(core=getattr(self.orquestador, "core", None))
            return {
                "tipo_mensaje": TIPO_RESULTADO,
                "mensaje": formatear_respuesta_executive_conversacional(resultado_rest, intencion_exec),
                "datos": {
                    "engine": engine,
                    "intent": {"intent": "HOST_AI_EXECUTIVE", "score": 1.0, "terms": {"intencion_executive": intencion_exec}},
                    "executive": resultado_rest,
                },
            }

        if intencion_exec in intenciones_focus:
            evento_focus = self._resolver_evento_activo_executive(contexto)
            if evento_focus:
                resultado_focus = executive.analizar_evento(evento_focus)
            else:
                resultado_focus = executive.analizar_restaurante(core=getattr(self.orquestador, "core", None))

            return {
                "tipo_mensaje": TIPO_RESULTADO,
                "mensaje": formatear_respuesta_executive_conversacional(resultado_focus, intencion_exec),
                "datos": {
                    "engine": engine,
                    "intent": {"intent": "HOST_AI_EXECUTIVE", "score": 1.0, "terms": {"intencion_executive": intencion_exec}},
                    "executive": resultado_focus,
                },
            }

        if intencion_exec in intenciones_plan:
            if intencion_exec == EXEC_INTENCION_PLAN_DIA:
                resultado_plan = executive.analizar_restaurante(core=getattr(self.orquestador, "core", None))
                tipo_plan = "restaurante"
            else:
                evento_plan = self._resolver_evento_activo_executive(contexto)
                if evento_plan:
                    resultado_plan = executive.analizar_evento_para_plan(evento_plan, core=getattr(self.orquestador, "core", None))
                    tipo_plan = "evento"
                else:
                    resultado_plan = executive.analizar_restaurante(core=getattr(self.orquestador, "core", None))
                    tipo_plan = "restaurante"

            resultado_plan_out = dict(resultado_plan)
            resultado_plan_out["plan_operativo"] = executive.generar_plan_operativo(resultado_plan, tipo_plan=tipo_plan)
            return {
                "tipo_mensaje": TIPO_RESULTADO,
                "mensaje": formatear_respuesta_executive_conversacional(resultado_plan_out, intencion_exec),
                "datos": {
                    "engine": engine,
                    "intent": {"intent": "HOST_AI_EXECUTIVE", "score": 1.0, "terms": {"intencion_executive": intencion_exec}},
                    "executive": resultado_plan_out,
                },
            }

        evento = self._resolver_evento_activo_executive(contexto)
        if not evento:
            return {
                "tipo_mensaje": TIPO_ADVERTENCIA,
                "mensaje": "Necesito un evento activo para generar el resumen ejecutivo. Selecciona un evento y vuelve a pedirlo.",
                "datos": {
                    "engine": engine,
                    "intent": {"intent": "HOST_AI_EXECUTIVE", "score": 1.0, "terms": {}},
                },
            }

        resultado = executive.analizar_evento(evento)
        mensaje = formatear_respuesta_executive_conversacional(resultado, intencion_exec)
        self._session.evento_activo = dict(evento)
        self._session.ultima_intencion = "HOST_AI_EXECUTIVE"
        self._session.registrar_accion("ANALISIS_EJECUTIVO", "Resumen ejecutivo del evento activo", module="EVENTOS", entity_id=str(evento.get("id") or ""))

        return {
            "tipo_mensaje": TIPO_RESULTADO if bool(resultado.get("ok")) else TIPO_ADVERTENCIA,
            "mensaje": mensaje,
            "datos": {
                "engine": engine,
                "intent": {"intent": "HOST_AI_EXECUTIVE", "score": 1.0, "terms": {"intencion_executive": intencion_exec}},
                "executive": resultado,
            },
        }

    def _resolver_evento_activo_executive(self, contexto: dict[str, Any]) -> dict[str, Any]:
        ctx = dict(contexto or {})
        evento_ctx = dict(ctx.get("evento_activo") or {}) if isinstance(ctx.get("evento_activo"), dict) else {}
        evento_sesion = dict(self._session.evento_activo or {})
        evento_base = evento_ctx or evento_sesion

        evento_id = str(ctx.get("evento_id") or evento_base.get("id") or "").strip()
        if evento_id:
            evento_cargado = self._cargar_evento_por_id(evento_id)
            if evento_cargado:
                return evento_cargado

        if evento_base:
            return self._evento_para_executive(evento_base)
        return {}

    def _cargar_evento_por_id(self, evento_id: str) -> dict[str, Any]:
        core = getattr(self.orquestador, "core", None)
        eventos = getattr(core, "eventos", None)
        if eventos is None:
            return {}
        try:
            evento = eventos.obtener(evento_id)
        except Exception:
            return {}
        return self._evento_para_executive(evento)

    @staticmethod
    def _evento_para_executive(evento: Any) -> dict[str, Any]:
        if isinstance(evento, dict):
            data = dict(evento)
            return {
                "id": data.get("id"),
                "nombre": data.get("nombre"),
                "tipo": data.get("tipo") or data.get("tipo_evento") or "evento",
                "personas": data.get("personas") or data.get("pax"),
                "pax": data.get("pax") or data.get("personas"),
                "fecha": data.get("fecha"),
                "hora_servicio": data.get("hora_servicio") or data.get("hora_inicio") or "12:00",
                "menu": data.get("menu") or data.get("tipo_menu") or "menu operativo",
                "lugar": data.get("lugar") or data.get("ubicacion") or data.get("ubicación") or "lugar operativo",
                "restricciones": data.get("restricciones") or "sin restricciones",
                "objetivo": data.get("objetivo") or "flujo completo",
            }

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

    @staticmethod
    def _normalizar_texto(texto: str) -> str:
        t = str(texto or "").strip().lower()
        t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
        return " ".join(t.split())


    def _resolver_referencia_resultado(self, match: Any, engine: dict[str, Any]) -> dict[str, Any]:
        ref = str((match.terms or {}).get("referencia") or "")
        items = list(self._session.ultima_lista_mostrada or [])
        if not items:
            return {
                "tipo_mensaje": TIPO_ADVERTENCIA,
                "mensaje": "No tengo una lista activa para resolver esa referencia. Primero realiza una busqueda o consulta listada.",
                "datos": {"engine": engine, "intent": match.to_dict()},
            }

        index = 0
        if ref == "segunda":
            index = 1
        if ref == "ultima":
            index = len(items) - 1

        if index < 0 or index >= len(items):
            return {
                "tipo_mensaje": TIPO_ADVERTENCIA,
                "mensaje": "No encuentro ese elemento en el contexto actual. ¿Puedes indicarme exactamente cual quieres abrir?",
                "datos": {"engine": engine, "intent": match.to_dict()},
            }

        seleccionado = dict(items[index])
        self._session.ultimo_elemento_seleccionado = seleccionado

        contexto = str(self._session.contexto_activo or "RECETA").upper()
        sidebar = "6"
        target_view = "RECETA"
        context_update: dict[str, Any] = {"contexto_activo": "RECETA", "receta_activa": seleccionado}
        if contexto in {"EVENTO", "EVENTOS"}:
            sidebar = "2"
            target_view = "EVENTO"
            context_update = {"contexto_activo": "EVENTO", "evento_activo": seleccionado}
        elif contexto in {"MENU", "MENUS"}:
            sidebar = "7"
            target_view = "MENU"
            context_update = {"contexto_activo": "MENU", "menu_activo": seleccionado}
        elif contexto in {"PRODUCCION"}:
            sidebar = "3"
            target_view = "PRODUCCION"
            context_update = {"contexto_activo": "PRODUCCION", "produccion_activa": seleccionado}

        tool_for_ref = "abrir_receta"
        if sidebar == "2":
            tool_for_ref = "abrir_evento"
        elif sidebar == "7":
            tool_for_ref = "abrir_menus"
        elif sidebar == "3":
            tool_for_ref = "abrir_produccion"
        tr = self.tool_executor.execute(tool_for_ref, params={"item": seleccionado, "referencia": ref}, session_context=self._session.to_dict())
        nav = dict(tr.navegacion or {})
        if not nav:
            nav = self._navigation_request(
                sidebar=sidebar,
                target_view=target_view,
                entity_id=str(seleccionado.get("id") or seleccionado.get("codigo") or ""),
                filter_data={"item": seleccionado, "referencia": ref},
                context_update=context_update,
                message="Navegacion solicitada desde referencia contextual.",
            )
        else:
            nav["context_update"] = context_update
        self._session.registrar_accion(
            "NAV_REQUEST",
            f"Abrir referencia {ref}",
            module=str(nav.get("target_module") or ""),
            entity_id=str(seleccionado.get("id") or seleccionado.get("codigo") or ""),
        )
        return {
            "tipo_mensaje": TIPO_RESULTADO,
            "mensaje": "De acuerdo, salgo al shell para abrir ese elemento.",
            "datos": {
                "engine": engine,
                "intent": match.to_dict(),
                "resultados": items,
                "navigation_request": nav,
                "tool": {"id": tool_for_ref, "estado": tr.estado, "duracion_ms": tr.duracion_ms},
            },
        }

    def _aplicar_resultado_tool_en_sesion(self, tool_result: dict[str, Any]) -> None:
        contexto = dict(tool_result.get("contexto_actualizado") or {})
        if "contexto_activo" in contexto:
            self._session.actualizar_contexto_activo(str(contexto.get("contexto_activo") or "HOME"), module=str(contexto.get("contexto_activo") or "HOME"))
        if "ultima_busqueda" in contexto:
            self._session.ultima_busqueda = str(contexto.get("ultima_busqueda") or "")
        if "ultima_lista_mostrada" in contexto:
            self._session.ultima_lista_mostrada = list(contexto.get("ultima_lista_mostrada") or [])
        if "receta_activa" in contexto and isinstance(contexto.get("receta_activa"), dict):
            self._session.receta_activa = dict(contexto.get("receta_activa") or {})
        if "escandallo_activo" in contexto and isinstance(contexto.get("escandallo_activo"), dict):
            self._session.escandallo_activo = dict(contexto.get("escandallo_activo") or {})
        if "menu_activo" in contexto and isinstance(contexto.get("menu_activo"), dict):
            self._session.menu_activo = dict(contexto.get("menu_activo") or {})
        if "evento_activo" in contexto and isinstance(contexto.get("evento_activo"), dict):
            self._session.evento_activo = dict(contexto.get("evento_activo") or {})

    def _consultar_engine_simulado(self, contenido: str, contexto: dict[str, Any] | None) -> dict[str, Any]:
        from CORE.orquestador import SolicitudHostAI

        req = SolicitudHostAI(
            "host_ai_engine_consulta",
            {
                "origen": "APP_SHELL",
                "modulo": "chat_host_ai",
                "tipo_peticion": "consulta_general",
                "datos_enviados": {
                    "pregunta": contenido,
                    "sim_scenario": self._detectar_escenario_simulado(contenido),
                },
                "proveedor_preferido": "SIMULADO",
                "formato_entrada": "texto",
                "usar_director": False,
                "contexto": dict(contexto or {}),
            },
        )
        resultado = self.orquestador.resolver(req)
        data = resultado.to_dict() if hasattr(resultado, "to_dict") else dict(resultado or {})
        return dict((data.get("datos") or {}).get("host_ai_engine") or {})

    def _registrar_log(self, texto: str, respuesta: dict[str, Any], inicio: float, error: str = "") -> None:
        duracion_ms = int((time.perf_counter() - inicio) * 1000)
        datos = dict(respuesta.get("datos") or {})
        intent = dict(datos.get("intent") or {})
        LOGGER.info(
            "chat_event %s",
            {
                "intencion": intent.get("intent") or self._session.ultima_intencion or "",
                "score": intent.get("score", 0),
                "duracion_ms": duracion_ms,
                "tipo_mensaje": respuesta.get("tipo_mensaje"),
                "resultados": len(list(datos.get("resultados") or [])),
                "navigation_request": bool(datos.get("navigation_request")),
                "error": error,
                "texto_len": len(str(texto or "")),
            },
        )

    def _navigation_request(
        self,
        *,
        sidebar: str,
        target_view: str = "",
        filter_data: dict[str, Any] | None = None,
        entity_id: str = "",
        message: str = "",
        context_update: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return NavigationRequest(
            target_module=str(self._sidebar_to_module.get(str(sidebar), "")),
            target_view=str(target_view or ""),
            filter_data=dict(filter_data or {}),
            entity_id=str(entity_id or ""),
            source="chat_host_ai",
            preserve_chat_session=True,
            message=str(message or ""),
            context_update=dict(context_update or {}),
        ).to_dict()

    @staticmethod
    def _detectar_escenario_simulado(texto: str) -> str:
        low = texto.lower()
        if "confirm" in low or "aplica" in low or "ejecut" in low:
            return "requiere_confirmacion"
        if "falta" in low or "incompleto" in low:
            return "falta_datos"
        if "error" in low:
            return "error_en_paso"
        if "receta" in low:
            return "consulta_simple_receta"
        if "import" in low:
            return "importacion_compleja"
        return ""

    @staticmethod
    def _mensaje_engine(engine: dict[str, Any]) -> str:
        estado = str(engine.get("estado") or "")
        if estado == "ERROR":
            errores = ", ".join(engine.get("errores") or [])
            return f"Error en proveedor simulado: {errores or 'sin detalle'}"
        respuesta = dict(engine.get("respuesta") or {})
        if respuesta.get("mensaje"):
            return str(respuesta.get("mensaje"))
        return "Respuesta simulada recibida."

    @staticmethod
    def _tipo_desde_engine(engine: dict[str, Any]) -> str:
        estado = str(engine.get("estado") or "")
        respuesta = dict(engine.get("respuesta") or {})
        estado_sugerido = str(respuesta.get("estado_sugerido") or "")
        if estado == "ERROR":
            return TIPO_ERROR
        if estado_sugerido == "ESPERANDO_CONFIRMACION":
            return TIPO_CONFIRMACION
        if estado_sugerido == "PLANIFICADA":
            return TIPO_PROPUESTA
        if estado_sugerido == "BLOQUEADA":
            return TIPO_INCIDENCIA
        return TIPO_RESULTADO

    @staticmethod
    def _normalizar(msg: MensajeChatHostAI) -> dict[str, Any]:
        return {
            "ok": msg.tipo != TIPO_ERROR,
            "tipo_mensaje": msg.tipo,
            "mensaje": msg.texto,
            "rol": msg.rol,
            "timestamp": msg.timestamp,
            "datos": dict(msg.datos or {}),
        }


__all__ = [
    "ServicioChatHostAIShell",
    "MensajeChatHostAI",
    "NavigationRequest",
    "TIPO_USUARIO",
    "TIPO_HOST_AI",
    "TIPO_EXPLICACION",
    "TIPO_AYUDA",
    "TIPO_ADVERTENCIA",
    "TIPO_INCIDENCIA",
    "TIPO_PROPUESTA",
    "TIPO_CONFIRMACION",
    "TIPO_RESULTADO",
    "TIPO_ERROR",
    "TIPO_SISTEMA",
]
