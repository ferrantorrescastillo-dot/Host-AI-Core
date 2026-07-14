from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RelacionArticulo555B:
    ingrediente: str
    estado: str
    articulo_id: str | None = None
    articulo_nombre: str | None = None
    confianza: float = 0.0
    candidatos: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FichaPreimportacion555B:
    codigo: str
    nombre: str
    estado: str
    accion: str
    motivo: str
    hoja: str
    fila_inicio: int
    fila_fin: int
    rendimiento: float
    unidad_rendimiento: str
    ingredientes: list[dict[str, Any]] = field(default_factory=list)
    relaciones_articulos: list[RelacionArticulo555B] = field(default_factory=list)
    grupo_duplicado: str | None = None
    tipo_duplicado: str | None = None
    confianza: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "codigo": self.codigo,
            "nombre": self.nombre,
            "estado": self.estado,
            "accion": self.accion,
            "motivo": self.motivo,
            "hoja": self.hoja,
            "fila_inicio": self.fila_inicio,
            "fila_fin": self.fila_fin,
            "rendimiento": self.rendimiento,
            "unidad_rendimiento": self.unidad_rendimiento,
            "ingredientes": list(self.ingredientes),
            "relaciones_articulos": [r.to_dict() for r in self.relaciones_articulos],
            "grupo_duplicado": self.grupo_duplicado,
            "tipo_duplicado": self.tipo_duplicado,
            "confianza": self.confianza,
        }


@dataclass(slots=True)
class ResultadoPreimportacion555B:
    archivo_excel: str
    ruta_destino: str
    modo: str
    fichas: list[FichaPreimportacion555B] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    copia_seguridad: str | None = None
    importados: int = 0
    datos_reales_modificados: bool = False

    def to_dict(self) -> dict[str, Any]:
        resumen = {
            "fichas_analizadas": len(self.fichas),
            "crear": sum(1 for f in self.fichas if f.accion == "CREAR"),
            "actualizar": sum(1 for f in self.fichas if f.accion == "ACTUALIZAR"),
            "sin_cambios": sum(1 for f in self.fichas if f.accion == "SIN_CAMBIOS"),
            "omitidas": sum(1 for f in self.fichas if f.accion == "OMITIR"),
            "a_revisar": sum(1 for f in self.fichas if f.estado == "REVISAR"),
            "ingredientes_enlazados": sum(
                1 for f in self.fichas for r in f.relaciones_articulos if r.estado == "ENLAZADO"
            ),
            "ingredientes_sin_enlace": sum(
                1 for f in self.fichas for r in f.relaciones_articulos if r.estado == "SIN_ENLACE"
            ),
            "ingredientes_con_candidatos": sum(
                1 for f in self.fichas for r in f.relaciones_articulos if r.estado == "CANDIDATOS"
            ),
            "importados": self.importados,
        }
        return {
            "archivo_excel": self.archivo_excel,
            "ruta_destino": self.ruta_destino,
            "modo": self.modo,
            "fichas": [f.to_dict() for f in self.fichas],
            "resumen": resumen,
            "errores": list(self.errores),
            "copia_seguridad": self.copia_seguridad,
            "datos_reales_modificados": self.datos_reales_modificados,
        }
