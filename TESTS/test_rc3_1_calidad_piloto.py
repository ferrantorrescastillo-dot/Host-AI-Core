from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.validador_calidad_piloto import ValidadorCalidadPiloto


def ejecutar_prueba():
    validador = ValidadorCalidadPiloto()

    articulo_ok = validador.validar_articulo({
        "nombre": "Aceite oliva",
        "unidad": "l",
        "precio": 5.20,
        "stock": 12,
        "proveedor": "Proveedor A",
    })
    assert articulo_ok.ok
    assert articulo_ok.total_criticas == 0

    articulo_mal = validador.validar_articulo({
        "nombre": "",
        "unidad": "",
        "precio": "abc",
        "stock": -2,
    })
    assert not articulo_mal.ok
    assert articulo_mal.total_criticas >= 2

    factura_mal = validador.validar_lineas_factura([
        {"nombre": "Tomate", "cantidad": 10, "precio": 2.1},
        {"nombre": "", "cantidad": 0, "precio": -1},
    ])
    assert not factura_mal.ok
    assert factura_mal.total_incidencias >= 3

    receta_mal = validador.validar_receta({
        "nombre": "Paella prueba",
        "raciones": 0,
        "precio_venta": 0,
        "ingredientes": [
            {"nombre": "Arroz", "cantidad": 1, "coste": 2},
            {"nombre": "", "cantidad": -1, "coste": -3},
        ],
    })
    assert not receta_mal.ok

    produccion_mal = validador.validar_produccion({
        "elaboracion": "",
        "cantidad": -5,
        "tiempo_minutos": -10,
    })
    assert not produccion_mal.ok

    paquete = validador.validar_paquete_piloto({
        "articulo": {"nombre": "Harina", "unidad": "kg", "precio": 1.1, "stock": 20, "proveedor": "Proveedor B"},
        "lineas_factura": [{"nombre": "Harina", "cantidad": 20, "precio": 1.1}],
        "receta": {"nombre": "Masa", "raciones": 10, "precio_venta": 4, "ingredientes": [{"nombre": "Harina", "cantidad": 1, "coste": 1.1}]},
        "produccion": {"elaboracion": "Masa", "cantidad": 10, "tiempo_minutos": 45},
    })
    assert paquete.ok

    print("TEST OK - Host AI RC3.1 Calidad para Piloto")
    print("Validaciones: articulo, factura, receta, produccion y paquete piloto")


if __name__ == "__main__":
    ejecutar_prueba()
