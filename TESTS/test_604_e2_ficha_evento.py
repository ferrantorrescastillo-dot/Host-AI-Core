from datetime import date
from pathlib import Path

import pytest

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from MOTORES.motor_eventos import MotorEventos


def resolver(core, intencion, parametros=None):
    return core.orquestador.resolver(SolicitudHostAI(intencion, parametros or {}))


def test_e2_fecha_flexible_y_ficha_completa_persistente(tmp_path: Path):
    core = HostAICore(tmp_path)
    creado = resolver(core, "crear_evento", {
        "nombre": "Boda E2",
        "fecha": "22/10/2026",
        "pax": 120,
        "tipo": "boda",
        "cliente": "Laura y Pau",
        "telefono": "600123123",
        "email": "laura@example.com",
        "ubicacion": "Masía del Mar",
        "hora_inicio": "13:30",
        "observaciones": "Alergia grave a frutos secos",
        "estado": "confirmado",
    })
    assert creado.ok
    evento = creado.datos["evento"]
    assert evento["fecha"] == "2026-10-22"
    assert evento["telefono"] == "600123123"
    assert evento["email"] == "laura@example.com"
    assert evento["hora_inicio"] == "13:30"
    assert evento["observaciones"] == "Alergia grave a frutos secos"
    assert evento["estado"] == "confirmado"

    evento_id = evento["id"]
    editado = resolver(core, "editar_evento", {
        "evento_id": evento_id,
        "cambios": {"fecha": "23 octubre 2026", "estado": "producción", "telefono": ""},
    })
    assert editado.ok
    assert editado.datos["evento"]["fecha"] == "2026-10-23"
    assert editado.datos["evento"]["estado"] == "produccion"
    assert editado.datos["evento"]["telefono"] == ""

    core_recargado = HostAICore(tmp_path)
    recuperado = core_recargado.eventos.obtener(evento_id)
    assert recuperado.cliente == "Laura y Pau"
    assert recuperado.email == "laura@example.com"
    assert recuperado.estado == "produccion"


def test_e2_fechas_naturales_y_validaciones():
    referencia = date(2026, 7, 10)  # viernes
    assert MotorEventos.normalizar_fecha("hoy", referencia) == "2026-07-10"
    assert MotorEventos.normalizar_fecha("mañana", referencia) == "2026-07-11"
    assert MotorEventos.normalizar_fecha("lunes", referencia) == "2026-07-13"
    assert MotorEventos.normalizar_fecha("22 de octubre de 2026", referencia) == "2026-10-22"
    assert MotorEventos.normalizar_fecha("22-10-26", referencia) == "2026-10-22"
    with pytest.raises(ValueError):
        MotorEventos.normalizar_fecha("un día raro", referencia)
    with pytest.raises(ValueError):
        MotorEventos.normalizar_estado("inventado")
    with pytest.raises(ValueError):
        MotorEventos.normalizar_hora("25:80")
