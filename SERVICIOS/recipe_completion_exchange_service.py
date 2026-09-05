from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
from itertools import islice
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

from openpyxl import Workbook, load_workbook

from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.receta_documentacion_batch_service import RecetaDocumentacionBatchService
from SERVICIOS.receta_documentacion_write_service import (
    NO_APLICA_FIELDS,
    RECIPE_DOCUMENTATION_FIELDS,
    RecetaDocumentacionError,
    RecetaDocumentacionWriteService,
    classify_recipe_proposals,
    is_no_aplica,
    recipe_completion_fingerprint,
)


class RecipeCompletionExchangeError(RecetaDocumentacionError):
    pass


class RecipeCompletionExchangeService:
    """Contrato XLSX de propuestas externas; nunca modifica recetas."""

    FORMAT = "HOSTAI_RECIPE_COMPLETION_PACKAGE"
    VERSION = "0.3"
    SUPPORTED_VERSIONS = frozenset({"0.1", "0.2", "0.3"})
    MAX_FILE_BYTES = 10 * 1024 * 1024
    MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
    MAX_ZIP_MEMBERS = 200
    MAX_ROWS = 5000
    MAX_COLUMNS = 200
    MAX_TEXT_LENGTH = 8000
    REQUIRED_HEADERS = ("recipe_id", "recipe_fingerprint", "nombre", "origen_propuesta")
    CONTEXT_HEADERS = (
        "import_id", "contexto_documental", "ingredientes_contexto",
        "recetas_relacionadas", "datos_documentales", "datos_calculados",
        "estados_campos_operativos",
        "ingredientes", "ingredientes_estructurados", "cantidades", "unidad",
        "categoria_contexto", "texto_original", "procedencia_documental",
        "articulos_relacionados", "menus_contexto", "contexto_servicio",
        "rendimiento_contexto", "unidad_rendimiento_contexto", "raciones_contexto",
        "campos_confirmados", "propuestas_previas", "campos_pendientes",
        "campos_proponibles", "campos_requieren_revision_humana",
    )
    BOOLEAN_FIELDS = frozenset({"puede_congelarse", "puede_refrigerarse"})
    NUMBER_FIELDS = frozenset({
        "numero_raciones", "rendimiento", "produccion_maxima", "rendimiento_por_tanda", "merma",
    })
    JSON_FIELDS = frozenset({
        "ingredientes_estructurados", "cantidad_por_racion", "rendimiento_neto",
        "personal_recomendado", "recursos_necesarios",
    })
    EXTERNAL_ORIGINS = frozenset({"CHATGPT", "OPENAI_API", "OTRO_PROVEEDOR_IA", "HUMANO", "ARCHIVO_EXTERNO"})

    def __init__(
        self,
        base_dir: Path,
        *,
        repository: RepositorioBibliotecaRecetas601 | None = None,
        recipe_service: RecetaDocumentacionWriteService | None = None,
        batch_service: RecetaDocumentacionBatchService | None = None,
    ) -> None:
        self.repository = repository or RepositorioBibliotecaRecetas601(base_dir)
        self.recipe_service = recipe_service or RecetaDocumentacionWriteService(base_dir, repository=self.repository)
        self.batch_service = batch_service or RecetaDocumentacionBatchService(
            base_dir, repository=self.repository, recipe_service=self.recipe_service,
        )

    def export(
        self,
        *,
        recipe_ids: list[str],
        scope: str = "BIBLIOTECA",
        import_id: str = "",
    ) -> dict[str, Any]:
        requested = list(dict.fromkeys(str(value).strip() for value in recipe_ids if str(value).strip()))
        recipes = {self._identity(item): item for item in self.repository.listar() if self._identity(item)}
        included: list[dict[str, Any]] = []
        excluded: list[dict[str, str]] = []
        for recipe_id in requested:
            recipe = recipes.get(recipe_id)
            if not recipe:
                excluded.append({"recipe_id": recipe_id, "motivo": "RECETA_NO_EXISTE"})
            elif not self._missing(recipe):
                excluded.append({"recipe_id": recipe_id, "motivo": "YA_COMPLETA"})
            else:
                included.append(recipe)

        workbook = Workbook()
        metadata = workbook.active
        metadata.title = "METADATA"
        for key, value in (
            ("format", self.FORMAT), ("version", self.VERSION), ("scope", str(scope or "BIBLIOTECA")),
            ("exported_at", datetime.now(timezone.utc).isoformat(timespec="seconds")),
            ("import_id", str(import_id or "")), ("recipe_count", len(included)),
        ):
            metadata.append([key, value])
        instructions = workbook.create_sheet("INSTRUCCIONES")
        instructions.append(["regla", "detalle"])
        for rule, detail in (
            ("OBJETIVO", "Completar exclusivamente columnas *_propuesto usando el contexto exportado por Host AI."),
            ("IDENTIDAD", "No modificar recipe_id, recipe_fingerprint ni import_id."),
            ("SIN_ESCRITURA", "La reimportacion solo crea propuestas; Host AI exigira vista previa y confirmacion humana antes de guardar."),
            ("ESTADOS", "Use un valor cuando exista evidencia; use NO_APLICA solo cuando el concepto no corresponda a la receta; deje vacio como ultimo recurso si no puede determinarlo."),
            ("NO_APLICA", "Use el estado solo en conceptos opcionales admitidos y explique el motivo en metadatos_propuestas. Nunca invente un valor para rellenar."),
            ("TRAZABILIDAD", "En metadatos_propuestas indique por campo origen, confianza (0..1), motivo, fuente y modelo."),
            ("CONTEXTO", "Respete datos documentales y confirmados. Use menus, servicio/pax, ingredientes, articulos, formatos, conversiones, precios/proveedores y recetas relacionadas solo como evidencia para proponer."),
            ("SEGURIDAD", "No incluya formulas, macros, enlaces ni columnas de propuesta desconocidas."),
        ):
            instructions.append([rule, detail])
        sheet = workbook.create_sheet("RECETAS")
        fields = sorted(RECIPE_DOCUMENTATION_FIELDS)
        headers = [
            *self.REQUIRED_HEADERS[:3], "origen", *self.CONTEXT_HEADERS,
            *[f"{field}_actual" for field in fields],
            *[f"{field}_propuesto" for field in fields],
            "metadatos_propuestas", "origen_propuesta",
        ]
        sheet.append(headers)
        for recipe in included:
            pending = self._missing(recipe)
            recipe_id = self._identity(recipe)
            context = self.recipe_service.completion_context(recipe_id)
            values: dict[str, Any] = {
                "recipe_id": recipe_id,
                "recipe_fingerprint": recipe_completion_fingerprint(recipe),
                "nombre": recipe.get("nombre") or "",
                "origen": recipe.get("origen") or "",
                "import_id": str(import_id or ""),
                "contexto_documental": self._cell_value(context.get("contexto_documental") or {}),
                "ingredientes_contexto": self._cell_value(context.get("ingredientes_contexto") or []),
                "recetas_relacionadas": self._cell_value(context.get("recetas_relacionadas") or []),
                "datos_documentales": self._cell_value(context.get("datos_documentales") or {}),
                "datos_calculados": self._cell_value(context.get("datos_calculados") or {}),
                "estados_campos_operativos": self._cell_value(context.get("estados_campos_operativos") or {}),
                "ingredientes": self._cell_value(recipe.get("ingredientes") or []),
                "ingredientes_estructurados": self._cell_value(recipe.get("ingredientes_estructurados") or []),
                "cantidades": self._cell_value(recipe.get("cantidades") or []),
                "unidad": self._cell_value(recipe.get("unidad") or ""),
                "categoria_contexto": self._cell_value(
                    recipe.get("categoria") or recipe.get("familia") or recipe.get("tipo") or ""
                ),
                "texto_original": self._cell_value(context.get("texto_original")),
                "procedencia_documental": self._cell_value(context.get("procedencia_documental") or {}),
                "articulos_relacionados": self._cell_value(context.get("articulos_relacionados") or []),
                "menus_contexto": self._cell_value(context.get("menus") or []),
                "contexto_servicio": self._cell_value(context.get("contexto_servicio") or []),
                "rendimiento_contexto": self._cell_value(recipe.get("rendimiento")),
                "unidad_rendimiento_contexto": self._cell_value(recipe.get("unidad_rendimiento")),
                "raciones_contexto": self._cell_value(recipe.get("numero_raciones")),
                "campos_confirmados": self._cell_value(context.get("campos_confirmados") or {}),
                "propuestas_previas": self._cell_value(context.get("propuestas_previas") or {}),
                "campos_pendientes": self._cell_value(pending),
                "campos_proponibles": self._cell_value(sorted(RECIPE_DOCUMENTATION_FIELDS)),
                "campos_requieren_revision_humana": self._cell_value(
                    (recipe.get("completitud") or {}).get("campos_requieren_revision_humana") or []
                ),
                "metadatos_propuestas": "",
                "origen_propuesta": "",
            }
            for field in fields:
                values[f"{field}_actual"] = self._cell_value(recipe.get(field))
                values[f"{field}_propuesto"] = ""
            sheet.append([values.get(header, "") for header in headers])
        for worksheet in workbook.worksheets:
            for row in worksheet.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str):
                        cell.data_type = "s"
        buffer = BytesIO()
        workbook.save(buffer)
        content = buffer.getvalue()
        suffix = re.sub(r"[^A-Za-z0-9_-]+", "-", str(import_id or scope or "biblioteca")).strip("-")[:50]
        return {
            "ok": True,
            "contrato": {"format": self.FORMAT, "version": self.VERSION},
            "filename": f"hostai-completado-recetas-{suffix or 'biblioteca'}.xlsx",
            "tipo_mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "contenido_base64": base64.b64encode(content).decode("ascii"),
            "recetas_solicitadas": len(requested), "recetas_exportadas": len(included),
            "recipe_ids": [self._identity(item) for item in included], "excluidas": excluded,
            "datos_reales_modificados": False,
        }

    def import_package(
        self,
        *,
        filename: str,
        content_base64: str,
        expected_recipe_ids: list[str] | None = None,
        scope: str = "BIBLIOTECA",
        import_id: str = "",
        source: str = "ARCHIVO_EXTERNO",
    ) -> dict[str, Any]:
        raw = self._decode_file(filename, content_base64)
        workbook = self._load_safe_workbook(raw)
        metadata = self._metadata(workbook)
        if metadata.get("format") != self.FORMAT:
            raise RecipeCompletionExchangeError("invalid_completion_format", "El archivo no es un paquete de completado de recetas de Host AI.")
        if metadata.get("version") not in self.SUPPORTED_VERSIONS:
            raise RecipeCompletionExchangeError("unsupported_completion_version", "La version del paquete de completado no es compatible.")
        if import_id and metadata.get("import_id") != str(import_id):
            raise RecipeCompletionExchangeError("completion_context_mismatch", "El archivo pertenece a otra importacion de origen.")
        if scope and metadata.get("scope") != str(scope):
            raise RecipeCompletionExchangeError("completion_scope_mismatch", "El ambito del archivo no coincide con el flujo actual.")
        if "RECETAS" not in workbook.sheetnames:
            raise RecipeCompletionExchangeError("missing_recipes_sheet", "El archivo no contiene la hoja RECETAS.")
        sheet = workbook["RECETAS"]
        # Algunos editores externos eliminan la dimension calculada de la hoja.
        # En modo read_only, openpyxl expone entonces max_row/max_column=None.
        # La iteracion acotada mantiene el limite sin depender de ese metadato.
        rows = list(islice(sheet.iter_rows(), self.MAX_ROWS + 2))
        if len(rows) > self.MAX_ROWS + 1 or (rows and max(len(row) for row in rows) > self.MAX_COLUMNS):
            raise RecipeCompletionExchangeError("completion_sheet_too_large", "La hoja RECETAS supera los limites permitidos.")
        if not rows:
            raise RecipeCompletionExchangeError("empty_completion_sheet", "La hoja RECETAS esta vacia.")
        headers = [str(cell.value or "").strip() for cell in rows[0]]
        if len(headers) != len(set(headers)):
            raise RecipeCompletionExchangeError("duplicate_completion_headers", "La hoja RECETAS contiene cabeceras duplicadas.")
        missing_headers = [header for header in self.REQUIRED_HEADERS if header not in headers]
        if metadata.get("version") == "0.3" and "import_id" not in headers:
            missing_headers.append("import_id")
        if missing_headers:
            raise RecipeCompletionExchangeError("invalid_completion_schema", "Faltan columnas obligatorias: " + ", ".join(missing_headers))
        formula_rows = sorted({cell.row for row in rows[1:] for cell in row if cell.data_type == "f"})
        if formula_rows:
            raise RecipeCompletionExchangeError("unsafe_formula", "El archivo contiene formulas y no puede importarse de forma segura.")

        records = [dict(zip(headers, [cell.value for cell in row])) for row in rows[1:] if any(cell.value not in (None, "") for cell in row)]
        identities = [str(record.get("recipe_id") or "").strip() for record in records]
        duplicates = {recipe_id for recipe_id, count in Counter(identities).items() if recipe_id and count > 1}
        expected = None if expected_recipe_ids is None else {
            str(value).strip() for value in expected_recipe_ids if str(value).strip()
        }
        repository_recipes = {self._identity(item): item for item in self.repository.listar() if self._identity(item)}
        proposal_columns = {f"{field}_propuesto": field for field in RECIPE_DOCUMENTATION_FIELDS}
        unknown_proposal_columns = sorted(
            header for header in headers if header.endswith("_propuesto") and header not in proposal_columns
        )
        source_default = self._source(source)
        validation_rows: list[dict[str, Any]] = []
        proposal_results: list[dict[str, Any]] = []
        field_totals = {
            "recibidos": 0, "utiles": 0, "requieren_revision": 0,
            "rechazados": 0, "bloqueados_criticos": 0,
        }
        fields_summary = {
            field: {
                "politica": "SELECCION_MASIVA" if field in {"descripcion", "elaboracion", "observaciones"}
                else "REVISION_INDIVIDUAL",
                "recibidos": 0, "utiles": 0, "requieren_revision": 0,
                "rechazados": 0, "bloqueados_criticos": 0,
            }
            for field in sorted(RECIPE_DOCUMENTATION_FIELDS)
        }

        for index, record in enumerate(records, start=2):
            recipe_id = str(record.get("recipe_id") or "").strip()
            row_result: dict[str, Any] = {"fila": index, "recipe_id": recipe_id, "estado": "RECHAZADA", "errores": [], "avisos": []}
            if not recipe_id:
                row_result["errores"].append("ID_VACIO")
            elif recipe_id in duplicates:
                row_result["errores"].append("ID_DUPLICADO")
            elif expected is not None and recipe_id not in expected:
                row_result["errores"].append("FUERA_DE_LA_SELECCION_EXPORTADA")
            row_import_id = str(record.get("import_id") or "").strip()
            if metadata.get("version") == "0.3" and row_import_id != str(metadata.get("import_id") or ""):
                row_result["errores"].append("IMPORTACION_FILA_NO_COINCIDE")
            recipe = repository_recipes.get(recipe_id)
            if recipe_id and not recipe:
                row_result["errores"].append("RECETA_NO_EXISTE")
            exported_fingerprint = str(record.get("recipe_fingerprint") or "").strip()
            if recipe and exported_fingerprint != recipe_completion_fingerprint(recipe):
                row_result["errores"].append("RECETA_CAMBIO_DESDE_EXPORTACION")

            proposed: dict[str, Any] = {}
            impossible_fields: dict[str, str] = {}
            trace_by_field: dict[str, dict[str, Any]] = {}
            supplied_metadata: dict[str, dict[str, Any]] = {}
            try:
                supplied_metadata = self._proposal_metadata(record.get("metadatos_propuestas"))
            except RecipeCompletionExchangeError as exc:
                row_result["errores"].append(f"metadatos_propuestas:{exc.code}")
            for column, field in proposal_columns.items():
                value = record.get(column)
                if value in (None, ""):
                    continue
                field_totals["recibidos"] += 1
                fields_summary[field]["recibidos"] += 1
                trace_by_field[field] = {
                    "columna": column, "campo": field, "valor_bruto": value,
                    "tipo_bruto": type(value).__name__, "estado": "RECIBIDO",
                    "politica": fields_summary[field]["politica"], "motivos": [],
                }
                impossible_reason = self._impossible_reason(value)
                if impossible_reason is not None:
                    impossible_fields[field] = impossible_reason
                    field_totals["requieren_revision"] += 1
                    fields_summary[field]["requieren_revision"] += 1
                    trace_by_field[field]["estado"] = "IMPOSIBLE_ESTIMAR_RAZONABLEMENTE"
                    trace_by_field[field]["motivos"] = [impossible_reason]
                    continue
                try:
                    if is_no_aplica(value):
                        field_metadata = supplied_metadata.get(field) or {}
                        reason = str(
                            field_metadata.get("motivo") or field_metadata.get("evidencia") or ""
                        ).strip()
                        if not reason:
                            raise RecipeCompletionExchangeError(
                                "missing_no_aplica_reason",
                                "NO_APLICA requiere un motivo o evidencia por campo.",
                            )
                    proposed[field] = self._typed_value(field, value)
                    trace_by_field[field]["valor_normalizado"] = proposed[field]
                    trace_by_field[field]["estado"] = "NORMALIZADO"
                except RecipeCompletionExchangeError as exc:
                    field_totals["rechazados"] += 1
                    fields_summary[field]["rechazados"] += 1
                    row_result["errores"].append(f"{field}:{exc.code}")
                    trace_by_field[field]["estado"] = "RECHAZADO"
                    trace_by_field[field]["motivos"] = [exc.code]
            if not trace_by_field:
                row_result["avisos"].append("SIN_PROPUESTAS_RECIBIDAS")

            fatal_row_error = any(":" not in error for error in row_result["errores"])
            if not fatal_row_error and recipe and proposed:
                proposal = self.recipe_service.proposal(recipe_id=recipe_id, proposed=proposed)
                coverage = dict(proposal.get("completitud") or {})
                resolution = dict(coverage.get("resolucion_campos") or {})
                for field, reason in impossible_fields.items():
                    resolution[field] = {
                        "estado": "IMPOSIBLE_ESTIMAR_RAZONABLEMENTE",
                        "origen": None, "motivo": reason,
                    }
                if impossible_fields:
                    coverage["resolucion_campos"] = resolution
                    coverage["pendientes"] = sorted(set(coverage.get("pendientes") or []) | set(impossible_fields))
                    coverage["production_ready_provisional"] = False
                    readiness = dict(coverage.get("production_ready") or {})
                    readiness["provisional"] = False
                    readiness["bloqueos_provisionales"] = sorted(
                        set(readiness.get("bloqueos_provisionales") or []) | set(impossible_fields)
                    )
                    coverage["production_ready"] = readiness
                    proposal["completitud"] = coverage
                clean = dict(proposal.get("datos_propuestos_ia") or {})
                blocked = list(proposal.get("propuestas_bloqueadas_revision") or [])
                safe, individual = classify_recipe_proposals(clean)
                field_totals["utiles"] += len(safe)
                field_totals["requieren_revision"] += len(individual)
                field_totals["bloqueados_criticos"] += len(blocked)
                field_totals["rechazados"] += max(0, len(proposed) - len(clean) - len(blocked))
                for field in safe:
                    fields_summary[field]["utiles"] += 1
                    trace_by_field[field]["estado"] = "ACEPTADO_SELECCION_MASIVA"
                for field in individual:
                    fields_summary[field]["requieren_revision"] += 1
                    trace_by_field[field]["estado"] = "ACEPTADO_REVISION_INDIVIDUAL"
                for entry in blocked:
                    blocked_field = str(entry.get("campo") or "")
                    if blocked_field in fields_summary:
                        fields_summary[blocked_field]["bloqueados_criticos"] += 1
                        trace_by_field[blocked_field]["estado"] = "BLOQUEADO_CONTENIDO_CRITICO"
                        trace_by_field[blocked_field]["motivos"] = list(entry.get("motivos") or [])
                for field in set(proposed) - set(clean) - {
                    str(entry.get("campo") or "") for entry in blocked
                }:
                    fields_summary[field]["rechazados"] += 1
                    reasons = [
                        str(entry.get("reason") or "RECHAZADO_POR_POLITICA")
                        for entry in proposal.get("campos_descartados") or []
                        if str(entry.get("key") or "") == field
                    ]
                    trace_by_field[field]["estado"] = "RECHAZADO"
                    trace_by_field[field]["motivos"] = reasons or ["RECHAZADO_POR_POLITICA"]
                if blocked:
                    row_result["avisos"].append("CONTENIDO_CRITICO_REQUIERE_REVISION")
                row_result["campos_utiles"] = sorted(safe)
                row_result["campos_requieren_revision_individual"] = sorted(individual)
                row_result["campos_aceptados"] = sorted(clean)
                row_result["campos_bloqueados"] = blocked
                row_result["tiene_propuestas_utiles"] = bool(safe)
                row_result["tiene_propuestas"] = bool(clean)
                row_result["requiere_revision"] = bool(individual or blocked or row_result["errores"])
                row_result["campos_imposibles_estimar"] = [
                    {"campo": field, "motivo": reason}
                    for field, reason in impossible_fields.items()
                ]
                row_result["requiere_revision"] = bool(row_result["requiere_revision"] or impossible_fields)
                if impossible_fields and row_result["estado"] == "UTIL":
                    row_result["estado"] = "UTIL_Y_REQUIERE_REVISION"
                if clean:
                    if safe and row_result["requiere_revision"]:
                        row_result["estado"] = "UTIL_Y_REQUIERE_REVISION"
                    elif safe:
                        row_result["estado"] = "UTIL"
                    else:
                        row_result["estado"] = "REQUIERE_REVISION"
                    row_source = self._source(record.get("origen_propuesta") or source_default)
                    proposal["metadatos_propuestas"] = {
                        field: self._normalized_metadata(
                            supplied_metadata.get(field), row_source=row_source,
                            fallback=(proposal.get("metadatos_propuestas") or {}).get(field),
                        )
                        for field in clean
                    }
                    row_result["origen_propuesta"] = row_source
                    proposal_results.append({
                        "recipe_id": recipe_id, "recipe_fingerprint": exported_fingerprint,
                        "proposal_result": proposal, "proposal_source": {
                            "fuente": "ARCHIVO_EXTERNO", "origen_externo": row_source,
                        },
                    })
                else:
                    row_result["avisos"].append("SIN_PROPUESTAS_UTILIZABLES")
                    row_result["estado"] = "REQUIERE_REVISION" if blocked else "RECHAZADA"
            elif not fatal_row_error:
                row_result["estado"] = "REQUIERE_REVISION"
                row_result["tiene_propuestas_utiles"] = False
                row_result["tiene_propuestas"] = False
                row_result["requiere_revision"] = True
            row_result["traza_campos"] = list(trace_by_field.values())
            validation_rows.append(row_result)

        validation = {
            "scope": str(scope or metadata.get("scope") or "BIBLIOTECA"),
            "import_id": str(import_id or metadata.get("import_id") or ""),
            "filas_recibidas": len(records),
            "filas_utiles": sum(bool(row.get("tiene_propuestas_utiles")) for row in validation_rows),
            "filas_con_propuestas": sum(bool(row.get("tiene_propuestas")) for row in validation_rows),
            "filas_requieren_revision": sum(bool(row.get("requiere_revision")) for row in validation_rows),
            "filas_rechazadas": sum(row["estado"] == "RECHAZADA" for row in validation_rows),
            "campos": field_totals,
            "campos_por_nombre": {field: counts for field, counts in fields_summary.items() if counts["recibidos"]},
            "columnas_propuesta_desconocidas": unknown_proposal_columns,
            "filas": validation_rows, "datos_reales_modificados": False,
        }
        batch = self.batch_service.start_external(
            proposal_results=proposal_results,
            validation=validation,
            import_id=str(import_id or metadata.get("import_id") or ""),
            scope=str(scope or metadata.get("scope") or "BIBLIOTECA"),
        )
        return {
            "ok": True, "contrato": {
                "format": self.FORMAT, "version": self.VERSION,
                "version_importada": metadata.get("version"),
            },
            "archivo": {
                "nombre": filename, "tamano": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            },
            "validacion": validation, "batch": batch, "datos_reales_modificados": False,
        }

    def _decode_file(self, filename: str, content_base64: str) -> bytes:
        safe_name = Path(str(filename or "")).name
        if not safe_name.lower().endswith(".xlsx") or safe_name != str(filename or ""):
            raise RecipeCompletionExchangeError("invalid_completion_filename", "Solo se admite un nombre de archivo XLSX seguro.")
        try:
            raw = base64.b64decode(str(content_base64 or ""), validate=True)
        except (ValueError, binascii.Error):
            raise RecipeCompletionExchangeError("invalid_completion_base64", "El contenido del archivo no es base64 valido.")
        if not raw or len(raw) > self.MAX_FILE_BYTES:
            raise RecipeCompletionExchangeError("invalid_completion_size", "El archivo esta vacio o supera el limite permitido.")
        return raw

    def _load_safe_workbook(self, raw: bytes):
        try:
            with ZipFile(BytesIO(raw)) as archive:
                members = archive.infolist()
                if len(members) > self.MAX_ZIP_MEMBERS or sum(item.file_size for item in members) > self.MAX_UNCOMPRESSED_BYTES:
                    raise RecipeCompletionExchangeError("unsafe_completion_archive", "El contenedor XLSX supera los limites de seguridad.")
            return load_workbook(BytesIO(raw), read_only=True, data_only=False, keep_links=False)
        except RecipeCompletionExchangeError:
            raise
        except (BadZipFile, OSError, ValueError, KeyError):
            raise RecipeCompletionExchangeError("invalid_completion_xlsx", "El archivo XLSX esta corrupto o no es valido.")

    def _metadata(self, workbook) -> dict[str, str]:
        if "METADATA" not in workbook.sheetnames:
            raise RecipeCompletionExchangeError("missing_completion_metadata", "El archivo no contiene metadatos de contrato.")
        return {
            str(row[0].value or "").strip(): str(row[1].value or "").strip()
            for row in workbook["METADATA"].iter_rows(min_col=1, max_col=2)
            if row[0].value not in (None, "")
        }

    def _typed_value(self, field: str, value: Any) -> Any:
        if isinstance(value, str) and len(value) > self.MAX_TEXT_LENGTH:
            raise RecipeCompletionExchangeError("value_too_long", "El valor supera la longitud maxima.")
        if is_no_aplica(value):
            if field not in NO_APLICA_FIELDS:
                raise RecipeCompletionExchangeError("no_aplica_no_permitido", "El campo no admite NO_APLICA.")
            return {"estado": "NO_APLICA"}
        if field in self.BOOLEAN_FIELDS:
            normalized = str(value).strip().casefold()
            if normalized in {"si", "sí", "true", "1", "yes"}:
                return True
            if normalized in {"no", "false", "0"}:
                return False
            raise RecipeCompletionExchangeError("invalid_boolean", "El valor booleano no es valido.")
        if field in self.NUMBER_FIELDS:
            try:
                number = float(str(value).replace(",", "."))
            except (TypeError, ValueError):
                raise RecipeCompletionExchangeError("invalid_number", "El numero no es valido.")
            if number <= 0:
                raise RecipeCompletionExchangeError("invalid_number", "El numero debe ser mayor que cero.")
            return int(number) if number.is_integer() else number
        if field in self.JSON_FIELDS:
            parsed = value
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                except ValueError:
                    raise RecipeCompletionExchangeError("invalid_structured_value", "El valor estructurado no es JSON valido.")
            expected = list if field in {"ingredientes_estructurados", "recursos_necesarios"} else (dict, list, int, float, str)
            if not isinstance(parsed, expected):
                raise RecipeCompletionExchangeError("invalid_structured_value", "El tipo del valor estructurado no es valido.")
            return parsed
        if field == "alergenos":
            if isinstance(value, (list, tuple)):
                return [str(item).strip() for item in value if str(item).strip()]
            text = str(value).strip()
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                except ValueError:
                    raise RecipeCompletionExchangeError("invalid_allergen_list", "La lista de alergenos no es JSON valido.")
                if not isinstance(parsed, list):
                    raise RecipeCompletionExchangeError("invalid_allergen_list", "Los alergenos deben ser una lista.")
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in re.split(r"[,;]", text) if item.strip()]
        return str(value).strip()

    @staticmethod
    def _impossible_reason(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        prefix = "PENDIENTE_IMPOSIBLE_DE_ESTIMAR"
        text = value.strip()
        if not text.upper().startswith(prefix):
            return None
        reason = text[len(prefix):].lstrip(" :-")
        return reason or "No existe base razonable para estimar este campo."

    def _proposal_metadata(self, value: Any) -> dict[str, dict[str, Any]]:
        if value in (None, ""):
            return {}
        if isinstance(value, str):
            if len(value) > self.MAX_TEXT_LENGTH:
                raise RecipeCompletionExchangeError("value_too_long", "Los metadatos superan la longitud maxima.")
            try:
                value = json.loads(value)
            except ValueError:
                raise RecipeCompletionExchangeError("invalid_proposal_metadata", "Los metadatos de propuestas no son JSON valido.")
        if not isinstance(value, dict):
            raise RecipeCompletionExchangeError("invalid_proposal_metadata", "Los metadatos de propuestas deben ser un objeto.")
        output: dict[str, dict[str, Any]] = {}
        for field, metadata in value.items():
            if field not in RECIPE_DOCUMENTATION_FIELDS or not isinstance(metadata, dict):
                continue
            output[field] = dict(metadata)
        return output

    def _normalized_metadata(
        self, value: dict[str, Any] | None, *, row_source: str,
        fallback: dict[str, Any] | None,
    ) -> dict[str, Any]:
        metadata = {**dict(fallback or {}), **dict(value or {})}
        origin = str(metadata.get("origen") or (
            "CONFIRMADO" if row_source == "HUMANO" else "IA_PROPUESTA"
        )).strip().upper()
        if origin not in {
            "DOCUMENTO", "REAL", "CALCULADO", "CONTEXTO_INTERNO", "IA_PROPUESTA",
            "REFERENCIA_EXTERNA", "CONFIRMADO",
        }:
            origin = "IA_PROPUESTA"
        confidence = metadata.get("confianza")
        try:
            confidence = max(0.0, min(1.0, float(confidence))) if confidence not in (None, "") else None
        except (TypeError, ValueError):
            confidence = None
        normalized = {
            "origen": origin,
            "confianza": confidence,
            "motivo": str(metadata.get("motivo") or metadata.get("evidencia") or "Propuesta recibida en paquete externo."),
            "estado_revision": "REQUIERE_REVISION_HUMANA",
            "fuente": str(metadata.get("fuente") or "ARCHIVO_EXTERNO"),
            "url": str(metadata.get("url") or "") or None,
            "fecha": str(metadata.get("fecha") or datetime.now(timezone.utc).isoformat(timespec="seconds")),
            "modelo": str(metadata.get("modelo") or metadata.get("proveedor") or row_source),
        }
        if str(metadata.get("estado_campo") or "").upper() == "NO_APLICA":
            normalized["estado_campo"] = "NO_APLICA"
        return normalized

    def _source(self, value: Any) -> str:
        source = str(value or "ARCHIVO_EXTERNO").strip().upper()
        return source if source in self.EXTERNAL_ORIGINS else "ARCHIVO_EXTERNO"

    @staticmethod
    def _cell_value(value: Any) -> str:
        if value in (None, ""):
            return ""
        if isinstance(value, (dict, list, tuple, bool, int, float)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        return str(value)

    @staticmethod
    def _missing(recipe: dict[str, Any]) -> list[str]:
        return list((recipe.get("completitud") or {}).get("campos_obligatorios_pendientes") or [])

    @staticmethod
    def _identity(recipe: dict[str, Any]) -> str:
        return str(recipe.get("id") or recipe.get("codigo") or "")


__all__ = ["RecipeCompletionExchangeService", "RecipeCompletionExchangeError"]
