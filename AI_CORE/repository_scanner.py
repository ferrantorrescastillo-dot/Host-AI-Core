from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
import fnmatch

from .repository_fingerprints import hash_file_content, hash_repository
from .repository_ids import file_id, normalize_relative_path
from .repository_models import FileRecord, FileStatus, FileType, RepositoryScanResult


DEFAULT_EXCLUDED_DIR_NAMES: tuple[str, ...] = (
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    "node_modules",
    "caches",
    "LOGS",
)

DEFAULT_EXCLUDED_RELATIVE_PATTERNS: tuple[str, ...] = (
    "AI_CORE/output/*",
    "TEMP/ai_core_*",
    "*.pyc",
)

DEFAULT_EXCLUDED_EXTENSIONS: tuple[str, ...] = (
    ".zip",
    ".exe",
    ".dll",
)


@dataclass(frozen=True)
class ScannerConfig:
    excluded_dir_names: tuple[str, ...] = DEFAULT_EXCLUDED_DIR_NAMES
    excluded_relative_patterns: tuple[str, ...] = DEFAULT_EXCLUDED_RELATIVE_PATTERNS
    excluded_extensions: tuple[str, ...] = DEFAULT_EXCLUDED_EXTENSIONS
    include_extensions: tuple[str, ...] | None = None
    max_file_size_bytes: int | None = None
    root_subdir: str | None = None


def _detect_file_type(path: Path) -> FileType:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return FileType.PYTHON
    if suffix in {".md", ".markdown"}:
        return FileType.MARKDOWN
    if suffix in {".txt", ".rst"}:
        return FileType.TEXT
    if suffix == ".json":
        return FileType.JSON
    if suffix in {".yaml", ".yml"}:
        return FileType.YAML
    if suffix == ".toml":
        return FileType.TOML
    if suffix in {".ini", ".cfg"}:
        return FileType.INI
    if suffix == ".csv":
        return FileType.CSV
    if suffix in {".xlsx", ".xls", ".xlsm", ".ods"}:
        return FileType.EXCEL
    if suffix in {".sqlite", ".db", ".db3"}:
        return FileType.DATABASE
    return FileType.UNKNOWN


def _match_any(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def _should_exclude_file(rel_path: str, path: Path, config: ScannerConfig) -> tuple[bool, str | None]:
    suffix = path.suffix.lower()
    if suffix in {ext.lower() for ext in config.excluded_extensions}:
        return True, f"extension_excluded:{suffix}"
    if _match_any(rel_path, config.excluded_relative_patterns):
        return True, "pattern_excluded"
    if config.include_extensions is not None and suffix not in {e.lower() for e in config.include_extensions}:
        return True, "extension_not_included"
    return False, None


def _safe_relative(root: Path, candidate: Path) -> str:
    return normalize_relative_path(candidate.relative_to(root).as_posix())


def scan_repository(project_root: Path, config: ScannerConfig | None = None) -> RepositoryScanResult:
    cfg = config or ScannerConfig()
    root = project_root.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Raiz invalida para escaneo: {project_root}")

    scan_root = root
    if cfg.root_subdir:
        scan_root = (root / cfg.root_subdir).resolve()
        if root not in [scan_root, *scan_root.parents] or not scan_root.is_dir():
            raise ValueError(f"Subdirectorio invalido para escaneo: {cfg.root_subdir}")

    warnings: list[str] = []
    errors: list[str] = []
    records: list[FileRecord] = []
    repository_pairs: list[tuple[str, str]] = []
    directories_found: set[str] = set()

    excluded_dir_names_lower = {d.lower() for d in cfg.excluded_dir_names}

    for current_dir, dirnames, filenames in os.walk(scan_root, topdown=True, followlinks=False):
        current_path = Path(current_dir)
        try:
            current_rel = _safe_relative(root, current_path)
        except Exception:
            warnings.append(f"ruta_no_relativizable:{current_path}")
            continue

        if current_rel:
            directories_found.add(current_rel)

        pruned: list[str] = []
        for d in sorted(dirnames, key=str.lower):
            d_path = current_path / d
            d_rel = _safe_relative(root, d_path)

            if d_path.is_symlink():
                try:
                    resolved = d_path.resolve(strict=False)
                    if root not in [resolved, *resolved.parents]:
                        warnings.append(f"symlink_fuera_raiz_ignorado:{d_rel}")
                        continue
                except Exception as exc:
                    warnings.append(f"symlink_inaccesible:{d_rel}:{exc}")
                    continue

            if d.lower() in excluded_dir_names_lower:
                continue
            if _match_any(d_rel, cfg.excluded_relative_patterns):
                continue
            pruned.append(d)
        dirnames[:] = pruned

        for fname in sorted(filenames, key=str.lower):
            path = current_path / fname
            try:
                rel_path = _safe_relative(root, path)
            except Exception:
                warnings.append(f"ruta_no_relativizable:{path}")
                continue

            if path.is_symlink():
                try:
                    resolved = path.resolve(strict=False)
                    if root not in [resolved, *resolved.parents]:
                        warnings.append(f"symlink_fuera_raiz_ignorado:{rel_path}")
                        continue
                except Exception as exc:
                    warnings.append(f"symlink_inaccesible:{rel_path}:{exc}")
                    continue

            try:
                stat = path.stat()
            except Exception as exc:
                warnings.append(f"archivo_inaccesible:{rel_path}:{exc}")
                continue

            excluded, exclusion_reason = _should_exclude_file(rel_path, path, cfg)
            file_type = _detect_file_type(path)
            file_encoding: str | None = None
            file_errors: list[str] = []
            file_warnings: list[str] = []
            fingerprint: str | None = None
            status = FileStatus.ANALYZED

            if cfg.max_file_size_bytes is not None and stat.st_size > cfg.max_file_size_bytes:
                excluded = True
                exclusion_reason = f"size_limit_exceeded:{cfg.max_file_size_bytes}"

            if excluded:
                status = FileStatus.EXCLUDED
            else:
                try:
                    fingerprint = hash_file_content(path)
                    repository_pairs.append((rel_path, fingerprint))
                except Exception as exc:
                    status = FileStatus.ERROR
                    file_errors.append(f"fingerprint_error:{exc}")

            if file_type in {FileType.EXCEL, FileType.DATABASE} and status == FileStatus.ANALYZED:
                file_warnings.append("metadatos_solo:no_se_analiza_contenido")

            rec = FileRecord(
                id=file_id(rel_path),
                relative_path=rel_path,
                filename=path.name,
                extension=path.suffix.lower(),
                size_bytes=stat.st_size,
                modified_time=float(stat.st_mtime),
                fingerprint=fingerprint,
                file_type=file_type,
                status=status,
                exclusion_reason=exclusion_reason,
                encoding=file_encoding,
                warnings=tuple(file_warnings),
                errors=tuple(file_errors),
            )
            records.append(rec)

    records.sort(key=lambda r: r.relative_path.lower())
    files_found = len(records)
    files_excluded = sum(1 for r in records if r.status == FileStatus.EXCLUDED)
    files_analyzed = sum(1 for r in records if r.status == FileStatus.ANALYZED)
    python_files = sum(1 for r in records if r.file_type == FileType.PYTHON and r.status == FileStatus.ANALYZED)
    repository_fingerprint = hash_repository(repository_pairs)

    return RepositoryScanResult(
        project_root=".",
        scanned_at=datetime.now(timezone.utc).isoformat(),
        directories_found=len(directories_found),
        files_found=files_found,
        files_analyzed=files_analyzed,
        files_excluded=files_excluded,
        python_files=python_files,
        warnings=tuple(sorted(warnings)),
        errors=tuple(sorted(errors)),
        metrics={
            "directories_found": len(directories_found),
            "files_found": files_found,
            "files_analyzed": files_analyzed,
            "files_excluded": files_excluded,
            "python_files": python_files,
        },
        repository_fingerprint=repository_fingerprint,
        file_records=tuple(records),
    )
