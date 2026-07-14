import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.gestor_base_datos_definitiva_451 import GestorBaseDatosDefinitiva451


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        db_dir = base / "DATOS" / "db"
        db_dir.mkdir(parents=True)
        (db_dir / "articulos.json").write_text(json.dumps([
            {"codigo": "ART000001", "nombre": "Arroz bomba", "familia": "Arroces", "proveedor": "Makro", "unidad": "kg", "precio": "3,20"}
        ], ensure_ascii=False), encoding="utf-8")
        (db_dir / "proveedores.json").write_text(json.dumps([
            {"nombre": "Makro", "nif": "B00000000"}
        ], ensure_ascii=False), encoding="utf-8")

        gestor = GestorBaseDatosDefinitiva451(base)
        inicial = gestor.inicializar()
        assert inicial["ok"] is True
        assert (db_dir / "host_ai.db").exists()
        estado = gestor.estado()
        for tabla in ["restaurantes", "articulos", "proveedores", "stock_movimientos", "pedidos", "recepciones", "historico_precios", "configuracion", "logs_ejecucion"]:
            assert tabla in estado["tablas"]

        migracion = gestor.migrar_json_basico()
        assert migracion["ok"] is True
        assert migracion["articulos"] == 1
        assert migracion["proveedores"] == 1
        estado2 = gestor.estado()
        assert estado2["conteos"]["articulos"] == 1
        assert estado2["conteos"]["proveedores"] == 1

    print("TEST OK - Host AI 4.5.1 Base de Datos Definitiva")


if __name__ == "__main__":
    main()
