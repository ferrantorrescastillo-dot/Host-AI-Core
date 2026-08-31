from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.host_ai_produccion_read_service import HostAIProduccionReadService
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService


class HostAIUsoElaboracionReadService:
    """Consulta inversa READ de usos canónicos de una elaboración."""

    MAX_LIMIT = 10
    MAX_DEPTH = 5

    def __init__(self, base_dir: Path, *, core: Any | None = None, biblioteca: Any | None = None,
                 menus: Any | None = None, produccion: Any | None = None) -> None:
        root = Path(base_dir)
        self.biblioteca = biblioteca or BibliotecaCulinariaReadService(root)
        self.menus = menus or MenusInteligentesService(root)
        self.produccion = produccion or (HostAIProduccionReadService(core) if core is not None else None)
        self._parent_graph: dict[str, list[dict[str, Any]]] | None = None

    def consultar(self, *, escandallo_id: str = "", termino: str = "", limite: int = 10) -> dict[str, Any]:
        size = max(1, min(int(limite or self.MAX_LIMIT), self.MAX_LIMIT))
        resolved = self._resolve_identity(str(escandallo_id or "").strip(), str(termino or "").strip(), size)
        if resolved["estado"] != "OK":
            return self._result(resolved["estado"], candidatos=resolved.get("candidatos"))

        target = dict(resolved["elaboracion"])
        target_id = target["escandallo_id"]
        ancestry = self._parent_paths(target_id)
        parents = [{
            "escandallo_id": path[-1]["escandallo_id"], "nombre": path[-1]["nombre"],
            "tipo_relacion": "SUBELABORACION_DIRECTA" if len(path) == 1 else "SUBELABORACION_INDIRECTA",
            "profundidad": len(path), "trazabilidad": [target, *path],
        } for path in ancestry[:size]]

        direct_menus = self._menu_uses(target_id, size)
        direct_production = self._production_uses(target_id, size)
        indirect_menus: list[dict[str, Any]] = []
        indirect_production: list[dict[str, Any]] = []
        for path in ancestry:
            parent = path[-1]
            for use in self._menu_uses(parent["escandallo_id"], size):
                indirect_menus.append({**use, "tipo_relacion": "USO_INDIRECTO",
                                       "trazabilidad": [use["menu"], *reversed(path), target]})
            for use in self._production_uses(parent["escandallo_id"], size):
                indirect_production.append({**use, "tipo_relacion": "USO_INDIRECTO",
                                            "trazabilidad": [use["plan"], *reversed(path), target]})

        indirect = self._deduplicate([*indirect_menus, *indirect_production], size)
        return self._result(
            "OK", elaboracion=target,
            menus=self._deduplicate([*direct_menus, *indirect_menus], size),
            produccion=self._deduplicate([*direct_production, *indirect_production], size),
            padres=parents, usos_directos=[*direct_menus, *direct_production][:size],
            usos_indirectos=indirect,
            trazabilidad=[item["trazabilidad"] for item in indirect if item.get("trazabilidad")][:size],
        )

    def _resolve_identity(self, identity: str, term: str, limit: int) -> dict[str, Any]:
        if identity:
            response = dict(self.biblioteca.detalle(identity) or {})
            detail = response.get("elaboracion")
            if response.get("ok") is not False and isinstance(detail, dict):
                return {"estado": "OK", "elaboracion": self._identity(detail)}
            return {"estado": "NO_ENCONTRADO"}
        if not term:
            return {"estado": "REQUIERE_TERMINO"}
        response = dict(self.biblioteca.listar({"q": term, "page": 1, "page_size": limit,
                                                "tiene_escandallo": "true"}) or {})
        items = [self._identity(dict(item)) for item in list((response.get("elaboraciones") or {}).get("items") or [])[:limit]]
        exact = [item for item in items if self._norm(term) in {self._norm(item["escandallo_id"]), self._norm(item["nombre"])}]
        selected = exact or items
        if len(selected) == 1:
            return {"estado": "OK", "elaboracion": selected[0]}
        return {"estado": "AMBIGUO" if selected else "NO_ENCONTRADO", "candidatos": selected}

    def _parent_paths(self, target_id: str) -> list[list[dict[str, Any]]]:
        graph = self._parent_graph
        if graph is None:
            graph = {}
            for recipe in self._all_recipes():
                parent = self._identity(recipe)
                response = dict(self.biblioteca.detalle(parent["escandallo_id"]) or {})
                ingredients = list(((response.get("elaboracion") or {}).get("receta") or {}).get("ingredientes") or [])
                for ingredient in ingredients:
                    child_id = str((ingredient or {}).get("escandallo_hijo_id") or "").strip()
                    if child_id:
                        graph.setdefault(child_id, []).append(parent)
            self._parent_graph = graph
        paths: list[list[dict[str, Any]]] = []
        queue: list[tuple[str, list[dict[str, Any]], set[str]]] = [(target_id, [], {target_id})]
        while queue:
            child_id, path, visited = queue.pop(0)
            if len(path) >= self.MAX_DEPTH:
                continue
            for parent in graph.get(child_id, []):
                parent_id = parent["escandallo_id"]
                if parent_id in visited:
                    continue
                next_path = [*path, parent]
                paths.append(next_path)
                queue.append((parent_id, next_path, {*visited, parent_id}))
        return paths

    def _all_recipes(self) -> list[dict[str, Any]]:
        response = dict(self.biblioteca.listar({"page": 1, "page_size": 100, "tiene_escandallo": "true"}) or {})
        return [dict(item) for item in list((response.get("elaboraciones") or {}).get("items") or [])]

    def _menu_uses(self, escandallo_id: str, limit: int) -> list[dict[str, Any]]:
        response = dict(self.menus.listar({"incluir_archivados": True}) or {})
        uses: list[dict[str, Any]] = []
        for menu in list(response.get("menus") or []):
            menu_ref = {"tipo": "MENU", "menu_id": str(menu.get("id") or ""), "nombre": str(menu.get("nombre") or "")}
            for section in list(menu.get("secciones") or []):
                for line in list((section or {}).get("elaboraciones") or []):
                    if str((line or {}).get("elaboracion_id") or "") == escandallo_id:
                        uses.append({
                            "origen": "MENU", "menu": menu_ref, "menu_id": menu_ref["menu_id"],
                            "nombre": menu_ref["nombre"], "estado": menu.get("estado") or None,
                            "version": menu.get("version"), "seccion": section.get("nombre") or None,
                            "cantidad": line.get("cantidad"), "tipo_relacion": "USO_DIRECTO",
                        })
        return uses[:limit]

    def _production_uses(self, escandallo_id: str, limit: int) -> list[dict[str, Any]]:
        if self.produccion is None:
            return []
        response = dict(self.produccion.consultar("buscar", termino=escandallo_id, limite=limit) or {})
        uses = []
        for row in list(response.get("resultados") or []):
            if str(row.get("receta_id") or "") != escandallo_id:
                continue
            plan = {"tipo": "PRODUCCION", "plan_id": row.get("plan_id"), "nombre": row.get("plan_nombre")}
            uses.append({
                "origen": "PRODUCCION", "plan": plan, "plan_id": row.get("plan_id"),
                "nombre": row.get("plan_nombre"), "estado": row.get("estado_plan"), "fecha": row.get("fecha"),
                "tarea_id": row.get("tarea_id"), "tarea_titulo": row.get("titulo"),
                "tipo_relacion": "USO_DIRECTO",
            })
        return uses[:limit]

    @staticmethod
    def _identity(item: dict[str, Any]) -> dict[str, Any]:
        return {"escandallo_id": str(item.get("id") or item.get("codigo") or ""), "nombre": str(item.get("nombre") or "")}

    @staticmethod
    def _deduplicate(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        seen: set[tuple[Any, ...]] = set()
        for item in items:
            key = (item.get("origen"), item.get("menu_id"), item.get("plan_id"), item.get("tarea_id"), item.get("seccion"))
            if key not in seen:
                seen.add(key)
                output.append(item)
            if len(output) >= limit:
                break
        return output

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in text if not unicodedata.combining(char)).strip().lower()

    @staticmethod
    def _result(state: str, *, elaboracion: dict[str, Any] | None = None,
                candidatos: list[dict[str, Any]] | None = None, menus: list[dict[str, Any]] | None = None,
                produccion: list[dict[str, Any]] | None = None, padres: list[dict[str, Any]] | None = None,
                usos_directos: list[dict[str, Any]] | None = None, usos_indirectos: list[dict[str, Any]] | None = None,
                trazabilidad: list[Any] | None = None) -> dict[str, Any]:
        return {
            "estado": state, "elaboracion": elaboracion, "candidatos": list(candidatos or []),
            "menus": list(menus or []), "produccion": list(produccion or []), "padres": list(padres or []),
            "usos_directos": list(usos_directos or []), "usos_indirectos": list(usos_indirectos or []),
            "eventos": {"estado": "NO_DISPONIBLE_RELACION_CANONICA", "items": [],
                        "motivo": "No existe una relación canónica estable entre Eventos y Menús/Elaboraciones."},
            "trazabilidad": list(trazabilidad or []), "fuente": "biblioteca_menus_produccion_canonicos",
            "solo_lectura": True, "datos_reales_modificados": False,
        }


__all__ = ["HostAIUsoElaboracionReadService"]
