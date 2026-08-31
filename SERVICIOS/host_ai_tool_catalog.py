from __future__ import annotations

from copy import deepcopy
from typing import Any

from SERVICIOS.host_ai_tool_registry import HostAIToolRegistry, TOOL_STATUS_ACTIVADA
from SERVICIOS.host_ai_tool_schemas import (
    ARTICLE_DETAIL_INPUT, ARTICLE_SEARCH_INPUT, ESCANDALLOS_INPUT, EVENTS_INPUT, MENU_INPUT, OPEN_ARTICLE_INPUT, OPEN_ELABORATION_INPUT,
    APPLY_RESERVATION_INPUT, CREATE_RESERVATION_INPUT, OPEN_EVENTS_INPUT, OPEN_RESERVATION_INPUT, OPEN_RESERVATIONS_INPUT, RESERVATIONS_INPUT, TRANSITION_RESERVATION_INPUT, UPDATE_RESERVATION_INPUT,
    OPEN_MENU_INPUT, OPEN_PRODUCTION_INPUT, OPEN_PURCHASE_INPUT, PRODUCTION_INPUT,
    PURCHASES_INPUT, STOCK_INPUT, USO_ELABORACION_INPUT, OPERATIONAL_NEEDS_INPUT,
    PREVIEW_ARTICLE_PRICE_INPUT, PREVIEW_ARTICLE_CONVERSION_INPUT, PREVIEW_ARTICLE_FORMAT_INPUT, CONFIRM_ARTICLE_CHANGE_INPUT, PREVIEW_LOT_LOCATION_INPUT, CONFIRM_LOT_LOCATION_INPUT,
    CREATE_EVENT_INPUT, CREATE_ARTICLE_INPUT, CREATE_RECIPE_INPUT, APPLY_CATALOG_INPUT,
)


class HostAIToolCatalog:
    TOOL_IDS = ("consultar_produccion", "consultar_estado_stock", "consultar_compras_pendientes")
    GENERAL_AGENT_TOOL_IDS = (
        *TOOL_IDS, "consultar_eventos", "consultar_evento_detalle", "buscar_articulos", "consultar_articulo_detalle", "consultar_reservas", "consultar_escandallos", "consultar_uso_elaboracion", "consultar_menu", "consultar_necesidades_operativas",
        "abrir_elaboracion", "abrir_articulo", "abrir_menu", "abrir_produccion_ui", "abrir_compra", "abrir_eventos", "abrir_reservas", "abrir_reserva",
        "crear_reserva", "modificar_reserva", "confirmar_reserva", "cancelar_reserva", "marcar_no_show", "completar_reserva", "aplicar_operacion_reserva",
        "preparar_precio_articulo", "preparar_conversion_articulo", "preparar_formato_articulo", "confirmar_cambio_articulo",
        "preparar_creacion_evento", "preparar_creacion_articulo", "preparar_creacion_receta", "aplicar_creacion_catalogo",
        "conservar_propuesta_receta", "preparar_ubicacion_lote", "confirmar_ubicacion_lote",
    )
    SCHEMAS = {
        "consultar_produccion": PRODUCTION_INPUT,
        "consultar_eventos": EVENTS_INPUT,
        "consultar_evento_detalle": EVENTS_INPUT,
        "buscar_articulos": ARTICLE_SEARCH_INPUT,
        "consultar_articulo_detalle": ARTICLE_DETAIL_INPUT,
        "consultar_reservas": RESERVATIONS_INPUT,
        "consultar_estado_stock": STOCK_INPUT,
        "consultar_compras_pendientes": PURCHASES_INPUT,
        "consultar_escandallos": ESCANDALLOS_INPUT,
        "consultar_uso_elaboracion": USO_ELABORACION_INPUT,
        "consultar_menu": MENU_INPUT,
        "consultar_necesidades_operativas": OPERATIONAL_NEEDS_INPUT,
        "abrir_elaboracion": OPEN_ELABORATION_INPUT,
        "abrir_articulo": OPEN_ARTICLE_INPUT,
        "abrir_menu": OPEN_MENU_INPUT,
        "abrir_produccion_ui": OPEN_PRODUCTION_INPUT,
        "abrir_compra": OPEN_PURCHASE_INPUT,
        "abrir_eventos": OPEN_EVENTS_INPUT,
        "abrir_reservas": OPEN_RESERVATIONS_INPUT,
        "abrir_reserva": OPEN_RESERVATION_INPUT,
        "crear_reserva": CREATE_RESERVATION_INPUT,
        "modificar_reserva": UPDATE_RESERVATION_INPUT,
        "confirmar_reserva": TRANSITION_RESERVATION_INPUT,
        "cancelar_reserva": TRANSITION_RESERVATION_INPUT,
        "marcar_no_show": TRANSITION_RESERVATION_INPUT,
        "completar_reserva": TRANSITION_RESERVATION_INPUT,
        "aplicar_operacion_reserva": APPLY_RESERVATION_INPUT,
        "preparar_precio_articulo": PREVIEW_ARTICLE_PRICE_INPUT,
        "preparar_conversion_articulo": PREVIEW_ARTICLE_CONVERSION_INPUT,
        "preparar_formato_articulo": PREVIEW_ARTICLE_FORMAT_INPUT,
        "confirmar_cambio_articulo": CONFIRM_ARTICLE_CHANGE_INPUT,
        "preparar_creacion_evento": CREATE_EVENT_INPUT,
        "preparar_creacion_articulo": CREATE_ARTICLE_INPUT,
        "preparar_creacion_receta": CREATE_RECIPE_INPUT,
        "aplicar_creacion_catalogo": APPLY_CATALOG_INPUT,
        "conservar_propuesta_receta": CREATE_RECIPE_INPUT,
        "preparar_ubicacion_lote": PREVIEW_LOT_LOCATION_INPUT,
        "confirmar_ubicacion_lote": CONFIRM_LOT_LOCATION_INPUT,
    }

    def __init__(self, registry: HostAIToolRegistry, tool_ids: tuple[str, ...] | None = None) -> None:
        self.registry = registry
        self.tool_ids = tuple(tool_ids or self.TOOL_IDS)

    @classmethod
    def for_general_agent(cls, registry: HostAIToolRegistry) -> "HostAIToolCatalog":
        return cls(registry, cls.GENERAL_AGENT_TOOL_IDS)

    def effective_tools(self) -> list[dict[str, Any]]:
        output = []
        for tool_id in self.tool_ids:
            tool = self.registry.get(tool_id)
            if not tool or tool.estado != TOOL_STATUS_ACTIVADA or tool.tipo not in {"READ", "ANALYSIS", "UI_ACTION", "PREVIEW", "CONFIRM"}:
                continue
            output.append({
                "tool_id": tool.id,
                "description": tool.descripcion,
                "type": tool.tipo,
                "input_schema": deepcopy(self.SCHEMAS[tool.id]),
                "result_schema": {"type": "object", "additionalProperties": True},
                "max_results": 10,
                "confirmation_policy": "EXPLICIT_HUMAN" if tool.requiere_confirmacion else "NONE",
                "enabled": True,
                "version": tool.version,
            })
        return output


__all__ = ["HostAIToolCatalog"]
