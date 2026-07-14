from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class IngredienteExtraido555B:
    nombre: str
    cantidad: float
    unidad: str
    fila_origen: int
    precio_unitario: float | None = None
    coste_racion: float | None = None
    articulo_encontrado: bool | None = None
    avisos: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FichaTecnicaExtraida555B:
    hoja: str
    fila_inicio: int
    fila_fin: int
    nombre: str
    rendimiento: float | None
    unidad_rendimiento: str | None
    ingredientes: list[IngredienteExtraido555B] = field(default_factory=list)
    confianza: float = 0.0
    avisos: list[str] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)

    @property
    def valida_para_importar(self) -> bool:
        return bool(self.nombre and self.rendimiento and self.rendimiento > 0 and self.ingredientes and not self.errores)

    def to_dict(self) -> dict[str, Any]:
        datos = asdict(self)
        datos["ingredientes"] = [i.to_dict() for i in self.ingredientes]
        datos["valida_para_importar"] = self.valida_para_importar
        return datos


@dataclass(slots=True)
class ResultadoExtraccionFichas555B:
    archivo: str
    fichas: list[FichaTecnicaExtraida555B] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        validas = sum(1 for ficha in self.fichas if ficha.valida_para_importar)
        return {
            "archivo": self.archivo,
            "fichas": [f.to_dict() for f in self.fichas],
            "resumen": {
                "fichas_detectadas": len(self.fichas),
                "fichas_validas_para_importar": validas,
                "fichas_a_revisar": len(self.fichas) - validas,
                "ingredientes_extraidos": sum(len(f.ingredientes) for f in self.fichas),
            },
            "errores": list(self.errores),
            "avisos": list(self.avisos),
            "modo": "vista_previa_solo_lectura",
            "escandallos_importados": 0,
            "datos_reales_modificados": False,
        }
