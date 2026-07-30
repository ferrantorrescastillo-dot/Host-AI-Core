from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from zipfile import BadZipFile


logger = logging.getLogger(__name__)


class WordDocumentReadError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


@dataclass(frozen=True)
class WordDocumentBlock:
    type: str
    text: str
    order: int
    level: int | None = None
    rows: list[list[str]] = field(default_factory=list)
    source_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo": self.type,
            "texto": self.text,
            "orden": self.order,
            "nivel": self.level,
            "filas": [list(row) for row in self.rows],
            "referencia_origen": self.source_reference,
        }


@dataclass(frozen=True)
class ParsedWordDocument:
    filename: str
    blocks: list[WordDocumentBlock]
    plain_text: str
    warnings: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nombre": self.filename,
            "formato": "DOCX",
            "bloques": [block.to_dict() for block in self.blocks],
            "texto_plano": self.plain_text,
            "advertencias": list(self.warnings),
            "metadatos": dict(self.metadata),
        }


class WordDocumentReader:
    """Lector DOCX único para modo manual y adaptadores públicos."""

    def read(self, path: str | Path, filename: str | None = None) -> ParsedWordDocument:
        source = Path(path)
        try:
            from docx import Document
            from docx.table import Table
            from docx.text.paragraph import Paragraph
            from docx.opc.exceptions import PackageNotFoundError
        except ImportError as exc:
            raise WordDocumentReadError(
                "lector_no_disponible",
                "El lector Word no está disponible: falta python-docx.",
                503,
            ) from exc

        try:
            document = Document(source)
        except (PackageNotFoundError, BadZipFile, ValueError, KeyError) as exc:
            raise WordDocumentReadError(
                "documento_corrupto",
                "El archivo no es un documento DOCX válido o está protegido.",
            ) from exc
        except Exception as exc:
            logger.exception("Error interno al abrir el documento Word %s.", filename or source.name)
            raise WordDocumentReadError(
                "error_interno",
                f"No se pudo abrir el documento Word: {type(exc).__name__}.",
                500,
            ) from exc

        blocks: list[WordDocumentBlock] = []
        for item in document.iter_inner_content():
            if isinstance(item, Paragraph):
                block = self._paragraph_block(item, len(blocks))
            elif isinstance(item, Table):
                block = self._table_block(item, len(blocks))
            else:
                block = None
            if block is not None:
                blocks.append(block)

        warnings: list[str] = []
        if document.inline_shapes:
            warnings.append(
                "El documento contiene imágenes que todavía no han sido interpretadas."
            )
        if not any(block.text.strip() for block in blocks):
            raise WordDocumentReadError(
                "documento_vacio",
                "El documento Word no contiene texto ni tablas interpretables.",
            )

        plain_text = "\n".join(block.text for block in blocks if block.text.strip())
        properties = document.core_properties
        metadata = {
            "titulo": properties.title or None,
            "autor": properties.author or None,
            "bloques": len(blocks),
            "tablas": sum(block.type == "table" for block in blocks),
            "imagenes_no_interpretadas": len(document.inline_shapes),
        }
        logger.info(
            "Lector Word usado: archivo=%s bloques=%d tablas=%d advertencias=%d",
            filename or source.name,
            len(blocks),
            metadata["tablas"],
            len(warnings),
        )
        return ParsedWordDocument(
            filename=filename or source.name,
            blocks=blocks,
            plain_text=plain_text,
            warnings=warnings,
            metadata=metadata,
        )

    @staticmethod
    def _paragraph_block(paragraph: Any, order: int) -> WordDocumentBlock | None:
        text = str(paragraph.text or "").strip()
        if not text:
            return None
        style_name = str(getattr(paragraph.style, "name", "") or "")
        style_lower = style_name.lower()
        level = None
        block_type = "paragraph"
        if style_lower.startswith(("heading", "título", "titulo")):
            digits = "".join(char for char in style_name if char.isdigit())
            level = int(digits) if digits else 1
            block_type = "heading"
        elif (
            "list" in style_lower
            or "lista" in style_lower
            or (paragraph._p.pPr is not None and paragraph._p.pPr.numPr is not None)
        ):
            block_type = "list_item"
        return WordDocumentBlock(
            type=block_type,
            text=text,
            order=order,
            level=level,
            source_reference=f"bloque:{order}",
        )

    @staticmethod
    def _table_block(table: Any, order: int) -> WordDocumentBlock | None:
        rows: list[list[str]] = []
        for row in table.rows:
            values = [str(cell.text or "").strip() for cell in row.cells]
            if any(values):
                rows.append(values)
        if not rows:
            return None
        text = "\n".join(" | ".join(value for value in row if value) for row in rows)
        return WordDocumentBlock(
            type="table",
            text=text,
            order=order,
            rows=rows,
            source_reference=f"bloque:{order}",
        )


__all__ = [
    "ParsedWordDocument",
    "WordDocumentBlock",
    "WordDocumentReadError",
    "WordDocumentReader",
]
