from pathlib import Path
import sys
from datetime import date

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    if hasattr(core, "memoria"):
        core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "compras" for p in listado.datos["pipelines"])

    n1 = core.orquestador.resolver(SolicitudHostAI("registrar_necesidad_compra", {
        "nombre": "Carrillera de ternera",
        "cantidad": 12,
        "unidad": "kg",
        "familia": "carnes",
        "proveedor_preferente": "Proveedor Carnes",
        "motivo": "Evento sábado",
        "prioridad": 95,
        "fecha_necesaria": date.today().isoformat(),
    }))
    assert n1.ok is True

    n2 = core.orquestador.resolver(SolicitudHostAI("registrar_necesidad_compra", {
        "nombre": "Vino tinto",
        "cantidad": 6,
        "unidad": "L",
        "familia": "bodega",
        "proveedor_preferente": "Proveedor Bebidas",
        "motivo": "Demi-glace",
        "prioridad": 80,
    }))
    assert n2.ok is True

    n3 = core.orquestador.resolver(SolicitudHostAI("registrar_necesidad_compra", {
        "nombre": "Huesos de ternera",
        "cantidad": 8,
        "unidad": "kg",
        "familia": "carnes",
        "proveedor_preferente": "Proveedor Carnes",
        "motivo": "Fondo oscuro",
        "prioridad": 90,
    }))
    assert n3.ok is True

    listar = core.orquestador.resolver(SolicitudHostAI("listar_necesidades_compra", {}))
    assert listar.ok is True
    assert len(listar.datos["necesidades"]) == 3
    assert listar.datos["necesidades"][0]["prioridad"] == 95

    diag = core.orquestador.resolver(SolicitudHostAI("diagnosticar_compras", {}))
    assert diag.ok is True
    assert diag.datos["urgentes"] == 2

    pedidos = core.orquestador.resolver(SolicitudHostAI("generar_pedidos_sugeridos", {}))
    assert pedidos.ok is True
    assert pedidos.requiere_aprobacion is True
    assert pedidos.datos["total_pedidos"] == 2
    assert pedidos.datos["total_necesidades"] == 3

    print("TEST OK - Host AI v1.0.2 Pipeline de Compras Inicial")
    print("Pedidos:", pedidos.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
