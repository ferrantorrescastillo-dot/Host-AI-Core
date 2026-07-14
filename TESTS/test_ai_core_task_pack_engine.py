from __future__ import annotations

import json
from pathlib import Path

from AI_CORE.cli import run
from AI_CORE.task_pack_engine import build_task_context_package, infer_domain


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bootstrap_repo(root: Path) -> None:
    _write(root / "AGENTS.md", "# AGENTS\n")
    _write(root / "MASTER_PLAN.md", "# MASTER\n")
    _write(root / "CODEX-01.md", "# C1\n")
    _write(root / "CODEX-02.md", "# C2\n")
    _write(root / "DEVKIT" / "KNOWLEDGE_CORE" / "03_REGLAS.md", "# Reglas\n")
    _write(root / "ROC" / "ROC-02A_OPERACION.md", "# Operacion\n")
    _write(root / "DOCS" / "PRODUCCION_GUIA.md", "# Produccion\n")
    _write(root / "SERVICIOS" / "motor_produccion.py", "class MotorProduccion:\n    def ejecutar(self):\n        return True\n")
    _write(root / "MOTORES" / "stock_core.py", "def resolver_stock():\n    return 1\n")
    _write(root / "TESTS" / "test_motor_produccion.py", "def test_ok():\n    assert True\n")
    _write(root / "DATOS" / "db" / "no_tocar.json", "{}\n")


def test_infer_domain() -> None:
    assert infer_domain("Mejorar Producción") == "produccion"
    assert infer_domain("Modificar Compras") == "compras"
    assert infer_domain("Resolver Stock") == "stock"


def test_task_pack_generation_complete(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _bootstrap_repo(root)

    result = build_task_context_package("Mejorar Producción", project_root=root)
    out = result.output_dir

    assert (out / "CONTEXT.md").is_file()
    assert (out / "DOCUMENTS.md").is_file()
    assert (out / "CODE_FILES.json").is_file()
    assert (out / "SYMBOLS.json").is_file()
    assert (out / "TESTS.json").is_file()
    assert (out / "CHECKLIST.md").is_file()
    assert (out / "COPILOT_PROMPT.md").is_file()

    docs_text = (out / "DOCUMENTS.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in docs_text
    assert "MASTER_PLAN.md" in docs_text

    code_files = json.loads((out / "CODE_FILES.json").read_text(encoding="utf-8"))
    assert any("motor_produccion.py" in f["path"] for f in code_files["files"])

    symbols = json.loads((out / "SYMBOLS.json").read_text(encoding="utf-8"))
    all_symbols = symbols["classes"] + symbols["functions"] + symbols["methods"]
    assert len(all_symbols) > 0

    tests_payload = json.loads((out / "TESTS.json").read_text(encoding="utf-8"))
    assert any("test_motor_produccion.py" in t["path"] for t in tests_payload["tests"])

    checklist = (out / "CHECKLIST.md").read_text(encoding="utf-8")
    assert "No modificar DATOS" in checklist

    prompt = (out / "COPILOT_PROMPT.md").read_text(encoding="utf-8")
    assert "Objetivo: Mejorar Producción" in prompt
    assert len(prompt) < 12000


def test_cli_task_context(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "repo"
    _bootstrap_repo(root)
    monkeypatch.chdir(root)

    code = run(["task-context", "Resolver Stock", "--root", str(root), "--output-base", "AI_CORE/output/tasks"])
    assert code == 0
    out = root / "AI_CORE" / "output" / "tasks" / "resolver_stock"
    assert out.is_dir()
    assert (out / "COPILOT_PROMPT.md").is_file()
