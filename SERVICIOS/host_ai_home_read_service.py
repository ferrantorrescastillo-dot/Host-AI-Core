from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Any
import logging

from SERVICIOS.biblioteca_escandallos_601 import RepositorioBibliotecaEscandallos601
from SERVICIOS.biblioteca_menus_601 import BibliotecaMenus601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.centro_importacion_601 import RepositorioCentroImportacion601


LOGGER = logging.getLogger("host_ai.app.home")

SEVERIDAD_INFO = "informacion"
SEVERIDAD_ATENCION = "atencion"
SEVERIDAD_IMPORTANTE = "importante"
SEVERIDAD_CRITICA = "critica"

ESTADO_CARGANDO = "cargando"
ESTADO_SIN_DATOS = "sin_datos"
ESTADO_DATOS = "datos_disponibles"
ESTADO_SERVICIO_NO_DISPONIBLE = "servicio_no_disponible"
ESTADO_ERROR_PARCIAL = "error_parcial"
ESTADO_ERROR_GENERAL = "error_general"


@dataclass
class HomeCard:
    tipo: str
    titulo: str
    resumen: str
    severidad: str
    cantidad: int
    modulo_origen: str
    accion_navegacion: str
    contexto_id: str = ""
    vigencia: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo": self.tipo,
            "titulo": self.titulo,
            "resumen": self.resumen,
            "severidad": self.severidad,
            "cantidad": self.cantidad,
            "modulo_origen": self.modulo_origen,
            "accion_navegacion": self.accion_navegacion,
            "contexto_id": self.contexto_id,
            "vigencia": self.vigencia,
        }


class HostAIHomeReadService:
    """Agregador de lectura para Host AI Home (APP-01.5).

    Consulta servicios existentes de dominio y normaliza resultados para la UI.
    No persiste, no recalcula y no ejecuta acciones de escritura.
    """

    def __init__(self, core: Any):
        self.core = core
        self.base_dir = getattr(core, "base_dir", None)
        self.repo_recetas = RepositorioBibliotecaRecetas601(self.base_dir)
        self.repo_escandallos = RepositorioBibliotecaEscandallos601(self.base_dir)
        self.repo_importacion = RepositorioCentroImportacion601(self.base_dir)
        self.servicio_menus = BibliotecaMenus601(self.base_dir)

    def cargar_home(self) -> dict[str, Any]:
        inicio = datetime.now()
        payload: dict[str, Any] = {
            "estado_global": ESTADO_CARGANDO,
            "modulos": {},
            "indicadores": [],
            "bandeja": [],
            "errores": [],
            "generado_en": datetime.now().isoformat(timespec="seconds"),
        }

        consultas = [
            ("eventos", self._leer_eventos_proximos),
            ("recetas", self._leer_recetas_pendientes),
            ("escandallos", self._leer_escandallos_desactualizados),
            ("incidencias", self._leer_incidencias_abiertas),
            ("compras", self._leer_compras_abiertas),
            ("stock", self._leer_alertas_stock),
            ("produccion", self._leer_produccion_pendiente),
            ("menus", self._leer_menus_desactualizados),
        ]

        for nombre, fn in consultas:
            payload["modulos"][nombre] = {"estado": ESTADO_CARGANDO, "total": 0, "items": []}
            try:
                data = fn()
                payload["modulos"][nombre] = data
            except AttributeError:
                payload["modulos"][nombre] = {
                    "estado": ESTADO_SERVICIO_NO_DISPONIBLE,
                    "total": 0,
                    "items": [],
                    "mensaje": "Servicio no disponible en este entorno.",
                }
            except Exception as exc:
                payload["modulos"][nombre] = {
                    "estado": ESTADO_ERROR_PARCIAL,
                    "total": 0,
                    "items": [],
                    "mensaje": "Error de lectura del modulo.",
                }
                payload["errores"].append({"modulo": nombre, "error": str(exc)})

        payload["indicadores"] = self._build_indicadores(payload["modulos"])
        payload["bandeja"] = self._build_bandeja(payload["modulos"])
        payload["estado_global"] = self._estado_global(payload["modulos"], payload["errores"])

        duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)
        LOGGER.info(
            "home_read %s",
            {
                "estado": payload["estado_global"],
                "duracion_ms": duracion_ms,
                "modulos": {k: v.get("estado") for k, v in payload["modulos"].items()},
                "errores": len(payload["errores"]),
            },
        )
        return payload

    def buscar_recetas(self, termino: str, limite: int = 10) -> list[dict[str, Any]]:
        t = str(termino or "").strip()
        if not t:
            return []
        por_nombre = self.repo_recetas.buscar(nombre=t, incluir_archivadas=False)
        por_ingrediente = self.repo_recetas.buscar(ingrediente=t, incluir_archivadas=False)
        por_familia = self.repo_recetas.buscar(familia=t, incluir_archivadas=False)
        resultados = []
        vistos: set[str] = set()
        for rec in (por_nombre + por_ingrediente + por_familia):
            clave = str(rec.get("id") or rec.get("codigo") or "")
            if clave and clave not in vistos:
                vistos.add(clave)
                resultados.append(rec)
        out: list[dict[str, Any]] = []
        for r in resultados[: max(1, limite)]:
            out.append(
                {
                    "id": str(r.get("id") or ""),
                    "codigo": str(r.get("codigo") or ""),
                    "nombre": str(r.get("nombre") or ""),
                    "familia": str(r.get("familia") or ""),
                    "estado": str(r.get("estado") or ""),
                }
            )
        return out

    def _leer_eventos_proximos(self) -> dict[str, Any]:
        eventos_raw = list(getattr(self.core.eventos, "listar_eventos")() or [])
        hoy = date.today()
        items: list[dict[str, Any]] = []
        for e in eventos_raw:
            evt = self._to_dict(e)
            fecha_txt = str(evt.get("fecha") or "")
            dias = self._dias_hasta(fecha_txt, hoy)
            if dias is not None and dias < 0:
                continue
            resumen = dict(
                getattr(self.core.eventos, "resumen_ejecutivo")(
                    str(evt.get("id") or "")
                )
                or {}
            )
            avisos = [str(aviso) for aviso in list(resumen.get("avisos") or [])]
            items.append(
                {
                    "id": str(evt.get("id") or ""),
                    "nombre": str(evt.get("nombre") or ""),
                    "fecha": fecha_txt,
                    "pax": int(evt.get("pax") or 0),
                    "estado": str(evt.get("estado") or ""),
                    "dias": dias if dias is not None else 999,
                    "servicios": len(list(evt.get("servicios") or [])),
                    "avisos": avisos,
                    "riesgos": avisos,
                    "estado_operativo": str(
                        resumen.get("estado_operativo") or ""
                    ),
                }
            )
        items.sort(key=lambda x: (x.get("dias", 999), x.get("fecha", ""), x.get("nombre", "")))
        modulo = self._pack_items(items)
        modulo.update(
            {
                "eventos_activos": len(items),
                "total_servicios": sum(
                    int(item.get("servicios") or 0) for item in items
                ),
                "total_avisos": sum(
                    len(list(item.get("avisos") or [])) for item in items
                ),
                "resumen": {
                    "eventos_activos": len(items),
                    "pax_total": sum(int(item.get("pax") or 0) for item in items),
                    "servicios": sum(
                        int(item.get("servicios") or 0) for item in items
                    ),
                    "avisos": sum(
                        len(list(item.get("avisos") or [])) for item in items
                    ),
                },
            }
        )
        return modulo

    def _leer_recetas_pendientes(self) -> dict[str, Any]:
        items = [
            {
                "id": str(r.get("id") or ""),
                "codigo": str(r.get("codigo") or ""),
                "nombre": str(r.get("nombre") or ""),
                "familia": str(r.get("familia") or ""),
                "estado": str(r.get("estado") or ""),
            }
            for r in self.repo_recetas.pendientes()
        ]
        return self._pack_items(items)

    def _leer_escandallos_desactualizados(self) -> dict[str, Any]:
        todos = self.repo_escandallos.listar(incluir_archivados=False)
        items = [
            {
                "id": str(e.get("id") or ""),
                "codigo": str(e.get("codigo") or ""),
                "nombre": str(e.get("nombre") or ""),
                "estado": str(e.get("estado") or ""),
            }
            for e in todos
            if str(e.get("estado") or "").upper() == "DESACTUALIZADO"
        ]
        return self._pack_items(items)

    def _leer_incidencias_abiertas(self) -> dict[str, Any]:
        data = self.repo_importacion.incidencias_pendientes()
        items = [
            {
                "id": str(i.get("id") or ""),
                "tipo": str(i.get("tipo") or ""),
                "detalle": str(i.get("detalle") or ""),
                "fecha": str(i.get("fecha") or ""),
                "estado": str(i.get("estado") or ""),
            }
            for i in data
        ]
        return self._pack_items(items)

    def _leer_compras_abiertas(self) -> dict[str, Any]:
        compras = self.core.compras
        necesidades = list(getattr(compras, "listar_necesidades")(solo_pendientes=True) or [])
        propuestas = list(getattr(compras, "listar_propuestas_compra")(solo_pendientes=True) or [])
        proveedores = list(getattr(compras, "listar_proveedores")(incluir_inactivos=False) or [])
        historial = list(getattr(compras, "listar_historial_compras")() or [])
        listar_pedidos = getattr(compras, "listar_pedidos", None)
        pedidos = (
            list(listar_pedidos() or [])
            if callable(listar_pedidos)
            else []
        )
        items = [
            {
                "id": str(n.get("id") or ""),
                "nombre": str(n.get("nombre") or ""),
                "prioridad": int(n.get("prioridad") or 0),
                "estado": str(n.get("estado") or ""),
                "fecha_necesaria": str(n.get("fecha_necesaria") or ""),
            }
            for n in necesidades
        ]
        modulo = self._pack_items(items)
        if propuestas or proveedores or historial:
            modulo["estado"] = ESTADO_DATOS
        modulo.update(
            {
                "necesidades_pendientes": len(necesidades),
                "propuestas_pendientes": len(propuestas),
                "propuestas": [
                    {
                        "id": str(p.get("id") or ""),
                        "producto": str(p.get("producto") or ""),
                        "comprar": float(p.get("comprar") or 0),
                        "unidad": str(p.get("unidad") or ""),
                        "prioridad": str(p.get("prioridad") or ""),
                        "proveedor_sugerido": str(p.get("proveedor_sugerido") or ""),
                        "estado": str(p.get("estado") or ""),
                        "creado_en": str(p.get("creado_en") or ""),
                    }
                    for p in propuestas
                ],
                "proveedores": [
                    {
                        "id": str(p.get("id") or ""),
                        "nombre": str(p.get("nombre") or ""),
                        "estado": str(p.get("estado") or ""),
                        "telefono": str(p.get("telefono") or ""),
                        "email": str(p.get("email") or ""),
                    }
                    for p in proveedores
                ],
                "historial": [
                    {
                        "id": str(c.get("id") or ""),
                        "producto": str(c.get("producto") or ""),
                        "cantidad": float(c.get("cantidad") or 0),
                        "unidad": str(c.get("unidad") or ""),
                        "proveedor": str(c.get("proveedor") or ""),
                        "estado": str(c.get("estado") or ""),
                        "creado_en": str(c.get("creado_en") or ""),
                    }
                    for c in historial
                ],
                "total_propuestas": len(propuestas),
                "total_proveedores": len(proveedores),
                "total_historial": len(historial),
                "pedidos": pedidos,
                "total_pedidos": len(pedidos),
            }
        )
        return modulo

    def _leer_alertas_stock(self) -> dict[str, Any]:
        motor = self.core.stock
        actual = dict(getattr(motor, "stock_actual")() or {})
        lotes = list(getattr(motor, "lotes_listado")() or [])
        movimientos = list(getattr(motor, "movimientos_listado")() or [])
        diag = dict(getattr(motor, "diagnosticar_stock")() or {})
        resumen_motor = dict(getattr(motor, "resumen_operativo")() or {})
        avisos = list(diag.get("avisos") or [])
        items = [
            {
                "tipo": str(a.get("tipo") or ""),
                "nivel": str(a.get("nivel") or ""),
                "mensaje": str(a.get("mensaje") or ""),
            }
            for a in avisos
        ]
        modulo = self._pack_items(items)
        modulo.update(
            {
                "existencias": list(actual.get("items") or []),
                "total_existencias": int(actual.get("total_items") or 0),
                "lotes": lotes,
                "total_lotes": int(actual.get("total_lotes") or len(lotes)),
                "movimientos": movimientos,
                "total_movimientos": len(movimientos),
                "alertas": items,
                "total_alertas": len(items),
                "estado_operativo": str(diag.get("estado") or ""),
                "caducidades": [
                    item
                    for item in items
                    if item["tipo"]
                    in {"caducado", "caducidad_cercana", "caducidad_invalida"}
                ],
                "total_caducidades": sum(
                    1
                    for item in items
                    if item["tipo"]
                    in {"caducado", "caducidad_cercana", "caducidad_invalida"}
                ),
                "resumen": {
                    "articulos": int(resumen_motor.get("total_articulos") or 0),
                    "lotes": int(resumen_motor.get("total_lotes") or 0),
                    "movimientos": len(movimientos),
                    "alertas": int(resumen_motor.get("total_avisos") or 0),
                    "bajo_minimo": int(
                        resumen_motor.get("articulos_bajo_minimo") or 0
                    ),
                    "caducados": int(resumen_motor.get("lotes_caducados") or 0),
                    "caducan_pronto": int(
                        resumen_motor.get("lotes_caducan_pronto") or 0
                    ),
                    "valor_total": float(resumen_motor.get("valor_total") or 0),
                },
            }
        )
        return modulo

    def _leer_produccion_pendiente(self) -> dict[str, Any]:
        motor = self.core.produccion_real
        planes = list(getattr(motor, "listar_planes")() or [])
        items: list[dict[str, Any]] = []
        for p in planes:
            plan_id = str(p.get("id") or "")
            if not plan_id:
                continue
            resumen = dict(getattr(motor, "resumen_ejecucion")(plan_id) or {})
            tareas = list(resumen.get("tareas") or [])
            estados = dict(resumen.get("estados") or {})
            pendientes = list(resumen.get("tareas_pendientes") or [])
            if not pendientes:
                continue
            items.append(
                {
                    "id": plan_id,
                    "nombre": str(p.get("nombre") or resumen.get("plan") or ""),
                    "evento_id": str(p.get("evento_id") or ""),
                    "evento": str(p.get("evento") or ""),
                    "fecha": str(p.get("fecha") or ""),
                    "responsable": str(p.get("responsable") or ""),
                    "estado": str(p.get("estado") or resumen.get("estado_plan") or ""),
                    "pax": int(p.get("pax") or 0),
                    "duracion_total_min": float(p.get("duracion_total_min") or 0),
                    "total_tareas": int(resumen.get("total_tareas") or len(tareas)),
                    "pendientes": int(estados.get("pendiente") or 0)
                    + int(estados.get("lista") or 0),
                    "en_curso": int(estados.get("en_curso") or 0),
                    "bloqueadas": int(estados.get("bloqueada") or 0),
                    "pausadas": int(estados.get("pausada") or 0),
                    "finalizadas": int(estados.get("finalizada") or 0),
                    "porcentaje_completado": float(resumen.get("porcentaje_completado") or 0),
                    "avisos": list(p.get("avisos") or []),
                    "alertas": list(resumen.get("alertas") or []),
                    "tareas": [
                        {
                            "id": str(t.get("id") or ""),
                            "titulo": str(t.get("titulo") or ""),
                            "estado": str(t.get("estado_ejecucion") or ""),
                            "prioridad": str(t.get("prioridad") or ""),
                            "cantidad": float(t.get("cantidad") or 0),
                            "unidad": str(t.get("unidad") or ""),
                            "responsable": str(t.get("responsable") or ""),
                            "bloqueo": str(t.get("bloqueo") or ""),
                            "retraso_min": int(t.get("retraso_min") or 0),
                            "progreso": float(t.get("porcentaje_avance") or 0),
                            "duracion_total_min": float(t.get("duracion_total_min") or 0),
                            "incidencias": list(t.get("incidencias") or []),
                        }
                        for t in tareas
                    ],
                }
            )
        modulo = self._pack_items(items)
        modulo.update(
            {
                "planes_activos": len(items),
                "total_tareas": sum(int(item["total_tareas"]) for item in items),
                "tareas_pendientes": sum(int(item["pendientes"]) for item in items),
                "tareas_en_curso": sum(int(item["en_curso"]) for item in items),
                "tareas_bloqueadas": sum(int(item["bloqueadas"]) for item in items),
                "tareas_pausadas": sum(int(item["pausadas"]) for item in items),
                "total_alertas": sum(
                    len(item["avisos"]) + len(item["alertas"]) for item in items
                ),
            }
        )
        modulo["resumen"] = {
            "planes_activos": modulo["planes_activos"],
            "tareas": modulo["total_tareas"],
            "pendientes": modulo["tareas_pendientes"],
            "en_curso": modulo["tareas_en_curso"],
            "bloqueadas": modulo["tareas_bloqueadas"],
            "pausadas": modulo["tareas_pausadas"],
            "alertas": modulo["total_alertas"],
        }
        return modulo

    def _leer_menus_desactualizados(self) -> dict[str, Any]:
        res = self.servicio_menus.ver_todos()
        menus = list(res.get("menus") or [])
        items = [
            {
                "id": str(m.get("menu_id") or ""),
                "codigo": str(m.get("codigo") or ""),
                "nombre": str(m.get("nombre") or ""),
                "estado": str(m.get("estado") or ""),
                "estado_publicacion": str(
                    m.get("estado_publicacion")
                    or (
                        "ARCHIVADO"
                        if str(m.get("estado") or "") == "ARCHIVADO"
                        else "BORRADOR"
                        if str(m.get("estado") or "") == "BORRADOR"
                        else "ACTIVO"
                    )
                ),
                "version": int(m.get("version_menu") or 1),
                "comensales": float(m.get("comensales_recomendado") or 0),
                "coste_total": float(m.get("coste_total") or 0),
                "coste_por_comensal": float(m.get("coste_por_comensal") or 0),
                "incidencias": list(m.get("incidencias") or []),
            }
            for m in menus
        ]
        modulo = self._pack_items(items)
        modulo["resumen"] = {
            "borradores": sum(item["estado_publicacion"] == "BORRADOR" for item in items),
            "activos": sum(item["estado_publicacion"] == "ACTIVO" for item in items),
            "archivados": sum(item["estado_publicacion"] == "ARCHIVADO" for item in items),
            "con_incidencias": sum(bool(item["incidencias"]) for item in items),
        }
        return modulo

    def _build_indicadores(self, modulos: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        mapa = [
            ("eventos", "Eventos proximos", "2"),
            ("recetas", "Recetas pendientes", "6"),
            ("escandallos", "Escandallos desactualizados", "6"),
            ("incidencias", "Incidencias abiertas", "10"),
            ("compras", "Compras abiertas", "4"),
            ("stock", "Alertas de stock", "5"),
            ("produccion", "Produccion pendiente", "3"),
            ("menus", "Menus desactualizados", "7"),
        ]
        for clave, titulo, nav in mapa:
            modulo = dict(modulos.get(clave) or {})
            out.append(
                {
                    "id": clave,
                    "titulo": titulo,
                    "estado": modulo.get("estado", ESTADO_SERVICIO_NO_DISPONIBLE),
                    "cantidad": int(modulo.get("total") or 0),
                    "accion_navegacion": nav,
                }
            )
        return out

    def _build_bandeja(self, modulos: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        cards: list[HomeCard] = []

        recetas = int((modulos.get("recetas") or {}).get("total") or 0)
        if recetas > 0:
            recetas_txt = self._plural(recetas, "receta", "recetas")
            cards.append(
                HomeCard(
                    tipo="RECETAS_PENDIENTES",
                    titulo=f"Hay {recetas} {recetas_txt} pendientes de completar.",
                    resumen="Conviene completar datos tecnicos antes de cierre operativo.",
                    severidad=SEVERIDAD_ATENCION,
                    cantidad=recetas,
                    modulo_origen="recetas",
                    accion_navegacion="6",
                )
            )

        esc = int((modulos.get("escandallos") or {}).get("total") or 0)
        if esc > 0:
            esc_txt = self._plural(esc, "escandallo", "escandallos")
            cards.append(
                HomeCard(
                    tipo="ESCANDALLOS_DESACTUALIZADOS",
                    titulo=f"Existen {esc} {esc_txt} desactualizados.",
                    resumen="Revisar costes antes de nuevas decisiones de menu.",
                    severidad=SEVERIDAD_IMPORTANTE,
                    cantidad=esc,
                    modulo_origen="escandallos",
                    accion_navegacion="6",
                )
            )

        inc = int((modulos.get("incidencias") or {}).get("total") or 0)
        if inc > 0:
            inc_txt = self._plural(inc, "incidencia", "incidencias")
            abierta_txt = self._plural(inc, "abierta", "abiertas")
            cards.append(
                HomeCard(
                    tipo="INCIDENCIAS_ABIERTAS",
                    titulo=f"Hay {inc} {inc_txt} {abierta_txt}.",
                    resumen="Pendientes de resolucion en importacion/catalogo.",
                    severidad=SEVERIDAD_IMPORTANTE,
                    cantidad=inc,
                    modulo_origen="incidencias",
                    accion_navegacion="10",
                )
            )

        eventos = list((modulos.get("eventos") or {}).get("items") or [])
        if eventos:
            primero = eventos[0]
            dias = int(primero.get("dias") or 999)
            sev = SEVERIDAD_CRITICA if dias <= 1 else SEVERIDAD_ATENCION
            cards.append(
                HomeCard(
                    tipo="EVENTO_PROXIMO",
                    titulo=f"Proximo evento: {primero.get('nombre') or 'Evento'}.",
                    resumen=f"Fecha {primero.get('fecha') or '-'} | faltan {dias if dias < 999 else '?'} dias.",
                    severidad=sev,
                    cantidad=1,
                    modulo_origen="eventos",
                    accion_navegacion="2",
                    contexto_id=str(primero.get("id") or ""),
                    vigencia=str(primero.get("fecha") or ""),
                )
            )

        stock_items = list((modulos.get("stock") or {}).get("items") or [])
        criticos = [x for x in stock_items if str(x.get("tipo") or "") == "bajo_stock"]
        if criticos:
            prod_txt = self._plural(len(criticos), "producto", "productos")
            cards.append(
                HomeCard(
                    tipo="STOCK_CRITICO",
                    titulo=f"Existen {len(criticos)} {prod_txt} con stock critico.",
                    resumen="Revisar minimo operativo en Stock.",
                    severidad=SEVERIDAD_CRITICA,
                    cantidad=len(criticos),
                    modulo_origen="stock",
                    accion_navegacion="5",
                )
            )

        produccion_items = list((modulos.get("produccion") or {}).get("items") or [])
        bloqueadas = sum(int(x.get("bloqueadas") or 0) for x in produccion_items)
        if bloqueadas > 0:
            tarea_txt = self._plural(bloqueadas, "tarea", "tareas")
            bloqueada_txt = self._plural(bloqueadas, "bloqueada", "bloqueadas")
            cards.append(
                HomeCard(
                    tipo="PRODUCCION_BLOQUEADA",
                    titulo=f"Hay {bloqueadas} {tarea_txt} de produccion {bloqueada_txt}.",
                    resumen="Resolver bloqueo operativo antes de continuar.",
                    severidad=SEVERIDAD_CRITICA,
                    cantidad=bloqueadas,
                    modulo_origen="produccion",
                    accion_navegacion="3",
                )
            )

        cards.sort(key=self._priority_key)
        return [c.to_dict() for c in cards]

    def _estado_global(self, modulos: dict[str, dict[str, Any]], errores: list[dict[str, str]]) -> str:
        estados = [str(v.get("estado") or "") for v in modulos.values()]
        if estados and all(e in {ESTADO_ERROR_PARCIAL, ESTADO_SERVICIO_NO_DISPONIBLE} for e in estados):
            return ESTADO_ERROR_GENERAL
        if errores:
            return ESTADO_ERROR_PARCIAL
        if any(e == ESTADO_DATOS for e in estados):
            return ESTADO_DATOS
        if estados and all(e == ESTADO_SIN_DATOS for e in estados):
            return ESTADO_SIN_DATOS
        return ESTADO_ERROR_PARCIAL

    @staticmethod
    def _pack_items(items: list[dict[str, Any]]) -> dict[str, Any]:
        if not items:
            return {"estado": ESTADO_SIN_DATOS, "total": 0, "items": []}
        return {"estado": ESTADO_DATOS, "total": len(items), "items": items}

    @staticmethod
    def _plural(cantidad: int, singular: str, plural: str) -> str:
        return singular if int(cantidad) == 1 else plural

    @staticmethod
    def _to_dict(obj: Any) -> dict[str, Any]:
        if isinstance(obj, dict):
            return dict(obj)
        if hasattr(obj, "to_dict"):
            return dict(obj.to_dict())
        out: dict[str, Any] = {}
        for key in ["id", "nombre", "fecha", "pax", "servicios", "estado"]:
            if hasattr(obj, key):
                out[key] = getattr(obj, key)
        if "servicios" in out and isinstance(out["servicios"], list):
            serializados = []
            for s in out["servicios"]:
                if hasattr(s, "to_dict"):
                    serializados.append(s.to_dict())
                elif isinstance(s, dict):
                    serializados.append(s)
            out["servicios"] = serializados
        return out

    @staticmethod
    def _dias_hasta(fecha_txt: str, hoy: date) -> int | None:
        if not fecha_txt:
            return None
        try:
            objetivo = datetime.fromisoformat(fecha_txt).date()
        except ValueError:
            return None
        return (objetivo - hoy).days

    @staticmethod
    def _priority_key(card: HomeCard) -> tuple[int, int, int, int, str]:
        sev_rank = {
            SEVERIDAD_INFO: 1,
            SEVERIDAD_ATENCION: 2,
            SEVERIDAD_IMPORTANTE: 3,
            SEVERIDAD_CRITICA: 4,
        }.get(card.severidad, 1)
        proximidad = 999
        if card.vigencia:
            try:
                proximidad = abs((datetime.fromisoformat(card.vigencia).date() - date.today()).days)
            except ValueError:
                proximidad = 999
        bloqueo = 1 if card.severidad == SEVERIDAD_CRITICA else 0
        cantidad = int(card.cantidad or 0)
        return (-sev_rank, -bloqueo, proximidad, -cantidad, card.titulo)


__all__ = [
    "HostAIHomeReadService",
    "HomeCard",
    "SEVERIDAD_INFO",
    "SEVERIDAD_ATENCION",
    "SEVERIDAD_IMPORTANTE",
    "SEVERIDAD_CRITICA",
    "ESTADO_CARGANDO",
    "ESTADO_SIN_DATOS",
    "ESTADO_DATOS",
    "ESTADO_SERVICIO_NO_DISPONIBLE",
    "ESTADO_ERROR_PARCIAL",
    "ESTADO_ERROR_GENERAL",
]
