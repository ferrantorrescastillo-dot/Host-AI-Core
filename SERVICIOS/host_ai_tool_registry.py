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
        _tool("consultar_estado_stock", "Consultar estado de Stock", "Consulta Stock en solo lectura. Para varios artículos usa una sola llamada con terminos (máximo 10); para uno usa consulta=articulo y termino. El batch devuelve un resultado por término y faltantes explícitos; resumen y alertas son exclusivamente globales", "CONSULTA", "READ", "STOCK", "HostAIHomeReadService", "consultar_estado_stock", tags=["stock", "consulta", "batch", "solo_lectura"]),
        _tool("buscar_articulos", "Buscar articulos", "Busca articulos en el catalogo canonico. Para varios ingredientes usa una sola llamada con terminos (maximo 10); cada termino conserva de forma independiente OK, AMBIGUO o NO_ENCONTRADO", "CONSULTA", "READ", "CATALOGO", "ArticulosCatalogReadService", "listar", tags=["articulos", "catalogo", "batch", "solo_lectura"]),
        _tool("consultar_articulo_detalle", "Consultar detalle de artículo", "Consulta ficha técnica, unidades, formato, precio, proveedores, stock y lotes de un artículo canónico", "CONSULTA", "READ", "CATALOGO", "ArticulosCatalogReadService", "obtener", tags=["articulos", "detalle", "stock", "solo_lectura", "general_agent"]),
        _tool("consultar_compras_pendientes", "Consultar compras pendientes", "Consulta pedidos abiertos o por estado", "CONSULTA", "READ", "COMPRAS", "HostAIComprasReadService", "consultar_pedidos", tags=["compras", "pedidos", "solo_lectura"]),
        _tool("consultar_pendiente_recepcion", "Consultar pendiente de recepción", "Consulta cantidades pendientes de recibir", "CONSULTA", "READ", "COMPRAS", "HostAIComprasReadService", "consultar_pedidos", tags=["compras", "recepcion", "solo_lectura"]),
        _tool("consultar_propuestas_compra", "Consultar propuestas de compra", "Lista propuestas existentes", "CONSULTA", "READ", "COMPRAS", "HostAIComprasReadService", "consultar_propuestas", tags=["compras", "propuestas", "solo_lectura"]),
        _tool("consultar_necesidades_compra", "Consultar necesidades de compra", "Lista necesidades ya calculadas", "CONSULTA", "READ", "COMPRAS", "HostAIComprasReadService", "consultar_necesidades", tags=["compras", "necesidades", "solo_lectura"]),
        _tool("buscar_pedidos_por_proveedor", "Buscar pedidos por proveedor", "Consulta pedidos de un proveedor", "CONSULTA", "READ", "COMPRAS", "HostAIComprasReadService", "buscar_por_proveedor", tags=["compras", "proveedores", "solo_lectura"]),
        _tool("consultar_produccion", "Consultar produccion", "Consulta Producción en solo lectura, globalmente o dentro de un plan. Puede resolver el plan por plan_id, nombre o menú de origen; si hay un menú activo, usa su menu_id para consultar solo el plan asociado", "CONSULTA", "READ", "PRODUCCION", "HostAIProduccionReadService", "consultar", tags=["produccion", "consulta", "solo_lectura"]),
        _tool("consultar_eventos", "Consultar Eventos", "Consulta exclusivamente el modulo canonico Eventos en solo lectura. Lista los proximos eventos por fecha o busca un evento por nombre o ID. No consulta tareas ni planes de Produccion", "CONSULTA", "READ", "EVENTOS", "HostAIHomeReadService", "listar_eventos", tags=["eventos", "consulta", "solo_lectura", "general_agent"]),
        _tool("consultar_evento_detalle", "Consultar detalle de Evento", "Consulta un evento canónico por ID y expone sus servicios y pases registrados en solo lectura.", "CONSULTA", "READ", "EVENTOS", "MotorEventos", "obtener", tags=["eventos", "detalle", "solo_lectura", "general_agent"]),
        _tool("consultar_reservas", "Consultar/listar reservas", "Consulta, lista y filtra las reservas de clientes del restaurante en solo lectura. Usala para preguntas generales, listados, fechas relativas como hoy o manana, proximas reservas, estado, servicio o nombre; usa reserva_id solo para consultar una reserva concreta. No abre vistas, no consulta Eventos, Produccion ni stock reservado y no modifica datos", "CONSULTA", "READ", "RESERVAS", "ReservasReadService", "listar", tags=["reservas", "clientes", "consulta", "solo_lectura", "general_agent"]),
        _tool("consultar_escandallos", "Consultar escandallos", "Consulta escandallos, ingredientes solicitados y costes canónicos. Para auditar varias recetas ya identificadas usa escandallo_ids en una única llamada batch (máximo 50). La analítica cerrada incluye MAX/MIN, ranking, conteos, LIST_COSTE_INCOMPLETO y DETAIL_COSTE_INCOMPLETO. En una pregunta causal, el DETAIL económico gobierna la respuesta aunque exista contexto previo. SIN_ESCANDALLO solo acredita que no hay escandallo registrado: no autoriza diagnosticar ingredientes, precios, conversiones, vinculaciones ni pasos de reparación. No existe capability para preparar, crear o guardar un escandallo ni para ofrecer uno de ejemplo", "CONSULTA", "READ", "RECETAS_ESCANDALLOS", "HostAIEscandallosReadService", "consultar", tags=["escandallos", "costes", "agregacion", "ranking", "conteo", "coste_incompleto", "batch", "solo_lectura", "general_agent"]),
        _tool("consultar_uso_elaboracion", "Consultar uso de elaboración", "Consulta en qué menús, producción y elaboraciones padre se usa un escandallo canónico", "CONSULTA", "READ", "RECETAS_ESCANDALLOS", "HostAIUsoElaboracionReadService", "consultar", tags=["escandallos", "menus", "produccion", "solo_lectura", "general_agent"]),
        _tool("consultar_menu", "Consultar menú", "Consulta el detalle y la composición completa de un menú canónico", "CONSULTA", "READ", "MENUS", "HostAIMenusReadService", "consultar", tags=["menus", "elaboraciones", "solo_lectura", "general_agent"]),
        _tool("consultar_necesidades_operativas", "Consultar necesidades operativas", "Calcula para un menú canónico la necesidad, stock utilizable, compras confirmadas pendientes, necesidad neta, formatos, proveedor, precio e incidencias sin crear pedidos ni modificar datos", "CONSULTA", "READ", "MENUS", "HostAIOperationalNeedsReadService", "consultar_menu", tags=["menus", "stock", "compras", "necesidades", "solo_lectura", "general_agent"]),
        _tool("abrir_elaboracion", "Abrir elaboración", "Abre en la interfaz la ficha canónica de una elaboración ya identificada. La vista Receta abre la entidad culinaria aunque no tenga escandallo; la vista Escandallo solo puede abrirse cuando existe un escandallo registrado. SIN_ESCANDALLO no significa que la receta no exista. Úsala cuando el usuario pida explícitamente abrir, mostrar, enseñar o ver esa vista: ejecútala directamente, sin pedir una confirmación adicional. No consulta ni modifica datos", "NAVEGACION", "UI_ACTION", "RECETAS_ESCANDALLOS", "HostAIToolExecutor", "abrir_elaboracion", tags=["elaboraciones", "navegacion", "ui_action", "general_agent"]),
        _tool("abrir_articulo", "Abrir artículo", "Abre en la interfaz la ficha canónica de un artículo ya identificado; la ficha incluye su estado de Stock. Úsala cuando el usuario pida explícitamente abrir, mostrar, enseñar o ver el artículo o su stock: ejecútala directamente, sin pedir una confirmación adicional. No consulta ni modifica datos", "NAVEGACION", "UI_ACTION", "CATALOGO", "HostAIToolExecutor", "abrir_articulo", tags=["articulos", "stock", "navegacion", "ui_action", "general_agent"]),
        _tool("abrir_menu", "Abrir menú", "Abre en la interfaz el menú canónico ya identificado. Úsala cuando el usuario pida explícitamente abrir, mostrar, enseñar o ver el menú: ejecútala directamente, sin pedir una confirmación adicional. No consulta ni modifica datos", "NAVEGACION", "UI_ACTION", "MENUS", "HostAIToolExecutor", "abrir_menu", tags=["menus", "navegacion", "ui_action", "general_agent"]),
        _tool("abrir_produccion_ui", "Abrir plan de producción", "Abre en la interfaz el plan canónico ya identificado. Úsala cuando el usuario pida explícitamente abrir, mostrar, enseñar o ver la Producción: ejecútala directamente, sin pedir una confirmación adicional. No consulta ni modifica datos", "NAVEGACION", "UI_ACTION", "PRODUCCION", "HostAIToolExecutor", "abrir_produccion_ui", tags=["produccion", "navegacion", "ui_action", "general_agent"]),
        _tool("abrir_compra", "Abrir Compras", "Abre el listado real de Compras o un pedido canónico ya identificado. No crea, confirma ni modifica pedidos", "NAVEGACION", "UI_ACTION", "COMPRAS", "HostAIToolExecutor", "abrir_compra", tags=["compras", "pedidos", "navegacion", "ui_action", "general_agent"]),
        _tool("abrir_eventos", "Abrir Eventos", "Abre la vista real del modulo Eventos. Usala solo cuando el usuario pida explicitamente abrir, mostrar, ensenar o ver Eventos; no abre Produccion y no modifica datos", "NAVEGACION", "UI_ACTION", "EVENTOS", "HostAIToolExecutor", "abrir_eventos", tags=["eventos", "navegacion", "ui_action", "general_agent"]),
        _tool("abrir_reservas", "Abrir listado de reservas", "Abre el modulo o listado general de Reservas. Es la UI_ACTION correcta para mostrar las reservas en plural y no requiere ningun ID. No consulta ni modifica datos", "NAVEGACION", "UI_ACTION", "RESERVAS", "HostAIToolExecutor", "abrir_reservas", tags=["reservas", "listado", "navegacion", "ui_action", "general_agent"]),
        _tool("abrir_reserva", "Abrir detalle de una reserva concreta", "Abre exclusivamente el detalle de una reserva concreta cuya identidad ya esta resuelta. Requiere siempre reserva_id canonico con formato RES-[A-F0-9]{12}; nunca debe usarse para abrir el listado general ni sin ID. No consulta ni modifica datos", "NAVEGACION", "UI_ACTION", "RESERVAS", "HostAIToolExecutor", "abrir_reserva", tags=["reserva_concreta", "detalle", "navegacion", "ui_action", "general_agent"]),
        _tool("crear_reserva", "Preparar nueva reserva", "Prepara una vista previa para crear una reserva; nunca persiste por si sola. Requiere cliente, fecha ISO, hora HH:MM y pax. Servicio es opcional: si falta, Reservas lo deriva de forma centralizada de la hora. Estado es opcional y por defecto PENDIENTE. Debe pedir confirmacion humana despues del preview", "PREPARACION", "PREVIEW", "RESERVAS", "ReservasWriteService", "preview_crear", solo_lectura=False, requiere_confirmacion=True, tags=["reservas", "write_preview", "general_agent"]),
        _tool("modificar_reserva", "Preparar modificacion de reserva", "Prepara una vista previa de cambios editables solo si la reserva esta PENDIENTE o CONFIRMADA; CANCELADA, NO_SHOW y COMPLETADA son terminales de solo lectura. No escribe hasta una confirmacion humana posterior", "PREPARACION", "PREVIEW", "RESERVAS", "ReservasWriteService", "preview_modificar", solo_lectura=False, requiere_confirmacion=True, tags=["reservas", "write_preview", "general_agent"]),
        _tool("confirmar_reserva", "Preparar confirmacion de estado", "Prepara la transicion PENDIENTE a CONFIRMADA; no escribe hasta una confirmacion humana posterior", "PREPARACION", "PREVIEW", "RESERVAS", "ReservasWriteService", "preview_confirmar", solo_lectura=False, requiere_confirmacion=True, tags=["reservas", "write_preview", "general_agent"]),
        _tool("cancelar_reserva", "Preparar cancelacion de reserva", "Prepara la cancelacion logica de una reserva concreta; no borra ni escribe hasta confirmacion humana posterior", "PREPARACION", "PREVIEW", "RESERVAS", "ReservasWriteService", "preview_cancelar", solo_lectura=False, requiere_confirmacion=True, tags=["reservas", "write_preview", "general_agent"]),
        _tool("marcar_no_show", "Preparar no-show", "Prepara marcar NO_SHOW una reserva confirmada; no escribe hasta confirmacion humana posterior", "PREPARACION", "PREVIEW", "RESERVAS", "ReservasWriteService", "preview_no_show", solo_lectura=False, requiere_confirmacion=True, tags=["reservas", "write_preview", "general_agent"]),
        _tool("completar_reserva", "Preparar reserva completada", "Prepara exclusivamente la transicion CONFIRMADA a COMPLETADA; no escribe hasta confirmacion humana posterior", "PREPARACION", "PREVIEW", "RESERVAS", "ReservasWriteService", "preview_completar", solo_lectura=False, requiere_confirmacion=True, tags=["reservas", "write_preview", "general_agent"]),
        _tool("aplicar_operacion_reserva", "Aplicar operacion de reserva confirmada", "Aplica exclusivamente el preview pendiente de esta sesion cuando el mensaje actual contiene confirmacion humana explicita. Requiere el token opaco exacto y no prepara operaciones nuevas", "CONFIRMACION", "CONFIRM", "RESERVAS", "ReservasWriteService", "confirm", solo_lectura=False, requiere_confirmacion=True, tags=["reservas", "confirmacion", "general_agent"]),
        _tool("preparar_precio_articulo", "Preparar precio de artículo", "Prepara el cambio parcial del precio canónico de un artículo ya identificado. Exige un importe explícito del usuario y nunca escribe por sí sola", "PREPARACION", "PREVIEW", "CATALOGO", "ConfirmacionFormatoArticuloService", "preview_change", solo_lectura=False, requiere_confirmacion=True, tags=["articulos", "precio", "write_preview", "general_agent"]),
        _tool("preparar_conversion_articulo", "Preparar conversión de artículo", "Prepara una relación explícita entre dos unidades conocidas de un artículo. No infiere factores y nunca escribe por sí sola", "PREPARACION", "PREVIEW", "CATALOGO", "ConfirmacionFormatoArticuloService", "preview_change", solo_lectura=False, requiere_confirmacion=True, tags=["articulos", "conversion", "write_preview", "general_agent"]),
        _tool("preparar_formato_articulo", "Preparar formato de compra", "Prepara unidades por envase manteniendo separado el precio del paquete y su coste unitario derivado. No representa una conversión física ni escribe por sí sola", "PREPARACION", "PREVIEW", "CATALOGO", "ConfirmacionFormatoArticuloService", "preview_change", solo_lectura=False, requiere_confirmacion=True, tags=["articulos", "formato", "envase", "write_preview", "general_agent"]),
        _tool("confirmar_cambio_articulo", "Aplicar cambio de artículo confirmado", "Aplica exclusivamente el preview de artículo pendiente de esta sesión después de confirmación humana explícita; no prepara cambios nuevos", "CONFIRMACION", "CONFIRM", "CATALOGO", "ConfirmacionFormatoArticuloService", "confirm_change", solo_lectura=False, requiere_confirmacion=True, tags=["articulos", "confirmacion", "general_agent"]),
        _tool("preparar_creacion_evento", "Preparar creación de evento", "Valida y prepara un evento nuevo sin escribir. Requiere nombre, fecha y pax; la escritura solo puede ocurrir en una confirmación posterior", "PREPARACION", "PREVIEW", "EVENTOS", "CatalogCrudWriteService", "preview", solo_lectura=False, requiere_confirmacion=True, tags=["eventos", "create", "write_preview", "general_agent"]),
        _tool("preparar_creacion_articulo", "Preparar creación de artículo", "Valida duplicados y prepara un artículo nuevo sin crear stock ni escribir. La escritura exige confirmación posterior", "PREPARACION", "PREVIEW", "CATALOGO", "CatalogCrudWriteService", "preview", solo_lectura=False, requiere_confirmacion=True, tags=["articulos", "create", "write_preview", "general_agent"]),
        _tool("preparar_creacion_receta", "Preparar creación de receta", "Prepara exclusivamente la propuesta culinaria estructurada existente, conservando ingredientes, cantidades y relaciones; nunca inventa ni escribe", "PREPARACION", "PREVIEW", "RECETAS_ESCANDALLOS", "CatalogCrudWriteService", "preview", solo_lectura=False, requiere_confirmacion=True, tags=["recetas", "create", "write_preview", "general_agent"]),
        _tool("aplicar_creacion_catalogo", "Aplicar creación confirmada", "Aplica exclusivamente el token pendiente de esta sesión tras confirmación humana explícita; no acepta payload ni reconstruye datos", "CONFIRMACION", "CONFIRM", "CATALOGO", "CatalogCrudWriteService", "confirm", solo_lectura=False, requiere_confirmacion=True, tags=["eventos", "articulos", "recetas", "confirmacion", "general_agent"]),
        _tool("preparar_ubicacion_lote", "Preparar cambio de ubicación de lote", "Prepara exclusivamente el cambio de un lote canónico a una ubicación canónica existente; nunca modifica cantidad ni escribe", "PREPARACION", "PREVIEW", "STOCK", "StockLoteWriteService", "preview_location", solo_lectura=False, requiere_confirmacion=True, tags=["stock", "lotes", "write_preview", "general_agent"]),
        _tool("confirmar_ubicacion_lote", "Confirmar ubicación de lote", "Aplica exclusivamente el preview pendiente validado mediante token opaco y confirmación humana explícita", "CONFIRMACION", "CONFIRM", "STOCK", "StockLoteWriteService", "confirm_location", solo_lectura=False, requiere_confirmacion=True, tags=["stock", "lotes", "confirmacion", "general_agent"]),
        _tool("conservar_propuesta_receta", "Conservar propuesta de receta", "Conserva en la sesión la propuesta culinaria estructurada que acabas de redactar. Es memoria temporal, no registra ni modifica una receta y no requiere confirmación. Úsala al proponer una receta para que una petición posterior de guardarla reutilice exactamente ingredientes y cantidades", "ANALISIS", "ANALYSIS", "RECETAS_ESCANDALLOS", "HostAIToolExecutor", "conservar_propuesta_receta", tags=["recetas", "propuesta", "no_write", "general_agent"]),
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
