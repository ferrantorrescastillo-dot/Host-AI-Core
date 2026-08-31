from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from MODELOS.hostai_import_package import hostai_import_package_json_schema
from SERVICIOS.analizador_importacion_restaurante import RestaurantDataImportAnalyzer
from SERVICIOS.hostai_import_package_adapter import PreparedImportPackageAdapter


class AIImportInterpretationError(RuntimeError):
    pass


class AIImportDocumentInterpreter:
    """Interpreta semántica documental con HostAIEngine y devuelve solo package 0.1."""

    VERSION = "AI_IMPORT_DOCUMENT_INTERPRETER_0.1"
    MAX_REGIONS = 80
    MAX_ROWS_PER_REGION = 40
    MAX_ROWS_TOTAL = 800

    def __init__(self, base_dir: Path, *, engine_factory: Callable[[Path], Any] | None = None) -> None:
        self.base_dir = Path(base_dir)
        self.engine_factory = engine_factory
        self._engine: Any = None
        self._cache: dict[str, dict[str, Any]] = {}

    def interpret(self, payload: dict[str, Any]) -> dict[str, Any]:
        structural = self._structural_document(payload)
        fingerprint = self._fingerprint(structural)
        if fingerprint in self._cache:
            return {**self._cache[fingerprint], "cache_hit": True}
        engine = self._get_engine()
        request = engine.crear_consulta(
            origen="BIBLIOTECA_IMPORTACION", modulo="IMPORTACIONES",
            tipo_peticion="INTERPRETAR_DOCUMENTO_A_HOSTAI_IMPORT_PACKAGE",
            proveedor_preferido=str(getattr(engine, "default_provider", "SIMULADO")),
            formato_entrada="json",
            datos_enviados={
                "instruccion": (
                    "Devuelve exclusivamente un objeto JSON hostai.import.package versión 0.1. "
                    "Interpreta entidades, relaciones, menús, contextos, variantes, occurrences, "
                    "ambigüedades y provenance. No incluyas IDs canónicos, stock, lotes, compras, "
                    "precios reales ni razonamiento interno. Declara incertidumbre."
                ),
                "schema_salida": hostai_import_package_json_schema(),
                "documento_estructural": structural,
                "solo_lectura": True,
            },
        )
        response = engine.ejecutar(request)
        if response.errores:
            raise AIImportInterpretationError("No he podido interpretar el archivo con IA.")
        package = self._package(response.respuesta)
        try:
            PreparedImportPackageAdapter.validate(package)
        except Exception as exc:
            raise AIImportInterpretationError("La interpretación IA no devolvió un package seguro.") from exc
        result = {
            "package": package, "fingerprint": fingerprint, "cache_hit": False,
            "usage": dict(getattr(response, "usage", {}) or {}),
            "cost_breakdown": dict(getattr(response, "cost_breakdown", {}) or {}),
            "structural_summary": structural["summary"],
        }
        self._cache[fingerprint] = result
        return result

    def _structural_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        analyzer = RestaurantDataImportAnalyzer()
        inputs = list(payload.get("archivos") or [])
        tables = []
        files = []
        rows_left = self.MAX_ROWS_TOTAL
        for item in inputs:
            name = Path(str(item.get("nombre") or "datos.xlsx")).name
            content, text = analyzer._content(item)
            parsed = analyzer._parse(name, content, text)
            files.append({"name": name, "size": len(content) or len(text.encode("utf-8")), "regions": len(parsed)})
            for table in parsed:
                if len(tables) >= self.MAX_REGIONS or rows_left <= 0:
                    break
                selected_rows = table.rows[:min(self.MAX_ROWS_PER_REGION, rows_left)]
                rows_left -= len(selected_rows)
                tables.append({
                    "file": table.source, "sheet": table.sheet, "region_id": table.region_id,
                    "range": [table.start_row, table.end_row], "header_row": table.header_row,
                    "title": table.context_title, "dimensions": table.dimensions,
                    "merged_cells": list(table.merged_cells or []), "headers": list(table.rows[0]) if table.rows else [],
                    "rows": selected_rows, "row_count": len(table.rows),
                    "deterministic_kind": table.kind, "confidence": table.confidence,
                    "deterministic_mapping": table.mapping,
                })
        return {
            "summary": {"files": len(files), "sheets": len({(x["file"], x["sheet"]) for x in tables}),
                        "regions": len(tables), "rows_sent": sum(len(x["rows"]) for x in tables)},
            "files": files, "regions": tables,
        }

    def _fingerprint(self, structural: dict[str, Any]) -> str:
        raw = json.dumps({"interpreter": self.VERSION, "schema": "0.1", "document": structural},
                         ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _package(raw: Any) -> dict[str, Any]:
        value = dict(raw or {}) if isinstance(raw, dict) else {}
        candidate: Any = value.get("package") or value.get("resultado") or value.get("mensaje") or value
        if isinstance(candidate, str):
            text = candidate.strip()
            if text.startswith("```"):
                text = text.strip("`").removeprefix("json").strip()
            try:
                candidate = json.loads(text)
            except json.JSONDecodeError as exc:
                raise AIImportInterpretationError("La IA no devolvió JSON válido.") from exc
        if not isinstance(candidate, dict):
            raise AIImportInterpretationError("La IA no devolvió un package estructurado.")
        return candidate

    def _get_engine(self) -> Any:
        if self._engine is None:
            if self.engine_factory:
                self._engine = self.engine_factory(self.base_dir)
            else:
                from SERVICIOS.host_ai_engine.service import HostAIEngine
                self._engine = HostAIEngine(self.base_dir)
        return self._engine
