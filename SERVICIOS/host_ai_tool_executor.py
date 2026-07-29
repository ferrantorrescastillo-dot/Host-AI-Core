from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
import logging
import time

from SERVICIOS.host_ai_tool_registry import HostAIToolRegistry, TOOL_STATUS_ACTIVADA


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
    def __init__(self, registry: HostAIToolRegistry, home_read_service: Any | None = None):
        self.registry = registry
        self.home_read_service = home_read_service

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
        except Exception as exc:
            LOGGER.exception("tool_execute_error %s", {"tool_id": tool.id, "error": str(exc)})
            return self._finish(
                HostAIToolResult(
                    estado="ERROR",
                    mensaje="Error ejecutando la herramienta.",
                    errores=[str(exc)],
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

    def _tool_mostrar_estado_general(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        modelo = self._ensure_home()
        modulos = dict(modelo.get("modulos") or {})
        partes = []
        for clave in ["eventos", "recetas", "escandallos", "incidencias", "compras", "stock", "produccion", "menus"]:
            m = dict(modulos.get(clave) or {})
            partes.append(f"{clave}: {m.get('estado', 'desconocido')} ({int(m.get('total') or 0)})")
        return HostAIToolResult(estado="OK", mensaje="Estado general: " + " | ".join(partes), datos={"home": modelo})

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
