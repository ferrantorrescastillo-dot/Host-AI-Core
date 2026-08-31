import json
from pathlib import Path

from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService


def _fixture(base: Path) -> None:
    db = base / "DATOS" / "db"; db.mkdir(parents=True)
    (db / "biblioteca_recetas_601.json").write_text(json.dumps({"version_modelo": "6.0.1", "recetas": [{
        "id": "REC601-000043", "codigo": "TABLA-QUESOS", "nombre": "Tabla de quesos",
        "ingredientes": ["Queso"], "cantidades": ["1 kg"], "elaboracion": "Disponer.",
        "numero_raciones": 10, "estado": "COMPLETO",
    }]}), encoding="utf-8")
    (db / "menus.json").write_text(json.dumps([{
        "menu_id": "MENU601-000010", "codigo": "MENU-BODA", "nombre": "MENU BODA",
        "modelo_biblioteca": "MENU_601", "origen_importacion": "BORONAT", "estado": "OPERATIVO",
        "estado_publicacion": "ACTIVO", "version_menu": 1, "comensales_recomendado": 100,
        "composicion": {"Otros": [
            {"tipo_referencia": "PRODUCTO", "referencia": "ART000349", "cantidad": 1, "orden": 0, "version_elaboracion": None},
            {"tipo_referencia": "RECETA", "referencia": "REC601-000043", "cantidad": 1, "orden": 1},
        ]},
        "lineas": [],
    }]), encoding="utf-8")
    for name, payload in (("biblioteca_escandallos_601.json", {"escandallos": []}), ("articulos.json", [{"codigo": "ART000349", "nombre": "Producto canónico", "unidad": "kg", "activo": True}]), ("escandallos_canonicos.json", [])):
        (db / name).write_text(json.dumps(payload), encoding="utf-8")


def test_menu601_se_lista_y_detalla_sin_convertirse_en_receta(tmp_path: Path):
    _fixture(tmp_path); before = (tmp_path / "DATOS/db/menus.json").read_bytes()
    service = MenusInteligentesService(tmp_path)
    listed = service.listar(); detail = service.obtener("MENU601-000010")
    product_line, recipe_line = detail["menu"]["secciones"][0]["elaboraciones"]
    assert [item["id"] for item in listed["menus"]] == ["MENU601-000010"]
    assert detail["menu"]["modelo_biblioteca"] == "MENU_601"
    assert product_line["tipo_referencia"] == "PRODUCTO"
    assert product_line["referencia_canonica"] == "ART000349"
    assert product_line["version_elaboracion"] is None
    assert recipe_line["tipo_referencia"] == "RECETA" and recipe_line["referencia_canonica"] == "REC601-000043"
    assert (tmp_path / "DATOS/db/menus.json").read_bytes() == before
    assert not any(item.get("id", "").startswith("MENU601") for item in service.recetas.listar(incluir_archivadas=True))


def test_receta_deriva_sus_menus_desde_repositorio_canonico(tmp_path: Path):
    _fixture(tmp_path)
    detail = BibliotecaCulinariaReadService(tmp_path).detalle("REC601-000043")["elaboracion"]
    assert detail["menus"] == [{"menu_id": "MENU601-000010", "nombre": "MENU BODA", "estado": "ACTIVO"}]


def test_linea_sin_referencia_da_error_de_dominio_legible(tmp_path: Path):
    _fixture(tmp_path)
    path = tmp_path / "DATOS/db/menus.json"
    menus = json.loads(path.read_text(encoding="utf-8"))
    menus[0]["composicion"] = {"Otros": [{"tipo_referencia": "PRODUCTO"}]}
    path.write_text(json.dumps(menus), encoding="utf-8")

    try:
        MenusInteligentesService(tmp_path).listar()
    except ValueError as exc:
        assert "MENU601-000010" in str(exc)
        assert "composicion.Otros.referencia es obligatoria" in str(exc)
    else:
        raise AssertionError("Se esperaba un error de dominio para la referencia obligatoria ausente")
