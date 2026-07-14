from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from .context_builder import build_context_markdown
from .context_manifest import build_manifest
from .document_discovery import discover_documents, find_project_root
from .repository_inventory import build_repository_inventory
from .repository_scanner import ScannerConfig


DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "produccion": ("produccion", "producción", "prod", "piloto-1.3", "piloto-1.4", "jornada"),
    "stock": ("stock", "inventario", "lote", "movimiento"),
    "compras": ("compra", "compras", "pedido", "proveedor"),
    "recepcion": ("recepcion", "recepción", "albaran", "albarán", "mercancia", "mercancía"),
    "eventos": ("evento", "eventos", "banquete"),
    "escandallos": ("escandallo", "escandallos", "receta", "coste_receta"),
    "costes": ("coste", "costes", "rentabilidad", "margen"),
    "arquitectura": ("arquitectura", "roc", "componente"),
    "ia": ("ia", "ai", "copilot", "prompt", "agente"),
}


@dataclass(frozen=True)
class TaskPackResult:
    task: str
    domain: str
    output_dir: Path
    documents_count: int
    code_files_count: int
    symbols_count: int
    tests_count: int
    prompt_size_chars: int


def _slugify(text: str) -> str:
    cleaned = text.strip().lower()
    cleaned = cleaned.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")
    return cleaned or "general"


def infer_domain(task_description: str) -> str:
    text = task_description.lower()
    best_domain = "general"
    best_score = 0
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for k in keywords if k in text)
        if score > best_score:
            best_score = score
            best_domain = domain
    return best_domain


def _select_documents(manifest_entries: list[object], max_docs: int = 20) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    for e in manifest_entries:
        category = getattr(e, "category")
        if category == "historico":
            continue
        selected.append(
            {
                "path": getattr(e, "relative_path"),
                "priority": getattr(e, "priority"),
                "category": category,
                "reason": getattr(e, "inclusion_reason"),
            }
        )
        if len(selected) >= max_docs:
            break
    return selected


def _score_path(path: str, domain: str) -> tuple[int, list[str]]:
    p = path.lower()
    reasons: list[str] = []
    score = 0

    if p.endswith(".py"):
        score += 20
    if p.startswith("tests/"):
        score += 8
    if p.startswith(("app/", "servicios/", "motores/", "core/", "pipelines/", "modelos/")):
        score += 12

    if domain != "general":
        keywords = DOMAIN_KEYWORDS.get(domain, ())
        for kw in keywords:
            if kw in p:
                score += 15
                reasons.append(f"match_keyword:{kw}")

    if not reasons:
        reasons.append("cercania_arquitectura")

    return score, reasons


def _select_code_files(inventory: dict[str, object], domain: str, max_files: int = 60) -> list[dict[str, object]]:
    scan = inventory.get("scan", {})
    file_records = scan.get("file_records", []) if isinstance(scan, dict) else []

    selected: list[dict[str, object]] = []
    for rec in file_records:
        if rec.get("status") != "analyzed":
            continue
        path = rec.get("relative_path", "")
        if not str(path).endswith(".py"):
            continue
        score, reasons = _score_path(str(path), domain)
        if domain == "general" and score < 20:
            continue
        if domain != "general" and score < 30:
            continue
        selected.append(
            {
                "path": path,
                "reason": ",".join(reasons),
                "priority": score,
                "domain_relation": domain,
            }
        )

    selected.sort(key=lambda x: (-int(x["priority"]), str(x["path"]).lower()))
    return selected[:max_files]


def _select_symbols(inventory: dict[str, object], code_files: list[dict[str, object]], domain: str) -> dict[str, list[dict[str, object]]]:
    module_index = {m.get("relative_path"): m for m in inventory.get("python_modules", [])}
    code_paths = {c["path"] for c in code_files}
    keywords = DOMAIN_KEYWORDS.get(domain, ()) if domain != "general" else ()

    classes: list[dict[str, object]] = []
    functions: list[dict[str, object]] = []
    methods: list[dict[str, object]] = []

    def rel_match(name: str) -> bool:
        if domain == "general":
            return True
        lower = name.lower()
        return any(k in lower for k in keywords)

    for path in sorted(code_paths):
        mod = module_index.get(path)
        if not isinstance(mod, dict):
            continue

        for cls in mod.get("classes", []):
            qn = str(cls.get("qualified_name", ""))
            if rel_match(qn) or path in code_paths:
                classes.append(
                    {
                        "id": cls.get("id"),
                        "qualified_name": qn,
                        "path": path,
                        "start_line": cls.get("start_line"),
                        "end_line": cls.get("end_line"),
                    }
                )
            for m in cls.get("methods", []):
                qn_m = str(m.get("qualified_name", ""))
                if rel_match(qn_m) or path in code_paths:
                    methods.append(
                        {
                            "id": m.get("id"),
                            "qualified_name": qn_m,
                            "path": path,
                            "function_type": m.get("function_type"),
                            "method_kind": m.get("method_kind"),
                            "start_line": m.get("start_line"),
                            "end_line": m.get("end_line"),
                        }
                    )

        for fn in mod.get("functions", []):
            qn_f = str(fn.get("qualified_name", ""))
            if rel_match(qn_f) or path in code_paths:
                functions.append(
                    {
                        "id": fn.get("id"),
                        "qualified_name": qn_f,
                        "path": path,
                        "function_type": fn.get("function_type"),
                        "start_line": fn.get("start_line"),
                        "end_line": fn.get("end_line"),
                    }
                )

    classes.sort(key=lambda x: (str(x["path"]).lower(), str(x["qualified_name"]).lower()))
    functions.sort(key=lambda x: (str(x["path"]).lower(), str(x["qualified_name"]).lower()))
    methods.sort(key=lambda x: (str(x["path"]).lower(), str(x["qualified_name"]).lower()))
    return {
        "classes": classes[:120],
        "functions": functions[:160],
        "methods": methods[:240],
    }


def _select_tests(code_files: list[dict[str, object]], domain: str, inventory: dict[str, object]) -> list[dict[str, object]]:
    scan = inventory.get("scan", {})
    file_records = scan.get("file_records", []) if isinstance(scan, dict) else []
    selected_code = [str(c["path"]) for c in code_files]
    stems = {Path(p).stem.lower() for p in selected_code}
    keywords = DOMAIN_KEYWORDS.get(domain, ()) if domain != "general" else ()

    tests: list[dict[str, object]] = []
    for rec in file_records:
        if rec.get("status") != "analyzed":
            continue
        path = str(rec.get("relative_path", ""))
        p_lower = path.lower()
        if not p_lower.startswith("tests/"):
            continue
        if not p_lower.endswith(".py"):
            continue

        reason = None
        for stem in stems:
            if stem and stem in p_lower:
                reason = f"match_stem:{stem}"
                break
        if reason is None and domain != "general":
            for kw in keywords:
                if kw in p_lower:
                    reason = f"match_keyword:{kw}"
                    break
        if reason is None:
            continue

        tests.append(
            {
                "path": path,
                "reason": reason,
            }
        )

    tests.sort(key=lambda x: str(x["path"]).lower())
    return tests[:120]


def _build_checklist(task: str, domain: str) -> str:
    lines = [
        "# Checklist tecnica",
        "",
        f"- Tarea: {task}",
        f"- Dominio inferido: {domain}",
        "",
        "- No modificar DATOS/ ni bases funcionales.",
        "- No modificar Documentos/AI.docx.",
        "- No romper compatibilidad de AI_CORE v1 y v2.1.",
        "- Mantener cambios acotados a archivos relevantes.",
        "- Añadir/actualizar tests relacionados.",
        "- Ejecutar tests especificos del alcance.",
        "- Revisar impactos en CLI y salidas.",
        "- Validar determinismo en salida generada.",
    ]
    return "\n".join(lines) + "\n"


def _build_documents_md(documents: list[dict[str, object]]) -> str:
    lines = ["# Documentos relevantes", "", "Prioridad ascendente (menor numero = mayor prioridad)", ""]
    for idx, d in enumerate(documents, start=1):
        lines.append(
            f"{idx}. {d['path']} | prioridad={d['priority']} | categoria={d['category']} | motivo={d['reason']}"
        )
    lines.append("")
    return "\n".join(lines)


def _build_copilot_prompt(
    task: str,
    domain: str,
    documents: list[dict[str, object]],
    code_files: list[dict[str, object]],
    tests: list[dict[str, object]],
) -> str:
    lines = [
        "# Prompt Operativo para Copilot",
        "",
        f"Objetivo: {task}",
        f"Dominio: {domain}",
        "",
        "## Restricciones",
        "- No tocar DATOS, DB ni Documentos/AI.docx.",
        "- No romper AI_CORE v1/v2.1.",
        "- Cambios minimos y verificables.",
        "",
        "## Documentacion prioritaria",
    ]
    for d in documents[:8]:
        lines.append(f"- {d['path']} (p={d['priority']})")

    lines.extend(["", "## Archivos de codigo foco"])
    for c in code_files[:20]:
        lines.append(f"- {c['path']} (p={c['priority']}, motivo={c['reason']})")

    lines.extend(["", "## Tests relacionados"])
    for t in tests[:20]:
        lines.append(f"- {t['path']} ({t['reason']})")

    lines.extend(
        [
            "",
            "## Entrega esperada",
            "- Implementacion acotada al objetivo.",
            "- Tests relevantes en verde.",
            "- Resumen tecnico de cambios con riesgos.",
        ]
    )
    return "\n".join(lines) + "\n"


def _safe_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _safe_write_json(path: Path, payload: object) -> None:
    content = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    _safe_write(path, content + "\n")


def build_task_context_package(
    task_description: str,
    project_root: Path | None = None,
    output_base: Path | None = None,
) -> TaskPackResult:
    root = find_project_root(project_root or Path.cwd())
    domain = infer_domain(task_description)
    task_slug = _slugify(task_description)

    base_out = output_base or (root / "AI_CORE" / "output" / "tasks")
    output_dir = (base_out / task_slug).resolve()
    if root not in [output_dir, *output_dir.parents]:
        raise ValueError("La salida de task-context debe quedar dentro del repositorio")

    docs, map_priority, discover_warnings = discover_documents(root)
    manifest, manifest_warnings = build_manifest(
        documents=docs,
        map_priority=map_priority,
        map_warnings=discover_warnings,
        domain=domain,
    )
    selected_documents = _select_documents(manifest)

    context_md = build_context_markdown(
        project_root=root,
        entries=manifest,
        warnings=manifest_warnings,
        domain=domain,
        max_sources=10,
    )
    context_preface = f"# Task Context\n\n- Tarea: {task_description}\n- Dominio inferido: {domain}\n\n"
    context_text = context_preface + context_md

    inv = build_repository_inventory(root, config=ScannerConfig())
    code_files = _select_code_files(inv, domain=domain)
    symbols = _select_symbols(inv, code_files=code_files, domain=domain)
    tests = _select_tests(code_files=code_files, domain=domain, inventory=inv)
    checklist_md = _build_checklist(task_description, domain)
    prompt_md = _build_copilot_prompt(task_description, domain, selected_documents, code_files, tests)

    _safe_write(output_dir / "CONTEXT.md", context_text)
    _safe_write(output_dir / "DOCUMENTS.md", _build_documents_md(selected_documents))
    _safe_write_json(output_dir / "CODE_FILES.json", {"task": task_description, "domain": domain, "files": code_files})
    _safe_write_json(output_dir / "SYMBOLS.json", {"task": task_description, "domain": domain, **symbols})
    _safe_write_json(
        output_dir / "TESTS.json",
        {
            "task": task_description,
            "domain": domain,
            "tests": tests,
            "coverage_known": {
                "tests_found": len(tests),
                "code_files_considered": len(code_files),
            },
        },
    )
    _safe_write(output_dir / "CHECKLIST.md", checklist_md)
    _safe_write(output_dir / "COPILOT_PROMPT.md", prompt_md)

    return TaskPackResult(
        task=task_description,
        domain=domain,
        output_dir=output_dir,
        documents_count=len(selected_documents),
        code_files_count=len(code_files),
        symbols_count=len(symbols.get("classes", [])) + len(symbols.get("functions", [])) + len(symbols.get("methods", [])),
        tests_count=len(tests),
        prompt_size_chars=len(prompt_md),
    )
