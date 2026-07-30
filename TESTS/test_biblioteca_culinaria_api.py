from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
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
    assert detail["escandallo"]["coste_por_racion"] == 0.85
    assert detail["receta"]["ingredientes"][0]["articulo_id"] == "ART-001"
    assert detail["documentos"][0]["tipo"] == "pdf"
    assert "AP" not in json.dumps(detail, ensure_ascii=False)


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
