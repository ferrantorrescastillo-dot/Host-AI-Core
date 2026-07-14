from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .document_classifier import default_category_rank
from .document_discovery import DocumentCandidate


DOMAIN_ALIASES: dict[str, str] = {
    "produccion": "produccion",
    "stock": "stock",
    "compras": "compras",
    "recepcion": "recepcion",
    "eventos": "eventos",
    "escandallos": "escandallos",
    "costes": "costes",
    "arquitectura": "arquitectura",
    "ia": "ia",
    "general": "general",
}


@dataclass(frozen=True)
class ManifestEntry:
    relative_path: str
    category: str
    priority: int
    size: int
    inclusion_reason: str
    status: str
    warnings: tuple[str, ...]
    domain_tags: tuple[str, ...]


def normalize_domain(domain: str | None) -> str:
    raw = (domain or "general").strip().lower()
    return DOMAIN_ALIASES.get(raw, "general")


def _required_priority(path: str) -> int | None:
    p = path.lower()
    if p == "agents.md":
        return 2
    if p == "master_plan.md":
        return 3
    if p == "codex-01.md":
        return 4
    if p == "codex-02.md":
        return 5
    return None


def _category_boost(path: str, category: str) -> int:
    p = path.lower()
    if p.startswith("roc/"):
        return 60
    if category == "gobierno":
        return 40
    if category == "arquitectura":
        return 30
    if category == "ejecucion de agentes":
        return 20
    if category == "dominio funcional":
        return 10
    if category == "referencia":
        return 5
    return 0


def build_manifest(
    documents: list[DocumentCandidate],
    map_priority: list[str],
    map_warnings: list[str],
    domain: str | None = None,
) -> tuple[list[ManifestEntry], list[str]]:
    """Construye manifiesto determinista y advertencias de cobertura."""
    normalized_domain = normalize_domain(domain)

    entries: list[ManifestEntry] = []
    warnings: list[str] = list(map_warnings)
    map_index = {path.lower(): idx for idx, path in enumerate(map_priority, start=1)}

    found_required = {
        "agents.md": False,
        "master_plan.md": False,
        "codex-01.md": False,
        "codex-02.md": False,
    }

    for doc in documents:
        path_l = doc.relative_path.lower()

        required_rank = _required_priority(doc.relative_path)
        if required_rank is not None:
            found_required[Path(doc.relative_path).name.lower()] = True

        map_rank = map_index.get(path_l)
        if map_rank is not None:
            priority = map_rank
            include_reason = "Priorizado por DOCUMENTACION_MAP.md"
        elif required_rank is not None:
            priority = required_rank
            include_reason = "Documento obligatorio base"
        else:
            base = default_category_rank(doc.classification.category)
            boost = _category_boost(doc.relative_path, doc.classification.category)
            domain_bonus = 0
            if normalized_domain != "general":
                domain_bonus = 0 if normalized_domain in doc.classification.domain_tags else 50
            priority = 100 + base + domain_bonus - boost
            include_reason = doc.classification.reason

        status = "selected"
        entry_warnings: list[str] = []
        if doc.size == 0:
            status = "warning"
            entry_warnings.append("Documento vacío")

        if normalized_domain != "general" and normalized_domain not in doc.classification.domain_tags:
            if priority < 20:
                entry_warnings.append(
                    "Incluido por autoridad documental aunque no coincida con dominio solicitado"
                )

        entries.append(
            ManifestEntry(
                relative_path=doc.relative_path,
                category=doc.classification.category,
                priority=priority,
                size=doc.size,
                inclusion_reason=include_reason,
                status=status,
                warnings=tuple(entry_warnings),
                domain_tags=doc.classification.domain_tags,
            )
        )

    for required, present in found_required.items():
        if not present:
            warnings.append(f"Documento obligatorio ausente: {required.upper()}")

    entries.sort(key=lambda e: (e.priority, e.relative_path.lower()))
    return entries, warnings


def manifest_to_json(entries: list[ManifestEntry], warnings: list[str]) -> str:
    payload = {
        "manifest_version": "ai_core_v1",
        "entries": [asdict(e) for e in entries],
        "warnings": warnings,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
