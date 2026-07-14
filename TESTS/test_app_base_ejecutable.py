from pathlib import Path
import sys
import subprocess

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from APP.consola import AppConsolaHostAI


def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    app = AppConsolaHostAI(core)

    assert app.core is core
    assert hasattr(core, "orquestador")
    assert hasattr(core, "asistente_conversacional")

    pipelines = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert pipelines.ok is True

    nombres = [p["nombre"] for p in pipelines.datos["pipelines"]]
    for obligatorio in ["evento", "stock", "compras", "escandallos", "costes", "produccion_real", "ia_culinaria", "asistente"]:
        assert obligatorio in nombres

    chat = core.orquestador.resolver(SolicitudHostAI("chat_host_ai", {
        "texto": "Tengo una boda de 50 pax",
        "contexto": {"fecha": "2026-07-07"}
    }))
    assert chat.ok is True
    assert "He creado el evento" in chat.mensaje

    demo = subprocess.run(
        [sys.executable, str(BASE_DIR / "demo_host_ai_3.py")],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    assert demo.returncode == 0
    assert "HOST AI 3.0 DEMO" in demo.stdout
    assert "Pipelines registrados" in demo.stdout

    print("TEST OK - Host AI 3.0.0 App Base Ejecutable")
    print("Pipelines:", nombres)
    print("Demo stdout:", demo.stdout)


if __name__ == "__main__":
    ejecutar_prueba()
