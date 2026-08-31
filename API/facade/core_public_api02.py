from __future__ import annotations

from pathlib import Path
from typing import Any
import inspect
import re

from CORE.host_ai_core import HostAICore
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_executive import HostAIExecutive
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService
from SERVICIOS.reservas_read_service import ReservasReadService
from SERVICIOS.reservas_write_service import ReservasWriteService, ErrorReservasWrite
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext

from API.facade.core_public_stub import CorePublicStubFacade


class CorePublicApi02Facade:
    """Fachada pública API-02.

    La API solo accede al Core mediante servicios públicos certificados.

    Responsabilidades:
    - Health y version mediante la fachada stub certificada.
    - Executive mediante HostAIExecutive.
    - Dashboard mediante Executive + HostAIHomeReadService.
    - Chat mediante ServicioChatHostAIShell.
    - Resto de endpoints en modo stub hasta próximas iteraciones.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = Path(base_dir or Path.cwd()).resolve()

        self._stub = CorePublicStubFacade()
        self._executive = HostAIExecutive(self.base_dir)

        self._core: HostAICore | None = None
        self._home_read_service: HostAIHomeReadService | None = None
        self._chat_service: ServicioChatHostAIShell | None = None
        self._chat_services_by_session: dict[str, ServicioChatHostAIShell] = {}
        self._reservas_write_service: ReservasWriteService | None = None

    _SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")

    @staticmethod
    def _base_payload() -> dict[str, Any]:
        return {
            "version": "1.0",
            "modo_seguro": True,
            "datos_reales_modificados": False,
        }

    @classmethod
    def _error_payload(
        cls,
        *,
        code: str,
        message: str,
    ) -> dict[str, Any]:
        return {
            "ok": False,
            **cls._base_payload(),
            "error": {
                "code": code,
                "message": message,
            },
        }

    def _get_core(self) -> HostAICore:
        if self._core is None:
            self._core = HostAICore(self.base_dir)

        return self._core

    def _get_home_read_service(self) -> HostAIHomeReadService:
        if self._home_read_service is None:
            self._home_read_service = HostAIHomeReadService(
                self._get_core(),
            )

        return self._home_read_service


    def health(self) -> dict[str, Any]:
        data = dict(self._stub.health() or {})

        return {
            "ok": bool(data.get("ok", True)),
            **self._base_payload(),
            "health": data,
        }

    def version(self) -> dict[str, Any]:
        data = dict(self._stub.version() or {})

        return {
            "ok": bool(data.get("ok", True)),
            **self._base_payload(),
            "version_info": data,
        }

    def executive(
        self,
        query: dict[str, Any],
    ) -> dict[str, Any]:
        q = dict(query or {})
        modo = str(
            q.get("modo") or "restaurante",
        ).strip().lower()

        try:
            if modo == "evento":
                evento = dict(q.get("evento") or {})
                resultado = self._executive.analizar_evento(
                    evento,
                )
            else:
                resultado = self._executive.analizar_restaurante(
                    core=None,
                )

            return {
                "ok": bool(resultado.get("ok", True)),
                **self._base_payload(),
                "datos_reales_modificados": bool((resultado.get("datos") or {}).get("datos_reales_modificados", False)),
                "executive": resultado,
            }

        except Exception:
            return self._error_payload(
                code="executive_unavailable",
                message=(
                    "No se pudo completar la consulta "
                    "Executive en este momento."
                ),
            )

    def dashboard(
        self,
        query: dict[str, Any],
    ) -> dict[str, Any]:
        q = dict(query or {})

        try:
            executive_payload = self.executive(q)
            executive_ok = bool(
                executive_payload.get("ok"),
            )

            executive_result = dict(
                executive_payload.get("executive") or {},
            )

            home_service = self._get_home_read_service()
            home_result = dict(
                home_service.cargar_home() or {},
            )

            modulos = dict(
                home_result.get("modulos") or {},
            )
            indicadores = list(
                home_result.get("indicadores") or [],
            )
            bandeja = list(
                home_result.get("bandeja") or [],
            )
            errores_home = list(
                home_result.get("errores") or [],
            )

            evento_activo = self._resolve_evento_activo(
                executive_result=executive_result,
                modulos=modulos,
            )

            prioridad = self._resolve_prioridad(
                executive_result=executive_result,
                bandeja=bandeja,
            )

            pendientes = self._resolve_pendientes(
                executive_result=executive_result,
                bandeja=bandeja,
                modulos=modulos,
            )

            riesgos = self._resolve_riesgos(
                executive_result=executive_result,
                modulos=modulos,
                bandeja=bandeja,
            )

            recomendaciones = self._resolve_recomendaciones(
                executive_result=executive_result,
                bandeja=bandeja,
            )

            workflows = list(
                executive_result.get(
                    "workflows_priorizados",
                )
                or executive_result.get(
                    "workflows_ejecutados",
                )
                or []
            )

            estado_general = (
                executive_result.get("estado_general")
                or executive_result.get("estado")
                or home_result.get("estado_global")
                or "sin_datos"
            )

            return {
                "ok": executive_ok or bool(home_result),
                **self._base_payload(),
                "dashboard": {
                    "estado_general": estado_general,
                    "actualizado_en": home_result.get(
                        "generado_en",
                    ),
                    "prioridad": prioridad,
                    "pendientes": pendientes,
                    "riesgos": riesgos,
                    "recomendaciones": recomendaciones,
                    "evento_activo": evento_activo,
                    "workflows": workflows,
                    "indicadores": indicadores,
                    "bandeja": bandeja,
                    "modulos": modulos,
                    "errores": errores_home,
                },
                "home": home_result,
            }

        except Exception:
            return self._error_payload(
                code="dashboard_unavailable",
                message=(
                    "No se pudo construir el dashboard "
                    "en este momento."
                ),
            )

    def eventos(
        self,
        query: dict[str, Any],
    ) -> dict[str, Any]:
        return self._stub.eventos(query)

    def reservas(self, query: dict[str, Any]) -> dict[str, Any]:
        q = dict(query or {})
        try:
            alcance = str(q.pop("alcance", "todas") or "todas").strip().lower()
            nombre = str(q.pop("q", "") or "")
            filtros = {
                "fecha": str(q.pop("fecha", "") or ""),
                "estado": str(q.pop("estado", "") or ""),
                "servicio": str(q.pop("servicio", "") or ""),
                "nombre": nombre,
                "limite": int(q.pop("limite", 50) or 50),
            }
            if q or alcance not in {"todas", "hoy", "proximas"}:
                raise ValueError("filtros de reservas no validos")
            service = ReservasReadService(self.base_dir)
            if alcance == "hoy":
                filtros.pop("fecha")
                items = service.hoy(**filtros)
            elif alcance == "proximas":
                filtros.pop("fecha")
                items = service.proximas(**filtros)
            else:
                items = service.listar(**filtros)
            return {"ok": True, **self._base_payload(), "reservas": {"items": items, "total": len(items)}}
        except (TypeError, ValueError):
            return {**self._error_payload(code="invalid_reservas_query", message="Los filtros de Reservas no son validos."), "error": {"status": 400, "code": "invalid_reservas_query", "message": "Los filtros de Reservas no son validos."}}

    def reserva(self, reserva_id: str) -> dict[str, Any]:
        item = ReservasReadService(self.base_dir).detalle(reserva_id)
        if item is None:
            return {**self._error_payload(code="reserva_not_found", message="Reserva no encontrada."), "error": {"status": 404, "code": "reserva_not_found", "message": "Reserva no encontrada."}}
        return {"ok": True, **self._base_payload(), "reserva": item}

    def _get_reservas_write_service(self) -> ReservasWriteService:
        if self._reservas_write_service is None:
            self._reservas_write_service = ReservasWriteService(self.base_dir)
        return self._reservas_write_service

    def previsualizar_reserva(self, body: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        payload = dict(body or {})
        allowed = {"operacion", "reserva_id", "payload", "session_id"}
        if set(payload) - allowed or not isinstance(payload.get("payload", {}), dict):
            return {**self._error_payload(code="invalid_reserva_write_body", message="Solicitud de preview no valida."), "error": {"status": 422, "code": "invalid_reserva_write_body", "message": "Solicitud de preview no valida."}}
        return self._reservas_write_call(
            self._get_reservas_write_service().preview, context,
            operacion=str(payload.get("operacion") or ""), payload=dict(payload.get("payload") or {}),
            reserva_id=str(payload.get("reserva_id") or ""), session_id=str(payload.get("session_id") or ""),
        )

    def confirmar_operacion_reserva(self, body: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        payload = dict(body or {})
        if set(payload) - {"preview_token", "session_id"}:
            return {**self._error_payload(code="invalid_reserva_confirmation_body", message="Confirmacion no valida."), "error": {"status": 422, "code": "invalid_reserva_confirmation_body", "message": "Confirmacion no valida."}}
        return self._reservas_write_call(
            self._get_reservas_write_service().confirm, context,
            preview_token=str(payload.get("preview_token") or ""), session_id=str(payload.get("session_id") or ""),
        )

    def _reservas_write_call(self, operation: Any, context: AuthorizedExecutionContext, **kwargs: Any) -> dict[str, Any]:
        try:
            return {**self._base_payload(), **operation(context=context, **kwargs)}
        except ErrorReservasWrite as exc:
            status = 403 if exc.code == "unauthorized" else 404 if exc.code == "reserva_not_found" else 409 if exc.code in {"invalid_preview", "expired_preview", "stale_preview"} else 422
            return {**self._error_payload(code=exc.code, message=str(exc)), "error": {"status": status, "code": exc.code, "message": str(exc)}}

    def workflow(
        self,
        query: dict[str, Any],
    ) -> dict[str, Any]:
        return self._stub.workflow(query)

    def plan(
        self,
        query: dict[str, Any],
    ) -> dict[str, Any]:
        return self._stub.plan(query)

    def _build_chat_service(
        self, session_id: str = "default",
    ) -> ServicioChatHostAIShell:
        return ServicioChatHostAIShell(
            self._get_core().orquestador,
            home_read_service=self._get_home_read_service(),
            session_id=session_id,
        )

    def _get_chat_service(
        self,
        session_id: str = "default",
    ) -> ServicioChatHostAIShell:
        sid = str(session_id or "default")
        if sid == "default":
            if self._chat_service is None:
                self._chat_service = self._create_chat_service("default")
            return self._chat_service
        service = self._chat_services_by_session.get(sid)
        if service is None:
            service = self._create_chat_service(sid)
            self._chat_services_by_session[sid] = service
        return service

    def _create_chat_service(self, session_id: str) -> ServicioChatHostAIShell:
        """Conserva factories legacy inyectados sin perder aislamiento nativo."""
        builder = self._build_chat_service
        if "session_id" in inspect.signature(builder).parameters:
            return builder(session_id)
        return builder()

    @classmethod
    def _resolve_session_id(cls, body: dict[str, Any], contexto: dict[str, Any]) -> str:
        raw = str(body.get("session_id") or contexto.get("session_id") or "").strip()
        if not raw:
            return "default"
        return raw if cls._SESSION_ID_PATTERN.fullmatch(raw) else "default"

    def chat(
        self,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        b = dict(body or {})
        mensaje = str(b.get("mensaje") or "")
        action_id = str(b.get("action_id") or "")
        action_context_id = str(b.get("action_context_id") or "")
        contexto = dict(b.get("contexto") or {})
        session_id = self._resolve_session_id(b, contexto)

        try:
            service = self._get_chat_service(session_id)
            resultado = service.ejecutar_accion_reserva(action_id, action_context_id=action_context_id, contexto=contexto) if action_id else service.enviar(mensaje, contexto=contexto)

            return {
                "ok": bool(resultado.get("ok", True)),
                **self._base_payload(),
                "respuesta": str(
                    resultado.get("mensaje") or "",
                ),
                "chat": resultado,
                "contexto": service.estado_sesion(),
                "session_id": session_id,
            }

        except Exception:
            return {
                **self._error_payload(
                    code="chat_unavailable",
                    message=(
                        "No se pudo procesar la consulta "
                        "en este momento."
                    ),
                ),
                "respuesta": (
                    "No se pudo procesar la consulta "
                    "en este momento."
                ),
            }

    @staticmethod
    def _resolve_evento_activo(
        *,
        executive_result: dict[str, Any],
        modulos: dict[str, Any],
    ) -> dict[str, Any]:
        evento_resumen = dict(
            executive_result.get("evento") or {},
        )

        resumen_restaurante = dict(
            executive_result.get("resumen_restaurante") or {},
        )

        if not evento_resumen:
            eventos_resumen = resumen_restaurante.get("eventos")

            if isinstance(eventos_resumen, dict):
                evento_resumen = dict(eventos_resumen)

        modulo_eventos = dict(
            modulos.get("eventos") or {},
        )

        items = [
            dict(item)
            for item in list(modulo_eventos.get("items") or [])
            if isinstance(item, dict)
        ]

        if not items:
            return evento_resumen

        evento_id = (
            evento_resumen.get("id")
            or evento_resumen.get("evento_id")
            or evento_resumen.get("prioritario_id")
        )

        evento_nombre = (
            evento_resumen.get("nombre")
            or evento_resumen.get("prioritario_nombre")
        )

        seleccionado: dict[str, Any] = {}

        if evento_id:
            evento_id_texto = str(evento_id)

            seleccionado = next(
                (
                    item
                    for item in items
                    if str(item.get("id") or "") == evento_id_texto
                ),
                {},
            )

        if not seleccionado and evento_nombre:
            evento_nombre_texto = str(evento_nombre).strip().lower()

            seleccionado = next(
                (
                    item
                    for item in items
                    if str(item.get("nombre") or "").strip().lower()
                    == evento_nombre_texto
                ),
                {},
            )

        if not seleccionado:
            seleccionado = items[0]

        return {
            **seleccionado,
            **evento_resumen,
            "id": (
                seleccionado.get("id")
                or evento_resumen.get("id")
                or evento_resumen.get("prioritario_id")
            ),
            "nombre": (
                seleccionado.get("nombre")
                or evento_resumen.get("nombre")
                or evento_resumen.get("prioritario_nombre")
            ),
            "fecha": (
                seleccionado.get("fecha")
                or evento_resumen.get("fecha")
            ),
            "pax": (
                seleccionado.get("pax")
                or evento_resumen.get("pax")
            ),
            "estado": (
                seleccionado.get("estado")
                or evento_resumen.get("estado")
                or "programado"
            ),
            "dias": (
                seleccionado.get("dias")
                or evento_resumen.get("dias")
            ),
            "servicios": (
                seleccionado.get("servicios")
                or evento_resumen.get("servicios")
            ),
        }

    @staticmethod
    def _resolve_prioridad(
        *,
        executive_result: dict[str, Any],
        bandeja: list[dict[str, Any]],
    ) -> dict[str, Any]:
        prioridad = executive_result.get(
            "prioridad_inmediata",
        )

        if isinstance(prioridad, dict) and prioridad:
            return dict(prioridad)

        resumen = dict(
            executive_result.get(
                "resumen_restaurante",
            )
            or {},
        )

        prioridad_resumen = resumen.get(
            "prioridad_dia",
        )

        if (
            isinstance(prioridad_resumen, dict)
            and prioridad_resumen
        ):
            return dict(prioridad_resumen)

        if bandeja:
            primera = dict(bandeja[0] or {})

            return {
                "codigo": primera.get("tipo")
                or primera.get("modulo_origen"),
                "titulo": primera.get("titulo"),
                "mensaje": primera.get("resumen"),
                "severidad": primera.get("severidad"),
                "cantidad": primera.get("cantidad"),
                "accion_navegacion": primera.get(
                    "accion_navegacion",
                ),
            }

        return {
            "codigo": "SIN_PRIORIDAD",
            "titulo": "Sin prioridad urgente",
            "mensaje": (
                "No hay acciones operativas críticas "
                "pendientes."
            ),
        }

    @staticmethod
    def _resolve_pendientes(
        *,
        executive_result: dict[str, Any],
        bandeja: list[dict[str, Any]],
        modulos: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        pendientes = list(
            executive_result.get("pendientes")
            or executive_result.get(
                "pendientes_operativos",
            )
            or []
        )

        result = pendientes or [
            {
                "codigo": item.get("tipo"),
                "titulo": item.get("titulo"),
                "descripcion": item.get("resumen"),
                "prioridad": item.get("severidad"),
                "estado": "pendiente",
                "modulo": item.get("modulo_origen"),
                "cantidad": item.get("cantidad"),
                "accion_navegacion": item.get(
                    "accion_navegacion",
                ),
                "entidad_id": item.get("contexto_id"),
            }
            for item in bandeja
            if isinstance(item, dict)
        ]
        recipe_items = list((((modulos or {}).get("recetas") or {}).get("items") or []))
        for pending in result:
            code = str(pending.get("codigo") or pending.get("tipo") or "").upper()
            if str(pending.get("modulo") or "").lower() == "recetas" or "RECETA" in code:
                pending["entidades"] = recipe_items
        return result

    @staticmethod
    def _resolve_riesgos(
        *,
        executive_result: dict[str, Any],
        modulos: dict[str, Any],
        bandeja: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        riesgos = list(
            executive_result.get("riesgos")
            or executive_result.get(
                "riesgos_operativos",
            )
            or []
        )

        if riesgos:
            return riesgos

        riesgos_home: list[dict[str, Any]] = []

        stock = dict(modulos.get("stock") or {})
        for alerta in list(stock.get("items") or []):
            if not isinstance(alerta, dict):
                continue

            riesgos_home.append(
                {
                    **alerta,
                    "nivel": alerta.get("nivel")
                    or "atencion",
                    "mensaje": alerta.get("mensaje")
                    or "Alerta de stock.",
                    "tipo": alerta.get("tipo")
                    or "stock",
                    "accion_recomendada": (
                        "Revisar existencias y "
                        "necesidades de compra."
                    ),
                    "modulo": "stock",
                },
            )

        for item in bandeja:
            if not isinstance(item, dict):
                continue

            severidad = str(
                item.get("severidad") or "",
            ).lower()

            if severidad not in {
                "importante",
                "critica",
            }:
                continue

            riesgos_home.append(
                {
                    "nivel": severidad,
                    "mensaje": item.get("titulo")
                    or item.get("resumen"),
                    "accion_recomendada": (
                        item.get("resumen")
                        or "Revisar la situación."
                    ),
                    "modulo": item.get(
                        "modulo_origen",
                    ),
                },
            )

        return riesgos_home

    @staticmethod
    def _resolve_recomendaciones(
        *,
        executive_result: dict[str, Any],
        bandeja: list[dict[str, Any]],
    ) -> list[Any]:
        recomendaciones = list(
            executive_result.get(
                "recomendaciones",
            )
            or executive_result.get(
                "recomendaciones_operativas",
            )
            or []
        )

        if recomendaciones:
            return recomendaciones

        return [
            {
                "titulo": item.get("titulo"),
                "mensaje": item.get("resumen"),
                "modulo": item.get("modulo_origen"),
                "accion_navegacion": item.get(
                    "accion_navegacion",
                ),
            }
            for item in bandeja[:5]
            if isinstance(item, dict)
        ]
