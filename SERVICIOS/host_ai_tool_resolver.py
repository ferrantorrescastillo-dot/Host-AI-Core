from __future__ import annotations

from typing import Any

from SERVICIOS.host_ai_deterministic_intent_router import (
    INTENT_ABRIR_MODULO,
    INTENT_BUSCAR_RECETA,
    INTENT_LISTAR_ESCANDALLOS_DESACTUALIZADOS,
    INTENT_LISTAR_INCIDENCIAS,
    INTENT_LISTAR_RECETAS_PENDIENTES,
    INTENT_MOSTRAR_ESTADO_GENERAL,
    INTENT_CONSULTAR_ESTADO_STOCK,
    INTENT_BUSCAR_ARTICULOS,
    INTENT_CONSULTAR_COMPRAS_PENDIENTES,
    INTENT_CONSULTAR_PENDIENTE_RECEPCION,
    INTENT_CONSULTAR_PROPUESTAS_COMPRA,
    INTENT_CONSULTAR_NECESIDADES_COMPRA,
    INTENT_BUSCAR_PEDIDOS_PROVEEDOR,
    INTENT_CONSULTAR_PRODUCCION,
    INTENT_MOSTRAR_EVENTOS_PROXIMOS,
)


class HostAIToolResolver:
    INTENT_TO_TOOL = {
        INTENT_BUSCAR_RECETA: "buscar_recetas",
        INTENT_LISTAR_RECETAS_PENDIENTES: "listar_recetas_pendientes",
        INTENT_LISTAR_ESCANDALLOS_DESACTUALIZADOS: "listar_escandallos_desactualizados",
        INTENT_LISTAR_INCIDENCIAS: "listar_incidencias",
        INTENT_MOSTRAR_EVENTOS_PROXIMOS: "mostrar_eventos_proximos",
        INTENT_MOSTRAR_ESTADO_GENERAL: "mostrar_estado_general",
        INTENT_CONSULTAR_ESTADO_STOCK: "consultar_estado_stock",
        INTENT_BUSCAR_ARTICULOS: "buscar_articulos",
        INTENT_CONSULTAR_COMPRAS_PENDIENTES: "consultar_compras_pendientes",
        INTENT_CONSULTAR_PENDIENTE_RECEPCION: "consultar_pendiente_recepcion",
        INTENT_CONSULTAR_PROPUESTAS_COMPRA: "consultar_propuestas_compra",
        INTENT_CONSULTAR_NECESIDADES_COMPRA: "consultar_necesidades_compra",
        INTENT_BUSCAR_PEDIDOS_PROVEEDOR: "buscar_pedidos_por_proveedor",
        INTENT_CONSULTAR_PRODUCCION: "consultar_produccion",
    }

    SIDEBAR_TO_TOOL = {
        "2": "abrir_evento",
        "3": "abrir_produccion",
        "4": "abrir_compras",
        "5": "abrir_stock",
        "6": "abrir_receta",
        "7": "abrir_menus",
        "8": "abrir_catalogo",
        "9": "abrir_importaciones",
        "10": "abrir_incidencias",
        "11": "abrir_estadisticas",
        "12": "abrir_configuracion",
    }

    def resolve(self, intent: str, terms: dict[str, Any] | None = None, session_context: dict[str, Any] | None = None) -> str:
        if intent == INTENT_ABRIR_MODULO:
            sidebar = str((terms or {}).get("modulo_sidebar") or "")
            return str(self.SIDEBAR_TO_TOOL.get(sidebar) or "")
        return str(self.INTENT_TO_TOOL.get(str(intent or "")) or "")


__all__ = ["HostAIToolResolver"]
