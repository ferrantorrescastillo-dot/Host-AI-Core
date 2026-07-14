import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.buscador_inteligente_articulos_415 import BuscadorInteligenteArticulos415


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Aceite oliva virgen extra", "proveedor": "Makro", "familia": "Aceites", "precio": 8.5},
        {"codigo": "ART000002", "nombre": "Arroz bomba", "proveedor": "Makro", "familia": "Arroces", "precio": 3.2},
        {"codigo": "ART000003", "nombre": "Coca Cola 33cl", "proveedor": "Distribuidor Bebidas", "familia": "Bebidas", "precio": 0.7},
        {"codigo": "ART000004", "nombre": "Tomate pera", "proveedor": "Verduras Penedes", "familia": "Verduras", "precio": 1.4},
        {"codigo": "ART000005", "nombre": "Aros metalicos 6 moldes", "proveedor": "Makro", "familia": "Utillaje", "precio": 21.9},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_db = Path(tmpdir) / "articulos.json"
        ruta_db.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")
        buscador = BuscadorInteligenteArticulos415(str(ruta_db))

        informe = buscador.buscar("arroz bomba")
        assert informe.encontrado
        assert informe.mejor_resultado.codigo == "ART000002"

        informe_makro = buscador.buscar("arroz bomba", proveedor="Makro")
        assert informe_makro.encontrado
        assert informe_makro.mejor_resultado.codigo == "ART000002"

        codigos = [item.codigo for item in informe_makro.resultados]
        assert "ART000005" not in codigos

        informe_no = buscador.buscar("arroz bomba", proveedor="Distribuidor Bebidas")
        assert informe_no.total_resultados == 0

        diagnostico = buscador.diagnosticar("makro")
        assert diagnostico.total_resultados >= 2

    print("TEST OK - Host AI 4.1.5.1 Buscador Inteligente Mejorado")
    print("Falsos positivos reducidos: OK")
    print("Diagnóstico: OK")


if __name__ == "__main__":
    main()
