"""AI_CORE v1: contexto automático y seguro para agentes.

Subsistema de solo lectura para descubrir documentación, clasificarla
y generar paquetes de contexto reproducibles.
"""

from .context_builder import build_context_markdown
from .context_manifest import build_manifest, manifest_to_json
from .document_discovery import discover_documents, find_project_root

__all__ = [
    "build_context_markdown",
    "build_manifest",
    "manifest_to_json",
    "discover_documents",
    "find_project_root",
]
