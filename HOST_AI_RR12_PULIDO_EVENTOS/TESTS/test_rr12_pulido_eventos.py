from APP.consola import AppConsolaHostAI
from MOTORES.motor_eventos import MotorEventos


class DBMemoria:
    def __init__(self):
        self.datos = {"eventos": []}
    def cargar(self, coleccion):
        return list(self.datos.get(coleccion, []))
    def guardar(self, coleccion, datos):
        self.datos[coleccion] = list(datos)


class Escandallos:
    def listar(self):
        return [{"receta_id": "REC-CARRILLERA", "nombre": "Carrillera melosa"}]


class Core:
    def __init__(self):
        self.eventos = MotorEventos(DBMemoria())
        self.escandallos_inteligente = Escandallos()


def test_rr12_linea_temporal_agrupa_pases_y_muestra_nombres(capsys):
    core = Core()
    evento = core.eventos.crear_evento("Boda RR1", "20/09/2026", 120)
    core.eventos.agregar_servicio(evento.id, "Cóctel", "coctel", "13:30", 180)
    core.eventos.agregar_servicio(evento.id, "Banquete", "banquete", "15:00", 150)
    banquete = core.eventos.obtener(evento.id).servicios[1]
    core.eventos.agregar_pase(evento.id, banquete.id, "Entrante", "15:10", 40, ["REC-CARRILLERA"])

    app = AppConsolaHostAI(core)
    app.ultimo_evento_id = evento.id
    app._ver_linea_temporal_evento_activo()
    salida = capsys.readouterr().out

    assert "15:00  SERVICIO  Banquete" in salida
    assert "15:10  PASE      Entrante" in salida
    assert "Recetas: Carrillera melosa" in salida
    assert "Total servicios: 2 | Pases: 1 | Recetas: 1" in salida
