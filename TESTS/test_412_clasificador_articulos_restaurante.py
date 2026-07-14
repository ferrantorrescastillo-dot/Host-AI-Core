import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.clasificador_inteligente_articulos_412 import ClasificadorInteligenteArticulos412


def main():
    clasificador = ClasificadorInteligenteArticulos412()

    filas = [
        {"Codigo": "", "Articulo": "A.P BROCHETA DE POLLO CON SALSA KARE.", "Proveedor": "M.P APERITIVOS.", "Familia": "", "Precio": "0,56"},
        {"Codigo": "", "Articulo": "M.P HARINA FUERZA", "Proveedor": "M.P", "Familia": "", "Precio": "1.20"},
        {"Codigo": "", "Articulo": "COCA COLA 33CL", "Proveedor": "", "Familia": "", "Precio": "0.70"},
        {"Codigo": "", "Articulo": "CAJA CARTON TAKE AWAY", "Proveedor": "", "Familia": "", "Precio": "0.12"},
        {"Codigo": "", "Articulo": "MENU BBQ FIN DE SEMANA", "Proveedor": "", "Familia": "", "Precio": "45"},
    ]

    informe = clasificador.clasificar_filas(filas)

    assert informe.total_articulos == 5
    tipos = [item.tipo_sugerido for item in informe.clasificaciones]

    assert "APERITIVO" in tipos
    assert "MATERIA_PRIMA" in tipos
    assert "BEBIDA" in tipos
    assert "CONSUMIBLE" in tipos
    assert "MENU" in tipos

    print("TEST OK - Host AI 4.1.2 Clasificador Inteligente de Artículos")
    print("Artículos:", informe.total_articulos)
    print("Resumen tipos:", informe.resumen_tipos)
    print("A revisar:", informe.total_revisar)


if __name__ == "__main__":
    main()
