from __future__ import annotations

import json
from pathlib import Path

from CORE.orquestador import OrquestadorHostAI, SolicitudHostAI
from SERVICIOS.host_ai_engine import HostAIEngine


class _DummyMemoria:
    def registrar_respuesta_orquestador(self, intencion: str, respuesta: dict) -> None:
        _ = (intencion, respuesta)

    def limpiar_memoria(self) -> None:
        return


class _DummyDirector:
    def ejecutar_pipeline(self, pipeline: str, accion: str, params: dict):
        raise RuntimeError(f"No deberia llamarse en este smoke test: {pipeline}:{accion}")


class _DummyRegistroPipelines:
    def listar(self):
        return []


class _DummyCore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.memoria = _DummyMemoria()
        self.director = _DummyDirector()
        self.registro_pipelines = _DummyRegistroPipelines()


def test_host_ai_engine_simulado_y_logs_sanitizados(tmp_path: Path) -> None:
    engine = HostAIEngine(tmp_path)

    resultado = engine.consultar(
        origen="Eventos",
        modulo="eventos",
        tipo_peticion="responder_pregunta",
        datos_enviados={"pregunta": "Que menu recomiendas", "password": "SECRETO"},
        proveedor_preferido="SIMULADO",
        formato_entrada="texto",
    )

    assert str(resultado.get("estado") or "") == "OK_SIMULADO"
    assert str(resultado.get("proveedor") or "") == "SIMULADO"
    assert isinstance(resultado.get("respuesta"), dict)

    log_path = tmp_path / "DATOS" / "logs" / "host_ai_engine_calls.jsonl"
    assert log_path.exists()
    contenido = log_path.read_text(encoding="utf-8")
    assert "SECRETO" not in contenido
    assert "***REDACTED***" in contenido


def test_host_ai_engine_multi_provider_preparado(tmp_path: Path) -> None:
    engine = HostAIEngine(tmp_path)
    providers = engine.providers_disponibles()
    ids = {str(p.get("id") or "") for p in providers}

    assert {"SIMULADO", "OPENAI", "AZURE_OPENAI", "CLAUDE", "GEMINI", "LOCAL"}.issubset(ids)

    respuesta_nc = engine.consultar(
        origen="Compras",
        modulo="compras",
        tipo_peticion="proponer_proveedor",
        datos_enviados={"producto": "Aceite"},
        proveedor_preferido="OPENAI",
    )
    assert str(respuesta_nc.get("estado") or "") == "ERROR"
    assert "no conectado" in " ".join(respuesta_nc.get("errores") or []).lower()


def test_orquestador_exponer_host_ai_engine(tmp_path: Path) -> None:
    core = _DummyCore(tmp_path)
    orquestador = OrquestadorHostAI(core)

    health = orquestador.resolver(SolicitudHostAI("host_ai_engine_health", {})).to_dict()
    assert health["ok"] is True
    assert str((health.get("datos") or {}).get("servicio") or "") == "HOST AI ENGINE"

    consulta = orquestador.resolver(
        SolicitudHostAI(
            "host_ai_engine_consulta",
            {
                "origen": "Escandallos",
                "modulo": "escandallos",
                "tipo_peticion": "detectar_duplicados",
                "datos_enviados": {"lineas": ["A", "B"]},
                "proveedor_preferido": "SIMULADO",
                "formato_entrada": "excel",
            },
        )
    ).to_dict()

    assert consulta["ok"] is True
    motor = ((consulta.get("datos") or {}).get("host_ai_engine") or {})
    assert str(motor.get("estado") or "") == "OK_SIMULADO"
    assert str(motor.get("modulo") or "") == "escandallos"
