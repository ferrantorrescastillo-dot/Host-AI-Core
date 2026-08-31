import json
from datetime import datetime
from pathlib import Path

from SERVICIOS.articulo_documentacion_write_service import ArticuloDocumentacionWriteService, HostAIArticleProposalGenerator
from SERVICIOS.catalog_crud_write_service import CatalogCrudWriteService
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.host_ai_engine.models import HostAIEngineResponse


class FakeGenerator:
    def generate(self, **_kwargs):
        return {"familia": "Verduras", "unidad_base": "u", "observaciones": "Conservar refrigerado", "precio": 1.2, "proveedor": "X", "stock": 100}


class _Connected:
    connected = True


class CapturingEngine:
    default_provider = "OPENAI"
    _providers = {"OPENAI": _Connected()}

    def __init__(self): self.request = None
    def ejecutar(self, request):
        self.request = request
        return HostAIEngineResponse(request.request_id, request.origen, request.modulo, request.tipo_peticion, {"mensaje": json.dumps({"familia": "Bebidas", "observaciones": "Para reducciones y desglasados."})}, "OK", [], 1, "OPENAI", "gpt-5-mini")


def context() -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext("REQ", "CHEF", "LOCAL", ("chef",), frozenset({"articulos:write", "articulos:preview"}))


def test_article_ai_filters_protects_existing_and_persists_provenance(tmp_path: Path) -> None:
    path = tmp_path / "DATOS/db/articulos.json"; path.parent.mkdir(parents=True)
    path.write_text(json.dumps([{"codigo": "ART-CHAMP", "nombre": "Champiñones", "unidad_base": "kg", "precio": None, "proveedor": ""}]), encoding="utf-8")
    service = ArticuloDocumentacionWriteService(tmp_path, generator=FakeGenerator(), now_provider=lambda: datetime(2026, 8, 26, 12))
    proposal = service.proposal(article_id="ART-CHAMP")
    assert proposal["datos_propuestos_ia"] == {"familia": "Verduras", "observaciones": "Conservar refrigerado"}
    assert json.loads(path.read_text())[0].get("familia") is None
    preview = service.preview(article_id="ART-CHAMP", selected=proposal["datos_propuestos_ia"], context=context())
    assert json.loads(path.read_text())[0].get("familia") is None
    saved = service.confirm(article_id="ART-CHAMP", selected=proposal["datos_propuestos_ia"], preview_token=preview["preview_token"], context=context())
    assert saved["articulo"]["unidad_base"] == "kg"
    assert saved["articulo"]["procedencia_campos"]["familia"]["tipo"] == "IA"
    assert saved["articulo"]["procedencia_campos"]["familia"]["estado_revision"] == "PENDIENTE_REVISION"
    assert saved["lectura_posterior_verificada"] is True


def test_human_crud_replaces_current_origin_and_keeps_ai_history(tmp_path: Path) -> None:
    path = tmp_path / "DATOS/db/articulos.json"; path.parent.mkdir(parents=True)
    path.write_text(json.dumps([{"codigo": "ART-CHAMP", "nombre": "Champiñones", "familia": "Verduras", "procedencia_campos": {"familia": {"tipo": "IA"}}, "historial_procedencia": [{"campo": "familia", "origen_nuevo": "IA"}]}]), encoding="utf-8")
    service = CatalogCrudWriteService(tmp_path, now_provider=lambda: datetime(2026, 8, 26, 13))
    preview = service.preview(domain="ARTICULO", operation="MODIFICAR", entity_id="ART-CHAMP", session_id="S1", context=context(), payload={"familia": "Vegetales"})
    saved = service.confirm(preview_token=preview["preview_token"], session_id="S1", context=context())["registro"]
    assert saved["procedencia_campos"]["familia"]["tipo"] == "USUARIO"
    assert saved["historial_procedencia"][0]["origen_nuevo"] == "IA"
    assert saved["historial_procedencia"][-1]["origen_nuevo"] == "USUARIO"


def test_draft_proposal_filters_existing_and_forbidden_without_write(tmp_path: Path) -> None:
    path = tmp_path / "DATOS/db/articulos.json"; path.parent.mkdir(parents=True); path.write_text("[]", encoding="utf-8")
    service = ArticuloDocumentacionWriteService(tmp_path, generator=FakeGenerator())
    before = path.read_bytes()
    result = service.draft_proposal(draft={"nombre": "Champiñones", "unidad_base": "kg"})
    assert result["datos_propuestos_ia"] == {"familia": "Verduras", "observaciones": "Conservar refrigerado"}
    assert "unidad_base" not in result["datos_propuestos_ia"]
    assert {"precio", "proveedor", "stock"}.issubset(set(result["campos_descartados"]))
    assert path.read_bytes() == before and result["datos_reales_modificados"] is False


def test_cava_generator_receives_safe_recipe_context_and_only_requests_missing_fields(tmp_path: Path) -> None:
    engine = CapturingEngine()
    generator = HostAIArticleProposalGenerator(tmp_path, engine=engine)
    article = {"codigo": "ART-CAVA", "nombre": "Cava para cocinar", "unidad_base": "ml", "unidad_compra": "botella", "cantidad_formato": 750, "unidad_formato": "ml", "precio": 3, "proveedor": "REAL", "stock": 9}
    result = generator.generate(article=article, missing_fields=["familia", "observaciones"], allowed_fields=set(ArticuloDocumentacionWriteService.FIELDS), culinary_context={"ingrediente_original": "cava", "receta_nombre": "SALSA DE CAVA", "receta_id": "SALSA-DE-CAVA", "uso_culinario": "reducir y desglasar", "cantidad_receta": 2, "unidad_receta": "L"})

    prompt = engine.request.datos_enviados["pregunta"]
    assert result == {"familia": "Bebidas", "observaciones": "Para reducciones y desglasados."}
    for value in ["Cava para cocinar", "cava", "SALSA-DE-CAVA", "reducir y desglasar", '"cantidad_receta": 2', '"unidad_receta": "L"', '"cantidad_formato": 750', '"unidad_base": "ml"']:
        assert value in prompt
    assert '"campos_faltantes_proponibles": ["familia", "observaciones"]' in prompt
    assert all(field not in result for field in ["unidad_base", "unidad_compra", "cantidad_formato", "unidad_formato", "precio", "proveedor", "stock"])
    assert '"precio"' not in prompt and '"proveedor"' not in prompt and '"stock"' not in prompt
    assert result.telemetry == {"contexto_receta_presente": True, "ingrediente_presente": True, "campos_existentes_enviados": ["cantidad_formato", "unidad_base", "unidad_compra", "unidad_formato"], "campos_solicitados": ["familia", "observaciones"]}


def test_general_article_without_recipe_context_still_works(tmp_path: Path) -> None:
    engine = CapturingEngine(); generator = HostAIArticleProposalGenerator(tmp_path, engine=engine)
    result = generator.generate(article={"codigo": "ART-1", "nombre": "Champiñones", "unidad_base": "kg"}, missing_fields=["familia", "observaciones"], allowed_fields=set(ArticuloDocumentacionWriteService.FIELDS))
    assert result.telemetry["contexto_receta_presente"] is False
    assert result.telemetry["ingrediente_presente"] is False
    assert result.telemetry["campos_existentes_enviados"] == ["unidad_base"]


def test_article_create_persists_mixed_draft_origins(tmp_path: Path) -> None:
    path = tmp_path / "DATOS/db/articulos.json"; path.parent.mkdir(parents=True); path.write_text("[]", encoding="utf-8")
    service = CatalogCrudWriteService(tmp_path, now_provider=lambda: datetime(2026, 8, 26, 14))
    preview = service.preview(domain="ARTICULO", operation="CREAR", entity_id="", session_id="S1", context=context(), payload={"nombre": "Champiñones", "codigo": "ART-CHAMP", "unidad_base": "kg", "familia": "Setas", "cantidad_formato": 500, "unidad_formato": "g"}, field_origins={"familia": "IA", "cantidad_formato": "IA", "unidad_formato": "IA"})
    saved = service.confirm(preview_token=preview["preview_token"], session_id="S1", context=context())["registro"]
    assert saved["procedencia_campos"]["nombre"]["tipo"] == "USUARIO"
    assert saved["procedencia_campos"]["unidad_base"]["tipo"] == "USUARIO"
    assert saved["procedencia_campos"]["familia"]["tipo"] == "IA"
    assert saved["procedencia_campos"]["familia"]["estado_revision"] == "PENDIENTE_REVISION"
