import json
from datetime import datetime
from pathlib import Path

from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.precio_referencia_web_service import PrecioReferenciaWebService


def test_referencia_web_normaliza_formato_sin_alterar_precio_ni_proveedor_real(tmp_path: Path) -> None:
    path = tmp_path / "DATOS" / "db" / "articulos.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps([{"codigo": "ART-TOMATE", "nombre": "Tomate pera", "precio": 2.30, "proveedor": "Proveedor real"}]), encoding="utf-8")
    service = PrecioReferenciaWebService(tmp_path, now_provider=lambda: datetime(2026, 8, 26, 12, 0, 0))
    context = AuthorizedExecutionContext("REQ", "CHEF", "LOCAL", ("chef",), frozenset({"articulos:write"}))
    result = {"producto": "Tomate pera", "precio_comercial": 1.75, "cantidad_formato": 500, "unidad_formato": "g", "tienda": "Tienda pública", "url": "https://example.test/tomate"}

    preview = service.preview(article_id="ART-TOMATE", result=result, context=context)
    saved = service.confirm(article_id="ART-TOMATE", result=result, preview_token=preview["preview_token"], context=context)
    repeated = service.confirm(article_id="ART-TOMATE", result=result, preview_token=preview["preview_token"], context=context)

    assert saved["referencia"]["precio_normalizado"] == 3.5
    assert saved["referencia"]["autoridad"] == "REFERENCIA_NO_REAL"
    assert saved["articulo"]["precio"] == 2.30 and saved["articulo"]["proveedor"] == "Proveedor real"
    assert saved["precio_real_modificado"] is False and saved["proveedor_real_modificado"] is False
    assert saved["lectura_posterior_verificada"] is True and repeated["idempotente"] is True


def test_referencia_manual_no_exige_url_y_no_altera_datos_reales(tmp_path: Path) -> None:
    path = tmp_path / "DATOS" / "db" / "articulos.json"; path.parent.mkdir(parents=True)
    path.write_text(json.dumps([{"codigo": "ART-CHAMP", "nombre": "Champiñones", "precio": None, "proveedor": ""}]), encoding="utf-8")
    service = PrecioReferenciaWebService(tmp_path, now_provider=lambda: datetime(2026, 8, 26, 12, 0, 0))
    context = AuthorizedExecutionContext("REQ", "CHEF", "LOCAL", ("chef",), frozenset({"articulos:write"}))
    result = {"precio_comercial": 4, "cantidad_formato": 500, "unidad_formato": "g"}

    preview = service.preview_manual(article_id="ART-CHAMP", result=result, context=context)
    saved = service.confirm_manual(article_id="ART-CHAMP", result=result, preview_token=preview["preview_token"], context=context)
    repeated = service.confirm_manual(article_id="ART-CHAMP", result=result, preview_token=preview["preview_token"], context=context)

    assert saved["referencia"]["actor_id"] == "CHEF"
    assert saved["referencia"]["tipo"] == "PRECIO_REFERENCIA_MANUAL"
    assert saved["referencia"]["origen"] == "USUARIO" and saved["referencia"]["precio_normalizado"] == 8
    assert saved["articulo"]["precio"] is None and saved["articulo"]["proveedor"] == ""
    assert saved["precio_real_modificado"] is False and saved["proveedor_real_modificado"] is False
    assert repeated["idempotente"] is True


def test_referencia_manual_conserva_token_si_cambia_el_segundo_entre_preview_y_confirmacion(tmp_path: Path) -> None:
    path = tmp_path / "DATOS" / "db" / "articulos.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps([{"codigo": "ART-CHAMP", "nombre": "Champiñones", "precio": None, "proveedor": ""}]),
        encoding="utf-8",
    )
    instants = iter((
        datetime(2026, 8, 26, 12, 0, 0),
        datetime(2026, 8, 26, 12, 0, 1),
        datetime(2026, 8, 26, 12, 0, 2),
    ))
    service = PrecioReferenciaWebService(tmp_path, now_provider=lambda: next(instants))
    context = AuthorizedExecutionContext("REQ", "CHEF", "LOCAL", ("chef",), frozenset({"articulos:write"}))
    result = {"precio_comercial": 4, "cantidad_formato": 500, "unidad_formato": "g"}

    preview = service.preview_manual(article_id="ART-CHAMP", result=result, context=context)
    saved = service.confirm_manual(
        article_id="ART-CHAMP",
        result=result,
        preview_token=preview["preview_token"],
        context=context,
    )

    assert saved["estado"] == "CONFIRMADO"
    assert saved["referencia"]["registrado_en"] == "2026-08-26T12:00:01"
    assert saved["articulo"]["precio"] is None and saved["articulo"]["proveedor"] == ""
