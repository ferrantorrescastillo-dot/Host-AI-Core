from pathlib import Path

from SERVICIOS.lanzador_host_ai_base_603 import LanzadorHostAIBase603


BASE_DIR = Path(__file__).resolve().parents[1]


def test_603_estructura_operativa_disponible():
    estado = LanzadorHostAIBase603(BASE_DIR).validar_estructura()
    assert estado.ok is True
    assert all(estado.elementos.values())


def test_603_menu_separa_producto_y_herramientas():
    salidas = []
    entradas = iter(["0"])
    lanzador = LanzadorHostAIBase603(BASE_DIR)

    lanzador.ejecutar_menu(
        input_fn=lambda _mensaje: next(entradas),
        print_fn=lambda *args: salidas.append(" ".join(map(str, args))),
    )

    texto = "\n".join(salidas)
    assert "Host AI Base (modo manual)" in texto
    assert "Hablar con Host AI" in texto
    assert "Herramientas técnicas y pruebas" in texto
    assert "Saliendo de Host AI" in texto
