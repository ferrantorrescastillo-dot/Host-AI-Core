import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.informe_pendientes_familia_4110 import InformePendientesFamilia4110


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Aceite", "familia": "Aceites", "proveedor": "Makro", "precio": 8.5, "origen": "excel"},
        {"codigo": "ART000002", "nombre": "Producto raro", "familia": "", "proveedor": "Makro", "precio": 1.2, "origen": "excel"},
        {"codigo": "ART000003", "nombre": "Otro raro", "familia": None, "proveedor": "", "precio": None, "origen": "alta_manual_416"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_db = Path(tmpdir) / "articulos.json"
        ruta_txt = Path(tmpdir) / "pendientes.txt"
        ruta_db.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

        generador = InformePendientesFamilia4110(str(ruta_db))
        informe = generador.exportar_txt(str(ruta_txt))

        assert informe.total_articulos == 3
        assert informe.pendientes == 2
        assert informe.estado == "revisar"
        assert informe.por_proveedor["Makro"] == 1
        assert informe.por_proveedor["SIN_PROVEEDOR"] == 1
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.1.10 Informe Pendientes de Familia")
    print("Pendientes:", informe.pendientes)
    print("Estado:", informe.estado)


if __name__ == "__main__":
    main()
