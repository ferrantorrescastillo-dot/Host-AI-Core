from __future__ import annotations

import base64
import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from MODELOS.importador_inteligente_biblioteca import DocumentType
from SERVICIOS.importador_inteligente_biblioteca import (
    ImportDocumentService,
    RuleBasedDocumentClassifier,
)


RECIPE_TEXT = """Receta: Salsa verde
Rendimiento: 4 raciones
Ingredientes:
Perejil: 0.1 kg
Aceite: 0.2 l
Procedimiento: Triturar todos los ingredientes.
"""


def _payload(name: str = "salsa-verde.txt", text: str = RECIPE_TEXT) -> dict:
    return {
        "nombre": name,
        "tipo_mime": "text/plain",
        "contenido_base64": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "texto": text,
    }


def test_clasificador_determinista_cubre_tipos_principales() -> None:
    classifier = RuleBasedDocumentClassifier()
    cases = {
        "receta con ingredientes y procedimiento": DocumentType.RECETA,
        "escandallo coste unitario": DocumentType.ESCANDALLO,
        "ficha tecnica appcc alergenos": DocumentType.FICHA_TECNICA,
        "menu entrante primer plato": DocumentType.MENU,
        "factura base imponible": DocumentType.FACTURA,
        "albaran entrega mercancia": DocumentType.ALBARAN,
    }
    for text, expected in cases.items():
        result, confidence = classifier.classify(filename="documento.txt", text=text)
        assert result == expected
        assert 0 <= confidence.value <= 1
        assert confidence.reason


def test_importacion_genera_solo_propuestas_y_no_conserva_documento(tmp_path: Path) -> None:
    service = ImportDocumentService(tmp_path)
    result = service.import_document(_payload())

    assert result["ok"] is True
    preview = result["importacion"]
    document = preview["documento"]
    assert document["clasificacion"]["tipo"] == "RECETA"
    assert document["contenido_almacenado"] is False
    assert preview["solo_previsualizacion"] is True
    assert preview["confirmacion_disponible"] is False
    assert preview["propuestas"]
    assert all(item["estado"] == "PENDIENTE_REVISION" for item in preview["propuestas"])
    assert all(item["persistida"] is False for item in preview["propuestas"])
    assert RECIPE_TEXT not in json.dumps(preview, ensure_ascii=False)

    import_id = document["id"]
    assert service.get_import(import_id)["importacion"] == preview
    proposals = service.get_proposals(import_id)
    assert proposals["total"] == len(preview["propuestas"])
    assert proposals["solo_previsualizacion"] is True


def test_importacion_rechaza_formato_y_controla_id_ausente(tmp_path: Path) -> None:
    service = ImportDocumentService(tmp_path)
    invalid = service.import_document(_payload("programa.exe"))
    assert invalid["error"]["code"] == "unsupported_format"
    assert invalid["error"]["status"] == 400
    assert service.get_import("NO-EXISTE")["error"]["status"] == 404
    assert service.get_proposals("NO-EXISTE")["error"]["status"] == 404


def test_http_importacion_biblioteca_post_get_y_propuestas(tmp_path: Path) -> None:
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))
    created = client.post("/api/v1/biblioteca/importaciones", json=_payload())
    assert created.status_code == 200
    body = created.json()
    assert body["ok"] is True
    assert body["modo_seguro"] is True
    assert body["datos_reales_modificados"] is False
    import_id = body["importacion"]["documento"]["id"]

    detail = client.get(f"/api/v1/biblioteca/importaciones/{import_id}")
    assert detail.status_code == 200
    assert detail.json()["importacion"]["documento"]["id"] == import_id

    proposals = client.get(f"/api/v1/biblioteca/importaciones/{import_id}/propuestas")
    assert proposals.status_code == 200
    assert proposals.json()["total"] >= 1
    assert proposals.json()["datos_reales_modificados"] is False

    missing = client.get("/api/v1/biblioteca/importaciones/NO-EXISTE")
    assert missing.status_code == 404
