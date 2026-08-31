from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import secrets
from threading import RLock
from typing import Any, Callable

from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.gestion_eventos_471 import ESTADOS_EVENTO, crear_evento, validar_evento
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext


class CatalogCrudError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class CatalogCrudWriteService:
    """Preview/confirm común para altas y cambios de catálogo operativo.

    No expone borrado físico. Cada confirmación conserva el token como clave
    idempotente y rechaza previews obsoletos antes de escribir.
    """

    _lock = RLock()
    DOMAINS = frozenset({"EVENTO", "ARTICULO", "RECETA"})
    OPERATIONS = frozenset({"CREAR", "MODIFICAR", "ARCHIVAR"})
    EVENT_FIELDS = frozenset({"nombre", "fecha", "hora", "hora_inicio", "pax", "personas", "estado", "cliente", "tipo", "ubicacion", "lugar", "observaciones", "servicios", "menus"})
    ARTICLE_FIELDS = frozenset({"nombre", "codigo", "unidad_base", "unidad_compra", "cantidad_formato", "unidad_formato", "precio", "proveedor", "proveedor_preferente", "conversiones", "estado", "activo", "familia", "referencia_proveedor", "observaciones"})
    RECIPE_FIELDS = frozenset({"nombre", "codigo", "familia", "tipo", "numero_raciones", "rendimiento", "unidad_rendimiento", "ingredientes", "cantidades", "ingredientes_estructurados", "elaboracion", "procedimiento", "tiempo_elaboracion", "tiempo_activo", "tiempo_pasivo", "tiempo_total", "conservacion", "alergenos", "observaciones", "estado"})

    def __init__(self, base_dir: Path | str, *, now_provider: Callable[[], datetime] = datetime.now, ttl_seconds: int = 900) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.now_provider = now_provider
        self.ttl_seconds = max(30, int(ttl_seconds))
        self.events_path = self.base_dir / "DATOS" / "db" / "eventos.json"
        self.articles_path = self.base_dir / "DATOS" / "db" / "articulos.json"
        self.audit_path = self.base_dir / "DATOS" / "auditoria" / "catalog_crud.jsonl"
        self.recipes = RepositorioBibliotecaRecetas601(self.base_dir)
        self._pending: dict[str, dict[str, Any]] = {}
        self._completed: dict[str, dict[str, Any]] = {}

    def preview(self, *, domain: str, operation: str, payload: dict[str, Any], entity_id: str, session_id: str, context: AuthorizedExecutionContext, field_origins: dict[str, str] | None = None) -> dict[str, Any]:
        domain = str(domain or "").upper().strip()
        operation = str(operation or "").upper().strip()
        if domain not in self.DOMAINS or operation not in self.OPERATIONS:
            raise CatalogCrudError("invalid_operation", "Operación de catálogo no permitida.")
        self._authorize(context, domain, preview=True)
        if operation == "ARCHIVAR" and domain != "RECETA":
            raise CatalogCrudError("invalid_operation", "Este dominio no admite archivado.")
        current = None if operation == "CREAR" else self._find(domain, entity_id)
        if operation != "CREAR" and current is None:
            raise CatalogCrudError("not_found", "No se ha encontrado el registro solicitado.")
        if operation == "ARCHIVAR" and str((current or {}).get("estado") or "").upper() == "ARCHIVADA":
            raise CatalogCrudError("already_archived", "La receta ya está archivada.")
        proposed = self._normalize(domain, operation, dict(payload or {}), current)
        self._validate(domain, proposed, current=current, operation=operation)
        token = secrets.token_urlsafe(32)
        item = {
            "domain": domain, "operation": operation, "entity_id": entity_id,
            "before": current, "proposed": proposed,
            "expected": self._fingerprint(current),
            "actor": self._actor(context, session_id),
            "expires": self.now_provider() + timedelta(seconds=self.ttl_seconds),
            "field_origins": {key: value for key, value in dict(field_origins or {}).items() if key in self.ARTICLE_FIELDS and value in {"IA", "USUARIO"}},
        }
        self._pending[token] = item
        return {"ok": True, "estado": "LISTO_PARA_CONFIRMAR", "dominio": domain, "operacion": operation, "antes": current, "propuesto": proposed, "preview_token": token, "expira_en": item["expires"].isoformat(timespec="seconds"), "requiere_confirmacion": True, "datos_reales_modificados": False}

    def confirm(self, *, preview_token: str, session_id: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        token = str(preview_token or "").strip()
        with self._lock:
            completed = self._completed.get(token)
            if completed:
                if completed["actor"] != self._actor(context, session_id):
                    raise CatalogCrudError("invalid_preview", "La confirmación no pertenece a esta sesión.")
                return {**completed["result"], "idempotente": True}
            item = self._pending.get(token)
            if not item:
                raise CatalogCrudError("invalid_preview", "Token de confirmación inválido.")
            self._authorize(context, item["domain"], preview=False)
            if item["actor"] != self._actor(context, session_id):
                raise CatalogCrudError("invalid_preview", "La confirmación no pertenece a esta sesión.")
            if self.now_provider() > item["expires"]:
                self._pending.pop(token, None)
                raise CatalogCrudError("expired_preview", "La vista previa ha caducado.")
            current = None if item["operation"] == "CREAR" else self._find(item["domain"], item["entity_id"])
            if self._fingerprint(current) != item["expected"]:
                raise CatalogCrudError("stale_preview", "El registro ha cambiado desde la vista previa.")
            result_entity = self._persist(item)
            result = {"ok": True, "estado": "CONFIRMADO", "dominio": item["domain"], "operacion": item["operation"], "registro": result_entity, "idempotente": False, "datos_reales_modificados": True}
            self._audit(context, item, result_entity)
            self._pending.pop(token, None)
            self._completed[token] = {"actor": item["actor"], "result": result}
            return result

    def discard(self, *, preview_token: str, session_id: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        token = str(preview_token or "").strip()
        with self._lock:
            item = self._pending.get(token)
            if not item or item["actor"] != self._actor(context, session_id):
                raise CatalogCrudError("invalid_preview", "Token de confirmación inválido.")
            self._authorize(context, item["domain"], preview=True)
            self._pending.pop(token, None)
            return {"ok": True, "estado": "DESCARTADO", "datos_reales_modificados": False}

    def event_detail(self, entity_id: str) -> dict[str, Any] | None:
        return self._find("EVENTO", entity_id)

    def _normalize(self, domain: str, operation: str, payload: dict[str, Any], current: dict[str, Any] | None) -> dict[str, Any]:
        allowed = {"EVENTO": self.EVENT_FIELDS, "ARTICULO": self.ARTICLE_FIELDS, "RECETA": self.RECIPE_FIELDS}[domain]
        if not payload and operation != "ARCHIVAR":
            raise CatalogCrudError("empty_payload", "No hay cambios para previsualizar.")
        if set(payload) - allowed:
            raise CatalogCrudError("unknown_fields", "La solicitud contiene campos no permitidos.")
        if operation == "CREAR" and any(key in payload for key in ("id", "id_evento")):
            raise CatalogCrudError("immutable_field", "El identificador se genera internamente.")
        proposed = dict(current or {})
        proposed.update(payload)
        if domain == "EVENTO":
            proposed["pax"] = int(proposed.get("pax") or proposed.get("personas") or 0)
            proposed["hora_inicio"] = str(proposed.get("hora_inicio") or proposed.get("hora") or "").strip()
            proposed["estado"] = str(proposed.get("estado") or "borrador").lower()
            if operation == "CREAR":
                generated = crear_evento(proposed.get("nombre"), proposed.get("fecha"), hora=proposed["hora_inicio"], tipo=proposed.get("tipo") or "evento", personas=proposed["pax"], cliente=proposed.get("cliente"), lugar=proposed.get("ubicacion") or proposed.get("lugar"), observaciones=proposed.get("observaciones"), estado=proposed["estado"])
                proposed = {**generated, **proposed, "id": generated["id_evento"]}
                proposed.pop("id_evento", None)
        elif domain == "ARTICULO":
            proposed["nombre"] = str(proposed.get("nombre") or "").strip()
            proposed["codigo"] = str(proposed.get("codigo") or "").strip()
            proposed["proveedor"] = proposed.get("proveedor") or proposed.get("proveedor_preferente") or ""
            proposed["activo"] = bool(proposed.get("activo", str(proposed.get("estado") or "ACTIVO").upper() != "INACTIVO"))
            if operation == "CREAR":
                proposed.update({"origen": "alta_manual_segura", "fecha_importacion": self.now_provider().isoformat(timespec="seconds")})
        else:
            if "procedimiento" in proposed and "elaboracion" not in proposed:
                proposed["elaboracion"] = proposed.pop("procedimiento")
            if "rendimiento" in proposed and "numero_raciones" not in proposed:
                proposed["numero_raciones"] = proposed["rendimiento"]
            if operation == "ARCHIVAR":
                proposed["estado"] = "ARCHIVADA"
        return proposed

    def _validate(self, domain: str, proposed: dict[str, Any], *, current: dict[str, Any] | None, operation: str) -> None:
        if domain == "EVENTO":
            check = validar_evento({**proposed, "personas": proposed.get("pax")})
            if not check["ok"]:
                raise CatalogCrudError("invalid_event", " · ".join(check["errores"]))
            if proposed.get("estado") not in ESTADOS_EVENTO and proposed.get("estado") != "pendiente":
                raise CatalogCrudError("invalid_state", "Estado de evento no válido.")
            self._ensure_unique(domain, proposed, current)
        elif domain == "ARTICULO":
            if not proposed.get("nombre") or not proposed.get("codigo"):
                raise CatalogCrudError("invalid_article", "Nombre y código son obligatorios.")
            if proposed.get("precio") not in (None, "") and float(proposed["precio"]) < 0:
                raise CatalogCrudError("invalid_article", "El precio no puede ser negativo.")
            self._ensure_unique(domain, proposed, current)
        elif operation != "ARCHIVAR":
            progressive = bool(
                current
                and str(current.get("estado") or "") == "PENDIENTE_DE_COMPLETAR"
                and current.get("campos_pendientes_importacion")
            )
            errors = (
                self.recipes.validar_borrador_incompleto(proposed)
                if progressive else self.recipes._validar_obligatorios(proposed)
            )
            if progressive and proposed.get("numero_raciones") != current.get("numero_raciones"):
                try:
                    if float(proposed.get("numero_raciones") or 0) <= 0:
                        errors.append("El rendimiento informado debe ser mayor que cero.")
                except (TypeError, ValueError):
                    errors.append("El rendimiento informado debe ser numérico.")
            if errors:
                raise CatalogCrudError("invalid_recipe", " · ".join(errors))
            for ingredient in proposed.get("ingredientes_estructurados") or []:
                if not isinstance(ingredient, dict):
                    raise CatalogCrudError("invalid_ingredient", "Los ingredientes estructurados no son válidos.")
                article_id = str(ingredient.get("article_id") or ingredient.get("articulo_id") or "").strip()
                if article_id and self._find("ARTICULO", article_id) is None:
                    raise CatalogCrudError("article_not_found", f"El artículo {article_id} no existe en el catálogo canónico.")
            self._ensure_unique(domain, proposed, current)

    def _ensure_unique(self, domain: str, proposed: dict[str, Any], current: dict[str, Any] | None) -> None:
        identity = self._entity_id(domain, current or {})
        name = self._norm(proposed.get("nombre")); code = self._norm(proposed.get("codigo"))
        for item in self._all(domain):
            if self._entity_id(domain, item) == identity:
                continue
            if name and self._norm(item.get("nombre")) == name:
                raise CatalogCrudError("duplicate", "Ya existe un registro con ese nombre.")
            if code and self._norm(item.get("codigo")) == code:
                raise CatalogCrudError("duplicate", "Ya existe un registro con ese código.")

    def _persist(self, item: dict[str, Any]) -> dict[str, Any]:
        domain, operation, proposed = item["domain"], item["operation"], dict(item["proposed"])
        if domain == "RECETA":
            if operation == "MODIFICAR":
                current = dict(item.get("before") or {})
                origins = dict(current.get("procedencia_campos") or {})
                history = list(current.get("historial_procedencia") or [])
                now = self.now_provider().isoformat(timespec="seconds")
                for field in self.RECIPE_FIELDS:
                    if field in proposed and proposed.get(field) != current.get(field):
                        history.append({"campo": field, "valor_anterior": current.get(field), "valor_nuevo": proposed.get(field), "origen_anterior": origins.get(field), "origen_nuevo": "USUARIO", "actor": item["actor"][0], "timestamp": now, "estado_revision": "VALIDADO_USUARIO"})
                        origins[field] = {"tipo": "USUARIO", "actor_id": item["actor"][0], "fecha": now, "estado_revision": "VALIDADO_USUARIO"}
                changes = {key: value for key, value in proposed.items() if key in self.RECIPE_FIELDS}
                changes.update({"procedencia_campos": origins, "historial_procedencia": history})
                response = (
                    self.recipes.editar_borrador_incompleto(item["entity_id"], changes)
                    if current.get("campos_pendientes_importacion")
                    else self.recipes.editar(item["entity_id"], changes)
                )
            else:
                response = self.recipes.crear(proposed) if operation == "CREAR" else self.recipes.archivar(item["entity_id"])
            if not response.get("ok"):
                raise CatalogCrudError("write_rejected", " · ".join(response.get("errores") or ["No se pudo guardar la receta."]))
            identity = str((response.get("receta") or proposed).get("id") or item["entity_id"])
            return self.recipes.obtener(identity) or response.get("receta") or proposed
        if domain == "ARTICULO" and operation == "MODIFICAR":
            current = dict(item.get("before") or {})
            origins = dict(current.get("procedencia_campos") or {})
            history = list(current.get("historial_procedencia") or [])
            now = self.now_provider().isoformat(timespec="seconds")
            for field in self.ARTICLE_FIELDS:
                if field in proposed and proposed.get(field) != current.get(field):
                    history.append({"campo": field, "valor_anterior": current.get(field), "valor_nuevo": proposed.get(field), "origen_anterior": origins.get(field), "origen_nuevo": "USUARIO", "actor": item["actor"][0], "timestamp": now, "estado_revision": "VALIDADO_USUARIO"})
                    origins[field] = {"tipo": "USUARIO", "actor_id": item["actor"][0], "fecha": now, "estado_revision": "VALIDADO_USUARIO"}
            proposed.update({"procedencia_campos": origins, "historial_procedencia": history})
        elif domain == "ARTICULO" and operation == "CREAR":
            now = self.now_provider().isoformat(timespec="seconds"); origins = {}; history = []
            requested_origins = dict(item.get("field_origins") or {})
            for field in self.ARTICLE_FIELDS:
                if field not in proposed or proposed.get(field) in (None, "", []): continue
                origin = requested_origins.get(field, "USUARIO")
                status = "PENDIENTE_REVISION" if origin == "IA" else "VALIDADO_USUARIO"
                origins[field] = {"tipo": origin, "actor_id": item["actor"][0], "fecha": now, "estado_revision": status}
                history.append({"campo": field, "valor_anterior": None, "valor_nuevo": proposed.get(field), "origen_anterior": None, "origen_nuevo": origin, "actor": item["actor"][0], "timestamp": now, "estado_revision": status})
            proposed.update({"procedencia_campos": origins, "historial_procedencia": history})
        path = self.events_path if domain == "EVENTO" else self.articles_path
        values = self._read_list(path)
        if operation == "CREAR":
            values.append(proposed)
        else:
            target = item["entity_id"]
            values = [proposed if self._entity_id(domain, value) == target else value for value in values]
        self._write_list(path, values)
        return proposed

    def _find(self, domain: str, entity_id: str) -> dict[str, Any] | None:
        key = str(entity_id or "").strip()
        return next((dict(item) for item in self._all(domain) if self._entity_id(domain, item) == key), None)

    def _all(self, domain: str) -> list[dict[str, Any]]:
        if domain == "RECETA": return [dict(item) for item in self.recipes.listar(incluir_archivadas=True)]
        return self._read_list(self.events_path if domain == "EVENTO" else self.articles_path)

    @staticmethod
    def _entity_id(domain: str, item: dict[str, Any]) -> str:
        return str(item.get("id") or item.get("id_evento") or item.get("codigo") or "").strip()

    @staticmethod
    def _read_list(path: Path) -> list[dict[str, Any]]:
        if not path.exists(): return []
        value = json.loads(path.read_text(encoding="utf-8"))
        return [dict(item) for item in value] if isinstance(value, list) else []

    @staticmethod
    def _write_list(path: Path, values: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)

    def _authorize(self, context: AuthorizedExecutionContext, domain: str, *, preview: bool) -> None:
        valid, _ = context.validate() if isinstance(context, AuthorizedExecutionContext) else (False, "")
        scope = {"EVENTO": "eventos", "ARTICULO": "articulos", "RECETA": "recetas"}[domain]
        accepted = {f"{scope}:write", f"{scope}:preview"} if preview else {f"{scope}:write"}
        if not valid or not accepted.intersection(context.scopes):
            raise CatalogCrudError("unauthorized", "El actor no está autorizado.")

    def _audit(self, context: AuthorizedExecutionContext, item: dict[str, Any], result: dict[str, Any]) -> None:
        record = {"request_id": context.request_id, "dominio": item["domain"], "operacion": item["operation"], "entity_id": self._entity_id(item["domain"], result), "actor": context.user_id, "timestamp": self.now_provider().isoformat(timespec="seconds"), "payload_hash": self._fingerprint(result)}
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as handle: handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    @staticmethod
    def _fingerprint(value: dict[str, Any] | None) -> str:
        if value is None: return "NEW"
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def _actor(context: AuthorizedExecutionContext, session_id: str) -> tuple[str, str, str]:
        return context.user_id, context.tenant_id, str(session_id or "")

    @staticmethod
    def _norm(value: Any) -> str: return " ".join(str(value or "").strip().casefold().split())


__all__ = ["CatalogCrudWriteService", "CatalogCrudError"]
