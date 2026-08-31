from __future__ import annotations

import json
from pathlib import Path

import pytest

from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import EstadoRendimiento, OrigenRendimiento, Receta
from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.confirmacion_rendimiento_elaboracion_service import (
    ConfirmacionRendimientoElaboracionService,
    ErrorConfirmacionRendimiento,
)
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.host_ai_escandallos_read_service import HostAIEscandallosReadService
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.validador_compatibilidad_rendimiento import (
    EstadoCompatibilidadRendimiento,
    ValidadorCompatibilidadRendimiento,
)


def _context(*scopes: str) -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext(
        request_id="REQ-1", user_id="USR-1", tenant_id="TENANT-1",
        roles=("chef",), scopes=frozenset(scopes),
    )


def _fixture(base: Path) -> RepositorioEscandallos:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    repo = RepositorioEscandallos(db / "escandallos_canonicos.json")
    child = Receta(
        "REC-HIJO", "Crema hija", 7, "u",
        [Ingrediente("ART-LECHE", "Leche", 1, "kg", articulo_id="ART-LECHE")],
        estado_rendimiento=EstadoRendimiento.IMPORTADO,
        origen_rendimiento=OrigenRendimiento("EXCEL", "fixture"),
    )
    parent = Receta(
        "REC-PADRE", "Postre padre", 1, "u",
        [Ingrediente(
            "ART-CREMA", "Crema hija", 1, "kg", articulo_id="ART-CREMA",
            metadata={"tipo": "ELABORACION", "referencia_elaboracion": "Crema hija"},
        )],
    )
    repo.guardar_todos([Escandallo(child, 10), Escandallo(parent, 0)])
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "ART-LECHE", "nombre": "Leche", "precio": 2, "unidad": "kg"},
        {"codigo": "ART-CREMA", "nombre": "Crema hija", "precio": 10, "unidad": "kg"},
    ]), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = base / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")
    return repo


def _confirm(
    service: ConfirmacionRendimientoElaboracionService,
    *, cantidad=1.26, unidad="kg", modo="TOTAL",
) -> tuple[dict, dict]:
    args = {
        "escandallo_id": "REC-HIJO", "cantidad": cantidad, "unidad": unidad,
        "origen": {"tipo": "USUARIO", "referencia": "medicion cocina"},
        "context": _context("escandallos:write"), "modo": modo,
    }
    preview = service.preview(**args)
    result = service.execute(**args, preview_token=preview["preview_token"])
    return preview, result


def test_preview_no_escribe_y_confirmacion_total_persiste_sin_cambiar_declarado(tmp_path: Path) -> None:
    repo = _fixture(tmp_path)
    path = tmp_path / "DATOS/db/escandallos_canonicos.json"
    before = path.read_bytes()
    service = ConfirmacionRendimientoElaboracionService(tmp_path, repo)
    args = {
        "escandallo_id": "REC-HIJO", "cantidad": 1.26, "unidad": "kg",
        "origen": {"tipo": "USUARIO", "referencia": "bascula"},
        "context": _context("escandallos:write"),
    }

    preview = service.preview(**args)
    assert preview["estado"] == "LISTO_PARA_CONFIRMAR"
    assert preview["datos_reales_modificados"] is False
    assert path.read_bytes() == before
    result = service.execute(**args, preview_token=preview["preview_token"])

    saved = repo.listar()[0].receta
    assert result["estado"] == "CONFIRMADO"
    assert saved.rendimiento == 7 and saved.unidad_rendimiento == "u"
    assert saved.rendimiento_neto.cantidad == 1.26
    assert saved.rendimiento_neto.unidad == "kg"
    assert saved.rendimiento_neto.estado is EstadoRendimiento.CONFIRMADO
    assert saved.rendimiento_neto.origen.tipo == "USUARIO"
    assert saved.rendimiento_neto.origen.actor_id == "USR-1"
    assert saved.rendimiento_neto.origen.fecha


def test_input_por_unidad_deriva_un_solo_rendimiento_neto_total(tmp_path: Path) -> None:
    repo = _fixture(tmp_path)
    service = ConfirmacionRendimientoElaboracionService(tmp_path, repo)

    _preview, result = _confirm(service, cantidad=0.18, unidad="kg", modo="POR_UNIDAD")

    assert result["rendimiento_neto"]["cantidad"] == 1.26
    raw = json.loads((tmp_path / "DATOS/db/escandallos_canonicos.json").read_text(encoding="utf-8"))
    recipe = raw["escandallos"][0]["receta"]
    assert recipe["rendimiento_neto"]["cantidad"] == 1.26
    assert "peso_por_unidad" not in recipe


def test_estimacion_parcial_exige_aceptacion_y_liga_origen_al_preview(tmp_path: Path) -> None:
    repo = _fixture(tmp_path)
    path = tmp_path / "DATOS/db/escandallos_canonicos.json"
    service = ConfirmacionRendimientoElaboracionService(tmp_path, repo)
    args = {
        "escandallo_id": "REC-HIJO", "cantidad": 1.276, "unidad": "kg",
        "origen": {"tipo": "USUARIO"}, "context": _context("escandallos:write"),
        "propuesta_origen": "TEORICO_PARCIAL",
    }
    before = path.read_bytes()
    preview = service.preview(**args)
    assert preview["propuesta_origen"] == "TEORICO_PARCIAL"
    assert path.read_bytes() == before

    with pytest.raises(ErrorConfirmacionRendimiento) as missing_acceptance:
        service.execute(**args, preview_token=preview["preview_token"])
    assert missing_acceptance.value.code == "partial_estimate_acceptance_required"
    assert path.read_bytes() == before

    with pytest.raises(ErrorConfirmacionRendimiento) as changed_origin:
        service.execute(
            **{**args, "propuesta_origen": "MANUAL"},
            preview_token=preview["preview_token"], acepta_estimacion_parcial=True,
        )
    assert changed_origin.value.code == "stale_or_invalid_preview"
    assert path.read_bytes() == before

    result = service.execute(
        **args, preview_token=preview["preview_token"], acepta_estimacion_parcial=True,
    )
    assert result["estado"] == "CONFIRMADO"
    assert result["rendimiento_neto"]["cantidad"] == 1.276


def test_estimacion_completa_y_entrada_manual_no_exigen_aceptacion_adicional(tmp_path: Path) -> None:
    for origin in ("TEORICO_COMPLETO", "MANUAL"):
        base = tmp_path / origin
        service = ConfirmacionRendimientoElaboracionService(base, _fixture(base))
        args = {
            "escandallo_id": "REC-HIJO", "cantidad": 1.35, "unidad": "kg",
            "origen": {"tipo": "USUARIO"}, "context": _context("escandallos:write"),
            "propuesta_origen": origin,
        }
        preview = service.preview(**args)
        result = service.execute(**args, preview_token=preview["preview_token"])
        assert preview["propuesta_origen"] == origin
        assert result["estado"] == "CONFIRMADO"


@pytest.mark.parametrize("cantidad", [0, -1, float("nan"), float("inf")])
def test_cantidad_invalida_se_rechaza(tmp_path: Path, cantidad: float) -> None:
    service = ConfirmacionRendimientoElaboracionService(tmp_path, _fixture(tmp_path))
    with pytest.raises(ErrorConfirmacionRendimiento) as exc:
        service.preview(
            escandallo_id="REC-HIJO", cantidad=cantidad, unidad="kg",
            origen={"tipo": "USUARIO"}, context=_context("escandallos:write"),
        )
    assert exc.value.code == "invalid_quantity"


def test_unidad_origen_identidad_y_escandallo_invalidos_se_rechazan(tmp_path: Path) -> None:
    service = ConfirmacionRendimientoElaboracionService(tmp_path, _fixture(tmp_path))
    base = {
        "escandallo_id": "REC-HIJO", "cantidad": 1, "unidad": "u",
        "origen": {"tipo": "USUARIO"}, "context": _context("escandallos:write"),
    }
    with pytest.raises(ErrorConfirmacionRendimiento) as unit:
        service.preview(**base)
    assert unit.value.code == "invalid_unit"
    with pytest.raises(ErrorConfirmacionRendimiento) as origin:
        service.preview(**{**base, "unidad": "kg", "origen": {}})
    assert origin.value.code == "invalid_origin"
    with pytest.raises(ErrorConfirmacionRendimiento) as missing:
        service.preview(**{**base, "unidad": "kg", "escandallo_id": "NO-EXISTE"})
    assert missing.value.code == "escandallo_not_found"
    with pytest.raises(ErrorConfirmacionRendimiento) as path:
        service.preview(**{**base, "unidad": "kg", "escandallo_id": "../../DATOS/x"})
    assert path.value.code == "invalid_escandallo_id"


def test_actor_sin_scope_y_preview_obsoleto_se_rechazan(tmp_path: Path) -> None:
    repo = _fixture(tmp_path)
    service = ConfirmacionRendimientoElaboracionService(tmp_path, repo)
    args = {
        "escandallo_id": "REC-HIJO", "cantidad": 1.26, "unidad": "kg",
        "origen": {"tipo": "USUARIO"}, "context": _context("escandallos:write"),
    }
    with pytest.raises(ErrorConfirmacionRendimiento) as unauthorized:
        service.preview(**{**args, "context": _context("escandallos:read")})
    assert unauthorized.value.code == "unauthorized"

    preview = service.preview(**args)
    changed = repo.listar()[0]
    changed.coste_total = 11
    repo.upsert(changed)
    with pytest.raises(ErrorConfirmacionRendimiento) as stale:
        service.execute(**args, preview_token=preview["preview_token"])
    assert stale.value.code == "stale_or_invalid_preview"


def test_idempotencia_no_reescribe_ni_degrada_trazabilidad(tmp_path: Path) -> None:
    repo = _fixture(tmp_path)
    service = ConfirmacionRendimientoElaboracionService(tmp_path, repo)
    _preview, first = _confirm(service)
    path = tmp_path / "DATOS/db/escandallos_canonicos.json"
    after_first = path.read_bytes()
    first_source = first["rendimiento_neto"]["origen"]

    preview = service.preview(
        escandallo_id="REC-HIJO", cantidad=1.26, unidad="kg",
        origen={"tipo": "USUARIO", "referencia": "otro texto"},
        context=_context("escandallos:write"),
    )
    result = service.execute(
        escandallo_id="REC-HIJO", cantidad=1.26, unidad="kg",
        origen={"tipo": "USUARIO", "referencia": "otro texto"},
        context=_context("escandallos:write"), preview_token=preview["preview_token"],
    )

    assert result["idempotente"] is True
    assert path.read_bytes() == after_first
    assert repo.listar()[0].receta.rendimiento_neto.origen.referencia == first_source["referencia"]


def test_valor_distinto_es_actualizacion_explicita_confirmada(tmp_path: Path) -> None:
    repo = _fixture(tmp_path)
    service = ConfirmacionRendimientoElaboracionService(tmp_path, repo)
    _confirm(service)

    args = {
        "escandallo_id": "REC-HIJO", "cantidad": 1.4, "unidad": "kg",
        "origen": {"tipo": "USUARIO", "referencia": "segunda medicion"},
        "context": _context("escandallos:write"),
    }
    preview = service.preview(**args)
    result = service.execute(**args, preview_token=preview["preview_token"])

    saved = repo.listar()[0].receta.rendimiento_neto
    assert result["estado"] == "CONFIRMADO" and result["idempotente"] is False
    assert saved.cantidad == 1.4
    assert saved.estado is EstadoRendimiento.CONFIRMADO
    assert saved.origen.referencia == "segunda medicion"


def test_read_after_write_validador_actualizado_resuelve_coste_padre(tmp_path: Path) -> None:
    repo = _fixture(tmp_path)
    child_before = repo.listar()[0].receta
    validator = ValidadorCompatibilidadRendimiento()
    assert validator.evaluar(1, "kg", child_before).estado is EstadoCompatibilidadRendimiento.INFORMACION_INSUFICIENTE

    _confirm(ConfirmacionRendimientoElaboracionService(tmp_path, repo))
    child_after = repo.listar()[0].receta
    assert validator.evaluar(1, "kg", child_after).estado is EstadoCompatibilidadRendimiento.COMPATIBLE_CON_CONVERSION

    read = HostAIEscandallosReadService(tmp_path).consultar("detalle", escandallo_id="REC-HIJO")["escandallo"]
    assert read["rendimiento"] == 7 and read["unidad_rendimiento"] == "u"
    assert read["rendimiento_neto"]["cantidad"] == 1.26
    parent = BibliotecaCulinariaReadService(tmp_path).detalle("REC-PADRE")["elaboracion"]
    line = parent["escandallo"]["lineas"][0]
    assert line["estado_coste"] == "COSTE_SUBELABORACION_RESUELTO"
    assert line["coste_linea"] == pytest.approx(2 / 1.26)
    assert line["trazabilidad_coste"]["conversion"]["procedencia"] == "rendimiento_neto_confirmado"


def test_write_no_se_publica_en_general_agent_ni_mcp() -> None:
    registry = build_default_tool_registry()
    general_ids = {item["tool_id"] for item in HostAIToolCatalog.for_general_agent(registry).effective_tools()}
    mcp_ids = {item["tool_id"] for item in HostAIToolCatalog(registry).effective_tools()}
    forbidden = {"confirmar_rendimiento", "editar_escandallo", "guardar_receta"}
    assert not general_ids & forbidden
    assert not mcp_ids & forbidden
