from __future__ import annotations

import base64
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from MODELOS.importador_inteligente_biblioteca import (
    Confidence,
    DocumentSection,
    DocumentType,
    ExtractedEntity,
    ImportDocument,
    Proposal,
    ProposalStatus,
    ProposalType,
)
from SERVICIOS.centro_importacion_601 import (
    DocumentoImportacion601,
    FlujoImportacionUnificado601,
    LectorExcel601,
    LectorImagen601,
    LectorPdf601,
    LectorTexto601,
    LectorWord601,
)


class DocumentClassifier(Protocol):
    def classify(self, *, filename: str, text: str) -> tuple[DocumentType, Confidence]: ...


class DocumentInterpreter(Protocol):
    def interpret(self, *, filename: str, content: bytes, text: str) -> DocumentoImportacion601: ...


class KnowledgeExtractor(Protocol):
    def extract(
        self,
        document: DocumentoImportacion601,
        document_type: DocumentType,
    ) -> tuple[list[DocumentSection], list[ExtractedEntity], dict[str, Any]]: ...


class ProposalBuilder(Protocol):
    def build(
        self,
        *,
        import_id: str,
        document_type: DocumentType,
        entities: list[ExtractedEntity],
        context: dict[str, Any],
        origin: dict[str, Any],
    ) -> list[Proposal]: ...


class RuleBasedDocumentClassifier:
    """Clasificador determinista y sustituible por IA sin cambiar el servicio."""

    RULES: tuple[tuple[DocumentType, tuple[str, ...]], ...] = (
        (DocumentType.FACTURA, ("factura", "base imponible", "numero factura")),
        (DocumentType.ALBARAN, ("albaran", "entrega mercancia")),
        (DocumentType.COMPRA, ("pedido de compra", "proveedor", "compra")),
        (DocumentType.MENU, ("menu", "entrante", "primer plato", "segundo plato")),
        (DocumentType.FICHA_TECNICA, ("ficha tecnica", "appcc", "alergenos")),
        (DocumentType.ESCANDALLO, ("escandallo", "coste unitario", "coste linea")),
        (DocumentType.RECETA, ("receta", "ingredientes", "procedimiento", "elaboracion")),
    )

    @staticmethod
    def _norm(value: str) -> str:
        text = unicodedata.normalize("NFKD", str(value or "").lower())
        return " ".join("".join(c for c in text if not unicodedata.combining(c)).split())

    def classify(self, *, filename: str, text: str) -> tuple[DocumentType, Confidence]:
        sample = self._norm(f"{filename}\n{text[:12000]}")
        for document_type, markers in self.RULES:
            matches = [marker for marker in markers if marker in sample]
            if matches:
                score = min(0.95, 0.62 + (0.1 * len(matches)))
                return document_type, Confidence(score, f"Marcadores detectados: {', '.join(matches)}.")
        if Path(filename).suffix.lower() in {".pdf", ".docx", ".xlsx", ".jpg", ".jpeg", ".png", ".txt"}:
            return DocumentType.DOCUMENTACION, Confidence(
                0.4, "Formato reconocido sin marcadores funcionales suficientes."
            )
        return DocumentType.DESCONOCIDO, Confidence(0.2, "No se detectó un tipo documental conocido.")


class ExistingReadersDocumentInterpreter:
    """Adapta los lectores 6.0.1; los bytes solo existen durante la interpretación."""

    READERS = {
        ".docx": LectorWord601,
        ".xlsx": LectorExcel601,
        ".pdf": LectorPdf601,
        ".jpg": LectorImagen601,
        ".jpeg": LectorImagen601,
        ".png": LectorImagen601,
    }

    def interpret(self, *, filename: str, content: bytes, text: str) -> DocumentoImportacion601:
        suffix = Path(filename).suffix.lower()
        if suffix in {"", ".txt"}:
            document = LectorTexto601().leer(text or content.decode("utf-8", errors="replace"))
            document.etiqueta_origen = filename or "texto_pegado"
            return document
        reader_type = self.READERS.get(suffix)
        if reader_type is None:
            return DocumentoImportacion601(
                origen="DESCONOCIDO",
                etiqueta_origen=filename,
                advertencias=[f"Formato no admitido: {suffix or 'sin extensión'}."],
            )
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp.write(content)
                temp_path = Path(temp.name)
            document = reader_type().leer(str(temp_path))
            document.etiqueta_origen = filename
            document.archivos = []
            return document
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)


class ExistingFlowKnowledgeExtractor:
    """Proyecta el contexto no persistente del flujo de importación certificado."""

    def __init__(self, base_dir: Path) -> None:
        self.flow = FlujoImportacionUnificado601(base_dir)

    def extract(
        self,
        document: DocumentoImportacion601,
        document_type: DocumentType,
    ) -> tuple[list[DocumentSection], list[ExtractedEntity], dict[str, Any]]:
        if document_type == DocumentType.ESCANDALLO:
            document.tipo_contenido = "ESCANDALLOS"
        elif document_type == DocumentType.MENU:
            document.tipo_contenido = "MENUS"
        else:
            document.tipo_contenido = "RECETAS"
        context = self.flow.ejecutar(document) if document.texto.strip() else {
            "resumen": {"mensaje": "Contenido pendiente de extracción especializada."},
            "recetas": [],
            "ingredientes": [],
            "productos_nuevos": [],
            "incidencias": [],
        }
        sections = self._sections(document.texto)
        entities = self._entities(context)
        return sections, entities, context

    @staticmethod
    def _sections(text: str) -> list[DocumentSection]:
        lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
        if not lines:
            return []
        title = lines[0][:200]
        fields: dict[str, Any] = {"contenido": lines[1:50]}
        return [DocumentSection("SEC-001", title, "contenido_detectado", fields)]

    @staticmethod
    def _entities(context: dict[str, Any]) -> list[ExtractedEntity]:
        entities: list[ExtractedEntity] = []
        for index, recipe in enumerate(list(context.get("recetas") or []), 1):
            data = dict(recipe) if isinstance(recipe, dict) else {"nombre": str(recipe)}
            name = str(data.get("nombre") or data.get("receta") or f"Receta {index}")
            entities.append(ExtractedEntity(
                f"ENT-REC-{index:03d}", "RECETA", name, data,
                Confidence(0.75, "Estructura detectada por el flujo de importación 6.0.1."),
            ))
        for index, ingredient in enumerate(list(context.get("ingredientes") or []), 1):
            data = dict(ingredient) if isinstance(ingredient, dict) else {"nombre": str(ingredient)}
            name = str(data.get("nombre") or data.get("ingrediente") or f"Ingrediente {index}")
            entities.append(ExtractedEntity(
                f"ENT-ING-{index:03d}", "INGREDIENTE", name, data,
                Confidence(0.7, "Ingrediente detectado por el flujo de importación 6.0.1."),
            ))
        return entities


class ReviewOnlyProposalBuilder:
    """Construye propuestas explicables; nunca invoca casos de uso de escritura."""

    def build(
        self,
        *,
        import_id: str,
        document_type: DocumentType,
        entities: list[ExtractedEntity],
        context: dict[str, Any],
        origin: dict[str, Any],
    ) -> list[Proposal]:
        proposals: list[Proposal] = []
        recipes = [entity for entity in entities if entity.kind == "RECETA"]
        for entity in recipes:
            proposals.extend([
                self._proposal(import_id, len(proposals) + 1, ProposalType.CREAR_ELABORACION, entity, origin),
                self._proposal(import_id, len(proposals) + 1, ProposalType.CREAR_RECETA, entity, origin),
            ])
        for product in list(context.get("productos_nuevos") or []):
            data = dict(product) if isinstance(product, dict) else {"nombre": str(product)}
            entity = ExtractedEntity(
                f"ENT-ART-{len(proposals) + 1:03d}",
                "ARTICULO",
                str(data.get("nombre") or data.get("producto") or "Artículo pendiente"),
                data,
                Confidence(0.6, "Producto no relacionado detectado por el flujo existente."),
            )
            proposals.append(self._proposal(
                import_id, len(proposals) + 1, ProposalType.CREAR_ARTICULO, entity, origin
            ))
        type_map = {
            DocumentType.ESCANDALLO: ProposalType.ACTUALIZAR_ESCANDALLO,
            DocumentType.FICHA_TECNICA: ProposalType.ACTUALIZAR_FICHA_TECNICA,
            DocumentType.MENU: ProposalType.CREAR_MENU,
        }
        if document_type in type_map and not proposals:
            entity = ExtractedEntity(
                "ENT-DOC-001", document_type.value, origin["nombre"], {},
                Confidence(0.5, "Tipo documental detectado; extracción detallada pendiente."),
            )
            proposals.append(self._proposal(
                import_id, 1, type_map[document_type], entity, origin
            ))
        if not proposals:
            entity = ExtractedEntity(
                "ENT-DOC-001", "DOCUMENTO", origin["nombre"], {},
                Confidence(0.4, "Documento recibido; requiere revisión humana."),
            )
            proposals.append(self._proposal(
                import_id, 1, ProposalType.REVISAR_DOCUMENTACION, entity, origin
            ))
        return proposals

    @staticmethod
    def _proposal(
        import_id: str,
        index: int,
        proposal_type: ProposalType,
        entity: ExtractedEntity,
        origin: dict[str, Any],
    ) -> Proposal:
        return Proposal(
            id=f"{import_id}-PROP-{index:03d}",
            type=proposal_type,
            status=ProposalStatus.PENDIENTE_REVISION,
            confidence=entity.confidence,
            explanation=f"Propuesta generada a partir de {entity.kind.lower()} «{entity.name}».",
            origin=dict(origin),
            payload={"entidad": entity.to_dict()},
        )


class ImportDocumentService:
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".jpg", ".jpeg", ".png", ".txt"}
    MAX_BYTES = 10 * 1024 * 1024

    def __init__(
        self,
        base_dir: Path,
        classifier: DocumentClassifier | None = None,
        interpreter: DocumentInterpreter | None = None,
        extractor: KnowledgeExtractor | None = None,
        proposal_builder: ProposalBuilder | None = None,
    ) -> None:
        self.classifier = classifier or RuleBasedDocumentClassifier()
        self.interpreter = interpreter or ExistingReadersDocumentInterpreter()
        self.extractor = extractor or ExistingFlowKnowledgeExtractor(base_dir)
        self.proposal_builder = proposal_builder or ReviewOnlyProposalBuilder()
        self._sessions: dict[str, dict[str, Any]] = {}

    def import_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        filename = Path(str(payload.get("nombre") or "documento.txt")).name
        suffix = Path(filename).suffix.lower()
        if suffix not in self.ALLOWED_EXTENSIONS:
            return self._error("unsupported_format", "Formato de documento no admitido.", 400)
        try:
            content = base64.b64decode(str(payload.get("contenido_base64") or ""), validate=True)
        except (ValueError, TypeError):
            return self._error("invalid_content", "El contenido del documento no es válido.", 400)
        text = str(payload.get("texto") or "")
        if not content and not text:
            return self._error("empty_document", "El documento está vacío.", 400)
        effective_size = len(content) if content else len(text.encode("utf-8"))
        if effective_size > self.MAX_BYTES:
            return self._error("document_too_large", "El documento supera el límite de 10 MB.", 413)
        media_type = str(payload.get("tipo_mime") or "application/octet-stream")
        document_type, classification = self.classifier.classify(filename=filename, text=text)
        interpreted = self.interpreter.interpret(
            filename=filename, content=content, text=text
        )
        if not text and interpreted.text:
            document_type, classification = self.classifier.classify(
                filename=filename, text=interpreted.text
            )
        sections, entities, context = self.extractor.extract(interpreted, document_type)
        import_id = f"IMPWEB-{uuid4().hex[:12].upper()}"
        origin = {"importacion_id": import_id, "nombre": filename, "tipo": interpreted.origen}
        proposals = self.proposal_builder.build(
            import_id=import_id,
            document_type=document_type,
            entities=entities,
            context=context,
            origin=origin,
        )
        document = ImportDocument(
            id=import_id,
            filename=filename,
            media_type=media_type,
            size=len(content) or len(text.encode("utf-8")),
            source=interpreted.origen,
            document_type=document_type,
            classification=classification,
            sections=sections,
            entities=entities,
            warnings=list(interpreted.advertencias or []),
        )
        session = {
            "documento": document.to_dict(),
            "resumen": {
                "secciones": len(sections),
                "entidades": len(entities),
                "propuestas": len(proposals),
                "incidencias": len(list(context.get("incidencias") or [])),
                "estado": "PENDIENTE_REVISION",
            },
            "propuestas": [item.to_dict() for item in proposals],
            "solo_previsualizacion": True,
            "confirmacion_disponible": False,
        }
        self._sessions[import_id] = session
        return {"ok": True, "importacion": session}

    def get_import(self, import_id: str) -> dict[str, Any]:
        session = self._sessions.get(str(import_id or ""))
        if session is None:
            return self._error("import_not_found", "Importación no encontrada.", 404)
        return {"ok": True, "importacion": session}

    def get_proposals(self, import_id: str) -> dict[str, Any]:
        session = self._sessions.get(str(import_id or ""))
        if session is None:
            return self._error("import_not_found", "Importación no encontrada.", 404)
        proposals = list(session.get("propuestas") or [])
        return {
            "ok": True,
            "importacion_id": import_id,
            "propuestas": proposals,
            "total": len(proposals),
            "solo_previsualizacion": True,
        }

    @staticmethod
    def _error(code: str, message: str, status: int) -> dict[str, Any]:
        return {"ok": False, "error": {"code": code, "message": message, "status": status}}


__all__ = [
    "DocumentClassifier",
    "DocumentInterpreter",
    "ExistingFlowKnowledgeExtractor",
    "ExistingReadersDocumentInterpreter",
    "ImportDocumentService",
    "KnowledgeExtractor",
    "ProposalBuilder",
    "ReviewOnlyProposalBuilder",
    "RuleBasedDocumentClassifier",
]
