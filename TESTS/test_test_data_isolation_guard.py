from __future__ import annotations

from pathlib import Path

import pytest

from TESTS.conftest import REAL_DATOS_ROOT


def test_pytest_bloquea_escritura_directa_en_datos_real() -> None:
    target = REAL_DATOS_ROOT / "logs" / "esto_no_debe_crearse.jsonl"

    with pytest.raises(AssertionError, match="TEST_DATA_ISOLATION_GUARD"):
        target.write_text("prohibido", encoding="utf-8")

    assert not target.exists()


def test_pytest_permite_escritura_en_raiz_aislada(tmp_path: Path) -> None:
    target = tmp_path / "DATOS" / "logs" / "aislado.jsonl"
    target.parent.mkdir(parents=True)
    target.write_text("ok", encoding="utf-8")

    assert target.read_text(encoding="utf-8") == "ok"
