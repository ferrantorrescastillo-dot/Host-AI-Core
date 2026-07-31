from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallos601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


def _seed(base_dir: Path) -> str:
    products = RepositorioProductosMaestro601(base_dir)
    products.crear_producto({
        "nombre": "MP ARROZ MENU WEB", "familia": "TEST", "unidad_base": "kg",
        "unidad_compra": "kg", "precio": "4", "proveedor": "PROV TEST",
        "proveedor_preferente": "PROV TEST", "fecha_precio": "2026-07-31", "iva": "10",
    })
    recipes = RepositorioBibliotecaRecetas601(base_dir)
    created = recipes.crear({
        "codigo": "REC-MENU-WEB", "nombre": "Arroz de menú", "familia": "TEST",
        "tipo": "PRINCIPAL", "numero_raciones": 10,
        "ingredientes": ["MP ARROZ MENU WEB"], "cantidades": ["1 kg"],
        "elaboracion": "Cocer.", "conservacion": "Caliente", "alergenos": [],
    })
    assert created["ok"] is True
    costing = BibliotecaEscandallos601(base_dir).generar_desde_receta(
        "REC-MENU-WEB", precio_venta_total=20,
    )
    assert costing["ok"] is True
    recipe = recipes.obtener("REC-MENU-WEB")
    assert recipe is not None
    return str(recipe.get("id") or recipe.get("codigo"))


def _payload(recipe_id: str) -> dict:
    return {
        "nombre": "Menú degustación web",
        "estado": "BORRADOR",
        "comensales": 10,
        "observaciones": "Preparado para Eventos",
        "secciones": [{
            "nombre": "Principal",
            "elaboraciones": [{"elaboracion_id": recipe_id, "cantidad": 1}],
        }],
    }


def test_crud_menu_versionado_reutiliza_biblioteca_y_costes(tmp_path: Path) -> None:
    recipe_id = _seed(tmp_path)
    service = MenusInteligentesService(tmp_path)

    created = service.crear(_payload(recipe_id))
    assert created["ok"] is True
    menu = created["menu"]
    assert menu["estado"] == "BORRADOR"
    assert menu["version"] == 1
    assert menu["coste_total"] > 0
    assert menu["coste_por_comensal"] > 0
    assert menu["secciones"][0]["elaboraciones"][0]["elaboracion_id"] == recipe_id

    updated = service.actualizar(menu["id"], {
        **_payload(recipe_id), "version": 1, "estado": "ACTIVO", "comensales": 20,
    })
    assert updated["ok"] is True
    assert updated["menu"]["estado"] == "ACTIVO"
    assert updated["menu"]["version"] == 2
    assert updated["menu"]["coste_total"] == menu["coste_total"] * 2

    conflict = service.actualizar(menu["id"], {**_payload(recipe_id), "version": 1})
    assert conflict["error"]["status"] == 409
    archived = service.archivar(menu["id"], {"version": 2})
    assert archived["menu"]["estado"] == "ARCHIVADO"
    assert service.listar()["total"] == 0
    assert service.listar({"incluir_archivados": "true"})["total"] == 1

    recipes = RepositorioBibliotecaRecetas601(tmp_path).listar(incluir_archivadas=True)
    assert len(recipes) == 1


def test_api_http_menus_crud_y_selector_biblioteca(tmp_path: Path) -> None:
    recipe_id = _seed(tmp_path)
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))

    options = client.get("/api/v1/menus/elaboraciones")
    assert options.status_code == 200
    assert options.json()["elaboraciones"][0]["id"] == recipe_id

    created = client.post("/api/v1/menus", json=_payload(recipe_id))
    assert created.status_code == 201
    menu = created.json()["menu"]
    detail = client.get(f"/api/v1/menus/{menu['id']}")
    assert detail.status_code == 200
    assert detail.json()["menu"]["coste_por_comensal"] > 0

    updated = client.patch(f"/api/v1/menus/{menu['id']}", json={
        **_payload(recipe_id), "version": 1, "estado": "ACTIVO",
    })
    assert updated.status_code == 200
    assert updated.json()["menu"]["version"] == 2
    deleted = client.request("DELETE", f"/api/v1/menus/{menu['id']}", json={"version": 2})
    assert deleted.status_code == 200
    assert deleted.json()["menu"]["estado"] == "ARCHIVADO"


def test_menu_rechaza_elaboracion_inexistente_sin_crearla(tmp_path: Path) -> None:
    service = MenusInteligentesService(tmp_path)
    result = service.crear(_payload("REC-NO-EXISTE"))
    assert result["error"]["code"] == "elaboration_not_found"
    assert RepositorioBibliotecaRecetas601(tmp_path).listar(incluir_archivadas=True) == []


def test_home_read_service_expone_resumen_real_de_menus(tmp_path: Path) -> None:
    recipe_id = _seed(tmp_path)
    created = MenusInteligentesService(tmp_path).crear(_payload(recipe_id))
    assert created["ok"] is True
    home = HostAIHomeReadService(SimpleNamespace(base_dir=tmp_path))

    module = home._leer_menus_desactualizados()

    assert module["total"] == 1
    assert module["items"][0]["id"] == created["menu"]["id"]
    assert module["items"][0]["coste_total"] > 0
    assert module["resumen"] == {
        "borradores": 1, "activos": 0, "archivados": 0, "con_incidencias": 0,
    }
