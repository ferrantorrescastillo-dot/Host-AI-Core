from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


TOOL_STATUS_ACTIVADA = "ACTIVADA"
TOOL_STATUS_DESHABILITADA = "DESHABILITADA"


@dataclass
class HostAITool:
    id: str
    nombre: str
    descripcion: str
    categoria: str
    tipo: str
    modulo: str
    servicio: str
    operacion: str
    solo_lectura: bool
    requiere_confirmacion: bool
    requiere_contexto: bool
    contextos_compatibles: list[str] = field(default_factory=list)
    permisos: list[str] = field(default_factory=list)
    estado: str = TOOL_STATUS_ACTIVADA
    tags: list[str] = field(default_factory=list)
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HostAIToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, HostAITool] = {}

    def register(self, tool: HostAITool) -> None:
        self._tools[tool.id] = tool

    def get(self, tool_id: str) -> HostAITool | None:
        return self._tools.get(str(tool_id or ""))

    def list_all(self) -> list[HostAITool]:
        return list(self._tools.values())

    def list_by_type(self, tool_type: str) -> list[HostAITool]:
        return [t for t in self._tools.values() if str(t.tipo).upper() == str(tool_type).upper()]

    def stats(self) -> dict[str, Any]:
        tools = self.list_all()
        by_type: dict[str, int] = {}
        for t in tools:
            by_type[t.tipo] = int(by_type.get(t.tipo, 0) + 1)
        return {
            "total": len(tools),
            "activas": len([t for t in tools if t.estado == TOOL_STATUS_ACTIVADA]),
            "deshabilitadas": len([t for t in tools if t.estado == TOOL_STATUS_DESHABILITADA]),
            "por_tipo": by_type,
        }


def _tool(
    tool_id: str,
    nombre: str,
    descripcion: str,
    categoria: str,
    tipo: str,
    modulo: str,
    servicio: str,
    operacion: str,
    solo_lectura: bool = True,
    requiere_confirmacion: bool = False,
    requiere_contexto: bool = False,
    contextos_compatibles: list[str] | None = None,
    permisos: list[str] | None = None,
    estado: str = TOOL_STATUS_ACTIVADA,
    tags: list[str] | None = None,
) -> HostAITool:
    return HostAITool(
        id=tool_id,
        nombre=nombre,
        descripcion=descripcion,
        categoria=categoria,
        tipo=tipo,
        modulo=modulo,
        servicio=servicio,
        operacion=operacion,
        solo_lectura=solo_lectura,
        requiere_confirmacion=requiere_confirmacion,
        requiere_contexto=requiere_contexto,
        contextos_compatibles=list(contextos_compatibles or []),
        permisos=list(permisos or ["HOST_AI_BASIC"]),
        estado=estado,
        tags=list(tags or []),
        version="1.0",
    )


def build_default_tool_registry() -> HostAIToolRegistry:
    r = HostAIToolRegistry()

    # READ/NAVIGATION activas.
    active_tools = [
        _tool("buscar_recetas", "Buscar recetas", "Busca recetas por termino", "CONSULTA", "READ", "RECETAS_ESCANDALLOS", "HostAIHomeReadService", "buscar_recetas", tags=["recetas", "busqueda"]),
        _tool("abrir_receta", "Abrir receta", "Solicita navegacion a recetas", "NAVEGACION", "NAVIGATION", "RECETAS_ESCANDALLOS", "ShellNavigationAdapter", "open_recipe", requiere_contexto=True, contextos_compatibles=["RECETA", "HOME"], tags=["recetas", "navegacion"]),
        _tool("buscar_escandallos", "Buscar escandallos", "Lista escandallos disponibles/desactualizados", "CONSULTA", "READ", "RECETAS_ESCANDALLOS", "HostAIHomeReadService", "listar_escandallos", tags=["escandallos", "consulta"]),
        _tool("abrir_escandallo", "Abrir escandallo", "Solicita navegacion a escandallos", "NAVEGACION", "NAVIGATION", "RECETAS_ESCANDALLOS", "ShellNavigationAdapter", "open_escandallo", requiere_contexto=True, contextos_compatibles=["RECETA", "ESCANDALLO", "HOME"], tags=["escandallos", "navegacion"]),
        _tool("buscar_eventos", "Buscar eventos", "Busca eventos en la lectura de Home", "CONSULTA", "READ", "EVENTOS", "HostAIHomeReadService", "listar_eventos", tags=["eventos"]),
        _tool("abrir_evento", "Abrir evento", "Solicita navegacion a eventos", "NAVEGACION", "NAVIGATION", "EVENTOS", "ShellNavigationAdapter", "open_event", requiere_contexto=True, contextos_compatibles=["EVENTO", "HOME"], tags=["eventos", "navegacion"]),
        _tool("mostrar_eventos", "Mostrar eventos", "Muestra eventos disponibles", "CONSULTA", "READ", "EVENTOS", "HostAIHomeReadService", "mostrar_eventos", tags=["eventos", "lista"]),
        _tool("abrir_produccion", "Abrir produccion", "Navega a produccion", "NAVEGACION", "NAVIGATION", "PRODUCCION", "ShellNavigationAdapter", "open_produccion", tags=["produccion", "navegacion"]),
        _tool("abrir_compras", "Abrir compras", "Navega a compras", "NAVEGACION", "NAVIGATION", "COMPRAS", "ShellNavigationAdapter", "open_compras", tags=["compras", "navegacion"]),
        _tool("abrir_stock", "Abrir stock", "Navega a stock", "NAVEGACION", "NAVIGATION", "STOCK", "ShellNavigationAdapter", "open_stock", tags=["stock", "navegacion"]),
        _tool("abrir_menus", "Abrir menus", "Navega a menus", "NAVEGACION", "NAVIGATION", "MENUS", "ShellNavigationAdapter", "open_menus", tags=["menus", "navegacion"]),
        _tool("abrir_catalogo", "Abrir catalogo", "Navega a catalogo", "NAVEGACION", "NAVIGATION", "CATALOGO", "ShellNavigationAdapter", "open_catalogo", tags=["catalogo", "navegacion"]),
        _tool("abrir_importaciones", "Abrir importaciones", "Navega a importaciones", "NAVEGACION", "NAVIGATION", "IMPORTACIONES", "ShellNavigationAdapter", "open_importaciones", tags=["importaciones", "navegacion"]),
        _tool("abrir_incidencias", "Abrir incidencias", "Navega a incidencias", "NAVEGACION", "NAVIGATION", "INCIDENCIAS", "ShellNavigationAdapter", "open_incidencias", tags=["incidencias", "navegacion"]),
        _tool("abrir_estadisticas", "Abrir estadisticas", "Navega a estadisticas", "NAVEGACION", "NAVIGATION", "ESTADISTICAS", "ShellNavigationAdapter", "open_estadisticas", tags=["estadisticas", "navegacion"]),
        _tool("abrir_configuracion", "Abrir configuracion", "Navega a configuracion", "NAVEGACION", "NAVIGATION", "CONFIGURACION", "ShellNavigationAdapter", "open_configuracion", tags=["configuracion", "navegacion"]),
        _tool("mostrar_estado_general", "Mostrar estado general", "Resume estado de modulos", "ANALISIS", "ANALYSIS", "HOME", "HostAIHomeReadService", "resumen_estado", tags=["estado", "analisis"]),
        _tool("consultar_estado_stock", "Consultar estado de Stock", "Consulta resumen, alertas o existencias de un articulo", "CONSULTA", "READ", "STOCK", "HostAIHomeReadService", "consultar_estado_stock", tags=["stock", "consulta", "solo_lectura"]),
        _tool("buscar_articulos", "Buscar articulos", "Busca articulos en el catalogo canonico", "CONSULTA", "READ", "CATALOGO", "ArticulosCatalogReadService", "listar", tags=["articulos", "catalogo", "solo_lectura"]),
        _tool("consultar_compras_pendientes", "Consultar compras pendientes", "Consulta pedidos abiertos o por estado", "CONSULTA", "READ", "COMPRAS", "HostAIComprasReadService", "consultar_pedidos", tags=["compras", "pedidos", "solo_lectura"]),
        _tool("consultar_pendiente_recepcion", "Consultar pendiente de recepción", "Consulta cantidades pendientes de recibir", "CONSULTA", "READ", "COMPRAS", "HostAIComprasReadService", "consultar_pedidos", tags=["compras", "recepcion", "solo_lectura"]),
        _tool("consultar_propuestas_compra", "Consultar propuestas de compra", "Lista propuestas existentes", "CONSULTA", "READ", "COMPRAS", "HostAIComprasReadService", "consultar_propuestas", tags=["compras", "propuestas", "solo_lectura"]),
        _tool("consultar_necesidades_compra", "Consultar necesidades de compra", "Lista necesidades ya calculadas", "CONSULTA", "READ", "COMPRAS", "HostAIComprasReadService", "consultar_necesidades", tags=["compras", "necesidades", "solo_lectura"]),
        _tool("buscar_pedidos_por_proveedor", "Buscar pedidos por proveedor", "Consulta pedidos de un proveedor", "CONSULTA", "READ", "COMPRAS", "HostAIComprasReadService", "buscar_por_proveedor", tags=["compras", "proveedores", "solo_lectura"]),
        _tool("listar_recetas_pendientes", "Listar recetas pendientes", "Lista recetas pendientes", "CONSULTA", "READ", "RECETAS_ESCANDALLOS", "HostAIHomeReadService", "listar_recetas_pendientes", tags=["recetas", "pendientes"]),
        _tool("listar_escandallos_desactualizados", "Listar escandallos desactualizados", "Lista escandallos desactualizados", "CONSULTA", "READ", "RECETAS_ESCANDALLOS", "HostAIHomeReadService", "listar_escandallos_desactualizados", tags=["escandallos", "desactualizados"]),
        _tool("listar_incidencias", "Listar incidencias", "Lista incidencias abiertas", "CONSULTA", "READ", "INCIDENCIAS", "HostAIHomeReadService", "listar_incidencias", tags=["incidencias"]),
        _tool("mostrar_eventos_proximos", "Mostrar eventos proximos", "Lista eventos proximos", "CONSULTA", "READ", "EVENTOS", "HostAIHomeReadService", "mostrar_eventos_proximos", tags=["eventos", "proximos"]),
    ]
    for t in active_tools:
        r.register(t)

    # WRITE futuras deshabilitadas.
    disabled_writes = [
        _tool("crear_receta", "Crear receta", "Crea una receta nueva", "ESCRITURA", "WRITE", "RECETAS_ESCANDALLOS", "RecetasService", "crear", solo_lectura=False, requiere_confirmacion=True, estado=TOOL_STATUS_DESHABILITADA),
        _tool("duplicar_receta", "Duplicar receta", "Duplica receta existente", "ESCRITURA", "WRITE", "RECETAS_ESCANDALLOS", "RecetasService", "duplicar", solo_lectura=False, requiere_confirmacion=True, estado=TOOL_STATUS_DESHABILITADA),
        _tool("actualizar_precio", "Actualizar precio", "Actualiza precio de producto", "ESCRITURA", "WRITE", "CATALOGO", "CatalogoService", "actualizar_precio", solo_lectura=False, requiere_confirmacion=True, estado=TOOL_STATUS_DESHABILITADA),
        _tool("recalcular_escandallo", "Recalcular escandallo", "Recalcula escandallo", "ESCRITURA", "WRITE", "RECETAS_ESCANDALLOS", "EscandallosService", "recalcular", solo_lectura=False, requiere_confirmacion=True, estado=TOOL_STATUS_DESHABILITADA),
        _tool("crear_evento", "Crear evento", "Crea evento", "ESCRITURA", "WRITE", "EVENTOS", "EventosService", "crear", solo_lectura=False, requiere_confirmacion=True, estado=TOOL_STATUS_DESHABILITADA),
        _tool("aprobar_compra", "Aprobar compra", "Aprueba compra", "ESCRITURA", "WRITE", "COMPRAS", "ComprasService", "aprobar", solo_lectura=False, requiere_confirmacion=True, estado=TOOL_STATUS_DESHABILITADA),
        _tool("crear_menu", "Crear menu", "Crea menu", "ESCRITURA", "WRITE", "MENUS", "MenusService", "crear", solo_lectura=False, requiere_confirmacion=True, estado=TOOL_STATUS_DESHABILITADA),
        _tool("importar_documento", "Importar documento", "Importa documento", "IMPORTACION", "IMPORT", "IMPORTACIONES", "ImportacionService", "importar", solo_lectura=False, requiere_confirmacion=True, estado=TOOL_STATUS_DESHABILITADA),
    ]
    for t in disabled_writes:
        r.register(t)

    return r


__all__ = [
    "HostAITool",
    "HostAIToolRegistry",
    "TOOL_STATUS_ACTIVADA",
    "TOOL_STATUS_DESHABILITADA",
    "build_default_tool_registry",
]
