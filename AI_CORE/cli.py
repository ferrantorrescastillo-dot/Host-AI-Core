from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .context_builder import build_context_markdown
from .context_manifest import build_manifest, manifest_to_json, normalize_domain
from .document_discovery import discover_documents, find_project_root
from .repository_inventory import build_repository_inventory, write_inventory_json
from .repository_scanner import ScannerConfig, scan_repository
from .task_pack_engine import build_task_context_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m AI_CORE.cli",
        description="AI_CORE v1: genera manifiesto y paquete de contexto documental.",
    )
    parser.add_argument(
        "--domain",
        default="general",
        help=(
            "Dominio opcional: produccion, stock, compras, recepcion, eventos, "
            "escandallos, costes, arquitectura, ia o general"
        ),
    )
    parser.add_argument(
        "--output",
        default="TEMP/ai_context.md",
        help="Ruta de salida del contexto markdown (relativa a la raíz).",
    )
    parser.add_argument(
        "--manifest-output",
        default="TEMP/ai_context_manifest.json",
        help="Ruta de salida del manifiesto JSON (relativa a la raíz).",
    )
    parser.add_argument(
        "--max-sources",
        type=int,
        default=12,
        help="Máximo de fuentes resumidas en el paquete de contexto.",
    )
    return parser


def build_repository_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m AI_CORE.cli repository",
        description="AI_CORE v2.1: inspeccion de repositorio y analisis estatico Python.",
    )
    sub = parser.add_subparsers(dest="repository_command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--root", default=".", help="Raiz del proyecto a inspeccionar.")
        p.add_argument("--subdir", default=None, help="Subdirectorio relativo a la raiz para limitar el escaneo.")
        p.add_argument("--max-size-bytes", type=int, default=None, help="Limite de tamano por archivo.")

    p_scan = sub.add_parser("scan", help="Escanea el repositorio y muestra metricas base.")
    add_common(p_scan)

    p_analyze = sub.add_parser("analyze-python", help="Escanea y analiza solo modulos Python con AST.")
    add_common(p_analyze)

    p_build = sub.add_parser("build-inventory", help="Construye inventario completo y lo escribe a JSON.")
    add_common(p_build)
    p_build.add_argument(
        "--output",
        default="AI_CORE/output/knowledge/repository_inventory.json",
        help="Ruta de salida del inventario JSON (relativa a la raiz).",
    )
    p_build.add_argument("--force", action="store_true", help="Sobrescribe salida existente.")

    p_summary = sub.add_parser("summary", help="Construye inventario y muestra resumen controlado.")
    add_common(p_summary)
    p_summary.add_argument(
        "--output",
        default="AI_CORE/output/knowledge/repository_inventory.json",
        help="Ruta de salida opcional para guardar inventario.",
    )
    p_summary.add_argument("--show-warnings", action="store_true", help="Muestra warnings del analisis.")

    return parser


def _safe_output_path(root: Path, output_arg: str) -> Path:
    out = Path(output_arg)
    if out.is_absolute():
        raise ValueError("Las rutas de salida deben ser relativas a la raíz del proyecto")
    resolved = (root / out).resolve()
    if root not in [resolved, *resolved.parents]:
        raise ValueError("La ruta de salida no puede salir de la raíz del proyecto")
    return resolved


def _build_scanner_config(args: argparse.Namespace) -> ScannerConfig:
    return ScannerConfig(
        max_file_size_bytes=args.max_size_bytes,
        root_subdir=args.subdir,
    )


def _run_repository(argv: list[str]) -> int:
    parser = build_repository_parser()
    args = parser.parse_args(argv)

    try:
        requested_root = Path(args.root)
        if not requested_root.exists() or not requested_root.is_dir():
            raise ValueError(f"Raiz inexistente o invalida: {requested_root}")
        root = find_project_root(requested_root)
        config = _build_scanner_config(args)

        if args.repository_command == "scan":
            result = scan_repository(root, config=config)
            print("AI_CORE repository scan OK")
            print(f"- raiz: {root}")
            print(f"- directorios: {result.directories_found}")
            print(f"- archivos: {result.files_found}")
            print(f"- analizados: {result.files_analyzed}")
            print(f"- excluidos: {result.files_excluded}")
            print(f"- python: {result.python_files}")
            print(f"- fingerprint: {result.repository_fingerprint}")
            return 0

        payload = build_repository_inventory(root, config=config)

        if args.repository_command == "analyze-python":
            metrics = payload["metrics"]
            print("AI_CORE repository analyze-python OK")
            print(f"- modulos_python: {metrics['python_modules']}")
            print(f"- modulos_ok: {metrics['python_modules_ok']}")
            print(f"- modulos_parse_error: {metrics['python_modules_parse_error']}")
            return 0

        out_path = _safe_output_path(root, args.output)
        if out_path.exists() and args.repository_command == "build-inventory" and not args.force:
            raise FileExistsError(f"Salida ya existe, use --force: {out_path}")
        write_inventory_json(payload, out_path)

        metrics = payload["metrics"]
        print("AI_CORE repository inventory OK")
        print(f"- salida: {out_path.relative_to(root)}")
        print(f"- fingerprint: {payload['repository_fingerprint']}")
        print(f"- archivos: {metrics['files_found']}")
        print(f"- excluidos: {metrics['files_excluded']}")
        print(f"- python_modulos: {metrics['python_modules']}")

        if args.repository_command == "summary":
            mods = payload["python_modules"]
            sample = mods[:5]
            print("- muestra_modulos:")
            for m in sample:
                print(f"  * {m['relative_path']} ({m['parse_status']})")
            if args.show_warnings and payload.get("warnings"):
                print("- warnings:")
                for w in payload["warnings"][:20]:
                    print(f"  * {w}")
        return 0
    except Exception as exc:
        print(f"ERROR AI_CORE repository: {exc}", file=sys.stderr)
        return 1


def _run_task_context(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m AI_CORE.cli task-context",
        description="Genera paquete de contexto de tarea para Copilot.",
    )
    parser.add_argument("task", help="Descripcion simple de la tarea (ej: Mejorar Produccion)")
    parser.add_argument("--root", default=".", help="Raiz del proyecto")
    parser.add_argument(
        "--output-base",
        default="AI_CORE/output/tasks",
        help="Directorio base de salida para paquetes de tarea.",
    )
    args = parser.parse_args(argv)

    try:
        requested_root = Path(args.root)
        if not requested_root.exists() or not requested_root.is_dir():
            raise ValueError(f"Raiz inexistente o invalida: {requested_root}")

        result = build_task_context_package(
            task_description=args.task,
            project_root=requested_root,
            output_base=Path(args.output_base),
        )
        print("AI_CORE task-context OK")
        print(f"- tarea: {result.task}")
        print(f"- dominio: {result.domain}")
        print(f"- salida: {result.output_dir}")
        print(f"- documentos: {result.documents_count}")
        print(f"- archivos_codigo: {result.code_files_count}")
        print(f"- simbolos: {result.symbols_count}")
        print(f"- tests: {result.tests_count}")
        print(f"- prompt_chars: {result.prompt_size_chars}")
        return 0
    except Exception as exc:
        print(f"ERROR AI_CORE task-context: {exc}", file=sys.stderr)
        return 1


def run(argv: list[str] | None = None) -> int:
    args_list = list(argv or sys.argv[1:])
    if args_list and args_list[0] == "repository":
        return _run_repository(args_list[1:])
    if args_list and args_list[0] == "task-context":
        return _run_task_context(args_list[1:])

    parser = build_parser()
    args = parser.parse_args(args_list)

    try:
        root = find_project_root(Path.cwd())
        documents, map_priority, discover_warnings = discover_documents(root)

        domain = normalize_domain(args.domain)
        manifest, manifest_warnings = build_manifest(
            documents=documents,
            map_priority=map_priority,
            map_warnings=discover_warnings,
            domain=domain,
        )

        context_md = build_context_markdown(
            project_root=root,
            entries=manifest,
            warnings=manifest_warnings,
            domain=domain,
            max_sources=max(1, args.max_sources),
        )
        manifest_json = manifest_to_json(manifest, manifest_warnings)

        out_md = _safe_output_path(root, args.output)
        out_manifest = _safe_output_path(root, args.manifest_output)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_manifest.parent.mkdir(parents=True, exist_ok=True)

        out_md.write_text(context_md, encoding="utf-8")
        out_manifest.write_text(manifest_json, encoding="utf-8")

        print("AI_CORE v1 generado correctamente")
        print(f"- raiz: {root}")
        print(f"- dominio: {domain}")
        print(f"- documentos descubiertos: {len(documents)}")
        print(f"- entradas manifiesto: {len(manifest)}")
        print(f"- contexto: {out_md.relative_to(root)}")
        print(f"- manifiesto: {out_manifest.relative_to(root)}")
        if manifest_warnings:
            print(f"- advertencias: {len(manifest_warnings)}")
        return 0
    except Exception as exc:
        print(f"ERROR AI_CORE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
