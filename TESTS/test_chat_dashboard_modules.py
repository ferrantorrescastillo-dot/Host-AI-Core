from pathlib import Path

from CORE.host_ai_core import HostAICore
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell


class HomeFixture:
    def cargar_home(self):
        return {
            "modulos": {
                "compras": {
                    "necesidades_pendientes": 1,
                    "propuestas_pendientes": 2,
                    "items": [{"nombre": "Tomate"}],
                    "propuestas": [{"producto": "Aceite"}],
                    "proveedores": [{"nombre": "Proveedor Uno"}],
                },
                "eventos": {
                    "items": [{"nombre": "Boda Norte", "riesgos": ["Lluvia"]}],
                    "resumen": {"pax_total": 90},
                },
                "produccion": {
                    "items": [{"nombre": "Banquete"}],
                    "tareas_en_curso": 2,
                },
                "stock": {
                    "alertas": [{"mensaje": "Tomate bajo mínimo"}],
                },
            }
        }


def _chat(tmp_path: Path) -> ServicioChatHostAIShell:
    core = HostAICore(tmp_path)
    service = ServicioChatHostAIShell(
        core.orquestador,
        home_read_service=HomeFixture(),
    )
    service._consultar_engine_simulado = lambda *_args, **_kwargs: {
        "estado": "OK",
        "proveedor": "SIMULADO",
        "respuesta": {},
        "errores": [],
    }
    return service


def test_chat_consulta_los_mismos_modulos_del_dashboard_sin_escribir(tmp_path: Path):
    service = _chat(tmp_path)

    compras = service.enviar("¿Qué compras tengo pendientes?")
    proveedores = service.enviar("¿Qué proveedores están activos?")
    eventos = service.enviar("¿Qué eventos tengo próximos?")
    produccion = service.enviar("¿Qué producción está en curso?")
    stock = service.enviar("¿Qué productos tienen stock crítico?")
    estado = service.enviar("¿Cuál es el estado general de la operación?")

    assert "1 necesidades y 2 propuestas" in compras["mensaje"]
    assert "Proveedor Uno" in proveedores["mensaje"]
    assert "Boda Norte" in eventos["mensaje"]
    assert "Banquete" in produccion["mensaje"]
    assert "Tomate bajo mínimo" in stock["mensaje"]
    assert "3 compras pendientes" in estado["mensaje"]
    assert compras["datos"]["informativa"] is True
    assert compras["datos"]["modo_lectura"] is True
    assert compras["datos"]["navigation_request"]["target_module"] == "COMPRAS"


def test_chat_responde_sin_datos_y_mantiene_modo_lectura(tmp_path: Path):
    service = _chat(tmp_path)
    service.home_read_service = type(
        "EmptyHome",
        (),
        {"cargar_home": lambda self: {"modulos": {}}},
    )()

    result = service.enviar("¿Qué eventos tengo próximos?")

    assert result["ok"] is True
    assert "Hay 0 eventos próximos" in result["mensaje"]
    assert result["datos"]["modo_lectura"] is True
