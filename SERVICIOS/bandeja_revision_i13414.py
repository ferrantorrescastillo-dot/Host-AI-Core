from __future__ import annotations
from pathlib import Path
from SERVICIOS.bandeja_revision_i13413 import BandejaRevisionI13413, formatear_bandeja_i13413
from SERVICIOS.simulador_importacion_menus_i13414 import SimuladorImportacionMenusI13414

class BandejaRevisionI13414(BandejaRevisionI13413):
    VERSION = 'I1.3.4.1.4'
    def __init__(self, base_dir: str | Path):
        super().__init__(base_dir)
        self.simulador = SimuladorImportacionMenusI13414(base_dir)
        self.dir_sesiones = self.base_dir / 'DATOS' / 'mur' / 'revisiones_i13414'

def formatear_bandeja_i13414(sesion, solo_pendientes=True):
    texto = formatear_bandeja_i13413(sesion, solo_pendientes)
    return texto.replace('I1.3.4.1.3 — BANDEJA', 'I1.3.4.1.4 — INTERPRETACIÓN CULINARIA + BANDEJA')
