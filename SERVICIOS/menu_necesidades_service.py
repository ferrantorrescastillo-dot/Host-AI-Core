from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from SERVICIOS.cruce_stock_produccion_556c import CruceStockProduccion556C
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from SERVICIOS.base_datos_local import BaseDatosLocal
from MOTORES.motor_compras import MotorCompras


class MenuNecesidadesService:
    """Proyecta necesidades y crea borradores controlados sin modificar Stock."""

    def __init__(self, base_dir: Path, compras: MotorCompras | None = None) -> None:
        self.base_dir = Path(base_dir)
        self.menus = MenusInteligentesService(self.base_dir)
        self.stock = CruceStockProduccion556C(self.base_dir)
        self.productos = RepositorioProductosMaestro601(self.base_dir)
        self.compras = compras
        self._propuestas: dict[str, dict[str, Any]] = {}

    def necesidades(self, menu_id: str) -> dict[str, Any]:
        result = self.menus.obtener(menu_id)
        if not result.get("ok"):
            return result
        menu = result["menu"]
        aggregated: dict[tuple[str, str], dict[str, Any]] = {}
        unresolved: list[dict[str, Any]] = []
        warnings: list[str] = []

        for section in menu.get("secciones") or []:
            for reference in section.get("elaboraciones") or []:
                objective = float(menu["comensales"]) * float(reference.get("cantidad") or 1)
                try:
                    crossed = self.stock.cruzar(
                        str(reference.get("elaboracion_nombre") or reference.get("elaboracion_id")),
                        objective,
                        "raciones",
                    )
                except (LookupError, ValueError) as exc:
                    warnings.append(str(exc))
                    continue
                factor = float((crossed.get("explosion") or {}).get("factor") or 0)
                for item in crossed.get("lineas") or []:
                    origin = {
                        "seccion": section.get("nombre"),
                        "elaboracion_id": reference.get("elaboracion_id"),
                        "elaboracion_nombre": reference.get("elaboracion_nombre"),
                        "cantidad": item.get("requerido"),
                        "unidad": item.get("unidad"),
                        "factor_escalado": factor,
                    }
                    article_id = str(item.get("articulo_id") or "").strip()
                    if not article_id or item.get("metodo_enlace_articulo") != "ARTICULO_ID_EXACTO":
                        unresolved.append(self._unresolved(item, origin))
                        continue
                    key = (article_id.casefold(), str(item.get("unidad") or "u").casefold())
                    if key in aggregated:
                        line = aggregated[key]
                        line["cantidad_necesaria"] = round(
                            float(line["cantidad_necesaria"]) + float(item.get("requerido") or 0), 4
                        )
                        line["origenes"].append(origin)
                    else:
                        aggregated[key] = self._line(item, origin)

        lines = list(aggregated.values()) + unresolved
        for line in aggregated.values():
            self._finish(line)
        complete = not any(line["estado"] in {
            "Sin artículo relacionado", "Conversión pendiente", "Stock no disponible"
        } for line in lines)
        blocking = [
            {"code": "UNRESOLVED_NEED", "message": line["motivo_no_resuelto"], "articulo_id": line.get("articulo_id")}
            for line in lines if line["estado"] in {"Sin artículo relacionado", "Conversión pendiente"}
        ]
        return {
            "ok": True,
            "necesidades": {
                "menu_id": menu["id"], "menu_version": menu["version"],
                "comensales": menu["comensales"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "complete": complete, "lines": lines, "warnings": warnings,
                "blocking_errors": blocking,
                "summary": {
                    "articulos": len(lines),
                    "cubiertos": sum(x["estado"] == "Cubierto por stock" for x in lines),
                    "compra_necesaria": sum(float(x.get("cantidad_faltante") or 0) > 0 for x in lines),
                    "sin_relacionar": sum(x["estado"] == "Sin artículo relacionado" for x in lines),
                    "conversiones_pendientes": sum(x["estado"] == "Conversión pendiente" for x in lines),
                    "candidatas_propuesta": sum(x["estado"] != "Cubierto por stock" for x in lines),
                },
                "solo_lectura": True, "datos_reales_modificados": False,
            },
        }

    def crear_propuesta(self, menu_id: str) -> dict[str, Any]:
        result = self.necesidades(menu_id)
        if not result.get("ok"):
            return result
        needs = result["necesidades"]
        lines = [
            self._proposal_line(line)
            for line in needs["lines"] if line.get("estado") != "Cubierto por stock"
        ]
        proposal_id = f"MENUPROP-{uuid4().hex[:10].upper()}"
        groups: dict[str, list[dict[str, Any]]] = {}
        for line in lines:
            groups.setdefault(str(line.get("proveedor") or "Sin proveedor asignado"), []).append(line)
        proposal = {
            "id": proposal_id, "menu_id": menu_id, "menu_version": needs["menu_version"],
            "estado": "BORRADOR", "generated_at": datetime.now(timezone.utc).isoformat(),
            "grupos_proveedor": [{"proveedor": key, "lineas": value} for key, value in groups.items()],
            "lineas": lines,
            "coste_estimado": round(sum(float(x.get("coste_estimado") or 0) for x in lines), 4),
            "coste_completo": all(x.get("coste_estimado") is not None for x in lines),
            "advertencias": [x["advertencia"] for x in lines if x.get("advertencia")],
            "resumen": {
                "articulos_propuestos": sum(float(x.get("cantidad_faltante") or 0) > 0 for x in lines),
                "articulos_pendientes": sum(x.get("cantidad_faltante") is None for x in lines),
                "proveedores_pendientes": sum(not x.get("proveedor") for x in lines),
            },
            "crea_pedido": False, "modifica_stock": False, "datos_reales_modificados": False,
            "version": 1, "pedidos_creados": [],
        }
        for index, line in enumerate(proposal["lineas"]):
            line.update({"id": f"LINEA-{index + 1:03d}", "incluir": True, "observaciones": ""})
        self._propuestas[proposal_id] = proposal
        return {"ok": True, "propuesta": proposal}

    def crear_propuesta_con_pedidos(self, menu_id: str, usuario: str = "web") -> dict[str, Any]:
        created = self.crear_propuesta(menu_id)
        if not created.get("ok"):
            return created
        proposal = created["propuesta"]
        included, pending, excluded, warnings = self._clasificar_lineas_pedido(proposal["lineas"])
        if not included:
            return self._resultado_pedidos(
                proposal, [], included, pending, excluded, warnings
            )
        return self.crear_pedidos(
            menu_id,
            proposal["id"],
            {
                "confirmacion": "CREAR_BORRADORES",
                "version": proposal["version"],
                "usuario": usuario,
            },
        )

    def actualizar_propuesta(self, menu_id: str, proposal_id: str, body: dict[str, Any]) -> dict[str, Any]:
        found = self.obtener_propuesta(menu_id, proposal_id)
        if not found.get("ok"):
            return found
        proposal = found["propuesta"]
        if int(body.get("version") or 0) != int(proposal["version"]):
            return {"ok": False, "error": {"status": 409, "code": "proposal_version_conflict", "message": "La propuesta cambió desde la última lectura."}}
        updates = {str(x.get("id")): x for x in body.get("lineas") or []}
        for line in proposal["lineas"]:
            change = updates.get(line["id"])
            if not change:
                continue
            line["incluir"] = bool(change.get("incluir", line["incluir"]))
            line["proveedor"] = str(change.get("proveedor", line.get("proveedor") or "")).strip() or None
            line["observaciones"] = str(change.get("observaciones", line.get("observaciones") or ""))
            if "cantidad_final_propuesta" in change:
                value = change.get("cantidad_final_propuesta")
                line["cantidad_final_propuesta"] = float(value) if value not in (None, "") else None
        proposal["version"] += 1
        proposal["estado"] = "REVISADA"
        return {"ok": True, "propuesta": proposal}

    def crear_pedidos(self, menu_id: str, proposal_id: str, body: dict[str, Any]) -> dict[str, Any]:
        found = self.obtener_propuesta(menu_id, proposal_id)
        if not found.get("ok"):
            return found
        proposal = found["propuesta"]
        if str(body.get("confirmacion") or "") != "CREAR_BORRADORES":
            return {"ok": False, "error": {"status": 400, "code": "confirmation_required", "message": "Debes confirmar explícitamente la creación de borradores."}}
        if int(body.get("version") or 0) != int(proposal["version"]):
            return {"ok": False, "error": {"status": 409, "code": "proposal_version_conflict", "message": "La propuesta está desactualizada. Guárdala o vuelve a cargarla antes de crear pedidos."}}
        menu_result = self.menus.obtener(menu_id)
        if not menu_result.get("ok"):
            return menu_result
        if int(menu_result["menu"]["version"]) != int(proposal["menu_version"]):
            return {"ok": False, "error": {"status": 409, "code": "menu_version_conflict", "message": "El menú cambió después de generar la propuesta. Calcula de nuevo sus necesidades."}}
        included, pending, excluded, warnings = self._clasificar_lineas_pedido(proposal["lineas"])
        if proposal.get("pedidos_creados"):
            return self._resultado_pedidos(proposal, proposal["pedidos_creados"], included, pending, excluded, warnings, idempotente=True)
        groups: dict[str, list[dict[str, Any]]] = {}
        for line in included:
            quantity = float(line["cantidad_final_propuesta"])
            groups.setdefault(line["proveedor"], []).append({
                "nombre": line.get("articulo"), "articulo_id": line.get("articulo_id"),
                "cantidad": quantity, "unidad": line.get("unidad_base"),
                "precio_unitario": line.get("precio_estimado") or 0,
                "observaciones": line.get("observaciones") or "",
                "propuesta_id": proposal_id,
            })
        payload = [{
            "proveedor": provider, "lineas": lines,
            "observaciones": f"Generado desde Menú {menu_id} v{proposal['menu_version']} | propuesta {proposal_id} | usuario {body.get('usuario') or 'web'}",
        } for provider, lines in groups.items()]
        if not payload:
            return {"ok": False, "error": {"status": 400, "code": "no_orderable_lines", "message": "No hay líneas válidas para crear borradores."}}
        if self.compras is None:
            self.compras = MotorCompras(BaseDatosLocal(self.base_dir))
        orders = self.compras.crear_pedidos_borrador_transaccional(payload)
        proposal["pedidos_creados"] = orders
        proposal["estado"] = "CONFIRMADA"
        proposal["crea_pedido"] = True
        proposal["datos_reales_modificados"] = True
        return self._resultado_pedidos(proposal, orders, included, pending, excluded, warnings)

    @staticmethod
    def _clasificar_lineas_pedido(lines: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
        included: list[dict[str, Any]] = []
        pending: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        warnings: list[str] = []
        for line in lines:
            if not line.get("incluir"):
                excluded.append(line)
                continue
            reasons = []
            if not line.get("articulo_id"):
                reasons.append("Falta artículo relacionado.")
            if not line.get("proveedor"):
                reasons.append("Falta proveedor.")
            try:
                valid_quantity = float(line.get("cantidad_final_propuesta")) > 0
            except (TypeError, ValueError):
                valid_quantity = False
            if not valid_quantity:
                reasons.append("Falta una cantidad válida.")
            if not line.get("unidad_base") and not line.get("formato_compra"):
                reasons.append("Falta unidad o formato de compra.")
            if reasons:
                pending.append({**line, "motivos_pendientes": reasons})
                warnings.extend(f"{line.get('articulo') or line.get('id')}: {reason}" for reason in reasons)
            else:
                included.append(line)
        return included, pending, excluded, warnings

    @staticmethod
    def _resultado_pedidos(proposal: dict[str, Any], orders: list[dict[str, Any]], included: list[dict[str, Any]], pending: list[dict[str, Any]], excluded: list[dict[str, Any]], warnings: list[str], *, idempotente: bool = False) -> dict[str, Any]:
        return {
            "ok": True, "propuesta": proposal,
            "pedidos": orders, "pedidos_creados": orders,
            "lineas_incluidas": included, "lineas_pendientes": pending,
            "lineas_excluidas": excluded, "advertencias": warnings, "errores": [],
            "idempotente": idempotente,
            "stock_modificado": False, "recepciones_creadas": 0,
        }

    def obtener_propuesta(self, menu_id: str, proposal_id: str) -> dict[str, Any]:
        proposal = self._propuestas.get(proposal_id)
        if not proposal or proposal.get("menu_id") != menu_id:
            return {"ok": False, "error": {"status": 404, "code": "proposal_not_found", "message": "Propuesta no encontrada."}}
        return {"ok": True, "propuesta": proposal}

    def _line(self, item: dict[str, Any], origin: dict[str, Any]) -> dict[str, Any]:
        product = self.productos.obtener_producto(str(item.get("articulo_id") or "")) or {}
        conversion_pending = item.get("estado") == "UNIDAD_INCOMPATIBLE"
        stock_known = bool(item.get("stock_localizado")) and not conversion_pending
        return {
            "articulo_id": item.get("articulo_id"), "articulo_codigo": item.get("articulo_id"),
            "articulo_nombre": item.get("articulo_nombre"), "ingrediente_nombre": item.get("nombre"),
            "origenes": [origin], "cantidad_necesaria": float(item.get("requerido") or 0),
            "unidad_necesaria": item.get("unidad"), "stock_fisico": item.get("disponible") if stock_known else None,
            "stock_reservado": 0.0 if stock_known else None,
            "stock_comprometido": 0.0 if stock_known else None,
            "stock_disponible": item.get("disponible") if stock_known else None,
            "cantidad_faltante": None, "unidad_stock": item.get("unidad_stock") or item.get("unidad"),
            "estado": "Stock no disponible", "conversion": item.get("metodo_enlace_stock"),
            "proveedor_preferente": product.get("proveedor_preferente") or product.get("proveedor") or item.get("proveedor") or None,
            "formato_compra": product.get("unidad_compra") or None,
            "cantidad_formato": self._number(product.get("cantidad_formato")),
            "cantidad_propuesta_compra": None, "coste_estimado": None,
            "precio_estimado": self._number(product.get("precio")), "fecha_precio": product.get("fecha_precio") or None,
            "motivo_no_resuelto": None, "_stock_known": stock_known,
            "_conversion_pending": conversion_pending,
        }

    def _finish(self, line: dict[str, Any]) -> None:
        if line.pop("_conversion_pending"):
            line.pop("_stock_known")
            line["estado"] = "Conversión pendiente"
            line["motivo_no_resuelto"] = "No existe una conversión canónica entre la unidad de Stock y la unidad de la receta."
            return
        if not line.pop("_stock_known"):
            line["motivo_no_resuelto"] = "El artículo no tiene inventario disponible."
            return
        missing = max(float(line["cantidad_necesaria"]) - float(line["stock_disponible"] or 0), 0)
        line["cantidad_faltante"] = round(missing, 4)
        available = float(line["stock_disponible"] or 0)
        line["estado"] = "Cubierto por stock" if missing == 0 else "Compra necesaria" if available == 0 else "Parcialmente cubierto"
        line["cantidad_propuesta_compra"] = self._purchase_quantity(missing, line.get("cantidad_formato"))
        if missing and not line.get("proveedor_preferente"):
            line["estado"] = "Proveedor pendiente"
        if missing and line.get("cantidad_formato") is None:
            if line.get("proveedor_preferente"):
                line["estado"] = "Formato de compra pendiente"
            line["motivo_no_resuelto"] = "Formato de compra pendiente; se conserva la cantidad base sin redondear."
        price = line.get("precio_estimado")
        if price is not None and line.get("cantidad_propuesta_compra") is not None:
            line["coste_estimado"] = round(float(price) * float(line["cantidad_propuesta_compra"]), 4)

    @staticmethod
    def _unresolved(item: dict[str, Any], origin: dict[str, Any]) -> dict[str, Any]:
        return {
            "articulo_id": None, "articulo_codigo": None, "articulo_nombre": None,
            "ingrediente_nombre": item.get("nombre"), "origenes": [origin],
            "cantidad_necesaria": item.get("requerido"), "unidad_necesaria": item.get("unidad"),
            "stock_fisico": None, "stock_reservado": None, "stock_comprometido": None,
            "stock_disponible": None, "cantidad_faltante": None, "unidad_stock": None,
            "estado": "Sin artículo relacionado", "conversion": None,
            "proveedor_preferente": None, "formato_compra": None,
            "cantidad_propuesta_compra": None, "coste_estimado": None,
            "motivo_no_resuelto": "El ingrediente no tiene una relación exacta y estable con un artículo.",
        }

    @staticmethod
    def _proposal_line(line: dict[str, Any]) -> dict[str, Any]:
        proposed = line.get("cantidad_propuesta_compra")
        raw_missing = line.get("cantidad_faltante")
        missing = float(raw_missing) if raw_missing is not None else None
        return {
            "articulo_id": line.get("articulo_id"), "articulo": line.get("articulo_nombre"),
            "cantidad_faltante": missing, "cantidad_necesaria": line.get("cantidad_necesaria"),
            "unidad_base": line.get("unidad_necesaria"), "estado": line.get("estado"),
            "proveedor": line.get("proveedor_preferente"), "formato_compra": line.get("formato_compra"),
            "cantidad_formatos": (round(float(proposed) / float(line["cantidad_formato"]), 4) if proposed is not None and line.get("cantidad_formato") else None),
            "cantidad_final_propuesta": proposed, "excedente_previsto": (round(float(proposed) - missing, 4) if proposed is not None and missing is not None else None),
            "precio_estimado": line.get("precio_estimado"), "coste_estimado": line.get("coste_estimado"),
            "motivo": "Faltante calculado para el menú" if missing is not None else "Pendiente de revisión antes de comprar",
            "advertencia": line.get("motivo_no_resuelto"),
        }

    @staticmethod
    def _purchase_quantity(missing: float, pack: float | None) -> float:
        if missing <= 0:
            return 0.0
        return round(math.ceil(missing / pack) * pack, 4) if pack and pack > 0 else round(missing, 4)

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            return float(str(value).replace(",", ".")) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None


__all__ = ["MenuNecesidadesService"]
