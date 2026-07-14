from __future__ import annotations

from pathlib import Path

import pytest

from AI_CORE.repository_fingerprints import hash_file_content
from AI_CORE.repository_scanner import ScannerConfig, scan_repository


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bootstrap_repo(root: Path) -> None:
    _write(root / "AGENTS.md", "# AGENTS\n")
    _write(root / "MASTER_PLAN.md", "# MASTER\n")
    _write(root / "DEVKIT" / "KNOWLEDGE_CORE" / "03_REGLAS.md", "# R\n")
    _write(root / "src" / "a.py", "x=1\n")
    _write(root / "src" / "b.py", "y=2\n")
    _write(root / "README.md", "doc\n")
    _write(root / ".git" / "config", "x\n")
    _write(root / ".venv" / "bin" / "python", "x\n")
    _write(root / "__pycache__" / "m.pyc", "x\n")
    _write(root / "AI_CORE" / "output" / "knowledge" / "repo.json", "{}\n")


def test_scan_basic_exclusions_and_determinism(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap_repo(root)

    res1 = scan_repository(root, ScannerConfig())
    res2 = scan_repository(root, ScannerConfig())

    rels = [r.relative_path for r in res1.file_records]
    assert rels == sorted(rels, key=str.lower)
    assert not any(r.relative_path.startswith(".git/") for r in res1.file_records)
    assert not any(r.relative_path.startswith(".venv/") for r in res1.file_records)
    assert not any(r.relative_path.startswith("__pycache__/") for r in res1.file_records)
    assert not any(r.relative_path.startswith("AI_CORE/output/") for r in res1.file_records)
    assert res1.repository_fingerprint == res2.repository_fingerprint


def test_file_fingerprint_stability_and_change(tmp_path: Path) -> None:
    file_path = tmp_path / "x.py"
    _write(file_path, "print('a')\n")
    h1 = hash_file_content(file_path)
    h2 = hash_file_content(file_path)
    assert h1 == h2
    _write(file_path, "print('b')\n")
    h3 = hash_file_content(file_path)
    assert h1 != h3


def test_repository_fingerprint_changes_on_tree_changes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap_repo(root)
    base = scan_repository(root, ScannerConfig()).repository_fingerprint

    _write(root / "src" / "c.py", "z=3\n")
    add_fp = scan_repository(root, ScannerConfig()).repository_fingerprint
    assert add_fp != base

    (root / "src" / "c.py").unlink()
    _write(root / "src" / "a.py", "x=9\n")
    mod_fp = scan_repository(root, ScannerConfig()).repository_fingerprint
    assert mod_fp != base

    (root / "src" / "b.py").unlink()
    del_fp = scan_repository(root, ScannerConfig()).repository_fingerprint
    assert del_fp != mod_fp


def test_symlink_outside_root_is_not_followed(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    outside.mkdir(parents=True, exist_ok=True)
    _write(outside / "secret.py", "a=1\n")
    _bootstrap_repo(root)

    link = root / "src" / "external_link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink no disponible en este entorno")

    result = scan_repository(root, ScannerConfig())
    assert not any("external_link" in r.relative_path and "secret.py" in r.relative_path for r in result.file_records)
    assert any("symlink_fuera_raiz_ignorado" in w for w in result.warnings)


def test_stable_file_ids(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap_repo(root)
    result = scan_repository(root, ScannerConfig())
    rec = next(r for r in result.file_records if r.relative_path == "src/a.py")
    assert rec.id == "file:src/a.py"
