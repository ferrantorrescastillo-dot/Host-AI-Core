from pathlib import Path
from SERVICIOS.simulador_importacion_menus_i1341 import SimuladorImportacionMenusI1341


def _pre(bloqueado=False):
    comp = {"nombre":"Parmentier de patata","grupo":"GUARNICION","rol":"GUARNICION","catalogado":not bloqueado}
    if bloqueado:
        comp.update({"resolucion":"PROPONER_NUEVA_RECETA","estado":"PROPUESTA_NUEVA_RECETA"})
    return {
      "menus":[{"nombre":"MENU BODA","hoja":"MENU BODA 31-1","secciones":[{"nombre":"SEGUNDO"}],
        "platos":[{"nombre_original":"Solomillo con parmentier","seccion":"Segundo","fila":20,"coste_racion":1.4,"componentes":[comp]}],
        "articulos_directos":[{"nombre":"Pan","coste_racion":.2}],"complementos":[{"nombre":"Bodega"}],
        "economico":{"precio_venta":75,"venta_neta":67.5,"coste_total":8.8,"food_cost_pct":11.7,"beneficio":66.2}}],
      "bloqueos": ([{"componente":"Parmentier de patata","rol":"GUARNICION","mensaje":"No creada"}] if bloqueado else [])
    }


def test_plan_listo_no_escribe(tmp_path: Path):
    sim=SimuladorImportacionMenusI1341(tmp_path)
    plan=sim.construir_plan(_pre(False), [])
    assert plan["estado_simulacion"]=="LISTA_PARA_TRANSACCION"
    assert plan["escrituras_habilitadas"] is False
    assert any(a["entidad"]=="DATOS_ECONOMICOS" for a in plan["acciones"])


def test_plan_bloqueado_marca_componente(tmp_path: Path):
    sim=SimuladorImportacionMenusI1341(tmp_path)
    plan=sim.construir_plan(_pre(True), [])
    assert plan["estado_simulacion"]=="BLOQUEADA"
    assert plan["resumen"]["bloqueadas"]==1


def test_detecta_actualizacion_por_nombre(tmp_path: Path):
    sim=SimuladorImportacionMenusI1341(tmp_path)
    plan=sim.construir_plan(_pre(False), [{"menu_id":"MENU-1","nombre":"Menu Boda"}])
    assert any(a["tipo"]=="ACTUALIZAR" and a["entidad"]=="MENU" for a in plan["acciones"])


def test_ids_deterministas(tmp_path: Path):
    sim=SimuladorImportacionMenusI1341(tmp_path)
    a=sim.construir_plan(_pre(False), [])
    b=sim.construir_plan(_pre(False), [])
    assert a["plan_id"]==b["plan_id"]
    assert [x["accion_id"] for x in a["acciones"]]==[x["accion_id"] for x in b["acciones"]]
