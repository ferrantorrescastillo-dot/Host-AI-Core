
from dataclasses import dataclass, field
from .receta import Receta
@dataclass
class Menu:
    nombre:str
    recetas:list[Receta]=field(default_factory=list)
