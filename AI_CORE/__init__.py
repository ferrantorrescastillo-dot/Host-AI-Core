"""AI_CORE v1: contexto automático y seguro para agentes.

Subsistema de solo lectura para descubrir documentación, clasificarla
y generar paquetes de contexto reproducibles.
"""

from .context_builder import build_context_markdown
from .context_manifest import build_manifest, manifest_to_json
from .document_discovery import discover_documents, find_project_root
from .repository_inventory import build_repository_inventory, write_inventory_json
from .repository_scanner import ScannerConfig, scan_repository
from .task_pack_engine import build_task_context_package, infer_domain

__all__ = [
    "build_context_markdown",
    "build_manifest",
    "manifest_to_json",
    "discover_documents",
    "find_project_root",
    "ScannerConfig",
    "scan_repository",
    "build_repository_inventory",
    "write_inventory_json",
    "build_task_context_package",
    "infer_domain",
]
