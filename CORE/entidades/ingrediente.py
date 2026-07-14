
from dataclasses import dataclass, field
from typing import Optional
@dataclass(slots=True)
class Ingrediente:
    codigo:str
    nombre:str
    cantidad:float
    unidad:str
    merma_pct:float=0.0
    articulo_id:Optional[str]=None
    proveedor_habitual:Optional[str]=None
    precio_unitario:float=0.0
    observaciones:str=""
    metadata:dict=field(default_factory=dict)
