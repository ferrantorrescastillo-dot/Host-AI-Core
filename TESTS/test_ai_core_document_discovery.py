from __future__ import annotations

from pathlib import Path

from AI_CORE.document_discovery import discover_documents, find_project_root


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bootstrap_fake_root(root: Path) -> None:
    _write(root / "AGENTS.md", "# AGENTS\n")
    _write(root / "MASTER_PLAN.md", "# MASTER\n")
    _write(root / "CODEX-01.md", "# C1\n")
    _write(root / "CODEX-02.md", "# C2\n")
    _write(root / "DEVKIT" / "KNOWLEDGE_CORE" / "03_REGLAS.md", "# Reglas\n")
    _write(root / "ROC" / "ROC-01A_NUCLEO.md", "# ROC\n")
    _write(root / "DOCS" / "ARQUITECTURA_GENERAL_HOST_AI.md", "# Arquitectura\n")


def test_find_project_root_detects_from_nested_path(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap_fake_root(root)
    nested = root / "DEVKIT" / "KNOWLEDGE_CORE"
    detected = find_project_root(nested)
    assert detected == root


def test_discover_documents_excludes_sensitive_and_datos(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap_fake_root(root)
    _write(root / "DOCS" / "notes.md", "# Notes\n")
    _write(root / "DOCS" / "secret_keys.md", "secret\n")
    _write(root / "DATOS" / "db" / "manual.md", "no debe entrar\n")
    _write(root / "LOGS" / "run.txt", "log\n")
    _write(root / "DOCS" / "binario.pdf", "fake")

    docs, _map_priority, warnings = discover_documents(root)
    rels = {d.relative_path for d in docs}

    assert "DOCS/notes.md" in rels
    assert "DOCS/secret_keys.md" not in rels
    assert "DATOS/db/manual.md" not in rels
    assert "LOGS/run.txt" not in rels
    assert all(not rel.lower().endswith(".pdf") for rel in rels)
    assert isinstance(warnings, list)


def test_documentacion_map_priority_and_warnings(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap_fake_root(root)
    _write(root / "DOCS" / "X.md", "# X\n")
    _write(
        root / "DOCUMENTACION_MAP.md",
        "- [X](DOCS/X.md)\n- AGENTS.md\n- ./NOPE.md\n- C:/abs/path.md\n",
    )

    _docs, map_priority, warnings = discover_documents(root)
    assert map_priority[0] == "DOCS/X.md"
    assert "AGENTS.md" in map_priority
    assert any("no encontrada" in w.lower() for w in warnings)
    assert any("absoluta" in w.lower() for w in warnings)
