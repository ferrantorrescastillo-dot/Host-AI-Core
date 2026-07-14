import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.validador_recepcion_mercancia_442 import ValidadorRecepcionMercancia442


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Arroz bomba", "proveedor": "Makro", "familia": "Arroces y cereales", "precio": 3.0},
        {"codigo": "ART000002", "nombre": "Aceite oliva", "proveedor": "Makro", "familia": "Aceites", "precio": 5.0},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_articulos = Path(tmpdir) / "articulos.json"
        ruta_json = Path(tmpdir) / "borrador.json"
        ruta_txt = Path(tmpdir) / "borrador.txt"
        ruta_articulos.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")

        validador = ValidadorRecepcionMercancia442(str(ruta_articulos))
        borrador = validador.validar_guardar_y_exportar(
            "De Makro han llegado 15 kg arroz bomba a 3,20 €/kg, 2 kg producto nuevo",
            str(ruta_json),
            str(ruta_txt),
        )

        assert borrador.total_lineas == 2
        assert borrador.estado == "requiere_revision"
        assert borrador.lineas_validadas[0].codigo_articulo == "ART000001"
        assert borrador.lineas_validadas[0].accion_sugerida == "entrada_stock"
        assert borrador.lineas_validadas[1].accion_sugerida == "crear_articulo_pendiente"
        assert ruta_json.exists()
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.4.2 Validador Recepción Mercancía")
    print("Estado:", borrador.estado)
    print("Líneas:", borrador.total_lineas)


if __name__ == "__main__":
    main()
