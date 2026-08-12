from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
import logging
import time

from SERVICIOS.host_ai_tool_registry import HostAIToolRegistry, TOOL_STATUS_ACTIVADA
from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.host_ai_compras_read_service import HostAIComprasReadService


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
    def __init__(self, registry: HostAIToolRegistry, home_read_service: Any | None = None, articulos_read_service: Any | None = None, compras_read_service: Any | None = None):
        self.registry = registry
        self.home_read_service = home_read_service
        self.articulos_read_service = articulos_read_service or self._build_articulos_read_service()
        core = getattr(home_read_service, "core", None)
        self.compras_read_service = compras_read_service or (HostAIComprasReadService(core) if core is not None else None)

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

    def _tool_mostrar_estado_general(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        modelo = self._ensure_home()
        modulos = dict(modelo.get("modulos") or {})
        partes = []
        for clave in ["eventos", "recetas", "escandallos", "incidencias", "compras", "stock", "produccion", "menus"]:
            m = dict(modulos.get(clave) or {})
            partes.append(f"{clave}: {m.get('estado', 'desconocido')} ({int(m.get('total') or 0)})")
        return HostAIToolResult(estado="OK", mensaje="Estado general: " + " | ".join(partes), datos={"home": modelo})

    def _tool_consultar_estado_stock(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        consulta = str(params.get("consulta") or "resumen").strip().lower()
        termino = str(params.get("termino") or "").strip()
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

        return HostAIToolResult(
            estado="OK",
            mensaje=mensaje,
            datos={
                "estado": estado_dto,
                "consulta": consulta,
                "termino": termino,
                "resumen": resumen,
                "existencias": existencias[:10],
                "alertas": alertas[:10],
                "fuente": "stock_canonico",
                "solo_lectura": True,
                "datos_reales_modificados": False,
            },
        )

    def _tool_buscar_articulos(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
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

    def _compras_result(self, data: dict[str, Any]) -> HostAIToolResult:
        state = str(data.get("estado") or "VACIO")
        if state == "AMBIGUO":
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
        return self._compras_result(self._compras_service().consultar_pedidos(estado=str(params.get("estado") or ""), solo_abiertos=not bool(params.get("estado"))))

    def _tool_consultar_pendiente_recepcion(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        return self._compras_result(self._compras_service().consultar_pedidos(pendientes_recepcion=True))

    def _tool_consultar_propuestas_compra(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        return self._compras_result(self._compras_service().consultar_propuestas())

    def _tool_consultar_necesidades_compra(self, _params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        return self._compras_result(self._compras_service().consultar_necesidades())

    def _tool_buscar_pedidos_por_proveedor(self, params: dict[str, Any], _ctx: dict[str, Any]) -> HostAIToolResult:
        return self._compras_result(self._compras_service().buscar_por_proveedor(str(params.get("proveedor") or "")))

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
