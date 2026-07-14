from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FileType(str, Enum):
    PYTHON = "python"
    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    INI = "ini"
    CSV = "csv"
    EXCEL = "excel"
    DATABASE = "database"
    UNKNOWN = "unknown"


class FileStatus(str, Enum):
    ANALYZED = "analyzed"
    EXCLUDED = "excluded"
    SKIPPED = "skipped"
    ERROR = "error"


class ParseStatus(str, Enum):
    OK = "ok"
    PARSE_ERROR = "parse_error"
    READ_ERROR = "read_error"
    EMPTY = "empty"


@dataclass(frozen=True)
class ImportRecord:
    import_type: str
    module: str | None
    imported_names: tuple[str, ...]
    aliases: tuple[str | None, ...]
    level: int
    start_line: int
    internal_resolution: str = "pending"
    raw_representation: str | None = None


@dataclass(frozen=True)
class PythonFunctionRecord:
    id: str
    module_id: str
    class_id: str | None
    qualified_name: str
    name: str
    function_type: str
    parameters: tuple[dict[str, str | None], ...]
    decorators: tuple[str, ...]
    docstring: str | None
    start_line: int
    end_line: int
    async_status: bool
    return_annotation: str | None
    parameter_annotations: tuple[dict[str, str | None], ...]
    method_kind: str | None = None


@dataclass(frozen=True)
class PythonClassRecord:
    id: str
    module_id: str
    qualified_name: str
    name: str
    bases: tuple[str, ...]
    decorators: tuple[str, ...]
    docstring: str | None
    methods: tuple[PythonFunctionRecord, ...]
    start_line: int
    end_line: int
    async_status: bool
    nested_classes: tuple["PythonClassRecord", ...] = ()


@dataclass(frozen=True)
class PythonModuleRecord:
    id: str
    file_id: str
    relative_path: str
    module_name: str
    package_name: str | None
    docstring: str | None
    imports: tuple[ImportRecord, ...]
    classes: tuple[PythonClassRecord, ...]
    functions: tuple[PythonFunctionRecord, ...]
    warnings: tuple[str, ...]
    parse_status: ParseStatus
    fingerprint: str
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class FileRecord:
    id: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    modified_time: float
    fingerprint: str | None
    file_type: FileType
    status: FileStatus
    exclusion_reason: str | None
    encoding: str | None
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepositoryScanResult:
    project_root: str
    scanned_at: str
    directories_found: int
    files_found: int
    files_analyzed: int
    files_excluded: int
    python_files: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    metrics: dict[str, int]
    repository_fingerprint: str
    file_records: tuple[FileRecord, ...] = field(default_factory=tuple)
