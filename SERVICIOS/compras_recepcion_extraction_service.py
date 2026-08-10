from __future__ import annotations

import re
import unicodedata
from copy import deepcopy
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from uuid import uuid4

from SERVICIOS.cruce_stock_produccion_556c import _canon_unidad, _convertir
from SERVICIOS.compras_recepciones_service import ComprasRecepcionesService
from SERVICIOS.importador_inteligente_biblioteca import ExistingReadersDocumentInterpreter
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


class ComprasRecepcionExtractionService:
    """Extrae propuestas revisables; nunca confirma recepciones ni escribe Stock."""

    def __init__(self, core: Any) -> None:
        self.core = core
        self.compras = core.compras
        self.productos = RepositorioProductosMaestro601(core.base_dir)
        self.receptions = ComprasRecepcionesService(core)

    def analizar(self, reception_id: str, body: dict[str, Any]) -> dict[str, Any]:
        reception = self.compras.recepciones_compra.get(reception_id)
        if not reception:
            return self._error(404, "reception_not_found", "Recepción no encontrada.")
        if reception.estado != "borrador":
            return self._error(409, "confirmed_reception_immutable", "Solo se analiza una recepción en borrador.")
        document = dict(reception.trazabilidad.get("documento") or {})
        if not document:
            return self._error(409, "document_required", "Adjunta un albarán antes de analizarlo.")
        order = self.compras.obtener_pedido(reception.pedido_id)
        if not order:
            return self._error(404, "order_not_found", "Pedido no encontrado.")
        path = (Path(self.core.base_dir) / str(document.get("ruta_relativa") or "")).resolve()
        if not path.is_file():
            return self._error(404, "document_file_not_found", "No se encuentra el archivo documental.")
        content = path.read_bytes()
        manual_text = str(body.get("texto_ocr") or "").strip()
        method = "texto_manual_ocr" if manual_text else "lector_nativo"
        warnings: list[str] = []
        if manual_text:
            text = manual_text
        elif path.suffix.lower() == ".pdf":
            try:
                pdf = self.core.lector_pdf_facturas.analizar_pdf(str(path), exportar_json=False)
                text = str(pdf.get("texto_completo") or "").strip()
                method = str(pdf.get("metodo_extraccion") or "pdf_texto_embebido")
            except Exception as exc:
                text = ""; warnings.append(f"No se pudo extraer texto PDF: {type(exc).__name__}.")
        else:
            interpreted = ExistingReadersDocumentInterpreter().interpret(
                filename=str(document.get("nombre") or path.name), content=content, text=""
            )
            text = str(interpreted.texto or "").strip()
            warnings.extend(str(item) for item in interpreted.advertencias)
        if not text:
            return self._error(
                422, "ocr_required",
                "El documento no contiene texto extraíble y no hay OCR real conectado. Añade una transcripción OCR para revisarla.",
                details={"metodo": "pendiente_ocr_real", "warnings": warnings},
            )
        parsed = self.core.lector_completo_lineas_factura.leer_factura_texto_completa(texto=text)
        header = self.core.lector_pdf_facturas.detectar_factura_desde_texto(text)
        detected_supplier = (order.proveedor if self._norm(order.proveedor) in self._norm(text)
                             else str(parsed.get("proveedor_nombre") or header.get("proveedor") or ""))
        provider = self._provider_result(order.proveedor, detected_supplier)
        extracted_lines = [self._match_line(raw, order, reception) for raw in list(parsed.get("lineas") or [])]
        previous = dict(reception.trazabilidad.get("extraccion_documental") or {})
        reviewed = {self._norm(line.get("source_text")): line for line in list(previous.get("applied_lines") or [])}
        for index, line in enumerate(extracted_lines):
            accepted = reviewed.get(self._norm(line.get("source_text")))
            if accepted:
                for key in ("matched_article_id", "article_name", "order_line_id", "accepted"):
                    line[key] = accepted.get(key, line.get(key))
                extracted_lines[index] = self._validate_reviewed_line(line, order, reception)
        missing = self._missing_order_lines(extracted_lines, order)
        issues = list(provider["issues"])
        if not str(header.get("numero_factura") or ""):
            issues.append(self._issue("REFERENCIA_PEDIDO_NO_DETECTADA", "No se detectó referencia de pedido.", False))
        issues.extend(issue for line in extracted_lines for issue in line["issues"])
        issues.extend(missing)
        extraction_id = str(previous.get("extraction_id") or f"EXT-REC-{uuid4().hex[:12].upper()}")
        extraction = {
            "extraction_id": extraction_id, "document_id": document["document_id"],
            "reception_id": reception.id, "order_id": reception.pedido_id,
            "supplier_name": detected_supplier,
            "supplier_tax_id": str(header.get("cif") or ""), "supplier_reference": "",
            "delivery_note_number": str(header.get("numero_factura") or ""),
            "delivery_date": str(header.get("fecha") or ""), "order_reference": self._order_reference(text, order.id),
            "currency": "EUR", "subtotal": float(header.get("base_imponible") or 0),
            "taxes": float(header.get("iva") or 0), "total": float(header.get("total") or parsed.get("total_importe_lineas") or 0),
            "confidence": float(parsed.get("confianza_media") or 0), "warnings": warnings,
            "provider_match": provider, "lines": extracted_lines, "issues": issues,
            "method": method, "model": "reglas_host_ai", "analyzed_at": datetime.now().isoformat(timespec="seconds"),
            "source_text": text, "decisions": list(previous.get("decisions") or []),
        }
        extraction["summary"] = self._summary(extraction)
        reception.trazabilidad["extraccion_documental"] = extraction
        reception.tocar(); self.compras._guardar()
        return {"ok": True, "extraccion": extraction, "propuesta": extraction,
                "recepcion": self.receptions._project(reception), "stock_modificado": False}

    def aplicar(self, reception_id: str, body: dict[str, Any]) -> dict[str, Any]:
        reception = self.compras.recepciones_compra.get(reception_id)
        if not reception:
            return self._error(404, "reception_not_found", "Recepción no encontrada.")
        if reception.estado != "borrador":
            return self._error(409, "confirmed_reception_immutable", "La recepción confirmada es inmutable.")
        stored = dict(reception.trazabilidad.get("extraccion_documental") or {})
        if not stored or str(body.get("extraction_id") or "") != str(stored.get("extraction_id") or ""):
            return self._error(409, "stale_extraction", "La propuesta ya no es la extracción vigente.")
        order = self.compras.obtener_pedido(reception.pedido_id)
        proposed = [self._validate_reviewed_line(dict(line), order, reception)
                    for line in list(body.get("lines") or stored.get("lines") or [])]
        blocking = [issue for line in proposed for issue in list(line.get("issues") or []) if issue.get("blocking")]
        blocking.extend(issue for issue in list(stored.get("provider_match", {}).get("issues") or []) if issue.get("blocking"))
        if blocking:
            return {**self._error(400, "proposal_has_blocking_issues", "Resuelve las incidencias bloqueantes antes de aplicar."), "issues": blocking}
        by_order = {str(line.get("order_line_id") or ""): line for line in proposed if line.get("accepted", True)}
        for line in reception.lineas:
            proposal = by_order.get(str(line.get("order_line_id") or ""))
            if not proposal:
                continue
            line["article_id"] = str(proposal.get("matched_article_id") or line.get("article_id") or "")
            line["article_name"] = str(proposal.get("article_name") or line.get("article_name") or "")
            line["received_quantity"] = proposal.get("quantity", line.get("received_quantity"))
            line["unit"] = str(proposal.get("unit") or line.get("unit") or "")
            line["received_price"] = proposal.get("unit_price") if proposal.get("unit_price") is not None else line.get("received_price")
            line["lot"] = str(proposal.get("lot") or line.get("lot") or "")
            line["expiry"] = str(proposal.get("expiration_date") or line.get("expiry") or "")
        reception.trazabilidad["extraccion_documental"]["decisions"] = list(body.get("decisions") or [])
        reception.trazabilidad["extraccion_documental"]["applied_at"] = datetime.now().isoformat(timespec="seconds")
        reception.trazabilidad["extraccion_documental"]["applied_lines"] = deepcopy(proposed)
        reception.trazabilidad["extraccion_documental"]["application_blocking_issues"] = blocking
        reception.tocar()
        self.receptions._validate(reception)
        self.compras._guardar()
        return {"ok": True, "recepcion": self.receptions._project(reception), "extraccion": reception.trazabilidad["extraccion_documental"],
                "stock_modificado": False, "confirmada": False}

    def _validate_reviewed_line(self, line: dict[str, Any], order: Any, reception: Any) -> dict[str, Any]:
        issues = [issue for issue in list(line.get("issues") or []) if not issue.get("blocking")]
        article_id = str(line.get("matched_article_id") or "")
        product = self.productos.obtener_producto(article_id) if article_id else None
        order_line = next((item for item in order.lineas if item.id == str(line.get("order_line_id") or "")), None) if order else None
        if not order_line and order:
            order_line = next((item for item in order.lineas if str(item.articulo_id or "") == article_id), None)
            if order_line:
                line["order_line_id"] = order_line.id
        reception_line = next((item for item in reception.lineas if order_line and item.get("order_line_id") == order_line.id), None)
        quantity = self._number(line.get("quantity")); unit = _canon_unidad(str(line.get("unit") or ""))
        if not product or not order_line:
            issues.append(self._issue("SIN_RELACIONAR", "Selecciona un artículo y una línea del pedido.", True))
        if quantity is None or quantity < 0:
            issues.append(self._issue("CANTIDAD_INVALIDA", "La cantidad propuesta debe ser cero o positiva.", True))
        if order_line and quantity is not None and _convertir(quantity, unit, _canon_unidad(order_line.unidad)) is None:
            issues.append(self._issue("CONVERSION_PENDIENTE", f"No existe conversión de {unit} a {_canon_unidad(order_line.unidad)}.", True))
        if order_line and quantity is not None:
            pending = float((reception_line or {}).get("pending_quantity") or order_line.cantidad)
            converted = _convertir(quantity, unit, _canon_unidad(order_line.unidad))
            if converted is not None and abs(converted - pending) > 1e-9 and not any(x.get("code") == "CANTIDAD_DISTINTA" for x in issues):
                issues.append(self._issue("CANTIDAD_DISTINTA", f"Cantidad propuesta {quantity} {unit}; pendiente {pending} {order_line.unidad}.", False))
        line["issues"] = issues; line["accepted"] = not any(issue.get("blocking") for issue in issues)
        return line

    def _match_line(self, raw: dict[str, Any], order: Any, reception: Any) -> dict[str, Any]:
        name = str(raw.get("descripcion") or "").strip(); source = str(raw.get("origen_texto") or name)
        supplier_ref = str(raw.get("codigo_proveedor") or self._capture(source, r"\b(?:ref|sku|cod)\.?\s*[:#-]?\s*([A-Z0-9-]+)") or "").strip()
        lot = self._capture(source, r"\b(?:lote|lot)\s*[:#-]?\s*([A-Z0-9-]+)")
        expiry = self._capture(source, r"\b(?:cad(?:ucidad)?|vence|exp)\s*[:#-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})")
        products = self.productos.listar_productos()
        candidates: list[dict[str, Any]] = []
        for product in products:
            refs = {self._norm(product.get("referencia_proveedor")), self._norm(product.get("codigo"))}
            aliases = [product.get("nombre"), product.get("alias"), *(product.get("aliases") or [])]
            score, method = 0.0, ""
            if supplier_ref and self._norm(supplier_ref) in refs:
                score, method = 100.0, "referencia_proveedor"
            elif self._norm(name) in {self._norm(value) for value in aliases if value}:
                score, method = 100.0, "nombre_exacto"
            else:
                score = max((SequenceMatcher(None, self._norm(name), self._norm(value)).ratio() * 100 for value in aliases if value), default=0)
                method = "similitud_texto"
            if score >= 55:
                candidates.append({"article_id": product.get("codigo"), "name": product.get("nombre"), "score": round(score, 2), "method": method, "unit": product.get("unidad_base") or product.get("unidad") or ""})
        candidates.sort(key=lambda item: item["score"], reverse=True)
        top = candidates[0] if candidates else None
        tied = bool(top and len(candidates) > 1 and candidates[1]["score"] >= top["score"] - 3)
        status = "SIN_MATCH" if not top else "AMBIGUO" if tied else "MATCH_EXACTO" if top["score"] == 100 else "MATCH_PROPUESTO"
        matched_id = str(top.get("article_id") or "") if top and status != "AMBIGUO" else ""
        order_line = next((line for line in order.lineas if str(line.articulo_id or "") == matched_id), None)
        if not order_line and top:
            order_line = next((line for line in order.lineas if self._norm(line.nombre) == self._norm(top.get("name"))), None)
        reception_line = next((line for line in reception.lineas if order_line and line.get("order_line_id") == order_line.id), None)
        quantity = float(raw.get("cantidad") or 0); unit = _canon_unidad(str(raw.get("unidad") or ""))
        issues: list[dict[str, Any]] = []
        comparison = "COINCIDE"
        if status in {"SIN_MATCH", "AMBIGUO"}:
            issues.append(self._issue(status, "La línea requiere seleccionar un artículo.", True)); comparison = "SIN_RELACIONAR"
        elif not order_line:
            issues.append(self._issue("ARTICULO_EXTRA", "El artículo no figura en el pedido.", True)); comparison = "ARTICULO_EXTRA"
        else:
            order_unit = _canon_unidad(order_line.unidad)
            converted = _convertir(quantity, unit, order_unit)
            if converted is None:
                issues.append(self._issue("CONVERSION_PENDIENTE", f"No existe conversión de {unit} a {order_unit}.", True)); comparison = "UNIDAD_DISTINTA"
            pending = float((reception_line or {}).get("pending_quantity") or order_line.cantidad)
            if converted is not None and abs(converted - pending) > 1e-9:
                issues.append(self._issue("CANTIDAD_DISTINTA", f"Documento {quantity} {unit}; pendiente {pending} {order_unit}.", False)); comparison = "CANTIDAD_DISTINTA"
            if raw.get("precio_unitario") is not None and abs(float(raw.get("precio_unitario") or 0) - float(order_line.precio_unitario or 0)) > 1e-9:
                issues.append(self._issue("PRECIO_DISTINTO", "El precio del albarán difiere del pedido.", False)); comparison = "PRECIO_DISTINTO" if comparison == "COINCIDE" else comparison
        order_price = float(getattr(order_line, "precio_unitario", 0) or 0)
        document_price = float(raw.get("precio_unitario") or 0)
        price_variation = round(((document_price - order_price) / order_price) * 100, 2) if order_price else None
        return {
            "source_text": source, "supplier_article_reference": supplier_ref,
            "article_name": str((top or {}).get("name") or name), "quantity": quantity, "unit": unit,
            "unit_price": float(raw.get("precio_unitario") or 0), "line_total": float(raw.get("importe") or 0),
            "lot": str(raw.get("lote") or lot or ""), "expiration_date": str(raw.get("caducidad") or expiry or ""),
            "confidence": float(raw.get("confianza") or 0), "matched_article_id": matched_id,
            "match_status": status, "comparison_status": comparison, "candidates": candidates[:5],
            "order_line_id": getattr(order_line, "id", ""), "ordered_quantity": float(getattr(order_line, "cantidad", 0) or 0),
            "previously_received": float((reception_line or {}).get("previously_received") or 0),
            "pending_quantity": float((reception_line or {}).get("pending_quantity") or 0),
            "order_unit": str(getattr(order_line, "unidad", "") or ""), "order_price": order_price,
            "price_variation_pct": price_variation,
            "issues": issues, "accepted": not any(issue["blocking"] for issue in issues),
        }

    def _provider_result(self, expected: str, detected: str) -> dict[str, Any]:
        if not detected:
            status, confidence = "PROVEEDOR_NO_DETECTADO", 0.0
        elif self._norm(expected) == self._norm(detected) or self._norm(expected) in self._norm(detected) or self._norm(detected) in self._norm(expected):
            status, confidence = "PROVEEDOR_COINCIDE", 100.0
        else:
            confidence = round(SequenceMatcher(None, self._norm(expected), self._norm(detected)).ratio() * 100, 2)
            status = "PROVEEDOR_DUDOSO" if confidence >= 65 else "PROVEEDOR_NO_COINCIDE"
        blocking = status == "PROVEEDOR_NO_COINCIDE"
        issues = [] if status == "PROVEEDOR_COINCIDE" else [self._issue(status, f"Proveedor del pedido: {expected}; detectado: {detected or 'no detectado'}.", blocking)]
        return {"status": status, "expected": expected, "detected": detected, "confidence": confidence, "issues": issues}

    def _missing_order_lines(self, lines: list[dict[str, Any]], order: Any) -> list[dict[str, Any]]:
        matched = {line.get("order_line_id") for line in lines}
        return [self._issue("ARTICULO_FALTANTE", f"{line.nombre} no aparece en el documento.", False, order_line_id=line.id) for line in order.lineas if line.id not in matched]

    @staticmethod
    def _order_reference(text: str, order_id: str) -> str:
        return order_id if order_id.lower() in text.lower() else ""

    @staticmethod
    def _summary(extraction: dict[str, Any]) -> dict[str, int]:
        lines = extraction["lines"]; issues = extraction["issues"]
        return {"detected_lines": len(lines), "exact_matches": sum(x["match_status"] == "MATCH_EXACTO" for x in lines),
                "requires_review": sum(x["match_status"] != "MATCH_EXACTO" or bool(x["issues"]) for x in lines),
                "blocking_issues": sum(bool(x.get("blocking")) for x in issues)}

    @staticmethod
    def _issue(code: str, message: str, blocking: bool, **extra: Any) -> dict[str, Any]:
        return {"code": code, "message": message, "blocking": blocking, **extra}

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or "").lower()).encode("ascii", "ignore").decode("ascii")
        return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())

    @staticmethod
    def _capture(text: str, pattern: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return str(match.group(1) if match else "")

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _error(status: int, code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"ok": False, "error": {"status": status, "code": code, "message": message, **({"details": details} if details else {})}}


__all__ = ["ComprasRecepcionExtractionService"]
