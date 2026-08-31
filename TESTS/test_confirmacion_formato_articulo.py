from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.confirmacion_formato_articulo_service import (
    ConfirmacionFormatoArticuloService,
    ErrorConfirmacionFormatoArticulo,
)
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.host_ai_escandallos_read_service import HostAIEscandallosReadService
from SERVICIOS.motor_calculo_escandallos_601 import MotorCalculoEscandallos601
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell


def _context(*scopes: str) -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext(
        request_id="REQ-FORMATO", user_id="USR-CHEF", tenant_id="TENANT-TEST",
        roles=("chef",), scopes=frozenset(scopes),
    )


def _fixture(base: Path) -> Path:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    articles = db / "articulos.json"
    articles.write_text(json.dumps([{
        "codigo": "ART-TEST",
        "nombre": "Artículo fixture",
        "precio": 0.26,
        "proveedor": "Proveedor fixture",
    }], ensure_ascii=False), encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    (db / "escandallos_canonicos.json").write_text(json.dumps({
        "schema_version": "1.0",
        "escandallos": [{"receta": {
            "codigo": "REC-CREMA-FIXTURE", "nombre": "Crema fixture",
            "rendimiento": 1, "unidad_rendimiento": "u",
            "ingredientes": [{
                "articulo_id": "ART-TEST", "nombre": "Artículo fixture",
                "cantidad": 7, "unidad": "u",
            }],
        }}],
    }, ensure_ascii=False), encoding="utf-8")
    invoices = base / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text(
        '{"registros":[]}', encoding="utf-8"
    )
    return articles


def test_contexto_interno_local_autoriza_preview_y_confirmacion_articulo_sin_relajar_parciales(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    names = (
        "HOST_AI_INTERNAL_USER_ID", "HOST_AI_INTERNAL_TENANT_ID",
        "HOST_AI_INTERNAL_ROLES", "HOST_AI_INTERNAL_SCOPES",
    )
    for name in names:
        monkeypatch.delenv(name, raising=False)
    context = AuthorizedExecutionContext.from_internal_environment(
        "REQ-LOCAL", role="chat", allow_local_default=True,
    )
    assert context.scopes == frozenset({
        "reservas:preview", "reservas:write", "articulos:preview", "articulos:write",
    })
    articles = _fixture(tmp_path)
    service = ConfirmacionFormatoArticuloService(tmp_path)
    preview = service.preview_change(
        operation="UPDATE_PRICE", article_id="ART-TEST", value="6,89",
        context=context, session_id="local-a",
    )
    assert preview["datos_reales_modificados"] is False
    confirmed = service.confirm_change(
        preview_token=preview["preview_token"], context=context, session_id="local-a",
    )
    assert confirmed["datos_reales_modificados"] is True
    assert json.loads(articles.read_text(encoding="utf-8"))[0]["precio"] == 6.89

    monkeypatch.setenv("HOST_AI_INTERNAL_ROLES", "chat")
    partial = AuthorizedExecutionContext.from_internal_environment(
        "REQ-PARTIAL", role="chat", allow_local_default=True,
    )
    assert partial.validate()[0] is False
    assert partial.scopes == frozenset()


def _args() -> dict:
    return {
        "article_id": "ART-TEST", "precio": 1.60,
        "unidad_compra": "paquete", "cantidad_formato": 6,
        "unidad_formato": "u", "cantidad_uso": 7, "unidad_uso": "u",
        "context": _context("articulos:write"),
    }


def test_preview_pack_no_persiste_y_expone_antes_propuesto_derivado(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    before = articles.read_bytes()
    preview = ConfirmacionFormatoArticuloService(tmp_path).preview(**_args())
    assert preview["antes"] == {
        "precio": 0.26, "unidad_compra": None, "cantidad_formato": None,
        "unidad_formato": None, "unidad_base": "kg",
        "unidad_base_sugerida": True,
        "estado_unidad_base": "SUGERIDA_PENDIENTE_REVISION",
    }
    assert preview["propuesto"] == {
        "precio": 1.6, "unidad_compra": "paquete", "cantidad_formato": 6.0,
        "unidad_formato": "u", "unidad_base": "u",
        "unidad_base_sugerida": False, "estado_unidad_base": "CONFIRMADA",
    }
    assert preview["derivado"]["precio_unitario"].startswith("0.266666")
    assert preview["derivado"]["uso"]["coste"].startswith("1.866666")
    assert preview["derivado"]["uso"]["presentacion"] == "1.87"
    assert preview["datos_reales_modificados"] is False
    assert articles.read_bytes() == before


def test_confirmacion_fixture_persiste_y_read_after_write_resuelve_coste(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    service = ConfirmacionFormatoArticuloService(tmp_path)
    preview = service.preview(**_args())
    result = service.execute(**_args(), preview_token=preview["preview_token"])
    assert result["datos_reales_modificados"] is True
    raw = json.loads(articles.read_text(encoding="utf-8"))[0]
    assert raw["precio"] == 1.6
    assert raw["unidad"] == "u"
    assert raw["catalogo_maestro"]["unidad_compra"] == "paquete"
    assert raw["catalogo_maestro"]["cantidad_formato"] == "6.0"
    assert raw["catalogo_maestro"]["unidad_formato"] == "u"
    assert raw["catalogo_maestro"]["unidad_base_sugerida"] is False
    assert raw["catalogo_maestro"]["actor_modificacion"] == "USR-CHEF"
    assert raw["catalogo_maestro"]["tenant_modificacion"] == "TENANT-TEST"
    assert "conversion_unidades" not in raw["catalogo_maestro"]
    history = json.loads(
        (tmp_path / "DATOS" / "facturas" / "historico_precios.json").read_text(encoding="utf-8")
    )["registros"]
    assert history[-1]["precio"] == 1.6
    assert history[-1]["unidad"] == "paquete"

    motor = MotorCalculoEscandallos601(RepositorioProductosMaestro601(tmp_path))
    direct = motor.calcular(
        nombre_escandallo="Fixture", numero_raciones=1,
        lineas_entrada=[{
            "producto_codigo": "ART-TEST", "nombre_mostrado": "Artículo fixture",
            "cantidad_neta": 7, "unidad_receta": "u",
        }],
    )["lineas"][0]
    assert direct["precio_compra_utilizado"] == 0.266667
    assert direct["unidad_precio"] == "u"
    assert direct["coste_linea"] == 1.866667

    costing = BibliotecaCulinariaReadService(tmp_path).detalle(
        "REC-CREMA-FIXTURE"
    )["elaboracion"]["escandallo"]
    line = costing["lineas"][0]
    assert line["precio_original"] == 1.6
    assert line["unidad_precio_original"] == "paquete"
    assert line["precio_aplicado"] == 0.266667
    assert line["unidad_precio_aplicado"] == "u"
    assert line["coste_linea"] == 1.866667
    assert line["estado_coste"] == "DISPONIBLE"
    assert costing["coste_total"] == 1.866667


def test_preview_obsoleto_se_rechaza_sin_sobrescribir(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    service = ConfirmacionFormatoArticuloService(tmp_path)
    preview = service.preview(**_args())
    payload = json.loads(articles.read_text(encoding="utf-8"))
    payload[0]["familia"] = "Cambio concurrente"
    articles.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ErrorConfirmacionFormatoArticulo, match="estado actual") as error:
        service.execute(**_args(), preview_token=preview["preview_token"])
    assert error.value.code == "stale_or_invalid_preview"
    assert json.loads(articles.read_text(encoding="utf-8"))[0]["precio"] == 0.26


def test_sin_scope_y_datos_incompletos_se_rechazan(tmp_path: Path) -> None:
    _fixture(tmp_path)
    service = ConfirmacionFormatoArticuloService(tmp_path)
    with pytest.raises(ErrorConfirmacionFormatoArticulo) as unauthorized:
        service.preview(**{**_args(), "context": _context("articulos:read")})
    assert unauthorized.value.code == "unauthorized"
    with pytest.raises(ErrorConfirmacionFormatoArticulo) as incomplete:
        service.preview(**{**_args(), "cantidad_formato": None})
    assert incomplete.value.code == "invalid_format_quantity"


def test_no_admite_inventar_conversion_entre_unidad_y_kg(tmp_path: Path) -> None:
    _fixture(tmp_path)
    with pytest.raises(ErrorConfirmacionFormatoArticulo) as incompatible:
        ConfirmacionFormatoArticuloService(tmp_path).preview(
            **{**_args(), "unidad_uso": "kg"}
        )
    assert incompatible.value.code == "incompatible_usage_unit"


def test_endpoint_http_real_exige_scope_y_preview_no_escribe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    articles = _fixture(tmp_path)
    before = articles.read_bytes()
    monkeypatch.setenv("HOST_AI_INTERNAL_USER_ID", "USR-CHEF")
    monkeypatch.setenv("HOST_AI_INTERNAL_TENANT_ID", "TENANT-TEST")
    monkeypatch.setenv("HOST_AI_INTERNAL_SCOPES", "articulos:write")
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))
    response = client.post("/api/v1/articulos/ART-TEST/formato/preview", json={
        "precio": 1.60, "unidad_compra": "paquete", "cantidad_formato": 6,
        "unidad_formato": "u", "cantidad_uso": 7, "unidad_uso": "u",
    })
    assert response.status_code == 200
    assert response.json()["datos_reales_modificados"] is False
    assert response.json()["derivado"]["uso"]["presentacion"] == "1.87"
    assert articles.read_bytes() == before

    monkeypatch.setenv("HOST_AI_INTERNAL_SCOPES", "articulos:read")
    denied = client.post("/api/v1/articulos/ART-TEST/formato/preview", json={
        "precio": 1.60, "unidad_compra": "paquete", "cantidad_formato": 6,
        "unidad_formato": "u",
    })
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "unauthorized"


def test_cambio_parcial_precio_preview_confirm_replay_y_auditoria(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    service = ConfirmacionFormatoArticuloService(tmp_path)
    context = _context("articulos:write")
    before = articles.read_bytes()
    preview = service.preview_change(
        operation="UPDATE_PRICE", article_id="ART-TEST", value="6,89",
        context=context, session_id="chat-a",
    )
    assert preview["antes"] == {"precio": 0.26}
    assert preview["propuesto"] == {"precio": 6.89}
    assert preview["presentation"]["changes"] == [{
        "field": "precio", "label": "Precio canónico", "before": "0.26", "after": "6.89",
    }]
    assert preview["presentation"]["notice"] == "Todavía no se ha modificado ningún dato."
    assert preview["datos_reales_modificados"] is False
    assert articles.read_bytes() == before

    confirmed = service.confirm_change(
        preview_token=preview["preview_token"], context=context, session_id="chat-a",
    )
    assert confirmed["datos_reales_modificados"] is True
    assert json.loads(articles.read_text(encoding="utf-8"))[0]["precio"] == 6.89
    replay = service.confirm_change(
        preview_token=preview["preview_token"], context=context, session_id="chat-a",
    )
    assert replay["idempotente"] is True
    audit = json.loads((tmp_path / "DATOS" / "auditoria" / "articulos.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert audit["articulo_id"] == "ART-TEST"
    assert audit["campos_modificados"] == ["precio"]
    assert "change_hash" in audit and "prompt" not in audit


def test_conversion_parcial_preserva_unidades_y_rechaza_factor_invalido(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    service = ConfirmacionFormatoArticuloService(tmp_path)
    context = _context("articulos:preview")
    before = articles.read_bytes()
    preview = service.preview_change(
        operation="UPDATE_CONVERSION", article_id="ART-TEST", value="0,005",
        unidad_origen="u", unidad_destino="kg", context=context, session_id="chat-a",
    )
    assert preview["propuesto"] == {"conversion_unidades": [{
        "tipo": "CONVERSION_FISICA", "unidad_origen": "u", "cantidad_origen": "1",
        "unidad_destino": "kg", "cantidad_destino": "0.005",
    }]}
    assert preview["presentation"]["derived"][0]["value"] == "1 u = 0.005 kg"
    assert articles.read_bytes() == before
    for invalid in (0, -1, "NaN", "Infinity"):
        with pytest.raises(ErrorConfirmacionFormatoArticulo) as error:
            service.preview_change(
                operation="UPDATE_CONVERSION", article_id="ART-TEST", value=invalid,
                unidad_origen="u", unidad_destino="kg", context=context, session_id="chat-a",
            )
        assert error.value.code == "invalid_conversion_factor"


def test_round_trip_conversion_fisica_es_compartida_por_coste_y_rendimiento(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    payload = json.loads(articles.read_text(encoding="utf-8"))
    payload[0].update({"precio": 2.0, "unidad": "kg"})
    payload[0]["catalogo_maestro"] = {
        "unidad_base": "kg", "unidad_base_sugerida": False,
    }
    articles.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    before = BibliotecaCulinariaReadService(tmp_path).detalle(
        "REC-CREMA-FIXTURE"
    )["elaboracion"]
    assert before["escandallo"]["estado_coste"] != "DISPONIBLE"
    assert before["receta"]["rendimiento_fisico_teorico"]["estado"] == "NO_CALCULABLE"

    context = _context("articulos:preview", "articulos:write")
    service = ConfirmacionFormatoArticuloService(tmp_path)
    preview = service.preview_change(
        operation="UPDATE_CONVERSION", article_id="ART-TEST", value="0.050",
        unidad_origen="u", unidad_destino="kg", context=context, session_id="cross-layer",
    )
    service.confirm_change(
        preview_token=preview["preview_token"], context=context, session_id="cross-layer",
    )

    after = BibliotecaCulinariaReadService(tmp_path).detalle(
        "REC-CREMA-FIXTURE"
    )["elaboracion"]
    assert after["escandallo"]["estado_coste"] == "DISPONIBLE"
    assert after["escandallo"]["lineas"][0]["coste_linea"] == 0.7
    theoretical = after["receta"]["rendimiento_fisico_teorico"]
    assert theoretical["estado"] == "COMPLETO"
    assert theoretical["cantidad"] == 0.35
    assert theoretical["ingredientes_excluidos"] == []


def test_cambio_articulo_otra_sesion_stale_y_descarte_no_escriben(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    service = ConfirmacionFormatoArticuloService(tmp_path)
    preview_context = _context("articulos:write")
    preview = service.preview_change(
        operation="UPDATE_PRICE", article_id="ART-TEST", value=2,
        context=preview_context, session_id="chat-a",
    )
    with pytest.raises(ErrorConfirmacionFormatoArticulo) as other:
        service.confirm_change(preview_token=preview["preview_token"], context=preview_context, session_id="chat-b")
    assert other.value.code == "invalid_preview"
    payload = json.loads(articles.read_text(encoding="utf-8"))
    payload[0]["familia"] = "Cambio concurrente"
    articles.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ErrorConfirmacionFormatoArticulo) as stale:
        service.confirm_change(preview_token=preview["preview_token"], context=preview_context, session_id="chat-a")
    assert stale.value.code == "stale_preview"

    discarded = service.preview_change(
        operation="UPDATE_PRICE", article_id="ART-TEST", value=3,
        context=preview_context, session_id="chat-a",
    )
    service.discard_change(preview_token=discarded["preview_token"], context=preview_context, session_id="chat-a")
    assert json.loads(articles.read_text(encoding="utf-8"))[0]["precio"] == 0.26


def test_chat_conversion_captura_preview_y_confirmacion_humana(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    engine = SimpleNamespace(base_dir=tmp_path)
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=engine), session_id="chat-conversion")
    shell.tool_executor.articulos_read_service = ArticulosCatalogReadService(tmp_path)
    shell.tool_executor.write_context = _context("articulos:preview", "articulos:write")
    shell.tool_executor.article_change_service = ConfirmacionFormatoArticuloService(
        tmp_path, articles=shell.tool_executor.articulos_read_service,
    )
    shell._session.acciones_economicas_contextuales = {
        "RESOLVE_MISSING_CONVERSION": {
            "context_id": "a" * 32, "articulo_id": "ART-TEST",
            "incidencia": "CONVERSION_NO_DISPONIBLE",
            "unidad_origen": "u", "unidad_destino": "kg",
        },
    }
    before = articles.read_bytes()
    question = shell.ejecutar_accion_reserva("RESOLVE_MISSING_CONVERSION", "a" * 32)
    assert "1 u" in question["mensaje"] and "kg" in question["mensaje"]
    assert "ART-TEST" not in question["mensaje"]

    preview = shell.enviar("1 unidad pesa 0,005 kg")
    assert preview["datos"]["datos_reales_modificados"] is False
    assert preview["datos"]["preview"]["derived"][0]["value"] == "1 u = 0.005 kg"
    assert "preview_token" not in preview["datos"]["preview"]
    assert articles.read_bytes() == before
    assert [a["action_id"] for a in preview["datos"]["economic_actions"]] == [
        "APPLY_PENDING_ARTICLE_CHANGE", "DISCARD_PENDING_ARTICLE_CHANGE",
    ]

    applied = shell.ejecutar_accion_reserva("APPLY_PENDING_ARTICLE_CHANGE")
    assert applied["datos"]["datos_reales_modificados"] is True
    raw = json.loads(articles.read_text(encoding="utf-8"))[0]["catalogo_maestro"]
    assert raw["conversion_unidades"] == [{
        "tipo": "CONVERSION_FISICA", "unidad_origen": "u", "cantidad_origen": "1",
        "unidad_destino": "kg", "cantidad_destino": "0.005",
    }]
    assert "unidad_compra" not in raw and "cantidad_formato" not in raw


def test_round_trip_conversion_fisica_persistencia_lectura_motor_y_detalle(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    context = _context("articulos:preview", "articulos:write")
    service = ConfirmacionFormatoArticuloService(tmp_path)
    before_detail = BibliotecaCulinariaReadService(tmp_path).detalle_coste_incompleto("REC-CREMA-FIXTURE")
    assert before_detail["estado_coste"] in {"PARCIAL", "SIN_COSTE"}
    assert before_detail["motivos"][0]["tipo"] == "CONVERSION_NO_DISPONIBLE"

    preview = service.preview_change(
        operation="UPDATE_CONVERSION", article_id="ART-TEST", value="0.005",
        unidad_origen="u", unidad_destino="kg", context=context, session_id="round-trip",
    )
    confirmed = service.confirm_change(
        preview_token=preview["preview_token"], context=context, session_id="round-trip",
    )
    assert confirmed["datos_reales_modificados"] is True

    read = ArticulosCatalogReadService(tmp_path).obtener("ART-TEST")["articulo"]
    assert read["conversion_unidades"] == preview["propuesto"]["conversion_unidades"]
    after_detail = BibliotecaCulinariaReadService(tmp_path).detalle_coste_incompleto("REC-CREMA-FIXTURE")
    assert after_detail["estado_coste"] == "DISPONIBLE"
    assert after_detail["coste_completo"] is True
    assert after_detail["motivos"] == []
    assert after_detail["coste_total"] == 0.0091
    assert articles.exists()


def _conversion_shell(tmp_path: Path, *, session_id: str = "chat-variable-weight") -> tuple[ServicioChatHostAIShell, Path]:
    articles = _fixture(tmp_path)
    payload = json.loads(articles.read_text(encoding="utf-8"))
    payload[0].update({
        "codigo": "ART000126",
        "nombre": "Chuleta lomo bajo 300-350g",
        "precio": 6.89,
    })
    articles.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    shell = ServicioChatHostAIShell(
        SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)), session_id=session_id,
    )
    shell.tool_executor.articulos_read_service = ArticulosCatalogReadService(tmp_path)
    shell.tool_executor.write_context = _context("articulos:preview", "articulos:write")
    shell.tool_executor.article_change_service = ConfirmacionFormatoArticuloService(
        tmp_path, articles=shell.tool_executor.articulos_read_service,
    )
    shell._session.captura_cambio_articulo = {
        "operation": "UPDATE_CONVERSION", "articulo_id": "ART000126",
        "nombre": "Chuleta lomo bajo 300-350g", "incidencia": "CONVERSION_NO_DISPONIBLE",
        "receta_id": "REC-TEST", "unidad_origen": "u", "unidad_destino": "kg",
    }
    return shell, articles


@pytest.mark.parametrize("answer", (
    "pesa entre 300 y 350 g",
    "de 300 a 350 gramos",
    "300-350g",
    "pesa entre 0,3 y 0,35 kg",
))
def test_chat_conversion_variable_pide_valor_exacto_sin_preview_ni_escritura(
    tmp_path: Path, answer: str,
) -> None:
    shell, articles = _conversion_shell(tmp_path)
    before = articles.read_bytes()

    response = shell.enviar(answer)

    assert response["datos"]["reason"] == "variable_physical_range"
    assert response["datos"]["economic_actions"] == []
    assert "preview" not in response["datos"]
    assert shell._session.confirmacion_articulo_pendiente == {}
    assert shell._session.captura_cambio_articulo["articulo_id"] == "ART000126"
    assert shell._session.captura_cambio_articulo["phase"] == "PHYSICAL_RANGE_CLARIFICATION"
    assert articles.read_bytes() == before


@pytest.mark.parametrize(("answer", "expected"), (
    ("usa 300 g por unidad", "1 u = 0.300 kg"),
    ("usa 325 gramos por unidad", "1 u = 0.325 kg"),
    ("usa 350 g por unidad", "1 u = 0.350 kg"),
    ("usa 1000 g por unidad", "1 u = 1 kg"),
    ("1 unidad pesa 0,35 kg", "1 u = 0.35 kg"),
    ("1 unidad pesa 0.35 kg", "1 u = 0.35 kg"),
))
def test_chat_conversion_exacta_normaliza_gramos_a_kg_con_decimal(
    tmp_path: Path, answer: str, expected: str,
) -> None:
    shell, articles = _conversion_shell(tmp_path)
    before = articles.read_bytes()

    response = shell.enviar(answer)

    preview = response["datos"]["preview"]
    assert preview["derived"][0]["value"] == expected
    assert response["datos"]["datos_reales_modificados"] is False
    assert articles.read_bytes() == before


def test_chat_conversion_variable_conserva_entidad_y_acepta_aclaracion_exacta(tmp_path: Path) -> None:
    shell, articles = _conversion_shell(tmp_path)
    before = articles.read_bytes()

    ambiguous = shell.enviar("pesa entre 300 y 350 g")
    clarified = shell.enviar("usa 325 g por unidad")

    assert ambiguous["datos"]["reason"] == "variable_physical_range"
    assert clarified["datos"]["preview"]["entity_id"] == "ART000126"
    assert clarified["datos"]["preview"]["derived"][0]["value"] == "1 u = 0.325 kg"
    assert shell._session.captura_cambio_articulo == {}
    assert articles.read_bytes() == before


def test_chat_conversion_no_infiere_peso_desde_nombre_del_articulo(tmp_path: Path) -> None:
    shell, articles = _conversion_shell(tmp_path)
    before = articles.read_bytes()

    response = shell.enviar("no conozco el peso exacto")

    assert response["datos"]["datos_reales_modificados"] is False
    assert "preview" not in response["datos"]
    assert shell._session.confirmacion_articulo_pendiente == {}
    assert shell._session.captura_cambio_articulo["articulo_id"] == "ART000126"
    assert articles.read_bytes() == before


def test_preview_articulo_caducado_y_capability_sin_scope(tmp_path: Path) -> None:
    _fixture(tmp_path)
    now = [datetime(2026, 8, 20, 12, 0, 0)]
    service = ConfirmacionFormatoArticuloService(tmp_path, ttl_seconds=30, now_provider=lambda: now[0])
    context = _context("articulos:write")
    preview = service.preview_change(
        operation="UPDATE_PRICE", article_id="ART-TEST", value=2,
        context=context, session_id="chat-a",
    )
    now[0] += timedelta(seconds=31)
    with pytest.raises(ErrorConfirmacionFormatoArticulo) as expired:
        service.confirm_change(preview_token=preview["preview_token"], context=context, session_id="chat-a")
    assert expired.value.code == "expired_preview"

    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)), session_id="no-scope")
    shell.tool_executor.articulos_read_service = ArticulosCatalogReadService(tmp_path)
    shell.tool_executor.write_context = _context("articulos:read")
    shell._session.economic_incidents = [{
        "receta_id": "REC", "incidencia": "SIN_PRECIO", "articulo_id": "ART-TEST",
    }]
    assert shell._economic_actions() == []


def test_chat_paquete_200_unidades_es_formato_no_conversion_fisica(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    payload = json.loads(articles.read_text(encoding="utf-8"))
    payload[0].update({"codigo": "ART000285", "nombre": "Servilleta MPRO", "precio": 6.89})
    articles.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    canonical_path = tmp_path / "DATOS/db/escandallos_canonicos.json"
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    canonical["escandallos"][0]["receta"]["ingredientes"][0]["articulo_id"] = "ART000285"
    canonical_path.write_text(json.dumps(canonical, ensure_ascii=False), encoding="utf-8")
    shell = ServicioChatHostAIShell(
        SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)), session_id="chat-formato",
    )
    shell.tool_executor.articulos_read_service = ArticulosCatalogReadService(tmp_path)
    shell.tool_executor.escandallos_read_service = HostAIEscandallosReadService(tmp_path)
    shell.tool_executor.write_context = _context("articulos:preview", "articulos:write")
    shell.tool_executor.article_change_service = ConfirmacionFormatoArticuloService(
        tmp_path, articles=shell.tool_executor.articulos_read_service,
    )
    shell._session.acciones_economicas_contextuales = {
        "RESOLVE_MISSING_CONVERSION": {
            "context_id": "d" * 32, "articulo_id": "ART000285",
            "receta_id": "REC-CREMA-FIXTURE",
            "incidencia": "CONVERSION_NO_DISPONIBLE", "unidad_origen": "u", "unidad_destino": "kg",
        },
    }
    shell.ejecutar_accion_reserva("RESOLVE_MISSING_CONVERSION", "d" * 32)
    before = articles.read_bytes()
    preview = shell.enviar("el paquete es de 200 unidades asi que el precio total entre 200 es 1 servilleta")
    assert "no una conversión física" in preview["mensaje"]
    visible = preview["datos"]["preview"]
    changes = {item["field"]: item for item in visible["changes"]}
    assert changes["unidad_compra"]["after"] == "paquete"
    assert changes["cantidad_formato"]["after"] == "200"
    assert changes["unidad_formato"]["after"] == "u"
    assert changes["unidad_base"]["after"] == "u"
    assert visible["derived"][0]["value"] == "0.03445 €/u"
    assert visible["derived"][0]["formula"] == "6.89 / 200"
    assert visible["unchanged"][0] == {
        "field": "precio", "label": "Precio del paquete sin IVA",
        "value": "6.89 €", "status": "Sin cambios",
    }
    assert all(item["after"] != "kg" for item in visible["changes"])
    assert "kg" not in json.dumps(visible["derived"])
    assert articles.read_bytes() == before
    applied = shell.ejecutar_accion_reserva("APPLY_PENDING_ARTICLE_CHANGE")
    assert applied["datos"]["datos_reales_modificados"] is True
    stored = json.loads(articles.read_text(encoding="utf-8"))[0]
    assert stored["precio"] == 6.89
    assert stored["catalogo_maestro"]["unidad_compra"] == "paquete"
    assert stored["catalogo_maestro"]["cantidad_formato"] == "200.0"
    assert stored["catalogo_maestro"]["unidad_formato"] == "u"
    assert stored["catalogo_maestro"]["unidad_base"] == "u"
    assert "comprobar ahora" in applied["mensaje"]
    check_action = applied["datos"]["economic_actions"][0]
    assert check_action["action_id"] == "CHECK_ESCANDALLO_COST"
    assert "receta_id" not in check_action and "articulo_id" not in check_action
    canonical_before = (tmp_path / "DATOS/db/escandallos_canonicos.json").read_bytes()

    checked = shell.ejecutar_accion_reserva(
        "CHECK_ESCANDALLO_COST", check_action["action_context_id"],
    )
    assert checked["datos"]["datos_reales_modificados"] is False
    assert "economic_check" in checked["datos"], checked
    assert checked["datos"]["economic_check"]["estado_coste"] == "DISPONIBLE"
    assert checked["datos"]["economic_check"]["coste_total"] == pytest.approx(0.24115)
    assert checked["datos"]["economic_check"]["coste_por_racion"] == pytest.approx(0.24115)
    assert checked["mensaje"] == (
        "El escandallo ya está completo y disponible. "
        "Coste total: 0,24115 €. Coste por ración: 0,24115 €."
    )
    assert shell._session.economic_incidents == []
    assert shell._session.escandallo_activo["estado_coste"] == "DISPONIBLE"
    assert checked["datos"]["ui_action"] == {
        "type": "OPEN_VIEW", "target": "ELABORACION", "id": "REC-CREMA-FIXTURE",
        "view": "ESCANDALLO", "label": "Crema fixture", "safe": True,
        "datos_reales_modificados": False,
    }
    assert checked["datos"]["ui_action_mode"] == "OFFER"
    assert (tmp_path / "DATOS/db/escandallos_canonicos.json").read_bytes() == canonical_before

    replay = shell.ejecutar_accion_reserva(
        "CHECK_ESCANDALLO_COST", check_action["action_context_id"],
    )
    assert replay["datos"]["reason"] == "stale_escandallo_check"
    assert replay["datos"]["datos_reales_modificados"] is False


def test_comprobar_escandallo_refresca_parcial_y_rechaza_otra_sesion() -> None:
    class EconomicRead:
        def consultar(self, **_params):
            return {
                "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO",
                "estado": "OK", "grounding_scope": "COSTE_INCOMPLETO",
                "receta_id": "REC-1", "nombre": "Receta fixture",
                "estado_coste": "PARCIAL", "coste_completo": False,
                "coste_total": None, "coste_por_racion": None,
                "motivos": [{
                    "tipo": "SIN_PRECIO", "articulo_id": "ART-NUEVO",
                    "nombre": "Patata", "detalle": "Sin precio vigente",
                }], "datos_reales_modificados": False,
            }

    class Articles:
        def obtener(self, article_id):
            return {"ok": True, "articulo": {"id": article_id, "nombre": "Patata"}}

    shell_a = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id="session-a")
    shell_a.tool_executor.escandallos_read_service = EconomicRead()
    shell_a.tool_executor.articulos_read_service = Articles()
    shell_a.tool_executor.write_context = _context("articulos:preview")
    shell_a._session.economic_incidents = [{
        "receta_id": "REC-1", "incidencia": "CONVERSION_NO_DISPONIBLE",
        "articulo_id": "ART-ANTIGUO",
    }]
    shell_a._session.acciones_economicas_contextuales = {
        "CHECK_ESCANDALLO_COST": {
            "context_id": "e" * 32, "session_id": "session-a",
            "receta_id": "REC-1", "articulo_id": "ART-ANTIGUO",
            "incidencia_previa": "CONVERSION_NO_DISPONIBLE",
        },
    }
    shell_b = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id="session-b")
    shell_b._session.acciones_economicas_contextuales = dict(shell_a._session.acciones_economicas_contextuales)

    foreign = shell_b.ejecutar_accion_reserva("CHECK_ESCANDALLO_COST", "e" * 32)
    checked = shell_a.ejecutar_accion_reserva("CHECK_ESCANDALLO_COST", "e" * 32)

    assert foreign["datos"]["reason"] == "stale_escandallo_check"
    assert foreign["datos"]["datos_reales_modificados"] is False
    assert "CONVERSION_NO_DISPONIBLE" not in checked["mensaje"]
    assert "SIN_PRECIO — Patata — Sin precio vigente" in checked["mensaje"]
    assert shell_a._session.economic_incidents == [{
        "receta_id": "REC-1", "incidencia": "SIN_PRECIO", "articulo_id": "ART-NUEVO",
        "nombre": "Patata", "unidad_origen": "", "unidad_destino": "",
        "detalle": "Sin precio vigente",
    }]
    assert checked["datos"]["economic_actions"][0]["action_id"] == "RESOLVE_MISSING_PRICE"
    assert checked["datos"]["ui_action"]["id"] == "REC-1"
    assert checked["datos"]["ui_action"]["view"] == "ESCANDALLO"
    assert checked["datos"]["datos_reales_modificados"] is False


@pytest.mark.parametrize("recipe_id", ("REC-ONE", "REC-EXCEL-ABC123"))
def test_comprobar_escandallo_ofrece_navegacion_para_cada_receta_sin_hardcode(recipe_id: str) -> None:
    class EconomicRead:
        def consultar(self, **params):
            assert params == {"agregacion": "DETAIL_COSTE_INCOMPLETO", "escandallo_id": recipe_id}
            return {
                "ok": True, "estado": "OK", "receta_id": recipe_id, "nombre": f"Nombre {recipe_id}",
                "estado_coste": "DISPONIBLE", "coste_completo": True, "motivos": [],
                "coste_total": 1, "coste_por_racion": 1, "datos_reales_modificados": False,
            }

    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id=f"session-{recipe_id}")
    shell.tool_executor.escandallos_read_service = EconomicRead()
    shell._session.acciones_economicas_contextuales = {"CHECK_ESCANDALLO_COST": {
        "context_id": "f" * 32, "session_id": f"session-{recipe_id}", "receta_id": recipe_id,
    }}

    response = shell.ejecutar_accion_reserva("CHECK_ESCANDALLO_COST", "f" * 32)

    assert response["datos"]["ui_action"]["id"] == recipe_id
    assert response["datos"]["ui_action_mode"] == "OFFER"
    assert response["datos"]["datos_reales_modificados"] is False


def test_comprobar_sin_escandallo_no_ofrece_navegacion() -> None:
    class EconomicRead:
        def consultar(self, **_params):
            return {
                "ok": True, "estado": "OK", "receta_id": "REC-SIN", "nombre": "Sin escandallo",
                "estado_coste": "SIN_ESCANDALLO", "coste_completo": False, "motivos": [],
                "datos_reales_modificados": False,
            }

    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id="session-sin")
    shell.tool_executor.escandallos_read_service = EconomicRead()
    shell._session.acciones_economicas_contextuales = {"CHECK_ESCANDALLO_COST": {
        "context_id": "b" * 32, "session_id": "session-sin", "receta_id": "REC-SIN",
    }}

    response = shell.ejecutar_accion_reserva("CHECK_ESCANDALLO_COST", "b" * 32)

    assert response["datos"]["ui_action"] is None
    assert response["datos"]["ui_action_mode"] is None
    assert response["datos"]["datos_reales_modificados"] is False


def test_chat_unidades_por_envase_ambiguo_pide_tipo_y_no_prepara_conversion(tmp_path: Path) -> None:
    _fixture(tmp_path)
    shell = ServicioChatHostAIShell(
        SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)), session_id="chat-ambiguo",
    )
    shell._session.captura_cambio_articulo = {
        "operation": "UPDATE_CONVERSION", "articulo_id": "ART-TEST", "nombre": "Artículo fixture",
        "unidad_origen": "u", "unidad_destino": "kg",
    }
    response = shell.enviar("son 200 unidades y se divide el precio entre 200")
    assert response["datos"]["reason"] == "purchase_unit_required"
    assert "paquete, caja, botella" in response["mensaje"]
    assert shell._session.confirmacion_articulo_pendiente == {}


def test_chat_conflicto_precio_formato_resuelve_en_preview_unico_y_write_atomico(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    payload = json.loads(articles.read_text(encoding="utf-8"))
    payload[0].update({
        "codigo": "ART000285", "nombre": "Servilleta MPRO 2C40 200 UNI NATU. 6,89€",
        "precio": 8.54, "precio_incluye_iva": False,
    })
    articles.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def shell_for(session_id: str) -> ServicioChatHostAIShell:
        shell = ServicioChatHostAIShell(
            SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)), session_id=session_id,
        )
        shell.tool_executor.articulos_read_service = ArticulosCatalogReadService(tmp_path)
        shell.tool_executor.write_context = _context("articulos:preview", "articulos:write")
        shell.tool_executor.article_change_service = ConfirmacionFormatoArticuloService(
            tmp_path, articles=shell.tool_executor.articulos_read_service,
        )
        shell._session.captura_cambio_articulo = {
            "operation": "UPDATE_CONVERSION", "articulo_id": "ART000285",
            "nombre": "Servilleta MPRO 2C40 200 UNI NATU. 6,89€",
            "unidad_origen": "u", "unidad_destino": "kg",
        }
        return shell

    no_price = shell_for("format-current")
    current_preview = no_price.enviar("el paquete es de 200 unidades")
    assert current_preview["datos"]["preview"]["derived"][0]["value"] == "0.0427 €/u"
    assert current_preview["datos"]["preview"]["unchanged"][0]["value"] == "8.54 €"

    shell = shell_for("format-conflict")
    before = articles.read_bytes()
    conflict = shell.enviar("El paquete es de 200 unidades y el precio sin IVA del paquete es 6,89 €")
    assert conflict["datos"]["reason"] == "PRICE_CONFLICT"
    assert conflict["datos"]["economic_actions"] == []
    assert shell._session.confirmacion_articulo_pendiente == {}
    assert shell._session.captura_cambio_articulo["format_value"] == "200"
    assert shell._session.captura_cambio_articulo["unidad_compra"] == "paquete"
    assert articles.read_bytes() == before

    combined = shell.enviar("cámbialo a 6,89")
    visible = combined["datos"]["preview"]
    changes = {item["field"]: item for item in visible["changes"]}
    assert changes["precio"] == {
        "field": "precio", "label": "Precio del paquete sin IVA", "before": "8.54", "after": "6.89",
    }
    assert changes["unidad_compra"]["after"] == "paquete"
    assert changes["cantidad_formato"]["after"] == "200"
    assert changes["unidad_formato"]["after"] == "u"
    assert changes["unidad_base"]["after"] == "u"
    assert visible["unchanged"] == []
    assert visible["derived"][0]["value"] == "0.03445 €/u"
    assert visible["derived"][0]["formula"] == "6.89 / 200"
    assert [item["action_id"] for item in combined["datos"]["economic_actions"]] == [
        "APPLY_PENDING_ARTICLE_CHANGE", "DISCARD_PENDING_ARTICLE_CHANGE",
    ]
    assert articles.read_bytes() == before

    applied = shell.ejecutar_accion_reserva("APPLY_PENDING_ARTICLE_CHANGE")
    assert applied["datos"]["datos_reales_modificados"] is True
    stored = json.loads(articles.read_text(encoding="utf-8"))[0]
    assert stored["precio"] == 6.89
    assert stored["catalogo_maestro"]["unidad_compra"] == "paquete"
    assert stored["catalogo_maestro"]["cantidad_formato"] == "200.0"
    assert stored["catalogo_maestro"]["unidad_formato"] == "u"
    assert stored["catalogo_maestro"]["unidad_base"] == "u"
    assert applied["datos"]["economic_actions"] == []


def test_chat_conflicto_precio_mantener_igual_descartar_e_invalidos(tmp_path: Path) -> None:
    articles = _fixture(tmp_path)
    payload = json.loads(articles.read_text(encoding="utf-8"))
    payload[0].update({
        "codigo": "ART000285", "nombre": "Servilleta 6,89€ solo en nombre",
        "precio": 8.54, "precio_incluye_iva": False,
    })
    articles.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def shell_for(session_id: str) -> ServicioChatHostAIShell:
        shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)), session_id=session_id)
        shell.tool_executor.articulos_read_service = ArticulosCatalogReadService(tmp_path)
        shell.tool_executor.write_context = _context("articulos:preview", "articulos:write")
        shell.tool_executor.article_change_service = ConfirmacionFormatoArticuloService(tmp_path, articles=shell.tool_executor.articulos_read_service)
        shell._session.captura_cambio_articulo = {
            "operation": "UPDATE_CONVERSION", "articulo_id": "ART000285",
            "nombre": "Servilleta 6,89€ solo en nombre", "unidad_origen": "u", "unidad_destino": "kg",
        }
        return shell

    keep = shell_for("keep-current")
    keep.enviar("paquete de 200 unidades y precio sin IVA 6,89 €")
    kept = keep.enviar("mantén 8,54")
    assert kept["datos"]["preview"]["unchanged"][0]["value"] == "8.54 €"
    assert kept["datos"]["preview"]["derived"][0]["value"] == "0.0427 €/u"

    same = shell_for("same-price")
    equal = same.enviar("paquete de 200 unidades y precio sin IVA 8,54 €")
    assert equal["datos"].get("reason") != "PRICE_CONFLICT"
    assert equal["datos"]["preview"]["derived"][0]["value"] == "0.0427 €/u"

    name_only = shell_for("name-only")
    preview = name_only.enviar("paquete de 200 unidades")
    assert preview["datos"]["preview"]["unchanged"][0]["value"] == "8.54 €"

    discarded = shell_for("discard-conflict")
    before = articles.read_bytes()
    discarded.enviar("paquete de 200 unidades y precio sin IVA 6,89 €")
    result = discarded.enviar("descartar")
    assert result["datos"]["reason"] == "PRICE_CONFLICT_DISCARDED"
    assert discarded._session.captura_cambio_articulo == {}
    assert articles.read_bytes() == before

    expired = shell_for("expired-conflict")
    expired.enviar("paquete de 200 unidades y precio sin IVA 6,89 €")
    expired._session.captura_cambio_articulo["expires_monotonic"] = 0
    expired_result = expired.enviar("el nuevo")
    assert expired_result["datos"]["reason"] == "expired_price_conflict"
    assert expired._session.captura_cambio_articulo == {}

    other_session = shell_for("other-session")
    assert other_session._session.captura_cambio_articulo.get("phase") != "PRICE_CONFLICT"

    for index, bad in enumerate(("0", "-1", "NaN", "infinito")):
        invalid = shell_for(f"invalid-{index}")
        response = invalid.enviar(f"paquete de 200 unidades y precio sin IVA {bad}")
        assert response["datos"]["reason"] == "invalid_price"
        assert response["datos"]["economic_actions"] == []
        assert invalid._session.confirmacion_articulo_pendiente == {}
