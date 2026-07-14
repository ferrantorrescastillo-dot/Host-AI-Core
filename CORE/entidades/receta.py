
from dataclasses import dataclass, field
from .ingrediente import Ingrediente
@dataclass
class Receta:
    codigo:str
    nombre:str
    rendimiento:float
    unidad_rendimiento:str
    ingredientes:list[Ingrediente]=field(default_factory=list)
