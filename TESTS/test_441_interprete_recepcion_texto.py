import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.interprete_recepcion_texto_441 import InterpreteRecepcionTexto441


def main():
    interprete = InterpreteRecepcionTexto441()

    texto = "De Makro han llegado 15 kg arroz bomba a 3,20 €/kg, 6 l aceite oliva y 4 cajas coca cola"
    resultado = interprete.interpretar(texto)

    assert resultado.estado == "ok"
    assert resultado.proveedor_general == "Makro"
    assert resultado.total_lineas == 3

    arroz = resultado.lineas[0]
    assert arroz.producto == "arroz bomba"
    assert arroz.cantidad == 15
    assert arroz.unidad == "kg"
    assert arroz.proveedor == "Makro"
    assert arroz.precio_unitario == 3.20

    aceite = resultado.lineas[1]
    assert aceite.producto == "aceite oliva"
    assert aceite.unidad == "l"

    coca = resultado.lineas[2]
    assert coca.unidad == "caja"

    print("TEST OK - Host AI 4.4.1 Intérprete Recepción Texto")
    print("Líneas detectadas:", resultado.total_lineas)


if __name__ == "__main__":
    main()
