from __future__ import annotations

import json
from pathlib import Path

from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import (
    EstadoRendimiento,
    OrigenRendimiento,
    Receta,
    RendimientoNeto,
)
from SERVICIOS.host_ai_escandallos_read_service import HostAIEscandallosReadService
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.schema_escandallos_555a import SCHEMA_VERSION
from SERVICIOS.serializador_escandallos_555a import escandallo_a_dict, escandallo_desde_dict
from SERVICIOS.validador_compatibilidad_rendimiento import (
    EstadoCompatibilidadRendimiento,
    ValidadorCompatibilidadRendimiento,
)
from SERVICIOS.validador_escandallos_555a import validar_receta


def _recipe(
    amount: float,
    unit: str,
    *,
    net: RendimientoNeto | None = None,
) -> Receta:
    return Receta(
        codigo="REC-HIJO",
        nombre="Elaboracion hija",
        rendimiento=amount,
        unidad_rendimiento=unit,
        ingredientes=[Ingrediente("ING-1", "Ingrediente", 1, "kg")],
        estado_rendimiento=EstadoRendimiento.IMPORTADO,
        origen_rendimiento=OrigenRendimiento("EXCEL", "Hoja:10"),
        rendimiento_neto=net,
    )


def test_compatibilidad_directa_kg_y_conversion_metrica() -> None:
    validator = ValidadorCompatibilidadRendimiento()
    recipe = _recipe(1, "kg")

    direct = validator.evaluar(0.02, "kg", recipe)
    grams = validator.evaluar(20, "g", recipe)

    assert direct.estado is EstadoCompatibilidadRendimiento.DIRECTAMENTE_COMPATIBLE
    assert direct.cantidad_en_unidad_rendimiento == 0.02
    assert direct.factor_aplicado == 0.02
    assert grams.estado is EstadoCompatibilidadRendimiento.DIRECTAMENTE_COMPATIBLE
    assert grams.cantidad_en_unidad_rendimiento == 0.02


def test_siete_unidades_con_rendimiento_neto_confirmado_convierten_un_kg() -> None:
    recipe = _recipe(7, "u", net=RendimientoNeto(
        1.26,
        "kg",
        EstadoRendimiento.CONFIRMADO,
        OrigenRendimiento("USUARIO", fecha="2026-08-14"),
    ))

    result = ValidadorCompatibilidadRendimiento().evaluar(1, "kg", recipe)

    assert result.estado is EstadoCompatibilidadRendimiento.COMPATIBLE_CON_CONVERSION
    assert round(result.factor_aplicado or 0, 6) == 0.793651
    assert round(result.cantidad_en_unidad_rendimiento or 0, 6) == 5.555556
    assert result.conversion["procedencia"] == "rendimiento_neto_confirmado"


def test_unidad_sin_equivalencia_y_conversion_no_confirmada_no_autorizan() -> None:
    validator = ValidadorCompatibilidadRendimiento()
    missing = validator.evaluar(0.02, "kg", _recipe(1, "u"))
    suggested = validator.evaluar(1, "kg", _recipe(
        7, "u", net=RendimientoNeto(1.26, "kg", EstadoRendimiento.SUGERIDO, OrigenRendimiento("SISTEMA")),
    ))
    imported = validator.evaluar(1, "kg", _recipe(
        7, "u", net=RendimientoNeto(1.26, "kg", EstadoRendimiento.IMPORTADO, OrigenRendimiento("EXCEL")),
    ))

    assert missing.estado is EstadoCompatibilidadRendimiento.INFORMACION_INSUFICIENTE
    assert suggested.estado is EstadoCompatibilidadRendimiento.INFORMACION_INSUFICIENTE
    assert imported.estado is EstadoCompatibilidadRendimiento.INFORMACION_INSUFICIENTE
    assert suggested.incidencias == ["RENDIMIENTO_NETO_NO_CONFIRMADO"]


def test_conversion_confirmada_a_otra_dimension_es_incompatible() -> None:
    recipe = _recipe(7, "u", net=RendimientoNeto(
        1.26, "kg", EstadoRendimiento.CONFIRMADO, OrigenRendimiento("USUARIO"),
    ))

    result = ValidadorCompatibilidadRendimiento().evaluar(1, "l", recipe)

    assert result.estado is EstadoCompatibilidadRendimiento.INCOMPATIBLE
    assert result.cantidad_en_unidad_rendimiento is None


def test_rendimiento_cero_es_invalido_y_no_calculable() -> None:
    recipe = _recipe(0, "kg")

    validation = validar_receta(recipe)
    compatibility = ValidadorCompatibilidadRendimiento().evaluar(1, "kg", recipe)

    assert validation.valido is False
    assert compatibility.estado is EstadoCompatibilidadRendimiento.INFORMACION_INSUFICIENTE
    assert compatibility.incidencias == ["RENDIMIENTO_INVALIDO"]


def test_rendimiento_neto_exige_cantidad_fisica_estado_y_trazabilidad() -> None:
    recipe = _recipe(7, "u", net=RendimientoNeto(
        0, "u", EstadoRendimiento.CONFIRMADO,
    ))

    result = validar_receta(recipe)

    assert result.valido is False
    assert "receta.rendimiento_neto.cantidad: debe ser mayor que 0." in result.errores
    assert "receta.rendimiento_neto.unidad: debe ser una unidad fisica canonica." in result.errores
    assert "receta.rendimiento_neto.origen: obligatorio." in result.errores


def test_schema_11_roundtrip_preserva_contrato_y_schema_10_sigue_leyendose(tmp_path: Path) -> None:
    recipe = _recipe(7, "u", net=RendimientoNeto(
        1.26, "kg", EstadoRendimiento.CONFIRMADO, OrigenRendimiento("USUARIO", "ficha"),
    ))
    payload = escandallo_a_dict(Escandallo(recipe, 10))
    restored = escandallo_desde_dict(payload).receta

    assert payload["schema_version"] == SCHEMA_VERSION == "1.1"
    assert restored.estado_rendimiento is EstadoRendimiento.IMPORTADO
    assert restored.origen_rendimiento.referencia == "Hoja:10"
    assert restored.rendimiento_neto.cantidad == 1.26
    assert restored.rendimiento_neto.estado is EstadoRendimiento.CONFIRMADO

    legacy = {
        "schema_version": "1.0",
        "escandallo": {
            "receta": {
                "codigo": "LEGACY", "nombre": "Legacy", "rendimiento": 1,
                "unidad_rendimiento": "u", "ingredientes": [{
                    "codigo": "I", "nombre": "Ingrediente", "cantidad": 1,
                    "unidad": "u", "merma_pct": 0, "articulo_id": None,
                    "proveedor_habitual": None, "precio_unitario": 0,
                    "observaciones": "", "metadata": {},
                }],
            },
            "coste_total": 0,
        },
    }
    legacy_recipe = escandallo_desde_dict(legacy).receta
    assert legacy_recipe.estado_rendimiento is None
    assert legacy_recipe.origen_rendimiento is None
    assert legacy_recipe.rendimiento_neto is None

    path = tmp_path / "escandallos.json"
    repository = RepositorioEscandallos(path)
    repository.guardar_todos([Escandallo(recipe, 10)])
    saved = json.loads(path.read_text(encoding="utf-8"))
    loaded = repository.listar()[0].receta
    assert saved["schema_version"] == "1.1"
    assert loaded.rendimiento_neto.cantidad == 1.26


def test_proyeccion_read_expone_contrato_sin_inventarlo_en_legacy(tmp_path: Path) -> None:
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos_canonicos.json").write_text(json.dumps({
        "schema_version": "1.1",
        "escandallos": [{
            "receta": {
                "codigo": "REC-READ", "nombre": "Crema prueba", "rendimiento": 7,
                "unidad_rendimiento": "u", "estado_rendimiento": "IMPORTADO",
                "origen_rendimiento": {"tipo": "EXCEL", "referencia": "Hoja:38"},
                "rendimiento_neto": {
                    "cantidad": 1.26, "unidad": "kg", "estado": "CONFIRMADO",
                    "origen": {"tipo": "USUARIO"},
                },
                "ingredientes": [{"codigo": "I", "nombre": "Leche", "cantidad": 1, "unidad": "kg"}],
            },
            "coste_total": 0,
        }, {
            "receta": {
                "codigo": "REC-LEGACY", "nombre": "Receta antigua", "rendimiento": 1,
                "unidad_rendimiento": "u", "ingredientes": [{
                    "codigo": "I2", "nombre": "Sal", "cantidad": 1, "unidad": "kg",
                }],
            },
            "coste_total": 0,
        }],
    }, ensure_ascii=False), encoding="utf-8")
    (db / "articulos.json").write_text("[]", encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = tmp_path / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")

    service = HostAIEscandallosReadService(tmp_path)
    current = service.consultar("detalle", escandallo_id="REC-READ")["escandallo"]
    legacy = service.consultar("detalle", escandallo_id="REC-LEGACY")["escandallo"]

    assert current["estado_rendimiento"] == "IMPORTADO"
    assert current["origen_rendimiento"] == {"tipo": "EXCEL", "referencia": "Hoja:38"}
    assert current["rendimiento_neto"]["cantidad"] == 1.26
    assert current["rendimiento_neto"]["estado"] == "CONFIRMADO"
    assert legacy["estado_rendimiento"] is None
    assert legacy["rendimiento_neto"] is None
