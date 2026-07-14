from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .document_classifier import Classification, classify_document


ALLOWED_EXTENSIONS = {".md", ".txt"}
ROOT_MARKERS = ("AGENTS.md", "MASTER_PLAN.md")
PRIMARY_SCAN_DIRS = (
    "DEVKIT",
    "DOCS",
    "ROC",
    "LEEME",
    "CERTIFICACION",
    "CHANGELOG",
    "Auditoria",
    "Documentos",
)
EXCLUDED_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    "DATOS",
    "LOGS",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
}
SENSITIVE_NAME_PATTERNS = (
    ".env",
    "secret",
    "credential",
    "token",
    "key",
    "password",
)


@dataclass(frozen=True)
class DocumentCandidate:
    relative_path: str
    absolute_path: Path
    size: int
    classification: Classification


def _to_relative_posix(root: Path, file_path: Path) -> str:
    return file_path.relative_to(root).as_posix()


def find_project_root(start: Path | None = None) -> Path:
    """Detecta la raíz del proyecto sin rutas absolutas preconfiguradas."""
    cursor = (start or Path.cwd()).resolve()
    if cursor.is_file():
        cursor = cursor.parent

    for parent in (cursor, *cursor.parents):
        has_markers = all((parent / marker).is_file() for marker in ROOT_MARKERS)
        if has_markers and (parent / "DEVKIT").is_dir():
            return parent
    raise FileNotFoundError(
        "No se pudo detectar la raíz del proyecto. "
        "Se esperaban AGENTS.md, MASTER_PLAN.md y carpeta DEVKIT."
    )


def _is_allowed_document(path: Path) -> bool:
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False
    name_l = path.name.lower()
    if any(fragment in name_l for fragment in SENSITIVE_NAME_PATTERNS):
        return False
    return True


def _iter_document_files(scan_root: Path) -> list[Path]:
    files: list[Path] = []
    for entry in scan_root.rglob("*"):
        if entry.is_dir():
            if entry.name in EXCLUDED_DIR_NAMES:
                continue
            # Evita recursión en carpetas históricas muy grandes.
            if entry.name.upper().startswith("HOST_AI_"):
                continue
            continue

        if not _is_allowed_document(entry):
            continue
        files.append(entry)
    return files


def _parse_documentacion_map(map_file: Path, root: Path) -> tuple[list[str], list[str]]:
    """Extrae rutas válidas de DOCUMENTACION_MAP.md en orden de aparición."""
    warnings: list[str] = []
    if not map_file.is_file():
        return [], warnings

    content = map_file.read_text(encoding="utf-8", errors="replace")
    candidates: list[str] = []

    md_links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", content)
    candidates.extend(md_links)

    for line in content.splitlines():
        token_match = re.search(r"([A-Za-z0-9_./\\-]+\.(?:md|txt))", line)
        if token_match:
            candidates.append(token_match.group(1))

    ordered: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        candidate = raw.strip().strip("'\"")
        if candidate.startswith("http://") or candidate.startswith("https://"):
            continue
        is_explicit_abs = bool(re.match(r"^[A-Za-z]:[\\/]", candidate)) or candidate.startswith(("/", "\\"))
        rel = Path(candidate)
        if rel.is_absolute() or is_explicit_abs:
            warnings.append(f"Ruta absoluta ignorada en DOCUMENTACION_MAP: {candidate}")
            continue
        normalized = rel.as_posix()
        target = (root / rel).resolve()
        if root not in [target, *target.parents]:
            warnings.append(f"Ruta fuera de la raíz ignorada en DOCUMENTACION_MAP: {candidate}")
            continue
        if not target.is_file():
            warnings.append(f"Ruta no encontrada en DOCUMENTACION_MAP: {normalized}")
            continue
        if target.suffix.lower() not in ALLOWED_EXTENSIONS:
            warnings.append(f"Archivo no textual ignorado en DOCUMENTACION_MAP: {normalized}")
            continue
        normalized = target.relative_to(root).as_posix()
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered, warnings


def discover_documents(root: Path) -> tuple[list[DocumentCandidate], list[str], list[str]]:
    """Descubre documentos oficiales y devuelve también mapa y advertencias."""
    warnings: list[str] = []
    found: dict[str, DocumentCandidate] = {}

    map_file = root / "DOCUMENTACION_MAP.md"
    map_priority, map_warnings = _parse_documentacion_map(map_file, root)
    warnings.extend(map_warnings)

    # Documentos de primer nivel.
    for marker in ("AGENTS.md", "MASTER_PLAN.md", "CODEX-01.md", "CODEX-02.md"):
        file_path = root / marker
        if file_path.is_file() and _is_allowed_document(file_path):
            rel = file_path.relative_to(root).as_posix()
            stat = file_path.stat()
            found[rel] = DocumentCandidate(
                relative_path=rel,
                absolute_path=file_path,
                size=stat.st_size,
                classification=classify_document(rel),
            )

    for dir_name in PRIMARY_SCAN_DIRS:
        scan_dir = root / dir_name
        if not scan_dir.is_dir():
            continue
        for file_path in _iter_document_files(scan_dir):
            rel = _to_relative_posix(root, file_path)
            if "/DATOS/" in f"/{rel}/" or rel.startswith("DATOS/"):
                continue
            if rel in found:
                continue
            stat = file_path.stat()
            found[rel] = DocumentCandidate(
                relative_path=rel,
                absolute_path=file_path,
                size=stat.st_size,
                classification=classify_document(rel),
            )

    ordered = sorted(found.values(), key=lambda d: d.relative_path.lower())
    return ordered, map_priority, warnings
