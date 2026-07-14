from __future__ import annotations

from pathlib import Path

from AI_CORE.context_builder import build_context_markdown
from AI_CORE.context_manifest import build_manifest
from AI_CORE.document_discovery import discover_documents


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bootstrap_fake_root(root: Path) -> None:
    _write(root / "AGENTS.md", "# AGENTS\n- reglas\n")
    _write(root / "MASTER_PLAN.md", "# MASTER\n- roadmap\n")
    _write(root / "CODEX-01.md", "# C1\n- metodo\n")
    _write(root / "CODEX-02.md", "# C2\n- tests\n")
    _write(root / "DEVKIT" / "KNOWLEDGE_CORE" / "03_REGLAS.md", "# Reglas\n- no romper\n")
    _write(root / "ROC" / "ROC-02A_OPERACION.md", "# ROC OP\n- produccion\n")
    _write(root / "DOCS" / "produccion_flujo.md", "# Flujo Produccion\n- cerrar produccion\n")
    _write(root / "DOCS" / "stock_guia.md", "# Guia Stock\n- conteo\n")


def test_manifest_priority_and_missing_required(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap_fake_root(root)
    (root / "CODEX-02.md").unlink()

    docs, map_priority, discover_warnings = discover_documents(root)
    manifest, warnings = build_manifest(docs, map_priority, discover_warnings, domain="general")

    first_paths = [m.relative_path for m in manifest[:3]]
    assert "AGENTS.md" in first_paths
    assert "MASTER_PLAN.md" in first_paths
    assert any("obligatorio ausente" in w.lower() for w in warnings)


def test_manifest_no_missing_required_warning_when_all_present(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap_fake_root(root)

    docs, map_priority, discover_warnings = discover_documents(root)
    _manifest, warnings = build_manifest(docs, map_priority, discover_warnings, domain="general")

    assert not any("documento obligatorio ausente" in w.lower() for w in warnings)


def test_context_generation_domain_filter_and_determinism(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap_fake_root(root)

    docs, map_priority, discover_warnings = discover_documents(root)
    manifest1, warnings1 = build_manifest(docs, map_priority, discover_warnings, domain="stock")
    manifest2, warnings2 = build_manifest(docs, map_priority, discover_warnings, domain="stock")

    assert [m.relative_path for m in manifest1] == [m.relative_path for m in manifest2]
    assert warnings1 == warnings2

    context_md = build_context_markdown(root, manifest1, warnings1, domain="stock", max_sources=6)
    assert "Dominio solicitado: stock" in context_md
    assert "## Orden de autoridad aplicado" in context_md
    assert "DOCS/stock_guia.md" in context_md


def test_context_has_no_absolute_paths(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap_fake_root(root)

    docs, map_priority, discover_warnings = discover_documents(root)
    manifest, warnings = build_manifest(docs, map_priority, discover_warnings, domain="general")
    context_md = build_context_markdown(root, manifest, warnings, domain="general", max_sources=5)

    assert str(root) not in context_md
    assert ":\\" not in context_md
