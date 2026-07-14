from pathlib import Path

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def resolver(core, intencion, parametros=None):
    return core.orquestador.resolver(SolicitudHostAI(intencion, parametros or {}))


def test_e1_crud_busqueda_duplicado_y_persistencia(tmp_path: Path):
    core = HostAICore(tmp_path)

    creado = resolver(core, "crear_evento", {
        "nombre": "Boda E1",
        "fecha": "2026-10-22",
        "pax": 80,
        "tipo": "boda",
        "cliente": "Ana y Marc",
        "ubicacion": "Masía",
    })
    assert creado.ok
    evento_id = creado.datos["evento"]["id"]

    listado = resolver(core, "listar_eventos")
    assert listado.ok
    assert len(listado.datos["eventos"]) == 1

    buscado = resolver(core, "buscar_eventos", {"texto": "Ana"})
    assert buscado.ok
    assert buscado.datos["eventos"][0]["id"] == evento_id

    editado = resolver(core, "editar_evento", {
        "evento_id": evento_id,
        "cambios": {"pax": 95, "nombre": "Boda E1 actualizada"},
    })
    assert editado.ok
    assert editado.datos["evento"]["pax"] == 95

    resolver(core, "agregar_servicio_evento", {
        "evento_id": evento_id,
        "nombre": "Cóctel",
        "hora_inicio": "13:00",
    })
    servicio_id = core.eventos.obtener(evento_id).servicios[0].id
    resolver(core, "agregar_pase_evento", {
        "evento_id": evento_id,
        "servicio_id": servicio_id,
        "nombre": "Aperitivo",
        "hora_inicio": "13:30",
        "recetas": ["REC-CARRILLERA"],
    })

    duplicado = resolver(core, "duplicar_evento", {
        "evento_id": evento_id,
        "nombre": "Boda E1 duplicada",
        "fecha": "2026-10-29",
    })
    assert duplicado.ok
    duplicado_id = duplicado.datos["evento"]["id"]
    assert duplicado_id != evento_id
    assert duplicado.datos["evento"]["servicios"][0]["id"] != servicio_id
    assert duplicado.datos["evento"]["servicios"][0]["pases"][0]["id"] != core.eventos.obtener(evento_id).servicios[0].pases[0].id

    # A fresh core must recover both events automatically from the local DB.
    core_recargado = HostAICore(tmp_path)
    assert len(core_recargado.eventos.listar_eventos()) == 2
    assert core_recargado.eventos.obtener(evento_id).pax == 95

    eliminado = resolver(core_recargado, "eliminar_evento", {"evento_id": evento_id})
    assert eliminado.ok
    assert len(core_recargado.eventos.listar_eventos()) == 1

    core_final = HostAICore(tmp_path)
    assert [e.id for e in core_final.eventos.listar_eventos()] == [duplicado_id]
