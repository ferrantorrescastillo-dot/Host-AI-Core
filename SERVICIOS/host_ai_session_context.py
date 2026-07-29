from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class SessionActionItem:
    action_type: str
    message: str
    module: str = ""
    entity_id: str = ""
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HostAISessionContext:
    usuario: str = "operador"
    ultima_intencion: str = ""
    ultimo_modulo: str = "HOME"
    ultima_navegacion: str = ""
    ultima_busqueda: str = ""
    ultima_lista_mostrada: list[dict[str, Any]] = field(default_factory=list)
    ultimo_elemento_seleccionado: dict[str, Any] = field(default_factory=dict)
    contexto_activo: str = "HOME"
    receta_activa: dict[str, Any] = field(default_factory=dict)
    escandallo_activo: dict[str, Any] = field(default_factory=dict)
    menu_activo: dict[str, Any] = field(default_factory=dict)
    evento_activo: dict[str, Any] = field(default_factory=dict)
    produccion_activa: dict[str, Any] = field(default_factory=dict)
    historial_corto_acciones: list[dict[str, Any]] = field(default_factory=list)
    actualizado_en: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # Alias para compatibilidad con pruebas APP-01.x/HF1.
        data["ultimo_termino_busqueda"] = self.ultima_busqueda
        data["ultimos_resultados"] = list(self.ultima_lista_mostrada)
        data["ultimo_elemento"] = str(
            self.ultimo_elemento_seleccionado.get("id")
            or self.ultimo_elemento_seleccionado.get("codigo")
            or ""
        )
        data["ultimo_modulo_abierto"] = self.ultimo_modulo
        return data

    def reset(self) -> None:
        self.ultima_intencion = ""
        self.ultimo_modulo = "HOME"
        self.ultima_navegacion = ""
        self.ultima_busqueda = ""
        self.ultima_lista_mostrada = []
        self.ultimo_elemento_seleccionado = {}
        self.contexto_activo = "HOME"
        self.receta_activa = {}
        self.escandallo_activo = {}
        self.menu_activo = {}
        self.evento_activo = {}
        self.produccion_activa = {}
        self.historial_corto_acciones = []
        self.actualizado_en = _now_iso()

    def registrar_accion(self, action_type: str, message: str, module: str = "", entity_id: str = "") -> None:
        item = SessionActionItem(
            action_type=str(action_type or "ACCION"),
            message=str(message or ""),
            module=str(module or ""),
            entity_id=str(entity_id or ""),
        )
        historial = list(self.historial_corto_acciones)
        historial.append(item.to_dict())
        self.historial_corto_acciones = historial[-20:]
        self.actualizado_en = _now_iso()

    def actualizar_contexto_activo(self, contexto: str, module: str = "") -> None:
        self.contexto_activo = str(contexto or "HOME").upper()
        if module:
            self.ultimo_modulo = str(module).upper()
        self.actualizado_en = _now_iso()

    def actualizar_desde_navegacion(self, nav_request: dict[str, Any]) -> None:
        nav = dict(nav_request or {})
        modulo = str(nav.get("target_module") or "").upper()
        if modulo:
            self.ultimo_modulo = modulo
            self.contexto_activo = modulo
            self.ultima_navegacion = modulo

        ctx = dict(nav.get("context_update") or {})
        if "contexto_activo" in ctx:
            self.contexto_activo = str(ctx.get("contexto_activo") or self.contexto_activo).upper()
        if "receta_activa" in ctx and isinstance(ctx.get("receta_activa"), dict):
            self.receta_activa = dict(ctx.get("receta_activa") or {})
        if "escandallo_activo" in ctx and isinstance(ctx.get("escandallo_activo"), dict):
            self.escandallo_activo = dict(ctx.get("escandallo_activo") or {})
        if "menu_activo" in ctx and isinstance(ctx.get("menu_activo"), dict):
            self.menu_activo = dict(ctx.get("menu_activo") or {})
        if "evento_activo" in ctx and isinstance(ctx.get("evento_activo"), dict):
            self.evento_activo = dict(ctx.get("evento_activo") or {})
        if "produccion_activa" in ctx and isinstance(ctx.get("produccion_activa"), dict):
            self.produccion_activa = dict(ctx.get("produccion_activa") or {})

        self.actualizado_en = _now_iso()


__all__ = ["HostAISessionContext", "SessionActionItem"]
