from __future__ import annotations

import base64

from SERVICIOS.analizador_importacion_restaurante import RestaurantDataImportAnalyzer


class FakeAmbiguityResolver:
    def __init__(self) -> None:
        self.calls = 0

    def resolve(self, region: dict) -> dict:
        self.calls += 1
        return {
            "tipo_region": "DESCONOCIDA",
            "mapping": {},
            "confidence": 0.5,
        }


def _csv_file(name: str, text: str) -> dict:
    return {
        "nombre": name,
        "tipo_mime": "text/csv",
        "contenido_base64": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "texto": text,
    }


def test_fase1_fallback_sin_ia_conserva_determinismo_y_dudas() -> None:
    resolver = FakeAmbiguityResolver()
    analyzer = RestaurantDataImportAnalyzer(ambiguity_resolver=resolver)
    result = analyzer.analyze({
        "archivos": [
            _csv_file("recetas.csv", "Receta,Ingrediente,Cantidad,Unidad\nRomesco,Tomate,1,kg\n"),
            _csv_file("dudas.csv", "Campo raro,Otro\nSalsa Romesco,1\n"),
        ],
        "resolver_ambiguedades_ia": False,
    })

    assert result["recetas"][0]["nombre"] == "Romesco"
    assert result["regiones_ambiguas"]
    assert result["propuestas_ia"] == []
    assert result["coste_ia"]["llamadas"] == 0
    assert result["datos_operativos_modificados"] is False
    assert resolver.calls == 0


def test_fase1_escala_deduplica_layouts_antes_de_llamar_a_ia() -> None:
    resolver = FakeAmbiguityResolver()
    analyzer = RestaurantDataImportAnalyzer(ambiguity_resolver=resolver)
    appearances = 40
    result = analyzer.analyze({
        "archivos": [
            _csv_file(f"repeticion-{index}.csv", "Campo raro,Otro\nRomesco,1\n")
            for index in range(appearances)
        ],
        "resolver_ambiguedades_ia": True,
    })

    metrics = result["coste_ia"]
    assert metrics["apariciones"] == appearances
    assert metrics["conceptos_unicos"] == 1
    assert metrics["conceptos_enviados"] == 1
    assert metrics["llamadas"] == resolver.calls == 1
    assert metrics["respuestas_reutilizadas"] == appearances - 1
    assert metrics["ahorro_llamadas_deduplicacion"] == appearances - 1
    assert metrics["tokens_reportados"] is None
    assert metrics["coste_reportado"] is None
    assert result["datos_operativos_modificados"] is False
