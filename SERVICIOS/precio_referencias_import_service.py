from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import re
from typing import Any

from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.precio_referencia_web_service import PrecioReferenciaWebError, PrecioReferenciaWebService
from SERVICIOS.clasificacion_entidad_catalogo import (
    AuditorClasificacionLegada,
    normalizar_tipo,
    requiere_precio_compra,
)


class PrecioReferenciasImportService:
    """Flujo determinista y seguro para referencias externas aportadas por el usuario."""

    def __init__(self, base_dir: Path | str, references: PrecioReferenciaWebService) -> None:
        self.base_dir = Path(base_dir).resolve(); self.references = references

    def missing_articles(self) -> dict[str, Any]:
        articles = self._articles(); recipes = self._recipe_usage()
        values = []; derived = []
        for article in articles:
            article_id = self._identity(article)
            if not article_id or article.get("precio") not in (None, ""): continue
            if not requiere_precio_compra(article):
                derived.append(self._derived_cost_state(article))
                continue
            refs = list(article.get("precios_referencia") or [])
            values.append({"article_id": article_id, "codigo": article.get("codigo") or article_id, "articulo": article.get("nombre") or "", "tipo_entidad": normalizar_tipo(article.get("tipo_entidad")), "unidad_base": article.get("unidad_base"), "unidad_compra": article.get("unidad_compra"), "cantidad_formato": article.get("cantidad_formato"), "unidad_formato": article.get("unidad_formato"), "recetas": sorted(recipes.get(article_id, set())), "usado_en_recetas": len(recipes.get(article_id, set())), "precio_real": None, "referencia": refs[-1] if refs else None, "estado": "CON_REFERENCIA" if refs else "SIN_PRECIO"})
        values.sort(key=lambda item: (str(item["articulo"]).casefold(), item["article_id"]))
        return {"ok": True, "articulos": values, "total": len(values), "costes_derivados": derived, "total_costes_derivados": len(derived), "consolidado_por": "ARTICLE_ID", "datos_reales_modificados": False, "coste_ia_usd": "0.00000000"}

    def export_text(self) -> dict[str, Any]:
        rows = self.missing_articles()["articulos"]
        lines = ["Necesito referencias actuales de precios en España para los siguientes artículos de hostelería.", "", "Devuelve una tabla con:", "article_id | artículo | producto encontrado | tienda | formato | precio | moneda | URL/fuente | fecha", "", "No inventes precios. La tienda encontrada es una referencia, no proveedor real del restaurante.", "", "Artículos:"]
        for row in rows:
            fmt = self._format(row)
            lines.append(f'{row["article_id"]} | {row["articulo"]} | unidad base {row.get("unidad_base") or "pendiente"} | formato {fmt}')
        return {"ok": True, "texto": "\n".join(lines), "total": len(rows), "coste_ia_usd": "0.00000000", "datos_reales_modificados": False}

    def migration_candidates(self) -> dict[str, Any]:
        return AuditorClasificacionLegada(self.base_dir).candidatos()

    def _derived_cost_state(self, article: dict[str, Any]) -> dict[str, Any]:
        from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService

        elaboration_id = str(article.get("elaboracion_id") or "")
        detail = BibliotecaCulinariaReadService(self.base_dir).detalle(elaboration_id)
        elaboration = dict(detail.get("elaboracion") or {}) if detail.get("ok") else {}
        costing = dict(elaboration.get("escandallo") or {})
        available = costing.get("estado_coste") == "DISPONIBLE"
        return {
            "article_id": self._identity(article),
            "articulo": str(article.get("nombre") or ""),
            "tipo_entidad": normalizar_tipo(article.get("tipo_entidad")),
            "elaboracion_id": elaboration_id,
            "origen_coste": "COSTE_DERIVADO_ELABORACION",
            "estado": "COSTE_DERIVADO_ESCANDALLO" if available else "ESCANDALLO_PENDIENTE",
            "coste_total": costing.get("coste_total") if available else None,
            "coste_por_racion": costing.get("coste_por_racion") if available else None,
        }

    def preview(self, raw: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        rows, detected = self._parse(raw)
        articles = {self._identity(item): item for item in self._articles()}
        valid = []; ambiguous = []; invalid = []
        for index, row in enumerate(rows, 1):
            article_id = str(row.get("article_id") or "").strip()
            if not article_id:
                matches = [key for key, article in articles.items() if str(article.get("nombre") or "").casefold() == str(row.get("articulo") or "").strip().casefold()]
                if len(matches) == 1: article_id = matches[0]
                elif len(matches) > 1: ambiguous.append({"fila": index, "datos": row, "motivo": "VARIAS_COINCIDENCIAS"}); continue
            if article_id not in articles: invalid.append({"fila": index, "datos": row, "motivo": "ARTICLE_ID_NO_VALIDO"}); continue
            try:
                reference = self.references.normalize_imported_candidate(row, context)
                preview = self.references.preview_imported(article_id=article_id, result=reference, context=context)
                valid.append({"fila": index, "article_id": article_id, "articulo": articles[article_id].get("nombre"), "referencia": preview["referencia_propuesta"], "preview_token": preview["preview_token"], "incluir": True})
            except PrecioReferenciaWebError as exc: invalid.append({"fila": index, "datos": row, "motivo": exc.code})
        return {"ok": True, "formato_detectado": detected, "listas": valid, "ambiguas": ambiguous, "invalidas": invalid, "resumen": {"listas": len(valid), "ambiguas": len(ambiguous), "invalidas": len(invalid)}, "requiere_confirmacion": True, "datos_reales_modificados": False, "coste_ia_usd": "0.00000000"}

    def confirm(self, rows: list[dict[str, Any]], context: AuthorizedExecutionContext) -> dict[str, Any]:
        confirmed = []
        for row in rows:
            if row.get("incluir") is False: continue
            confirmed.append(self.references.confirm_imported(article_id=str(row.get("article_id") or ""), result=dict(row.get("referencia") or {}), preview_token=str(row.get("preview_token") or ""), context=context))
        return {"ok": True, "confirmadas": len(confirmed), "resultados": confirmed, "lectura_posterior_verificada": all(item.get("lectura_posterior_verificada") for item in confirmed), "datos_reales_modificados": bool(confirmed), "coste_ia_usd": "0.00000000"}

    def _parse(self, raw: str) -> tuple[list[dict[str, Any]], str]:
        text = str(raw or "").strip()
        if not text: return [], "VACIO"
        try:
            value = json.loads(text)
            rows = value if isinstance(value, list) else value.get("rows") or value.get("articulos") if isinstance(value, dict) else []
            if isinstance(rows, list): return [self._canonical(dict(row)) for row in rows if isinstance(row, dict)], "JSON"
        except (ValueError, TypeError): pass
        if text.lstrip().startswith("|"):
            lines = [line.strip().strip("|") for line in text.splitlines() if line.strip().startswith("|")]
            lines = [line for line in lines if not re.fullmatch(r"[\s|:-]+", f"|{line}|")]
            return self._delimited(lines, "|"), "MARKDOWN"
        delimiter = "\t" if "\t" in text.splitlines()[0] else ","
        return self._delimited(text.splitlines(), delimiter), "TSV" if delimiter == "\t" else "CSV"

    def _delimited(self, lines: list[str], delimiter: str) -> list[dict[str, Any]]:
        reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delimiter, skipinitialspace=True)
        return [self._canonical(dict(row)) for row in reader]

    @staticmethod
    def _canonical(row: dict[str, Any]) -> dict[str, Any]:
        normalized = {str(key or "").strip().lower().replace(" ", "_"): value for key, value in row.items()}
        fmt = str(normalized.get("formato") or "").strip()
        match = re.search(r"([0-9]+(?:[.,][0-9]+)?)\s*(kg|g|ml|l|u)\b", fmt, re.I)
        price = str(normalized.get("precio") or normalized.get("precio_comercial") or "").replace("€", "").strip().replace(",", ".")
        return {"article_id": normalized.get("article_id") or normalized.get("codigo"), "articulo": normalized.get("artículo") or normalized.get("articulo"), "producto": normalized.get("producto_encontrado") or normalized.get("producto") or normalized.get("artículo") or normalized.get("articulo"), "tienda_referencia": normalized.get("tienda") or normalized.get("tienda_referencia"), "cantidad_formato": normalized.get("cantidad_formato") or (match.group(1).replace(",", ".") if match else None), "unidad_formato": normalized.get("unidad_formato") or (match.group(2).lower() if match else None), "formato_comercial": fmt, "precio_comercial": price, "moneda": normalized.get("moneda") or "EUR", "url": normalized.get("url/fuente") or normalized.get("url") or normalized.get("fuente"), "consultado_en": normalized.get("fecha") or normalized.get("consultado_en")}

    def _articles(self) -> list[dict[str, Any]]:
        path = self.base_dir / "DATOS" / "db" / "articulos.json"
        value = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        return [dict(item) for item in value] if isinstance(value, list) else []

    def _recipe_usage(self) -> dict[str, set[str]]:
        result: dict[str, set[str]] = {}
        for name in ("biblioteca_recetas_601.json", "biblioteca_escandallos_601.json", "escandallos_canonicos.json"):
            path = self.base_dir / "DATOS" / "db" / name
            if not path.exists(): continue
            try: value = json.loads(path.read_text(encoding="utf-8"))
            except ValueError: continue
            self._visit_usage(value, result, "")
        return result

    @classmethod
    def _visit_usage(cls, value: Any, result: dict[str, set[str]], recipe: str) -> None:
        if isinstance(value, dict):
            current = str(value.get("codigo") or value.get("receta_id") or value.get("nombre") or recipe)
            article_id = str(value.get("article_id") or value.get("articulo_id") or value.get("articulo_codigo") or "")
            if article_id: result.setdefault(article_id, set()).add(current)
            for nested in value.values(): cls._visit_usage(nested, result, current)
        elif isinstance(value, list):
            for nested in value: cls._visit_usage(nested, result, recipe)

    @staticmethod
    def _identity(article: dict[str, Any]) -> str: return str(article.get("id") or article.get("codigo") or "")
    @staticmethod
    def _format(row: dict[str, Any]) -> str:
        amount = row.get("cantidad_formato"); unit = row.get("unidad_formato")
        return f"{amount:g} {unit}" if isinstance(amount, (int, float)) and unit else f"{amount or ''} {unit or ''}".strip() or str(row.get("unidad_compra") or "pendiente")


__all__ = ["PrecioReferenciasImportService"]
