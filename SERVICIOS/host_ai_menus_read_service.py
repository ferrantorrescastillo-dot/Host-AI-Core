from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

from SERVICIOS.menus_inteligentes_service import MenusInteligentesService


class HostAIMenusReadService:
    """Adaptador conversacional READ sobre MenusInteligentesService."""

    MAX_LIMIT = 10

    def __init__(self, base_dir: Path, menus: Any | None = None) -> None:
        self.menus = menus or MenusInteligentesService(Path(base_dir))

    def consultar(self, consulta: str = "detalle", *, menu_id: str = "", termino: str = "",
                  limite: int = 10) -> dict[str, Any]:
        mode = str(consulta or "detalle").strip().lower()
        size = max(1, min(int(limite or self.MAX_LIMIT), self.MAX_LIMIT))
        identity = str(menu_id or "").strip()
        term = str(termino or "").strip()

        if identity:
            response = dict(self.menus.obtener(identity) or {})
            if response.get("ok") is False or not isinstance(response.get("menu"), dict):
                return self._result("NO_ENCONTRADO", mode, term)
            return self._result("OK", mode, term, menu=self._menu_dto(dict(response["menu"])))
        if not term:
            return self._result("REQUIERE_TERMINO", mode, term)

        response = dict(self.menus.listar({"q": term, "incluir_archivados": True}) or {})
        candidates = [self._menu_summary(dict(item)) for item in list(response.get("menus") or [])[:size]]
        exact = [item for item in candidates if self._norm(term) in {self._norm(item["menu_id"]), self._norm(item["nombre"])}]
        selected = exact or candidates
        if len(selected) != 1:
            return self._result("AMBIGUO" if selected else "NO_ENCONTRADO", mode, term, candidatos=selected)
        detail = dict(self.menus.obtener(selected[0]["menu_id"]) or {})
        if detail.get("ok") is False or not isinstance(detail.get("menu"), dict):
            return self._result("NO_ENCONTRADO", mode, term)
        return self._result("OK", mode, term, menu=self._menu_dto(dict(detail["menu"])))

    @classmethod
    def _menu_dto(cls, menu: dict[str, Any]) -> dict[str, Any]:
        sections: list[dict[str, Any]] = []
        elaborations: list[dict[str, Any]] = []
        for section in list(menu.get("secciones") or []):
            lines = []
            for item in list((section or {}).get("elaboraciones") or []):
                line = {
                    "elaboracion_id": str((item or {}).get("elaboracion_id") or ""),
                    "nombre": str((item or {}).get("elaboracion_nombre") or ""),
                    "cantidad": (item or {}).get("cantidad"),
                    "estado_coste": (item or {}).get("estado_coste") or None,
                    "coste_por_racion": (item or {}).get("coste_por_racion"),
                    "coste_linea_por_comensal": (item or {}).get("coste_linea_por_comensal"),
                    "coste_linea_total": (item or {}).get("coste_linea_total"),
                    "motivo_coste_no_disponible": (item or {}).get("motivo_coste_no_disponible"),
                    "version_elaboracion": (item or {}).get("version_elaboracion"),
                    "orden": (item or {}).get("orden"),
                    "observaciones": (item or {}).get("observaciones") or "",
                    "tipo_referencia": "RECETA",
                }
                lines.append(line)
                elaborations.append({**line, "seccion": (section or {}).get("nombre") or None})
            sections.append({
                "seccion_id": (section or {}).get("id") or None,
                "nombre": (section or {}).get("nombre") or None,
                "orden": (section or {}).get("orden"),
                "elaboraciones": lines,
            })
        return {
            "menu_id": str(menu.get("id") or ""),
            "codigo": str(menu.get("codigo") or ""),
            "nombre": str(menu.get("nombre") or ""),
            "estado": menu.get("estado") or None,
            "estado_operativo": menu.get("estado_operativo") or None,
            "version": menu.get("version"),
            "fecha": menu.get("fecha") or None,
            "comensales": menu.get("comensales"),
            "secciones": sections,
            "elaboraciones": elaborations,
            "total_elaboraciones": len(elaborations),
            "composicion_completa": True,
            "coste_total": menu.get("coste_total"),
            "coste_por_comensal": menu.get("coste_por_comensal"),
            "coste_completo": menu.get("coste_completo"),
            "lineas_sin_coste": menu.get("lineas_sin_coste"),
            "advertencias": list(menu.get("advertencias") or []),
            "incidencias": list(menu.get("incidencias") or []),
        }

    @staticmethod
    def _menu_summary(menu: dict[str, Any]) -> dict[str, Any]:
        return {
            "menu_id": str(menu.get("id") or ""),
            "nombre": str(menu.get("nombre") or ""),
            "estado": menu.get("estado") or None,
            "version": menu.get("version"),
        }

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in text if not unicodedata.combining(char)).strip().lower()

    @staticmethod
    def _result(state: str, mode: str, term: str, *, menu: dict[str, Any] | None = None,
                candidatos: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {
            "estado": state,
            "consulta": mode,
            "termino": term,
            "menu": menu,
            "candidatos": list(candidatos or []),
            "fuente": "menus_inteligentes_canonico",
            "solo_lectura": True,
            "datos_reales_modificados": False,
        }


__all__ = ["HostAIMenusReadService"]
