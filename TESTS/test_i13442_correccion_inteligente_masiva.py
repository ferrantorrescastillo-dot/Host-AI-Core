import json
from pathlib import Path

from SERVICIOS.bandeja_correccion_inteligente_i13442 import BandejaCorreccionInteligenteI13442
from SERVICIOS.diagnostico_correccion_inteligente_i13442 import DiagnosticoCorreccionInteligenteI13442


def write(root, rel, data):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def fixture(tmp_path):
    menus = [{
        "menu_id": "M1", "nombre": "Menu", "secciones": [{"seccion_id": "S1", "nombre": "Principal"}],
        "platos": [
            {"plato_id": "P1", "nombre": "Crema catalana", "seccion": "Postre", "componentes": []},
            {"plato_id": "P2", "nombre": "Ambiguo", "seccion": "Principal", "componentes": []},
        ],
        "articulos_directos": [{"nombre": "Pan"}], "bebidas": [], "complementos": [], "servicios": [],
        "economico": {"precio_venta": 10, "coste_total": 3, "food_cost_pct": 99, "beneficio": None},
        "resumen": {"secciones": 1, "platos": 2, "componentes": 0, "articulos_directos": 1, "bebidas": 0, "complementos": 0},
    }]
    recetas = [{"receta_id": "R1", "nombre": "Crema catalana"}]
    articulos = [{"codigo": "A1", "nombre": "Pan"}]
    write(tmp_path, "menus.json", menus)
    write(tmp_path, "recetas.json", recetas)
    write(tmp_path, "articulos.json", articulos)
    return BandejaCorreccionInteligenteI13442(tmp_path, "menus.json", "recetas.json", "articulos.json")


def test_agrupar_y_filtrar(tmp_path):
    b = fixture(tmp_path)
    assert b.agrupar_por_tipo()
    assert b.agrupar_por_menu()[0]["menu"] == "Menu"
    assert all(x[1]["severidad"] == "AVISO" for x in b.incidencias_filtradas(severidad="AVISO"))


def test_resolucion_univoca_conserva_ambiguo(tmp_path):
    b = fixture(tmp_path)
    r = b.resolver_automaticamente_univocos()
    assert r["resueltas"] >= 3
    assert b.resumen()["total"] == 1
    assert b.incidencias()[0]["codigo"] == "PLATO_SIN_RECETA_PRINCIPAL"


def test_indices_por_tipo_y_menu(tmp_path):
    b = fixture(tmp_path)
    assert b.indices_por_codigo("SECCION_REFERENCIA_INEXISTENTE")
    assert len(b.indices_por_menu("Menu")) == b.resumen()["total"]


def test_no_escribe_antes_de_guardar(tmp_path):
    b = fixture(tmp_path)
    p = tmp_path / "menus.json"
    before = p.read_bytes()
    b.resolver_automaticamente_univocos()
    assert p.read_bytes() == before


def test_guardar_despues_de_auto(tmp_path):
    b = fixture(tmp_path)
    b.resolver_automaticamente_univocos()
    # Eliminamos el único caso ambiguo para completar el diagnóstico de escritura.
    b.eliminar([1])
    r = b.guardar(confirmar=True)
    assert r["transaccion"]["estado"] == "COMMIT"
    assert Path(r["transaccion"]["backup_dir"]).exists()


def test_diagnostico(tmp_path):
    r = DiagnosticoCorreccionInteligenteI13442(tmp_path).ejecutar()
    assert r["diagnostico"] == "OK"
    assert r["final"]["total"] == 1
