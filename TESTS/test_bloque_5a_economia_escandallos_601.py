from __future__ import annotations

from decimal import Decimal
import json

import pytest

from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
from SERVICIOS.motor_calculo_escandallos_601 import (
    INC_CANTIDAD_INEXISTENTE,
    INC_CONVERSION_INEXISTENTE,
    INC_PRODUCTO_SIN_PRECIO,
    INC_UNIDAD_INCOMPATIBLE,
    MotorCalculoEscandallos601,
)
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from SERVICIOS.serializador_escandallos_555a import escandallo_a_dict, escandallo_desde_dict


def _motor(tmp_path):
    repo = RepositorioProductosMaestro601(tmp_path)
    return repo, MotorCalculoEscandallos601(repo)


def _crear_producto(repo: RepositorioProductosMaestro601, **overrides) -> str:
    base = {
        "nombre": "Producto test",
        "familia": "TEST",
        "unidad_base": "kg",
        "unidad_compra": "kg",
        "precio": "1.00",
        "proveedor": "Proveedor Test",
        "proveedor_preferente": "Proveedor Test",
        "fecha_precio": "2026-08-15",
        "iva": "10",
    }
    base.update(overrides)
    creado = repo.crear_producto(base)
    return str(creado.get("codigo") or "")


def _calcular(motor: MotorCalculoEscandallos601, lineas: list[dict], raciones: float = 1.0) -> dict:
    return motor.calcular(
        nombre_escandallo="Bloque 5A",
        numero_raciones=raciones,
        lineas_entrada=lineas,
        precio_venta_total=100.0,
    )


def _tipos_incidencia(linea: dict) -> set[str]:
    return {str(i.get("tipo") or "") for i in list(linea.get("incidencias") or [])}


def test_pack_precio_comercial_y_redondeo_final(tmp_path):
    repo, motor = _motor(tmp_path)
    cod_huevos = _crear_producto(
        repo,
        nombre="Huevos M/L",
        unidad_base="u",
        unidad_compra="paquete",
        cantidad_formato="6",
        unidad_formato="u",
        precio="1.60",
    )

    resultado = _calcular(
        motor,
        [
            {
                "producto_codigo": cod_huevos,
                "nombre_mostrado": "Huevos M/L",
                "cantidad_texto": "7 u",
                "unidad_receta": "u",
            }
        ],
    )

    linea = resultado["lineas"][0]
    assert linea["precio_compra_utilizado"] == pytest.approx(0.266667, abs=1e-6)
    assert linea["coste_linea"] == pytest.approx(1.866667, abs=1e-6)
    assert f"{linea['coste_linea']:.2f}" == "1.87"


def test_conversiones_canonicas_kg_g_y_l_ml_en_ambos_sentidos(tmp_path):
    repo, motor = _motor(tmp_path)
    cod_harina_kg = _crear_producto(repo, nombre="Harina KG", unidad_base="kg", unidad_compra="kg", precio="3.00")
    cod_sal_g = _crear_producto(repo, nombre="Sal G", unidad_base="g", unidad_compra="g", precio="0.02")
    cod_caldo_l = _crear_producto(repo, nombre="Caldo L", unidad_base="l", unidad_compra="l", precio="2.40")
    cod_esencia_ml = _crear_producto(repo, nombre="Esencia ML", unidad_base="ml", unidad_compra="ml", precio="0.01")

    resultado = _calcular(
        motor,
        [
            {"producto_codigo": cod_harina_kg, "nombre_mostrado": "Harina KG", "cantidad_texto": "500 g", "unidad_receta": "g"},
            {"producto_codigo": cod_sal_g, "nombre_mostrado": "Sal G", "cantidad_texto": "0.5 kg", "unidad_receta": "kg"},
            {"producto_codigo": cod_caldo_l, "nombre_mostrado": "Caldo L", "cantidad_texto": "250 ml", "unidad_receta": "ml"},
            {"producto_codigo": cod_esencia_ml, "nombre_mostrado": "Esencia ML", "cantidad_texto": "0.25 l", "unidad_receta": "l"},
        ],
    )

    costes = [l["coste_linea"] for l in resultado["lineas"]]
    assert costes[0] == pytest.approx(1.5, abs=1e-6)  # 500g -> 0.5kg * 3.00
    assert costes[1] == pytest.approx(10.0, abs=1e-6)  # 0.5kg -> 500g * 0.02
    assert costes[2] == pytest.approx(0.6, abs=1e-6)  # 250ml -> 0.25l * 2.40
    assert costes[3] == pytest.approx(2.5, abs=1e-6)  # 0.25l -> 250ml * 0.01


def test_rechaza_conversiones_no_permitidas_u_kg_y_kg_l(tmp_path):
    repo, motor = _motor(tmp_path)
    cod_carne = _crear_producto(repo, nombre="Carne KG", unidad_base="kg", unidad_compra="kg", precio="12.00")
    cod_aceite = _crear_producto(repo, nombre="Aceite L", unidad_base="l", unidad_compra="l", precio="4.00")

    resultado = _calcular(
        motor,
        [
            {"producto_codigo": cod_carne, "nombre_mostrado": "Carne KG", "cantidad_texto": "2 u", "unidad_receta": "u"},
            {"producto_codigo": cod_aceite, "nombre_mostrado": "Aceite L", "cantidad_texto": "1 kg", "unidad_receta": "kg"},
        ],
    )

    for linea in resultado["lineas"]:
        tipos = _tipos_incidencia(linea)
        assert INC_CONVERSION_INEXISTENTE in tipos
        assert INC_UNIDAD_INCOMPATIBLE in tipos
        assert linea["coste_linea"] is None


def test_nulls_formato_incompleto_y_coste_parcial(tmp_path):
    repo, motor = _motor(tmp_path)
    cod_ok = _crear_producto(repo, nombre="Producto OK", unidad_base="kg", unidad_compra="kg", precio="2.00")
    cod_sin_precio = _crear_producto(repo, nombre="Producto sin precio", unidad_base="kg", unidad_compra="kg", precio=None)
    cod_formato_incompleto = _crear_producto(
        repo,
        nombre="Huevos formato incompleto",
        unidad_base="u",
        unidad_compra="paquete",
        cantidad_formato="6",
        unidad_formato="",
        precio="1.60",
    )

    resultado = _calcular(
        motor,
        [
            {"producto_codigo": cod_ok, "nombre_mostrado": "Producto OK", "cantidad_texto": "1 kg", "unidad_receta": "kg"},
            {"producto_codigo": cod_sin_precio, "nombre_mostrado": "Producto sin precio", "cantidad_texto": "1 kg", "unidad_receta": "kg"},
            {"producto_codigo": cod_ok, "nombre_mostrado": "Producto OK", "cantidad_texto": "", "unidad_receta": "kg"},
            {"producto_codigo": cod_formato_incompleto, "nombre_mostrado": "Huevos formato incompleto", "cantidad_texto": "7 u", "unidad_receta": "u"},
        ],
    )

    assert resultado["coste_total"] == pytest.approx(2.0, abs=1e-6)
    assert resultado["coste_completo"] is False
    assert resultado["coste_parcial"] is True
    assert len(resultado["lineas_sin_coste"]) == 3

    lineas = resultado["lineas"]
    assert INC_PRODUCTO_SIN_PRECIO in _tipos_incidencia(lineas[1])
    assert INC_CANTIDAD_INEXISTENTE in _tipos_incidencia(lineas[2])
    assert INC_UNIDAD_INCOMPATIBLE in _tipos_incidencia(lineas[3])


def test_referencia_importada_es_fallback_y_precio_real_tiene_prioridad(tmp_path):
    repo, motor = _motor(tmp_path)
    referencia = {
        "tipo": "PRECIO_REFERENCIA_IMPORTADA",
        "origen": "IMPORTADO",
        "precio_normalizado": 4.0,
        "unidad_normalizada": "kg",
        "tienda_referencia": "Tienda externa",
        "consultado_en": "2026-08-27T10:00:00+02:00",
        "autoridad": "REFERENCIA_NO_REAL",
    }
    codigo_fallback = _crear_producto(
        repo, nombre="Producto con referencia", precio=None,
        proveedor="Proveedor real", proveedor_preferente="Proveedor real",
        precios_referencia=[referencia],
    )
    codigo_real = _crear_producto(
        repo, nombre="Producto con precio real", precio="3.00",
        precios_referencia=[referencia],
    )
    articulos = json.loads(repo.path_articulos.read_text(encoding="utf-8"))
    for articulo in articulos:
        if articulo.get("codigo") in {codigo_fallback, codigo_real}:
            articulo["precios_referencia"] = [referencia]
    repo.path_articulos.write_text(json.dumps(articulos, ensure_ascii=False), encoding="utf-8")

    resultado = _calcular(motor, [
        {"producto_codigo": codigo_fallback, "cantidad_texto": "1 kg", "unidad_receta": "kg"},
        {"producto_codigo": codigo_real, "cantidad_texto": "1 kg", "unidad_receta": "kg"},
    ])

    fallback, real = resultado["lineas"]
    assert fallback["precio_compra_utilizado"] == pytest.approx(4.0)
    assert fallback["precio_provisional"] is True
    assert fallback["precio_referencia"]["fuente"] == "referencia_externa"
    assert real["precio_compra_utilizado"] == pytest.approx(3.0)
    assert real["precio_provisional"] is False
    assert real["precio_referencia"]["fuente"] in {"asociacion", "historico", "catalogo_producto"}


def test_suma_decimal_y_serializacion_no_pierde_semantica(tmp_path):
    repo, motor = _motor(tmp_path)
    cod_a = _crear_producto(
        repo,
        nombre="Huevos 6u",
        unidad_base="u",
        unidad_compra="paquete",
        cantidad_formato="6",
        unidad_formato="u",
        precio="1.60",
    )
    cod_b = _crear_producto(
        repo,
        nombre="Formato 3u",
        unidad_base="u",
        unidad_compra="paquete",
        cantidad_formato="3",
        unidad_formato="u",
        precio="2.40",
    )

    resultado = _calcular(
        motor,
        [
            {"producto_codigo": cod_a, "nombre_mostrado": "Huevos 6u", "cantidad_texto": "7 u", "unidad_receta": "u"},
            {"producto_codigo": cod_b, "nombre_mostrado": "Formato 3u", "cantidad_texto": "2 u", "unidad_receta": "u"},
        ],
    )

    total_esperado = Decimal("1.866666666666666666666666667") + Decimal("1.6")
    assert resultado["coste_total"] == pytest.approx(float(total_esperado.quantize(Decimal("0.000001"))), abs=1e-6)
    assert resultado["coste_completo"] is True
    assert resultado["coste_parcial"] is False
    assert resultado["lineas_sin_coste"] == []

    esc = Escandallo(
        receta=Receta(
            codigo="REC-TEST-SEM",
            nombre="Semantica",
            rendimiento=1.0,
            unidad_rendimiento="u",
            ingredientes=[
                Ingrediente(
                    codigo="ART-1",
                    nombre="Huevos 6u",
                    cantidad=7.0,
                    unidad="u",
                    precio_unitario=0.26666666666666666,
                )
            ],
        ),
        coste_total=1.8666666666666667,
    )
    payload = escandallo_a_dict(esc)
    restaurado = escandallo_desde_dict(payload)
    assert restaurado.coste_total == pytest.approx(1.8666666666666667)

    payload_null = dict(payload)
    payload_null["escandallo"] = dict(payload["escandallo"])
    payload_null["escandallo"]["coste_total"] = None
    with pytest.raises(ValueError):
        escandallo_desde_dict(payload_null)
