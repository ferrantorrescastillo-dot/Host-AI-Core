from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .context_manifest import ManifestEntry, normalize_domain


@dataclass(frozen=True)
class SourceSummary:
    relative_path: str
    title: str
    bullets: tuple[str, ...]


def _read_title_and_excerpt(path: Path, max_lines: int = 80) -> tuple[str, list[str]]:
    if not path.is_file():
        return "(no disponible)", []

    lines: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f):
            if idx >= max_lines:
                break
            lines.append(line.rstrip("\n"))

    title = "(sin título detectado)"
    for line in lines:
        cleaned = line.strip()
        if cleaned.startswith("#"):
            title = cleaned.lstrip("# ").strip() or title
            break
    if title == "(sin título detectado)" and lines:
        title = lines[0].strip() or title
    return title, lines


def _extract_bullets(lines: list[str], limit: int = 5) -> list[str]:
    bullets: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
        elif stripped and not stripped.startswith("#") and len(stripped) > 30:
            bullets.append(stripped)
        if len(bullets) >= limit:
            break
    return bullets


def _authority_order_lines(entries: list[ManifestEntry]) -> list[str]:
    top = entries[:8]
    lines: list[str] = []
    for idx, entry in enumerate(top, start=1):
        lines.append(
            f"{idx}. {entry.relative_path} "
            f"(categoria={entry.category}, prioridad={entry.priority})"
        )
    return lines


def build_context_markdown(
    project_root: Path,
    entries: list[ManifestEntry],
    warnings: list[str],
    domain: str | None = None,
    max_sources: int = 12,
) -> str:
    """Genera paquete de contexto conciso y trazable sin volcar documentos completos."""
    normalized_domain = normalize_domain(domain)
    selected = entries[:max_sources]

    summaries: list[SourceSummary] = []
    for entry in selected:
        abs_path = project_root / entry.relative_path
        title, lines = _read_title_and_excerpt(abs_path)
        bullets = tuple(_extract_bullets(lines))
        summaries.append(
            SourceSummary(
                relative_path=entry.relative_path,
                title=title,
                bullets=bullets,
            )
        )

    output: list[str] = []
    output.append("# Host AI - Paquete de Contexto AI_CORE v1")
    output.append("")
    output.append("## Objetivo del paquete")
    output.append(
        "Contexto documental de solo lectura para guiar a un agente de IA "
        "sin copiar masivamente documentación, manteniendo autoridad y trazabilidad."
    )
    output.append("")
    output.append("## Parámetros")
    output.append(f"- Dominio solicitado: {normalized_domain}")
    output.append(f"- Fuentes seleccionadas: {len(selected)} de {len(entries)}")
    output.append("")

    output.append("## Documentos consultados")
    for entry in selected:
        output.append(
            "- "
            f"{entry.relative_path} "
            f"(categoria={entry.category}, prioridad={entry.priority}, estado={entry.status})"
        )
    output.append("")

    output.append("## Orden de autoridad aplicado")
    output.extend(_authority_order_lines(entries))
    output.append("")

    output.append("## Resumen estructurado por fuente")
    for summary in summaries:
        output.append(f"### {summary.relative_path}")
        output.append(f"- Título detectado: {summary.title}")
        if summary.bullets:
            for bullet in summary.bullets:
                output.append(f"- {bullet}")
        else:
            output.append("- Sin extractos útiles en el tramo leído.")
        output.append(
            "- Referencia original: consultar el archivo fuente para precisión operativa."
        )
        output.append("")

    output.append("## Advertencias")
    if warnings:
        for warning in warnings:
            output.append(f"- {warning}")
    else:
        output.append("- Sin advertencias críticas detectadas.")
    output.append("")

    output.append("## Instrucciones para el agente")
    output.append(
        "- Si existe conflicto entre resúmenes, consultar primero el documento original "
        "de mayor autoridad según el orden anterior."
    )
    output.append(
        "- No asumir que el resumen sustituye a la fuente: usarlo solo como mapa de arranque."
    )
    output.append(
        "- Si falta un documento obligatorio, detener decisiones críticas y solicitar revisión humana."
    )
    output.append("")

    return "\n".join(output).rstrip() + "\n"
