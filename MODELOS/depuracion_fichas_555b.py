from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class IncidenciaDepuracion555B:
    codigo: str
    nivel: str
    mensaje: str
    campo: str | None = None
    valor_original: Any = None
    valor_propuesto: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FichaDepurada555B:
    id_origen: str
    hoja: str
    fila_inicio: int
    fila_fin: int
    nombre_original: str
    nombre_normalizado: str
    rendimiento: float | None
    unidad_rendimiento: str | None
    ingredientes: list[dict[str, Any]] = field(default_factory=list)
    incidencias: list[IncidenciaDepuracion555B] = field(default_factory=list)
    elaboraciones_referenciadas: list[str] = field(default_factory=list)
    grupo_duplicado: str | None = None
    tipo_duplicado: str | None = None
    confianza_final: float = 0.0
    estado: str = "REVISAR"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id_origen": self.id_origen,
            "hoja": self.hoja,
            "fila_inicio": self.fila_inicio,
            "fila_fin": self.fila_fin,
            "nombre_original": self.nombre_original,
            "nombre_normalizado": self.nombre_normalizado,
            "rendimiento": self.rendimiento,
            "unidad_rendimiento": self.unidad_rendimiento,
            "ingredientes": list(self.ingredientes),
            "incidencias": [i.to_dict() for i in self.incidencias],
            "elaboraciones_referenciadas": list(self.elaboraciones_referenciadas),
            "grupo_duplicado": self.grupo_duplicado,
            "tipo_duplicado": self.tipo_duplicado,
            "confianza_final": self.confianza_final,
            "estado": self.estado,
        }


@dataclass(slots=True)
class ResultadoDepuracion555B:
    archivo: str
    fichas: list[FichaDepurada555B] = field(default_factory=list)
    grupos_duplicados: list[dict[str, Any]] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        preparadas = sum(1 for f in self.fichas if f.estado == "PREPARADA")
        revisar = sum(1 for f in self.fichas if f.estado == "REVISAR")
        rechazadas = sum(1 for f in self.fichas if f.estado == "RECHAZADA")
        return {
            "archivo": self.archivo,
            "fichas": [f.to_dict() for f in self.fichas],
            "grupos_duplicados": list(self.grupos_duplicados),
            "resumen": {
                "fichas_analizadas": len(self.fichas),
                "preparadas": preparadas,
                "a_revisar": revisar,
                "rechazadas": rechazadas,
                "grupos_duplicados": len(self.grupos_duplicados),
                "elaboraciones_referenciadas": sum(len(f.elaboraciones_referenciadas) for f in self.fichas),
                "incidencias": sum(len(f.incidencias) for f in self.fichas),
            },
            "errores": list(self.errores),
            "modo": "vista_previa_depurada_solo_lectura",
            "escandallos_importados": 0,
            "datos_reales_modificados": False,
        }
