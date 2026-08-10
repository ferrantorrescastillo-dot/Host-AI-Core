from __future__ import annotations

import base64
import hashlib
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from MODELOS.compras import RecepcionCompra
from SERVICIOS.cruce_stock_produccion_556c import _canon_unidad, _convertir
from SERVICIOS.importador_inteligente_biblioteca import ImportDocumentService
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


class ComprasRecepcionesService:
    """Orquesta borradores de recepci\u00f3n sobre Compras y Stock can\u00f3nicos."""

    def __init__(self, core: Any) -> None:
        self.core = core
        self.compras = core.compras
        self.stock = core.stock
        self.productos = RepositorioProductosMaestro601(core.base_dir)
        self.documents_dir = Path(core.base_dir) / "DATOS" / "documentos" / "recepciones"

    def adjuntar_documento(self, reception_id: str, body: dict[str, Any]) -> dict[str, Any]:
        reception = self.compras.recepciones_compra.get(reception_id)
        if not reception:
            return self._error(404, "reception_not_found", "Recepción no encontrada.")
        if reception.estado != "borrador":
            return self._error(409, "confirmed_reception_immutable", "La evidencia de una recepción confirmada es inmutable.")
        filename = Path(str(body.get("nombre") or "")).name
        suffix = Path(filename).suffix.lower()
        if suffix not in ImportDocumentService.ALLOWED_EXTENSIONS:
            return self._error(400, "unsupported_document_format", "Formato de documento no admitido.")
        try:
            content = base64.b64decode(str(body.get("contenido_base64") or ""), validate=True)
        except (ValueError, TypeError):
            return self._error(400, "invalid_document_content", "El contenido del documento no es válido.")
        if not content:
            return self._error(400, "empty_document", "El documento está vacío.")
        if len(content) > ImportDocumentService.MAX_BYTES:
            return self._error(413, "document_too_large", "El documento supera el límite de 10 MB.")
        checksum = hashlib.sha256(content).hexdigest()
        current = dict(reception.trazabilidad.get("documento") or {})
        if current.get("checksum_sha256") == checksum:
            return {"ok": True, "recepcion": self._project(reception), "documento": current,
                    "idempotente": True, "stock_modificado": False}
        if current:
            return self._error(409, "document_already_attached", "La recepción ya tiene un documento adjunto.")
        document_id = f"DOC-REC-{uuid4().hex[:12].upper()}"
        target = self.documents_dir / f"{document_id}{suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(target.suffix + ".tmp")
        temp.write_bytes(content)
        temp.replace(target)
        now = datetime.now().isoformat(timespec="seconds")
        document = {
            "document_id": document_id, "nombre": filename,
            "tipo_mime": str(body.get("tipo_mime") or "application/octet-stream"),
            "tamano": len(content), "fecha_subida": now,
            "usuario": str(body.get("usuario") or "web"), "proveedor": reception.proveedor,
            "order_id": reception.pedido_id, "reception_id": reception.id,
            "referencia": str(body.get("referencia") or ""), "fecha_albaran": str(body.get("fecha_albaran") or ""),
            "observaciones": str(body.get("observaciones") or ""), "checksum_sha256": checksum,
            "estado": "PENDIENTE_REVISION", "ruta_relativa": str(target.relative_to(Path(self.core.base_dir))).replace("\\", "/"),
        }
        trace_before = deepcopy(reception.trazabilidad)
        reception.trazabilidad["documento"] = document
        reception.trazabilidad.update({"document_id": document_id, "document_name": filename,
                                       "document_type": "albaran", "document_reference": document["referencia"]})
        reception.tocar()
        try:
            self.compras._guardar()
        except Exception:
            reception.trazabilidad = trace_before
            target.unlink(missing_ok=True)
            raise
        return {"ok": True, "recepcion": self._project(reception), "documento": document,
                "idempotente": False, "stock_modificado": False}

    def obtener_documento(self, reception_id: str) -> dict[str, Any]:
        reception = self.compras.recepciones_compra.get(reception_id)
        if not reception:
            return self._error(404, "reception_not_found", "Recepción no encontrada.")
        document = dict(reception.trazabilidad.get("documento") or {})
        if not document:
            return self._error(404, "document_not_found", "La recepción no tiene documento adjunto.")
        path = Path(self.core.base_dir) / str(document.get("ruta_relativa") or "")
        if not path.is_file() or self.documents_dir.resolve() not in path.resolve().parents:
            return self._error(404, "document_file_not_found", "No se encuentra el archivo documental.")
        return {"ok": True, "documento": {**document, "contenido_base64": base64.b64encode(path.read_bytes()).decode("ascii")},
                "stock_modificado": False}

    def quitar_documento(self, reception_id: str) -> dict[str, Any]:
        reception = self.compras.recepciones_compra.get(reception_id)
        if not reception:
            return self._error(404, "reception_not_found", "Recepción no encontrada.")
        if reception.estado != "borrador":
            return self._error(409, "confirmed_reception_immutable", "La evidencia de una recepción confirmada es inmutable.")
        document = dict(reception.trazabilidad.pop("documento", {}) or {})
        for key in ("document_id", "document_name", "document_type", "document_reference"):
            reception.trazabilidad[key] = ""
        reception.tocar(); self.compras._guardar()
        if document:
            path = Path(self.core.base_dir) / str(document.get("ruta_relativa") or "")
            if path.is_file() and self.documents_dir.resolve() in path.resolve().parents:
                path.unlink()
        return {"ok": True, "recepcion": self._project(reception), "documento_eliminado": bool(document),
                "stock_modificado": False}

    def crear(self, pedido_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        pedido = self.compras.obtener_pedido(pedido_id)
        if not pedido:
            return self._error(404, "order_not_found", "Pedido no encontrado.")
        if pedido.estado not in {"preparado", "enviado", "parcialmente_recibido"}:
            return self._error(409, "order_not_receivable", f"El pedido no admite recepci\u00f3n en estado {pedido.estado}.")
        existing = next((r for r in self.compras.recepciones_compra.values()
                         if r.pedido_id == pedido_id and r.estado == "borrador"), None)
        if existing:
            return {"ok": True, "recepcion": self._project(existing), "idempotente": True, "stock_modificado": False}
        received = self._received_by_line(pedido_id)
        lines = []
        for line in pedido.lineas:
            previous = round(received.get(line.id, 0.0), 6)
            pending = max(0.0, round(float(line.cantidad) - previous, 6))
            if pending <= 0:
                continue
            lines.append({
                "order_line_id": line.id, "article_id": line.articulo_id or "", "article_name": line.nombre,
                "ordered_quantity": float(line.cantidad), "previously_received": previous, "pending_quantity": pending,
                "received_quantity": pending, "unit": line.unidad, "order_price": float(line.precio_unitario or 0),
                "received_price": None, "lot": "", "expiry": "", "location": "", "observations": "",
                "incidences": [],
            })
        if not lines:
            return self._error(409, "order_fully_received", "El pedido ya est\u00e1 completamente recibido.")
        body = dict(body or {})
        reception = RecepcionCompra(
            pedido_id=pedido.id, proveedor=pedido.proveedor, estado="borrador", lineas=lines,
            observaciones=str(body.get("observaciones") or ""),
            trazabilidad={
                "fecha": str(body.get("fecha") or datetime.now().date().isoformat()),
                "referencia": str(body.get("referencia") or ""),
                "document_id": str(body.get("document_id") or ""), "document_name": str(body.get("document_name") or ""),
                "document_type": str(body.get("document_type") or "albaran"),
                "document_reference": str(body.get("document_reference") or body.get("referencia") or ""),
            },
        )
        self.compras.recepciones_compra[reception.id] = reception
        self.compras._guardar()
        return {"ok": True, "recepcion": self._project(reception), "idempotente": False, "stock_modificado": False}

    def obtener(self, reception_id: str) -> dict[str, Any]:
        reception = self.compras.recepciones_compra.get(reception_id)
        if not reception:
            return self._error(404, "reception_not_found", "Recepci\u00f3n no encontrada.")
        return {"ok": True, "recepcion": self._project(reception), "stock_modificado": False}

    def actualizar(self, reception_id: str, body: dict[str, Any]) -> dict[str, Any]:
        reception = self.compras.recepciones_compra.get(reception_id)
        if not reception:
            return self._error(404, "reception_not_found", "Recepci\u00f3n no encontrada.")
        if reception.estado != "borrador":
            return self._error(409, "confirmed_reception_immutable", "Una recepci\u00f3n confirmada no se puede reescribir.")
        self._apply_changes(reception, body)
        reception.tocar()
        self._validate(reception)
        self.compras._guardar()
        return {"ok": True, "recepcion": self._project(reception), "stock_modificado": False}

    def _apply_changes(self, reception: RecepcionCompra, body: dict[str, Any]) -> None:
        updates = {str(line.get("order_line_id") or ""): line for line in list(body.get("lineas") or [])}
        for line in reception.lineas:
            change = updates.get(str(line.get("order_line_id") or ""))
            if not change:
                continue
            for key in ("received_quantity", "received_price", "unit", "lot", "expiry", "location", "observations", "article_id", "article_name"):
                if key in change:
                    line[key] = change[key]
        known_ids = {str(line.get("order_line_id") or "") for line in reception.lineas}
        for change in list(body.get("lineas") or []):
            key = str(change.get("order_line_id") or "")
            if key and key in known_ids:
                continue
            reception.lineas.append({
                "order_line_id": key or f"MANUAL-{uuid4().hex[:8].upper()}", "article_id": str(change.get("article_id") or ""),
                "article_name": str(change.get("article_name") or "L\u00ednea manual"), "ordered_quantity": 0.0,
                "previously_received": 0.0, "pending_quantity": 0.0, "received_quantity": change.get("received_quantity", 0),
                "unit": str(change.get("unit") or ""), "order_price": 0.0, "received_price": change.get("received_price"),
                "lot": str(change.get("lot") or ""), "expiry": str(change.get("expiry") or ""),
                "location": str(change.get("location") or ""), "observations": str(change.get("observations") or ""), "incidences": [],
            })
        for key in ("fecha", "referencia", "document_id", "document_name", "document_type", "document_reference"):
            if key in body:
                reception.trazabilidad[key] = str(body.get(key) or "")
        if "observaciones" in body:
            reception.observaciones = str(body.get("observaciones") or "")
        document = reception.trazabilidad.get("documento")
        if isinstance(document, dict):
            mapping = {"referencia": "referencia", "fecha_albaran": "fecha_albaran", "observaciones": "observaciones"}
            for source, target in mapping.items():
                if source in body:
                    document[target] = str(body.get(source) or "")
            if any(key in body for key in mapping):
                document["estado"] = "REVISADO"
            document["proveedor"] = reception.proveedor
            document["order_id"] = reception.pedido_id
            document["reception_id"] = reception.id
            reception.trazabilidad["document_reference"] = str(document.get("referencia") or "")

    def confirmar(self, reception_id: str, body: dict[str, Any]) -> dict[str, Any]:
        reception = self.compras.recepciones_compra.get(reception_id)
        if not reception:
            return self._error(404, "reception_not_found", "Recepci\u00f3n no encontrada.")
        if reception.estado == "confirmada":
            return {"ok": True, "recepcion": self._project(reception), "idempotente": True, "stock_modificado": False}
        if str(body.get("confirmacion") or "") != "CONFIRMAR_RECEPCION":
            return self._error(400, "confirmation_required", "Debes confirmar expl\u00edcitamente la recepci\u00f3n.")
        extraction = dict(reception.trazabilidad.get("extraccion_documental") or {})
        if extraction and (not extraction.get("applied_at") or extraction.get("application_blocking_issues")):
            return self._error(409, "document_review_pending", "La propuesta documental debe revisarse y aplicarse antes de confirmar.")
        expected_version = str(body.get("actualizado_en") or "")
        if expected_version and expected_version != reception.actualizado_en:
            return self._error(409, "stale_reception", "La recepci\u00f3n cambió desde que se abrió. Recárgala antes de confirmar.")
        purchases = deepcopy(self.compras.recepciones_compra)
        if "lineas" in body:
            self._apply_changes(reception, body)
        issues = self._validate(reception)
        blocking = [issue for issue in issues if issue.get("bloqueante")]
        if blocking:
            self.compras.recepciones_compra = purchases
            return {"ok": False, "error": {"status": 400, "code": "invalid_reception", "message": "La recepci\u00f3n contiene incidencias bloqueantes."}, "incidencias": blocking}
        pedido = self.compras.obtener_pedido(reception.pedido_id)
        if not pedido:
            self.compras.recepciones_compra = purchases
            return self._error(404, "order_not_found", "Pedido no encontrado.")
        stock_lots, stock_moves = deepcopy(self.stock.lotes), deepcopy(self.stock.movimientos)
        order_before = deepcopy(pedido.to_dict())
        movements = []
        try:
            for line in reception.lineas:
                quantity = float(line.get("received_quantity") or 0)
                if quantity <= 0:
                    continue
                price = line.get("received_price")
                price = float(line.get("order_price") or 0) if price in (None, "") else float(price)
                stock_quantity = float(line.get("stock_quantity") or quantity)
                stock_unit = str(line.get("canonical_unit") or line.get("unit") or "")
                trace = {
                    "reception_id": reception.id, "order_id": pedido.id, "provider": pedido.proveedor,
                    "article_id": line.get("article_id"), "quantity_received": quantity,
                    "unit_received": line.get("unit"), "quantity": stock_quantity, "unit": stock_unit,
                    "lot": line.get("lot") or "", "expiry": line.get("expiry") or "", "location": line.get("location") or "",
                    "origin": "recepcion_compra",
                    "document_id": reception.trazabilidad.get("document_id") or "",
                    "extraction_id": (reception.trazabilidad.get("extraccion_documental") or {}).get("extraction_id") or "",
                }
                result = self.stock.registrar_entrada(
                    nombre=str(line.get("article_name") or ""), cantidad=stock_quantity, unidad=stock_unit,
                    ubicacion=str(line.get("location") or ""), proveedor=pedido.proveedor,
                    articulo_id=str(line.get("article_id") or ""), caducidad=str(line.get("expiry") or ""),
                    coste_unitario=price, motivo=f"recepci\u00f3n de compra {reception.id}", trazabilidad=trace,
                )
                movements.append(result["movimiento"])
                line["movement_id"] = result["movimiento"]["id"]
                line["stock_lot_id"] = result["lote"]["id"]
            reception.estado = "confirmada"; reception.confirmado_en = datetime.now().isoformat(timespec="seconds")
            reception.stock_aplicado = True; reception.stock_aplicado_en = reception.confirmado_en; reception.tocar()
            received = self._received_by_line(pedido.id)
            complete = all(received.get(line.id, 0.0) >= float(line.cantidad) - 1e-9 for line in pedido.lineas)
            pedido.estado = "recibido" if complete else "parcialmente_recibido"
            if complete: pedido.recibido_en = reception.confirmado_en
            pedido.recepciones.append({"id": reception.id, "creado_en": reception.creado_en, "estado": reception.estado, "lineas": len(movements)})
            pedido.tocar("recepcion_confirmada", f"Recepci\u00f3n {reception.id} confirmada con {len(movements)} entradas de Stock.")
            self.compras._guardar()
        except Exception:
            self.stock.lotes, self.stock.movimientos = stock_lots, stock_moves
            self.stock._guardar_automatico()
            self.compras.recepciones_compra = purchases
            self.compras.pedidos_sugeridos[pedido.id] = type(pedido).from_dict(order_before)
            self.compras._guardar()
            raise
        return {"ok": True, "recepcion": self._project(reception), "pedido": pedido.to_dict(), "movimientos": movements,
                "idempotente": False, "stock_modificado": bool(movements)}

    def _received_by_line(self, pedido_id: str) -> dict[str, float]:
        totals: dict[str, float] = {}
        for reception in self.compras.recepciones_compra.values():
            if reception.pedido_id != pedido_id or reception.estado != "confirmada":
                continue
            for line in reception.lineas:
                key = str(line.get("order_line_id") or "")
                totals[key] = totals.get(key, 0.0) + float(line.get("received_quantity") or 0)
        return totals

    def _validate(self, reception: RecepcionCompra) -> list[dict[str, Any]]:
        issues = []
        for line in reception.lineas:
            line_issues = []
            article_id = str(line.get("article_id") or "").strip()
            product = self.productos.obtener_producto(article_id) if article_id else None
            if not product:
                line_issues.append({"code": "ARTICULO_SIN_RELACIONAR", "message": "La l\u00ednea no tiene un art\u00edculo can\u00f3nico relacionado.", "bloqueante": True})
            raw_unit = str(line.get("unit") or "").strip()
            raw_canonical = str((product or {}).get("unidad_base") or (product or {}).get("unidad") or "").strip()
            unit = _canon_unidad(raw_unit) if raw_unit else ""
            canonical = _canon_unidad(raw_canonical) if raw_canonical else ""
            converted = _convertir(float(self._number(line.get("received_quantity")) or 0), unit, canonical) if product and unit and canonical else None
            line["canonical_unit"] = canonical
            line["stock_quantity"] = converted
            if product and converted is None:
                line_issues.append({"code": "UNIDAD_INCOMPATIBLE", "message": f"Unidad recibida {unit or 'sin unidad'}; unidad can\u00f3nica {canonical or 'sin definir'}.", "bloqueante": True})
            quantity = self._number(line.get("received_quantity"))
            if quantity is None or quantity < 0:
                line_issues.append({"code": "CANTIDAD_INVALIDA", "message": "La cantidad recibida debe ser cero o positiva.", "bloqueante": True})
            elif quantity != float(line.get("pending_quantity") or 0):
                line_issues.append({"code": "DIFERENCIA_CANTIDAD", "message": f"Pendiente {line.get('pending_quantity')} y recibido ahora {quantity}.", "bloqueante": False})
            if line.get("received_price") not in (None, "") and float(line["received_price"]) != float(line.get("order_price") or 0):
                line_issues.append({"code": "DIFERENCIA_PRECIO", "message": "El precio recibido difiere del precio del pedido.", "bloqueante": False})
            line["incidences"] = line_issues
            issues.extend([{**issue, "order_line_id": line.get("order_line_id")} for issue in line_issues])
        reception.incidencias = issues
        return issues

    def _project(self, reception: RecepcionCompra) -> dict[str, Any]:
        self._validate(reception)
        data = reception.to_dict()
        extraction = dict(reception.trazabilidad.get("extraccion_documental") or {})
        document_review_pending = bool(extraction and (not extraction.get("applied_at") or extraction.get("application_blocking_issues")))
        data.update({
            "reception_id": reception.id, "order_id": reception.pedido_id, "fecha": reception.trazabilidad.get("fecha"),
            "referencia": reception.trazabilidad.get("referencia"), "document_id": reception.trazabilidad.get("document_id"),
            "document_name": reception.trazabilidad.get("document_name"), "document_type": reception.trazabilidad.get("document_type"),
            "document_reference": reception.trazabilidad.get("document_reference"),
            "documento": reception.trazabilidad.get("documento"),
            "extraccion_documental": reception.trazabilidad.get("extraccion_documental"),
            "estado": reception.estado.upper(), "confirmable": reception.estado == "borrador" and not document_review_pending and not any(x.get("bloqueante") for x in reception.incidencias),
        })
        return data

    @staticmethod
    def _number(value: Any) -> float | None:
        try: return float(value)
        except (TypeError, ValueError): return None

    @staticmethod
    def _error(status: int, code: str, message: str) -> dict[str, Any]:
        return {"ok": False, "error": {"status": status, "code": code, "message": message}}


__all__ = ["ComprasRecepcionesService"]
