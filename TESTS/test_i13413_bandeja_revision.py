from pathlib import Path
from SERVICIOS.bandeja_revision_i13413 import BandejaRevisionI13413


def _plan():
    return {
        "plan_id": "PLAN-X", "estado_simulacion": "BLOQUEADA", "bloqueos": [{"componente": "nuez"}],
        "acciones": [
            {"accion_id":"A1","tipo":"RESOLVER_ANTES_DE_IMPORTAR","entidad":"COMPONENTE_PENDIENTE","nombre":"Nuez moscada","estado":"BLOQUEADA","detalle":{"menu":"M1","plato":"Crema"}},
            {"accion_id":"A2","tipo":"CREAR_RELACION","entidad":"COMPLEMENTO","nombre":"Calçots en tempura","estado":"PLANIFICADA","detalle":{"menu":"M1"}},
            {"accion_id":"A3","tipo":"REGISTRAR","entidad":"DATOS_ECONOMICOS","nombre":"M1","estado":"PLANIFICADA","detalle":{"menu":"M1"}},
        ],
        "resumen":{"acciones":3,"ejecutables":2,"bloqueadas":1,"vincular":0,"relaciones":1},
        "integridad":{"sin_escrituras":True},
    }


def test_crea_bandeja_con_bloqueo_y_aviso(tmp_path: Path):
    b=BandejaRevisionI13413(tmp_path)
    s=b.crear_sesion(_plan())
    assert s["resumen_revision"]["iniciales"] == 2
    assert s["resumen_revision"]["bloqueantes"] == 1
    assert Path(s["ruta_sesion"]).exists()


def test_eliminacion_masiva_solo_modifica_plan_sesion(tmp_path: Path):
    b=BandejaRevisionI13413(tmp_path); s=b.crear_sesion(_plan())
    s=b.aplicar_masiva(s,"1,2","ELIMINAR")
    assert s["resumen_revision"]["eliminadas"] == 2
    assert [a["accion_id"] for a in s["plan"]["acciones"]] == ["A3"]
    assert s["plan"]["estado_simulacion"] == "LISTA_PARA_TRANSACCION"


def test_reclasificacion_masiva(tmp_path: Path):
    b=BandejaRevisionI13413(tmp_path); s=b.crear_sesion(_plan())
    s=b.aplicar_masiva(s,"2","CLASIFICAR",clasificacion="PLATO_RECETA")
    a=next(a for a in s["plan"]["acciones"] if a["accion_id"]=="A2")
    assert a["entidad"] == "PLATO_MENU"
    assert a["estado"] == "PLANIFICADA"


def test_vincular_resuelve_bloqueo(tmp_path: Path):
    b=BandejaRevisionI13413(tmp_path); s=b.crear_sesion(_plan())
    s=b.vincular(s,1,"ARTICULO","Nuez moscada molida")
    a=next(a for a in s["plan"]["acciones"] if a["accion_id"]=="A1")
    assert a["tipo"] == "VINCULAR"
    assert a["estado"] == "PLANIFICADA"
    assert s["resumen_revision"]["bloqueantes"] == 0


def test_renombrar_y_aprender(tmp_path: Path):
    b=BandejaRevisionI13413(tmp_path); s=b.crear_sesion(_plan())
    s=b.renombrar(s,2,"Calçots en tempura",recordar=True)
    assert b.ruta_aprendizaje.exists()


def test_mantener_bloqueante_no_desbloquea(tmp_path: Path):
    b=BandejaRevisionI13413(tmp_path); s=b.crear_sesion(_plan())
    s=b.aplicar_masiva(s,"1","MANTENER")
    assert s["resumen_revision"]["bloqueantes"] == 1
    assert s["plan"]["estado_simulacion"] == "BLOQUEADA"
