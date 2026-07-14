from __future__ import annotations

import json
from pathlib import Path

from SERVICIOS.certificador_final_importador_i135 import CertificadorFinalImportadorI135
from SERVICIOS.utilidades_importador_i135 import (
    agrupar_incidencias,
    coincidencias_exactas,
    filtrar_incidencias,
    fingerprint_incidencia,
)


def test_utilidades_incidencias_centralizadas():
    incidencias = [
        {"codigo": "A", "severidad": "ERROR", "menu": "Menú Uno", "plato": "P1", "referencia": "R1"},
        {"codigo": "A", "severidad": "AVISO", "menu": "Menú Uno", "plato": "P2", "referencia": "R2"},
        {"codigo": "B", "severidad": "AVISO", "menu": "Menú Dos", "plato": "P3", "referencia": "R3"},
    ]
    assert fingerprint_incidencia(incidencias[0])[0] == "A"
    assert len(filtrar_incidencias(incidencias, severidad="AVISO")) == 2
    assert len(filtrar_incidencias(incidencias, codigo="A")) == 2
    assert len(filtrar_incidencias(incidencias, menu="uno")) == 2
    grupos = agrupar_incidencias(incidencias, campo="codigo", valor_vacio="SIN_CODIGO")
    assert grupos[0]["codigo"] == "A"
    assert grupos[0]["cantidad"] == 2


def test_coincidencias_exactas_deduplicadas():
    catalogo = [
        {"receta_id": "R1", "nombre": "Crema catalana"},
        {"receta_id": "R1", "nombre": "Crema catalana"},
        {"receta_id": "R2", "nombre": "Otra"},
    ]
    encontrados = coincidencias_exactas(catalogo, "crema catalana", ("nombre",))
    assert len(encontrados) == 1
    assert encontrados[0]["receta_id"] == "R1"


def test_certificacion_final_es_solo_lectura(tmp_path: Path):
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    menus = [{"menu_id": "M1", "nombre": "Menú", "secciones": [], "platos": []}]
    (db / "menus.json").write_text(json.dumps(menus), encoding="utf-8")
    (db / "escandallos.json").write_text("[]", encoding="utf-8")
    (db / "articulos.json").write_text("[]", encoding="utf-8")
    antes = (db / "menus.json").read_bytes()
    resultado = CertificadorFinalImportadorI135(tmp_path).ejecutar()
    assert resultado["estado"] == "CERTIFICADO"
    assert resultado["solo_lectura"] is True
    assert resultado["modulos_ok"] == resultado["modulos_total"]
    assert (db / "menus.json").read_bytes() == antes
    assert Path(resultado["informe_json"]).exists()
    assert Path(resultado["informe_txt"]).exists()
