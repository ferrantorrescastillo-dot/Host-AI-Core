from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DocumentType(str, Enum):
    RECETA = "RECETA"
    ESCANDALLO = "ESCANDALLO"
    FICHA_TECNICA = "FICHA_TECNICA"
    MENU = "MENU"
    COMPRA = "COMPRA"
    FACTURA = "FACTURA"
    ALBARAN = "ALBARAN"
    DOCUMENTACION = "DOCUMENTACION"
    DESCONOCIDO = "DESCONOCIDO"
    MIXTO = "MIXTO"


class ProposalType(str, Enum):
    CREAR_ELABORACION = "CREAR_ELABORACION"
    CREAR_RECETA = "CREAR_RECETA"
    ACTUALIZAR_RECETA = "ACTUALIZAR_RECETA"
    CREAR_ARTICULO = "CREAR_ARTICULO"
    RELACIONAR_INGREDIENTE = "RELACIONAR_INGREDIENTE"
    ACTUALIZAR_FICHA_TECNICA = "ACTUALIZAR_FICHA_TECNICA"
    ACTUALIZAR_ESCANDALLO = "ACTUALIZAR_ESCANDALLO"
    CREAR_MENU = "CREAR_MENU"
    REVISAR_DOCUMENTACION = "REVISAR_DOCUMENTACION"
    CREAR_ESCANDALLO = "CREAR_ESCANDALLO"
    GENERAR_FICHA_TECNICA = "GENERAR_FICHA_TECNICA"
    REVISAR_COINCIDENCIA = "REVISAR_COINCIDENCIA"


class ProposalStatus(str, Enum):
    PENDIENTE_REVISION = "PENDIENTE_REVISION"


@dataclass(frozen=True)
class Confidence:
    value: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"valor": round(max(0.0, min(1.0, self.value)), 4), "explicacion": self.reason}


@dataclass(frozen=True)
class DocumentSection:
    id: str
    title: str
    kind: str
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExtractedEntity:
    id: str
    kind: str
    name: str
    fields: dict[str, Any]
    confidence: Confidence

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "confidence": self.confidence.to_dict()}


@dataclass(frozen=True)
class Proposal:
    id: str
    type: ProposalType
    status: ProposalStatus
    confidence: Confidence
    explanation: str
    origin: dict[str, Any]
    payload: dict[str, Any]
    title: str = ""
    source_entity: str = ""
    source_blocks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tipo": self.type.value,
            "estado": self.status.value,
            "confianza": self.confidence.to_dict(),
            "explicacion": self.explanation,
            "titulo": self.title or self.type.value.replace("_", " ").title(),
            "origen": dict(self.origin),
            "entidad_origen": self.source_entity or None,
            "bloques_origen": list(self.source_blocks),
            "advertencias": list(self.warnings),
            "conflictos": list(self.conflicts),
            "datos_propuestos": dict(self.payload),
            "persistida": False,
        }


@dataclass(frozen=True)
class ImportDocument:
    id: str
    filename: str
    media_type: str
    size: int
    source: str
    document_type: DocumentType
    classification: Confidence
    sections: list[DocumentSection]
    entities: list[ExtractedEntity]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.filename,
            "tipo_mime": self.media_type,
            "tamano": self.size,
            "origen": self.source,
            "clasificacion": {
                "tipo": self.document_type.value,
                "confianza": self.classification.to_dict(),
                "evidencias": [self.classification.reason],
                "advertencias": list(self.warnings),
            },
            "secciones": [item.to_dict() for item in self.sections],
            "entidades": [item.to_dict() for item in self.entities],
            "advertencias": list(self.warnings),
            "contenido_almacenado": False,
        }


__all__ = [
    "Confidence",
    "DocumentSection",
    "DocumentType",
    "ExtractedEntity",
    "ImportDocument",
    "Proposal",
    "ProposalStatus",
    "ProposalType",
]
