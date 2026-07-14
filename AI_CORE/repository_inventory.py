from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from .python_static_analyzer import analyze_python_file
from .repository_models import FileType, ParseStatus
from .repository_scanner import ScannerConfig, scan_repository


SCHEMA_VERSION = "ai_core_repository_inventory_v2_1"
GENERATOR_VERSION = "AI_CORE v2.1"


def _as_jsonable(obj: object) -> object:
    if hasattr(obj, "value"):
        return getattr(obj, "value")
    return obj


def _to_serializable(data: object) -> object:
    if isinstance(data, dict):
        return {k: _to_serializable(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_to_serializable(x) for x in data]
    if isinstance(data, tuple):
        return [_to_serializable(x) for x in data]
    if hasattr(data, "__dataclass_fields__"):
        return _to_serializable(asdict(data))
    converted = _as_jsonable(data)
    if converted is not data:
        return _to_serializable(converted)
    return data


def build_repository_inventory(
    project_root: Path,
    config: ScannerConfig | None = None,
) -> dict[str, object]:
    scan_result = scan_repository(project_root=project_root, config=config)

    modules = []
    parse_errors = 0
    ok_modules = 0
    total_classes = 0
    total_functions = 0
    total_methods = 0
    total_imports = 0

    for file_record in scan_result.file_records:
        if file_record.file_type != FileType.PYTHON or file_record.status.value != "analyzed":
            continue
        module = analyze_python_file(project_root / file_record.relative_path, file_record.relative_path)
        modules.append(module)
        if module.parse_status == ParseStatus.OK:
            ok_modules += 1
        if module.parse_status == ParseStatus.PARSE_ERROR:
            parse_errors += 1
        total_classes += len(module.classes)
        total_functions += len(module.functions)
        total_methods += sum(len(c.methods) for c in module.classes)
        total_imports += len(module.imports)

    modules.sort(key=lambda m: m.relative_path.lower())

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": ".",
        "repository_fingerprint": scan_result.repository_fingerprint,
        "metrics": {
            **scan_result.metrics,
            "python_modules": len(modules),
            "python_modules_ok": ok_modules,
            "python_modules_parse_error": parse_errors,
            "python_classes": total_classes,
            "python_functions": total_functions,
            "python_methods": total_methods,
            "python_imports": total_imports,
        },
        "scan": _to_serializable(scan_result),
        "python_modules": _to_serializable(tuple(modules)),
        "warnings": sorted(list(scan_result.warnings)),
        "errors": sorted(list(scan_result.errors)),
    }
    return payload


def write_inventory_json(payload: dict[str, object], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    content = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    # Validación estructural previa a escritura final.
    json.loads(content)
    tmp_path.write_text(content + "\n", encoding="utf-8")
    tmp_path.replace(output_path)
    return output_path
