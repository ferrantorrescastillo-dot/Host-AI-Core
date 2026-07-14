from pathlib import Path
import json
import tempfile
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.integracion_conversacional_datos_5414 import IntegradorConversacionalDatos5414


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "DATOS" / "db"
        db.mkdir(parents=True)
        (db / "escandallos.json").write_text(json.dumps([
            {"nombre": "Paella de marisco", "ingredientes": [{"nombre": "arroz bomba"}, {"nombre": "caldo de pescado"}]}
        ]), encoding="utf-8")
        (db / "stock_inicial.json").write_text(json.dumps([
            {"articulo": "arroz bomba", "cantidad": 20, "unidad": "kg"},
            {"articulo": "caldo de pescado", "cantidad": 40, "unidad": "l"}
        ]), encoding="utf-8")
        (db / "articulos.json").write_text(json.dumps([
            {"nombre": "arroz bomba", "proveedor": "Makro"},
            {"nombre": "caldo de pescado", "proveedor": "Proveedor Mar"}
        ]), encoding="utf-8")
        (db / "proveedores.json").write_text("[]", encoding="utf-8")
        integrador = IntegradorConversacionalDatos5414(base)
        resultado = integrador.preparar_contexto({"tipo": "boda", "personas": 150, "menu": "paella"})
        assert resultado["ok"] is True
        assert len(resultado["menus_encontrados"]) == 1
        assert resultado["stock"]["total"] == 2
        assert len(resultado["proveedores"]) == 2
        assert resultado["datos_reales_modificados"] is False
        assert resultado["listo_para_motores"] is True
    print("TEST OK 5.4.14 Integracion Conversacional Completa")


if __name__ == "__main__":
    main()
