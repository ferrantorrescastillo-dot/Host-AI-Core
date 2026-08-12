from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from SERVICIOS.host_ai_engine.director import DirectorIAFuncional
from SERVICIOS.host_ai_engine.models import (
    CAPACIDADES_FUTURAS_ENGINE,
    AUTONOMIA_CONSULTAR,
    ConfirmationRequest,
    ESTADO_ENGINE_ERROR,
    ESTADO_ENGINE_OK,
    ESTADO_ENGINE_OK_SIMULADO,
    HostAISolicitudOperativa,
    HostAIEngineRequest,
    HostAIEngineResponse,
)
from SERVICIOS.host_ai_engine.providers import NotConnectedProvider, SimulatedProvider
from SERVICIOS.host_ai_engine.openai_provider import OpenAIProvider


SENSITIVE_KEYS = {
    "password",
    "pass",
    "token",
    "api_key",
    "apikey",
    "secret",
    "authorization",
    "cookie",
    "set-cookie",
    "dni",
    "telefono",
    "movil",
    "email",
    "mail",
}


class HostAIEngine:
    VERSION = "6.0.0-ARCH"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.logs_dir = self.base_dir / "DATOS" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.logs_dir / "host_ai_engine_calls.jsonl"
        self.audit_path = self.logs_dir / "host_ai_engine_auditoria.jsonl"

        openai_provider = OpenAIProvider()
        self._providers = {
            "SIMULADO": SimulatedProvider(),
            "OPENAI": openai_provider if openai_provider.connected else NotConnectedProvider("OPENAI", openai_provider.model_name),
            "AZURE_OPENAI": NotConnectedProvider("AZURE_OPENAI"),
            "CLAUDE": NotConnectedProvider("CLAUDE"),
            "GEMINI": NotConnectedProvider("GEMINI"),
            "LOCAL": NotConnectedProvider("LOCAL"),
        }
        configured_default = str(os.getenv("HOST_AI_AI_PROVIDER") or "SIMULADO").strip().upper()
        self.default_provider = configured_default if configured_default in self._providers else "SIMULADO"
        self.director = DirectorIAFuncional(self.base_dir)

    def providers_disponibles(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for key, provider in self._providers.items():
            conectado = bool(provider.connected)
            out.append(
                {
                    "id": key,
                    "provider": provider.provider_name,
                    "modelo": provider.model_name,
                    "estado": "conectado" if conectado else "no_conectado",
                }
            )
        return out

    def capacidades_futuras(self) -> dict[str, str]:
        return dict(CAPACIDADES_FUTURAS_ENGINE)

    def healthcheck(self) -> dict[str, Any]:
        return {
            "ok": True,
            "servicio": "HOST AI ENGINE",
            "version": self.VERSION,
            "provider_por_defecto": self.default_provider,
            "providers": self.providers_disponibles(),
            "director_ia": "activo",
        }

    def crear_solicitud_operativa(
        self,
        *,
        usuario: str,
        origen: str,
        modulo_origen: str,
        texto_original: str,
        intencion: str,
        nivel_de_autonomia: str = AUTONOMIA_CONSULTAR,
        datos_de_entrada: dict[str, Any] | None = None,
        contexto: dict[str, Any] | None = None,
        proveedor_preferido: str = "SIMULADO",
        formato_entrada: str = "texto",
        confirmaciones_recibidas: list[Any] | None = None,
        version_del_contrato: str = "1.0",
    ) -> HostAISolicitudOperativa:
        confirmaciones_norm: list[ConfirmationRequest] = []
        for item in list(confirmaciones_recibidas or []):
            if isinstance(item, ConfirmationRequest):
                confirmaciones_norm.append(item)
                continue
            if isinstance(item, dict):
                confirmaciones_norm.append(
                    ConfirmationRequest(
                        id_confirmacion=str(item.get("id_confirmacion") or ""),
                        id_solicitud=str(item.get("id_solicitud") or ""),
                        acciones_incluidas=list(item.get("acciones_incluidas") or []),
                        resumen_visible=str(item.get("resumen_visible") or ""),
                        impacto=str(item.get("impacto") or ""),
                        riesgos=list(item.get("riesgos") or []),
                        fecha_solicitud=str(item.get("fecha_solicitud") or ""),
                        estado=str(item.get("estado") or "PENDIENTE"),
                        usuario_que_responde=str(item.get("usuario_que_responde") or ""),
                        fecha_respuesta=str(item.get("fecha_respuesta") or ""),
                        alcance_autorizado=dict(item.get("alcance_autorizado") or {}),
                        caducidad_opcional=str(item.get("caducidad_opcional") or ""),
                        plan_hash=str(item.get("plan_hash") or ""),
                    )
                )
        return HostAISolicitudOperativa(
            usuario=str(usuario or "sistema"),
            origen=str(origen or "HOST_AI"),
            modulo_origen=str(modulo_origen or "general"),
            texto_original=str(texto_original or ""),
            intencion=str(intencion or "consulta_simple"),
            nivel_de_autonomia=str(nivel_de_autonomia or AUTONOMIA_CONSULTAR),
            datos_de_entrada=dict(datos_de_entrada or {}),
            contexto=dict(contexto or {}),
            proveedor_preferido=str(proveedor_preferido or "SIMULADO"),
            formato_entrada=str(formato_entrada or "texto"),
            confirmaciones_recibidas=confirmaciones_norm,
            version_del_contrato=str(version_del_contrato or "1.0"),
        )

    def crear_consulta(
        self,
        *,
        origen: str,
        modulo: str,
        tipo_peticion: str,
        datos_enviados: dict[str, Any] | None = None,
        proveedor_preferido: str = "SIMULADO",
        formato_entrada: str = "texto",
    ) -> HostAIEngineRequest:
        return HostAIEngineRequest(
            origen=str(origen or ""),
            modulo=str(modulo or ""),
            tipo_peticion=str(tipo_peticion or ""),
            datos_enviados=dict(datos_enviados or {}),
            proveedor_preferido=str(proveedor_preferido or "SIMULADO").upper(),
            formato_entrada=str(formato_entrada or "texto"),
        )

    def ejecutar(self, request: HostAIEngineRequest) -> HostAIEngineResponse:
        inicio = time.perf_counter()
        provider_key = str(request.proveedor_preferido or "SIMULADO").upper()
        provider = self._providers.get(provider_key) or self._providers["SIMULADO"]
        provider_result = provider.ejecutar(request)
        elapsed_ms = int((time.perf_counter() - inicio) * 1000)

        estado = ESTADO_ENGINE_OK
        if provider.provider_name == "SIMULADO":
            estado = ESTADO_ENGINE_OK_SIMULADO
        if not provider_result.ok:
            estado = ESTADO_ENGINE_ERROR

        response = HostAIEngineResponse(
            request_id=request.request_id,
            origen=request.origen,
            modulo=request.modulo,
            tipo_peticion=request.tipo_peticion,
            respuesta=provider_result.salida,
            estado=estado,
            errores=list(provider_result.errores or []),
            tiempo_ms=elapsed_ms,
            proveedor=provider_result.proveedor,
            modelo=provider_result.modelo,
        )
        self._registrar_llamada(request, response)
        return response

    def consultar(
        self,
        *,
        origen: str,
        modulo: str,
        tipo_peticion: str,
        datos_enviados: dict[str, Any] | None = None,
        proveedor_preferido: str = "SIMULADO",
        formato_entrada: str = "texto",
        usar_director: bool = False,
        usuario: str = "sistema",
        texto_original: str = "",
        nivel_de_autonomia: str = AUTONOMIA_CONSULTAR,
        contexto: dict[str, Any] | None = None,
        confirmaciones_recibidas: list[Any] | None = None,
        version_del_contrato: str = "1.0",
    ) -> dict[str, Any]:
        if usar_director:
            solicitud = self.crear_solicitud_operativa(
                usuario=usuario,
                origen=origen,
                modulo_origen=modulo,
                texto_original=texto_original,
                intencion=tipo_peticion,
                nivel_de_autonomia=nivel_de_autonomia,
                datos_de_entrada=datos_enviados,
                contexto=contexto,
                proveedor_preferido=proveedor_preferido,
                formato_entrada=formato_entrada,
                confirmaciones_recibidas=confirmaciones_recibidas,
                version_del_contrato=version_del_contrato,
            )
            resultado = self.director.procesar(solicitud)
            self._registrar_auditoria(resultado)
            return resultado

        request = self.crear_consulta(
            origen=origen,
            modulo=modulo,
            tipo_peticion=tipo_peticion,
            datos_enviados=datos_enviados,
            proveedor_preferido=proveedor_preferido,
            formato_entrada=formato_entrada,
        )
        return self.ejecutar(request).to_dict()

    def _sanear(self, value: Any) -> Any:
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for k, v in value.items():
                key_norm = str(k or "").strip().lower()
                if (
                    key_norm in SENSITIVE_KEYS
                    or "api_key" in key_norm
                    or "token" in key_norm
                    or "secret" in key_norm
                    or "password" in key_norm
                ):
                    out[k] = "***REDACTED***"
                else:
                    out[k] = self._sanear(v)
            return out
        if isinstance(value, list):
            return [self._sanear(v) for v in value]
        if isinstance(value, str):
            sanitized = value
            openai_key = str(os.getenv("OPENAI_API_KEY") or "").strip()
            if openai_key:
                sanitized = sanitized.replace(openai_key, "***REDACTED***")
            if len(sanitized) > 500:
                return sanitized[:500] + "..."
            return sanitized
        return value

    def _append_jsonl(self, payload: dict[str, Any]) -> None:
        line = json.dumps(payload, ensure_ascii=False)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.logs_dir, suffix=".tmp") as tmp:
            if self.log_path.exists():
                tmp.write(self.log_path.read_text(encoding="utf-8"))
            tmp.write(line + "\n")
            tmp.flush()
            temp_path = Path(tmp.name)
        temp_path.replace(self.log_path)

    def _registrar_llamada(self, request: HostAIEngineRequest, response: HostAIEngineResponse) -> None:
        payload = {
            "registrado_en": datetime.now().isoformat(timespec="seconds"),
            "request": self._sanear(request.to_dict()),
            "response": self._sanear(response.to_dict()),
        }
        self._append_jsonl(payload)

    def _registrar_auditoria(self, payload: dict[str, Any]) -> None:
        line = json.dumps(self._sanear(payload), ensure_ascii=False)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.logs_dir, suffix=".tmp") as tmp:
            if self.audit_path.exists():
                tmp.write(self.audit_path.read_text(encoding="utf-8"))
            tmp.write(line + "\n")
            tmp.flush()
            temp_path = Path(tmp.name)
        temp_path.replace(self.audit_path)
