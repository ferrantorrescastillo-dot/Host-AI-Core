from SERVICIOS.import_ambiguity_resolver import resolve_regions_once, sanitize_proposal


class FakeResolver:
    def __init__(self): self.calls = 0
    def resolve(self, region):
        self.calls += 1
        return {"tipo_region": "RECETA", "mapping": {"ARTICULO": "ingrediente"},
                "confidence": .9, "proveedor": "inventado", "stock": 99}


def region(identifier):
    return {"region_id": identifier, "headers": ["ARTICULO", "NETO"],
            "opciones_permitidas": ["ingrediente", "cantidad"], "duda": "mapping"}


def test_layout_repetido_se_resuelve_una_vez_y_sigue_siendo_propuesta():
    fake = FakeResolver()
    proposals, calls = resolve_regions_once([region(str(i)) for i in range(20)], fake)
    assert calls == fake.calls == 1
    assert len(proposals) == 20
    assert all(item["status"] == "PROPUESTA_PENDIENTE_REVISION" for item in proposals)
    assert all("stock" not in item and "proveedor" not in item for item in proposals)


def test_respuesta_invalida_descarta_mapping_y_no_se_convierte_en_verdad():
    result = sanitize_proposal({"tipo_region": "RECETA", "mapping": {
        "INEXISTENTE": "stock", "ARTICULO": "ingrediente"}}, region("R1"))
    assert result["valid"] is False
    assert result["mapping"] == {"ARTICULO": "ingrediente"}
    assert result["status"] == "PROPUESTA_PENDIENTE_REVISION"
