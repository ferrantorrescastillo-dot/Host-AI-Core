from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

from SERVICIOS.simulador_importacion_menus_i13411 import _norm


def fingerprint_incidencia(inc: dict[str, Any]) -> tuple[str, str, str, str, str]:
    """Identidad estable y reutilizable de una incidencia del importador."""
    return (
        str(inc.get("codigo") or ""),
        _norm(inc.get("menu")),
        _norm(inc.get("plato")),
        _norm(inc.get("referencia")),
        str(inc.get("severidad") or ""),
    )


def filtrar_incidencias(
    incidencias: Iterable[dict[str, Any]],
    *,
    severidad: str | None = None,
    codigo: str | None = None,
    menu: str | None = None,
) -> list[tuple[int, dict[str, Any]]]:
    sev = str(severidad or "").upper()
    cod = str(codigo or "").upper()
    men = _norm(menu)
    salida: list[tuple[int, dict[str, Any]]] = []
    for i, inc in enumerate(incidencias, 1):
        if sev and str(inc.get("severidad") or "").upper() != sev:
            continue
        if cod and str(inc.get("codigo") or "").upper() != cod:
            continue
        if men and men not in _norm(inc.get("menu")):
            continue
        salida.append((i, inc))
    return salida


def agrupar_incidencias(
    incidencias: Iterable[dict[str, Any]],
    *,
    campo: str,
    valor_vacio: str,
) -> list[dict[str, Any]]:
    grupos: dict[str, list[int]] = defaultdict(list)
    severidades: dict[str, Counter[str]] = defaultdict(Counter)
    for i, inc in enumerate(incidencias, 1):
        clave = str(inc.get(campo) or valor_vacio)
        grupos[clave].append(i)
        severidades[clave][str(inc.get("severidad") or "INFO")] += 1
    return [
        {
            campo: clave,
            "cantidad": len(indices),
            "indices": indices,
            "errores": severidades[clave].get("ERROR", 0),
            "avisos": severidades[clave].get("AVISO", 0),
        }
        for clave, indices in sorted(grupos.items(), key=lambda x: (-len(x[1]), _norm(x[0])))
    ]


def coincidencias_exactas(
    catalogo: Iterable[dict[str, Any]],
    texto: str,
    campos: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Coincidencia exacta, normalizada, única por identidad de catálogo."""
    q = _norm(texto)
    if not q:
        return []
    encontrados: list[dict[str, Any]] = []
    vistos: set[str] = set()
    for item in catalogo:
        if any(_norm(item.get(campo)) == q for campo in campos):
            key = str(
                item.get("receta_id")
                or item.get("codigo")
                or item.get("id")
                or _norm(item.get("nombre") or item.get("articulo"))
            )
            if key not in vistos:
                vistos.add(key)
                encontrados.append(item)
    return encontrados
