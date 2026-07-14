from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional


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


def extraer_articulo_stock_553(texto: str) -> str:
    t = _norm(texto).replace("?", "")
    patrones = (
        r"(?:que|cuanto) stock (?:tienes|hay|queda|tenemos) (?:de )?(.+)$",
        r"stock (?:actual )?(?:de )?(.+)$",
        r"existencias (?:de )?(.+)$",
        r"cuanto queda (?:de )?(.+)$",
    )
    for patron in patrones:
        match = re.search(patron, t)
        if match:
            return match.group(1).strip(" .")
    return ""


def es_consulta_stock_real_553(texto: str) -> bool:
    t = _norm(texto)
    return any(token in t for token in ("stock", "existencias", "cuanto queda")) and bool(extraer_articulo_stock_553(texto))


class ConectorStockReal553:
    """Consulta el inventario real sin modificar archivos."""

    VERSION = "5.5.3"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.db_dir = self.base_dir / "DATOS" / "db"

    def consultar(self, termino: str) -> Dict[str, Any]:
        termino_n = _norm(termino)
        stock = _load_list(self.db_dir / "stock_inicial.json")
        movimientos = _load_list(self.db_dir / "stock_movimientos.json")
        articulos = _load_list(self.db_dir / "articulos.json")

        candidatos = [r for r in stock if termino_n in _norm(r.get("articulo") or r.get("nombre"))]
        if not candidatos:
            return {
                "ok": True,
                "encontrado": False,
                "termino": termino,
                "coincidencias": [],
                "fuentes": ["DATOS/db/stock_inicial.json", "DATOS/db/stock_movimientos.json"],
                "solo_lectura": True,
            }

        resultados: List[Dict[str, Any]] = []
        for fila in candidatos:
            codigo = fila.get("codigo") or fila.get("articulo_id")
            nombre = fila.get("articulo") or fila.get("nombre")
            relacionados = [
                m for m in movimientos
                if (codigo and (m.get("codigo") == codigo or m.get("articulo_id") == codigo))
                or _norm(m.get("articulo") or m.get("nombre")) == _norm(nombre)
            ]
            relacionados.sort(key=lambda m: str(m.get("fecha_hora") or m.get("creado_en") or ""))
            ultimo = relacionados[-1] if relacionados else None

            stock_actual = fila.get("stock_actual", fila.get("cantidad", 0))
            fuente_stock = "stock_inicial"
            if ultimo and ultimo.get("stock_despues") is not None:
                stock_actual = ultimo.get("stock_despues")
                fuente_stock = "ultimo_movimiento"

            articulo = next((a for a in articulos if a.get("codigo") == codigo), {})
            minimo = fila.get("stock_minimo", 0) or 0
            try:
                actual_num = float(stock_actual or 0)
                minimo_num = float(minimo or 0)
            except (TypeError, ValueError):
                actual_num, minimo_num = 0.0, 0.0

            if actual_num <= 0:
                estado = "ROTURA DE STOCK"
                gravedad = "CRÍTICO"
            elif minimo_num and actual_num <= minimo_num:
                estado = "EN MÍNIMO"
                gravedad = "ALTO"
            elif minimo_num and actual_num <= minimo_num * 1.5:
                estado = "STOCK AJUSTADO"
                gravedad = "MEDIO"
            else:
                estado = "STOCK CORRECTO"
                gravedad = "BAJO"

            resultados.append({
                "codigo": codigo,
                "articulo": nombre,
                "stock_actual": actual_num,
                "stock_minimo": minimo_num,
                "unidad": fila.get("unidad") or articulo.get("unidad") or "u",
                "ubicacion": fila.get("ubicacion") or "sin ubicación",
                "proveedor": fila.get("proveedor") or articulo.get("proveedor") or "sin proveedor",
                "precio": articulo.get("precio"),
                "estado": estado,
                "gravedad": gravedad,
                "fuente_stock": fuente_stock,
                "ultimo_movimiento": ultimo,
            })

        return {
            "ok": True,
            "encontrado": True,
            "termino": termino,
            "coincidencias": resultados,
            "fuentes": ["DATOS/db/stock_inicial.json", "DATOS/db/stock_movimientos.json", "DATOS/db/articulos.json"],
            "solo_lectura": True,
        }


def formatear_stock_real_553(resultado: Dict[str, Any]) -> str:
    termino = resultado.get("termino", "")
    if not resultado.get("encontrado"):
        return (
            f"STOCK REAL: {termino}\n"
            "- No he localizado ese artículo en el inventario activo.\n\n"
            "SIGUIENTE PASO PROFESIONAL\n"
            "- Comprueba el nombre exacto o busca primero el artículo por nombre.\n\n"
            "SEGURIDAD\n- Consulta en modo solo lectura.\n- Datos reales modificados: NO."
        )

    lines = [f"STOCK REAL: {termino}", ""]
    for item in resultado.get("coincidencias", []):
        lines.extend([
            str(item.get("articulo", "Artículo")),
            f"- Stock actual: {item.get('stock_actual'):g} {item.get('unidad')}",
            f"- Stock mínimo: {item.get('stock_minimo'):g} {item.get('unidad')}",
            f"- Estado: {item.get('estado')} ({item.get('gravedad')})",
            f"- Ubicación: {item.get('ubicacion')}",
            f"- Proveedor habitual: {item.get('proveedor')}",
        ])
        if item.get("precio") is not None:
            lines.append(f"- Precio registrado: {item.get('precio')} €/{item.get('unidad')}")
        ultimo = item.get("ultimo_movimiento") or {}
        if ultimo:
            lines.append(f"- Último movimiento: {ultimo.get('tipo', 'movimiento')} {ultimo.get('cantidad', '')} {ultimo.get('unidad', '')}")
        lines.append("")

    lines.extend([
        "LECTURA DE SEGUNDO JEFE",
        "- El stock mostrado procede del inventario activo y, cuando existe, del último movimiento registrado.",
        "",
        "SEGURIDAD",
        "- Consulta en modo solo lectura.",
        "- Datos reales modificados: NO.",
    ])
    return "\n".join(lines)


def procesar_consulta_stock_real_553(texto: str, base_dir: Path) -> Dict[str, Any]:
    if not es_consulta_stock_real_553(texto):
        return {"gestionado": False}
    termino = extraer_articulo_stock_553(texto)
    datos = ConectorStockReal553(base_dir).consultar(termino)
    return {
        "gestionado": True,
        "ok": True,
        "version": "5.5.3",
        "intencion": "consultar_stock_real",
        "estado": "stock_real_consultado",
        "mensaje": formatear_stock_real_553(datos),
        "datos": datos,
        "pasos": [],
    }


__all__ = [
    "ConectorStockReal553",
    "es_consulta_stock_real_553",
    "extraer_articulo_stock_553",
    "formatear_stock_real_553",
    "procesar_consulta_stock_real_553",
]
