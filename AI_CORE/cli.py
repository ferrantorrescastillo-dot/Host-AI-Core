from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .context_builder import build_context_markdown
from .context_manifest import build_manifest, manifest_to_json, normalize_domain
from .document_discovery import discover_documents, find_project_root


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


def _safe_output_path(root: Path, output_arg: str) -> Path:
    out = Path(output_arg)
    if out.is_absolute():
        raise ValueError("Las rutas de salida deben ser relativas a la raíz del proyecto")
    resolved = (root / out).resolve()
    if root not in [resolved, *resolved.parents]:
        raise ValueError("La ruta de salida no puede salir de la raíz del proyecto")
    return resolved


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
