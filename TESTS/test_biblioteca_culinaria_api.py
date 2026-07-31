from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService


def _write_fixture(base: Path) -> None:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    recipe = {
        "id": "REC601-000001", "codigo": "SALSA-TOMATE", "nombre": "Salsa de tomate",
        "familia": "Salsas", "categoria": "Salsas", "tipo": "AP", "descripcion": "Base culinaria",
        "numero_raciones": 10, "ingredientes": ["Tomate pera", "Sal"],
        "cantidades": ["2 kg", "20 g"], "elaboracion": "Cocer y triturar.",
        "tiempo_elaboracion": "45 min", "conservacion": "Refrigerado 3 días",
        "alergenos": [], "observaciones": "", "fotografia": "", "estado": "OPERATIVA",
        "version": 2, "creado_en": "2026-01-01", "actualizado_en": "2026-07-30",
        "ficha_tecnica": {"receta": {"elaboracion": "Cocer y triturar."}},
        "completitud": {"porcentaje": 75, "campos_obligatorios_pendientes": ["Producción máxima"]},
        "documentos_pdf": ["fichas/salsa.pdf"], "documentos_word": [], "documentos_fotografias": [],
        "menus_utilizacion": ["Menú verano"], "eventos_utilizacion": ["EVT-1"],
    }
    (db / "biblioteca_recetas_601.json").write_text(
        json.dumps({"version_modelo": "6.0.1", "fichas_tecnicas": [recipe]}), encoding="utf-8",
    )
    (db / "biblioteca_escandallos_601.json").write_text(json.dumps({
        "version_modelo": "6.0.1",
        "escandallos": [{
            "id": "ESC601-000001", "codigo": "ESC-SALSA", "nombre": "Salsa",
            "receta_asociada": {"id": "REC601-000001", "codigo": "SALSA-TOMATE"},
            "estado": "OPERATIVO", "coste_total": 8.5, "coste_por_racion": 0.85,
            "rendimiento_total": 10, "fecha_ultimo_calculo": "2026-07-29",
            "lineas": [
                {"cantidad": 2, "unidad": "kg", "precio_unitario": 4, "coste_linea": 8},
                {"cantidad": 0.02, "unidad": "kg", "precio_unitario": 25, "coste_linea": 0.5},
            ],
        }],
    }), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "ART-001", "nombre": "Tomate pera", "precio": 4, "unidad": "kg"},
        {"codigo": "ART-002", "nombre": "Sal", "precio": 0.5, "unidad": "kg"},
    ]), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = base / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")


def _write_canonical_fixture(base: Path) -> None:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos_canonicos.json").write_text(json.dumps({
        "schema_version": "1.0",
        "escandallos": [
            {
                "receta": {
                    "codigo": "REC-SALSA-ROMESCO",
                    "nombre": "A.P. Salsa romesco",
                    "rendimiento": 12,
                    "unidad_rendimiento": "raciones",
                    "ingredientes": [
                        {
                            "codigo": "ART-001", "articulo_id": "ART-001",
                            "nombre": "Tomate pera", "cantidad": 2, "unidad": "kg",
                            "merma_pct": 5, "precio_unitario": 4,
                        },
                        {"nombre": "Ingrediente heredado", "cantidad": 20, "unidad": "g"},
                    ],
                },
                "coste_total": 8.5,
            },
            {
                "receta": {
                    "codigo": "REC-CREMA-CATALANA",
                    "nombre": "Crema catalana",
                    "rendimiento": 10,
                    "unidad_rendimiento": "raciones",
                    "ingredientes": [{"nombre": "Leche", "cantidad": 1, "unidad": "l"}],
                },
                "coste_total": 0,
            },
        ],
    }, ensure_ascii=False), encoding="utf-8")
    (db / "escandallos.json").write_text(json.dumps([
        {"receta_id": "REC-LEGACY", "nombre": "La fuente legacy no debe duplicarse", "lineas": []},
    ]), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "ART-001", "nombre": "Tomate pera", "precio": 4, "unidad": "kg"},
        {"codigo": "ART-002", "nombre": "Leche", "precio": 1, "unidad": "l"},
        {"codigo": "ART-MP", "nombre": "Materia prima no elaborada", "precio": 1, "unidad": "kg"},
    ]), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = base / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")


def test_biblioteca_resumen_listado_busqueda_filtros_y_detalle(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    service = BibliotecaCulinariaReadService(tmp_path)
    summary = service.resumen()["biblioteca"]
    assert summary["total_elaboraciones"] == 1
    assert summary["sin_escandallo"] == 0
    listed = service.listar({
        "q": "tomate", "categoria": "Salsas", "tiene_receta": "true",
        "orden": "coste", "direccion": "desc", "page": "1", "page_size": "10",
    })["elaboraciones"]
    assert listed["total"] == 1
    assert listed["items"][0]["tipo"] == "Elaboración"
    detail = service.detalle("REC601-000001")["elaboracion"]
    assert detail["escandallo"]["coste_por_racion"] == 0.801
    assert detail["escandallo"]["coste_total"] == 8.01
    assert detail["escandallo"]["lineas"][0]["origen_precio"] == "catalogo_articulos"
    assert detail["receta"]["ingredientes"][0]["articulo_id"] == "ART-001"
    assert detail["documentos"][0]["tipo"] == "pdf"
    assert "AP" not in json.dumps(detail, ensure_ascii=False)


def test_biblioteca_proyecta_escandallos_canonicos_sin_incluir_articulos(tmp_path: Path) -> None:
    _write_canonical_fixture(tmp_path)
    service = BibliotecaCulinariaReadService(tmp_path)

    summary = service.resumen()["biblioteca"]
    assert summary["total_elaboraciones"] == 2
    assert summary["sin_receta"] == 0
    assert summary["sin_escandallo"] == 0
    assert summary["sin_ficha_tecnica"] == 2

    listed = service.listar({
        "q": "tomate", "tiene_receta": "true", "tiene_escandallo": "true",
        "tiene_ficha_tecnica": "false", "page": "1", "page_size": "1",
    })["elaboraciones"]
    assert listed["total"] == 1
    assert listed["total_pages"] == 1
    assert listed["items"][0]["id"] == "REC-SALSA-ROMESCO"
    assert listed["items"][0]["nombre"] == "Elaboración Salsa romesco"
    assert listed["items"][0]["coste_total"] is None
    assert listed["items"][0]["estado_coste"] == "PARCIAL"
    assert listed["items"][0]["coste_completo"] is False
    assert "sin precio" in listed["items"][0]["motivo_coste_no_disponible"]
    assert listed["items"][0]["tiene_ficha_tecnica"] is False

    all_items = service.listar({})["elaboraciones"]["items"]
    assert {item["id"] for item in all_items} == {
        "REC-SALSA-ROMESCO", "REC-CREMA-CATALANA",
    }
    assert all(item["nombre"] != "Materia prima no elaborada" for item in all_items)
    crema = next(item for item in all_items if item["id"] == "REC-CREMA-CATALANA")
    assert crema["coste_total"] == 1
    assert crema["coste_por_racion"] == 0.1
    assert crema["coste_completo"] is True


def test_biblioteca_detalle_canonico_es_estable_parcial_y_enlaza_articulo_real(tmp_path: Path) -> None:
    _write_canonical_fixture(tmp_path)
    first = BibliotecaCulinariaReadService(tmp_path).detalle("REC-SALSA-ROMESCO")["elaboracion"]
    second = BibliotecaCulinariaReadService(tmp_path).detalle("REC-SALSA-ROMESCO")["elaboracion"]

    assert first["id"] == second["id"] == "REC-SALSA-ROMESCO"
    assert first["tiene_receta"] is True
    assert first["tiene_escandallo"] is True
    assert first["tiene_ficha_tecnica"] is False
    assert first["receta"]["procedimiento"] is None
    assert first["receta"]["ingredientes"][0]["articulo_id"] == "ART-001"
    assert first["receta"]["ingredientes"][0]["codigo"] == "ART-001"
    assert first["receta"]["ingredientes"][0]["nombre_articulo"] == "Tomate pera"
    assert first["receta"]["ingredientes"][0]["unidad_base"] == "kg"
    assert first["receta"]["ingredientes"][0]["cantidad"] == 2.0
    assert first["receta"]["ingredientes"][0]["estado_relacion"] == "relacionado"
    assert first["receta"]["ingredientes"][1]["estado_relacion"] == "sin_relacionar"
    assert [
        line["nombre_original"] for line in first["escandallo"]["lineas"]
    ] == [
        line["nombre_original"] for line in first["receta"]["ingredientes"]
    ]
    assert first["escandallo"]["ingredientes_sin_coste"] == 1
    assert first["escandallo"]["ingredientes_sin_conversion"] == 0
    assert first["escandallo"]["estado_coste"] == "PARCIAL"
    assert first["escandallo"]["coste_total"] is None
    assert first["escandallo"]["coste_total_parcial"] == 8.421053
    assert first["escandallo"]["lineas"][0]["origen_precio"] == "catalogo_articulos"
    assert first["escandallo"]["lineas"][0]["coste_linea"] == 8.421053
    assert first["escandallo"]["lineas"][1]["motivo_sin_coste"] == "Artículo sin relacionar"
    assert first["ficha_tecnica"]["persistida"] is False
    assert first["ficha_tecnica"]["origen"] == "proyeccion_datos_existentes"
    assert first["ficha_tecnica"]["estado"] == "EN_CONSTRUCCION"
    assert "Procedimiento" in first["ficha_tecnica"]["campos_pendientes"]
    assert first["ficha_tecnica"]["ingredientes"] == first["receta"]["ingredientes"]
    assert first["documentos"] == []
    assert first["menus"] == []
    assert first["eventos"] == []
    assert first["produccion"] == {
        "indicaciones": {
            "produccion_minima": None,
            "produccion_maxima": None,
            "personal_recomendado": None,
            "recursos": [],
            "notas": None,
        },
        "ordenes": [],
        "necesidades": [],
        "historial": [],
    }
    assert first["historial"] == []
    assert first["tiene_produccion"] is False
    assert first["tiene_relaciones_menu_evento"] is False
    assert "Ficha técnica en construcción." in first["avisos"]
    assert "A.P" not in json.dumps(first, ensure_ascii=False)


def test_biblioteca_escandallo_reutiliza_precios_conversiones_y_no_extrae_textos(
    tmp_path: Path,
) -> None:
    _write_canonical_fixture(tmp_path)
    db = tmp_path / "DATOS" / "db"
    canonical = json.loads((db / "escandallos_canonicos.json").read_text(encoding="utf-8"))
    canonical["escandallos"][0]["receta"]["ingredientes"] = [
        {"articulo_id": "ART-KG", "nombre": "Harina", "cantidad": 500, "unidad": "g"},
        {"articulo_id": "ART-PACK", "nombre": "Huevos paquete 99,99 €", "cantidad": 1, "unidad": "u"},
        {"articulo_id": "ART-ENV", "nombre": "Mayonesa envase", "cantidad": 0.05, "unidad": "kg"},
        {"articulo_id": "ART-NOUNIT", "nombre": "Producto sin unidad 7,50 €", "cantidad": 1, "unidad": "kg"},
        {"articulo_id": "ART-UNIT", "nombre": "Producto incompatible", "cantidad": 1, "unidad": "kg"},
        {"articulo_id": "ART-L", "nombre": "Aceite", "cantidad": 2, "unidad": "l"},
        {"articulo_id": "ART-ML", "nombre": "Leche", "cantidad": 250, "unidad": "ml"},
        {"articulo_id": "ART-ZERO", "nombre": "Artículo promocional", "cantidad": 1, "unidad": "u"},
        {"nombre": "Artículo no relacionado", "cantidad": 1, "unidad": "u"},
    ]
    (db / "escandallos_canonicos.json").write_text(
        json.dumps(canonical, ensure_ascii=False), encoding="utf-8",
    )
    articles = [
        {"codigo": "ART-KG", "nombre": "Harina", "precio": 2, "unidad": "kg",
         "catalogo_maestro": {"fecha_precio": "2026-07-24"}},
        {"codigo": "ART-PACK", "nombre": "Huevos paquete 99,99 €", "precio": 12, "unidad": "u",
         "catalogo_maestro": {"unidad_compra": "paquete", "cantidad_formato": "6", "unidad_base": "u", "fecha_precio": "2026-07-24"}},
        {"codigo": "ART-ENV", "nombre": "Mayonesa envase", "precio": 11, "unidad": "kg",
         "catalogo_maestro": {"unidad_compra": "envase", "cantidad_formato": "2.2", "unidad_base": "kg", "fecha_precio": "2026-07-24"}},
        {"codigo": "ART-NOUNIT", "nombre": "Producto sin unidad 7,50 €", "precio": 7.5},
        {"codigo": "ART-UNIT", "nombre": "Producto incompatible", "precio": 3, "unidad": "u"},
        {"codigo": "ART-L", "nombre": "Aceite", "precio": 3, "unidad": "l"},
        {"codigo": "ART-ML", "nombre": "Leche", "precio": 2, "unidad": "l"},
        {"codigo": "ART-ZERO", "nombre": "Artículo promocional", "precio": 0, "unidad": "u"},
    ]
    (db / "articulos.json").write_text(json.dumps(articles, ensure_ascii=False), encoding="utf-8")

    esc = BibliotecaCulinariaReadService(tmp_path).detalle("REC-SALSA-ROMESCO")["elaboracion"]["escandallo"]
    lines = esc["lineas"]
    assert lines[0]["precio_unitario"] == 2
    assert lines[0]["precio_original"] == 2
    assert lines[0]["precio_aplicado"] == 2
    assert lines[0]["unidad_precio_original"] == "kg"
    assert lines[0]["unidad_precio_aplicado"] == "kg"
    assert lines[0]["tipo_conversion"] == "metrica"
    assert lines[0]["origen_precio"] == "catalogo_articulos"
    assert lines[0]["factor_conversion"] == 0.001
    assert lines[0]["coste_linea"] == 1
    assert lines[0]["fecha_precio"] == "2026-07-24"
    assert lines[1]["precio_unitario"] == 2
    assert lines[1]["precio_original"] == 12
    assert lines[1]["unidad_precio_original"] == "paquete"
    assert lines[1]["tipo_conversion"] == "envase"
    assert lines[1]["coste_linea"] == 2
    assert lines[2]["precio_unitario"] == 5
    assert lines[2]["coste_linea"] == 0.25
    public_article = ArticulosCatalogReadService(tmp_path).obtener("ART-NOUNIT")["articulo"]
    assert lines[3]["precio_unitario"] == public_article["precio"] == 7.5
    assert lines[3]["origen_precio"] == "catalogo_articulos"
    assert lines[3]["unidad_precio"] == "kg"
    assert lines[3]["unidad_precio_original"] is None
    assert lines[3]["tipo_conversion"] == "normalizacion_heredada"
    assert lines[3]["factor_conversion"] == 1
    assert lines[3]["coste_linea"] == 7.5
    assert lines[3]["motivo_sin_coste"] is None
    assert lines[4]["coste_linea"] is None
    assert lines[4]["precio_aplicado"] == 3
    assert lines[4]["unidad_precio_aplicado"] == "u"
    assert lines[4]["tipo_conversion"] == "no_disponible"
    assert lines[4]["motivo_sin_coste"] == "Conversión no disponible"
    assert lines[5]["factor_conversion"] == 1
    assert lines[5]["coste_linea"] == 6
    assert lines[6]["factor_conversion"] == 0.001
    assert lines[6]["coste_linea"] == 0.5
    assert lines[7]["precio_unitario"] == 0
    assert lines[7]["coste_linea"] == 0
    assert lines[7]["estado_coste"] == "DISPONIBLE"
    assert lines[8]["estado_coste"] == "ARTICULO_SIN_RELACIONAR"
    for line in lines:
        if line["coste_linea"] is not None:
            assert line["precio_aplicado"] is not None
            assert line["unidad_precio_aplicado"]
            assert line["estado_coste"] == "DISPONIBLE"
            assert line["motivo_sin_coste"] is None
    assert esc["coste_total"] is None
    assert esc["coste_total_parcial"] == 17.25
    assert esc["coste_por_racion"] is None
    assert esc["ingredientes_sin_conversion"] == 1


def test_biblioteca_detalle_sin_receta_no_inventa_contenido(tmp_path: Path) -> None:
    _write_canonical_fixture(tmp_path)
    path = tmp_path / "DATOS" / "db" / "escandallos_canonicos.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["escandallos"][0]["receta"]["ingredientes"] = []
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    detail = BibliotecaCulinariaReadService(tmp_path).detalle("REC-SALSA-ROMESCO")["elaboracion"]
    assert detail["tiene_receta"] is False
    assert detail["receta"]["ingredientes"] == []
    assert detail["receta"]["pasos"] == []
    assert detail["receta"]["procedimiento"] is None
    assert detail["ficha_tecnica"]["proceso"]["procedimiento"] is None


def test_biblioteca_sin_datos_parametros_invalidos_y_no_encontrado(tmp_path: Path) -> None:
    service = BibliotecaCulinariaReadService(tmp_path)
    assert service.resumen()["biblioteca"]["estado"] == "sin_datos"
    assert service.listar({})["elaboraciones"]["items"] == []
    assert service.listar({"page_size": "101"})["error"]["status"] == 400
    assert service.listar({"tiene_receta": "quizas"})["error"]["status"] == 400
    assert service.detalle("NO-EXISTE")["error"]["status"] == 404


def test_http_biblioteca_contratos_publicos(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))
    assert client.get("/api/v1/biblioteca").json()["biblioteca"]["total_elaboraciones"] == 1
    listed = client.get("/api/v1/biblioteca/elaboraciones?q=salsa")
    assert listed.status_code == 200
    assert listed.json()["elaboraciones"]["total"] == 1
    detail = client.get("/api/v1/biblioteca/elaboraciones/REC601-000001")
    assert detail.status_code == 200
    assert detail.json()["elaboracion"]["nombre"] == "Salsa de tomate"
    assert client.get("/api/v1/biblioteca/elaboraciones/NO-EXISTE").status_code == 404


def test_http_biblioteca_publica_fuente_canonica_real(tmp_path: Path) -> None:
    _write_canonical_fixture(tmp_path)
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))

    response = client.get("/api/v1/biblioteca/elaboraciones?q=romesco")
    assert response.status_code == 200
    assert response.json()["elaboraciones"]["items"][0]["id"] == "REC-SALSA-ROMESCO"

    detail = client.get("/api/v1/biblioteca/elaboraciones/REC-SALSA-ROMESCO")
    assert detail.status_code == 200
    assert detail.json()["elaboracion"]["receta"]["ingredientes"][0]["articulo_id"] == "ART-001"
