from pathlib import Path
import sys, shutil

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    db_dir = BASE_DIR / "DATOS" / "db"
    if db_dir.exists():
        shutil.rmtree(db_dir)

    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "persistencia" for p in listado.datos["pipelines"])

    crear = core.orquestador.resolver(SolicitudHostAI("chat_host_ai", {
        "texto": "Tengo una boda de 60 pax",
        "contexto": {"fecha": "2026-07-08"},
    }))
    assert crear.ok is True

    stock = core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {
        "nombre": "Carrillera de ternera",
        "cantidad": 5,
        "unidad": "kg",
        "familia": "carnes",
        "articulo_id": "ART-CARRILLERA",
    }))
    assert stock.ok is True

    compra = core.orquestador.resolver(SolicitudHostAI("registrar_necesidad_compra", {
        "nombre": "Vino tinto",
        "cantidad": 6,
        "unidad": "L",
        "proveedor_preferente": "Proveedor Bebidas",
    }))
    assert compra.ok is True

    guardar = core.orquestador.resolver(SolicitudHostAI("guardar_todo_db", {}))
    assert guardar.ok is True

    resumen = core.orquestador.resolver(SolicitudHostAI("resumen_db", {}))
    assert resumen.ok is True
    col = {c["coleccion"]: c["total"] for c in resumen.datos["colecciones"]}
    assert col["eventos"] >= 1
    assert col["stock_lotes"] >= 1
    assert col["compras_necesidades"] >= 1

    snap = core.orquestador.resolver(SolicitudHostAI("snapshot_db", {"nombre": "test_snapshot"}))
    assert snap.ok is True
    assert (db_dir / "snapshots" / "test_snapshot.json").exists()

    print("TEST OK - Host AI 3.0.1 Base de Datos Local")
    print("Resumen:", resumen.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
