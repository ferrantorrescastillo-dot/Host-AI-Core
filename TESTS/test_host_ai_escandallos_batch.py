from SERVICIOS.host_ai_escandallos_read_service import HostAIEscandallosReadService


class _Biblioteca:
    def detalle(self, identity):
        if identity == "REC-OK":
            return {"ok": True, "elaboracion": {"id": identity, "nombre": "Receta", "receta": {"ingredientes": []}}}
        return {"ok": False}


def test_detalle_lote_devuelve_detalles_y_faltantes_sin_escritura(tmp_path) -> None:
    service = HostAIEscandallosReadService(tmp_path, biblioteca=_Biblioteca())

    result = service.consultar(escandallo_ids=["REC-OK", "REC-AUSENTE", "REC-OK"])

    assert result["estado"] == "PARCIAL"
    assert result["batch_size"] == 2
    assert result["total_encontrados"] == 1
    assert result["no_encontrados"] == ["REC-AUSENTE"]
    assert result["datos_reales_modificados"] is False