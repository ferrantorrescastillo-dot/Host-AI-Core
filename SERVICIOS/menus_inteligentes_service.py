from __future__ import annotations

from pathlib import Path
from typing import Any

from SERVICIOS.biblioteca_menus_601 import BibliotecaMenus601
from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601


PUBLIC_STATES = {"BORRADOR", "ACTIVO", "ARCHIVADO"}


class MenusInteligentesService:
    """Contrato público de Menús sobre BibliotecaMenus601 y su motor de costes."""

    def __init__(self, base_dir: Path) -> None:
        self.menus = BibliotecaMenus601(base_dir)
        self.recetas = RepositorioBibliotecaRecetas601(base_dir)
        self.biblioteca = BibliotecaCulinariaReadService(base_dir)

    def listar(self, query: dict[str, Any] | None = None) -> dict[str, Any]:
        query = dict(query or {})
        include_archived = self._bool(query.get("incluir_archivados"), False)
        wanted_state = str(query.get("estado") or "").strip().upper()
        text = self._norm(query.get("q"))
        items = [self._public(item) for item in self.menus.ver_todos().get("menus", [])]
        if not include_archived:
            items = [item for item in items if item["estado"] != "ARCHIVADO"]
        if wanted_state:
            if wanted_state not in PUBLIC_STATES:
                return self._error("invalid_state", "El estado de menú no es válido.", 400)
            items = [item for item in items if item["estado"] == wanted_state]
        if text:
            items = [item for item in items if text in self._norm(item["nombre"])]
        items.sort(key=lambda item: (item["estado"], self._norm(item["nombre"])))
        return {
            "ok": True,
            "menus": items,
            "total": len(items),
            "resumen": {
                "borradores": sum(item["estado"] == "BORRADOR" for item in items),
                "activos": sum(item["estado"] == "ACTIVO" for item in items),
                "archivados": sum(item["estado"] == "ARCHIVADO" for item in items),
            },
        }

    def obtener(self, menu_id: str) -> dict[str, Any]:
        # GET público estrictamente READ: ver_detalle también detecta y persiste
        # desactualización, algo impropio de una pantalla de consulta.
        menu = self.menus.repo.obtener(menu_id)
        if not menu:
            return self._error("menu_not_found", "Menú no encontrado.", 404)
        return {"ok": True, "menu": self._public(menu)}

    def elaboraciones(self, query: dict[str, Any] | None = None) -> dict[str, Any]:
        # Alias compatible: la autoridad del selector es el catÃ¡logo pÃºblico completo.
        result = self.biblioteca.listar({"page_size": 100, **dict(query or {})})
        if not result.get("ok"):
            return result
        catalog = result["elaboraciones"]
        return {
            "ok": True,
            "elaboraciones": [
                {
                    "id": item["id"], "codigo": item["codigo"],
                    "nombre": item["nombre"], "familia": item.get("categoria") or "",
                }
                for item in catalog["items"]
            ],
            "total": catalog["total"],
        }

    def crear(self, body: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize(body)
        if "error" in normalized:
            return normalized
        result = self.menus.nuevo_menu(normalized)
        return {"ok": True, "menu": self._public(result["menu"])}

    def actualizar(self, menu_id: str, body: dict[str, Any]) -> dict[str, Any]:
        current = self.menus.repo.obtener(menu_id)
        if not current:
            return self._error("menu_not_found", "Menú no encontrado.", 404)
        expected = body.get("version")
        if not isinstance(expected, int) or expected != int(current.get("version_menu") or 1):
            return self._error(
                "menu_version_conflict",
                "El menú cambió desde la última lectura.",
                409,
                current_version=int(current.get("version_menu") or 1),
            )
        merged = {
            "nombre": body.get("nombre", current.get("nombre")),
            "comensales": body.get("comensales", current.get("comensales_recomendado")),
            "estado": body.get("estado", self._public_state(current)),
            "observaciones": body.get("observaciones", current.get("observaciones")),
            "secciones": body.get("secciones", self._sections(current)),
        }
        normalized = self._normalize(merged)
        if "error" in normalized:
            return normalized
        result = self.menus.editar_menu(menu_id, normalized)
        return {"ok": True, "menu": self._public(result["menu"])}

    def archivar(self, menu_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        current = self.menus.repo.obtener(menu_id)
        if not current:
            return self._error("menu_not_found", "Menú no encontrado.", 404)
        expected = dict(body or {}).get("version")
        if expected is not None and expected != int(current.get("version_menu") or 1):
            return self._error("menu_version_conflict", "El menú cambió desde la última lectura.", 409)
        result = self.menus.archivar_menu(menu_id)
        return {"ok": True, "menu": self._public(result["menu"])}

    def _normalize(self, body: dict[str, Any]) -> dict[str, Any]:
        name = str(body.get("nombre") or "").strip()
        if not name:
            return self._error("invalid_menu", "El nombre del menú es obligatorio.", 400)
        state = str(body.get("estado") or "BORRADOR").strip().upper()
        if state not in PUBLIC_STATES:
            return self._error("invalid_state", "El estado de menú no es válido.", 400)
        try:
            diners = float(body.get("comensales") or 0)
        except (TypeError, ValueError):
            diners = 0
        if diners <= 0:
            return self._error("invalid_diners", "Los comensales deben ser mayores que cero.", 400)
        sections = body.get("secciones")
        if not isinstance(sections, list):
            return self._error("invalid_sections", "Las secciones deben enviarse como lista.", 400)
        composition: dict[str, list[dict[str, Any]]] = {}
        seen_names: set[str] = set()
        for index, section in enumerate(sections):
            if not isinstance(section, dict):
                return self._error("invalid_section", "Cada sección debe ser un objeto.", 400)
            section_name = str(section.get("nombre") or "").strip()
            if not section_name or self._norm(section_name) in seen_names:
                return self._error("invalid_section", "Cada sección necesita un nombre único.", 400)
            seen_names.add(self._norm(section_name))
            references = section.get("elaboraciones")
            if not isinstance(references, list):
                return self._error("invalid_section", "Las elaboraciones deben enviarse como lista.", 400)
            composition[section_name] = []
            for reference in references:
                recipe_id = str((reference or {}).get("elaboracion_id") or "").strip()
                recipe = self._elaboration(recipe_id)
                if not recipe:
                    return self._error(
                        "elaboration_not_found",
                        f"La elaboración {recipe_id or '(vacía)'} no existe en la Biblioteca.",
                        400,
                    )
                try:
                    quantity = float((reference or {}).get("cantidad") or 1)
                except (TypeError, ValueError):
                    quantity = 0
                if quantity <= 0:
                    return self._error("invalid_quantity", "La cantidad debe ser mayor que cero.", 400)
                composition[section_name].append({
                    "tipo_referencia": "RECETA",
                    "referencia": str(recipe.get("id") or recipe.get("codigo") or recipe_id),
                    "cantidad": quantity,
                    "orden": int((reference or {}).get("orden") or len(composition[section_name])),
                    "observaciones": str((reference or {}).get("observaciones") or ""),
                    "version_elaboracion": (reference or {}).get("version_elaboracion"),
                })
        return {
            "nombre": name,
            "comensales_recomendado": diners,
            "observaciones": str(body.get("observaciones") or ""),
            "estado_publicacion": state,
            "composicion": composition,
        }

    def _public(self, menu: dict[str, Any]) -> dict[str, Any]:
        menu = self._with_current_cost(menu)
        return {
            "id": str(menu.get("menu_id") or ""),
            "codigo": str(menu.get("codigo") or ""),
            "nombre": str(menu.get("nombre") or ""),
            "estado": self._public_state(menu),
            "estado_operativo": str(menu.get("estado") or ""),
            "version": int(menu.get("version_menu") or 1),
            "comensales": float(menu.get("comensales_recomendado") or 0),
            "observaciones": str(menu.get("observaciones") or ""),
            "secciones": self._sections(menu),
            "coste_total": float(menu.get("coste_total") or 0),
            "coste_por_comensal": float(menu.get("coste_por_comensal") or 0),
            "coste_completo": bool(menu.get("coste_completo", True)),
            "lineas_sin_coste": int(menu.get("lineas_sin_coste") or 0),
            "advertencias": list(menu.get("advertencias_coste") or []),
            "incidencias": list(menu.get("incidencias") or []),
            "creado_en": menu.get("creado_en"),
            "actualizado_en": menu.get("actualizado_en"),
            "origen": menu.get("hoja_origen") or menu.get("origen_importacion"),
            "modelo_biblioteca": str(menu.get("modelo_biblioteca") or ""),
        }

    def _sections(self, menu: dict[str, Any]) -> list[dict[str, Any]]:
        line_costs = {
            (self._norm(line.get("seccion")), self._norm(line.get("referencia"))): line
            for line in menu.get("lineas") or []
        }
        sections = []
        for order, (name, references) in enumerate(dict(menu.get("composicion") or {}).items()):
            items = []
            for reference in references or []:
                if not isinstance(reference, dict):
                    raise ValueError(
                        f"Menú {menu.get('menu_id') or '(sin id)'}: composicion.{name} contiene una línea que no es un objeto."
                    )
                canonical_reference = str(reference.get("referencia") or "")
                if not canonical_reference:
                    raise ValueError(
                        f"Menú {menu.get('menu_id') or '(sin id)'}: composicion.{name}.referencia es obligatoria."
                    )
                reference_type = str(reference.get("tipo_referencia") or "RECETA").upper()
                recipe = self._elaboration(canonical_reference) if reference_type == "RECETA" else None
                product = self.menus.repo_prod.obtener_producto(canonical_reference) if reference_type == "PRODUCTO" else None
                related = recipe or product or {}
                line = line_costs.get((self._norm(name), self._norm(reference.get("referencia"))), {})
                items.append({
                    "elaboracion_id": str(related.get("id") or related.get("codigo") or canonical_reference),
                    "elaboracion_nombre": str(related.get("nombre") or canonical_reference),
                    "tipo_referencia": reference_type,
                    "referencia_canonica": canonical_reference,
                    "cantidad": float(reference.get("cantidad") or 1),
                    "coste_por_racion": line.get("coste_por_racion"),
                    "coste_linea_por_comensal": line.get("coste_linea_por_comensal"),
                    "coste_linea_total": line.get("coste_linea_total"),
                    "coste_por_comensal": line.get("coste_por_comensal"),
                    "estado_coste": str(line.get("estado_coste") or "SIN_COSTE"),
                    "motivo_coste_no_disponible": line.get("motivo_coste_no_disponible"),
                    "fecha_coste": line.get("fecha_coste"),
                    "orden": int(reference.get("orden") or len(items)),
                    "observaciones": str(reference.get("observaciones") or ""),
                    "version_elaboracion": reference.get("version_elaboracion") or related.get("version"),
                })
            sections.append({"id": f"SEC-{order + 1:03d}", "nombre": name, "orden": order, "elaboraciones": items})
        return sections

    def _with_current_cost(self, menu: dict[str, Any]) -> dict[str, Any]:
        calculation = self.menus.motor.calcular(
            nombre_menu=str(menu.get("nombre") or "MenÃº"),
            comensales=float(menu.get("comensales_recomendado") or 0),
            composicion=dict(menu.get("composicion") or {}),
            precio_venta_comensal=float(menu.get("precio_venta_comensal") or 0),
            precio_venta_total=float(menu.get("precio_venta_total") or 0),
        )
        return {
            **menu,
            "lineas": list(calculation.get("lineas") or []),
            "coste_por_comensal": calculation.get("coste_por_comensal"),
            "coste_total": calculation.get("coste_total"),
            "coste_completo": calculation.get("coste_completo"),
            "lineas_sin_coste": calculation.get("lineas_sin_coste"),
            "advertencias_coste": list(calculation.get("advertencias") or []),
            "incidencias": list(calculation.get("incidencias") or []),
        }

    def _elaboration(self, elaboration_id: str) -> dict[str, Any] | None:
        result = self.biblioteca.detalle(elaboration_id)
        return result.get("elaboracion") if result.get("ok") else None

    @staticmethod
    def _public_state(menu: dict[str, Any]) -> str:
        explicit = str(menu.get("estado_publicacion") or "").upper()
        if explicit in PUBLIC_STATES:
            return explicit
        internal = str(menu.get("estado") or "").upper()
        if internal == "ARCHIVADO":
            return "ARCHIVADO"
        if internal == "BORRADOR":
            return "BORRADOR"
        return "ACTIVO"

    @staticmethod
    def _norm(value: Any) -> str:
        return " ".join(str(value or "").strip().lower().split())

    @staticmethod
    def _bool(value: Any, default: bool) -> bool:
        if value in (None, ""):
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "si", "sí"}

    @staticmethod
    def _error(code: str, message: str, status: int, **extra: Any) -> dict[str, Any]:
        return {"ok": False, "error": {"code": code, "message": message, "status": status, **extra}}


__all__ = ["MenusInteligentesService", "PUBLIC_STATES"]
