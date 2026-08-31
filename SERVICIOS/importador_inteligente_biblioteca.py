from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
import tempfile
import unicodedata
from copy import deepcopy
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
)
from SERVICIOS.extractor_recetas_word import WordRecipeExtractor
from SERVICIOS.borrador_importacion_biblioteca import (
    ArticleCandidateFinder,
    CanonicalRecipeMatcher,
    DraftConflictError,
    DraftValidationError,
    ImportDraftService,
    normalize_text,
)
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from SERVICIOS.lector_word_documentos import WordDocumentReadError, WordDocumentReader
from SERVICIOS.confirmacion_importacion_biblioteca import (
    ImportConfirmationService,
    ImportSessionRepository,
)
from SERVICIOS.canonicalizacion_recetas_legacy_service import (
    LEGACY_WITHOUT_CANONICAL,
    LegacyCanonicalizationError,
    LegacyRecipeCanonicalizationService,
)
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.analizador_importacion_restaurante import (
    RestaurantDataImportAnalyzer,
    RestaurantImportAnalysisError,
)
from SERVICIOS.analizador_importacion_hibrido import HybridRestaurantImportAnalyzer
from SERVICIOS.hostai_import_package_adapter import PreparedImportPackageAdapter
from MODELOS.hostai_import_package import HostAIImportPackageError
from SERVICIOS.ai_import_document_interpreter import AIImportDocumentInterpreter, AIImportInterpretationError
from SERVICIOS.repository_initialization_policy import non_persistent_repository_initialization
from SERVICIOS.menu_importacion_biblioteca import project_menu_imports
from SERVICIOS.import_ambiguity_resolver import (
    HostAIEngineImportAmbiguityResolver,
    ImportAmbiguityResolver,
)


logger = logging.getLogger(__name__)


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
        if suffix == ".docx":
            return self._interpret_word(filename, content)
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

    @staticmethod
    def _interpret_word(filename: str, content: bytes) -> DocumentoImportacion601:
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp:
                temp.write(content)
                temp_path = Path(temp.name)
            parsed = WordDocumentReader().read(temp_path, filename=filename)
            return DocumentoImportacion601(
                origen="WORD",
                etiqueta_origen=filename,
                texto=parsed.plain_text,
                archivos=[],
                advertencias=list(parsed.warnings),
                payload={"documento_estructurado": parsed.to_dict()},
            )
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)


class ExistingFlowKnowledgeExtractor:
    """Proyecta el contexto no persistente del flujo de importación certificado."""

    def __init__(self, base_dir: Path) -> None:
        self.flow = FlujoImportacionUnificado601(base_dir)
        self.word_recipes = WordRecipeExtractor(base_dir)

    def extract(
        self,
        document: DocumentoImportacion601,
        document_type: DocumentType,
    ) -> tuple[list[DocumentSection], list[ExtractedEntity], dict[str, Any]]:
        structured = dict((document.payload or {}).get("documento_estructurado") or {})
        if document.origen == "WORD" and structured:
            blocks = list(structured.get("bloques") or [])
            context = self.word_recipes.extract(blocks)
            return self._structured_sections(blocks), self._entities(context), context
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
    def _structured_sections(blocks: list[dict[str, Any]]) -> list[DocumentSection]:
        sections: list[DocumentSection] = []
        for index, block in enumerate(blocks, 1):
            text = str(block.get("texto") or "").strip()
            if not text:
                continue
            sections.append(DocumentSection(
                id=f"SEC-{index:03d}",
                title=text[:200],
                kind=str(block.get("tipo") or "unknown"),
                fields={
                    "nivel": block.get("nivel"),
                    "filas": list(block.get("filas") or []),
                    "orden": block.get("orden"),
                    "referencia_origen": block.get("referencia_origen"),
                },
            ))
        return sections

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
            name = str(
                data.get("nombre_original")
                or data.get("nombre")
                or data.get("ingrediente")
                or f"Ingrediente {index}"
            )
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
        for entity in [item for item in entities if item.kind == "RECETA"]:
            match = dict(entity.fields.get("coincidencia_biblioteca") or {})
            state = str(match.get("estado") or "nueva_entidad")
            if state == "coincidencia_exacta":
                proposals.append(self._proposal(
                    import_id, len(proposals) + 1, ProposalType.ACTUALIZAR_RECETA,
                    entity, origin, conflicts=list(match.get("candidatos") or []),
                ))
            elif state == "posible_duplicado":
                proposals.append(self._proposal(
                    import_id, len(proposals) + 1, ProposalType.REVISAR_COINCIDENCIA,
                    entity, origin, conflicts=list(match.get("candidatos") or []),
                ))
            else:
                proposals.append(self._proposal(
                    import_id, len(proposals) + 1, ProposalType.CREAR_RECETA, entity, origin,
                    title=f"Crear elaboración/receta canónica: {entity.name}",
                    explanation=(
                        "Una única operación conceptual crea la ficha culinaria canónica; "
                        "no son dos entidades independientes."
                    ),
                ))

        for entity in [item for item in entities if item.kind == "INGREDIENTE"]:
            state = str(entity.fields.get("estado_relacion") or "sin_relacionar")
            proposal_type = {
                "relacionado": ProposalType.RELACIONAR_INGREDIENTE,
                "coincidencia_dudosa": ProposalType.REVISAR_COINCIDENCIA,
                "sin_relacionar": ProposalType.CREAR_ARTICULO,
            }.get(state, ProposalType.REVISAR_COINCIDENCIA)
            proposals.append(self._proposal(
                import_id,
                len(proposals) + 1,
                proposal_type,
                entity,
                origin,
                conflicts=list(entity.fields.get("candidatos") or []),
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
            proposals.append(self._proposal(import_id, 1, type_map[document_type], entity, origin))
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
        conflicts: list[dict[str, Any]] | None = None,
        title: str | None = None,
        explanation: str | None = None,
    ) -> Proposal:
        source_blocks = list(entity.fields.get("bloques_origen") or [])
        if entity.fields.get("bloque_origen"):
            source_blocks.append(str(entity.fields["bloque_origen"]))
        return Proposal(
            id=f"{import_id}-PROP-{index:03d}",
            type=proposal_type,
            status=ProposalStatus.PENDIENTE_REVISION,
            confidence=entity.confidence,
            explanation=explanation or f"Propuesta generada a partir de {entity.kind.lower()} «{entity.name}».",
            origin=dict(origin),
            payload={"entidad": entity.to_dict()},
            title=title or f"{proposal_type.value.replace('_', ' ').title()}: {entity.name}",
            source_entity=entity.id,
            source_blocks=source_blocks,
            warnings=list(entity.fields.get("advertencias") or []),
            conflicts=list(conflicts or []),
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
        ambiguity_resolver: ImportAmbiguityResolver | None = None,
        ai_document_interpreter: AIImportDocumentInterpreter | None = None,
    ) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.classifier = classifier or RuleBasedDocumentClassifier()
        self.interpreter = interpreter or ExistingReadersDocumentInterpreter()
        with non_persistent_repository_initialization():
            self.extractor = extractor or ExistingFlowKnowledgeExtractor(base_dir)
            self.drafts = ImportDraftService(base_dir)
            self.legacy_canonicalization = LegacyRecipeCanonicalizationService(base_dir)
        self.proposal_builder = proposal_builder or ReviewOnlyProposalBuilder()
        self.ambiguity_resolver = ambiguity_resolver
        self.ai_document_interpreter = ai_document_interpreter
        self.repository = ImportSessionRepository(base_dir, persistent=False)
        self.confirmations = ImportConfirmationService(base_dir, self.repository)
        self._sessions = self.repository.load_all()

    def import_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        with non_persistent_repository_initialization():
            return self._import_document_read_only(payload)

    def _import_document_read_only(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("archivos") is not None or payload.get("texto_pegado") or payload.get("hostai_import_package") is not None:
            return self._import_restaurant_data(payload)
        filename = Path(str(payload.get("nombre") or "documento.txt")).name
        suffix = Path(filename).suffix.lower()
        if suffix not in self.ALLOWED_EXTENSIONS:
            return self._error("formato_no_soportado", "Formato de documento no admitido.", 400)
        try:
            content = base64.b64decode(str(payload.get("contenido_base64") or ""), validate=True)
        except (ValueError, TypeError):
            return self._error("contenido_no_interpretable", "El contenido del documento no es válido.", 400)
        text = str(payload.get("texto") or "")
        if not content and not text:
            return self._error("documento_vacio", "El documento está vacío.", 400)
        effective_size = len(content) if content else len(text.encode("utf-8"))
        if effective_size > self.MAX_BYTES:
            return self._error("document_too_large", "El documento supera el límite de 10 MB.", 413)
        media_type = str(payload.get("tipo_mime") or "application/octet-stream")
        document_type, classification = self.classifier.classify(filename=filename, text=text)
        try:
            interpreted = self.interpreter.interpret(
                filename=filename, content=content, text=text
            )
        except WordDocumentReadError as exc:
            return self._error(exc.code, str(exc), exc.status)
        except Exception as exc:
            logger.exception("Error interno al interpretar %s.", filename)
            return self._error(
                "error_interno",
                f"No se pudo interpretar el documento: {type(exc).__name__}.",
                500,
            )
        if not text and interpreted.texto:
            document_type, classification = self.classifier.classify(
                filename=filename, text=interpreted.texto
            )
        sections, entities, context = self.extractor.extract(interpreted, document_type)
        detected_recipes = list(context.get("recetas") or [])
        if detected_recipes:
            document_type = (
                DocumentType.RECETA
                if document_type in {
                    DocumentType.DOCUMENTACION,
                    DocumentType.DESCONOCIDO,
                    DocumentType.RECETA,
                }
                else DocumentType.MIXTO
            )
            classification = Confidence(
                min(0.92, 0.72 + (0.05 * len(detected_recipes))),
                (
                    f"Se detectaron {len(detected_recipes)} recetas delimitadas "
                    "por la estructura y el contenido del documento."
                ),
            )
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
                "recetas_detectadas": len(list(context.get("recetas") or [])),
                "ingredientes_detectados": len(list(context.get("ingredientes") or [])),
                "ingredientes_relacionados": sum(
                    item.get("estado_relacion") == "relacionado"
                    for item in list(context.get("ingredientes") or [])
                ),
                "coincidencias_dudosas": sum(
                    item.get("estado_relacion") == "coincidencia_dudosa"
                    for item in list(context.get("ingredientes") or [])
                ),
                "ingredientes_sin_relacionar": sum(
                    item.get("estado_relacion") == "sin_relacionar"
                    for item in list(context.get("ingredientes") or [])
                ),
                "ingredientes_nuevos": sum(
                    item.get("estado_relacion") == "sin_relacionar"
                    for item in list(context.get("ingredientes") or [])
                ),
                "duplicados_detectados": sum(
                    str((item.get("coincidencia_biblioteca") or {}).get("estado") or "")
                    in {"coincidencia_exacta", "posible_duplicado"}
                    for item in list(context.get("recetas") or [])
                ),
                "estado": "PENDIENTE_REVISION",
            },
            "propuestas": [item.to_dict() for item in proposals],
            "solo_previsualizacion": True,
            "confirmacion_disponible": True,
            "estado": "PENDIENTE_REVISION",
            "historial": [],
            "limitaciones": [
                "Las imágenes incrustadas no se interpretan en esta fase.",
                "Los documentos ambiguos requieren revisión humana.",
            ],
        }
        session["borrador"] = self.drafts.build(
            import_id=import_id,
            classification=document_type.value,
            confidence=classification.value,
            recipes=list(context.get("recetas") or []),
        )
        logger.info(
            "Importación interpretada: lector=%s tipo=%s secciones=%d entidades=%d propuestas=%d advertencias=%d",
            interpreted.origen,
            document_type.value,
            len(sections),
            len(entities),
            len(proposals),
            len(interpreted.advertencias or []),
        )
        self._sessions[import_id] = session
        self.repository.save_all(self._sessions)
        return {"ok": True, "importacion": session}

    def _import_restaurant_data(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            package_adapter = PreparedImportPackageAdapter()
            if package_adapter.can_handle(payload):
                analysis = package_adapter.analyze(payload)
            elif payload.get("analizar_documento_con_ia"):
                interpreter = self.ai_document_interpreter or AIImportDocumentInterpreter(self.base_dir)
                interpreted = interpreter.interpret(payload)
                analysis = package_adapter.analyze({"hostai_import_package": interpreted["package"]})
                analysis["ai_import"] = {
                    "used": True, "fingerprint": interpreted["fingerprint"],
                    "cache_hit": interpreted["cache_hit"], "structural_summary": interpreted["structural_summary"],
                    "usage": interpreted["usage"], "cost_breakdown": interpreted["cost_breakdown"],
                }
            else:
                resolver = self.ambiguity_resolver
                if payload.get("resolver_ambiguedades_ia") and resolver is None:
                    resolver = HostAIEngineImportAmbiguityResolver(self.base_dir)
                structural = RestaurantDataImportAnalyzer(ambiguity_resolver=resolver)
                analysis = HybridRestaurantImportAnalyzer(self.base_dir, structural).analyze(payload)
                unresolved = len(analysis.get("regiones_ambiguas") or [])
                regions = len(analysis.get("hojas") or [])
                known = bool(analysis.get("resultado_hibrido", {}).get("historico_compatible"))
                analysis["ai_import"] = {
                    "used": False, "offered": bool(not known and (unresolved >= 3 or regions >= 8)),
                    "classification": "KNOWN" if known else "COMPLEX" if (unresolved >= 3 or regions >= 8) else "BASIC",
                    "structural_summary": {"sheets": int(analysis.get("resumen", {}).get("hojas_analizadas") or 0),
                                           "regions": regions, "unresolved_regions": unresolved},
                }
        except AIImportInterpretationError as exc:
            return self._error("ai_import_interpretation_failed", str(exc), 422)
        except HostAIImportPackageError as exc:
            return self._error("hostai_import_package_invalido", str(exc), 400)
        except RestaurantImportAnalysisError as exc:
            return self._error("importacion_no_interpretable", str(exc), 400)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self._error("contenido_no_interpretable", str(exc), 400)
        except Exception as exc:
            logger.exception("Error interno al analizar una importación de restaurante.")
            return self._error("error_interno", f"No se pudo analizar la importación: {type(exc).__name__}.", 500)

        import_id = f"IMPWEB-{uuid4().hex[:12].upper()}"
        exclude_legacy_ap = bool(payload.get("excluir_ap_antiguos"))
        exclusions: list[dict[str, Any]] = []
        if exclude_legacy_ap:
            for collection in ("articulos", "recetas"):
                kept = []
                for item in list(analysis.get(collection) or []):
                    if normalize_text(item.get("nombre")).startswith("a p "):
                        exclusions.append({
                            "nombre": item.get("nombre"), "tipo_origen": collection.upper(),
                            "accion": "IGNORAR", "motivo": "Exclusión A.P confirmada para esta sesión.",
                            "origen": item.get("origen") or item.get("trazabilidad"),
                        })
                    else:
                        kept.append(item)
                analysis[collection] = kept
            for menu in analysis.get("menus") or []:
                menu["componentes"] = [
                    item for item in menu.get("componentes") or []
                    if not normalize_text(item.get("nombre")).startswith("a p ")
                ]
            analysis["exclusiones_sesion"] = exclusions
            analysis["opciones_sesion"] = {"excluir_ap_antiguos": True}
        recipes = list(analysis.get("recetas") or [])
        entities: list[ExtractedEntity] = []
        for index, recipe in enumerate(recipes, 1):
            entities.append(ExtractedEntity(
                f"ENT-REC-{index:03d}", "RECETA", str(recipe.get("nombre") or f"Receta {index}"),
                dict(recipe), Confidence(0.82, "Estructura tabular detectada sin IA."),
            ))
        for index, article in enumerate(list(analysis.get("articulos") or []), 1):
            entities.append(ExtractedEntity(
                f"ENT-ART-{index:03d}", "ARTICULO", str(article.get("nombre") or f"Artículo {index}"),
                {**dict(article), "tipo_propuesto": "ARTICULO_COMPRADO"},
                Confidence(0.78, "Nombre y columnas de catálogo detectados sin IA."),
            ))
        for index, supplier in enumerate(list(analysis.get("proveedores") or []), 1):
            entities.append(ExtractedEntity(
                f"ENT-PROV-{index:03d}", "PROVEEDOR", str(supplier.get("nombre") or f"Proveedor {index}"),
                dict(supplier), Confidence(0.8, "Listado de proveedores detectado sin IA."),
            ))
        for index, menu in enumerate(list(analysis.get("menus") or []), 1):
            entities.append(ExtractedEntity(
                f"ENT-MENU-{index:03d}", "MENU", str(menu.get("nombre") or f"Menú {index}"),
                dict(menu), Confidence(0.8, "Contenedor culinario separado de las recetas."),
            ))
        origin = {"importacion_id": import_id, "nombre": "Sesión multifuente", "tipo": "MULTIFUENTE"}
        proposals = self.proposal_builder.build(
            import_id=import_id, document_type=DocumentType.MIXTO,
            entities=entities, context={"recetas": recipes}, origin=origin,
        )
        summary = dict(analysis["resumen"])
        summary.update({
            "secciones": len(analysis.get("hojas") or []), "entidades": len(entities),
            "propuestas": len(proposals),
            "incidencias": summary.get("decisiones_usuario", summary.get("ambiguedades", 0)),
            "recetas_detectadas": len(recipes),
            "ingredientes_detectados": sum(len(r.get("ingredientes_estructurados") or []) for r in recipes),
            "ingredientes_relacionados": 0,
            "coincidencias_dudosas": len(analysis.get("dudas", {}).get("relaciones") or []),
            "ingredientes_sin_relacionar": sum(len(r.get("ingredientes_estructurados") or []) for r in recipes),
            "ingredientes_nuevos": sum(len(r.get("ingredientes_estructurados") or []) for r in recipes),
            "duplicados_detectados": len(analysis.get("duplicados") or []),
            "estado": "PENDIENTE_REVISION",
        })
        document = {
            "id": import_id, "nombre": "Sesión de datos del restaurante",
            "tipo_mime": "application/vnd.host-ai.import-session", "tamano": sum(x["tamano"] for x in analysis["archivos"]),
            "origen": "HOSTAI_IMPORT_PACKAGE" if analysis.get("package_metadata") is not None else "MULTIFUENTE", "clasificacion": {
                "tipo": "MIXTO", "confianza": Confidence(0.8, "Fuentes tabulares correlacionadas como conjunto.").to_dict(),
                "evidencias": ["Mapping determinista de hojas y columnas."], "advertencias": [],
            },
            "secciones": analysis["hojas"], "entidades": [item.to_dict() for item in entities],
            "advertencias": [], "contenido_almacenado": False,
        }
        session = {
            "documento": document, "resumen": summary,
            "propuestas": [item.to_dict() for item in proposals],
            "analisis_restaurante": analysis, "solo_previsualizacion": True,
            "confirmacion_disponible": True, "estado": "PENDIENTE_REVISION", "historial": [],
            "limitaciones": [
                "XLS debe convertirse a XLSX.",
                "No se evalúan macros, fórmulas, SQL ni contenido ejecutable.",
                "Las columnas de precio ambiguas requieren revisión humana.",
            ],
        }
        session["borrador"] = self.drafts.build(
            import_id=import_id, classification="MIXTO", confidence=0.8, recipes=recipes,
        )
        self._align_recipe_proposals_with_draft(session)
        ingredient_drafts = [
            ingredient
            for recipe in session["borrador"].get("recipes") or []
            for ingredient in recipe.get("ingredients") or []
        ]
        related_states = {"RELACIONADO", "COINCIDENCIA_EXACTA_PROPUESTA"}
        related_count = sum(
            ingredient.get("relation_status") in related_states and bool(ingredient.get("article_id"))
            for ingredient in ingredient_drafts
        )
        candidate_count = sum(
            ingredient.get("relation_status") == "REVISAR_COINCIDENCIA"
            for ingredient in ingredient_drafts
        )
        session["resumen"].update({
            "ingredientes_detectados": len(ingredient_drafts),
            "ingredientes_relacionados": related_count,
            "coincidencias_dudosas": candidate_count,
            "ingredientes_sin_relacionar": len(ingredient_drafts) - related_count - candidate_count,
            "ingredientes_nuevos": sum(
                ingredient.get("relation_status") == "SIN_RELACIONAR"
                for ingredient in ingredient_drafts
            ),
        })
        recipe_entities = [
            entity for entity in session["documento"]["entidades"] if entity.get("kind") == "RECETA"
        ]
        for entity, recipe_draft in zip(recipe_entities, session["borrador"].get("recipes") or []):
            projected_ingredients = []
            for ingredient in recipe_draft.get("ingredients") or []:
                status = str(ingredient.get("relation_status") or "SIN_RELACIONAR")
                projected_ingredients.append({
                    "nombre_original": ingredient.get("name_raw"),
                    "cantidad_texto": ingredient.get("quantity_raw"),
                    "unidad": ingredient.get("unit"),
                    "estado_relacion": (
                        "relacionado" if status in related_states and ingredient.get("article_id")
                        else "coincidencia_dudosa" if status == "REVISAR_COINCIDENCIA"
                        else "sin_relacionar"
                    ),
                    "articulo_id": ingredient.get("article_id"),
                })
            entity.setdefault("fields", {})["ingredientes_estructurados"] = projected_ingredients
        recipe_drafts = {
            self._norm(item.get("title")): item
            for item in session["borrador"].get("recipes") or []
        }
        for relation in analysis.get("relaciones") or []:
            parent = recipe_drafts.get(self._norm(relation.get("elaboracion")))
            component = recipe_drafts.get(self._norm(relation.get("depende_de")))
            if parent and component:
                component["entity_type"] = "SUBELABORACION"
                component["parent_recipe_id"] = parent["id"]
                if component.get("proposed_action") == "CREAR_RECETA":
                    component["proposed_action"] = "CREAR_SUBELABORACION"
        session["borrador"]["catalogo"] = self._build_catalog_draft(
            list(analysis.get("articulos") or []),
            list(analysis.get("proveedores") or []),
            recipes,
        )
        session["borrador"]["article_decisions"] = [
            {"article_draft_id": item["id"], "decision": "PENDIENTE", "article_id": None}
            for item in session["borrador"]["catalogo"]["articulos"]
            if item.get("accion") == "REQUIERE_REVISION"
        ]
        session["borrador"]["menus"] = deepcopy(list(analysis.get("menus") or []))
        session["borrador"]["menu_decisions"] = []
        session["preview_global"] = self._catalog_preview(
            session["borrador"]["catalogo"], session["borrador"].get("recipes") or [],
            session["borrador"].get("menus") or [], session["borrador"].get("menu_decisions") or [],
        )
        session["resolucion_identidad"] = self._identity_resolution(
            recipes, session["borrador"], session["preview_global"]
        )
        session["borrador"]["variant_decisions"] = [
            {"group_id": item["id"], "decision": "PENDIENTE"}
            for item in session["resolucion_identidad"].get("variantes", {}).get("items", [])
            if item.get("requiere_decision")
        ]
        session["borrador"] = self.drafts.validate(session["borrador"])
        self._project_current_draft_decisions(session)
        session["confirmacion_disponible"] = bool(
            session["borrador"].get("validation", {}).get("valid")
            and not session["preview_global"]["contadores"]["pendientes"]
        )
        self._sessions[import_id] = session
        self.repository.save_all(self._sessions)
        return {"ok": True, "importacion": session, "datos_operativos_modificados": False}

    @staticmethod
    def _align_recipe_proposals_with_draft(session: dict[str, Any]) -> None:
        """La propuesta visible refleja el matching canónico ya calculado en el draft."""
        by_name = {
            normalize_text(item.get("title")): item
            for item in session.get("borrador", {}).get("recipes") or []
        }
        labels = {
            "REUTILIZAR_EXISTENTE": ("REUTILIZAR_RECETA", "Reutilizar receta existente"),
            "REQUIERE_REVISION": ("REVISAR_COINCIDENCIA", "Pendiente de decisión de identidad"),
            "IGNORAR": ("IGNORAR", "Ignorar en esta importación"),
            "CREAR_SUBELABORACION": ("CREAR_RECETA", "Crear subelaboración nueva"),
            "CREAR_RECETA": ("CREAR_RECETA", "Crear receta nueva"),
        }
        for proposal in session.get("propuestas") or []:
            entity = ((proposal.get("datos_propuestos") or {}).get("entidad") or {})
            if entity.get("kind") != "RECETA":
                continue
            draft = by_name.get(normalize_text(entity.get("name")))
            if not draft:
                continue
            action = str(draft.get("proposed_action") or "REQUIERE_REVISION")
            proposal_type, label = labels.get(action, ("REVISAR_COINCIDENCIA", "Pendiente"))
            proposal["tipo"] = proposal_type
            proposal["titulo"] = f"{label}: {draft.get('title')}"
            proposal["explicacion"] = f"Acción canónica prevista: {action}."

    @staticmethod
    def _identity_resolution(
        source_recipes: list[dict[str, Any]], draft: dict[str, Any], preview: dict[str, Any]
    ) -> dict[str, Any]:
        recipe_groups: dict[str, list[dict[str, Any]]] = {
            "ya_canonicas": [], "ya_conocidas_legacy": [], "nuevas_reales": [],
            "posibles_variantes": [], "requieren_revision": [],
        }
        safe_legacy_by_index: dict[int, list[dict[str, Any]]] = {}
        for index, item in enumerate(draft.get("recipes") or []):
            safe_legacy_by_index[index] = [candidate for candidate in item.get("duplicate_candidates") or [] if (
                candidate.get("estado_identidad") == LEGACY_WITHOUT_CANONICAL
                and float(candidate.get("coincidencia_ingredientes") or 0) >= 0.8
            )]
        colliding_indexes: set[int] = set()
        legacy_names = [
            (index, str(candidate.get("nombre") or ""))
            for index, candidates in safe_legacy_by_index.items() for candidate in candidates
        ]
        for position, (left_index, left_name) in enumerate(legacy_names):
            for right_index, right_name in legacy_names[position + 1:]:
                if left_index != right_index and CanonicalRecipeMatcher._names_linguistically_related(
                    normalize_text(left_name), normalize_text(right_name)
                ):
                    colliding_indexes.update((left_index, right_index))
        for index, item in enumerate(draft.get("recipes") or []):
            source = source_recipes[index] if index < len(source_recipes) else {}
            legacy = safe_legacy_by_index[index] if index not in colliding_indexes else []
            projected = {"id": item.get("id"), "nombre": item.get("title")}
            if item.get("proposed_action") == "REUTILIZAR_EXISTENTE":
                recipe_groups["ya_canonicas"].append(projected)
            elif legacy and not source.get("posible_variante"):
                projected["legacy_source_ids"] = sorted({
                    str(candidate.get("id") or candidate.get("codigo") or "")
                    for candidate in legacy if candidate.get("id") or candidate.get("codigo")
                })
                projected["datos_pendientes"] = not bool(item.get("procedure"))
                recipe_groups["ya_conocidas_legacy"].append(projected)
            elif source.get("posible_variante"):
                recipe_groups["posibles_variantes"].append(projected)
            elif item.get("proposed_action") == "REQUIERE_REVISION":
                recipe_groups["requieren_revision"].append(projected)
            else:
                recipe_groups["nuevas_reales"].append(projected)
        article_counts = preview.get("contadores") or {}
        total_articles = sum(
            int(article_counts.get(key) or 0)
            for key in ("articulos_reutilizados", "articulos_nuevos", "articulos_requieren_revision")
        )
        if not total_articles:
            total_articles = sum(len(items) for items in (preview.get("articulos") or {}).values())
        return {
            "recetas": {
                "total": len(draft.get("recipes") or []),
                **{key: len(value) for key, value in recipe_groups.items()},
                "grupos": recipe_groups,
            },
            "articulos": {
                "total": total_articles,
                "ya_existentes": int(article_counts.get("articulos_reutilizados") or 0),
                "nuevos_reales": int(article_counts.get("articulos_nuevos") or 0),
                "requieren_revision": int(article_counts.get("articulos_requieren_revision") or 0),
            },
            "variantes": ImportDocumentService._variant_resolution(source_recipes),
        }

    @staticmethod
    def _variant_resolution(source_recipes: list[dict[str, Any]]) -> dict[str, Any]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for recipe in source_recipes:
            if recipe.get("posible_variante"):
                grouped.setdefault(normalize_text(recipe.get("nombre")), []).append(recipe)
        groups: list[dict[str, Any]] = []
        exact_duplicates = 0
        for key, occurrences in grouped.items():
            versions_by_signature: dict[tuple[Any, ...], dict[str, Any]] = {}
            for occurrence in occurrences:
                ingredients = list(occurrence.get("ingredientes_estructurados") or [])
                normalized_lines = sorted((
                    normalize_text(line.get("article_id") or line.get("articulo_id") or line.get("nombre_original")),
                    normalize_text(line.get("cantidad_texto") or line.get("cantidad")),
                    normalize_text(line.get("unidad")),
                ) for line in ingredients)
                signature = (
                    tuple(normalized_lines),
                    normalize_text(occurrence.get("rendimiento") or occurrence.get("numero_raciones")),
                    normalize_text(occurrence.get("tipo")),
                )
                version = versions_by_signature.setdefault(signature, {
                    "id": f"{occurrence.get('id_origen') or 'VAR'}-VERSION",
                    "nombre": occurrence.get("nombre"),
                    "ingredientes": ingredients,
                    "rendimiento": occurrence.get("rendimiento") or occurrence.get("numero_raciones"),
                    "unidad_rendimiento": occurrence.get("unidad_rendimiento"),
                    "origenes": [], "apariciones": 0,
                })
                version["apariciones"] += 1
                for block in occurrence.get("bloques_origen") or []:
                    if block not in version["origenes"]:
                        version["origenes"].append(block)
            versions = list(versions_by_signature.values())
            exact_duplicates += len(occurrences) - len(versions)
            tokens = key.split()
            normalized_name = str(occurrences[0].get("nombre") or "").strip().rstrip(".")
            entity_kind = (
                "MENU_O_CONTENEDOR" if key.startswith("menu ")
                else "ETIQUETA_CONTEXTO_POR_REVISAR" if len(tokens) == 1 and len(versions) > 1
                else "RECETA_O_ELABORACION"
            )
            groups.append({
                "id": f"VARIANT-GROUP-{len(groups)+1:03d}", "nombre": normalized_name,
                "tipo_entidad_propuesto": entity_kind,
                "apariciones": len(occurrences), "versiones_estructurales": len(versions),
                "duplicados_exactos": len(occurrences) - len(versions),
                "requiere_decision": len(versions) > 1,
                "versiones": versions,
                "diferencias": ImportDocumentService._variant_differences(versions),
            })
        return {
            "apariciones": sum(len(items) for items in grouped.values()),
            "grupos": len(groups), "duplicados_exactos_colapsados": exact_duplicates,
            "grupos_requieren_decision": sum(item["requiere_decision"] for item in groups),
            "items": groups,
        }

    @staticmethod
    def _variant_differences(versions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(versions) < 2:
            return []
        baseline = versions[0]
        base_lines = {
            normalize_text(item.get("article_id") or item.get("articulo_id") or item.get("nombre_original")): item
            for item in baseline.get("ingredientes") or []
        }
        differences: list[dict[str, Any]] = []
        for index, version in enumerate(versions[1:], 2):
            current_lines = {
                normalize_text(item.get("article_id") or item.get("articulo_id") or item.get("nombre_original")): item
                for item in version.get("ingredientes") or []
            }
            for name in sorted(current_lines.keys() - base_lines.keys()):
                differences.append({"version": index, "tipo": "INGREDIENTE_ANADIDO", "nombre": current_lines[name].get("nombre_original")})
            for name in sorted(base_lines.keys() - current_lines.keys()):
                differences.append({"version": index, "tipo": "INGREDIENTE_RETIRADO", "nombre": base_lines[name].get("nombre_original")})
            for name in sorted(base_lines.keys() & current_lines.keys()):
                left, right = base_lines[name], current_lines[name]
                left_value = (left.get("cantidad_texto") or left.get("cantidad"), left.get("unidad"))
                right_value = (right.get("cantidad_texto") or right.get("cantidad"), right.get("unidad"))
                if left_value != right_value:
                    differences.append({"version": index, "tipo": "CANTIDAD_CAMBIA", "nombre": right.get("nombre_original"), "antes": left_value, "despues": right_value})
            if baseline.get("rendimiento") != version.get("rendimiento"):
                differences.append({"version": index, "tipo": "RENDIMIENTO_CAMBIA", "antes": baseline.get("rendimiento"), "despues": version.get("rendimiento")})
        return differences

    def preview_legacy_canonicalization(
        self, import_id: str, payload: dict[str, Any], context: AuthorizedExecutionContext
    ) -> dict[str, Any]:
        session = self._sessions.get(str(import_id or ""))
        if session is None:
            return self._error("import_not_found", "Importación no encontrada.", 404)
        known = session.get("resolucion_identidad", {}).get("recetas", {}).get("grupos", {}).get("ya_conocidas_legacy", [])
        allowed = {source_id for item in known for source_id in item.get("legacy_source_ids") or []}
        requested = set(payload.get("legacy_ids") or allowed)
        if not requested or not requested <= allowed:
            return self._error("invalid_legacy_selection", "La selección no pertenece al análisis actual.", 400)
        try:
            result = self.legacy_canonicalization.preview(
                legacy_ids=sorted(requested), context=context
            )
        except LegacyCanonicalizationError as exc:
            return self._error(exc.code, str(exc), 409)
        return {**result, "importacion_id": import_id}

    def confirm_legacy_canonicalization(
        self, import_id: str, payload: dict[str, Any], context: AuthorizedExecutionContext
    ) -> dict[str, Any]:
        if import_id not in self._sessions:
            return self._error("import_not_found", "Importación no encontrada.", 404)
        try:
            result = self.legacy_canonicalization.confirm(
                preview_token=str(payload.get("preview_token") or ""), context=context
            )
        except LegacyCanonicalizationError as exc:
            return self._error(exc.code, str(exc), 409)
        return {**result, "importacion_id": import_id}

    def _build_catalog_draft(
        self, articles: list[dict[str, Any]], suppliers: list[dict[str, Any]],
        recipes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        repository = RepositorioProductosMaestro601(self.base_dir)
        existing_suppliers = repository.listar_proveedores_canonicos()
        supplier_by_name = {self._supplier_norm(item.get("nombre")): item for item in existing_suppliers}
        recipe_names = {self._norm(item.get("nombre")) for item in recipes}
        supplier_drafts = []
        for item in suppliers:
            name = str(item.get("nombre") or "").strip()
            existing = supplier_by_name.get(self._supplier_norm(name))
            composite_name = existing is None and bool(
                re.search(r"[/|]|(?<=\w)\.(?=\w)", name)
            )
            supplier_drafts.append({
                "id": f"PROV-DRAFT-{len(supplier_drafts)+1:03d}", "nombre": name,
                "accion": "REUTILIZAR" if existing else "REQUIERE_REVISION" if composite_name else "CREAR",
                "proveedor_id": str((existing or {}).get("codigo") or "") or None,
                "estado": "PENDIENTE" if composite_name else "LISTO",
                "tipo": "PROVEEDOR_REAL",
                "motivo": "Nombre compuesto: requiere confirmar la identidad del proveedor." if composite_name else "",
                "origen": item.get("origen"),
            })
        finder = ArticleCandidateFinder(self.base_dir)
        article_drafts = []
        for item in articles:
            name = str(item.get("nombre") or "").strip()
            match = finder.find(
                name,
                str(item.get("unidad_base") or item.get("unidad") or "") or None,
                item,
            )
            same_as_recipe = self._norm(name) in recipe_names
            exact = match.get("status") == "COINCIDENCIA_EXACTA_PROPUESTA" and match.get("article_id")
            semantic_type = str(item.get("tipo_semantico") or "").strip().upper()
            package_semantics = item.get("evidencia_tipo") is not None
            purchased_type = (not package_semantics) or (
                bool("ARTICULO_COMPRADO" in semantic_type or "MATERIA_PRIMA" in semantic_type)
                and not any(token in semantic_type for token in (
                    "ELABORACION", "SUBELABORACION", "PRODUCTO_VENDIBLE", "MENU", "CONTEXT", "PLATO",
                ))
            )
            type_requires_review = package_semantics and not purchased_type
            ambiguous = (
                same_as_recipe or match.get("status") == "REVISAR_COINCIDENCIA"
                or (not exact and type_requires_review)
            )
            action = "REQUIERE_REVISION" if ambiguous else "REUTILIZAR" if exact else "CREAR"
            supplier_name = str(item.get("proveedor") or "").strip()
            article_drafts.append({
                "id": f"ART-DRAFT-{len(article_drafts)+1:03d}", "nombre": name,
                "tipo_entidad": "ARTICULO_COMPRADO" if purchased_type else semantic_type or "AMBIGUO",
                "tipo_semantico": semantic_type or None, "accion": action,
                "article_id": str(match.get("article_id") or "") or None,
                "candidatos": list(match.get("candidates") or []),
                "proveedor": supplier_name or None,
                "formato": item.get("formato"),
                "precio_compra_importado": item.get("precio_compra"),
                "precio_referencia_importado": item.get("precio_referencia_importado"),
                "precio_aplicable": False,
                "estado": "PENDIENTE" if ambiguous else "LISTO",
                "motivo": (
                    "Mismo nombre que una receta; requiere revisión." if same_as_recipe
                    else "La clasificación semántica no demuestra que sea un artículo comprado."
                    if type_requires_review and not exact else ""
                ),
                "evidencia_tipo": item.get("evidencia_tipo"),
                "evidencia_identidad": match.get("evidencia_identidad"),
                "origen": item.get("origen"),
            })
        relations = []
        known_suppliers = {self._supplier_norm(item["nombre"]) for item in supplier_drafts}
        for article in article_drafts:
            supplier = str(article.get("proveedor") or "")
            if not supplier:
                continue
            if self._supplier_norm(supplier) not in known_suppliers:
                continue
            ready = article["estado"] == "LISTO"
            relations.append({
                "articulo_draft_id": article["id"], "articulo": article["nombre"],
                "proveedor": supplier, "accion": "CREAR" if ready else "REQUIERE_REVISION",
                "estado": "LISTO" if ready else "PENDIENTE",
                "evidencia": article.get("origen"),
            })
        return {"proveedores": supplier_drafts, "articulos": article_drafts, "relaciones": relations}

    def _catalog_preview(
        self, catalog: dict[str, Any], recipes: list[dict[str, Any]], menus: list[dict[str, Any]] | None = None,
        menu_decisions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        def grouped(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
            return {
                key.lower(): [item for item in items if item.get("accion") == key]
                for key in ("CREAR", "REUTILIZAR", "REQUIERE_REVISION", "IGNORAR", "ES_ELABORACION")
            }
        suppliers = list(catalog.get("proveedores") or [])
        articles = list(catalog.get("articulos") or [])
        relations = list(catalog.get("relaciones") or [])
        pending_suppliers = sum(item.get("estado") == "PENDIENTE" for item in suppliers)
        pending_articles = sum(item.get("estado") == "PENDIENTE" for item in articles)
        pending_relations = sum(item.get("estado") == "PENDIENTE" for item in relations)
        recipe_groups = {
            "crear_nueva": [], "reutilizar_existente": [], "requiere_revision": [],
        }
        for recipe in recipes:
            action = str(recipe.get("proposed_action") or "")
            item = {
                "nombre": recipe.get("title") or recipe.get("nombre"),
                "accion": action,
                "coincidencia": (recipe.get("duplicate_candidates") or [None])[0],
            }
            if action == "REUTILIZAR_EXISTENTE":
                recipe_groups["reutilizar_existente"].append(item)
            elif action == "REQUIERE_REVISION":
                recipe_groups["requiere_revision"].append(item)
            else:
                recipe_groups["crear_nueva"].append(item)
        pending_recipes = len(recipe_groups["requiere_revision"])
        ingredients = [ingredient for recipe in recipes for ingredient in recipe.get("ingredients") or []]
        related_ingredients = sum(bool(item.get("article_id")) for item in ingredients)
        pending = pending_suppliers + pending_articles + pending_relations + pending_recipes
        menu_projection = project_menu_imports(
            self.base_dir, list(menus or []), recipes, menu_decisions, articles
        )
        pending_menus = len(menu_projection["pendientes"])
        menu_lines = [line for item in sum(menu_projection.values(), []) for line in item.get("lineas") or []]
        pending += pending_menus
        return {
            "proveedores": grouped(suppliers), "articulos": grouped(articles),
            "elaboraciones": recipe_groups,
            "relaciones": grouped(relations), "ignorados": [], "errores": [],
            "menus": menu_projection,
            "contadores": {
                "proveedores_nuevos": sum(x["accion"] == "CREAR" for x in suppliers),
                "proveedores_reutilizados": sum(x["accion"] == "REUTILIZAR" for x in suppliers),
                "articulos_nuevos": sum(x["accion"] == "CREAR" for x in articles),
                "articulos_reutilizados": sum(x["accion"] == "REUTILIZAR" for x in articles),
                "articulos_requieren_revision": sum(x["accion"] == "REQUIERE_REVISION" for x in articles),
                "articulos_ignorados": sum(x["accion"] == "IGNORAR" for x in articles),
                "articulos_reclasificados_elaboracion": sum(x["accion"] == "ES_ELABORACION" for x in articles),
                "recetas_elaboraciones": len(recipes),
                "recetas_nuevas": len(recipe_groups["crear_nueva"]),
                "recetas_reutilizadas": len(recipe_groups["reutilizar_existente"]),
                "recetas_requieren_revision": pending_recipes,
                "relaciones": len(relations),
                "relaciones_a_escribir": sum(x.get("accion") == "CREAR" for x in relations),
                "relaciones_reutilizadas": sum(x.get("accion") == "REUTILIZAR" for x in relations),
                "relaciones_pendientes": pending_relations,
                "ingredientes_detectados": len(ingredients),
                "ingredientes_relacionados": related_ingredients,
                "ingredientes_sin_relacionar": len(ingredients) - related_ingredients,
                "menus_recibidos": len(menus or []),
                "menus_crear": len(menu_projection["crear"]),
                "menus_reutilizar": len(menu_projection["reutilizar"]),
                "menus_actualizar": len(menu_projection["actualizar"]),
                "menus_pendientes": pending_menus,
                "menus_excluidos": len(menu_projection.get("excluidos") or []),
                "menus_no_soportados": len(menu_projection["no_soportados"]),
                "menu_lineas_resueltas": sum(line.get("estado") == "RESUELTA" for line in menu_lines),
                "menu_lineas_pendientes": sum(line.get("estado") == "PENDIENTE" for line in menu_lines),
                "menu_lineas_contexto": sum(line.get("estado") == "CONTEXTO" for line in menu_lines),
                "pendientes": pending,
                "pendientes_desglose": {
                    "identidad_receta": pending_recipes, "articulo": pending_articles,
                    "relacion": pending_relations, "proveedor": pending_suppliers,
                    "documentacion": 0, "menu": pending_menus, "otro": 0,
                },
            },
            "solo_previsualizacion": True,
        }

    @staticmethod
    def _norm(value: Any) -> str:
        return normalize_text(value)

    @staticmethod
    def _supplier_norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or "").casefold())
        folded = " ".join("".join(
            char for char in text if not unicodedata.combining(char)
        ).split())
        return folded.strip().rstrip(".,;:").rstrip()

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

    def get_draft(self, import_id: str) -> dict[str, Any]:
        session = self._sessions.get(str(import_id or ""))
        if session is None:
            return self._error("import_not_found", "Importación no encontrada.", 404)
        validated = self.drafts.validate(session["borrador"])
        return {
            "ok": True,
            "importacion_id": import_id,
            "borrador": validated,
            "datos_reales_modificados": False,
        }

    def update_draft(self, import_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._sessions.get(str(import_id or ""))
        if session is None:
            return self._error("import_not_found", "Importación no encontrada.", 404)
        try:
            updated = self.drafts.update(session["borrador"], dict(payload or {}))
        except DraftConflictError as exc:
            return {
                "ok": False,
                "error": {
                    "code": "draft_version_conflict",
                    "message": "El borrador fue actualizado en otra revisión.",
                    "status": 409,
                    "current_version": exc.current_version,
                },
            }
        except DraftValidationError as exc:
            return self._error("invalid_draft", str(exc), 400)
        session["borrador"] = updated
        self._project_current_draft_decisions(session)
        self.repository.save_all(self._sessions)
        return {
            "ok": True,
            "importacion_id": import_id,
            "borrador": updated,
            "preview_global": deepcopy(session.get("preview_global") or {}),
            "resolucion_identidad": deepcopy(session.get("resolucion_identidad") or {}),
            "solo_previsualizacion": True,
            "confirmacion_disponible": bool(
                updated.get("validation", {}).get("valid")
            ),
            "datos_reales_modificados": False,
        }

    def _project_current_draft_decisions(self, session: dict[str, Any]) -> None:
        """Proyecta el borrador vigente al DTO de sesiÃ³n sin escribir dominio."""
        decisions = {
            str(item.get("group_id") or ""): str(item.get("decision") or "PENDIENTE")
            for item in session.get("borrador", {}).get("variant_decisions") or []
        }
        variants = session.get("resolucion_identidad", {}).get("variantes") or {}
        for item in variants.get("items") or []:
            decision = decisions.get(str(item.get("id") or ""), "PENDIENTE")
            item["decision"] = decision
            item["requiere_decision"] = bool(item.get("versiones_estructurales", 0) > 1 and decision == "PENDIENTE")
        variants["grupos_requieren_decision"] = sum(
            bool(item.get("requiere_decision")) for item in variants.get("items") or []
        )
        review_ids = {
            str(item.get("id") or "")
            for item in session.get("resolucion_identidad", {}).get("recetas", {}).get("grupos", {}).get("requieren_revision", [])
        }
        recipes = session.get("borrador", {}).get("recipes") or []
        unresolved = sum(
            str(item.get("id") or "") in review_ids
            and item.get("identity_decision") in {None, "", "PENDIENTE"}
            for item in recipes
        )
        session.get("resolucion_identidad", {}).get("recetas", {})["requieren_revision"] = unresolved
        draft = session.get("borrador", {})
        if "menus" not in draft:
            draft["menus"] = deepcopy(list(session.get("analisis_restaurante", {}).get("menus") or []))
        catalog = draft.get("catalogo") or {}
        articles = {str(item.get("id") or ""): item for item in catalog.get("articulos") or []}
        for stored in session.get("borrador", {}).get("article_decisions") or []:
            item = articles.get(str(stored.get("article_draft_id") or ""))
            if not item:
                continue
            decision = str(stored.get("decision") or "PENDIENTE")
            if decision == "REUTILIZAR_ARTICULO":
                item.update(accion="REUTILIZAR", estado="LISTO", article_id=stored.get("article_id"))
            elif decision == "ES_ELABORACION":
                item.update(accion="ES_ELABORACION", estado="LISTO")
            elif decision in {"NO_ARTICULO_COMPRA", "PRODUCTO_VENDIBLE", "IGNORAR"}:
                item.update(accion="IGNORAR", estado="LISTO")
            else:
                item.update(accion="REQUIERE_REVISION", estado="PENDIENTE")
        decision_by_id = {
            str(item.get("article_draft_id") or ""): str(item.get("decision") or "PENDIENTE")
            for item in session.get("borrador", {}).get("article_decisions") or []
        }
        for relation in catalog.get("relaciones") or []:
            decision = decision_by_id.get(str(relation.get("articulo_draft_id") or ""))
            if decision in {"NO_ARTICULO_COMPRA", "ES_ELABORACION", "PRODUCTO_VENDIBLE", "IGNORAR"}:
                relation.update(accion="IGNORAR", estado="LISTO")
            elif decision == "REUTILIZAR_ARTICULO":
                relation.update(accion="CREAR", estado="LISTO")
            elif decision == "PENDIENTE":
                relation.update(accion="REQUIERE_REVISION", estado="PENDIENTE")
        if catalog:
            session["preview_global"] = self._catalog_preview(
                catalog, draft.get("recipes") or [], draft.get("menus") or [], draft.get("menu_decisions") or [],
            )
            session["preview_global"]["draft_version"] = int(draft.get("draft_version") or draft.get("version") or 0)
            session["preview_global"]["draft_fingerprint"] = hashlib.sha256(
                json.dumps(draft, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
            ).hexdigest()
            article_counts = session["preview_global"]["contadores"]
            identity_articles = session.get("resolucion_identidad", {}).get("articulos") or {}
            identity_articles["ya_existentes"] = int(article_counts.get("articulos_reutilizados") or 0)
            identity_articles["nuevos_reales"] = int(article_counts.get("articulos_nuevos") or 0)
            identity_articles["requieren_revision"] = int(article_counts.get("articulos_requieren_revision") or 0)

    def confirm(self, import_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if import_id not in self._sessions:
            return self._error("import_not_found", "Importación no encontrada.", 404)
        return self.confirmations.confirm(self._sessions, import_id, dict(payload or {}))

    def get_status(self, import_id: str) -> dict[str, Any]:
        session = self._sessions.get(import_id)
        if session is None:
            return self._error("import_not_found", "Importación no encontrada.", 404)
        return {
            "ok": True, "importacion_id": import_id,
            "estado": session.get("estado", "PENDIENTE_REVISION"),
            "version": session.get("borrador", {}).get("version", 0),
            "resultado": session.get("resultado_confirmacion"),
        }

    def get_history(self, import_id: str) -> dict[str, Any]:
        session = self._sessions.get(import_id)
        if session is None:
            return self._error("import_not_found", "Importación no encontrada.", 404)
        history = list(session.get("historial") or [])
        return {"ok": True, "importacion_id": import_id, "historial": history, "total": len(history)}

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
