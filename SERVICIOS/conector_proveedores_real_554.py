from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def _load_list(path: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []
    return [row for row in data if isinstance(row, dict)] if isinstance(data, list) else []


def es_consulta_proveedor_real_554(texto: str) -> bool:
    t = _norm(texto)
    return any(x in t for x in ("quien vende", "que proveedor vende", "proveedores venden", "proveedor de", "donde compro"))


def extraer_articulo_proveedor_554(texto: str) -> str:
    t = _norm(texto).replace("?", "")
    patrones = (
        r"quien vende (.+)$",
        r"que proveedores? venden? (.+)$",
        r"proveedores? de (.+)$",
        r"donde compro (.+)$",
    )
    for patron in patrones:
        match = re.search(patron, t)
        if match:
            return match.group(1).strip(" .")
    return ""


class ConectorProveedoresReal554:
    """Relaciona artículos con proveedores y precios existentes en solo lectura."""

    VERSION = "5.5.4"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.db_dir = self.base_dir / "DATOS" / "db"

    def consultar(self, termino: str) -> Dict[str, Any]:
        t = _norm(termino)
        articulos = _load_list(self.db_dir / "articulos.json")
        stock = _load_list(self.db_dir / "stock_inicial.json")
        proveedores = _load_list(self.db_dir / "proveedores.json")
        precios = _load_list(self.db_dir / "precios.json")

        matches = [a for a in articulos if t in _norm(a.get("nombre") or a.get("articulo"))]
        resultados: List[Dict[str, Any]] = []
        for art in matches:
            codigo = art.get("codigo") or art.get("articulo_id")
            nombre = art.get("nombre") or art.get("articulo")
            proveedor_nombre = art.get("proveedor")
            stock_row = next((s for s in stock if s.get("codigo") == codigo or _norm(s.get("articulo")) == _norm(nombre)), {})
            proveedor_nombre = proveedor_nombre or stock_row.get("proveedor")

            proveedor_reg = next((p for p in proveedores if _norm(p.get("nombre")) == _norm(proveedor_nombre)), {})
            hist = [p for p in precios if (codigo and p.get("articulo_id") == codigo) or _norm(p.get("nombre")) == _norm(nombre)]
            hist.sort(key=lambda p: str(p.get("fecha") or p.get("creado_en") or ""))
            ultimo_precio = hist[-1] if hist else {}
            precio = ultimo_precio.get("precio_unitario", art.get("precio"))
            unidad = ultimo_precio.get("unidad") or stock_row.get("unidad") or art.get("unidad") or "u"

            if proveedor_nombre:
                resultados.append({
                    "articulo": nombre,
                    "codigo_articulo": codigo,
                    "proveedor": proveedor_nombre,
                    "codigo_proveedor": proveedor_reg.get("codigo"),
                    "estado_proveedor": proveedor_reg.get("estado", "registrado en artículo"),
                    "precio": precio,
                    "unidad": unidad,
                    "fecha_precio": ultimo_precio.get("fecha"),
                    "origen_relacion": "articulos/stock_inicial",
                })

        # Evita duplicados exactos artículo-proveedor.
        vistos = set()
        unicos = []
        for r in resultados:
            key = (_norm(r["articulo"]), _norm(r["proveedor"]))
            if key not in vistos:
                vistos.add(key)
                unicos.append(r)

        return {
            "ok": True,
            "encontrado": bool(unicos),
            "termino": termino,
            "coincidencias": unicos,
            "solo_lectura": True,
            "fuentes": ["DATOS/db/articulos.json", "DATOS/db/stock_inicial.json", "DATOS/db/proveedores.json", "DATOS/db/precios.json"],
        }


def formatear_proveedores_real_554(resultado: Dict[str, Any]) -> str:
    termino = resultado.get("termino", "")
    if not resultado.get("encontrado"):
        return (
            f"PROVEEDORES REALES: {termino}\n"
            "- He localizado el término, pero no una relación artículo-proveedor válida.\n\n"
            "SIGUIENTE PASO PROFESIONAL\n"
            "- Revisa el nombre exacto del artículo o asigna un proveedor habitual en su ficha.\n\n"
            "SEGURIDAD\n- Consulta en modo solo lectura.\n- Datos reales modificados: NO."
        )

    lines = [f"PROVEEDORES REALES: {termino}", f"Coincidencias: {len(resultado.get('coincidencias', []))}", ""]
    for item in resultado.get("coincidencias", []):
        lines.append(str(item.get("articulo")))
        lines.append(f"- Proveedor habitual: {item.get('proveedor')}")
        if item.get("precio") is not None:
            lines.append(f"- Precio registrado: {item.get('precio')} €/{item.get('unidad')}")
        if item.get("fecha_precio"):
            lines.append(f"- Fecha del precio: {item.get('fecha_precio')}")
        lines.append(f"- Estado: {item.get('estado_proveedor')}")
        lines.append("")

    lines.extend([
        "LECTURA DE SEGUNDO JEFE",
        "- Muestro únicamente relaciones y precios existentes; no invento proveedores alternativos.",
        "",
        "SEGURIDAD",
        "- Consulta en modo solo lectura.",
        "- Datos reales modificados: NO.",
    ])
    return "\n".join(lines)


def procesar_consulta_proveedores_real_554(texto: str, base_dir: Path) -> Dict[str, Any]:
    if not es_consulta_proveedor_real_554(texto):
        return {"gestionado": False}
    termino = extraer_articulo_proveedor_554(texto)
    datos = ConectorProveedoresReal554(base_dir).consultar(termino)
    return {
        "gestionado": True,
        "ok": True,
        "version": "5.5.4",
        "intencion": "consultar_proveedores_reales",
        "estado": "proveedores_reales_consultados",
        "mensaje": formatear_proveedores_real_554(datos),
        "datos": datos,
        "pasos": [],
    }


__all__ = [
    "ConectorProveedoresReal554",
    "es_consulta_proveedor_real_554",
    "extraer_articulo_proveedor_554",
    "formatear_proveedores_real_554",
    "procesar_consulta_proveedores_real_554",
]
