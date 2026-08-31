from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
import logging
import re
import time

from SERVICIOS.host_ai_tool_registry import HostAIToolRegistry, TOOL_STATUS_ACTIVADA
from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.host_ai_compras_read_service import HostAIComprasReadService
from SERVICIOS.host_ai_produccion_read_service import HostAIProduccionReadService
from SERVICIOS.host_ai_escandallos_read_service import HostAIEscandallosReadService
from SERVICIOS.host_ai_uso_elaboracion_read_service import HostAIUsoElaboracionReadService
from SERVICIOS.host_ai_menus_read_service import HostAIMenusReadService
from SERVICIOS.host_ai_operational_needs_read_service import HostAIOperationalNeedsReadService
from SERVICIOS.reservas_read_service import ReservasReadService
from MODELOS.reserva import RESERVA_ID_PATTERN
from SERVICIOS.reservas_write_service import ErrorReservasWrite, ReservasWriteService
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.confirmacion_formato_articulo_service import (
    ConfirmacionFormatoArticuloService, ErrorConfirmacionFormatoArticulo,
)
from SERVICIOS.catalog_crud_write_service import CatalogCrudError, CatalogCrudWriteService
from SERVICIOS.stock_lote_write_service import StockLoteWriteError, StockLoteWriteService


LOGGER = logging.getLogger("host_ai.platform.tools")


@dataclass
class HostAIToolResult:
    estado: str
    mensaje: str
    datos: dict[str, Any] = field(default_factory=dict)
    acciones: list[dict[str, Any]] = field(default_factory=list)
    contexto_actualizado: dict[str, Any] = field(default_factory=dict)
    navegacion: dict[str, Any] = field(default_factory=dict)
    errores: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    duracion_ms: int = 0
    tool_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HostAIToolExecutor:
    def __init__(self, registry: HostAIToolRegistry, home_read_service: Any | None = None, articulos_read_service: Any | None = None, compras_read_service: Any | None = None, produccion_read_service: Any | None = None, escandallos_read_service: Any | None = None, uso_elaboracion_read_service: Any | None = None, menus_read_service: Any | None = None, operational_needs_read_service: Any | None = None, reservas_read_service: Any | None = None, reservas_write_service: Any | None = None, article_change_service: Any | None = None, catalog_crud_service: Any | None = None, write_context: AuthorizedExecutionContext | None = None, session_id: str = ""):
        self.registry = registry
        self.home_read_service = home_read_service
        self.articulos_read_service = articulos_read_service or self._build_articulos_read_service()
        core = getattr(home_read_service, "core", None)
        base_dir = getattr(core, "base_dir", None)
        self.menus_read_service = menus_read_service or (HostAIMenusReadService(base_dir) if base_dir is not None else None)
        self.operational_needs_read_service = operational_needs_read_service or (
            HostAIOperationalNeedsReadService(base_dir, core=core) if base_dir is not None else None
        )
        self.compras_read_service = compras_read_service or (HostAIComprasReadService(core) if core is not None else None)
        self.produccion_read_service = produccion_read_service or (
            HostAIProduccionReadService(core, menus_read_service=self.menus_read_service) if core is not None else None
        )
        self.escandallos_read_service = escandallos_read_service or (HostAIEscandallosReadService(base_dir) if base_dir is not None else None)
        self.uso_elaboracion_read_service = uso_elaboracion_read_service or (HostAIUsoElaboracionReadService(base_dir, core=core) if base_dir is not None else None)
        self.reservas_read_service = reservas_read_service or (ReservasReadService(base_dir) if base_dir is not None else None)
        self.reservas_write_service = reservas_write_service or (ReservasWriteService(base_dir) if base_dir is not None else None)
        self.catalog_crud_service = catalog_crud_service or (CatalogCrudWriteService(base_dir) if base_dir is not None else None)
        self.stock_lot_write_service = StockLoteWriteService(core) if core is not None else None
        article_base = base_dir or getattr(self.articulos_read_service, "base_dir", None)
        self.article_change_service = article_change_service or (
            ConfirmacionFormatoArticuloService(article_base, articles=self.articulos_read_service)
            if article_base is not None else None
        )
        self.write_context = write_context
        self.session_id = str(session_id or "")
        self._agent_read_handlers = {
            "consultar_estado_stock": self._tool_consultar_estado_stock,
            "buscar_articulos": self._tool_buscar_articulos,
            "consultar_articulo_detalle": self._tool_consultar_articulo_detalle,
            "consultar_compras_pendientes": self._tool_consultar_compras_pendientes,
            "consultar_produccion": self._tool_consultar_produccion,
            "consultar_eventos": self._tool_consultar_eventos,
            "consultar_evento_detalle": self._tool_consultar_evento_detalle,
            "consultar_reservas": self._tool_consultar_reservas,
            "consultar_escandallos": self._tool_consultar_escandallos,
            "consultar_uso_elaboracion": self._tool_consultar_uso_elaboracion,
            "consultar_menu": self._tool_consultar_menu,
            "consultar_necesidades_operativas": self._tool_consultar_necesidades_operativas,
            "conservar_propuesta_receta": self._tool_conservar_propuesta_receta,
        }

    def _tool_conservar_propuesta_receta(self, params: dict[str, Any], _context: dict[str, Any] | None = None) -> HostAIToolResult:
        proposal = dict(params or {})
        return HostAIToolResult(estado="OK", mensaje="Propuesta culinaria conservada en esta sesión; no se ha guardado ninguna receta.", datos={"estado": "PROPUESTA_NO_GUARDADA", "datos_reales_modificados": False}, contexto_actualizado={"propuesta_receta_activa": proposal}, tool_id="conservar_propuesta_receta")

    def execute_catalog_create_flow(self, tool_id: str, params: dict[str, Any] | None = None, request_id: str = "") -> HostAIToolResult:
        action, data = str(tool_id or ""), dict(params or {})
        if self.catalog_crud_service is None:
            return HostAIToolResult(estado="ERROR", mensaje="Creación de catálogo no disponible.", errores=["catalog_write_unavailable"], tool_id=action)
        try:
            if action == "aplicar_creacion_catalogo":
                context = self._catalog_context("write", request_id)
                result = self.catalog_crud_service.confirm(preview_token=str(data.get("preview_token") or ""), session_id=self.session_id, context=context)
                record, domain = dict(result.get("registro") or {}), str(result.get("dominio") or "")
                identity = str(record.get("id") or record.get("codigo") or "")
                target, view = ("EVENTOS", "DETALLE") if domain == "EVENTO" else (("ARTICULO", "FICHA") if domain == "ARTICULO" else ("ELABORACION", "RECETA"))
                result["ui_action"] = {"type": "OPEN_VIEW", "target": target, "id": identity, "view": view, "label": {"EVENTO": "Abrir evento", "ARTICULO": "Abrir artículo", "RECETA": "Abrir receta"}.get(domain, "Abrir")}
                context_updates = {"confirmacion_catalogo_pendiente": {}}
                if domain == "RECETA":
                    context_updates["propuesta_receta_activa"] = {}
                return HostAIToolResult(estado="OK", mensaje=f"{domain.title()} creado correctamente.", datos=result, acciones=[result["ui_action"]], contexto_actualizado=context_updates, tool_id=action)
            domains = {"preparar_creacion_evento": "EVENTO", "preparar_creacion_articulo": "ARTICULO", "preparar_creacion_receta": "RECETA"}
            domain = domains.get(action)
            if not domain:
                return HostAIToolResult(estado="ERROR", mensaje="Operación no autorizada.", errores=["agent_write_not_allowed"], tool_id=action)
            context = self._catalog_context("preview", request_id, domain)
            result = self.catalog_crud_service.preview(domain=domain, operation="CREAR", payload=data, entity_id="", session_id=self.session_id, context=context)
            pending = {"preview_token": result["preview_token"], "operacion": "CREAR", "dominio": domain, "payload": result.get("propuesto"), "session_id": self.session_id, "expira_en": result.get("expira_en")}
            return HostAIToolResult(estado="OK", mensaje="Vista previa preparada; falta confirmación humana.", datos=result, contexto_actualizado={"confirmacion_catalogo_pendiente": pending}, tool_id=action)
        except CatalogCrudError as exc:
            return HostAIToolResult(estado="ERROR", mensaje=str(exc), errores=[exc.code], datos={"datos_reales_modificados": False}, tool_id=action)

    def execute_stock_lot_location_flow(self, tool_id: str, params: dict[str, Any] | None = None, request_id: str = "") -> HostAIToolResult:
        action, data = str(tool_id or ""), dict(params or {})
        if self.stock_lot_write_service is None: return HostAIToolResult(estado="ERROR", mensaje="Gestión de lotes no disponible.", errores=["stock_lot_write_unavailable"], tool_id=action)
        try:
            context = self._stock_lot_context(action, request_id)
            if action == "confirmar_ubicacion_lote":
                result = self.stock_lot_write_service.confirm_location(lot_id=str(data.get("lote_id") or ""), location_id=str(data.get("location_id") or ""), preview_token=str(data.get("preview_token") or ""), context=context, session_id=self.session_id)
                lot = dict(result.get("lote") or {})
                ui = {"type": "OPEN_VIEW", "target": "LOTE", "id": str(lot.get("id") or ""), "view": "DETALLE", "label": "Abrir lote"}
                return HostAIToolResult(estado="OK", mensaje="Ubicación actualizada correctamente.", datos={**result, "ui_action": ui}, acciones=[ui], contexto_actualizado={"confirmacion_ubicacion_lote_pendiente": {}, "lote_activo": lot}, tool_id=action)
            if action == "descartar_ubicacion_lote":
                result = self.stock_lot_write_service.discard_location(preview_token=str(data.get("preview_token") or ""), context=context, session_id=self.session_id)
                return HostAIToolResult(estado="OK", mensaje="Cambio de ubicación cancelado sin modificar stock.", datos=result, contexto_actualizado={"confirmacion_ubicacion_lote_pendiente": {}}, tool_id=action)
            if action != "preparar_ubicacion_lote": return HostAIToolResult(estado="ERROR", mensaje="Operación de lote no autorizada.", errores=["agent_write_not_allowed"], tool_id=action)
            result = self.stock_lot_write_service.preview_location(lot_id=str(data.get("lote_id") or ""), location_id=str(data.get("location_id") or ""), context=context, session_id=self.session_id)
            after = dict(result.get("lote_despues") or {}); pending = {"preview_token": result["preview_token"], "lote_id": str(after.get("id") or data.get("lote_id") or ""), "location_id": str(data.get("location_id") or "")}
            return HostAIToolResult(estado="OK", mensaje="Vista previa preparada; falta confirmación humana.", datos=result, contexto_actualizado={"confirmacion_ubicacion_lote_pendiente": pending, "lote_activo": after}, tool_id=action)
        except StockLoteWriteError as exc:
            return HostAIToolResult(estado="ERROR", mensaje=str(exc), errores=[exc.code], datos={"datos_reales_modificados": False}, tool_id=action)

    def _stock_lot_context(self, action: str, request_id: str) -> AuthorizedExecutionContext:
        configured = self.write_context
        if configured is None: raise StockLoteWriteError("unauthorized", "Falta contexto autorizado.")
        candidate = AuthorizedExecutionContext(str(request_id or configured.request_id), configured.user_id, configured.tenant_id, configured.roles, configured.scopes)
        valid, _ = candidate.validate(); required = "stock:write" if action == "confirmar_ubicacion_lote" else "stock:preview"
        if not valid or required not in candidate.scopes: raise StockLoteWriteError("unauthorized", "El actor no está autorizado.")
        return candidate

    def discard_catalog_create(self, preview_token: str, request_id: str = "") -> HostAIToolResult:
        try:
            pending_domain = "RECETA"
            item = getattr(self.catalog_crud_service, "_pending", {}).get(str(preview_token or ""), {}) if self.catalog_crud_service else {}
            pending_domain = str(item.get("domain") or pending_domain)
            result = self.catalog_crud_service.discard(preview_token=preview_token, session_id=self.session_id, context=self._catalog_context("preview", request_id, pending_domain))
            return HostAIToolResult(estado="OK", mensaje="Creación descartada sin modificar datos.", datos=result, contexto_actualizado={"confirmacion_catalogo_pendiente": {}})
        except CatalogCrudError as exc:
            return HostAIToolResult(estado="ERROR", mensaje=str(exc), errores=[exc.code])

    def _catalog_context(self, kind: str, request_id: str, domain: str = "") -> AuthorizedExecutionContext:
        configured = self.write_context
        if configured is None:
            if kind == "write": raise CatalogCrudError("unauthorized", "La confirmación requiere identidad autorizada.")
            scope = {"EVENTO": "eventos:preview", "ARTICULO": "articulos:preview", "RECETA": "recetas:preview"}[domain]
            return AuthorizedExecutionContext(str(request_id or "chat-preview"), "host-ai-preview", "local-preview", ("preview",), frozenset({scope}))
        return AuthorizedExecutionContext(str(request_id or configured.request_id), configured.user_id, configured.tenant_id, configured.roles, configured.scopes)

    def execute_article_change_flow(self, tool_id: str, params: dict[str, Any] | None = None, request_id: str = "") -> HostAIToolResult:
        action = str(tool_id or "")
        data = dict(params or {})
        if self.article_change_service is None:
            return HostAIToolResult(estado="ERROR", mensaje="Cambio de artículo no disponible.", errores=["article_change_unavailable"], tool_id=action)
        try:
            context = self._article_execution_context(action, request_id)
            if action == "confirmar_cambio_articulo":
                result = self.article_change_service.confirm_change(
                    preview_token=str(data.get("preview_token") or ""), context=context, session_id=self.session_id,
                )
            elif action == "descartar_cambio_articulo":
                result = self.article_change_service.discard_change(
                    preview_token=str(data.get("preview_token") or ""), context=context, session_id=self.session_id,
                )
            else:
                operation = {
                    "preparar_precio_articulo": "UPDATE_PRICE",
                    "preparar_conversion_articulo": "UPDATE_CONVERSION",
                    "preparar_formato_articulo": "UPDATE_FORMAT",
                }.get(action)
                if not operation:
                    return HostAIToolResult(estado="ERROR", mensaje="Operación de artículo no autorizada.", errores=["agent_write_not_allowed"], tool_id=action)
                result = self.article_change_service.preview_change(
                    operation=operation, article_id=str(data.get("articulo_id") or ""), value=data.get("valor"),
                    unidad_origen=str(data.get("unidad_origen") or ""),
                    unidad_destino=str(data.get("unidad_destino") or ""),
                    unidad_compra=str(data.get("unidad_compra") or ""),
                    precio_propuesto=data.get("precio_propuesto"),
                    context=context, session_id=self.session_id,
                )
            context_update: dict[str, Any] = {}
            if action in {"preparar_precio_articulo", "preparar_conversion_articulo", "preparar_formato_articulo"}:
                context_update["confirmacion_articulo_pendiente"] = {
                    "preview_token": str(result.get("preview_token") or ""),
                    "operacion": str(result.get("operacion") or ""),
                    "articulo_id": str(result.get("articulo_id") or ""),
                    "expira_en": str(result.get("expira_en") or ""),
                }
            elif action in {"confirmar_cambio_articulo", "descartar_cambio_articulo"}:
                context_update["confirmacion_articulo_pendiente"] = {}
            return HostAIToolResult(estado="OK", mensaje="Operación de artículo preparada o aplicada.", datos=result, contexto_actualizado=context_update, tool_id=action)
        except ErrorConfirmacionFormatoArticulo as exc:
            return HostAIToolResult(estado="ERROR", mensaje=str(exc), errores=[exc.code], datos={"datos_reales_modificados": False}, tool_id=action)

    def _article_execution_context(self, action: str, request_id: str) -> AuthorizedExecutionContext:
        configured = self.write_context
        if configured is None:
            raise ErrorConfirmacionFormatoArticulo("unauthorized", "Falta contexto autorizado.")
        candidate = AuthorizedExecutionContext(
            request_id=str(request_id or configured.request_id), user_id=configured.user_id,
            tenant_id=configured.tenant_id, roles=configured.roles, scopes=configured.scopes,
        )
        valid, _ = candidate.validate()
        required = "articulos:write" if action == "confirmar_cambio_articulo" else "articulos:preview"
        if not valid or required not in candidate.scopes:
            raise ErrorConfirmacionFormatoArticulo("unauthorized", "El actor no está autorizado.")
        return candidate

    def execute_agent_write_flow(self, tool_id: str, params: dict[str, Any] | None = None, request_id: str = "") -> HostAIToolResult:
        action = str(tool_id or "")
        data = dict(params or {})
        if self.reservas_write_service is None:
            return HostAIToolResult(estado="ERROR", mensaje="Escritura de Reservas no autorizada.", errores=["write_context_unavailable"], tool_id=action)
        try:
            context = self._reservation_execution_context(action, request_id)
            if action == "aplicar_operacion_reserva":
                result = self.reservas_write_service.confirm(preview_token=str(data.get("preview_token") or ""), context=context, session_id=self.session_id)
                reservation = dict(result.get("reserva") or {})
                return HostAIToolResult(estado="OK", mensaje="Operacion de reserva confirmada.", datos=result, contexto_actualizado={"contexto_activo": "RESERVA", "ultimo_modulo": "RESERVAS", "reserva_activa": reservation, "confirmacion_reserva_pendiente": {}})
            operations = {"crear_reserva": "CREAR", "modificar_reserva": "MODIFICAR", "confirmar_reserva": "CONFIRMAR", "cancelar_reserva": "CANCELAR", "marcar_no_show": "NO_SHOW", "completar_reserva": "COMPLETAR"}
            operation = operations.get(action)
            if not operation:
                return HostAIToolResult(estado="ERROR", mensaje="Operacion WRITE no autorizada.", errores=["agent_write_not_allowed"], tool_id=action)
            identity = str(data.pop("reserva_id", "") or "")
            result = self.reservas_write_service.preview(operacion=operation, payload=data, reserva_id=identity, context=context, session_id=self.session_id)
            pending = {"preview_token": result["preview_token"], "operacion": operation, "reserva_id": identity, "expira_en": result["expira_en"]}
            return HostAIToolResult(estado="OK", mensaje="Vista previa preparada; falta confirmacion humana.", datos=result, contexto_actualizado={"contexto_activo": "RESERVA", "ultimo_modulo": "RESERVAS", "confirmacion_reserva_pendiente": pending})
        except ErrorReservasWrite as exc:
            error_data: dict[str, Any] = {"datos_reales_modificados": False}
            if exc.code == "terminal_state":
                reservation_id = str(locals().get("identity") or data.get("reserva_id") or "")
                current = self.reservas_read_service.detalle(reservation_id) if self.reservas_read_service and reservation_id else None
                error_data["reservation_capabilities"] = {
                    "reserva_id": reservation_id, "estado": str((current or {}).get("estado") or ""),
                    "read_only": True,
                    "allowed": ["abrir_ficha", "consultar_reservas", "crear_nueva_reserva_separada"],
                    "forbidden": ["editar", "cambiar_campos", "observaciones", "evento_id", "confirmar", "cancelar", "no_show", "completar"],
                }
            return HostAIToolResult(estado="ERROR", mensaje=str(exc), errores=[exc.code], datos=error_data, tool_id=action)

    def _reservation_execution_context(self, action: str, request_id: str) -> AuthorizedExecutionContext:
        configured = self.write_context
        if configured is not None:
            candidate = AuthorizedExecutionContext(
                request_id=str(request_id or configured.request_id), user_id=configured.user_id,
                tenant_id=configured.tenant_id, roles=configured.roles, scopes=configured.scopes,
            )
            valid, _ = candidate.validate()
            if valid:
                return candidate
        if action != "aplicar_operacion_reserva":
            return AuthorizedExecutionContext(
                request_id=str(request_id or "chat-preview"), user_id="host-ai-preview",
                tenant_id="local-preview", roles=("preview",), scopes=frozenset({ReservasWriteService.PREVIEW_SCOPE}),
            )
        raise ErrorReservasWrite("unauthorized", "La confirmacion requiere identidad, tenant y scope reservas:write configurados.")

    def execute_agent_ui_action(self, tool_id: str, params: dict[str, Any] | None = None) -> HostAIToolResult:
        inicio = time.perf_counter()
        action_id = str(tool_id or "")
        additional_handlers = {
            "abrir_articulo": self._ui_abrir_articulo,
            "abrir_menu": self._ui_abrir_menu,
            "abrir_produccion_ui": self._ui_abrir_produccion,
            "abrir_compra": self._ui_abrir_compra,
            "abrir_eventos": self._ui_abrir_eventos,
            "abrir_reservas": self._ui_abrir_reservas,
            "abrir_reserva": self._ui_abrir_reserva,
        }
        if action_id in additional_handlers:
            try:
                return self._finish(additional_handlers[action_id](dict(params or {})), inicio)
            except Exception:
                LOGGER.exception("agent_ui_action_error %s", {"tool_id": action_id})
                return self._finish(self._ui_error(action_id, "ui_action_internal_error"), inicio)
        if action_id != "abrir_elaboracion":
            return self._finish(HostAIToolResult(
                estado="ERROR", mensaje="Acción de interfaz no autorizada.",
                errores=["agent_ui_action_not_allowed"], tool_id=str(tool_id or ""),
            ), inicio)
        if self.escandallos_read_service is None:
            return self._finish(HostAIToolResult(
                estado="ERROR", mensaje="Servicio de Escandallos no disponible.",
                errores=["escandallos_read_unavailable"], tool_id=str(tool_id or ""),
            ), inicio)
        data = dict(params or {})
        identity = str(data.get("elaboracion_id") or "").strip()
        view = str(data.get("vista") or "").strip().lower()
        detail = self.escandallos_read_service.consultar("detalle", escandallo_id=identity)
        elaboration = (
            detail.get("elaboracion") or detail.get("escandallo")
        ) if detail.get("estado") == "OK" else None
        canonical_id = str((elaboration or {}).get("id") or "")
        if not canonical_id or canonical_id != identity or view not in {"receta", "escandallo"}:
            return self._finish(HostAIToolResult(
                estado="ERROR", mensaje="El destino solicitado no existe o no está permitido.",
                errores=["ui_action_target_invalid"], tool_id=str(tool_id or ""),
            ), inicio)
        if view == "escandallo" and (elaboration or {}).get("tiene_escandallo") is False:
            return self._finish(HostAIToolResult(
                estado="ERROR",
                mensaje="La receta existe, pero no tiene un escandallo registrado.",
                errores=["escandallo_not_found"], tool_id=str(tool_id or ""),
                datos={
                    "estado": "ESCANDALLO_NO_ENCONTRADO",
                    "receta_id": canonical_id,
                    "nombre": str((elaboration or {}).get("nombre") or canonical_id),
                    "estado_coste": "SIN_ESCANDALLO",
                    "datos_reales_modificados": False,
                },
            ), inicio)
        action = {
            "type": "OPEN_VIEW", "target": "ELABORACION", "id": canonical_id,
            "view": view.upper(), "label": str((elaboration or {}).get("nombre") or canonical_id),
            "safe": True, "datos_reales_modificados": False,
        }
        return self._finish(HostAIToolResult(
            estado="OK", mensaje="Vista de elaboración preparada.", datos={
                "ui_action": action, "solo_lectura": True, "datos_reales_modificados": False,
            }, acciones=[action], tool_id=str(tool_id or ""),
        ), inicio)

    def _ui_abrir_articulo(self, data: dict[str, Any]) -> HostAIToolResult:
        identity = str(data.get("articulo_id") or "").strip()
        detail = dict(self.articulos_read_service.obtener(identity) or {}) if self.articulos_read_service else {}
        article = detail.get("articulo") if detail.get("ok") is not False else None
        canonical_id = str((article or {}).get("id") or "")
        if not canonical_id or canonical_id != identity or str(data.get("vista") or "").lower() != "ficha":
            return self._ui_error("abrir_articulo")
        return self._ui_success("abrir_articulo", "ARTICULO", canonical_id, "FICHA", str((article or {}).get("nombre") or canonical_id))

    def _ui_abrir_menu(self, data: dict[str, Any]) -> HostAIToolResult:
        identity = str(data.get("menu_id") or "").strip()
        detail = self.menus_read_service.consultar(menu_id=identity) if self.menus_read_service else {}
        menu = detail.get("menu") if detail.get("estado") == "OK" else None
        canonical_id = str((menu or {}).get("menu_id") or "")
        if not canonical_id or canonical_id != identity:
            return self._ui_error("abrir_menu")
        return self._ui_success("abrir_menu", "MENU", canonical_id, "DETALLE", str((menu or {}).get("nombre") or canonical_id))

    def _ui_abrir_produccion(self, data: dict[str, Any]) -> HostAIToolResult:
        identity = str(data.get("plan_id") or "").strip()
        plans = list(self.produccion_read_service.motor.listar_planes() or []) if self.produccion_read_service else []
        plan = next((item for item in plans if str(item.get("id") or "") == identity), None)
        if not plan:
            return self._ui_error("abrir_produccion_ui")
        return self._ui_success("abrir_produccion_ui", "PRODUCCION", identity, "PLAN", str(plan.get("nombre") or identity))

    def _ui_abrir_compra(self, data: dict[str, Any]) -> HostAIToolResult:
        view = str(data.get("vista") or "").lower()
        identity = str(data.get("pedido_id") or "").strip()
        if view == "listado" and not identity:
            return self._ui_success("abrir_compra", "COMPRA", "", "LISTADO", "Compras")
        if identity and re.fullmatch(r"[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*", identity) is None:
            return self._ui_error("abrir_compra")
        orders = list(self._compras_service().consultar_pedidos().get("pedidos") or [])
        order = next((item for item in orders if str(item.get("pedido_id") or "") == identity), None)
        if view != "pedido" or not order:
            return self._ui_error("abrir_compra")
        return self._ui_success("abrir_compra", "COMPRA", identity, "PEDIDO", str(order.get("proveedor_nombre") or identity))

    def _ui_abrir_eventos(self, _data: dict[str, Any]) -> HostAIToolResult:
        return self._ui_success("abrir_eventos", "EVENTOS", "", "LISTADO", "Eventos")

    def _ui_abrir_reservas(self, _data: dict[str, Any]) -> HostAIToolResult:
        return self._ui_success("abrir_reservas", "RESERVAS", "", "LISTADO", "Reservas")

    def _ui_abrir_reserva(self, data: dict[str, Any]) -> HostAIToolResult:
        identity = str(data.get("reserva_id") or "").strip().upper()
        if RESERVA_ID_PATTERN.fullmatch(identity) is None or self.reservas_read_service is None:
            return self._ui_error("abrir_reserva")
        detail = self.reservas_read_service.detalle(identity)
        if not detail or str(detail.get("reserva_id") or "") != identity:
            return self._ui_error("abrir_reserva")
        return self._ui_success("abrir_reserva", "RESERVAS", identity, "DETALLE", str(detail.get("nombre_cliente") or identity))

    @staticmethod
    def _ui_error(tool_id: str, code: str = "ui_action_target_invalid") -> HostAIToolResult:
        return HostAIToolResult(estado="ERROR", mensaje="El destino solicitado no existe o no está permitido.", errores=[code], tool_id=tool_id)

    @staticmethod
    def _ui_success(tool_id: str, target: str, identity: str, view: str, label: str) -> HostAIToolResult:
        action = {"type": "OPEN_VIEW", "target": target, "id": identity, "view": view, "label": label, "safe": True, "datos_reales_modificados": False}
        return HostAIToolResult(estado="OK", mensaje="Vista preparada.", datos={"ui_action": action, "solo_lectura": True, "datos_reales_modificados": False}, acciones=[action], tool_id=tool_id)

    def execute_agent_read(self, tool_id: str, params: dict[str, Any] | None = None, execution_context: Any | None = None) -> HostAIToolResult:
        inicio = time.perf_counter()
        handler = self._agent_read_handlers.get(str(tool_id or ""))
        if handler is None:
            return self._finish(HostAIToolResult(estado="ERROR", mensaje="Herramienta READ no autorizada.", errores=["agent_tool_not_allowed"], tool_id=str(tool_id or "")), inicio)
        if execution_context is not None:
            valid, _reason = execution_context.validate()
            if not valid:
                return self._finish(HostAIToolResult(estado="ERROR", mensaje="Contexto autorizado invalido.", errores=["invalid_execution_context"], tool_id=str(tool_id or "")), inicio)
        try:
            result = handler(dict(params or {}), {})
            result.tool_id = str(tool_id)
            return self._finish(result, inicio)
        except Exception:
            LOGGER.exception("agent_tool_execute_error %s", {"tool_id": tool_id})
            return self._finish(HostAIToolResult(estado="ERROR", mensaje="Error ejecutando la herramienta READ.", errores=["internal_tool_error"], tool_id=str(tool_id or "")), inicio)

    def _build_articulos_read_service(self) -> Any | None:
        core = getattr(self.home_read_service, "core", None)
        base_dir = getattr(core, "base_dir", None)
        if core is None or base_dir is None:
            return None
        return ArticulosCatalogReadService(
            base_dir,
            stock=getattr(core, "stock", None),
            compras=getattr(core, "compras", None),
        )

    def execute(self, tool_id: str, params: dict[str, Any] | None = None, session_context: dict[str, Any] | None = None) -> HostAIToolResult:
        inicio = time.perf_counter()
        tool = self.registry.get(tool_id)
        p = dict(params or {})
        ctx = dict(session_context or {})

        if tool is None:
            return self._finish(
                HostAIToolResult(
                    estado="ERROR",
                    mensaje="Herramienta no registrada.",
                    errores=["tool_not_found"],
                    tool_id=str(tool_id or ""),
                ),
                inicio,
            )

        if tool.estado != TOOL_STATUS_ACTIVADA:
            return self._finish(
                HostAIToolResult(
                    estado="DESHABILITADA",
                    mensaje="La herramienta esta deshabilitada en este entorno.",
                    advertencias=["tool_disabled"],
                    tool_id=tool.id,
                ),
                inicio,
            )

        if tool.tipo not in {"READ", "NAVIGATION", "ANALYSIS"}:
            return self._finish(
                HostAIToolResult(
                    estado="DESHABILITADA",
                    mensaje="Solo se permiten herramientas READ/NAVIGATION/ANALYSIS en este sprint.",
                    advertencias=["tool_type_not_allowed"],
                    tool_id=tool.id,
                ),
                inicio,
            )

        if tool.requiere_contexto and not ctx.get("contexto_activo"):
            return self._finish(
                HostAIToolResult(
                    estado="ADVERTENCIA",
                    mensaje="Necesito contexto activo para ejecutar esta herramienta.",
                    advertencias=["missing_context"],
                    tool_id=tool.id,
                ),
                inicio,
            )

        try:
            handler = getattr(self, f"_tool_{tool.id}", None)
            if handler is None:
                return self._finish(
                    HostAIToolResult(
                        estado="ERROR",
                        mensaje="Herramienta registrada sin ejecutor disponible.",
                        errores=["tool_handler_missing"],
                        tool_id=tool.id,
                    ),
                    inicio,
                )
            result = handler(p, ctx)
            result.tool_id = tool.id
            return self._finish(result, inicio)
        except Exception:
            LOGGER.exception("tool_execute_error %s", {"tool_id": tool.id})
            return self._finish(
                HostAIToolResult(
                    estado="ERROR",
                    mensaje="Error ejecutando la herramienta.",
                    errores=["internal_tool_error"],
                    tool_id=tool.id,
                ),
                inicio,
            )

    def _finish(self, result: HostAIToolResult, inicio: float) -> HostAIToolResult:
        result.duracion_ms = int((time.perf_counter() - inicio) * 1000)
        LOGGER.info(
            "tool_audit %s",
            {
                "tool_id": result.tool_id,
                "estado": result.estado,
                "duracion_ms": result.duracion_ms,
                "errores": list(result.errores),
                "advertencias": list(result.advertencias),
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "contexto": str((result.contexto_actualizado or {}).get("contexto_activo") or ""),
            },
        )
        return result

    def _ensure_home(self) -> dict[str, Any]:
        if self.home_read_service is None:
            return {"modulos": {}, "estado_global": "servicio_no_disponible"}
        return dict(self.home_read_service.cargar_home() or {})

    def _build_nav(self, target_module: str, target_view: str = "", entity_id: str = "", filter_data: dict[str, Any] | None = None, context_update: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "target_module": str(target_module or ""),
            "target_view": str(target_view or ""),
            "filter_data": dict(filter_data or {}),
            "entity_id": str(entity_id or ""),
            "source": "tool_executor",
            "preserve_chat_session": True,
            "message": "Navegacion solicitada por herramienta registrada.",
            "context_update": dict(context_update or {}),
        }

    def _tool_buscar_recetas(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        termino = str(params.get("termino") or "").strip()
        if not termino:
            return HostAIToolResult(estado="ADVERTENCIA", mensaje="Necesito un termino para buscar receta.", advertencias=["missing_term"])
        items = list((self.home_read_service.buscar_recetas(termino, limite=10) if self.home_read_service else []) or [])
        if not items:
            return HostAIToolResult(estado="OK", mensaje=f"No encontre recetas relacionadas con '{termino}'. Puedes probar con otro nombre o ingrediente.", datos={"resultados": []})
        return HostAIToolResult(
            estado="OK",
            mensaje=f"Encontre {len(items)} recetas relacionadas con '{termino}'.",
            datos={"resultados": items[:10], "termino": termino},
            acciones=[{"code": "abrir_recetas", "label": "Abrir Recetas y Escandallos"}],
            contexto_actualizado={"contexto_activo": "RECETA", "ultima_busqueda": termino, "ultima_lista_mostrada": items[:10]},
        )

    def _tool_abrir_receta(self, params: dict[str, Any], ctx: dict[str, Any]) -> HostAIToolResult:
        item = dict(params.get("item") or ctx.get("ultimo_elemento_seleccionado") or {})
        nav = self._build_nav(
            "RECETAS_ESCANDALLOS",
            target_view="RECETA",
            entity_id=str(item.get("id") or item.get("codigo") or ""),
            filter_data={"item": item},
            context_update={"contexto_activo": "RECETA", "receta_activa": item},
        )
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir la receta.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})

    def _tool_buscar_escandallos(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        term = str(params.get("termino") or "").lower().strip()
        items = list((((self._ensure_home().get("modulos") or {}).get("escandallos") or {}).get("items") or []))
        if term:
            items = [i for i in items if term in str(i.get("nombre") or "").lower() or term in str(i.get("codigo") or "").lower()]
        if not items:
            return HostAIToolResult(estado="OK", mensaje="No hay escandallos desactualizados.", datos={"resultados": []})
        return HostAIToolResult(estado="OK", mensaje=f"Hay {len(items)} escandallos desactualizados.", datos={"resultados": items[:10]}, contexto_actualizado={"contexto_activo": "ESCANDALLO", "ultima_lista_mostrada": items[:10]})

    def _tool_abrir_escandallo(self, params: dict[str, Any], ctx: dict[str, Any]) -> HostAIToolResult:
        item = dict(params.get("item") or ctx.get("escandallo_activo") or ctx.get("receta_activa") or {})
        nav = self._build_nav(
            "RECETAS_ESCANDALLOS",
            target_view="ESCANDALLO",
            entity_id=str(item.get("id") or item.get("codigo") or ""),
            filter_data={"item": item},
            context_update={"contexto_activo": "ESCANDALLO", "escandallo_activo": item},
        )
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir el escandallo.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})

    def _tool_buscar_eventos(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        term = str(params.get("termino") or "").lower().strip()
        items = list((((self._ensure_home().get("modulos") or {}).get("eventos") or {}).get("items") or []))
        if term:
            items = [i for i in items if term in str(i.get("nombre") or "").lower()]
        if not items:
            return HostAIToolResult(estado="OK", mensaje="No hay eventos proximos registrados en este momento.", datos={"resultados": []})
        top = items[:5]
        texto_items = "; ".join([f"{x.get('nombre')} ({x.get('fecha')})" for x in top])
        return HostAIToolResult(
            estado="OK",
            mensaje=f"Eventos proximos: {texto_items}.",
            datos={"resultados": top},
            acciones=[{"code": "abrir_eventos", "label": "Abrir Eventos"}],
            contexto_actualizado={"contexto_activo": "EVENTO", "ultima_lista_mostrada": top},
        )

    def _tool_mostrar_eventos(self, params: dict[str, Any], ctx: dict[str, Any]) -> HostAIToolResult:
        return self._tool_buscar_eventos(params, ctx)

    def _tool_abrir_evento(self, params: dict[str, Any], ctx: dict[str, Any]) -> HostAIToolResult:
        item = dict(params.get("item") or ctx.get("evento_activo") or {})
        nav = self._build_nav(
            "EVENTOS",
            target_view="EVENTO",
            entity_id=str(item.get("id") or ""),
            filter_data={"item": item},
            context_update={"contexto_activo": "EVENTO", "evento_activo": item},
        )
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir eventos.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})

    def _tool_mostrar_eventos_proximos(self, params: dict[str, Any], ctx: dict[str, Any]) -> HostAIToolResult:
        return self._tool_buscar_eventos(params, ctx)

    def _tool_consultar_eventos(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        consulta = str(params.get("consulta") or "proximos").strip().lower()
        termino = str(params.get("evento_id") or params.get("termino") or "").strip().lower()
        limite = max(1, min(int(params.get("limite") or 10), 10))
        items = list((((self._ensure_home().get("modulos") or {}).get("eventos") or {}).get("items") or []))
        if termino:
            items = [item for item in items if termino in str(item.get("id") or "").lower() or termino in str(item.get("nombre") or "").lower()]
        resultados = items[:limite]
        estado = "OK" if resultados else "NO_ENCONTRADO"
        return HostAIToolResult(estado="OK", mensaje="Consulta de Eventos completada.", datos={
            "estado": estado, "consulta": consulta, "resultados": resultados,
            "total_resultados": len(resultados), "fuente": "eventos_canonicos",
            "orden": "fecha_ascendente", "solo_lectura": True,
            "datos_reales_modificados": False,
        })

    def _tool_consultar_evento_detalle(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        event_id = str(params.get("evento_id") or "").strip()
        if not event_id:
            return HostAIToolResult(estado="ERROR", mensaje="Necesito un evento concreto para consultar su detalle.", errores=["event_id_required"])
        core = getattr(self.home_read_service, "core", None)
        events = getattr(core, "eventos", None)
        if events is None:
            return HostAIToolResult(estado="ERROR", mensaje="El detalle de Eventos no está disponible.", errores=["event_detail_unavailable"])
        try:
            raw = events.obtener(event_id)
        except (KeyError, ValueError):
            return HostAIToolResult(estado="OK", mensaje="Evento no encontrado.", datos={"estado": "NO_ENCONTRADO", "evento": None, "solo_lectura": True, "datos_reales_modificados": False})
        event = raw.to_dict() if hasattr(raw, "to_dict") else dict(raw or {})
        services = []
        for service in list(event.get("servicios") or []):
            item = dict(service or {})
            services.append({
                "servicio_id": str(item.get("id") or ""), "nombre": str(item.get("nombre") or ""),
                "menu_id": str(item.get("menu_id") or ""),
                "pases": [
                    {"pase_id": str(p.get("id") or ""), "nombre": str(p.get("nombre") or ""), "menu_id": str(p.get("menu_id") or ""), "recetas": list(p.get("recetas") or [])}
                    for p in list(item.get("pases") or []) if isinstance(p, dict)
                ],
            })
        detail = {"evento_id": str(event.get("id") or ""), "nombre": str(event.get("nombre") or ""), "fecha": event.get("fecha"), "hora_inicio": event.get("hora_inicio"), "pax": event.get("pax"), "estado": event.get("estado"), "servicios": services}
        return HostAIToolResult(estado="OK", mensaje="Detalle de evento obtenido.", datos={"estado": "OK", "evento": detail, "fuente": "motor_eventos_canonico", "solo_lectura": True, "datos_reales_modificados": False})

    def _tool_consultar_reservas(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        if self.reservas_read_service is None:
            return HostAIToolResult(estado="ERROR", mensaje="El servicio de reservas no esta disponible.", errores=["reservas_service_unavailable"])
        alcance = str(params.get("alcance") or "todas").strip().lower()
        query = str(params.get("q") or "").strip()
        reserva_id = str(params.get("reserva_id") or "").strip().upper()
        limite = max(1, min(int(params.get("limite") or 10), 10))
        common = {
            "estado": str(params.get("estado") or "").strip(),
            "servicio": str(params.get("servicio") or "").strip(),
            "limite": limite,
        }
        context = {"contexto_activo": "RESERVA", "ultimo_modulo": "RESERVAS", "ultima_busqueda": query or reserva_id}
        if reserva_id:
            detail = self.reservas_read_service.detalle(reserva_id)
            results = [detail] if detail else []
            state = "OK" if detail else "NO_ENCONTRADO"
            if detail:
                context["reserva_activa"] = dict(detail)
        else:
            if alcance == "hoy":
                results = self.reservas_read_service.hoy(nombre=query, **common)
            elif alcance == "proximas":
                results = self.reservas_read_service.proximas(nombre=query, **common)
            else:
                results = self.reservas_read_service.listar(fecha=str(params.get("fecha") or "").strip(), nombre=query, **common)
            state = "AMBIGUO" if query and len(results) > 1 else ("OK" if results else "NO_ENCONTRADO")
            if query and len(results) == 1:
                context["reserva_activa"] = dict(results[0])
        context["ultima_lista_mostrada"] = list(results)
        message = "No hay reservas registradas." if not results else ("Hay varias reservas coincidentes; indica el ID exacto." if state == "AMBIGUO" else "Consulta de reservas completada.")
        return HostAIToolResult(estado="OK", mensaje=message, datos={
            "estado": state, "alcance": alcance, "resultados": results, "total_resultados": len(results),
            "fuente": "reservas_canonicas", "solo_lectura": True, "datos_reales_modificados": False,
        }, contexto_actualizado=context)

    def _tool_mostrar_estado_general(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        modelo = self._ensure_home()
        modulos = dict(modelo.get("modulos") or {})
        partes = []
        for clave in ["eventos", "recetas", "escandallos", "incidencias", "compras", "stock", "produccion", "menus"]:
            m = dict(modulos.get(clave) or {})
            partes.append(f"{clave}: {m.get('estado', 'desconocido')} ({int(m.get('total') or 0)})")
        return HostAIToolResult(estado="OK", mensaje="Estado general: " + " | ".join(partes), datos={"home": modelo})

    def _tool_consultar_estado_stock(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        consulta_solicitada = str(params.get("consulta") or "resumen").strip().lower()
        termino = str(params.get("termino") or "").strip()
        terminos = list(params.get("terminos") or [])
        if terminos:
            return self._stock_batch(terminos)
        consulta = "articulo" if termino else consulta_solicitada
        stock = dict(((self._ensure_home().get("modulos") or {}).get("stock") or {}))
        resumen = self._stock_resumen(stock)
        alertas = [self._stock_alerta(item) for item in list(stock.get("alertas") or [])[:10]]
        existencias = [self._stock_existencia(item) for item in list(stock.get("existencias") or [])[:10]]
        estado_dto = "OK"
        mensaje = self._stock_mensaje_resumen(resumen)

        if consulta == "alertas":
            existencias = []
            mensaje = f"Hay {len(alertas)} alertas de Stock." if alertas else "No hay alertas de Stock registradas."
        elif consulta == "articulo":
            alertas = []
            existencias, estado_dto, mensaje = self._buscar_stock_articulo(termino)

        datos = {
            "estado": estado_dto,
            "consulta": consulta,
            "termino": termino,
            "ambito_resultados": "FILTRADO_POR_TERMINO" if consulta == "articulo" else "GLOBAL",
            "existencias": existencias[:10],
            "alertas": alertas[:10],
            "fuente": "stock_canonico",
            "solo_lectura": True,
            "datos_reales_modificados": False,
        }
        if consulta == "articulo":
            datos["resultados_filtrados"] = existencias[:10]
            datos["resumen_global"] = resumen
        else:
            datos["resumen"] = resumen

        return HostAIToolResult(
            estado="OK",
            mensaje=mensaje,
            datos=datos,
        )

    def _stock_batch(self, raw_terms: list[Any]) -> HostAIToolResult:
        terms = [str(value or "").strip() for value in raw_terms]
        if not terms or len(terms) > 10 or any(not value for value in terms):
            return HostAIToolResult(estado="ERROR", mensaje="La consulta batch admite entre 1 y 10 articulos.", errores=["invalid_stock_batch"])
        normalized: set[str] = set()
        items: list[dict[str, Any]] = []
        for term in terms:
            key = self._norm_text(term)
            if key in normalized:
                items.append({"termino": term, "estado": "DUPLICADO", "existencias": []})
                continue
            normalized.add(key)
            existencias, state, _message = self._buscar_stock_articulo(term)
            items.append({"termino": term, "estado": state, "existencias": existencias[:10]})
        partial = any(item["estado"] != "OK" for item in items)
        checked = sum(item["estado"] == "OK" for item in items)
        return HostAIToolResult(
            estado="OK",
            mensaje=f"Stock batch: {checked} de {len(items)} articulos comprobados.",
            datos={
                "estado": "PARCIAL" if partial else "OK", "consulta": "articulos_batch",
                "items": items, "batch_size": len(items), "comprobados": checked,
                "resultados_parciales": partial, "fuente": "stock_canonico",
                "solo_lectura": True, "datos_reales_modificados": False,
            },
        )

    def _tool_buscar_articulos(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        if "terminos" in params:
            return self._tool_buscar_articulos_batch(list(params.get("terminos") or []), _ctx)
        termino = str(params.get("termino") or "").strip()
        if not termino:
            return self._article_search_result(
                estado="REQUIERE_TERMINO",
                termino="",
                articulos=[],
                total=0,
                mensaje="Indica un nombre o codigo de articulo para buscar.",
            )
        if self.articulos_read_service is None:
            return self._article_search_result(
                estado="SERVICIO_NO_DISPONIBLE",
                termino=termino,
                articulos=[],
                total=0,
                mensaje="El catalogo de articulos no esta disponible en este entorno.",
            )

        result = dict(self.articulos_read_service.listar({"q": termino, "page": 1, "page_size": 10}) or {})
        if result.get("ok") is False:
            return self._article_search_result(
                estado="ERROR",
                termino=termino,
                articulos=[],
                total=0,
                mensaje="No se pudo consultar el catalogo de articulos.",
            )
        catalogo = dict(result.get("catalogo") or {})
        items = [self._article_basic(item) for item in list(catalogo.get("items") or [])[:10]]
        exact_code = [item for item in items if self._norm_text(item.get("codigo")) == self._norm_text(termino)]
        exact_name = [item for item in items if self._norm_text(item.get("nombre")) == self._norm_text(termino)]

        selected = exact_code if len(exact_code) == 1 else exact_name if len(exact_name) == 1 else []
        if selected:
            items = selected
            estado = "OK"
            total = 1
        else:
            total = int(catalogo.get("total") or len(items))
            estado = "OK" if len(items) == 1 else "AMBIGUO" if items else "NO_ENCONTRADO"

        if estado == "OK":
            item = items[0]
            mensaje = f"{item['codigo']} — {item['nombre']} — {item.get('unidad') or 'unidad no definida'} — {item.get('estado') or 'estado no informado'}."
        elif estado == "AMBIGUO":
            lines = [f"{index}. {item['codigo']} — {item['nombre']} — {item.get('unidad') or 'unidad no definida'}" for index, item in enumerate(items, start=1)]
            mensaje = f"He encontrado {total} articulos relacionados con '{termino}':\n" + "\n".join(lines) + "\nIndica el numero, codigo o nombre exacto."
        else:
            mensaje = f"No encuentro ningun articulo que coincida con '{termino}'."

        return self._article_search_result(
            estado=estado,
            termino=termino,
            articulos=items,
            total=total,
            mensaje=mensaje,
        )

    def _tool_buscar_articulos_batch(self, raw_terms: list[Any], ctx: dict[str, Any]) -> HostAIToolResult:
        terms = [str(value or "").strip() for value in raw_terms]
        if not terms or len(terms) > 10 or any(not term for term in terms):
            return HostAIToolResult(
                estado="ERROR",
                mensaje="La busqueda batch admite entre 1 y 10 terminos no vacios.",
                errores=["invalid_article_search_batch"],
            )
        results: list[dict[str, Any]] = []
        for term in terms:
            single = self._tool_buscar_articulos({"termino": term}, ctx)
            data = dict(single.datos or {})
            articles = [dict(item) for item in list(data.get("articulos") or [])]
            state = str(data.get("estado") or "ERROR")
            item = {
                "termino": term,
                "estado": state,
                "articulos": articles,
                "total_encontrados": int(data.get("total_encontrados") or len(articles)),
            }
            if state == "OK" and len(articles) == 1:
                article = articles[0]
                item.update({
                    "article_id": str(article.get("article_id") or article.get("id") or article.get("codigo") or ""),
                    "codigo": str(article.get("codigo") or ""),
                    "nombre": str(article.get("nombre") or ""),
                    "unidad": article.get("unidad"),
                })
            elif state == "AMBIGUO":
                item["candidatos"] = articles
            results.append(item)
        resolved = sum(item["estado"] == "OK" for item in results)
        partial = resolved != len(results)
        return HostAIToolResult(
            estado="OK",
            mensaje=f"Busqueda batch: {resolved} de {len(results)} terminos resueltos sin ambiguedad.",
            datos={
                "estado": "PARCIAL" if partial else "OK",
                "resultados": results,
                "batch_size": len(results),
                "resueltos": resolved,
                "resultados_parciales": partial,
                "fuente": "catalogo_articulos_canonico",
                "solo_lectura": True,
                "datos_reales_modificados": False,
            },
        )

    def _tool_consultar_articulo_detalle(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        article_id = str(params.get("article_id") or "").strip()
        detail = dict(self.articulos_read_service.obtener(article_id) or {}) if self.articulos_read_service else {}
        article = detail.get("articulo") if detail.get("ok") is not False else None
        if not isinstance(article, dict):
            return HostAIToolResult(estado="OK", mensaje="Artículo no encontrado.", datos={"estado": "NO_ENCONTRADO", "article_id": article_id, "solo_lectura": True, "datos_reales_modificados": False})
        return HostAIToolResult(estado="OK", mensaje="Detalle de artículo obtenido.", datos={
            "estado": "OK", "articulo": article, "fuente": "catalogo_articulos_canonico",
            "solo_lectura": True, "datos_reales_modificados": False,
        }, contexto_actualizado={"contexto_activo": "ARTICULO", "ultimo_modulo": "CATALOGO", "articulo_activo": {"id": article.get("id"), "nombre": article.get("nombre"), "tipo": "ARTICULO"}})

    def _compras_result(self, data: dict[str, Any]) -> HostAIToolResult:
        state = str(data.get("estado") or "VACIO")
        if state == "AMBIGUO":
            orders = list(data.get("pedidos") or [])
            if orders:
                lines = [f"{item.get('pedido_id')} — {item.get('proveedor_nombre')} — {item.get('estado')}" for item in orders]
                message = "He encontrado varios pedidos compatibles:\n" + "\n".join(lines) + "\nIndica el pedido exacto."
            else:
                names = ", ".join(str(item.get("nombre") or "") for item in list(data.get("proveedores") or []))
                message = f"Hay varios proveedores coincidentes: {names}. Indica el nombre exacto."
        elif state in {"VACIO", "NO_ENCONTRADO"}:
            message = "No hay resultados para esta consulta de Compras."
        elif data.get("pedidos"):
            lines = []
            for order in list(data.get("pedidos") or []):
                pending = sum(float(line.get("pendiente") or 0) for line in list(order.get("lineas") or []))
                suffix = f"; pendiente {pending:g}" if order.get("pendiente_recepcion") else ""
                lines.append(f"{order.get('pedido_id')} — {order.get('proveedor_nombre')} — {order.get('estado')}{suffix}")
            message = "Pedidos encontrados:\n" + "\n".join(lines)
        elif data.get("propuestas"):
            message = f"Hay {len(data['propuestas'])} propuestas de compra existentes."
        else:
            message = f"Hay {len(data.get('necesidades') or [])} necesidades de compra existentes."
        return HostAIToolResult(estado="OK", mensaje=message, datos=data)

    def _compras_service(self) -> Any:
        if self.compras_read_service is None:
            raise RuntimeError("Servicio de lectura de Compras no disponible")
        return self.compras_read_service

    def _tool_consultar_compras_pendientes(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        consulta = str(params.get("consulta") or "listado")
        pedido_id = str(params.get("pedido_id") or "").strip()
        return self._compras_result(self._compras_service().consultar_pedidos(
            consulta=consulta,
            estado=str(params.get("estado") or ""),
            pedido_id=pedido_id,
            article_id=str(params.get("article_id") or ""),
            proveedor=str(params.get("proveedor") or ""),
            limite=params.get("limite", 10),
            solo_abiertos=not bool(params.get("estado")) and not bool(pedido_id) and consulta != "pedido",
        ))

    def _tool_consultar_pendiente_recepcion(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        return self._compras_result(self._compras_service().consultar_pedidos(pendientes_recepcion=True))

    def _tool_consultar_propuestas_compra(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        return self._compras_result(self._compras_service().consultar_propuestas())

    def _tool_consultar_necesidades_compra(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        return self._compras_result(self._compras_service().consultar_necesidades())

    def _tool_buscar_pedidos_por_proveedor(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        return self._compras_result(self._compras_service().buscar_por_proveedor(str(params.get("proveedor") or "")))

    def _tool_consultar_produccion(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        if self.produccion_read_service is None:
            raise RuntimeError("Servicio de lectura de Produccion no disponible")
        data = self.produccion_read_service.consultar(
            str(params.get("consulta") or "pendientes"),
            termino=str(params.get("termino") or ""),
            fecha=params.get("fecha"),
            limite=params.get("limite", 10),
            plan_id=str(params.get("plan_id") or ""),
            menu_id=str(params.get("menu_id") or ""),
        )
        state = str(data.get("estado") or "VACIO")
        results = list(data.get("resultados") or [])
        if state == "AMBIGUO":
            message = f"He encontrado {len(results)} tareas de produccion posibles. Indica una tarea concreta."
        elif state in {"VACIO", "NO_ENCONTRADO"}:
            message = "No hay resultados para esta consulta de Produccion."
        else:
            message = "Produccion encontrada:\n" + "\n".join(f"{item.get('titulo')} — {item.get('estado')}" for item in results)
        return HostAIToolResult(estado="OK", mensaje=message, datos=data)

    def _tool_consultar_escandallos(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        if self.escandallos_read_service is None:
            raise RuntimeError("Servicio de lectura de Escandallos no disponible")
        data = self.escandallos_read_service.consultar(
            consulta=str(params.get("consulta") or "buscar"),
            termino=str(params.get("termino") or ""),
            escandallo_id=str(params.get("escandallo_id") or ""),
            limite=params.get("limite", 10),
            agregacion=str(params.get("agregacion") or ""),
            orden=str(params.get("orden") or ""),
            posicion=params.get("posicion", 1),
            estado_coste=str(params.get("estado_coste") or ""),
            pagina=params.get("pagina", 1),
            escandallo_ids=list(params.get("escandallo_ids") or []),
            nombre_referencia=str(params.get("nombre_referencia") or ""),
        )
        return HostAIToolResult(estado="OK", mensaje="Consulta de escandallos completada.", datos=data)

    def _tool_consultar_uso_elaboracion(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        if self.uso_elaboracion_read_service is None:
            raise RuntimeError("Servicio de lectura de uso de elaboraciones no disponible")
        data = self.uso_elaboracion_read_service.consultar(
            escandallo_id=str(params.get("escandallo_id") or ""),
            termino=str(params.get("termino") or ""),
            limite=params.get("limite", 10),
        )
        return HostAIToolResult(estado="OK", mensaje="Consulta de uso de elaboración completada.", datos=data)

    def _tool_consultar_menu(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        if self.menus_read_service is None:
            raise RuntimeError("Servicio de lectura de Menús no disponible")
        data = self.menus_read_service.consultar(
            consulta=str(params.get("consulta") or "detalle"),
            menu_id=str(params.get("menu_id") or ""),
            termino=str(params.get("termino") or ""),
            limite=params.get("limite", 10),
        )
        return HostAIToolResult(estado="OK", mensaje="Consulta de menú completada.", datos=data)

    def _tool_consultar_necesidades_operativas(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        if self.operational_needs_read_service is None:
            raise RuntimeError("Servicio de necesidades operativas no disponible")
        data = self.operational_needs_read_service.consultar_menu(str(params.get("menu_id") or ""))
        return HostAIToolResult(
            estado="OK" if data.get("estado") == "OK" else "NO_ENCONTRADO",
            mensaje="Necesidades operativas calculadas.", datos=data,
        )

    def _article_search_result(
        self,
        *,
        estado: str,
        termino: str,
        articulos: list[dict[str, Any]],
        total: int,
        mensaje: str,
    ) -> HostAIToolResult:
        return HostAIToolResult(
            estado="OK" if estado not in {"ERROR", "SERVICIO_NO_DISPONIBLE"} else "ERROR",
            mensaje=mensaje,
            datos={
                "estado": estado,
                "termino": termino,
                "total_encontrados": int(total),
                "articulos": articulos[:10],
                "puede_abrir_buscador": True,
                "busqueda_sugerida": termino,
                "fuente": "catalogo_articulos_canonico",
                "solo_lectura": True,
                "datos_reales_modificados": False,
            },
            contexto_actualizado={
                "contexto_activo": "CATALOGO",
                "ultima_busqueda": termino,
                "ultima_lista_mostrada": articulos[:10],
            } if articulos else {},
        )

    @staticmethod
    def _article_basic(item: dict[str, Any]) -> dict[str, Any]:
        estado = str(item.get("estado") or "")
        estado_norm = estado.strip().lower()
        activo = True if estado_norm == "activo" else False if estado_norm in {"inactivo", "archivado"} else None
        return {
            "article_id": str(item.get("id") or ""),
            "codigo": str(item.get("codigo") or ""),
            "nombre": str(item.get("nombre") or ""),
            "unidad": item.get("unidad") or None,
            "estado": estado or None,
            "activo": activo,
        }

    @staticmethod
    def _stock_resumen(stock: dict[str, Any]) -> dict[str, Any]:
        source = dict(stock.get("resumen") or {})
        return {
            "estado_operativo": str(stock.get("estado_operativo") or ""),
            "existencias": int(stock.get("total_existencias") or 0),
            "alertas": int(stock.get("total_alertas") or 0),
            "lotes_visibles": int(stock.get("total_lotes") or 0),
            "bajo_minimo": int(source.get("bajo_minimo") or 0),
            "caducados": int(source.get("caducados") or 0),
            "caducan_pronto": int(source.get("caducan_pronto") or 0),
        }

    @staticmethod
    def _stock_existencia(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "article_id": str(item.get("articulo_id") or item.get("article_id") or item.get("codigo") or ""),
            "nombre": str(item.get("nombre") or ""),
            "cantidad": item.get("cantidad"),
            "unidad": item.get("unidad") or None,
        }

    @staticmethod
    def _stock_alerta(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "tipo": str(item.get("tipo") or ""),
            "nivel": str(item.get("nivel") or ""),
            "mensaje": str(item.get("mensaje") or ""),
        }

    @staticmethod
    def _stock_mensaje_resumen(resumen: dict[str, Any]) -> str:
        return f"Stock consultado: {resumen['existencias']} existencias y {resumen['alertas']} alertas registradas."

    def _buscar_stock_articulo(self, termino: str) -> tuple[list[dict[str, Any]], str, str]:
        if not termino or self.articulos_read_service is None:
            return [], "NO_ENCONTRADO", "No se ha encontrado el articulo solicitado."
        result = dict(self.articulos_read_service.listar({"q": termino, "page": 1, "page_size": 10}) or {})
        catalogo = dict(result.get("catalogo") or {})
        candidates = [self._stock_catalog_item(item) for item in list(catalogo.get("items") or [])[:10]]
        exact = [
            item for item in candidates
            if self._norm_text(item.get("nombre")) == self._norm_text(termino)
            or self._norm_text(item.get("article_id")) == self._norm_text(termino)
        ]
        if len(exact) == 1:
            candidates = exact
        elif len(candidates) > 1:
            return candidates, "AMBIGUO", f"He encontrado {len(candidates)} articulos posibles para '{termino}'. Indica cual quieres consultar."
        if not candidates:
            return [], "NO_ENCONTRADO", f"No se ha encontrado ningun articulo relacionado con '{termino}'."
        item = candidates[0]
        if item.get("cantidad") is None:
            return candidates, "OK", f"{item['nombre']} existe en el catalogo, pero su stock es desconocido."
        return candidates, "OK", f"{item['nombre']}: {item['cantidad']} {item.get('unidad') or ''} disponibles.".strip()

    @staticmethod
    def _stock_catalog_item(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "article_id": str(item.get("id") or item.get("codigo") or ""),
            "nombre": str(item.get("nombre") or ""),
            "cantidad": item.get("stock"),
            "unidad": item.get("unidad_stock") or item.get("unidad") or None,
        }

    @staticmethod
    def _norm_text(value: Any) -> str:
        import unicodedata

        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in text if not unicodedata.combining(char)).strip().lower()

    def _tool_listar_recetas_pendientes(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        items = list((((self._ensure_home().get("modulos") or {}).get("recetas") or {}).get("items") or []))
        if not items:
            return HostAIToolResult(estado="OK", mensaje="No hay recetas pendientes de completar.", datos={"resultados": []})
        return HostAIToolResult(estado="OK", mensaje=f"Hay {len(items)} recetas pendientes de completar.", datos={"resultados": items[:10]}, contexto_actualizado={"contexto_activo": "RECETA", "ultima_lista_mostrada": items[:10]})

    def _tool_listar_escandallos_desactualizados(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        return self._tool_buscar_escandallos({}, {})

    def _tool_listar_incidencias(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        items = list((((self._ensure_home().get("modulos") or {}).get("incidencias") or {}).get("items") or []))
        if not items:
            return HostAIToolResult(estado="OK", mensaje="No hay incidencias abiertas.", datos={"resultados": []})
        return HostAIToolResult(estado="OK", mensaje=f"Hay {len(items)} incidencias abiertas.", datos={"resultados": items[:10]}, contexto_actualizado={"contexto_activo": "INCIDENCIAS", "ultima_lista_mostrada": items[:10]})

    def _tool_abrir_produccion(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        nav = self._build_nav("PRODUCCION", target_view="MODULO", context_update={"contexto_activo": "PRODUCCION"})
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir ese modulo.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})

    def _tool_abrir_compras(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        nav = self._build_nav("COMPRAS", target_view="MODULO", context_update={"contexto_activo": "COMPRAS"})
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir ese modulo.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})

    def _tool_abrir_stock(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        nav = self._build_nav("STOCK", target_view="MODULO", context_update={"contexto_activo": "STOCK"})
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir ese modulo.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})

    def _tool_abrir_menus(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        nav = self._build_nav("MENUS", target_view="MODULO", context_update={"contexto_activo": "MENU"})
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir ese modulo.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})

    def _tool_abrir_catalogo(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        nav = self._build_nav("CATALOGO", target_view="MODULO", context_update={"contexto_activo": "CATALOGO"})
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir ese modulo.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})

    def _tool_abrir_importaciones(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        nav = self._build_nav("IMPORTACIONES", target_view="MODULO", context_update={"contexto_activo": "IMPORTACIONES"})
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir ese modulo.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})

    def _tool_abrir_incidencias(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        nav = self._build_nav("INCIDENCIAS", target_view="MODULO", context_update={"contexto_activo": "INCIDENCIAS"})
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir ese modulo.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})

    def _tool_abrir_estadisticas(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        nav = self._build_nav("ESTADISTICAS", target_view="MODULO", context_update={"contexto_activo": "ESTADISTICAS"})
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir ese modulo.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})

    def _tool_abrir_configuracion(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        nav = self._build_nav("CONFIGURACION", target_view="MODULO", context_update={"contexto_activo": "CONFIGURACION"})
        return HostAIToolResult(estado="OK", mensaje="De acuerdo, salgo al shell para abrir ese modulo.", navegacion=nav, contexto_actualizado=nav.get("context_update") or {})


__all__ = ["HostAIToolExecutor", "HostAIToolResult"]
