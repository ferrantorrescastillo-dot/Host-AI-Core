from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from types import SimpleNamespace

from openpyxl import Workbook

from SERVICIOS.analizador_importacion_hibrido import HybridRestaurantImportAnalyzer
from SERVICIOS.analizador_importacion_restaurante import RestaurantDataImportAnalyzer
from SERVICIOS.borrador_importacion_biblioteca import (
    ArticleCandidateFinder,
    CanonicalRecipeMatcher,
)
from SERVICIOS.import_ambiguity_resolver import HostAIEngineImportAmbiguityResolver
from SERVICIOS.importador_inteligente_biblioteca import ImportDocumentService
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


def _file(name: str, content: bytes) -> dict:
    return {"nombre": name, "contenido_base64": base64.b64encode(content).decode()}


def _known_555b() -> bytes:
    book = Workbook()
    sheet = book.active
    sheet.title = "M.P PRUEBA"
    sheet.append(["FICHA TECNICA PLATO"])
    sheet.append(["ARTICULO", "Salsa histórica", "KG", 1, "€/UN"])
    sheet.append(["Naranja", None, 1, None, 2.5])
    sheet.append(["Sal", None, .01, None, .5])
    target = io.BytesIO()
    book.save(target)
    return target.getvalue()


def _known_555b_many(total: int = 7) -> bytes:
    book = Workbook()
    sheet = book.active
    sheet.title = "M.P LOTE"
    for index in range(total):
        sheet.append(["FICHA TECNICA PLATO"])
        sheet.append(["ARTICULO", f"Receta histórica {index + 1}", "KG", 1, "€/UN"])
        sheet.append([f"Ingrediente histórico {index + 1}", None, 1, None, 2.5])
        sheet.append([])
    target = io.BytesIO()
    book.save(target)
    return target.getvalue()


def test_pipeline_web_usa_555b_y_perfil_sin_write(tmp_path: Path):
    session = ImportDocumentService(tmp_path).import_document({
        "archivos": [_file("conocido.xlsx", _known_555b())]
    })["importacion"]
    analysis = session["analisis_restaurante"]
    assert analysis["resultado_hibrido"]["historico_compatible"] is True
    assert analysis["resultado_hibrido"]["candidatos_historicos"] == 1
    assert analysis["perfiles_importacion"]
    assert all(profile["persistido"] is False for profile in analysis["perfiles_importacion"])
    assert any("HISTORICO" in recipe["origenes_detector"] for recipe in analysis["recetas"])
    assert RepositorioBibliotecaRecetas601(tmp_path).listar() == []


def test_match_semantico_salsa_naranja_requiere_estructura_compatible(tmp_path: Path):
    repo = RepositorioBibliotecaRecetas601(tmp_path)
    repo.crear_ficha_tecnica({
        "nombre": "SALSA DE NARANJA", "ingredientes": ["Naranja", "Azúcar"],
        "cantidades": ["1 kg", "0.1 kg"],
        "ingredientes_estructurados": [
            {"nombre_original": "Naranja", "cantidad": 1, "unidad": "kg"},
            {"nombre_original": "Azúcar", "cantidad": .1, "unidad": "kg"},
        ], "elaboracion": "Reducir", "numero_raciones": 10, "tipo": "PRINCIPAL",
    })
    matcher = CanonicalRecipeMatcher(tmp_path)
    compatible = matcher.match({"nombre": "Salsa naranja", "ingredientes_estructurados": [
        {"nombre_original": "Naranja"}, {"nombre_original": "Azúcar"},
    ]})
    variant = matcher.match({"nombre": "Salsa naranja", "ingredientes_estructurados": [
        {"nombre_original": "Tomate"}, {"nombre_original": "Pimiento"},
    ]})
    assert compatible["accion"] == "REUTILIZAR_EXISTENTE"
    assert compatible["candidatos"][0]["coincidencia_linguistica"] is True
    assert variant["accion"] == "REQUIERE_REVISION"


def test_article_identity_uses_canonical_id_and_confirmed_recipe_relations(tmp_path: Path):
    articles = RepositorioProductosMaestro601(tmp_path)
    shallot = articles.crear_producto({
        "codigo": "ART-CHALOTA", "nombre": "Cebolla chalota", "unidad_base": "kg",
    })
    recipes = RepositorioBibliotecaRecetas601(tmp_path)
    recipes.crear_ficha_tecnica({
        "nombre": "Base confirmada", "ingredientes": ["chalota"],
        "cantidades": ["1 kg"], "ingredientes_estructurados": [{
            "nombre_original": "chalota", "cantidad": 1, "unidad": "kg",
            "article_id": shallot["codigo"],
        }],
        "elaboracion": "Pochar", "numero_raciones": 10, "tipo": "PRINCIPAL",
    })
    finder = ArticleCandidateFinder(tmp_path)

    learned = finder.find("Chalota", "kg")
    by_id = finder.find("Nombre de proveedor distinto", "kg", {
        "article_id": shallot["codigo"],
    })

    assert learned["status"] == "COINCIDENCIA_EXACTA_PROPUESTA"
    assert learned["article_id"] == shallot["codigo"]
    assert learned["evidencia_identidad"] == "RELACION_HISTORICA_CONFIRMADA"
    assert by_id["article_id"] == shallot["codigo"]
    assert by_id["evidencia_identidad"] == "IDENTIFICADOR_CANONICO"


def test_article_identity_keeps_real_ambiguity_and_new_entity_separate(tmp_path: Path):
    articles = RepositorioProductosMaestro601(tmp_path)
    articles.crear_producto({"nombre": "Nata cocina 18%", "unidad_base": "l"})
    articles.crear_producto({"nombre": "Nata montar 35%", "unidad_base": "l"})
    finder = ArticleCandidateFinder(tmp_path)

    ambiguous = finder.find("Nata", "l")
    new = finder.find("Ingrediente lunar irrepetible", "kg")

    assert ambiguous["status"] == "REVISAR_COINCIDENCIA"
    assert ambiguous["article_id"] is None
    assert len(ambiguous["candidates"]) == 2
    assert new["status"] == "SIN_RELACIONAR"
    assert new["article_id"] is None


def test_supplier_identity_reads_catalog_and_purchases_without_writing(tmp_path: Path):
    RepositorioProductosMaestro601(tmp_path)
    purchases_path = tmp_path / "DATOS" / "db" / "compras_proveedores.json"
    purchases_path.write_text(json.dumps([{
        "id": "PROVCMP-EXISTENTE", "nombre": "Proveedor de Compras", "estado": "activo",
    }]), encoding="utf-8")

    catalog = ImportDocumentService(tmp_path)._build_catalog_draft(
        [], [{"nombre": "Proveedor de Compras"}], [],
    )

    assert catalog["proveedores"][0]["accion"] == "REUTILIZAR"
    assert catalog["proveedores"][0]["proveedor_id"] == "PROVCMP-EXISTENTE"
    assert json.loads(purchases_path.read_text(encoding="utf-8"))[0]["id"] == "PROVCMP-EXISTENTE"


def test_recipe_from_other_origin_is_reused_only_with_compatible_structure(tmp_path: Path):
    repo = RepositorioBibliotecaRecetas601(tmp_path)
    repo.crear_ficha_tecnica({
        "nombre": "Crema de calabaza", "ingredientes": ["Calabaza", "Cebolla"],
        "cantidades": ["1 kg", "0.2 kg"], "elaboracion": "Triturar",
        "numero_raciones": 10, "tipo": "PRINCIPAL",
    })
    stored = repo.listar()[0]
    matcher = CanonicalRecipeMatcher(tmp_path)

    same_entity = matcher.match({
        "nombre": "Crema calabaza", "id_origen": "OTRO-ARCHIVO-77",
        "ingredientes_estructurados": [
            {"nombre_original": "Calabaza"}, {"nombre_original": "Cebolla"},
        ],
    })
    different = matcher.match({
        "nombre": "Crema calabaza", "ingredientes_estructurados": [
            {"nombre_original": "Chocolate"}, {"nombre_original": "Nata"},
        ],
    })

    assert same_entity["accion"] == "REUTILIZAR_EXISTENTE"
    assert same_entity["entidad_existente_id"] == stored["id"]
    assert different["accion"] == "REQUIERE_REVISION"


def test_cost_sheet_without_canonical_recipe_blocks_blind_recipe_creation(tmp_path: Path):
    cost_path = tmp_path / "DATOS" / "db" / "escandallos_canonicos.json"
    cost_path.parent.mkdir(parents=True, exist_ok=True)
    cost_path.write_text(json.dumps({"schema_version": "test", "escandallos": [{
        "receta": {
            "codigo": "REC-COST-CEVICHE", "nombre": "Ceviche de corvina",
            "rendimiento": 10, "unidad_rendimiento": "u",
            "ingredientes": [{
                "codigo": "ART-CORVINA", "nombre": "Corvina", "cantidad": 1,
                "unidad": "kg", "articulo_id": "ART-CORVINA",
            }],
        },
        "coste_total": 10,
    }]}), encoding="utf-8")

    match = CanonicalRecipeMatcher(tmp_path).match({
        "nombre": "Ceviche corvina",
        "ingredientes_estructurados": [{"nombre_original": "Corvina"}],
    })

    assert match["accion"] == "REQUIERE_REVISION"
    assert match["estado"] == "EXISTE_EN_LEGACY_SIN_CANONICALIZAR"
    assert match["candidatos"][0]["tipo"] == "ESCANDALLO_SIN_RECETA_CANONICA"
    assert RepositorioBibliotecaRecetas601(tmp_path).listar() == []


class _FakeEngine:
    def __init__(self): self.calls = 0
    def crear_consulta(self, **kwargs): return kwargs
    def ejecutar(self, request):
        self.calls += 1
        return SimpleNamespace(errores=[], respuesta={"mensaje": (
            '{"tipo_region":"RECETA","nombre_candidato":"Salsa",'
            '"mapping":{"ARTICULO":"ingrediente"},"confidence":0.91}'
        )})


def test_resolver_usa_host_ai_engine_canonico_fake_y_no_escribe(tmp_path: Path):
    fake = _FakeEngine()
    resolver = HostAIEngineImportAmbiguityResolver(tmp_path, engine_factory=lambda _: fake)
    result = resolver.resolve({"titulo_contextual": "Salsa", "headers": ["ARTICULO"],
                               "filas": [{"ARTICULO": "Naranja"}]})
    assert result["tipo_region"] == "RECETA"
    assert fake.calls == 1
    assert not (tmp_path / "DATOS").exists()


class _WarningsStructural:
    def analyze(self, payload):
        warnings = [{"motivo": f"warning {index}"} for index in range(50)]
        return {
            "recetas": [], "resumen": {"ambiguedades": 52}, "dudas": {
                "precio": warnings, "relaciones": [
                    {"tipo": "REQUIERE_REVISION", "nombre": "A"},
                    {"tipo": "REQUIERE_REVISION", "nombre": "B"},
                ],
            }, "regiones_ambiguas": [],
        }


def test_warnings_tecnicos_no_incrementan_decisiones_usuario(tmp_path: Path):
    result = HybridRestaurantImportAnalyzer(tmp_path, _WarningsStructural()).analyze({
        "archivos": []
    })
    assert result["resumen"]["warnings_tecnicos"] == 50
    assert result["resumen"]["decisiones_usuario"] == 2


def test_historico_descarta_rotulo_tapa_de_menu_y_conserva_nombre_especifico():
    recipes = HybridRestaurantImportAnalyzer._recipes({"fichas": [
        {
            "accion": "CREAR", "estado": "PREPARADA", "nombre": "TAPA",
            "hoja": "M.P Menú finde", "ingredientes": [],
        },
        {
            "accion": "CREAR", "estado": "PREPARADA", "nombre": "Tapa de anchoa",
            "hoja": "M.P Menú finde", "ingredientes": [],
        },
    ]}, "escandallos.xlsx")

    assert [item["nombre"] for item in recipes] == ["Tapa de anchoa"]


def test_ia_es_opt_in_y_layout_repetido_solo_resuelve_una_vez():
    class Resolver:
        def __init__(self): self.calls = 0
        def resolve(self, region):
            self.calls += 1
            return {"tipo_region": "RECETA", "mapping": {}, "confidence": .8}
    resolver = Resolver()
    analyzer = RestaurantDataImportAnalyzer(resolver)
    region = {"nombre": "ambiguo.csv", "contenido_base64": base64.b64encode(
        b"Columna rara,Otra rara\nA,1\n"
    ).decode()}
    normal = analyzer.analyze({"archivos": [region]})
    enabled = analyzer.analyze({"archivos": [region, region], "resolver_ambiguedades_ia": True})
    assert normal["coste_ia"]["usada"] is False
    assert resolver.calls == 1
    assert enabled["coste_ia"]["ambiguedades_enviadas"] == 1


def test_pipeline_70_20_10_conserva_origen_y_deja_ambiguo_pendiente(tmp_path: Path):
    structural = (
        "Receta,Ingrediente,Cantidad,Unidad\n"
        "Receta nueva A,Tomate,1,kg\n"
        "Receta nueva B,Cebolla,1,kg\n"
    ).encode()
    ambiguous = b"Campo X,Campo Y\nvalor,1\n"
    analysis = HybridRestaurantImportAnalyzer(
        tmp_path, RestaurantDataImportAnalyzer()
    ).analyze({"archivos": [
        _file("historico.xlsx", _known_555b_many(7)),
        _file("estructural.csv", structural),
        _file("ambiguo.csv", ambiguous),
    ]})
    assert sum("HISTORICO" in item["origenes_detector"] for item in analysis["recetas"]) == 7
    assert {item["nombre"] for item in analysis["recetas"]}.issuperset(
        {"Receta nueva A", "Receta nueva B"}
    )
    assert analysis["decisiones_usuario"]
    assert analysis["coste_ia"]["usada"] is False


def test_pipeline_web_conecta_resolver_host_engine_fake_solo_con_opt_in(tmp_path: Path):
    fake = _FakeEngine()
    resolver = HostAIEngineImportAmbiguityResolver(tmp_path, engine_factory=lambda _: fake)
    payload = {"archivos": [_file("ambiguo.csv", b"Campo X,Campo Y\nvalor,1\n")]}
    service = ImportDocumentService(tmp_path, ambiguity_resolver=resolver)
    service.import_document(payload)
    assert fake.calls == 0
    enabled = service.import_document({**payload, "resolver_ambiguedades_ia": True})
    assert enabled["ok"] is True
    assert fake.calls == 1
    proposals = enabled["importacion"]["analisis_restaurante"]["propuestas_ia"]
    assert proposals and proposals[0]["status"] == "PROPUESTA_PENDIENTE_REVISION"
    assert RepositorioBibliotecaRecetas601(tmp_path).listar() == []
def test_variant_projection_collapses_exact_duplicates_and_groups_material_versions():
    def recipe(recipe_id: str, name: str, ingredient: str) -> dict:
        return {
            "id_origen": recipe_id, "nombre": name, "posible_variante": True,
            "ingredientes_estructurados": [{
                "nombre_original": ingredient, "cantidad_texto": "1", "unidad": "kg",
            }],
            "bloques_origen": [f"fixture.xlsx:Hoja:{recipe_id}"],
        }
    result = ImportDocumentService._variant_resolution([
        recipe("R1", "Patatas Bravas", "Patata"),
        recipe("R2", "patatas bravas.", "Patata"),
        recipe("R3", "PATATAS BRAVAS", "Patata"),
        recipe("R4", "Patatas Bravas", "Patata"),
        recipe("R5", "Patatas bravas", "Salsa brava"),
    ])

    assert result["apariciones"] == 5
    assert result["grupos"] == 1
    assert result["duplicados_exactos_colapsados"] == 3
    assert result["grupos_requieren_decision"] == 1
    assert result["items"][0]["versiones_estructurales"] == 2
    assert len(result["items"][0]["versiones"][0]["origenes"]) == 4


def test_variant_projection_marks_single_token_context_and_menu_without_forcing_recipe():
    items = ImportDocumentService._variant_resolution([
        {"id_origen": "T1", "nombre": "TAPA", "posible_variante": True,
         "ingredientes_estructurados": [{"nombre_original": "Croqueta"}], "bloques_origen": ["f:h:r1"]},
        {"id_origen": "T2", "nombre": "TAPA", "posible_variante": True,
         "ingredientes_estructurados": [{"nombre_original": "Ensalada"}], "bloques_origen": ["f:h:r2"]},
        {"id_origen": "M1", "nombre": "MENU CALÇOTADA", "posible_variante": True,
         "ingredientes_estructurados": [{"nombre_original": "Salsa romesco"}], "bloques_origen": ["f:h:r3"]},
        {"id_origen": "M2", "nombre": "MENU CALÇOTADA", "posible_variante": True,
         "ingredientes_estructurados": [{"nombre_original": "Butifarra"}], "bloques_origen": ["f:h:r4"]},
    ])["items"]

    by_name = {item["nombre"]: item for item in items}
    assert by_name["TAPA"]["tipo_entidad_propuesto"] == "ETIQUETA_CONTEXTO_POR_REVISAR"
    assert by_name["MENU CALÇOTADA"]["tipo_entidad_propuesto"] == "MENU_O_CONTENEDOR"
