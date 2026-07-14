from __future__ import annotations

import json
from pathlib import Path

from AI_CORE.cli import run
from AI_CORE.repository_inventory import build_repository_inventory, write_inventory_json
from AI_CORE.repository_scanner import ScannerConfig


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bootstrap(root: Path) -> None:
    _write(root / "AGENTS.md", "# AGENTS\n")
    _write(root / "MASTER_PLAN.md", "# MASTER\n")
    _write(root / "CODEX-01.md", "# C1\n")
    _write(root / "CODEX-02.md", "# C2\n")
    _write(root / "DEVKIT" / "KNOWLEDGE_CORE" / "03_REGLAS.md", "# R\n")
    _write(root / "ROC" / "ROC-01A_NUCLEO.md", "# ROC\n")
    _write(root / "DOCS" / "ARQUITECTURA_GENERAL_HOST_AI.md", "# A\n")
    _write(root / "pkg" / "m.py", "import os\nclass A:\n    def x(self):\n        return 1\n")


def _normalized(payload: dict[str, object]) -> dict[str, object]:
    copy = json.loads(json.dumps(payload))
    copy.pop("generated_at", None)
    if isinstance(copy.get("scan"), dict):
        copy["scan"].pop("scanned_at", None)
    return copy


def test_inventory_json_and_determinism(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap(root)
    payload1 = build_repository_inventory(root, ScannerConfig())
    payload2 = build_repository_inventory(root, ScannerConfig())
    assert payload1["repository_fingerprint"] == payload2["repository_fingerprint"]
    assert _normalized(payload1) == _normalized(payload2)

    out = root / "AI_CORE" / "output" / "knowledge" / "repository_inventory.json"
    write_inventory_json(payload1, out)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["schema_version"]
    assert "metrics" in loaded
    assert not out.with_suffix(".json.tmp").exists()


def test_cli_repository_commands_and_v1_compatibility(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "repo"
    _bootstrap(root)
    monkeypatch.chdir(root)

    assert run(["repository", "scan", "--root", str(root)]) == 0
    assert run(["repository", "analyze-python", "--root", str(root)]) == 0
    assert run([
        "repository",
        "build-inventory",
        "--root",
        str(root),
        "--output",
        "AI_CORE/output/knowledge/repository_inventory.json",
        "--force",
    ]) == 0
    assert run([
        "repository",
        "summary",
        "--root",
        str(root),
        "--output",
        "AI_CORE/output/knowledge/repository_inventory.json",
    ]) == 0
    assert run(["repository", "scan", "--root", str(root / "NOPE")]) == 1

    assert run(["--domain", "general", "--output", "TEMP/ctx.md", "--manifest-output", "TEMP/mf.json"]) == 0
