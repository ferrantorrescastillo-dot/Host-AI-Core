from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import uuid4
import logging
import re
import time
import unicodedata

from SERVICIOS.host_ai_deterministic_intent_router import (
    HostAIDeterministicIntentRouter,
    INTENT_ABRIR_REFERENCIA_RESULTADO,
    INTENT_AYUDA,
    INTENT_ABRIR_MODULO,
    INTENT_BUSCAR_RECETA,
    INTENT_BUSCAR_ARTICULOS,
    INTENT_CONSULTAR_COMPRAS_PENDIENTES,
    INTENT_CONSULTAR_PENDIENTE_RECEPCION,
    INTENT_CONSULTAR_PROPUESTAS_COMPRA,
    INTENT_CONSULTAR_NECESIDADES_COMPRA,
    INTENT_BUSCAR_PEDIDOS_PROVEEDOR,
    INTENT_CONSULTAR_PRODUCCION,
    INTENT_CONSULTAR_MARGEN_ACTUAL,
    INTENT_CONSULTAR_ESTADO_STOCK,
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
from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
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
from SERVICIOS.host_ai_platform import GeneralAgentPlatformRuntime, SessionContext as PlatformSessionContext
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.host_ai_tool_resolver import HostAIToolResolver
from SERVICIOS.host_ai_agent_observability import HostAIAgentObservability
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.articulo_economico_canonico import convert_quantity, normalize_unit
from SERVICIOS.host_ai_conversation_brain import HostAIConversationBrain
from SERVICIOS.receta_completion_workflow import RecipeCompletionWorkflow
from SERVICIOS.host_ai_operational_synthesis import MISSING_RECIPE_OPTIONS
from SERVICIOS.confirmacion_procedimiento_receta_service import (
    ConfirmacionProcedimientoRecetaService,
    ErrorConfirmacionProcedimientoReceta,
)
from SERVICIOS.confirmacion_relacion_ingrediente_service import (
    ConfirmacionRelacionIngredienteService,
    ErrorConfirmacionRelacionIngrediente,
)
from SERVICIOS.produccion_inteligente_workflow import IntelligentProductionWorkflow
import os


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
    Orquestador -> Host AI Engine -> proveedor configurado.
    """

    def __init__(self, orquestador: Any, home_read_service: Any | None = None, session_id: str = "default"):
        self.orquestador = orquestador
        self.home_read_service = home_read_service
        self.router = HostAIDeterministicIntentRouter()
        self.tool_registry = build_default_tool_registry()
        self.tool_resolver = HostAIToolResolver()
        self.session_id = str(session_id or "default")
        write_context = AuthorizedExecutionContext.from_internal_environment(
            "chat-session", role="chat", allow_local_default=True,
        )
        legacy_executor = HostAIToolExecutor(self.tool_registry, home_read_service=self.home_read_service, write_context=write_context, session_id=self.session_id)
        self._catalog_executor = legacy_executor
        self.tool_executor = GeneralAgentPlatformRuntime(legacy_executor, self.tool_registry, PlatformSessionContext(self.session_id))
        self.general_agent = HostAIAgent(
            getattr(self.orquestador, "host_ai_engine", None),
            self.tool_executor,
            HostAIToolCatalog.for_general_agent(self.tool_registry),
            HostAIAgentPolicy(),
        )
        base_dir = getattr(getattr(self.orquestador, "host_ai_engine", None), "base_dir", None) or Path.cwd()
        self.agent_observability = HostAIAgentObservability(base_dir)
        self.conversation_brain = HostAIConversationBrain()
        self.recipe_completion_workflow = RecipeCompletionWorkflow(base_dir)
        self.recipe_procedure_service = ConfirmacionProcedimientoRecetaService(base_dir)
        self.ingredient_relation_service = ConfirmacionRelacionIngredienteService(base_dir)
        self.production_workflow = IntelligentProductionWorkflow(self.tool_executor)
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
            lot_location = self._try_stock_lot_location(contenido, dict(contexto or {}))
            if lot_location is not None:
                salida = MensajeChatHostAI(rol="host_ai", tipo=str(lot_location.get("tipo_mensaje") or TIPO_CONFIRMACION), texto=str(lot_location["mensaje"]), datos=dict(lot_location["datos"]))
                self._mensajes.append(salida); self._registrar_log(contenido, lot_location, inicio); return self._normalizar(salida)
            if self._session.captura_cambio_articulo:
                return self._capture_article_change_value(contenido, dict(contexto or {}), inicio)
            request_id = str((contexto or {}).get("_host_ai_request_id") or "")
            candidate, readiness = self._general_agent_status()
            self.agent_observability.emit(
                "general_agent_route", request_id=request_id,
                general_agent_candidate=True, enabled=readiness["enabled"],
                provider=readiness["provider"], provider_connected=readiness["connected"],
                supports_tool_calling=readiness["tool_calling"], selected_path="GENERAL_AGENT" if candidate else "LEGACY_WORKFLOW",
                reason=readiness["reason"],
            )
            if candidate:
                agent_response = self._try_general_agent(contenido, dict(contexto or {}))
                if agent_response is not None:
                    salida = MensajeChatHostAI(rol="host_ai", tipo=TIPO_RESULTADO, texto=agent_response["mensaje"], datos=agent_response["datos"])
                    self._mensajes.append(salida)
                    self._registrar_log(contenido, {"tipo_mensaje": TIPO_RESULTADO, **agent_response}, inicio)
                    return self._normalizar(salida)
            # The local/simulated runtime cannot perform model tool-calling. Keep
            # explicit catalogue CREATE commands on the same typed PREVIEW path
            # instead of degrading them to the legacy "SIMULACION" message.
            catalog_preview = self._try_safe_catalog_create_without_provider(contenido, request_id)
            if catalog_preview is not None:
                salida = MensajeChatHostAI(rol="host_ai", tipo=TIPO_CONFIRMACION, texto=catalog_preview["mensaje"], datos=catalog_preview["datos"])
                self._mensajes.append(salida)
                self._registrar_log(contenido, catalog_preview, inicio)
                return self._normalizar(salida)
            recipe_request = self._try_recipe_request(contenido)
            if recipe_request is not None:
                salida = MensajeChatHostAI(
                    rol="host_ai", tipo=TIPO_RESULTADO,
                    texto=str(recipe_request["mensaje"]), datos=dict(recipe_request["datos"]),
                )
                self._mensajes.append(salida)
                self._registrar_log(contenido, recipe_request, inicio)
                return self._normalizar(salida)
            recipe_completion = self._try_recipe_completion(contenido)
            if recipe_completion is not None:
                salida = MensajeChatHostAI(
                    rol="host_ai", tipo=TIPO_RESULTADO,
                    texto=str(recipe_completion["mensaje"]), datos=dict(recipe_completion["datos"]),
                )
                self._mensajes.append(salida)
                self._registrar_log(contenido, recipe_completion, inicio)
                return self._normalizar(salida)
            production_completion = self._try_production_planning(contenido)
            if production_completion is not None:
                salida = MensajeChatHostAI(rol="host_ai", tipo=TIPO_RESULTADO, texto=str(production_completion["mensaje"]), datos=dict(production_completion["datos"]))
                self._mensajes.append(salida)
                self._registrar_log(contenido, production_completion, inicio)
                return self._normalizar(salida)
            agent_response = self._try_general_agent(contenido, dict(contexto or {}))
            if agent_response is not None:
                salida = MensajeChatHostAI(rol="host_ai", tipo=TIPO_RESULTADO, texto=agent_response["mensaje"], datos=agent_response["datos"])
                self._mensajes.append(salida)
                self._registrar_log(contenido, {"tipo_mensaje": TIPO_RESULTADO, **agent_response}, inicio)
                return self._normalizar(salida)
            article_selection = self._seleccion_articulo_contextual(contenido)
            selection_term = str((article_selection or {}).get("termino") or "")
            stock_match = self.router.detectar(selection_term or contenido)
            if stock_match.intent == INTENT_CONSULTAR_ESTADO_STOCK:
                respuesta = self._resolver_stock_conversacional(
                    contenido,
                    dict(contexto or {}),
                    stock_match,
                )
                salida = MensajeChatHostAI(
                    rol="host_ai",
                    tipo=str(respuesta.get("tipo_mensaje") or TIPO_RESULTADO),
                    texto=str(respuesta.get("mensaje") or ""),
                    datos=dict(respuesta.get("datos") or {}),
                )
                self._mensajes.append(salida)
                self._registrar_log(contenido, respuesta, inicio)
                return self._normalizar(salida)

            if stock_match.intent == INTENT_BUSCAR_ARTICULOS:
                respuesta = self._resolver_articulos_conversacional(
                    contenido,
                    dict(contexto or {}),
                    stock_match,
                    seleccion=article_selection,
                )
                salida = MensajeChatHostAI(
                    rol="host_ai",
                    tipo=str(respuesta.get("tipo_mensaje") or TIPO_RESULTADO),
                    texto=str(respuesta.get("mensaje") or ""),
                    datos=dict(respuesta.get("datos") or {}),
                )
                self._mensajes.append(salida)
                self._registrar_log(contenido, respuesta, inicio)
                return self._normalizar(salida)

            compras_intents = {
                INTENT_CONSULTAR_COMPRAS_PENDIENTES,
                INTENT_CONSULTAR_PENDIENTE_RECEPCION,
                INTENT_CONSULTAR_PROPUESTAS_COMPRA,
                INTENT_CONSULTAR_NECESIDADES_COMPRA,
                INTENT_BUSCAR_PEDIDOS_PROVEEDOR,
            }
            if stock_match.intent in compras_intents:
                respuesta = self._resolver_compras_conversacional(contenido, dict(contexto or {}), stock_match)
                salida = MensajeChatHostAI(rol="host_ai", tipo=str(respuesta.get("tipo_mensaje") or TIPO_RESULTADO), texto=str(respuesta.get("mensaje") or ""), datos=dict(respuesta.get("datos") or {}))
                self._mensajes.append(salida)
                self._registrar_log(contenido, respuesta, inicio)
                return self._normalizar(salida)

            if stock_match.intent == INTENT_CONSULTAR_PRODUCCION:
                respuesta = self._resolver_produccion_conversacional(contenido, dict(contexto or {}), stock_match)
                salida = MensajeChatHostAI(rol="host_ai", tipo=str(respuesta.get("tipo_mensaje") or TIPO_RESULTADO), texto=str(respuesta.get("mensaje") or ""), datos=dict(respuesta.get("datos") or {}))
                self._mensajes.append(salida)
                self._registrar_log(contenido, respuesta, inicio)
                return self._normalizar(salida)

            engine = self._consultar_engine_simulado(contenido, contexto)
            if str(engine.get("estado") or "") == "ERROR":
                # Executive conversacional no depende de proveedor generativo; mantener ruta determinista local.
                if (
                    detectar_intencion_executive(contenido) is not None
                    or self._es_consulta_modulos(contenido)
                ):
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
            error = MensajeChatHostAI(
                rol="host_ai",
                tipo=TIPO_ERROR,
                texto="No he podido procesar la consulta de forma segura. Intentalo de nuevo.",
                datos={"safe_error_code": "internal_error", "datos_reales_modificados": False},
            )
            self._mensajes.append(error)
            self._registrar_log(contenido, {"tipo_mensaje": TIPO_ERROR, "mensaje": str(exc)}, inicio, error=str(exc))
            return self._normalizar(error)
        finally:
            self._procesando = False

    def ejecutar_accion_reserva(self, action_id: str, action_context_id: str = "", contexto: dict[str, Any] | None = None) -> dict[str, Any]:
        action = str(action_id or "").upper()
        if action in {"APPLY_PENDING_LOT_LOCATION", "DISCARD_PENDING_LOT_LOCATION"}:
            pending = dict(self._session.confirmacion_ubicacion_lote_pendiente or {})
            if not pending: return self._reservation_action_message("La vista previa ya no está disponible.", TIPO_ADVERTENCIA, reason="confirmation_missing")
            tool = "confirmar_ubicacion_lote" if action.startswith("APPLY") else "descartar_ubicacion_lote"
            result = self._catalog_executor.execute_stock_lot_location_flow(tool, pending, request_id=str((contexto or {}).get("_host_ai_request_id") or "chat-lot-location"))
            self._session.confirmacion_ubicacion_lote_pendiente = {}
            if result.estado != "OK": return self._reservation_action_message(result.mensaje, TIPO_ERROR, reason=str((result.errores or ["lot_location_error"])[0]))
            ui_action = dict((result.datos or {}).get("ui_action") or {})
            return self._reservation_action_message(result.mensaje, TIPO_RESULTADO, ui_action=ui_action or None)
        if action in {"APPLY_PENDING_CATALOG_CREATE", "DISCARD_PENDING_CATALOG_CREATE"}:
            pending = dict(self._session.confirmacion_catalogo_pendiente or {})
            if not pending or str(action_context_id or "") != str(pending.get("preview_token") or "")[-12:]:
                return self._reservation_action_message("La vista previa ya no está disponible.", TIPO_ADVERTENCIA, reason="confirmation_missing")
            if action == "DISCARD_PENDING_CATALOG_CREATE":
                result = self._catalog_executor.discard_catalog_create(str(pending.get("preview_token") or ""), str((contexto or {}).get("_host_ai_request_id") or ""))
                self._session.confirmacion_catalogo_pendiente = {}
                return self._reservation_action_message(result.mensaje, TIPO_RESULTADO if result.estado == "OK" else TIPO_ERROR)
            return self.enviar("Sí, confirmar.", contexto=dict(contexto or {}))
        if action == "PREVIEW_RECIPE_PROCEDURE":
            return self._preview_recipe_procedure()
        if action == "CONFIRM_RECIPE_PROCEDURE":
            return self._confirm_recipe_procedure(str((contexto or {}).get("_host_ai_request_id") or ""))
        if action == "PREVIEW_INGREDIENT_RELATION":
            return self._preview_ingredient_relation()
        if action == "CONFIRM_INGREDIENT_RELATION":
            return self._confirm_ingredient_relation()
        if action in {"RESOLVE_MISSING_PRICE", "RESOLVE_MISSING_CONVERSION"}:
            return self._execute_economic_action(action, action_context_id)
        if action == "CHECK_ESCANDALLO_COST":
            return self._execute_escandallo_cost_check(action_context_id)
        if action in {"APPLY_PENDING_ARTICLE_CHANGE", "DISCARD_PENDING_ARTICLE_CHANGE"}:
            return self._execute_pending_article_change(action, contexto or {})
        preview_actions = {"APPLY_PENDING_RESERVATION", "DISCARD_PENDING_RESERVATION"}
        contextual_actions = {
            "CONFIRM_RESERVATION", "EDIT_RESERVATION", "CANCEL_RESERVATION",
            "MARK_RESERVATION_NO_SHOW", "COMPLETE_RESERVATION", "OPEN_RESERVATION",
        }
        if action not in preview_actions | contextual_actions:
            return self._reservation_action_message("Accion de reserva no valida.", TIPO_ERROR, reason="invalid_action_id")

        if action in preview_actions:
            pending = dict(self._session.confirmacion_reserva_pendiente or {})
            if not pending:
                return self._reservation_action_message("No hay una operacion de reserva pendiente.", TIPO_ADVERTENCIA, reason="confirmation_missing")
            if action == "DISCARD_PENDING_RESERVATION":
                pending_id = str(pending.get("reserva_id") or "")
                self._session.confirmacion_reserva_pendiente = {}
                current = self._reservation_detail(pending_id)
                if current:
                    self._session.reserva_activa = current
                return self._reservation_action_message("Cambio descartado sin modificar la reserva.", TIPO_RESULTADO)
            return self.enviar("Sí, confirmar.", contexto=dict(contexto or {}))

        snapshot = dict(self._session.acciones_reserva_contextuales or {})
        active = dict(self._session.reserva_activa or {})
        reservation_id = str(snapshot.get("reserva_id") or "")
        active_id = str(active.get("reserva_id") or active.get("id") or "")
        current = self._reservation_detail(reservation_id)
        current_state = str((current or {}).get("estado") or "").upper()
        context_matches = str(action_context_id or "") == str(snapshot.get("context_id") or "")
        if not context_matches or not current or active_id != reservation_id or current_state != str(snapshot.get("estado") or "").upper():
            if current:
                self._session.reserva_activa = current
            self._session.acciones_reserva_contextuales = {}
            return self._reservation_action_message(
                "La reserva ha cambiado y esa accion ya no esta disponible. He actualizado las opciones.",
                TIPO_ADVERTENCIA, reason="stale_reservation_action",
            )

        if action in {"OPEN_RESERVATION", "EDIT_RESERVATION"}:
            ui_action = {"type": "OPEN_VIEW", "target": "RESERVAS", "id": reservation_id, "view": "DETALLE", "label": reservation_id}
            text = "Abro la ficha segura de la reserva." if action == "OPEN_RESERVATION" else "Abro la ficha para modificarla con su flujo seguro."
            return self._reservation_action_message(text, TIPO_RESULTADO, ui_action=ui_action)

        transitions: dict[str, tuple[set[str], str]] = {
            "CONFIRM_RESERVATION": ({"PENDIENTE"}, "confirmar_reserva"),
            "CANCEL_RESERVATION": ({"PENDIENTE", "CONFIRMADA"}, "cancelar_reserva"),
            "MARK_RESERVATION_NO_SHOW": ({"CONFIRMADA"}, "marcar_no_show"),
            "COMPLETE_RESERVATION": ({"CONFIRMADA"}, "completar_reserva"),
        }
        allowed_states, tool_id = transitions[action]
        if current_state not in allowed_states:
            return self._reservation_action_message(
                "Esa accion ya no esta permitida para el estado actual de la reserva.",
                TIPO_ADVERTENCIA, reason="reservation_action_unavailable",
            )
        request_id = str((contexto or {}).get("_host_ai_request_id") or "")
        result = self.tool_executor.execute_agent_write_flow(tool_id, {"reserva_id": reservation_id}, request_id=request_id)
        if result.estado != "OK":
            return self._reservation_action_message(
                str(result.mensaje or "No se pudo preparar el cambio."), TIPO_ADVERTENCIA,
                reason=str((result.errores or ["preview_error"])[0]),
            )
        self._aplicar_resultado_tool_en_sesion(result.to_dict())
        return self._reservation_action_message(
            "He preparado el cambio. Revisa los datos y elige una opcion.",
            TIPO_RESULTADO, preview=dict(result.datos or {}),
        )

    def _try_stock_lot_location(self, text: str, context: dict[str, Any]) -> dict[str, Any] | None:
        normalized = self._normalizar_texto(text).strip(" .!?¿¡")
        pending = dict(self._session.confirmacion_ubicacion_lote_pendiente or {})
        confirmation_text = " ".join(re.sub(r"[^a-z0-9]+", " ", normalized).split())
        if pending and confirmation_text in {"si", "si confirmar", "confirmar", "confirmo", "cancelar", "no cancelar"}:
            tool_id = "confirmar_ubicacion_lote" if confirmation_text in {"si", "si confirmar", "confirmar", "confirmo"} else "descartar_ubicacion_lote"
            result = self._catalog_executor.execute_stock_lot_location_flow(
                tool_id,
                pending,
                request_id=str(context.get("_host_ai_request_id") or "chat-lot-location"),
            )
            self._session.confirmacion_ubicacion_lote_pendiente = {}
            return {
                "mensaje": result.mensaje,
                "datos": dict(result.datos or {}) if result.estado == "OK" else {"datos_reales_modificados": False},
                "tipo_mensaje": TIPO_RESULTADO if result.estado == "OK" else TIPO_ERROR,
            }
        keywords = ("ubicacion", "pon el lote", "ponlo en", "arregla la ubicacion")
        if not any(value in normalized for value in keywords): return None
        core = getattr(getattr(self._catalog_executor, "home_read_service", None), "core", None)
        if core is None: return {"mensaje": "No está disponible el inventario canónico de lotes.", "datos": {"datos_reales_modificados": False}, "tipo_mensaje": TIPO_ADVERTENCIA}
        lots = list(getattr(getattr(core, "stock", None), "lotes", {}).values())
        explicit = re.findall(r"\bLOTE?-[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*\b", text, flags=re.IGNORECASE)
        context_id = str(context.get("lote_id") or (context.get("lote_activo") or {}).get("id") or self._session.lote_activo.get("id") or "")
        candidates = [lot for lot in lots if explicit and str(lot.id).casefold() == explicit[0].casefold()] if explicit else ([lot for lot in lots if str(lot.id) == context_id] if context_id else [])
        if explicit and not candidates: return {"mensaje": "No existe ese lote canónico. No se ha modificado stock.", "datos": {"datos_reales_modificados": False}, "tipo_mensaje": TIPO_ADVERTENCIA}
        if len(candidates) != 1: return {"mensaje": "No puedo identificar un único lote. Indica el lote exacto.", "datos": {"candidatos": [{"lote_id": str(l.id), "articulo": str(l.nombre)} for l in candidates], "datos_reales_modificados": False}, "tipo_mensaje": TIPO_ADVERTENCIA}
        lot = candidates[0]
        locations = list(self._catalog_executor.stock_lot_write_service.locations().get("ubicaciones") or [])
        destination_text = normalized.split(" en ", 1)[-1].strip(" .") if " en " in normalized else ""
        exact_locations = [loc for loc in locations if self._normalizar_texto(str(loc.get("nombre") or "")) == destination_text]
        partial_locations = [loc for loc in locations if destination_text and destination_text in self._normalizar_texto(str(loc.get("nombre") or ""))]
        matches = exact_locations or partial_locations
        if len(matches) != 1:
            message = "La ubicación no existe." if not matches else "Hay varias ubicaciones compatibles. Elige una: " + ", ".join(str(loc.get("nombre")) for loc in matches)
            return {"mensaje": message + " No se ha modificado stock.", "datos": {"ubicaciones": matches, "datos_reales_modificados": False}, "tipo_mensaje": TIPO_ADVERTENCIA}
        result = self._catalog_executor.execute_stock_lot_location_flow("preparar_ubicacion_lote", {"lote_id": str(lot.id), "location_id": str(matches[0]["id"])}, request_id=str(context.get("_host_ai_request_id") or "chat-lot-preview"))
        if result.estado != "OK": return {"mensaje": result.mensaje, "datos": {"datos_reales_modificados": False}, "tipo_mensaje": TIPO_ADVERTENCIA}
        pending = dict(result.contexto_actualizado.get("confirmacion_ubicacion_lote_pendiente") or {}); self._session.confirmacion_ubicacion_lote_pendiente = pending; self._session.lote_activo = lot.to_dict()
        preview = dict(result.datos or {}); before, after = dict(preview.get("lote_antes") or {}), dict(preview.get("lote_despues") or {})
        message = f"Cambiar ubicación de lote\n\nLote: {before.get('id')}\nArtículo: {before.get('nombre')}\nUbicación actual: {before.get('ubicacion') or 'Sin ubicación'}\nNueva ubicación: {after.get('ubicacion')}\n\nEste cambio no modifica la cantidad de stock."
        actions = [{"action_id": "APPLY_PENDING_LOT_LOCATION"}, {"action_id": "DISCARD_PENDING_LOT_LOCATION"}]
        return {"mensaje": message, "datos": {"confirmation_actions": actions, "preview": {"operation": "CHANGE_LOT_LOCATION", "lot": before.get("id"), "article": before.get("nombre"), "current_location": before.get("ubicacion") or "Sin ubicación", "new_location": after.get("ubicacion")}, "datos_reales_modificados": False}, "tipo_mensaje": TIPO_CONFIRMACION}

    def _execute_economic_action(self, action: str, action_context_id: str) -> dict[str, Any]:
        snapshot = dict(self._session.acciones_economicas_contextuales or {})
        stored = snapshot.get(action) if isinstance(snapshot.get(action), dict) else {}
        if not stored or str(stored.get("context_id") or "") != str(action_context_id or ""):
            return self._chat_action_message(
                "Esta accion economica ya no esta disponible.", TIPO_ADVERTENCIA,
                reason="stale_economic_action",
            )
        article_id = str(stored.get("articulo_id") or "")
        read_service = getattr(self.tool_executor, "articulos_read_service", None)
        detail = dict(read_service.obtener(article_id) or {}) if read_service and article_id else {}
        article = detail.get("articulo") if detail.get("ok") is not False else None
        canonical_id = str((article or {}).get("id") or "")
        if not canonical_id or canonical_id != article_id:
            self._session.acciones_economicas_contextuales = {}
            return self._chat_action_message(
                "El articulo asociado ya no esta disponible.", TIPO_ADVERTENCIA,
                reason="economic_article_unavailable",
            )
        label = str((article or {}).get("nombre") or canonical_id)
        self._session.captura_cambio_articulo = {
            "operation": "UPDATE_PRICE" if action == "RESOLVE_MISSING_PRICE" else "UPDATE_CONVERSION",
            "articulo_id": canonical_id, "nombre": label,
            "incidencia": str(stored.get("incidencia") or ""),
            "receta_id": str(stored.get("receta_id") or ""),
            "unidad_origen": str(stored.get("unidad_origen") or ""),
            "unidad_destino": str(stored.get("unidad_destino") or ""),
        }
        self._session.acciones_economicas_contextuales = {}
        if action == "RESOLVE_MISSING_PRICE":
            question = f"¿Qué precio de compra quieres registrar para {label}?"
        else:
            source = str(stored.get("unidad_origen") or "")
            target = str(stored.get("unidad_destino") or "")
            question = f"¿A cuánto equivale 1 {source} de {label} en {target}?"
        return self._chat_action_message(
            question, TIPO_RESULTADO,
        )

    def _capture_article_change_value(self, text: str, context: dict[str, Any], started: float) -> dict[str, Any]:
        capture = dict(self._session.captura_cambio_articulo or {})
        if str(capture.get("phase") or "") == "PRICE_CONFLICT":
            return self._resolve_article_price_conflict(text, capture, context, started)
        if str(capture.get("phase") or "") == "PHYSICAL_RANGE_CLARIFICATION":
            if time.monotonic() > float(capture.get("expires_monotonic") or 0):
                self._session.captura_cambio_articulo = {}
                return self._article_capture_warning(
                    "La aclaración de conversión ha caducado; inicia de nuevo el cambio.",
                    "expired_physical_range_clarification",
                )
            capture = {key: value for key, value in capture.items() if key not in {
                "phase", "expires_monotonic",
            }}
        operation = str(capture.get("operation") or "")
        normalized = self._normalizar_texto(text)
        if operation == "UPDATE_CONVERSION":
            physical_range = self._explicit_physical_range(normalized)
            if physical_range is not None:
                lower, upper, unit = physical_range
                ttl = int(getattr(getattr(self.tool_executor, "article_change_service", None), "ttl_seconds", 900) or 900)
                self._session.captura_cambio_articulo = {
                    **capture, "phase": "PHYSICAL_RANGE_CLARIFICATION",
                    "expires_monotonic": time.monotonic() + ttl,
                }
                source = str(capture.get("unidad_origen") or "unidad")
                return self._article_capture_warning(
                    f"El peso indicado es variable entre {self._decimal_text(lower)} y "
                    f"{self._decimal_text(upper)} {unit}. Para registrar la conversión necesito "
                    f"un valor exacto que represente 1 {source}.",
                    "variable_physical_range",
                )
        values = re.findall(r"(?<![\w])([+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+))(?![\w])", str(text or ""))
        if not values:
            message = "Necesito un valor numérico positivo para preparar el cambio."
            msg = MensajeChatHostAI(rol="host_ai", tipo=TIPO_ADVERTENCIA, texto=message, datos={"datos_reales_modificados": False})
            self._mensajes.append(msg)
            return self._normalizar(msg)
        package_units = {
            "paquete": "paquete", "paquetes": "paquete", "caja": "caja", "cajas": "caja",
            "botella": "botella", "botellas": "botella", "bolsa": "bolsa", "bolsas": "bolsa",
            "bandeja": "bandeja", "bandejas": "bandeja", "lata": "lata", "latas": "lata",
            "saco": "saco", "sacos": "saco",
        }
        purchase_unit = next((canonical for token, canonical in package_units.items() if re.search(rf"\b{token}\b", normalized)), "")
        unit_count_signal = bool(re.search(r"\b(unidad|unidades|uds|piezas)\b", normalized))
        exact_physical_value = self._normalized_physical_value(
            normalized, str(capture.get("unidad_destino") or ""),
        ) if operation == "UPDATE_CONVERSION" else None
        physical_signal = (
            bool(re.search(r"\b(pesa|peso|equivale|equivalen)\b", normalized))
            or exact_physical_value is not None
        ) and str(capture.get("unidad_destino") or "") in {"kg", "g", "l", "ml"}
        format_signal = bool(purchase_unit) and unit_count_signal
        if operation == "UPDATE_CONVERSION" and unit_count_signal and not purchase_unit and not physical_signal:
            msg = MensajeChatHostAI(
                rol="host_ai", tipo=TIPO_ADVERTENCIA,
                texto="Entiendo que indicas unidades por envase, pero necesito saber si es un paquete, caja, botella u otro formato de compra.",
                datos={"datos_reales_modificados": False, "reason": "purchase_unit_required"},
            )
            self._mensajes.append(msg)
            return self._normalizar(msg)
        effective_operation = "UPDATE_FORMAT" if operation == "UPDATE_CONVERSION" and format_signal else operation
        if effective_operation == "UPDATE_FORMAT":
            quantity_match = re.search(r"\b(?:de|contiene|trae)\s+(\d+(?:[.,]\d+)?)\s+(?:unidad|unidades|uds|piezas)\b", normalized)
            if quantity_match is None:
                quantity_match = re.search(r"\b(?:entre|por)\s+(\d+(?:[.,]\d+)?)\b", normalized)
            captured_value = quantity_match.group(1) if quantity_match else values[-1]
        else:
            captured_value = (
                format(exact_physical_value, "f") if exact_physical_value is not None
                else values[-1] if effective_operation == "UPDATE_CONVERSION" else values[0]
            )
        proposed_price = self._explicit_user_price(text) if effective_operation == "UPDATE_FORMAT" else None
        if effective_operation == "UPDATE_FORMAT" and proposed_price is None and re.search(
            r"\bprecio\b[^.,;]*(?:nan|infinito|infinity)", str(text or ""), flags=re.IGNORECASE,
        ):
            return self._article_capture_warning("El precio aportado debe ser un número finito mayor que cero.", "invalid_price")
        if proposed_price is not None:
            if proposed_price <= 0 or not proposed_price.is_finite():
                return self._article_capture_warning("El precio aportado debe ser un número finito mayor que cero.", "invalid_price")
            read_service = getattr(self.tool_executor, "articulos_read_service", None)
            detail = dict(read_service.obtener(str(capture.get("articulo_id") or "")) or {}) if read_service else {}
            article = detail.get("articulo") if detail.get("ok") is not False else None
            canonical_price = self._decimal_value((article or {}).get("precio"))
            if canonical_price is not None and proposed_price != canonical_price:
                ttl = int(getattr(getattr(self.tool_executor, "article_change_service", None), "ttl_seconds", 900) or 900)
                self._session.captura_cambio_articulo = {
                    **capture, "phase": "PRICE_CONFLICT", "effective_operation": "UPDATE_FORMAT",
                    "format_value": captured_value, "unidad_compra": purchase_unit,
                    "unidad_contenido": "u", "canonical_price": str(canonical_price),
                    "proposed_price": str(proposed_price), "expires_monotonic": time.monotonic() + ttl,
                }
                label = "con IVA" if bool((article or {}).get("precio_incluye_iva")) else "sin IVA"
                return self._article_capture_warning(
                    f"El artículo tiene actualmente un precio de {self._decimal_text(canonical_price)} € {label} por {purchase_unit}, "
                    f"pero me has indicado {self._decimal_text(proposed_price)} €. ¿Quieres mantener "
                    f"{self._decimal_text(canonical_price)} € o cambiarlo a {self._decimal_text(proposed_price)} €?",
                    "PRICE_CONFLICT",
                )
            if canonical_price == proposed_price:
                proposed_price = None
        return self._prepare_article_change_preview(
            capture, effective_operation, captured_value, purchase_unit, context, started,
            precio_propuesto=proposed_price, source_text=text,
        )

    def _prepare_article_change_preview(
        self, capture: dict[str, Any], effective_operation: str, captured_value: Any,
        purchase_unit: str, context: dict[str, Any], started: float, *,
        precio_propuesto: Decimal | None = None, source_text: str = "",
    ) -> dict[str, Any]:
        tool_id = {
            "UPDATE_PRICE": "preparar_precio_articulo",
            "UPDATE_CONVERSION": "preparar_conversion_articulo",
            "UPDATE_FORMAT": "preparar_formato_articulo",
        }[effective_operation]
        result = self.tool_executor.execute_article_change_flow(tool_id, {
            "articulo_id": str(capture.get("articulo_id") or ""), "valor": captured_value,
            "unidad_origen": str(capture.get("unidad_origen") or ""),
            "unidad_destino": "u" if effective_operation == "UPDATE_FORMAT" else str(capture.get("unidad_destino") or ""),
            "unidad_compra": purchase_unit if effective_operation == "UPDATE_FORMAT" else "",
            "precio_propuesto": str(precio_propuesto) if precio_propuesto is not None else None,
        }, request_id=str(context.get("_host_ai_request_id") or "chat-article-preview"))
        if result.estado != "OK":
            msg = MensajeChatHostAI(rol="host_ai", tipo=TIPO_ADVERTENCIA, texto=str(result.mensaje), datos={"datos_reales_modificados": False, "reason": str((result.errores or ["preview_error"])[0])})
            self._mensajes.append(msg)
            return self._normalizar(msg)
        preview = dict(result.datos or {})
        self._session.captura_cambio_articulo = {}
        self._session.confirmacion_articulo_pendiente = {
            "preview_token": str(preview.get("preview_token") or ""),
            "operacion": effective_operation, "articulo_id": str(capture.get("articulo_id") or ""),
            "receta_id": str(capture.get("receta_id") or ""),
            "incidencia": str(capture.get("incidencia") or ""),
            "expira_en": str(preview.get("expira_en") or ""),
        }
        actions = [
            {"action_id": "APPLY_PENDING_ARTICLE_CHANGE", "label": "Aplicar cambio"},
            {"action_id": "DISCARD_PENDING_ARTICLE_CHANGE", "label": "Descartar"},
        ]
        public_preview = dict(preview.get("presentation") or {})
        intro = "Entendido: son unidades por envase, no una conversión física. " if effective_operation == "UPDATE_FORMAT" else ""
        msg = MensajeChatHostAI(rol="host_ai", tipo=TIPO_RESULTADO, texto=f"{intro}He preparado el cambio. Revisa los datos y elige una opción.", datos={"preview": public_preview, "economic_actions": actions, "datos_reales_modificados": False})
        self._mensajes.append(msg)
        self._registrar_log(source_text, {"tipo_mensaje": TIPO_RESULTADO, "datos": msg.datos}, started)
        return self._normalizar(msg)

    def _resolve_article_price_conflict(
        self, text: str, capture: dict[str, Any], context: dict[str, Any], started: float,
    ) -> dict[str, Any]:
        normalized = self._normalizar_texto(text)
        if any(term in normalized for term in ("descartar", "cancela", "cancelar")):
            self._session.captura_cambio_articulo = {}
            return self._article_capture_warning("Cambio descartado sin modificar el artículo.", "PRICE_CONFLICT_DISCARDED")
        if time.monotonic() > float(capture.get("expires_monotonic") or 0):
            self._session.captura_cambio_articulo = {}
            return self._article_capture_warning("La aclaración de precio ha caducado; inicia de nuevo el cambio.", "expired_price_conflict")
        canonical = self._decimal_value(capture.get("canonical_price"))
        proposed = self._decimal_value(capture.get("proposed_price"))
        numeric = self._explicit_resolution_number(text)
        use_proposed = any(term in normalized for term in ("el nuevo", "he dicho", "cambia", "cambialo"))
        use_canonical = any(term in normalized for term in ("manten", "actual", "estaba", "deja el"))
        if numeric is not None:
            if numeric == proposed:
                use_proposed = True
            elif numeric == canonical:
                use_canonical = True
            else:
                return self._article_capture_warning("Indica si quieres mantener el precio actual o usar el precio aportado.", "PRICE_CONFLICT_UNRESOLVED")
        if use_proposed == use_canonical or canonical is None or proposed is None:
            return self._article_capture_warning("Indica si quieres mantener el precio actual o usar el precio aportado.", "PRICE_CONFLICT_UNRESOLVED")
        base_capture = {key: value for key, value in capture.items() if key not in {
            "phase", "effective_operation", "format_value", "unidad_compra", "unidad_contenido",
            "canonical_price", "proposed_price", "expires_monotonic",
        }}
        return self._prepare_article_change_preview(
            base_capture, "UPDATE_FORMAT", capture.get("format_value"), str(capture.get("unidad_compra") or ""),
            context, started, precio_propuesto=proposed if use_proposed else None, source_text=text,
        )

    @classmethod
    def _explicit_user_price(cls, text: str) -> Decimal | None:
        raw = str(text or "")
        patterns = (
            r"\bprecio(?:\s+(?:sin|con)\s+iva)?(?:\s+del?\s+[\wÀ-ÿ-]+)?\s*(?:es|:)?\s*([+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+))",
            r"(?<![\w])([+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+))\s*€",
        )
        for pattern in patterns:
            match = re.search(pattern, raw, flags=re.IGNORECASE)
            if match:
                return cls._decimal_value(match.group(1))
        return None

    @classmethod
    def _explicit_resolution_number(cls, text: str) -> Decimal | None:
        values = re.findall(r"(?<![\w])([+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+))(?![\w])", str(text or ""))
        return cls._decimal_value(values[0]) if len(values) == 1 else None

    @classmethod
    def _explicit_physical_range(cls, text: str) -> tuple[Decimal, Decimal, str] | None:
        number = r"([+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+))"
        unit = r"(kg|kilogramos?|kilos?|g|gramos?|l|litros?|ml|mililitros?)"
        patterns = (
            rf"\bentre\s+{number}\s*(?:{unit})?\s+y\s+{number}\s*{unit}\b",
            rf"\bde\s+{number}\s*(?:{unit})?\s+a\s+{number}\s*{unit}\b",
            rf"(?<![\w]){number}\s*(?:{unit})?\s*[-–—]\s*{number}\s*{unit}\b",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match is None:
                continue
            groups = match.groups()
            lower = cls._decimal_value(groups[0])
            if len(groups) == 4:
                first_unit, upper_raw, final_unit = groups[1], groups[2], groups[3]
            else:
                first_unit, upper_raw, final_unit = groups[1], groups[2], groups[3]
            upper = cls._decimal_value(upper_raw)
            canonical_unit = cls._canonical_physical_unit(final_unit or first_unit)
            if lower is not None and upper is not None and canonical_unit:
                return min(lower, upper), max(lower, upper), canonical_unit
        return None

    @classmethod
    def _normalized_physical_value(cls, text: str, target_unit: str) -> Decimal | None:
        match = re.search(
            r"(?<![\w])([+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+))\s*"
            r"(kg|kilogramos?|kilos?|g|gramos?|l|litros?|ml|mililitros?)\b",
            text,
        )
        if match is None:
            return None
        value = cls._decimal_value(match.group(1))
        source = cls._canonical_physical_unit(match.group(2))
        target = cls._canonical_physical_unit(target_unit)
        if value is None or source is None or target is None:
            return None
        converted = convert_quantity(value, source, target)
        if converted is None:
            return None
        if (source, target) in {("g", "kg"), ("ml", "l")} and converted != converted.to_integral_value():
            return converted.quantize(Decimal("0.001"))
        return converted.normalize()

    @staticmethod
    def _canonical_physical_unit(unit: Any) -> str | None:
        normalized = str(unit or "").strip().lower()
        canonical = normalize_unit(normalized)
        return canonical if canonical in {"g", "kg", "ml", "l"} else None

    @staticmethod
    def _decimal_value(value: Any) -> Decimal | None:
        try:
            parsed = Decimal(str(value).strip().replace(",", "."))
        except (InvalidOperation, ValueError):
            return None
        return parsed if parsed.is_finite() else None

    @staticmethod
    def _decimal_text(value: Decimal) -> str:
        return format(value.normalize(), "f")

    def _article_capture_warning(self, text: str, reason: str) -> dict[str, Any]:
        msg = MensajeChatHostAI(
            rol="host_ai", tipo=TIPO_ADVERTENCIA, texto=text,
            datos={"economic_actions": [], "datos_reales_modificados": False, "reason": reason},
        )
        self._mensajes.append(msg)
        return self._normalizar(msg)

    def _execute_pending_article_change(self, action: str, context: dict[str, Any]) -> dict[str, Any]:
        pending = dict(self._session.confirmacion_articulo_pendiente or {})
        token = str(pending.get("preview_token") or "")
        if not token:
            return self._chat_action_message("No hay un cambio de artículo pendiente.", TIPO_ADVERTENCIA, reason="confirmation_missing")
        tool_id = "confirmar_cambio_articulo" if action == "APPLY_PENDING_ARTICLE_CHANGE" else "descartar_cambio_articulo"
        result = self.tool_executor.execute_article_change_flow(tool_id, {"preview_token": token}, request_id=str(context.get("_host_ai_request_id") or "chat-article-confirm"))
        if result.estado != "OK":
            return self._chat_action_message(str(result.mensaje), TIPO_ADVERTENCIA, reason=str((result.errores or ["confirmation_error"])[0]))
        self._session.confirmacion_articulo_pendiente = {}
        modified = bool((result.datos or {}).get("datos_reales_modificados", False))
        actions: list[dict[str, str]] = []
        recipe_id = str(pending.get("receta_id") or "")
        if modified and recipe_id:
            context_id = uuid4().hex
            self._session.acciones_economicas_contextuales = {
                "CHECK_ESCANDALLO_COST": {
                    "context_id": context_id,
                    "receta_id": recipe_id,
                    "articulo_id": str(pending.get("articulo_id") or ""),
                    "incidencia_previa": str(pending.get("incidencia") or ""),
                    "session_id": self.session_id,
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
            }
            actions = [{
                "action_id": "CHECK_ESCANDALLO_COST",
                "action_context_id": context_id,
                "label": "Comprobar escandallo",
            }]
        elif not modified:
            self._session.acciones_economicas_contextuales = {}
        data = {"economic_actions": actions, "datos_reales_modificados": modified, "article_change": dict(result.datos or {})}
        text = "Artículo actualizado. ¿Quieres comprobar ahora el estado económico del escandallo?" if actions else ("Artículo actualizado. El escandallo debe recalcularse para comprobar su estado económico." if modified else "Cambio descartado sin modificar el artículo.")
        msg = MensajeChatHostAI(rol="host_ai", tipo=TIPO_RESULTADO, texto=text, datos=data)
        self._mensajes.append(msg)
        return self._normalizar(msg)

    def _execute_escandallo_cost_check(self, action_context_id: str) -> dict[str, Any]:
        snapshot = dict(self._session.acciones_economicas_contextuales or {})
        stored = snapshot.get("CHECK_ESCANDALLO_COST") if isinstance(snapshot.get("CHECK_ESCANDALLO_COST"), dict) else {}
        if (
            not stored
            or str(stored.get("context_id") or "") != str(action_context_id or "")
            or str(stored.get("session_id") or "") != self.session_id
        ):
            return self._chat_action_message(
                "Esta comprobación económica ya no está disponible.", TIPO_ADVERTENCIA,
                reason="stale_escandallo_check",
            )
        recipe_id = str(stored.get("receta_id") or "").strip()
        service = getattr(self.tool_executor, "escandallos_read_service", None)
        if not recipe_id or service is None:
            self._session.acciones_economicas_contextuales = {}
            return self._chat_action_message(
                "No puedo comprobar ese escandallo de forma segura.", TIPO_ADVERTENCIA,
                reason="escandallo_check_unavailable",
            )
        result = dict(service.consultar(
            agregacion="DETAIL_COSTE_INCOMPLETO", escandallo_id=recipe_id,
        ) or {})
        self._session.acciones_economicas_contextuales = {}
        if result.get("ok") is False or str(result.get("estado") or "OK") not in {"OK", "RESUELTO"}:
            return self._chat_action_message(
                "La receta o su escandallo ya no están disponibles.", TIPO_ADVERTENCIA,
                reason="escandallo_check_not_found",
            )
        incidents = [{
            "receta_id": str(result.get("receta_id") or recipe_id),
            "incidencia": str(reason.get("tipo") or ""),
            "articulo_id": str(reason.get("articulo_id") or ""),
            "nombre": str(reason.get("nombre") or ""),
            "unidad_origen": str(reason.get("unidad_origen") or ""),
            "unidad_destino": str(reason.get("unidad_destino") or ""),
            "detalle": str(reason.get("detalle") or ""),
        } for reason in list(result.get("motivos") or [])[:10] if isinstance(reason, dict)]
        self._session.economic_incidents = incidents
        state = str(result.get("estado_coste") or "SIN_COSTE")
        active = dict(self._session.escandallo_activo or self._session.receta_activa or {})
        active.update({
            "id": str(result.get("receta_id") or recipe_id),
            "nombre": str(result.get("nombre") or active.get("nombre") or ""),
            "estado_coste": state,
            "coste_total": result.get("coste_total"),
            "coste_por_racion": result.get("coste_por_racion"),
        })
        self._session.escandallo_activo = active
        actions = self._economic_actions() if incidents else []
        if result.get("coste_completo") is True or state == "DISPONIBLE":
            total = result.get("coste_total")
            per_portion = result.get("coste_por_racion")
            text = "El escandallo ya está completo y disponible."
            if total is not None:
                text += f" Coste total: {str(total).replace('.', ',')} €."
            if per_portion is not None:
                text += f" Coste por ración: {str(per_portion).replace('.', ',')} €."
        elif state == "SIN_ESCANDALLO":
            text = (
                "El coste está incompleto porque esta receta no tiene un escandallo registrado. "
                "Por eso no hay un coste total ni un coste por ración calculable."
            )
        elif incidents:
            causes = "; ".join(
                " — ".join(value for value in (
                    str(item.get("incidencia") or ""), str(item.get("nombre") or ""),
                    str(item.get("detalle") or ""),
                ) if value) for item in incidents
            )
            text = f"El escandallo sigue {state} por: {causes}."
        else:
            text = f"El escandallo sigue {state}, pero el cálculo actual no expone una causa concreta."
        navigation = None
        if state != "SIN_ESCANDALLO":
            navigation = self._validated_ui_action({
                "type": "OPEN_VIEW", "target": "ELABORACION", "id": recipe_id,
                "view": "ESCANDALLO", "label": str(result.get("nombre") or active.get("nombre") or recipe_id),
            })
        msg = MensajeChatHostAI(
            rol="host_ai", tipo=TIPO_RESULTADO, texto=text,
            datos={
                "economic_actions": actions, "economic_check": result,
                "ui_action": navigation, "ui_action_mode": "OFFER" if navigation else None,
                "datos_reales_modificados": False,
            },
        )
        self._mensajes.append(msg)
        return self._normalizar(msg)

    def _chat_action_message(
        self, text: str, message_type: str, *, reason: str = "",
        ui_action: dict[str, Any] | None = None,
        preview: dict[str, Any] | None = None,
        recipe_actions: list[dict[str, Any]] | None = None,
        datos_reales_modificados: bool = False,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "economic_actions": [], "datos_reales_modificados": bool(datos_reales_modificados),
        }
        if reason:
            data["reason"] = reason
        if ui_action:
            data["ui_action"] = self._validated_ui_action(ui_action)
        if preview is not None:
            data["preview"] = dict(preview)
        if recipe_actions is not None:
            data["recipe_actions"] = list(recipe_actions)
        msg = MensajeChatHostAI(rol="host_ai", tipo=message_type, texto=text, datos=data)
        self._mensajes.append(msg)
        return self._normalizar(msg)

    def _economic_actions(self) -> list[dict[str, str]]:
        if str((self._session.confirmacion_articulo_pendiente or {}).get("preview_token") or ""):
            return [
                {"action_id": "APPLY_PENDING_ARTICLE_CHANGE", "label": "Aplicar cambio"},
                {"action_id": "DISCARD_PENDING_ARTICLE_CHANGE", "label": "Descartar"},
            ]
        supported = {
            "SIN_PRECIO": ("RESOLVE_MISSING_PRICE", "Completar precio"),
            "CONVERSION_NO_DISPONIBLE": ("RESOLVE_MISSING_CONVERSION", "Configurar conversión"),
        }
        canonical_incident = {
            "PRODUCTO_SIN_PRECIO": "SIN_PRECIO",
            "CONVERSION_INEXISTENTE": "CONVERSION_NO_DISPONIBLE",
            "UNIDAD_INCOMPATIBLE": "CONVERSION_NO_DISPONIBLE",
            "UNIDADES_INCOMPATIBLES": "CONVERSION_NO_DISPONIBLE",
        }
        actions: list[dict[str, str]] = []
        snapshots: dict[str, dict[str, str]] = {}
        read_service = getattr(self.tool_executor, "articulos_read_service", None)
        write_context = getattr(self.tool_executor, "write_context", None)
        if not write_context or "articulos:preview" not in set(getattr(write_context, "scopes", ()) or ()):
            self._session.acciones_economicas_contextuales = {}
            return []
        for incident in list(self._session.economic_incidents or [])[:10]:
            raw_kind = str(incident.get("incidencia") or "").upper()
            kind = canonical_incident.get(raw_kind, raw_kind)
            article_id = str(incident.get("articulo_id") or "").strip()
            contract = supported.get(kind)
            if not contract or not article_id or contract[0] in snapshots or read_service is None:
                continue
            detail = dict(read_service.obtener(article_id) or {})
            article = detail.get("articulo") if detail.get("ok") is not False else None
            if str((article or {}).get("id") or "") != article_id:
                continue
            action_id, label = contract
            context_id = uuid4().hex
            snapshots[action_id] = {
                "context_id": context_id,
                "receta_id": str(incident.get("receta_id") or ""),
                "incidencia": kind,
                "articulo_id": article_id,
                "unidad_origen": str(incident.get("unidad_origen") or ""),
                "unidad_destino": str(incident.get("unidad_destino") or ""),
            }
            actions.append({
                "action_id": action_id, "action_context_id": context_id,
                "label": label,
            })
        self._session.acciones_economicas_contextuales = snapshots
        return actions

    def _reservation_action_message(self, text: str, message_type: str, *, reason: str = "", ui_action: dict[str, Any] | None = None, preview: dict[str, Any] | None = None) -> dict[str, Any]:
        actions = self._catalog_confirmation_actions() or self._reservation_actions()
        data: dict[str, Any] = {"reservation_actions": actions, "confirmation_actions": actions, "datos_reales_modificados": False}
        if reason:
            data["reason"] = reason
        if ui_action:
            data["ui_action"] = dict(ui_action)
        if preview:
            data["preview"] = dict(preview)
        msg = MensajeChatHostAI(rol="host_ai", tipo=message_type, texto=text, datos=data)
        self._mensajes.append(msg)
        return self._normalizar(msg)

    def _catalog_confirmation_actions(self) -> list[dict[str, str]]:
        pending = dict(self._session.confirmacion_catalogo_pendiente or {})
        token = str(pending.get("preview_token") or "")
        if not token:
            return []
        try:
            if datetime.fromisoformat(str(pending.get("expira_en") or "")) < datetime.now():
                self._session.confirmacion_catalogo_pendiente = {}
                return []
        except ValueError:
            self._session.confirmacion_catalogo_pendiente = {}
            return []
        context_id = token[-12:]
        return [
            {"action_id": "APPLY_PENDING_CATALOG_CREATE", "action_context_id": context_id, "label": "Confirmar", "style": "primary"},
            {"action_id": "DISCARD_PENDING_CATALOG_CREATE", "action_context_id": context_id, "label": "Cancelar", "style": "secondary"},
        ]

    def _pending_catalog_write(self) -> dict[str, Any] | None:
        pending = dict(self._session.confirmacion_catalogo_pendiente or {})
        actions = self._catalog_confirmation_actions()
        if not actions:
            return None
        return {
            "operation": str(pending.get("operacion") or "CREAR"),
            "domain": str(pending.get("dominio") or ""),
            "preview": dict(pending.get("payload") or {}),
            "confirmation_required": True,
            "actions": actions,
        }

    def _try_safe_catalog_create_without_provider(self, content: str, request_id: str) -> dict[str, Any] | None:
        normalized = self._normalizar_texto(content)
        if not re.search(r"\b(crea|crear|guarda|guardar)\b", normalized):
            return None
        domain, payload = "", {}
        if re.search(r"\bevento\b", normalized):
            domain = "EVENTO"
            date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", content)
            event_date = date_match.group(1) if date_match else ""
            if re.search(r"\bmanana\b", normalized):
                from datetime import timedelta
                event_date = (datetime.now() + timedelta(days=1)).date().isoformat()
            time_match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", content)
            pax_match = re.search(r"\b(?:para\s+)?(\d+)\s*(?:personas|pax)\b", normalized)
            name_match = re.search(r"\bevento\s+(?:llamado\s+|de\s+)?(.+?)(?=\s+para\s+ma(?:n|ñ)ana|\s+ma(?:n|ñ)ana|\s+el\s+20\d{2}-|\s+a\s+las\s+\d|\s+para\s+\d+\s*(?:personas|pax)|[.,]|$)", content, re.IGNORECASE)
            name = str(name_match.group(1) if name_match else "").strip()
            if not name or not event_date or not pax_match:
                return {"mensaje": "Necesito nombre, fecha y número de personas para preparar el evento.", "datos": {"datos_reales_modificados": False}}
            payload = {"nombre": name[:120], "fecha": event_date, "pax": int(pax_match.group(1))}
            if time_match:
                payload["hora_inicio"] = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
        elif re.search(r"\barticulo\b", normalized):
            domain = "ARTICULO"
            name_match = re.search(r"\bart[ií]culo\s+(?:llamado\s+)?(.+?)(?=,|\s+unidad\s+|\s+proveedor\s+|$)", content, re.IGNORECASE)
            unit_match = re.search(r"\bunidad(?:\s+base)?\s+([\w.-]+)", content, re.IGNORECASE)
            provider_match = re.search(r"\bproveedor\s+([^,.]+)", content, re.IGNORECASE)
            name = str(name_match.group(1) if name_match else "").strip()
            if not name:
                return {"mensaje": "Necesito el nombre del artículo para preparar su creación.", "datos": {"datos_reales_modificados": False}}
            code = "ART-" + re.sub(r"[^A-Z0-9]+", "-", self._normalizar_texto(name).upper()).strip("-")[:40]
            payload = {"nombre": name, "codigo": code}
            if unit_match: payload["unidad_base"] = unit_match.group(1)
            if provider_match: payload["proveedor"] = provider_match.group(1).strip()
        elif re.search(r"\breceta\b", normalized) and self._session.propuesta_receta_activa:
            domain, payload = "RECETA", dict(self._session.propuesta_receta_activa)
        else:
            return None
        tool_id = {"EVENTO": "preparar_creacion_evento", "ARTICULO": "preparar_creacion_articulo", "RECETA": "preparar_creacion_receta"}[domain]
        result = self._catalog_executor.execute_catalog_create_flow(tool_id, payload, request_id=request_id)
        if result.estado != "OK":
            return {"mensaje": result.mensaje, "datos": {"datos_reales_modificados": False, "reason": (result.errores or ["preview_error"])[0]}}
        self._aplicar_resultado_tool_en_sesion({"contexto_actualizado": result.contexto_actualizado})
        pending_write = self._pending_catalog_write()
        actions = list((pending_write or {}).get("actions") or [])
        return {
            "mensaje": f"He preparado la creación de {domain.lower()}. Revisa los datos antes de continuar.",
            "datos": {
                "pending_write": pending_write,
                "preview": dict((pending_write or {}).get("preview") or {}),
                "confirmation_actions": actions,
                "reservation_actions": actions,
                "datos_reales_modificados": False,
            },
        }

    def _reservation_detail(self, reservation_id: str) -> dict[str, Any]:
        read_service = getattr(self.tool_executor, "reservas_read_service", None)
        return dict(read_service.detalle(reservation_id) or {}) if read_service and reservation_id else {}

    def _reservation_actions(self) -> list[dict[str, str]]:
        pending = dict(self._session.confirmacion_reserva_pendiente or {})
        if str(pending.get("preview_token") or ""):
            try:
                if datetime.fromisoformat(str(pending.get("expira_en") or "")) < datetime.now():
                    return []
            except ValueError:
                return []
            self._session.acciones_reserva_contextuales = {}
            return [
                {"action_id": "APPLY_PENDING_RESERVATION", "label": "Aplicar cambio", "style": "primary"},
                {"action_id": "DISCARD_PENDING_RESERVATION", "label": "Descartar", "style": "secondary"},
            ]
        active = dict(self._session.reserva_activa or {})
        reservation_id = str(active.get("reserva_id") or active.get("id") or "")
        current = self._reservation_detail(reservation_id)
        if not current:
            self._session.acciones_reserva_contextuales = {}
            return []
        self._session.reserva_activa = current
        state = str(current.get("estado") or "").upper()
        context_id = uuid4().hex
        self._session.acciones_reserva_contextuales = {"reserva_id": reservation_id, "estado": state, "context_id": context_id}
        by_state = {
            "PENDIENTE": ["CONFIRM_RESERVATION", "EDIT_RESERVATION", "CANCEL_RESERVATION", "OPEN_RESERVATION"],
            "CONFIRMADA": ["EDIT_RESERVATION", "CANCEL_RESERVATION", "MARK_RESERVATION_NO_SHOW", "COMPLETE_RESERVATION", "OPEN_RESERVATION"],
            "CANCELADA": ["OPEN_RESERVATION"], "NO_SHOW": ["OPEN_RESERVATION"], "COMPLETADA": ["OPEN_RESERVATION"],
        }
        labels = {
            "CONFIRM_RESERVATION": "Confirmar reserva", "EDIT_RESERVATION": "Modificar",
            "CANCEL_RESERVATION": "Cancelar reserva", "MARK_RESERVATION_NO_SHOW": "Marcar no-show",
            "COMPLETE_RESERVATION": "Completar", "OPEN_RESERVATION": "Abrir ficha",
        }
        secondary = {"EDIT_RESERVATION", "OPEN_RESERVATION"}
        return [{"action_id": item, "action_context_id": context_id, "label": labels[item], "style": "secondary" if item in secondary else "primary"} for item in by_state.get(state, [])]

    def estado_sesion(self) -> dict[str, Any]:
        return self._session.to_dict()

    def _try_recipe_completion(self, content: str) -> dict[str, Any] | None:
        normalized = self._normalizar_texto(content)
        requested = any(phrase in normalized for phrase in (
            "termina esta receta", "terminala", "terminamela", "completar esta receta",
            "completa esta receta", "que le falta", "dejame esta receta lista",
        ))
        if not requested:
            return None
        active = dict(self._session.receta_activa or self._session.escandallo_activo or {})
        recipe_id = str(active.get("id") or active.get("codigo") or "").strip()
        if not recipe_id:
            return {
                "mensaje": "Puedo revisarla de principio a fin, pero todavía no tengo una receta concreta abierta.",
                "datos": {"recipe_completion": {"estado": "REQUIERE_RECETA", "datos_reales_modificados": False}},
            }
        route, workflow = self.conversation_brain.prepare_turn(
            content, self._session.workflow_activo, active,
        )
        result = self.recipe_completion_workflow.investigate(recipe_id)
        if result.procedure_proposal:
            self._session.confirmacion_procedimiento_receta_pendiente = {
                "recipe_id": result.recipe_id,
                "procedure": result.procedure_proposal,
                "estado": "PROPUESTA_PENDIENTE",
            }
        relation = next((item for item in result.actions if item.get("action_id") == "PREVIEW_INGREDIENT_RELATION"), None)
        if isinstance(relation, dict) and relation.get("article_id"):
            self._session.confirmacion_relacion_ingrediente_pendiente = {
                "recipe_id": str(relation.get("recipe_id") or result.recipe_id),
                "ingredient_index": int(relation.get("ingredient_index") or 0),
                "article_id": str(relation.get("article_id") or ""),
                "estado": "PROPUESTA_PENDIENTE",
            }
        updated = self.conversation_brain.record_tool_results(workflow.to_dict(), ["consultar_escandallos", "buscar_articulos"])
        self._session.actualizar_workflow(updated.to_dict())
        self.agent_observability.emit(
            "recipe_completion_investigation",
            model_tier=route.tier, reasoning_effort=route.reasoning_effort,
            routing_reason=route.reason, workflow_type=updated.workflow_type,
        )
        return {
            "mensaje": result.summary,
            "datos": {
                "recipe_completion": result.to_dict(),
                "workflow": self._session.workflow_activo,
                "recipe_actions": result.actions,
                "datos_reales_modificados": False,
            },
        }

    def _try_recipe_request(self, content: str) -> dict[str, Any] | None:
        """Resuelve peticiones culinarias directas usando la biblioteca canónica existente."""
        if self._general_agent_enabled():
            return None
        normalized = self._normalizar_texto(content)
        completion_markers = (
            "completa", "completar", "termina esta receta", "que le falta",
            "proponer una receta con ia", "crear la receta conmigo", "vincular una receta",
        )
        is_recipe_request = self._is_direct_recipe_goal(normalized)
        if not is_recipe_request or any(marker in normalized for marker in completion_markers):
            return None
        opening = any(marker in normalized for marker in ("abre ", "abrir ", "abreme "))
        term = re.sub(
            r"^(?:como se prepara|dame|muestrame|ensename|busca|buscar|abre|abrir|abreme)\s+",
            "", normalized,
        )
        term = re.sub(r"^(?:la\s+)?receta(?:\s+de)?\s+", "", term)
        term = " ".join(term.strip(" ?.!").split())
        if not term:
            return None
        response = self.recipe_completion_workflow.recipes.consultar("detalle", termino=term, limite=10)
        state = str(response.get("estado") or "NO_ENCONTRADO").upper()
        if state == "AMBIGUO":
            candidates = [dict(item) for item in list(response.get("elaboraciones") or [])[:10] if isinstance(item, dict)]
            self._session.contexto_activo = "RECETA"
            self._session.ultima_lista_mostrada = candidates
            names = "\n".join(f"{index}. {item.get('nombre') or item.get('id')}" for index, item in enumerate(candidates, 1))
            return {"mensaje": f"He encontrado varias recetas posibles:\n\n{names}\n\n¿Cuál quieres usar?",
                    "datos": {"estado": "AMBIGUO", "candidatos": candidates, "datos_reales_modificados": False}}
        detail = response.get("elaboracion")
        if state != "OK" or not isinstance(detail, dict):
            options = list(MISSING_RECIPE_OPTIONS)
            return {"mensaje": "⚠️ No encuentro esta receta en Host AI.\n\n¿Qué quieres hacer?\n\n" +
                    "\n".join(f"{index}. {option}" for index, option in enumerate(options, 1)),
                    "datos": {"estado": "NO_ENCONTRADO", "recipe_options": options, "datos_reales_modificados": False}}

        recipe_id = str(detail.get("id") or detail.get("codigo") or "")
        active = {"id": recipe_id, "codigo": detail.get("codigo"), "nombre": detail.get("nombre"), "tipo": "RECETA"}
        self._session.contexto_activo = "RECETA"
        self._session.receta_activa = active
        if opening:
            tool_result = self.tool_executor.execute_agent_read(
                "abrir_elaboracion", {"elaboracion_id": recipe_id, "vista": "receta"},
            )
            action = dict((tool_result.datos or {}).get("ui_action") or {})
            return {"mensaje": f"He abierto {detail.get('nombre') or recipe_id}.",
                    "datos": {"estado": "OK", "ui_action": action, "ui_actions": [action] if action else [],
                              "datos_reales_modificados": False}}

        investigation = self.recipe_completion_workflow.investigate(recipe_id)
        ingredients = []
        for item in list(detail.get("ingredientes") or []):
            if not isinstance(item, dict):
                continue
            name = item.get("nombre_articulo") or item.get("nombre_original") or item.get("nombre") or "Ingrediente"
            amount, unit = item.get("cantidad"), item.get("unidad")
            ingredients.append(f"- {name}" + (f" — {amount} {unit or ''}" if amount not in (None, "") else ""))
        lines = [f"# {detail.get('nombre') or recipe_id}"]
        if detail.get("rendimiento") not in (None, ""):
            lines.extend(["", f"**Rendimiento:** {detail.get('rendimiento')} {detail.get('unidad_rendimiento') or ''}".rstrip()])
        lines.extend(["", "## Ingredientes", "", *(ingredients or ["No hay ingredientes registrados."])])
        procedure = str(detail.get("procedimiento") or "").strip()
        lines.extend(["", "## Preparación", "", procedure or "⚠️ Falta el procedimiento."])
        for title, key in (("Tiempo", "tiempo_total"), ("Conservación", "conservacion"), ("Alérgenos", "alergenos"), ("Observaciones", "observaciones")):
            value = detail.get(key)
            if value not in (None, "", [], {}):
                lines.extend(["", f"## {title}", "", str(value)])
        missing = [str(item.get("campo")) for item in investigation.completeness.get("FALTA", []) if isinstance(item, dict)]
        actions = list(investigation.actions)
        if missing:
            lines.extend(["", "⚠️ Faltan datos en esta receta", "", *[f"- {item}" for item in dict.fromkeys(missing)], "",
                          "1. Completar la receta conmigo", "2. Proponer una receta con IA", "3. Dejarla como está"])
        return {"mensaje": "\n".join(lines), "datos": {"estado": "OK", "receta": detail,
                "recipe_completion": investigation.to_dict(), "recipe_actions": actions,
                "datos_reales_modificados": False}}

    @staticmethod
    def _is_direct_recipe_goal(normalized: str) -> bool:
        """Solo da prioridad al fallback cuando la receta es el objetivo raíz explícito."""
        text = str(normalized or "").strip(" ¿?!.\t\r\n")
        higher_goals = (
            "menu", "produccion", "evento", "aprovisionamiento", "necesidades",
            "stock", "compras", "analiza", "organiza", "multifuente",
        )
        if any(re.search(rf"\b{re.escape(goal)}\b", text) for goal in higher_goals):
            return False
        return bool(re.match(
            r"^(?:dame|muestrame|ensename|busca|buscar|abre|abrir|abreme)\s+"
            r"(?:(?:la|una)\s+)?receta\b|^como\s+se\s+(?:prepara|hace)\b",
            text,
        ))

    def _try_production_planning(self, content: str) -> dict[str, Any] | None:
        normalized = self._normalizar_texto(content)
        if not any(phrase in normalized for phrase in ("hazme la produccion", "preparame la produccion", "plan de produccion")):
            return None
        active_event = dict(self._session.evento_activo or {})
        term = normalized.replace("hazme la produccion", "").replace("preparame la produccion", "").replace("de la", "").strip()
        route, workflow = self.conversation_brain.prepare_turn(content, self._session.workflow_activo, active_event)
        result = self.production_workflow.investigate(term, active_event)
        updated = self.conversation_brain.record_tool_results(workflow.to_dict(), ["consultar_eventos", "consultar_produccion"])
        self._session.actualizar_workflow(updated.to_dict())
        return {"mensaje": self.production_workflow.professional_summary(result), "datos": {"production_completion": result.to_dict(), "workflow": self._session.workflow_activo, "datos_reales_modificados": False}}

    def _preview_recipe_procedure(self) -> dict[str, Any]:
        pending = dict(self._session.confirmacion_procedimiento_receta_pendiente or {})
        if not pending:
            return self._chat_action_message("No hay una propuesta de procedimiento pendiente.", TIPO_ADVERTENCIA, reason="recipe_procedure_missing")
        try:
            preview = self.recipe_procedure_service.preview(
                recipe_id=str(pending.get("recipe_id") or ""), procedure=str(pending.get("procedure") or ""),
                context=self.tool_executor.write_context,
            )
        except ErrorConfirmacionProcedimientoReceta as exc:
            return self._chat_action_message(str(exc), TIPO_ADVERTENCIA, reason=exc.code)
        self._session.confirmacion_procedimiento_receta_pendiente = {
            **pending, "preview_token": str(preview.get("preview_token") or ""), "estado": "LISTO_PARA_CONFIRMAR",
        }
        return self._chat_action_message(
            "He preparado la propuesta de procedimiento. Revísala y confirma solo si quieres guardarla.", TIPO_RESULTADO,
            preview={key: preview.get(key) for key in ("recipe_id", "nombre", "procedimiento_actual", "procedimiento_propuesto", "origen_propuesta")},
            recipe_actions=[{"action_id": "CONFIRM_RECIPE_PROCEDURE", "label": "Guardar procedimiento"}],
        )

    def _confirm_recipe_procedure(self, request_id: str) -> dict[str, Any]:
        pending = dict(self._session.confirmacion_procedimiento_receta_pendiente or {})
        if str(pending.get("estado") or "") != "LISTO_PARA_CONFIRMAR":
            return self._chat_action_message("Primero prepara y revisa la propuesta de procedimiento.", TIPO_ADVERTENCIA, reason="recipe_procedure_confirmation_missing")
        try:
            context = self.tool_executor.write_context
            result = self.recipe_procedure_service.confirm(
                recipe_id=str(pending.get("recipe_id") or ""), procedure=str(pending.get("procedure") or ""),
                preview_token=str(pending.get("preview_token") or ""), context=context,
            )
        except ErrorConfirmacionProcedimientoReceta as exc:
            return self._chat_action_message(str(exc), TIPO_ADVERTENCIA, reason=exc.code)
        self._session.confirmacion_procedimiento_receta_pendiente = {}
        return self._chat_action_message(
            "He guardado el procedimiento confirmado." if result.get("datos_reales_modificados") else "El procedimiento ya estaba guardado.",
            TIPO_RESULTADO, datos_reales_modificados=bool(result.get("datos_reales_modificados")),
        )

    def _preview_ingredient_relation(self) -> dict[str, Any]:
        pending = dict(self._session.confirmacion_relacion_ingrediente_pendiente or {})
        if not pending:
            return self._chat_action_message("No hay una relación de ingrediente pendiente.", TIPO_ADVERTENCIA, reason="ingredient_relation_missing")
        try:
            preview = self.ingredient_relation_service.preview(
                recipe_id=str(pending.get("recipe_id") or ""), ingredient_index=int(pending.get("ingredient_index") or 0),
                article_id=str(pending.get("article_id") or ""), context=self.tool_executor.write_context,
            )
        except ErrorConfirmacionRelacionIngrediente as exc:
            return self._chat_action_message(str(exc), TIPO_ADVERTENCIA, reason=exc.code)
        self._session.confirmacion_relacion_ingrediente_pendiente = {
            **pending, "preview_token": str(preview.get("preview_token") or ""), "estado": "LISTO_PARA_CONFIRMAR",
        }
        article = dict(preview.get("articulo_propuesto") or {})
        return self._chat_action_message(
            f"He encontrado una coincidencia clara para {preview.get('ingrediente')}: {article.get('nombre')}. Puedo relacionarla con este ingrediente.",
            TIPO_RESULTADO, preview={"ingrediente": preview.get("ingrediente"), "articulo": article},
            recipe_actions=[{"action_id": "CONFIRM_INGREDIENT_RELATION", "label": "Relacionar ingrediente"}],
        )

    def _confirm_ingredient_relation(self) -> dict[str, Any]:
        pending = dict(self._session.confirmacion_relacion_ingrediente_pendiente or {})
        if str(pending.get("estado") or "") != "LISTO_PARA_CONFIRMAR":
            return self._chat_action_message("Primero revisa la relación propuesta.", TIPO_ADVERTENCIA, reason="ingredient_relation_confirmation_missing")
        try:
            result = self.ingredient_relation_service.confirm(
                recipe_id=str(pending.get("recipe_id") or ""), ingredient_index=int(pending.get("ingredient_index") or 0),
                article_id=str(pending.get("article_id") or ""), preview_token=str(pending.get("preview_token") or ""),
                context=self.tool_executor.write_context,
            )
        except ErrorConfirmacionRelacionIngrediente as exc:
            return self._chat_action_message(str(exc), TIPO_ADVERTENCIA, reason=exc.code)
        self._session.confirmacion_relacion_ingrediente_pendiente = {}
        follow_up = self.recipe_completion_workflow.investigate(str(pending.get("recipe_id") or ""))
        return self._chat_action_message(
            "Ya está relacionada. " + follow_up.summary, TIPO_RESULTADO,
            datos_reales_modificados=bool(result.get("datos_reales_modificados")),
        )

    @staticmethod
    def _general_agent_enabled() -> bool:
        import os
        return str(os.getenv("HOST_AI_GENERAL_AGENT_READ") or "").strip().lower() in {"1", "true", "yes", "on", "si", "sí"}

    def _general_agent_ready(self) -> bool:
        """El modelo toma el control cuando hay provider real con tool calling."""
        return self._general_agent_status()[0]

    def _general_agent_status(self) -> tuple[bool, dict[str, Any]]:
        if not self._general_agent_enabled():
            return False, {"enabled": False, "provider": "", "connected": False, "tool_calling": False, "reason": "feature_disabled"}
        engine = getattr(self.general_agent, "engine", None)
        provider = getattr(engine, "_providers", {}).get(getattr(engine, "default_provider", ""))
        provider_name = str(getattr(provider, "provider_name", getattr(engine, "default_provider", "")) or "")
        connected = bool(provider and getattr(provider, "connected", False))
        tool_calling = bool(provider and getattr(provider, "supports_tool_calling", False))
        ready = bool(provider and connected and tool_calling)
        reason = "ready" if ready else "provider_unavailable"
        return ready, {"enabled": True, "provider": provider_name, "connected": connected, "tool_calling": tool_calling, "reason": reason}

    def _try_general_agent(self, contenido: str, contexto: dict[str, Any]) -> dict[str, Any] | None:
        enabled = self._general_agent_enabled()
        http_request_id = str(contexto.pop("_host_ai_request_id", "") or "")
        self.agent_observability.emit("general_agent_enabled", request_id=http_request_id, enabled=enabled)
        LOGGER.info("general_agent_enabled %s", {"enabled": enabled})
        if not enabled:
            return None
        if getattr(self.general_agent, "engine", None) is None:
            return self._safe_agent_fallback("provider_unsupported")
        started = time.perf_counter()
        history = [
            {"role": "assistant" if item.rol == "host_ai" else "user", "content": item.texto}
            for item in self._mensajes[:-1][-8:]
            if item.rol in {"usuario", "host_ai"} and str(item.texto or "").strip()
        ]
        active_by_context = {
            "ELABORACION": self._session.escandallo_activo or self._session.receta_activa,
            "MENU": self._session.menu_activo,
            "PRODUCCION": self._session.produccion_activa,
            "EVENTO": self._session.evento_activo,
            "RESERVA": self._session.reserva_activa,
            "ARTICULO": self._session.articulo_activo,
            "COMPRA": self._session.compra_activa,
        }
        active_entity = active_by_context.get(self._session.contexto_activo, {}) or self._session.escandallo_activo or self._session.receta_activa
        if self._session.contexto_activo == "EVENTO" and not active_entity:
            active_entity = {"tipo": "EVENTO", "dominio": "EVENTOS"}
        if self._session.contexto_activo == "RESERVA" and not active_entity:
            active_entity = {"tipo": "RESERVA", "dominio": "RESERVAS"}
        route, workflow = self.conversation_brain.prepare_turn(
            contenido, self._session.workflow_activo, dict(active_entity or {}),
        )
        self._session.actualizar_workflow(workflow.to_dict())
        route, workflow = self.conversation_brain.prepare_turn(
            contenido,
            self._session.workflow_activo,
            dict(active_entity or {}),
        )
        self._session.actualizar_workflow(workflow.to_dict())
        self.agent_observability.emit(
            "intelligence_route",
            request_id=http_request_id,
            model_tier=route.tier,
            reasoning_effort=route.reasoning_effort,
            routing_reason=route.reason,
            workflow_type=route.workflow_type,
        )
        pending_before = dict(self._session.confirmacion_reserva_pendiente or {})
        catalog_pending_before = dict(self._session.confirmacion_catalogo_pendiente or {})
        result = self.general_agent.run(
            contenido,
            conversation_context={
                "contexto_activo": self._session.contexto_activo,
                "active_entity": dict(active_entity or {}),
                "pending_confirmation": dict(self._session.confirmacion_catalogo_pendiente or self._session.confirmacion_articulo_pendiente or self._session.confirmacion_reserva_pendiente or {}),
                "recipe_proposal": dict(self._session.propuesta_receta_activa or {}),
                "restaurant_context": {"business_type": "restaurante/cocina profesional", "language": "es"},
                "conversation_history": history,
                "economic_recipe_candidates": [
                    dict(item) for item in list(self._session.economic_recipe_candidates or [])[:10]
                    if isinstance(item, dict)
                ],
                "economic_incidents": [
                    dict(item) for item in list(self._session.economic_incidents or [])[:10]
                    if isinstance(item, dict)
                ],
                "request_id": http_request_id,
                "telemetry": self.agent_observability,
                "user_context": self._safe_user_context(contexto),
                "intelligence_route": route.to_dict(),
                "workflow": workflow.to_dict(),
            },
        )
        if not result.ok:
            reason = self._agent_failure_reason(str(result.safe_error or ""))
            self.agent_observability.emit("agent_fallback", request_id=http_request_id, agent_run_id=result.request_id, provider=result.provider, model=result.model, agent_step=result.steps, reason=result.safe_error, normalized_reason=reason, fallback_selected=True, duration_ms=round((time.perf_counter() - started) * 1000, 2))
            LOGGER.info("agent_fallback %s", {"request_id": result.request_id, "provider": result.provider, "model": result.model, "steps": result.steps, "tools_executed": result.executed_tools, "reason": reason, "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
            return self._safe_agent_fallback(reason, result)
        if "consultar_eventos" in list(result.executed_tools or []):
            self._session.actualizar_contexto_activo("EVENTO", module="EVENTOS")
        if "consultar_reservas" in list(result.executed_tools or []):
            self._session.actualizar_contexto_activo("RESERVA", module="RESERVAS")
        result_context = dict(getattr(result, "context_updates", {}) or {})
        if "economic_incidents" not in result_context:
            self._session.economic_incidents = []
            self._session.acciones_economicas_contextuales = {}
        if result_context:
            self._aplicar_resultado_tool_en_sesion({"contexto_actualizado": result_context})
        self._session.actualizar_workflow(
            self.conversation_brain.record_tool_results(
                self._session.workflow_activo,
                list(result.executed_tools or []),
            ).to_dict()
        )
        grounding_requirement = str(getattr(result, "grounding_requirement", "NONE") or "NONE")
        grounding_retry = bool(getattr(result, "grounding_retry", False))
        termination_reason = str(getattr(result, "termination_reason", "agent_final") or "agent_final")
        LOGGER.info("agent_final %s", {"request_id": result.request_id, "provider": result.provider, "model": result.model, "steps": result.steps, "tools_executed": result.executed_tools, "grounding_requirement": grounding_requirement, "grounding_retry": grounding_retry, "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
        ui_action = self._validated_ui_action(
            next(iter(list(getattr(result, "ui_actions", []) or [])), None)
        )
        purchase_groups = list(result_context.get("purchase_groups") or [])
        specific_purchase_action = None
        for group in purchase_groups:
            purchase_action = dict(group.get("action") or {}) if isinstance(group, dict) else {}
            if str(purchase_action.get("type") or "").upper() != "OPEN_ORDER":
                continue
            specific_purchase_action = self._validated_ui_action({
                    "type": "OPEN_VIEW",
                    "target": "COMPRA",
                    "id": purchase_action.get("pedido_id"),
                    "view": "PEDIDO",
                    "label": purchase_action.get("label") or "Abrir pedido",
                })
            if specific_purchase_action:
                break
        if specific_purchase_action and (
            ui_action is None
            or (ui_action.get("target") == "COMPRA" and ui_action.get("view") == "LISTADO")
        ):
            ui_action = specific_purchase_action
        if ui_action:
            entity_type = (
                "RECETA" if ui_action["target"] == "ELABORACION" and ui_action["view"] == "RECETA"
                else ui_action["target"]
            )
            active = {"id": ui_action["id"], "nombre": ui_action["label"], "tipo": entity_type, "vista": ui_action["view"]}
            target = ui_action["target"]
            context_keys = {"MENU": "menu_activo", "PRODUCCION": "produccion_activa", "ARTICULO": "articulo_activo", "COMPRA": "compra_activa", "EVENTOS": "evento_activo", "RESERVAS": "reserva_activa"}
            update = {"contexto_activo": "EVENTO" if target == "EVENTOS" else ("RESERVA" if target == "RESERVAS" else target)}
            if target == "ELABORACION":
                update.update({"receta_activa": active if ui_action["view"] == "RECETA" else {}, "escandallo_activo": active if ui_action["view"] == "ESCANDALLO" else {}})
            elif context_keys.get(target):
                update[context_keys[target]] = active
            nav_context = {"target_module": target, "context_update": update}
            self._session.actualizar_desde_navegacion(nav_context)
        reservation_actions = self._catalog_confirmation_actions() or self._reservation_actions()
        pending_write = self._pending_catalog_write()
        economic_actions = self._economic_actions()
        response_text = str(result.text or "")
        if reservation_actions and reservation_actions[0]["action_id"] == "APPLY_PENDING_RESERVATION":
            response_text = "He preparado el cambio. Revisa los datos y elige una opcion."
        elif reservation_actions and reservation_actions[0]["action_id"] == "APPLY_PENDING_CATALOG_CREATE":
            response_text = f"He preparado la creación de {str((self._session.confirmacion_catalogo_pendiente or {}).get('dominio') or 'registro').lower()}. Revisa los datos y confirma o cancela."
        elif bool(getattr(result, "datos_reales_modificados", False)):
            if catalog_pending_before:
                response_text = f"{str(catalog_pending_before.get('dominio') or 'Registro').title()} creado correctamente."
            else:
                response_text = "Reserva creada correctamente." if str(pending_before.get("operacion") or "") == "CREAR" else "Reserva actualizada correctamente."
        return {
            "mensaje": response_text,
            "datos": {
                "general_agent": {"enabled": True, "attempted": True, "request_id": result.request_id, "provider": result.provider, "model": result.model, "steps": result.steps, "tools_executed": result.executed_tools, "grounding_requirement": grounding_requirement, "grounding_retry": grounding_retry, "termination_reason": termination_reason, "fallback": False, "final_answer_source": "MODEL"},
                "workflow": self._session.workflow_activo,
                "ui_action": ui_action,
                "datos_reales_modificados": bool(getattr(result, "datos_reales_modificados", False)),
                "reservation_actions": reservation_actions,
                "confirmation_actions": reservation_actions,
                "preview": dict((self._session.confirmacion_catalogo_pendiente or {}).get("payload") or {}),
                "pending_write": pending_write,
                "economic_actions": economic_actions,
                "purchase_groups": purchase_groups,
                "operational_incidents": list(result_context.get("operational_incidents") or []),
            },
        }

    @staticmethod
    def _validated_ui_action(value: Any) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            return None
        action = {
            "type": str(value.get("type") or "").upper(),
            "target": str(value.get("target") or "").upper(),
            "id": str(value.get("id") or "").strip(),
            "view": str(value.get("view") or "").upper(),
            "label": str(value.get("label") or "").strip(),
        }
        allowed = {
            "ELABORACION": {"RECETA", "ESCANDALLO"},
            "ARTICULO": {"FICHA"},
            "MENU": {"DETALLE"},
            "PRODUCCION": {"PLAN"},
            "COMPRA": {"LISTADO", "PEDIDO"},
            "EVENTOS": {"LISTADO", "DETALLE"},
            "RESERVAS": {"LISTADO", "DETALLE"},
            "LOTE": {"DETALLE"},
        }
        if action["type"] != "OPEN_VIEW" or action["view"] not in allowed.get(action["target"], set()):
            return None
        if not action["id"] and not (action["target"] in {"COMPRA", "EVENTOS", "RESERVAS"} and action["view"] == "LISTADO"):
            return None
        if action["target"] == "RESERVAS":
            if action["view"] == "LISTADO" and action["id"]:
                return None
            if action["view"] == "DETALLE" and re.fullmatch(r"RES-[A-F0-9]{12}", action["id"]) is None:
                return None
        if action["id"] and re.fullmatch(r"[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*", action["id"]) is None:
            return None
        action["safe"] = True
        action["datos_reales_modificados"] = False
        return action

    @staticmethod
    def _safe_agent_fallback(reason: str, result: Any | None = None) -> dict[str, Any]:
        return {
            "mensaje": "No he podido consultar de forma segura la informacion interna solicitada. Intentalo de nuevo; no se ha modificado ningun dato.",
            "datos": {
                "general_agent": {
                    "enabled": True, "attempted": result is not None,
                    "request_id": str(getattr(result, "request_id", "") or ""),
                    "provider": str(getattr(result, "provider", "") or ""),
                    "model": str(getattr(result, "model", "") or ""),
                    "steps": int(getattr(result, "steps", 0) or 0),
                    "tools_executed": list(getattr(result, "executed_tools", []) or []),
                    "grounding_requirement": str(getattr(result, "grounding_requirement", "") or ""),
                    "grounding_retry": bool(getattr(result, "grounding_retry", False)),
                    "termination_reason": str(reason or "safe_fallback"), "fallback": True,
                },
                "datos_reales_modificados": False,
            },
        }

    @staticmethod
    def _agent_failure_reason(error: str) -> str:
        value = str(error or "").strip().lower()
        if value == "grounding_failed":
            return "grounding_failed"
        if value in {"tool_error", "tool_not_allowed", "tool_type_not_allowed", "function_call_parse_error"} or value.startswith("invalid_type:") or value.startswith("invalid_enum:"):
            return "tool_error"
        if value in {"max_tool_calls_exceeded", "repeated_tool_call", "max_agent_steps_exceeded", "agent_timeout"}:
            return "limit_reached"
        if value == "provider_tool_calling_not_supported":
            return "provider_unsupported"
        if value in {"invalid_provider_turn", "invalid_provider_result", "empty_output", "json_parse_error", "final_schema_invalid"}:
            return "invalid_result"
        if value in {"api_bad_request", "api_schema_error", "api_timeout", "api_connection_error", "provider_runtime_error"}:
            return "provider_error"
        return "provider_error"

    @staticmethod
    def _safe_user_context(contexto: dict[str, Any]) -> dict[str, Any]:
        reserved = {
            "active_entity",
            "conversation_history",
            "request_id",
            "telemetry",
            "contexto_activo",
            "_host_ai_request_id",
        }
        out: dict[str, Any] = {}
        for key, value in dict(contexto or {}).items():
            if str(key) in reserved:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                out[str(key)] = value
        return out

    def actualizar_contexto_activo(self, contexto: str) -> None:
        self._session.actualizar_contexto_activo(contexto=contexto)

    def aplicar_navigation_request(self, nav_request: dict[str, Any]) -> None:
        self._session.actualizar_desde_navegacion(nav_request)

    def platform_stats(self) -> dict[str, Any]:
        return dict(self.tool_registry.stats())

    def _resolver_intencion(self, texto: str, contexto: dict[str, Any], engine: dict[str, Any]) -> dict[str, Any]:
        consulta_modulos = self._resolver_consulta_modulos(texto, engine)
        if consulta_modulos is not None:
            return consulta_modulos

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
            "tipo_mensaje": (
                self._tipo_desde_engine(engine)
                if str(engine.get("proveedor") or "").upper() == "OPENAI"
                else TIPO_ADVERTENCIA
            ),
            "mensaje": self._mensaje_engine(engine),
            "datos": {"engine": engine, "intent": match.to_dict()},
        }

    def _resolver_stock_conversacional(self, texto: str, contexto: dict[str, Any], match: Any) -> dict[str, Any]:
        terms = dict(match.terms or {})
        tr = self.tool_executor.execute(
            "consultar_estado_stock",
            params={
                "consulta": str(terms.get("consulta") or "resumen"),
                "termino": str(terms.get("termino") or ""),
            },
            session_context=self._session.to_dict(),
        )
        self._session.ultima_intencion = match.intent
        self._session.registrar_accion("INTENCION", match.intent)
        tool_context = dict(tr.datos or {})
        engine = self._consultar_engine(texto, contexto, tool_context=tool_context)
        provider = str(engine.get("proveedor") or "").upper()
        mensaje = tr.mensaje
        if provider == "OPENAI" and str(engine.get("estado") or "") == "OK":
            mensaje = self._mensaje_engine(engine)
        tipo = TIPO_RESULTADO if tr.estado == "OK" else TIPO_ERROR
        return {
            "tipo_mensaje": tipo,
            "mensaje": mensaje,
            "datos": {
                "engine": engine,
                "intent": match.to_dict(),
                "tool": {
                    "id": "consultar_estado_stock",
                    "estado": tr.estado,
                    "duracion_ms": tr.duracion_ms,
                },
                "tool_context": tool_context,
                "datos_reales_modificados": False,
            },
        }

    def _resolver_articulos_conversacional(
        self,
        texto: str,
        contexto: dict[str, Any],
        match: Any,
        seleccion: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        termino = str((match.terms or {}).get("termino") or "").strip()
        tr = self.tool_executor.execute(
            "buscar_articulos",
            params={"termino": termino, "limite": 10},
            session_context=self._session.to_dict(),
        )
        self._session.ultima_intencion = match.intent
        self._session.registrar_accion("INTENCION", match.intent)
        self._aplicar_resultado_tool_en_sesion(tr.to_dict())
        tool_context = dict(tr.datos or {})
        if seleccion and tool_context.get("estado") == "OK" and len(list(tool_context.get("articulos") or [])) == 1:
            articulo_seleccionado = dict(list(tool_context.get("articulos") or [])[0])
            tool_context.update(
                {
                    "seleccion_resuelta": True,
                    "seleccion_original": str(seleccion.get("seleccion_original") or texto),
                    "indice_seleccionado": seleccion.get("indice_seleccionado"),
                    "criterio_seleccion": str(seleccion.get("criterio_seleccion") or ""),
                    "articulo_seleccionado": articulo_seleccionado,
                }
            )
        engine = self._consultar_engine(texto, contexto, tool_context=tool_context)
        provider = str(engine.get("proveedor") or "").upper()
        mensaje = tr.mensaje
        if provider == "OPENAI" and str(engine.get("estado") or "") == "OK":
            mensaje = self._mensaje_engine(engine)
        navigation = NavigationRequest(
            target_module="CATALOGO",
            target_view="articulos",
            filter_data={"termino": termino},
            message="Abrir esta búsqueda en Artículos.",
        ).to_dict()
        return {
            "tipo_mensaje": TIPO_RESULTADO if tr.estado == "OK" else TIPO_ERROR,
            "mensaje": mensaje,
            "datos": {
                "engine": engine,
                "intent": match.to_dict(),
                "tool": {"id": "buscar_articulos", "estado": tr.estado, "duracion_ms": tr.duracion_ms},
                "tool_context": tool_context,
                "resultados": list(tool_context.get("articulos") or []),
                "navigation_request": navigation,
                "datos_reales_modificados": False,
            },
        }

    def _seleccion_articulo_contextual(self, texto: str) -> dict[str, Any] | None:
        if str(self._session.contexto_activo or "").upper() != "CATALOGO":
            return None
        items = [dict(item) for item in list(self._session.ultima_lista_mostrada or []) if isinstance(item, dict)]
        if not items:
            return None
        norm = self._normalizar_texto(texto)
        ordinales = {
            "1": 0, "la 1": 0, "el 1": 0, "la primera": 0, "el primero": 0,
            "2": 1, "la 2": 1, "el 2": 1, "la segunda": 1, "el segundo": 1,
            "3": 2, "la 3": 2, "el 3": 2, "la tercera": 2, "el tercero": 2,
        }
        index = ordinales.get(norm)
        if norm in {"la ultima", "el ultimo", "ultima", "ultimo"}:
            index = len(items) - 1
        if index is not None:
            if 0 <= index < len(items):
                return {
                    "termino": str(items[index].get("codigo") or items[index].get("article_id") or ""),
                    "seleccion_original": texto,
                    "indice_seleccionado": index + 1,
                    "criterio_seleccion": "ordinal",
                }
            return None
        exact = [
            item for item in items
            if norm in {
                self._normalizar_texto(str(item.get("codigo") or "")),
                self._normalizar_texto(str(item.get("article_id") or "")),
                self._normalizar_texto(str(item.get("nombre") or "")),
            }
        ]
        if len(exact) == 1:
            selected_index = items.index(exact[0])
            return {
                "termino": str(exact[0].get("codigo") or exact[0].get("article_id") or ""),
                "seleccion_original": texto,
                "indice_seleccionado": selected_index + 1,
                "criterio_seleccion": "identificador_o_nombre_exacto",
            }
        return None

    def _resolver_compras_conversacional(self, texto: str, contexto: dict[str, Any], match: Any) -> dict[str, Any]:
        tool_id = self.tool_resolver.resolve(match.intent)
        tr = self.tool_executor.execute(tool_id, params=dict(match.terms or {}), session_context=self._session.to_dict())
        tool_context = dict(tr.datos or {})
        engine = self._consultar_engine(texto, contexto, tool_context=tool_context)
        navigation = self._navigation_request(
            sidebar="4",
            target_view="MODULO",
            message="Abrir esta consulta en Compras.",
            context_update={"contexto_activo": "COMPRAS"},
        ) if self._es_peticion_visual(texto) else {}
        mensaje = tr.mensaje
        if str(engine.get("proveedor") or "").upper() == "OPENAI" and str(engine.get("estado") or "") == "OK":
            mensaje = self._mensaje_engine(engine)
        response_data = {
            "engine": engine,
            "intent": match.to_dict(),
            "tool": {"id": tool_id, "estado": tr.estado, "duracion_ms": tr.duracion_ms},
            "tool_context": tool_context,
            "datos_reales_modificados": False,
        }
        if navigation:
            response_data["navigation_request"] = navigation
        return {"tipo_mensaje": TIPO_RESULTADO if tr.estado == "OK" else TIPO_ERROR, "mensaje": mensaje, "datos": response_data}

    def _resolver_produccion_conversacional(self, texto: str, contexto: dict[str, Any], match: Any) -> dict[str, Any]:
        tr = self.tool_executor.execute("consultar_produccion", params=dict(match.terms or {}), session_context=self._session.to_dict())
        tool_context = dict(tr.datos or {})
        engine = self._consultar_engine(texto, contexto, tool_context=tool_context)
        mensaje = tr.mensaje
        if str(engine.get("proveedor") or "").upper() == "OPENAI" and str(engine.get("estado") or "") == "OK":
            mensaje = self._mensaje_engine(engine)
        return {"tipo_mensaje": TIPO_RESULTADO if tr.estado == "OK" else TIPO_ERROR, "mensaje": mensaje,
                "datos": {"engine": engine, "intent": match.to_dict(), "tool": {"id": "consultar_produccion", "estado": tr.estado, "duracion_ms": tr.duracion_ms}, "tool_context": tool_context, "datos_reales_modificados": False}}

    def _resolver_consulta_modulos(
        self,
        texto: str,
        engine: dict[str, Any],
    ) -> dict[str, Any] | None:
        consulta = self._detectar_consulta_modulos(texto)
        if consulta is None:
            return None
        if self.home_read_service is None:
            return {
                "tipo_mensaje": TIPO_ADVERTENCIA,
                "mensaje": "La información operativa no está disponible en este momento.",
                "datos": {"engine": engine, "informativa": True},
            }

        home = dict(self.home_read_service.cargar_home() or {})
        modulos = dict(home.get("modulos") or {})
        modulo, target = consulta
        mensaje = self._formatear_consulta_modulos(modulo, modulos)
        navigation = NavigationRequest(
            target_module=target,
            source="chat_host_ai",
            message="Abrir la pantalla manual relacionada.",
        ).to_dict()
        return {
            "tipo_mensaje": TIPO_RESULTADO,
            "mensaje": f"Consulta informativa. {mensaje}",
            "datos": {
                "engine": engine,
                "informativa": True,
                "modo_lectura": True,
                "modulos_consultados": (
                    ["compras", "eventos", "produccion", "stock"]
                    if modulo == "operacion"
                    else [modulo]
                ),
                "navigation_request": navigation,
            },
        }

    @classmethod
    def _es_consulta_modulos(cls, texto: str) -> bool:
        return cls._detectar_consulta_modulos(texto) is not None

    @classmethod
    def _detectar_consulta_modulos(
        cls,
        texto: str,
    ) -> tuple[str, str] | None:
        normalized = cls._normalizar_texto(texto)
        if "proveedor" in normalized:
            return "proveedores", "COMPRAS"
        if "compra" in normalized and any(
            term in normalized for term in ("pendiente", "necesidad", "propuesta")
        ):
            return "compras", "COMPRAS"
        if "evento" in normalized and any(
            term in normalized for term in ("proximo", "activo", "tengo", "hay")
        ):
            return "eventos", "EVENTOS"
        if "produccion" in normalized and any(
            term in normalized for term in ("curso", "activa", "pendiente", "estado")
        ):
            return "produccion", "PRODUCCION"
        if "stock" in normalized and any(
            term in normalized for term in ("critic", "alerta", "minimo", "riesgo")
        ):
            return "stock", "STOCK"
        if "estado general" in normalized or "estado de la operacion" in normalized:
            return "operacion", "EXECUTIVE"
        return None

    @staticmethod
    def _formatear_consulta_modulos(
        consulta: str,
        modulos: dict[str, Any],
    ) -> str:
        compras = dict(modulos.get("compras") or {})
        eventos = dict(modulos.get("eventos") or {})
        produccion = dict(modulos.get("produccion") or {})
        stock = dict(modulos.get("stock") or {})

        if consulta == "compras":
            necesidades = int(compras.get("necesidades_pendientes") or 0)
            propuestas = int(compras.get("propuestas_pendientes") or 0)
            nombres = [
                str(item.get("nombre") or item.get("producto") or "")
                for item in (
                    list(compras.get("items") or [])
                    + list(compras.get("propuestas") or [])
                )
                if isinstance(item, dict)
            ]
            return ServicioChatHostAIShell._resumen_con_nombres(
                f"Hay {necesidades} necesidades y {propuestas} propuestas de compra pendientes",
                nombres,
            )
        if consulta == "proveedores":
            proveedores = list(compras.get("proveedores") or [])
            nombres = [
                str(item.get("nombre") or "")
                for item in proveedores
                if isinstance(item, dict)
            ]
            return ServicioChatHostAIShell._resumen_con_nombres(
                f"Hay {len(proveedores)} proveedores activos",
                nombres,
            )
        if consulta == "eventos":
            items = list(eventos.get("items") or [])
            nombres = [
                str(item.get("nombre") or "")
                for item in items
                if isinstance(item, dict)
            ]
            pax = int(dict(eventos.get("resumen") or {}).get("pax_total") or 0)
            return ServicioChatHostAIShell._resumen_con_nombres(
                f"Hay {len(items)} eventos próximos con {pax} PAX",
                nombres,
            )
        if consulta == "produccion":
            planes = list(produccion.get("items") or [])
            nombres = [
                str(item.get("nombre") or "")
                for item in planes
                if isinstance(item, dict)
            ]
            en_curso = int(produccion.get("tareas_en_curso") or 0)
            return ServicioChatHostAIShell._resumen_con_nombres(
                f"Hay {len(planes)} planes activos y {en_curso} tareas en curso",
                nombres,
            )
        if consulta == "stock":
            alertas = list(stock.get("alertas") or stock.get("items") or [])
            mensajes = [
                str(item.get("mensaje") or item.get("tipo") or "")
                for item in alertas
                if isinstance(item, dict)
            ]
            return ServicioChatHostAIShell._resumen_con_nombres(
                f"Hay {len(alertas)} alertas de stock",
                mensajes,
            )
        return (
            "Estado general: "
            f"{len(list(eventos.get('items') or []))} eventos próximos, "
            f"{int(produccion.get('tareas_en_curso') or 0)} tareas de producción en curso, "
            f"{int(compras.get('necesidades_pendientes') or 0) + int(compras.get('propuestas_pendientes') or 0)} compras pendientes "
            f"y {len(list(stock.get('alertas') or stock.get('items') or []))} alertas de stock."
        )

    @staticmethod
    def _resumen_con_nombres(resumen: str, nombres: list[str]) -> str:
        disponibles = [nombre for nombre in nombres if nombre]
        if not disponibles:
            return f"{resumen}."
        return f"{resumen}: {', '.join(disponibles[:5])}."

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

    @classmethod
    def _es_peticion_visual(cls, texto: str) -> bool:
        normalized = cls._normalizar_texto(texto)
        return any(token in normalized for token in ("abre", "abrir", "abreme", "ensename", "muestrame", "ver", "llévame", "llevame"))


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
        if "reserva_activa" in contexto and isinstance(contexto.get("reserva_activa"), dict):
            self._session.reserva_activa = dict(contexto.get("reserva_activa") or {})
        if "confirmacion_reserva_pendiente" in contexto and isinstance(contexto.get("confirmacion_reserva_pendiente"), dict):
            self._session.confirmacion_reserva_pendiente = dict(contexto.get("confirmacion_reserva_pendiente") or {})
        if "acciones_reserva_contextuales" in contexto and isinstance(contexto.get("acciones_reserva_contextuales"), dict):
            self._session.acciones_reserva_contextuales = dict(contexto.get("acciones_reserva_contextuales") or {})
        if "economic_recipe_candidates" in contexto and isinstance(contexto.get("economic_recipe_candidates"), list):
            self._session.economic_recipe_candidates = [
                dict(item) for item in list(contexto.get("economic_recipe_candidates") or [])[:10]
                if isinstance(item, dict)
            ]
        if "economic_incidents" in contexto and isinstance(contexto.get("economic_incidents"), list):
            self._session.economic_incidents = [
                dict(item) for item in list(contexto.get("economic_incidents") or [])[:10]
                if isinstance(item, dict)
            ]
        if "confirmacion_articulo_pendiente" in contexto and isinstance(contexto.get("confirmacion_articulo_pendiente"), dict):
            self._session.confirmacion_articulo_pendiente = dict(contexto.get("confirmacion_articulo_pendiente") or {})
        if "confirmacion_catalogo_pendiente" in contexto and isinstance(contexto.get("confirmacion_catalogo_pendiente"), dict):
            self._session.confirmacion_catalogo_pendiente = dict(contexto.get("confirmacion_catalogo_pendiente") or {})
        if "propuesta_receta_activa" in contexto and isinstance(contexto.get("propuesta_receta_activa"), dict):
            self._session.propuesta_receta_activa = dict(contexto.get("propuesta_receta_activa") or {})

    def _consultar_engine(self, contenido: str, contexto: dict[str, Any] | None, tool_context: dict[str, Any] | None = None) -> dict[str, Any]:
        from CORE.orquestador import SolicitudHostAI

        preferred_provider = str(
            getattr(getattr(self.orquestador, "host_ai_engine", None), "default_provider", "SIMULADO")
        )
        deterministic_match = self.router.detectar(contenido)
        if preferred_provider.upper() == "OPENAI" and not tool_context and (
            deterministic_match.intent != INTENT_DESCONOCIDA
            or detectar_intencion_executive(contenido) is not None
            or self._es_consulta_modulos(contenido)
        ):
            preferred_provider = "SIMULADO"

        req = SolicitudHostAI(
            "host_ai_engine_consulta",
            {
                "origen": "APP_SHELL",
                "modulo": "chat_host_ai",
                "tipo_peticion": "consulta_general",
                "datos_enviados": {
                    "pregunta": contenido,
                    "sim_scenario": self._detectar_escenario_simulado(contenido),
                    **({"tool_context": dict(tool_context)} if tool_context else {}),
                },
                "proveedor_preferido": preferred_provider,
                "formato_entrada": "texto",
                "usar_director": False,
                "contexto": dict(contexto or {}),
            },
        )
        resultado = self.orquestador.resolver(req)
        data = resultado.to_dict() if hasattr(resultado, "to_dict") else dict(resultado or {})
        return dict((data.get("datos") or {}).get("host_ai_engine") or {})

    # Alias temporal para consumidores y tests históricos; ya no implica proveedor simulado.
    def _consultar_engine_simulado(self, contenido: str, contexto: dict[str, Any] | None) -> dict[str, Any]:
        return self._consultar_engine(contenido, contexto)

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
            return f"No se pudo obtener respuesta del proveedor de IA: {errores or 'sin detalle'}"
        respuesta = dict(engine.get("respuesta") or {})
        if respuesta.get("mensaje"):
            return str(respuesta.get("mensaje"))
        return "El proveedor de IA no devolvió texto utilizable."

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
