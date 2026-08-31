from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallos601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService
from SERVICIOS.motor_calculo_menus_601 import MotorCalculoMenus601
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


def _seed_canonical(base_dir: Path) -> str:
    db = base_dir / "DATOS" / "db"
    db.mkdir(parents=True, exist_ok=True)
    (db / "escandallos_canonicos.json").write_text(json.dumps({
        "schema_version": "1.0",
        "escandallos": [{
            "receta": {
                "codigo": "REC-ENSALADILLA-GAMBA", "nombre": "Ensaladilla de gamba",
                "rendimiento": 4, "unidad_rendimiento": "raciones",
                "ingredientes": [{"codigo": "ART-ENSALADILLA", "articulo_id": "ART-ENSALADILLA", "nombre": "Ingredientes ensaladilla", "cantidad": 1, "unidad": "kg"}],
            },
            "coste_total": 6.82,
        }, {
            "receta": {
                "codigo": "REC-CEVICHE-ANTIGUO", "nombre": "Ceviche de corvina",
                "rendimiento": 10, "unidad_rendimiento": "raciones",
                "ingredientes": [{"codigo": "ART-CORVINA", "articulo_id": "ART-CORVINA", "nombre": "Corvina", "cantidad": 1, "unidad": "kg"}],
            },
            "coste_total": 25, "coste_por_racion": 2.5,
        }],
    }, ensure_ascii=False), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "ART-ENSALADILLA", "nombre": "Ingredientes ensaladilla", "precio": 6.82, "unidad": "kg"},
        {"codigo": "ART-CORVINA", "nombre": "Corvina", "precio": 25, "unidad": "kg"},
    ]), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = base_dir / "DATOS" / "facturas"
    invoices.mkdir(parents=True, exist_ok=True)
    (invoices / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")
    return "REC-ENSALADILLA-GAMBA"


def test_crud_menu_versionado_reutiliza_biblioteca_y_costes(tmp_path: Path) -> None:
    recipe_id = _seed_canonical(tmp_path)
    service = MenusInteligentesService(tmp_path)

    created = service.crear(_payload(recipe_id))
    assert created["ok"] is True
    menu = created["menu"]
    assert menu["estado"] == "BORRADOR"
    assert menu["version"] == 1
    assert menu["coste_total"] > 0
    assert menu["coste_por_comensal"] > 0
    line = menu["secciones"][0]["elaboraciones"][0]
    assert line["elaboracion_id"] == recipe_id
    assert line["coste_por_racion"] == 1.705
    assert line["coste_linea_por_comensal"] == 1.705
    assert line["coste_linea_total"] == 17.05
    assert line["estado_coste"] == "DISPONIBLE"
    assert menu["coste_completo"] is True
    assert menu["lineas_sin_coste"] == 0

    updated = service.actualizar(menu["id"], {
        **_payload(recipe_id), "version": 1, "estado": "ACTIVO", "comensales": 20,
    })
    assert updated["ok"] is True
    assert updated["menu"]["estado"] == "ACTIVO"
    assert updated["menu"]["version"] == 2
    assert updated["menu"]["coste_total"] == menu["coste_total"] * 2

    doubled_quantity = service.actualizar(menu["id"], {
        **_payload(recipe_id), "version": 2, "estado": "ACTIVO",
        "comensales": 10,
        "secciones": [{"nombre": "Principal", "elaboraciones": [{
            "elaboracion_id": recipe_id, "cantidad": 2,
        }]}],
    })
    assert doubled_quantity["menu"]["coste_por_comensal"] == 3.41
    assert doubled_quantity["menu"]["coste_total"] == 34.1

    conflict = service.actualizar(menu["id"], {**_payload(recipe_id), "version": 1})
    assert conflict["error"]["status"] == 409
    archived = service.archivar(menu["id"], {"version": 3})
    assert archived["menu"]["estado"] == "ARCHIVADO"
    assert service.listar()["total"] == 0
    assert service.listar({"incluir_archivados": "true"})["total"] == 1

    recipes = RepositorioBibliotecaRecetas601(tmp_path).listar(incluir_archivadas=True)
    assert recipes == []


def test_api_http_menus_crud_y_selector_biblioteca(tmp_path: Path) -> None:
    recipe_id = _seed_canonical(tmp_path)
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))

    options = client.get("/api/v1/menus/elaboraciones")
    assert options.status_code == 200
    assert recipe_id in {item["id"] for item in options.json()["elaboraciones"]}

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


def test_menu_marca_escandallo_incompleto_sin_convertirlo_en_cero(tmp_path: Path) -> None:
    recipe_id = _seed(tmp_path)
    menu = MenusInteligentesService(tmp_path).crear(_payload(recipe_id))["menu"]
    line = menu["secciones"][0]["elaboraciones"][0]

    assert line["estado_coste"] == "INCOMPLETO"
    assert line["coste_por_racion"] is None
    assert line["coste_linea_por_comensal"] is None
    assert line["coste_linea_total"] is None
    assert menu["coste_completo"] is False
    assert menu["lineas_sin_coste"] == 1


def test_motor_distingue_sin_escandallo_incompleto_y_cero_real() -> None:
    class EmptyRepo:
        def obtener(self, _ref: str): return None
        def listar(self, **_kwargs): return []
        def obtener_producto(self, _ref: str): return None
        def buscar_productos(self, _query: dict): return []

    details = {
        "SIN-ESC": {"id": "SIN-ESC", "nombre": "Sin escandallo", "escandallo": None},
        "INCOMPLETO": {"id": "INCOMPLETO", "nombre": "Incompleta", "escandallo": {
            "estado_coste": "PARCIAL", "coste_por_racion": None,
            "ingredientes_sin_coste": 1, "ingredientes_sin_conversion": 0,
        }},
        "CERO": {"id": "CERO", "nombre": "Coste cero real", "escandallo": {
            "estado_coste": "DISPONIBLE", "coste_por_racion": 0,
            "ingredientes_sin_coste": 0, "ingredientes_sin_conversion": 0,
        }},
    }
    repo = EmptyRepo()
    motor = MotorCalculoMenus601(repo, repo, repo, elaboracion_resolver=details.get)
    result = motor.calcular(nombre_menu="Estados de coste", comensales=10, composicion={
        "Principal": [
            {"tipo_referencia": "RECETA", "referencia": "SIN-ESC", "cantidad": 1},
            {"tipo_referencia": "RECETA", "referencia": "INCOMPLETO", "cantidad": 1},
            {"tipo_referencia": "RECETA", "referencia": "CERO", "cantidad": 1},
        ],
    })

    assert [line["estado_coste"] for line in result["lineas"]] == [
        "SIN_COSTE", "INCOMPLETO", "DISPONIBLE",
    ]
    assert result["lineas"][0]["coste_por_racion"] is None
    assert result["lineas"][1]["coste_por_racion"] is None
    assert result["lineas"][2]["coste_por_racion"] == 0
    assert result["lineas"][2]["coste_linea_total"] == 0
    assert result["coste_completo"] is False
    assert result["lineas_sin_coste"] == 2


def test_motor_no_trata_cero_tecnico_de_rendimiento_pendiente_como_coste_real() -> None:
    receta = {
        "id": "REC-PENDIENTE", "codigo": "REC-PENDIENTE",
        "nombre": "Histórica pendiente", "estado": "PENDIENTE_DE_COMPLETAR",
        "numero_raciones": 0, "campos_pendientes_importacion": ["rendimiento"],
    }
    escandallo = {
        "id": "ESC-PENDIENTE", "codigo": "ESC-PENDIENTE",
        "nombre": "Histórica pendiente", "estado": "OPERATIVO",
        "coste_por_racion": 0,
        "receta_asociada": {"id": receta["id"], "codigo": receta["codigo"]},
    }

    class Repo:
        def obtener(self, ref: str):
            if ref in {receta["id"], receta["codigo"]}: return receta
            if ref in {escandallo["id"], escandallo["codigo"]}: return escandallo
            return None
        def listar(self, **_kwargs): return [escandallo]
        def obtener_producto(self, _ref: str): return None
        def buscar_productos(self, _query: dict): return []

    repo = Repo()
    result = MotorCalculoMenus601(repo, repo, repo).calcular(
        nombre_menu="Rendimiento pendiente", comensales=10,
        composicion={"Principal": [{
            "tipo_referencia": "RECETA", "referencia": receta["id"], "cantidad": 1,
        }]},
    )

    linea = result["lineas"][0]
    assert linea["estado_coste"] == "INCOMPLETO"
    assert linea["coste_por_racion"] is None
    assert linea["coste_linea_total"] is None
    assert linea["motivo_coste_no_disponible"] == "Pendiente de rendimiento."


def test_selector_y_menu_reutilizan_elaboracion_canonica_antigua(tmp_path: Path) -> None:
    _seed_canonical(tmp_path)
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))

    found = client.get("/api/v1/biblioteca/elaboraciones", params={
        "q": "corvina", "page": 1, "page_size": 1, "tiene_escandallo": "true",
    })
    assert found.status_code == 200
    catalog = found.json()["elaboraciones"]
    assert catalog["total"] == 1
    assert catalog["total_pages"] == 1
    assert catalog["items"][0]["id"] == "REC-CEVICHE-ANTIGUO"
    assert catalog["items"][0]["coste_por_racion"] is not None
    assert catalog["items"][0]["coste_por_racion"] == 2.5

    created = client.post("/api/v1/menus", json=_payload("REC-CEVICHE-ANTIGUO"))
    assert created.status_code == 201
    assert created.json()["menu"]["secciones"][0]["elaboraciones"][0]["elaboracion_nombre"] == "Ceviche de corvina"
    assert created.json()["menu"]["coste_por_comensal"] > 0
    assert RepositorioBibliotecaRecetas601(tmp_path).listar(incluir_archivadas=True) == []


def test_home_read_service_expone_resumen_real_de_menus(tmp_path: Path) -> None:
    recipe_id = _seed_canonical(tmp_path)
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
