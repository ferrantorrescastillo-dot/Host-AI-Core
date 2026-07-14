import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.generador_codigos_articulos_413 import GeneradorCodigosArticulos413


def main():
    generador = GeneradorCodigosArticulos413()

    filas = [
        {"Codigo": "", "Articulo": "Aceite oliva"},
        {"Codigo": "ART999999", "Articulo": "Arroz bomba"},
        {"Codigo": "", "Articulo": "Coca Cola"},
        {"Codigo": "DUP001", "Articulo": "Tomate"},
        {"Codigo": "DUP001", "Articulo": "Tomate cherry"},
    ]

    informe = generador.generar_para_filas(filas)

    assert informe.total_articulos == 5
    assert informe.codigos_generados == 2
    assert informe.codigos_respetados == 1
    assert informe.codigos_duplicados == 2
    assert informe.total_revisar == 2

    codigos = [item.codigo_final for item in informe.resultados]
    assert "ART000001" in codigos
    assert "ART000002" in codigos
    assert "ART999999" in codigos

    print("TEST OK - Host AI 4.1.3 Generador de Códigos Internos de Artículos")
    print("Artículos:", informe.total_articulos)
    print("Generados:", informe.codigos_generados)
    print("Duplicados:", informe.codigos_duplicados)


if __name__ == "__main__":
    main()
