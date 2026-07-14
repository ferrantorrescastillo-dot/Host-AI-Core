from pathlib import Path
class MotorMemoriaOperacional:
    def __init__(self, base_dir: Path):
        self.eventos = []
    def limpiar_memoria(self):
        self.eventos = []
    def registrar_respuesta_orquestador(self, intencion, respuesta):
        self.eventos.append({"intencion": intencion, "respuesta": respuesta})
