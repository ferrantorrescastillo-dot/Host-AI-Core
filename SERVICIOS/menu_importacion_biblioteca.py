from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.biblioteca_menus_601 import BibliotecaMenus601
from SERVICIOS.borrador_importacion_biblioteca import normalize_text
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from SERVICIOS.repository_initialization_policy import non_persistent_repository_initialization


def _exact(items: list[dict[str, Any]], name: Any, *fields: str) -> list[dict[str, Any]]:
    wanted = normalize_text(name)
    return [
        item for item in items
        if wanted and any(normalize_text(item.get(field)) == wanted for field in fields)
    ]


def _line_name(line: dict[str, Any]) -> str:
    return str(line.get("nombre") or line.get("name") or "").strip()


def _menu_signature(menu: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (normalize_text(line.get("seccion") or "Otros"), normalize_text(_line_name(line)))
        for line in menu.get("componentes") or [] if _line_name(line)
    )


def _canonical_signature(menu: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for section, lines in dict(menu.get("composicion") or {}).items():
        for line in lines or []:
            values.append((normalize_text(section), normalize_text(line.get("referencia"))))
    return tuple(values)


def _source_identity(menu: dict[str, Any]) -> tuple[Any, ...]:
    origin = dict(menu.get("origen") or {})
    return (
        normalize_text(origin.get("source_filename")), normalize_text(origin.get("sheet")),
        origin.get("title_row"), origin.get("escandallo_row"),
        str(menu.get("tipo") or "MENU").upper(), _menu_signature(menu),
    )


def _confirmed_menu_sources(base_dir: Path) -> dict[str, dict[str, Any]]:
    """Reconstruye procedencia MENU601 -> bloque fuente desde sesiones confirmadas (solo lectura)."""
    try:
        payload = json.loads((base_dir / "DATOS/db/biblioteca_importaciones_web.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    sessions = payload.get("sesiones") if isinstance(payload, dict) else {}
    result: dict[str, dict[str, Any]] = {}
    for session in dict(sessions or {}).values():
        if str(session.get("estado") or "") != "CONFIRMADA":
            continue
        created = list((((session.get("preview_global") or {}).get("menus") or {}).get("crear") or []))
        entities = [
            item for item in ((session.get("resultado_confirmacion") or {}).get("entidades") or [])
            if item.get("tipo") == "MENU"
        ]
        draft_menus = list((session.get("borrador") or {}).get("menus") or [])
        by_draft_id = {f"MENU-DRAFT-{index:03d}": item for index, item in enumerate(draft_menus, 1)}
        for entity, projected in zip(entities, created):
            source = by_draft_id.get(str(projected.get("id") or ""))
            if source and entity.get("id"):
                result[str(entity["id"])] = source
    return result


def _canonical_lines(menu: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for section, values in dict(menu.get("composicion") or {}).items():
        for value in values or []:
            lines.append({
                "indice": len(lines) + 1,
                "nombre": str(((value.get("snapshot_referencia") or {}).get("nombre")) or value.get("referencia") or ""),
                "seccion": section, "cantidad": value.get("cantidad") or 1,
                "origen": {}, "estado": "RESUELTA",
                "tipo_referencia": value.get("tipo_referencia"), "referencia": value.get("referencia"),
                "futura": False,
            })
    return lines


def project_menu_imports(
    base_dir: Path,
    menus: list[dict[str, Any]],
    recipes: list[dict[str, Any]],
    decisions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Proyecta candidatos de menú contra el dominio canónico, sin escribir."""
    with non_persistent_repository_initialization():
        library = BibliotecaCulinariaReadService(base_dir)
        products_repo = RepositorioProductosMaestro601(base_dir)
        menu_service = BibliotecaMenus601(base_dir)
    elaborations = list((library.listar({"page_size": 10000}).get("elaboraciones") or {}).get("items") or [])
    products = products_repo.listar_productos()
    canonical_menus = menu_service.repo.listar(incluir_archivados=True)
    confirmed_sources = _confirmed_menu_sources(base_dir)
    recipe_by_name: dict[str, list[dict[str, Any]]] = {}
    for recipe in recipes:
        recipe_by_name.setdefault(normalize_text(recipe.get("title")), []).append(recipe)
    package_names: dict[str, list[tuple[tuple[str, str], ...]]] = {}
    for menu in menus:
        package_names.setdefault(normalize_text(menu.get("nombre")), []).append(_menu_signature(menu))

    decisions_by_id = {
        str(item.get("menu_draft_id") or ""): item
        for item in decisions or [] if isinstance(item, dict)
    }
    projected: list[dict[str, Any]] = []
    projected_keys: set[tuple[str, tuple[tuple[str, str], ...]]] = set()
    for index, source in enumerate(menus, 1):
        menu = deepcopy(source)
        name = str(menu.get("nombre") or "").strip()
        imported_name = name
        kind = str(menu.get("tipo") or "MENU").upper()
        lines_out: list[dict[str, Any]] = []
        reasons: list[str] = []
        for line_index, line in enumerate(menu.get("componentes") or [], 1):
            line_name = _line_name(line)
            resolved: dict[str, Any] | None = None
            drafts = recipe_by_name.get(normalize_text(line_name), [])
            safe_drafts = [item for item in drafts if item.get("proposed_action") != "REQUIERE_REVISION"]
            if len(safe_drafts) == 1:
                draft = safe_drafts[0]
                candidates = draft.get("duplicate_candidates") or []
                canonical_id = None
                if draft.get("proposed_action") in {"REUTILIZAR_EXISTENTE", "SIN_CAMBIOS"} and candidates:
                    canonical_id = candidates[0].get("id") or candidates[0].get("codigo")
                resolved = {
                    "estado": "RESUELTA", "tipo_referencia": "RECETA",
                    "referencia": canonical_id, "receta_draft_id": draft.get("id"),
                    "futura": not bool(canonical_id),
                }
            elif len(drafts) > 1:
                reasons.append(f"Línea ambigua por variantes de receta: {line_name}.")
            else:
                recipe_matches = _exact(elaborations, line_name, "nombre", "codigo", "id")
                product_matches = _exact(products, line_name, "nombre", "codigo", "id")
                if len(recipe_matches) == 1:
                    found = recipe_matches[0]
                    resolved = {"estado": "RESUELTA", "tipo_referencia": "RECETA", "referencia": found.get("id") or found.get("codigo"), "futura": False}
                elif len(product_matches) == 1:
                    found = product_matches[0]
                    resolved = {"estado": "RESUELTA", "tipo_referencia": "PRODUCTO", "referencia": found.get("codigo") or found.get("id"), "futura": False}
                else:
                    reasons.append(f"No existe una identidad canónica inequívoca para: {line_name or '(línea vacía)'}.")
            lines_out.append({
                "indice": line_index, "nombre": line_name,
                "seccion": str(line.get("seccion") or "Otros").strip() or "Otros",
                "cantidad": line.get("cantidad_origen") or 1,
                "origen": deepcopy(line),
                **(resolved or {"estado": "PENDIENTE", "tipo_referencia": None, "referencia": None, "futura": False}),
            })

        same_name_structures = package_names.get(normalize_text(name), [])
        if len(set(same_name_structures)) > 1:
            reasons.append("Hay varios menús del package con el mismo nombre y estructuras diferentes.")
        if kind != "MENU":
            reasons.append(f"El bloque es {kind}, no un menú operativo canónico.")
        if not lines_out:
            reasons.append("El menú no contiene líneas operativas.")

        provenance_matches = [
            item for item in canonical_menus
            if item.get("menu_id") in confirmed_sources
            and _source_identity(confirmed_sources[str(item["menu_id"])]) == _source_identity(menu)
        ]
        resolved_signature = tuple(
            (normalize_text(line["seccion"]), normalize_text(line.get("referencia")))
            for line in lines_out if line.get("estado") == "RESUELTA"
        )
        structural_matches = [
            item for item in canonical_menus
            if len(resolved_signature) == len(lines_out)
            and resolved_signature == _canonical_signature(item)
        ]
        existing = _exact(canonical_menus, name, "nombre", "codigo", "menu_id")
        action = "CREAR"
        canonical_id = None
        if len(provenance_matches) == 1:
            matched = provenance_matches[0]
            canonical_id = matched.get("menu_id")
            name = str(matched.get("nombre") or name)
            lines_out = _canonical_lines(matched)
            reasons = []
            action = "REUTILIZAR"
        elif len(provenance_matches) > 1:
            reasons.append("La procedencia coincide con varios menús canónicos.")
        elif len(structural_matches) == 1:
            matched = structural_matches[0]
            canonical_id = matched.get("menu_id")
            name = str(matched.get("nombre") or name)
            lines_out = _canonical_lines(matched)
            reasons = []
            action = "REUTILIZAR"
        elif len(structural_matches) > 1:
            reasons.append("La firma estructural coincide con varios menús canónicos.")
        elif len(existing) == 1:
            canonical_id = existing[0].get("menu_id")
            if not reasons and resolved_signature == _canonical_signature(existing[0]):
                action = "REUTILIZAR"
            else:
                reasons.append("Ya existe un menú con el mismo nombre pero la estructura no coincide exactamente.")
        elif len(existing) > 1:
            reasons.append("Existen varios menús canónicos con el mismo nombre.")
        if reasons or any(line["estado"] == "PENDIENTE" for line in lines_out):
            action = "PENDIENTE"
        if kind != "MENU" and not lines_out:
            action = "EXCLUIR"
        package_key = (normalize_text(name), _menu_signature(menu))
        reuse_from_same_import = action == "CREAR" and package_key in projected_keys
        if reuse_from_same_import:
            action = "REUTILIZAR"
        elif action == "CREAR":
            projected_keys.add(package_key)

        draft_id = f"MENU-DRAFT-{index:03d}"
        decision = decisions_by_id.get(draft_id) or {}
        final_name = str(decision.get("nombre_final") or name).strip() or name
        line_decisions = {
            int(item.get("line_index") or 0): item
            for item in decision.get("line_decisions") or [] if isinstance(item, dict)
        }
        for line in lines_out:
            selected = line_decisions.get(int(line.get("indice") or 0))
            if not selected:
                continue
            choice = str(selected.get("decision") or "PENDIENTE")
            if choice == "EXCLUIR":
                line.update(estado="CONTEXTO", tipo_referencia=None, referencia=None, futura=False)
            elif choice == "USAR_REFERENCIA":
                line.update(
                    estado="RESUELTA", tipo_referencia=selected.get("tipo_referencia"),
                    referencia=selected.get("referencia"), futura=False,
                )
            else:
                line.update(estado="PENDIENTE", tipo_referencia=None, referencia=None, futura=False)
        resolved_line_reasons = {
            reason
            for line in lines_out if line.get("estado") == "RESUELTA"
            for reason in (
                f"Línea ambigua por variantes de receta: {line.get('nombre') or ''}.",
                f"No existe una identidad canónica inequívoca para: {line.get('nombre') or '(línea vacía)'}.",
            )
        }
        reasons = [reason for reason in reasons if reason not in resolved_line_reasons]
        explicit = str(decision.get("decision") or "PENDIENTE")
        pending_lines = sum(line["estado"] == "PENDIENTE" for line in lines_out)
        if explicit == "EXCLUIR_MENU_DOCUMENTAL":
            action = "EXCLUIR"
        elif explicit == "CREAR_MENU" and not pending_lines:
            action, canonical_id = "CREAR", None
        elif explicit == "REUTILIZAR_MENU" and decision.get("menu_id") and not pending_lines:
            action, canonical_id = "REUTILIZAR", str(decision["menu_id"])
        elif decision:
            action = "PENDIENTE"

        projected.append({
            "id": draft_id, "nombre": final_name, "nombre_importado": imported_name, "tipo": kind,
            "accion": action, "menu_id": canonical_id, "origen": deepcopy(menu.get("origen") or {}),
            "reutilizar_de_misma_importacion": reuse_from_same_import,
            "comensales_base": 1, "lineas": lines_out,
            "lineas_resueltas": sum(line["estado"] == "RESUELTA" for line in lines_out),
            "lineas_pendientes": pending_lines,
            "lineas_contexto": sum(line["estado"] == "CONTEXTO" for line in lines_out),
            "motivos": list(dict.fromkeys(reasons)), "decision": explicit,
        })

    return {
        "crear": [item for item in projected if item["accion"] == "CREAR"],
        "reutilizar": [item for item in projected if item["accion"] == "REUTILIZAR"],
        "actualizar": [],
        "pendientes": [item for item in projected if item["accion"] == "PENDIENTE"],
        "excluidos": [item for item in projected if item["accion"] == "EXCLUIR"],
        "no_soportados": [],
    }


def apply_menu_imports(
    base_dir: Path,
    projection: dict[str, Any],
    recipe_ids: dict[str, str],
    import_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Aplica solo menús seguros mediante BibliotecaMenus601 canónica."""
    with non_persistent_repository_initialization():
        service = BibliotecaMenus601(base_dir)
    actions: list[dict[str, Any]] = []
    entities: list[dict[str, Any]] = []
    for item in projection.get("crear") or []:
        composition: dict[str, list[dict[str, Any]]] = {}
        for line in item.get("lineas") or []:
            reference = line.get("referencia")
            if line.get("futura"):
                reference = recipe_ids.get(normalize_text(line.get("nombre")))
            if not reference:
                raise ValueError(f"Dependencia de menú no resuelta: {line.get('nombre')}.")
            composition.setdefault(str(line.get("seccion") or "Otros"), []).append({
                "tipo_referencia": line.get("tipo_referencia"), "referencia": reference,
                "cantidad": line.get("cantidad") or 1, "orden": int(line.get("indice") or 0),
                "observaciones": "",
            })
        result = service.nuevo_menu({
            "nombre": item["nombre"], "tipo": item.get("tipo") or "MENU",
            "comensales_recomendado": 1, "composicion": composition,
            "observaciones": f"Importado desde {import_id}. Cantidades normalizadas por comensal.",
        })
        if not result.get("ok"):
            raise ValueError(str(result.get("mensaje") or f"No se pudo crear el menú {item['nombre']}."))
        created = result["menu"]
        actions.append({"tipo": "CREAR_MENU", "id": created["menu_id"]})
        entities.append({"tipo": "MENU", "id": created["menu_id"], "nombre": created["nombre"]})
    for item in projection.get("reutilizar") or []:
        existing = service.repo.obtener(str(item.get("menu_id") or item.get("nombre") or ""))
        if not existing:
            raise ValueError(f"Menú a reutilizar no encontrado: {item.get('nombre')}.")
        actions.append({"tipo": "REUTILIZAR_MENU", "id": existing["menu_id"]})
        entities.append({"tipo": "MENU_EXISTENTE", "id": existing["menu_id"], "nombre": existing["nombre"]})
    return actions, entities
