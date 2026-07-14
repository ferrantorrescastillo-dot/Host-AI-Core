from pathlib import Path
import tempfile

from MOTORES.motor_eventos import MotorEventos


class DBMemoria:
    def __init__(self):
        self.datos = {"eventos": []}
    def cargar(self, coleccion):
        return list(self.datos.get(coleccion, []))
    def guardar(self, coleccion, datos):
        self.datos[coleccion] = list(datos)


def test_e3_flujo_operativo_eventos():
    db = DBMemoria()
    motor = MotorEventos(db)
    evento = motor.crear_evento("Boda E3", "22/10/2026", 80, cliente="Ana")
    motor.agregar_servicio(evento.id, "Cóctel", "coctel", "13:00", 90)
    servicio = motor.obtener(evento.id).servicios[0]
    motor.agregar_pase(evento.id, servicio.id, "Entrante", "13:30", 35, ["REC-CARRILLERA"], "Caliente")
    pase = motor.obtener(evento.id).servicios[0].pases[0]

    linea = motor.construir_linea_temporal(evento.id)
    assert [x["tipo"] for x in linea["linea_temporal"]] == ["servicio", "pase"]
    assert linea["linea_temporal"][1]["recetas"] == ["REC-CARRILLERA"]

    motor.editar_servicio(evento.id, servicio.id, {"hora_inicio": "12:45", "duracion_min": 100})
    motor.editar_pase(evento.id, servicio.id, pase.id, {"nombre": "Primer pase", "recetas": ["REC-CARRILLERA", "REC-CARRILLERA"]})
    assert motor.obtener(evento.id).servicios[0].hora_inicio == "12:45"
    assert motor.obtener(evento.id).servicios[0].pases[0].recetas == ["REC-CARRILLERA"]

    motor.duplicar_pase(evento.id, servicio.id, pase.id)
    assert len(motor.obtener(evento.id).servicios[0].pases) == 2
    assert len({p.id for p in motor.obtener(evento.id).servicios[0].pases}) == 2

    motor.duplicar_servicio(evento.id, servicio.id)
    assert len(motor.obtener(evento.id).servicios) == 2
    assert len({s.id for s in motor.obtener(evento.id).servicios}) == 2

    resumen = motor.resumen_ejecutivo(evento.id)
    assert resumen["totales"]["servicios"] == 2
    assert resumen["totales"]["pases"] == 4
    assert resumen["estado_operativo"] == "listo"

    recargado = MotorEventos(db)
    assert len(recargado.obtener(evento.id).servicios) == 2
    assert recargado.construir_linea_temporal(evento.id)["linea_temporal"]

    segundo = recargado.obtener(evento.id).servicios[1]
    recargado.eliminar_pase(evento.id, segundo.id, segundo.pases[0].id)
    recargado.eliminar_servicio(evento.id, segundo.id)
    assert len(recargado.obtener(evento.id).servicios) == 1
