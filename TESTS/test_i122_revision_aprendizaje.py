from pathlib import Path

from SERVICIOS.importador_seguro_escandallos_i12 import ImportadorSeguroEscandallosI12


class DetectorFake:
    def analizar(self, *_args, **_kwargs):
        return {
            "escandallos": [{
                "hoja": "MP boda",
                "nombre": "Sorbete mandarina",
                "rendimiento_cantidad": 58,
                "rendimiento_unidad": "u",
                "tipo": "receta",
                "avisos": [],
                "ingredientes": [{
                    "nombre": "Zumo naranja 1,5 Lt. pack de 6",
                    "cantidad": 1.5,
                    "unidad": "L",
                    "precio_unitario": 3.26,
                    "coste": 4.89,
                    "avisos": [],
                }],
            }]
        }


def catalogo():
    return [
        {"codigo": "ART1", "nombre": "Zumo de Naranja 6x250 ml", "proveedor": "A"},
        {"codigo": "ART2", "nombre": "Zumo naranja 1,5 Lt", "proveedor": "B"},
    ]


def test_revision_manual_resuelve_y_recalcula(tmp_path: Path):
    ruta = tmp_path / "memoria.json"
    imp = ImportadorSeguroEscandallosI12(detector=DetectorFake(), ruta_memoria=ruta)
    previa = imp.preparar("fake.xlsx", catalogo_articulos=catalogo())
    assert previa["resumen"]["vinculos_probables"] == 1
    ok = imp.aplicar_decision(
        previa,
        "Zumo naranja 1,5 Lt. pack de 6",
        {"articulo_id": "ART2", "nombre": "Zumo naranja 1,5 Lt"},
        recordar=True,
    )
    assert ok is True
    assert previa["resumen"]["vinculos_exactos"] == 1
    assert previa["resumen"]["vinculos_probables"] == 0
    ing = previa["recetas"][0]["ingredientes"][0]
    assert ing["articulo_id"] == "ART2"
    assert ing["estado"] == "exacto"
    assert ruta.exists()


def test_memoria_se_reutiliza_en_segunda_importacion(tmp_path: Path):
    ruta = tmp_path / "memoria.json"
    imp = ImportadorSeguroEscandallosI12(detector=DetectorFake(), ruta_memoria=ruta)
    previa = imp.preparar("fake.xlsx", catalogo_articulos=catalogo())
    imp.aplicar_decision(
        previa,
        "Zumo naranja 1,5 Lt. pack de 6",
        {"articulo_id": "ART2", "nombre": "Zumo naranja 1,5 Lt"},
        recordar=True,
    )
    segunda = imp.preparar("fake.xlsx", catalogo_articulos=catalogo())
    ing = segunda["recetas"][0]["ingredientes"][0]
    assert ing["estado"] == "exacto"
    assert ing["articulo_id"] == "ART2"
    assert "aprendido" in ing["motivo_vinculo"]


def test_pendientes_revision_agrupa_repetidos(tmp_path: Path):
    imp = ImportadorSeguroEscandallosI12(detector=DetectorFake(), ruta_memoria=tmp_path / "m.json")
    previa = imp.preparar("fake.xlsx", catalogo_articulos=catalogo())
    previa["recetas"].append(previa["recetas"][0].copy())
    pendientes = imp.pendientes_revision(previa)
    assert len(pendientes) == 1
