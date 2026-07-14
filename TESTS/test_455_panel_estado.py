from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.panel_estado_455 import PanelEstadoHostAI455


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        for carpeta in ["APP", "SERVICIOS", "TESTS", "DOCS", "DATOS/db"]:
            (base / carpeta).mkdir(parents=True, exist_ok=True)
        (base / "APP" / "demo.py").write_text("print('ok')", encoding="utf-8")
        (base / "SERVICIOS" / "demo.py").write_text("print('ok')", encoding="utf-8")
        (base / "TESTS" / "test_demo.py").write_text("print('ok')", encoding="utf-8")

        estado = PanelEstadoHostAI455(base).generar_estado()
        assert estado["ok"] is True
        assert estado["conteos"]["apps"] == 1
        assert estado["conteos"]["servicios"] == 1
        assert estado["conteos"]["tests"] == 1
        assert "lectura_host_ai" in estado

    print("TEST OK 4.5.5 - Panel de estado")


if __name__ == "__main__":
    main()
