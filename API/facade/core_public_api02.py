from __future__ import annotations

from pathlib import Path
from typing import Any

from CORE.host_ai_core import HostAICore
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_executive import HostAIExecutive
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService

from API.facade.core_public_stub import CorePublicStubFacade


class CorePublicApi02Facade:
    """Fachada API-02.

    Implementa el primer endpoint real de plataforma reutilizando HostAIExecutive.
    El resto de endpoints permanece en modo stub hasta iteraciones siguientes.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self._stub = CorePublicStubFacade()
        self._executive = HostAIExecutive(self.base_dir)
        self._chat_service: ServicioChatHostAIShell | None = None

    @staticmethod
    def _error_payload() -> dict[str, Any]:
        return {
            "ok": False,
            "version": "1.0",
            "modo_seguro": True,
            "datos_reales_modificados": False,
            "error": {
                "code": "executive_unavailable",
                "message": "No se pudo completar la consulta Executive en este momento.",
            },
        }

    def health(self) -> dict[str, Any]:
        data = dict(self._stub.health() or {})
        return {
            "ok": bool(data.get("ok", True)),
            "version": "1.0",
            "modo_seguro": True,
            "datos_reales_modificados": False,
            "health": data,
        }

    def version(self) -> dict[str, Any]:
        data = dict(self._stub.version() or {})
        return {
            "ok": bool(data.get("ok", True)),
            "version": "1.0",
            "modo_seguro": True,
            "datos_reales_modificados": False,
            "version_info": data,
        }

    def executive(self, query: dict[str, Any]) -> dict[str, Any]:
        q = dict(query or {})
        modo = str(q.get("modo") or "restaurante").strip().lower()
        try:
            if modo == "evento":
                evento = dict(q.get("evento") or {})
                resultado = self._executive.analizar_evento(evento)
            else:
                resultado = self._executive.analizar_restaurante(core=None)

            return {
                "ok": bool(resultado.get("ok", True)),
                "version": "1.0",
                "modo_seguro": True,
                "datos_reales_modificados": False,
                "executive": resultado,
            }
        except Exception:
            return self._error_payload()

    def dashboard(self, query: dict[str, Any]) -> dict[str, Any]:
        q = dict(query or {})
        try:
            executive_payload = self.executive(q)
            if not bool(executive_payload.get("ok")):
                return {
                    "ok": False,
                    "version": "1.0",
                    "modo_seguro": True,
                    "datos_reales_modificados": False,
                    "error": {
                        "code": "dashboard_unavailable",
                        "message": "No se pudo construir el dashboard en este momento.",
                    },
                }

            executive_result = dict(executive_payload.get("executive") or {})
            evento_activo = dict((executive_result.get("evento") or {}))
            if not evento_activo:
                evento_activo = dict((executive_result.get("resumen_restaurante") or {}).get("eventos") or {})

            payload = {
                "ok": True,
                "version": "1.0",
                "modo_seguro": True,
                "datos_reales_modificados": False,
                "dashboard": {
                    "estado_general": executive_result.get("estado_general") or executive_result.get("estado") or "sin_datos",
                    "prioridad": executive_result.get("prioridad_inmediata") or (executive_result.get("resumen_restaurante") or {}).get("prioridad_dia") or {},
                    "pendientes": executive_result.get("pendientes") or executive_result.get("pendientes_operativos") or [],
                    "riesgos": executive_result.get("riesgos") or executive_result.get("riesgos_operativos") or [],
                    "recomendaciones": executive_result.get("recomendaciones") or executive_result.get("recomendaciones_operativas") or [],
                    "evento_activo": evento_activo,
                    "workflows": executive_result.get("workflows_priorizados") or executive_result.get("workflows_ejecutados") or [],
                },
            }
            return payload
        except Exception:
            return {
                "ok": False,
                "version": "1.0",
                "modo_seguro": True,
                "datos_reales_modificados": False,
                "error": {
                    "code": "dashboard_unavailable",
                    "message": "No se pudo construir el dashboard en este momento.",
                },
            }

    def eventos(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._stub.eventos(query)

    def workflow(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._stub.workflow(query)

    def plan(self, query: dict[str, Any]) -> dict[str, Any]:
        return self._stub.plan(query)

    def _build_chat_service(self) -> ServicioChatHostAIShell:
        core = HostAICore(self.base_dir)
        home_read = HostAIHomeReadService(core)
        return ServicioChatHostAIShell(core.orquestador, home_read_service=home_read)

    def _get_chat_service(self) -> ServicioChatHostAIShell:
        if self._chat_service is None:
            self._chat_service = self._build_chat_service()
        return self._chat_service

    def chat(self, body: dict[str, Any]) -> dict[str, Any]:
        b = dict(body or {})
        mensaje = str(b.get("mensaje") or "")
        contexto = dict(b.get("contexto") or {})
        try:
            service = self._get_chat_service()
            resultado = service.enviar(mensaje, contexto=contexto)
            payload = {
                "ok": bool(resultado.get("ok", True)),
                "version": "1.0",
                "respuesta": str(resultado.get("mensaje") or ""),
                "modo_seguro": True,
                "datos_reales_modificados": False,
                "chat": resultado,
                "contexto": service.estado_sesion(),
            }
            return payload
        except Exception:
            return {
                "ok": False,
                "version": "1.0",
                "respuesta": "No se pudo procesar la consulta en este momento.",
                "modo_seguro": True,
                "datos_reales_modificados": False,
                "error": {
                    "code": "chat_unavailable",
                    "message": "No se pudo procesar la consulta en este momento.",
                },
            }
