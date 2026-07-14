
from dataclasses import dataclass
from .receta import Receta
@dataclass
class Escandallo:
    receta:Receta
    coste_total:float=0.0
