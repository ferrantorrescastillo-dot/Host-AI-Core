from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import load_workbook

from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.recipe_completion_exchange_service import RecipeCompletionExchangeService
from SERVICIOS.receta_documentacion_write_service import (
    RecetaDocumentacionError,
    RecetaDocumentacionWriteService,
    classify_recipe_proposals,
)


def _context() -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext(
        "REQ-OPERATIONAL", "CHEF", "LOCAL", ("chef",), frozenset({"recetas:write"}),
    )


def _fixture(base: Path) -> Path:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    recipe = {
        "id": "REC601-000777", "codigo": "AGUA-JAMAICA", "nombre": "Agua de jamaica",
        "familia": "Bebidas", "tipo": "BEBIDA", "descripcion": "Bebida del menú de verano.",
        "numero_raciones": 0, "rendimiento": "", "unidad_rendimiento": "",
        "ingredientes": ["Flor de hibiscus", "Limón", "Azúcar"],
        "cantidades": ["0.5", "1", "1"],
        "ingredientes_estructurados": [
            {"nombre_original": "Flor de hibiscus", "cantidad": 0.5, "unidad": None},
            {"nombre_original": "Limón", "cantidad": 1, "unidad": None},
            {"nombre_original": "Azúcar", "cantidad": 1, "unidad": None},
        ],
        "elaboracion": "Infusionar, colar, endulzar y enfriar.",
        "tiempo_activo": "15 minutos", "tiempo_pasivo": "45 minutos", "tiempo_total": "",
        "conservacion": "", "alergenos": [], "observaciones": "", "fotografia": "",
        "estado": "PENDIENTE_DE_COMPLETAR", "version": 1,
        "creado_en": "2026-09-01T10:00:00", "actualizado_en": "2026-09-01T10:00:00",
        "completitud": {"campos_obligatorios_pendientes": ["Rendimiento", "Documentación"]},
        "procedencia_campos": {"descripcion": {"tipo": "DOCUMENTO"}},
    }
    recipe_path = db / "biblioteca_recetas_601.json"
    recipe_path.write_text(json.dumps({"version_modelo": "6.0.1", "recetas": [recipe]}, ensure_ascii=False), encoding="utf-8")
    (db / "biblioteca_escandallos_601.json").write_text(json.dumps({
        "version_modelo": "6.0.1", "escandallos": [{
            "id": "ESC601-000777", "codigo": "ESC-AGUA-JAMAICA", "nombre": "Agua de jamaica",
            "receta_asociada": {"id": recipe["id"], "codigo": recipe["codigo"]},
            "estado": "CON_INCIDENCIAS", "lineas": [], "otros_costes": 0,
        }], "historial_calculos": [], "simulaciones": [],
    }, ensure_ascii=False), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "ART-HIBISCUS", "nombre": "Flor de hibiscus", "precio": 10, "unidad": "kg"},
        {"codigo": "ART-LIMON", "nombre": "Limón", "precio": 2, "unidad": "u"},
        {"codigo": "ART-AZUCAR", "nombre": "Azúcar", "precio": 1, "unidad": "kg"},
    ], ensure_ascii=False), encoding="utf-8")
    (db / "menus.json").write_text(json.dumps([{
        "menu_id": "MENU601-000001", "codigo": "MENU-VERANO", "nombre": "Menú verano",
        "tipo": "Servicio de terraza", "estado": "BORRADOR", "modelo_biblioteca": "MENU_601",
        "comensales_recomendado": 10,
        "composicion": {"bebidas": [{
            "tipo_referencia": "RECETA", "referencia": recipe["id"], "cantidad": 10,
        }]},
    }], ensure_ascii=False), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = base / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")
    return recipe_path


def _proposals() -> dict[str, object]:
    return {
        "descripcion": "No debe sustituir el texto documental.",
        "tiempo_total": {"valor": "60 minutos", "origen": "CALCULADO", "confianza": 1},
        "rendimiento": {"valor": 10, "confianza": 0.9, "motivo": "El menú prevé diez servicios."},
        "unidad_rendimiento": "raciones", "numero_raciones": 10,
        "cantidad_por_racion": {"valor": 250, "unidad": "ml"},
        "produccion_maxima": 20, "personal_recomendado": 1,
        "conservacion": "Mantener refrigerada hasta revisión del responsable.",
        "tiempo_descongelacion": {
            "estado": "NO_APLICA", "confianza": 0.98,
            "motivo": "La bebida se conserva refrigerada y no se congela.",
        },
        "ingredientes_estructurados": [
            {"nombre_original": "Flor de hibiscus", "cantidad": 0.5, "unidad": "kg", "confianza": 0.85},
            {"nombre_original": "Limón", "cantidad": 1, "unidad": "u", "confianza": 0.9},
            {"nombre_original": "Azúcar", "cantidad": 1, "unidad": "kg", "conversion": {"factor": 1}},
        ],
    }


def test_agua_jamaica_contexto_precedencia_propuestas_y_cero_write(tmp_path: Path) -> None:
    recipe_path = _fixture(tmp_path)
    calls: list[dict[str, object]] = []

    class Generator:
        def generate(self, *, recipe, missing_fields, allowed_fields):
            calls.append({"recipe": recipe, "missing_fields": missing_fields, "allowed_fields": allowed_fields})
            return _proposals()

    before = recipe_path.read_bytes()
    service = RecetaDocumentacionWriteService(tmp_path, generator=Generator())
    result = service.proposal(recipe_id="REC601-000777", proposed={})

    assert calls and calls[0]["recipe"]["_contexto_completado"]["menus"][0]["tipo"] == "Servicio de terraza"
    assert calls[0]["recipe"]["_contexto_completado"]["menus"][0]["pax"] == 10
    assert "descripcion" not in result["datos_propuestos_ia"]
    assert result["datos_propuestos_ia"]["tiempo_total"] == "60 minutos"
    assert result["metadatos_propuestas"]["tiempo_total"]["origen"] == "CALCULADO"
    assert result["datos_propuestos_ia"]["ingredientes_estructurados"][0]["unidad"] == "kg"
    assert result["datos_propuestos_ia"]["ingredientes_estructurados"][0]["cantidad_normalizada"] == 0.5
    safe, critical = classify_recipe_proposals(result["datos_propuestos_ia"])
    assert set(safe) <= {"descripcion", "elaboracion", "observaciones"}
    assert {"rendimiento", "numero_raciones", "cantidad_por_racion", "produccion_maxima", "personal_recomendado", "ingredientes_estructurados"} <= set(critical)
    assert result["completitud"]["propuesta"]["porcentaje"] > result["completitud"]["documental"]["porcentaje"]
    assert result["datos_reales_modificados"] is False
    assert recipe_path.read_bytes() == before


def test_agua_jamaica_escandallo_y_ficha_provisionales_rechazo_y_confirmacion(tmp_path: Path) -> None:
    recipe_path = _fixture(tmp_path)
    service = RecetaDocumentacionWriteService(tmp_path)
    result = service.proposal(recipe_id="REC601-000777", proposed=_proposals())
    proposals = result["datos_propuestos_ia"]
    read = BibliotecaCulinariaReadService(tmp_path)
    before = recipe_path.read_bytes()

    projection = read.proyectar_provisional(
        "REC601-000777", propuestas=proposals,
        metadatos_propuestas=result["metadatos_propuestas"], completitud=result["completitud"],
    )
    rejected = read.proyectar_provisional("REC601-000777", propuestas={})

    assert projection["datos_reales_modificados"] is False and recipe_path.read_bytes() == before
    assert projection["ficha_tecnica"]["estado"] == "PROVISIONAL"
    assert projection["ficha_tecnica"]["estados_campos_operativos"]["tiempo_descongelacion"]["estado"] == "NO_APLICA"
    assert projection["ficha_tecnica"]["rendimiento"] == 10
    assert projection["escandallo"]["estado_coste"] == "PROVISIONAL"
    assert [line["coste_linea"] for line in projection["escandallo"]["lineas"]] == [5.0, 2.0, 1.0]
    assert projection["escandallo"]["coste_total"] == 8.0
    assert projection["escandallo"]["coste_por_racion"] == 0.8
    assert projection["escandallo"]["lineas_datos_propuestos"] == 3
    assert rejected["escandallo"]["coste_total"] is None

    selected = {
        key: proposals[key] for key in (
            "ingredientes_estructurados", "rendimiento", "unidad_rendimiento",
            "numero_raciones", "cantidad_por_racion", "produccion_maxima", "personal_recomendado",
            "tiempo_descongelacion",
        )
    }
    metadata = {key: result["metadatos_propuestas"][key] for key in selected}
    preview = service.preview(
        recipe_id="REC601-000777", selected=selected, overwrite_fields=[], context=_context(),
        proposal_metadata_by_field=metadata,
    )
    assert preview["datos_reales_modificados"] is False and recipe_path.read_bytes() == before
    confirmed = service.confirm(
        recipe_id="REC601-000777", selected=selected, overwrite_fields=[],
        preview_token=preview["preview_token"], context=_context(),
        proposal_metadata_by_field=metadata,
    )
    repeated = service.confirm(
        recipe_id="REC601-000777", selected=selected, overwrite_fields=[],
        preview_token=preview["preview_token"], context=_context(),
        proposal_metadata_by_field=metadata,
    )
    reread = RepositorioBibliotecaRecetas601(tmp_path).obtener("REC601-000777")
    canonical = read.detalle("REC601-000777")["elaboracion"]
    assert confirmed["lectura_posterior_verificada"] is True
    assert repeated["idempotente"] is True
    assert reread["ingredientes_estructurados"][0]["unidad"] == "kg"
    assert reread.get("tiempo_descongelacion") in (None, "")
    assert reread["estados_campos_operativos"]["tiempo_descongelacion"]["estado"] == "NO_APLICA"
    assert canonical["ficha_tecnica"]["estados_campos_operativos"]["tiempo_descongelacion"]["estado"] == "NO_APLICA"
    assert canonical["escandallo"]["coste_total"] == 8.0
    assert canonical["escandallo"]["estado_coste"] == "DISPONIBLE"


def test_stale_y_round_trip_xlsx_fisico_versionado(tmp_path: Path) -> None:
    _fixture(tmp_path)
    repository = RepositorioBibliotecaRecetas601(tmp_path)
    service = RecetaDocumentacionWriteService(tmp_path, repository=repository)
    exchange = RecipeCompletionExchangeService(tmp_path, repository=repository, recipe_service=service)
    exported = exchange.export(recipe_ids=["REC601-000777"], import_id="IMPORT-AGUA")
    workbook = load_workbook(BytesIO(base64.b64decode(exported["contenido_base64"])))
    assert dict(workbook["METADATA"].values)["version"] == "0.3"
    assert "INSTRUCCIONES" in workbook.sheetnames
    instructions = " ".join(str(cell.value or "") for row in workbook["INSTRUCCIONES"] for cell in row)
    assert "NO_APLICA" in instructions
    sheet = workbook["RECETAS"]
    headers = [cell.value for cell in sheet[1]]
    row = {name: index + 1 for index, name in enumerate(headers)}
    exported_row = {name: sheet.cell(2, column).value for name, column in row.items()}
    assert exported_row["import_id"] == "IMPORT-AGUA"
    assert json.loads(exported_row["contexto_servicio"])[0]["pax"] == 10
    assert json.loads(exported_row["contexto_servicio"])[0]["servicio"] == "Servicio de terraza"
    assert len(json.loads(exported_row["ingredientes_contexto"])) == 3
    sheet.cell(2, row["rendimiento_propuesto"], 10)
    sheet.cell(2, row["unidad_rendimiento_propuesto"], "raciones")
    sheet.cell(2, row["numero_raciones_propuesto"], 10)
    sheet.cell(2, row["cantidad_por_racion_propuesto"], json.dumps({"valor": 250, "unidad": "ml"}))
    sheet.cell(2, row["produccion_maxima_propuesto"], 20)
    sheet.cell(2, row["personal_recomendado_propuesto"], 1)
    sheet.cell(2, row["tiempo_descongelacion_propuesto"], "NO_APLICA")
    sheet.cell(2, row["ingredientes_estructurados_propuesto"], json.dumps(_proposals()["ingredientes_estructurados"], ensure_ascii=False))
    sheet.cell(2, row["metadatos_propuestas"], json.dumps({
        "rendimiento": {"origen": "CONTEXTO_INTERNO", "confianza": 0.9, "motivo": "Contexto de menú"},
        "tiempo_descongelacion": {
            "origen": "IA_PROPUESTA", "confianza": 0.9,
            "motivo": "La bebida no se congela en el proceso propuesto.",
        },
    }, ensure_ascii=False))
    sheet.cell(2, row["origen_propuesta"], "CHATGPT")
    output = BytesIO(); workbook.save(output)
    imported = exchange.import_package(
        filename="agua-completada.xlsx", content_base64=base64.b64encode(output.getvalue()).decode(),
        expected_recipe_ids=["REC601-000777"], import_id="IMPORT-AGUA",
    )
    item = imported["batch"]["resultados"][0]
    assert imported["contrato"] == {
        "format": "HOSTAI_RECIPE_COMPLETION_PACKAGE", "version": "0.3", "version_importada": "0.3",
    }
    assert item["datos_requieren_revision_individual"]["rendimiento"] == 10
    assert item["metadatos_propuestas"]["rendimiento"]["confianza"] == 0.9
    assert item["metadatos_propuestas"]["rendimiento"]["origen"] == "CONTEXTO_INTERNO"
    assert item["datos_requieren_revision_individual"]["tiempo_descongelacion"] == {"estado": "NO_APLICA"}
    assert item["metadatos_propuestas"]["tiempo_descongelacion"]["estado_campo"] == "NO_APLICA"
    assert imported["datos_reales_modificados"] is False

    proposal = service.proposal(recipe_id="REC601-000777", proposed={"rendimiento": 10})
    preview = service.preview(
        recipe_id="REC601-000777", selected=proposal["datos_propuestos_ia"],
        overwrite_fields=[], context=_context(), proposal_metadata_by_field=proposal["metadatos_propuestas"],
    )
    recipe_path = tmp_path / "DATOS" / "db" / "biblioteca_recetas_601.json"
    concurrent = json.loads(recipe_path.read_text(encoding="utf-8"))
    concurrent["recetas"][0]["actualizado_en"] = "2026-09-02T12:00:00"
    recipe_path.write_text(json.dumps(concurrent, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(RecetaDocumentacionError, match="vista previa"):
        service.confirm(
            recipe_id="REC601-000777", selected=proposal["datos_propuestos_ia"],
            overwrite_fields=[], preview_token=preview["preview_token"], context=_context(),
            proposal_metadata_by_field=proposal["metadatos_propuestas"],
        )


def test_confirmar_campo_seguro_no_exige_rendimiento_ajeno_en_borrador(tmp_path: Path) -> None:
    _fixture(tmp_path)
    service = RecetaDocumentacionWriteService(tmp_path)
    selected = {"observaciones": "Texto culinario revisado."}
    preview = service.preview(
        recipe_id="REC601-000777", selected=selected, overwrite_fields=[], context=_context(),
    )

    confirmed = service.confirm(
        recipe_id="REC601-000777", selected=selected, overwrite_fields=[],
        preview_token=preview["preview_token"], context=_context(),
    )

    assert confirmed["ok"] is True
    assert confirmed["lectura_posterior_verificada"] is True
    assert confirmed["receta"]["numero_raciones"] == 0
