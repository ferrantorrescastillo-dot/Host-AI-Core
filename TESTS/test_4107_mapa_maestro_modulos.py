from pathlib import Path
import tempfile

from SERVICIOS.mapa_maestro_modulos_4107 import generar_mapa_maestro, formatear_mapa_maestro, bloque_por_codigo


def main() -> None:
    assert bloque_por_codigo("481") == "4.8 Rentabilidad"
    assert bloque_por_codigo("4107") == "4.10 Auditoria/Cierre"
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        for carpeta in ["APP", "SERVICIOS", "TESTS", "DOCS"]:
            (raiz / carpeta).mkdir()
        (raiz / "APP" / "coste_real_receta_481.py").write_text("", encoding="utf-8")
        (raiz / "SERVICIOS" / "panel_ia_central_497.py").write_text("", encoding="utf-8")
        (raiz / "TESTS" / "test_4107_mapa_maestro_modulos.py").write_text("", encoding="utf-8")
        (raiz / "APP" / "legacy.py").write_text("", encoding="utf-8")
        resultado = generar_mapa_maestro(raiz)
        assert resultado["total_archivos_mapeados"] == 4
        assert len(resultado["bloques"]["4.8 Rentabilidad"]) == 1
        assert len(resultado["bloques"]["4.9 IA Operativa"]) == 1
        assert len(resultado["bloques"]["4.10 Auditoria/Cierre"]) == 1
        assert len(resultado["historicos"]) == 1
        texto = formatear_mapa_maestro(resultado)
        assert "HOST AI 4.10.7" in texto
        assert "4.8 Rentabilidad" in texto
    print("OK test_4107_mapa_maestro_modulos")


if __name__ == "__main__":
    main()
