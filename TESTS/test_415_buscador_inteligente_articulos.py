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
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_db = Path(tmpdir) / "articulos.json"
        ruta_db.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

        buscador = BuscadorInteligenteArticulos415(str(ruta_db))

        informe = buscador.buscar("aceite")
        assert informe.encontrado
        assert informe.mejor_resultado.codigo == "ART000001"

        informe_error_escritura = buscador.buscar("tomate perra")
        assert informe_error_escritura.encontrado
        assert informe_error_escritura.mejor_resultado.codigo == "ART000004"

        informe_proveedor = buscador.buscar("arroz", proveedor="Makro")
        assert informe_proveedor.encontrado
        assert informe_proveedor.mejor_resultado.codigo == "ART000002"

        informe_lista = buscador.listar_por_proveedor("Makro")
        assert informe_lista.total_resultados == 2

    print("TEST OK - Host AI 4.1.5 Buscador Inteligente de Artículos")
    print("Búsqueda por nombre: OK")
    print("Búsqueda con error leve: OK")
    print("Filtro proveedor secundario: OK")


if __name__ == "__main__":
    main()
