from __future__ import annotations

import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional

from MOTORES.motor_stock import MotorStock
from SERVICIOS.base_datos_local import BaseDatosLocal
from SERVICIOS.escalador_explosion_recetas_556ab import MotorEscaladoExplosion556AB


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_list(path: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("items", "registros", "articulos", "stock", "movimientos"):
            if isinstance(data.get(key), list):
                return [x for x in data[key] if isinstance(x, dict)]
    return []


def _canon_unidad(unidad: str) -> str:
    u = _norm(unidad)
    equivalencias = {
        "kg": "kg", "kgs": "kg", "kilo": "kg", "kilos": "kg", "kilogramo": "kg", "kilogramos": "kg",
        "g": "g", "gr": "g", "gramo": "g", "gramos": "g",
        "l": "l", "lt": "l", "litro": "l", "litros": "l",
        "ml": "ml", "mililitro": "ml", "mililitros": "ml",
        "ud": "u", "uds": "u", "u": "u", "unidad": "u", "unidades": "u", "pax": "u", "racion": "u", "raciones": "u",
    }
    return equivalencias.get(u, u or "u")


def _convertir(cantidad: float, origen: str, destino: str) -> Optional[float]:
    o, d = _canon_unidad(origen), _canon_unidad(destino)
    if o == d:
        return cantidad
    factores = {
        ("kg", "g"): 1000.0, ("g", "kg"): 0.001,
        ("l", "ml"): 1000.0, ("ml", "l"): 0.001,
    }
    factor = factores.get((o, d))
    return cantidad * factor if factor is not None else None


def _codigo(fila: Dict[str, Any]) -> str:
    return str(fila.get("codigo") or fila.get("articulo_id") or fila.get("id") or "").strip()


def _nombre(fila: Dict[str, Any]) -> str:
    return str(fila.get("articulo") or fila.get("nombre") or fila.get("ingrediente") or "").strip()


class CruceStockProduccion556C:
    """Cruza necesidades de producción con inventario usando enlaces canónicos.

    Prioridad de resolución:
    1. ID/código de artículo exacto.
    2. Nombre exacto normalizado.
    3. Nombre contenido único.
    4. Parecido fuerte y no ambiguo.

    La consulta es siempre de solo lectura.
    """

    VERSION = "5.5.6CD.1"

    def __init__(self, base_dir: Path, stock_motor: MotorStock | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.db_dir = self.base_dir / "DATOS" / "db"
        self.motor = MotorEscaladoExplosion556AB(self.base_dir)
        self.stock_motor = stock_motor or MotorStock(BaseDatosLocal(self.base_dir))
        self.stock: List[Dict[str, Any]] = []
        self.articulos = _load_list(self.db_dir / "articulos.json")

        self.stock_por_id: Dict[str, Dict[str, Any]] = {}
        self.stock_por_nombre: Dict[str, Dict[str, Any]] = {}
        self.articulos_por_id = {_codigo(x).casefold(): x for x in self.articulos if _codigo(x)}
        self.articulos_por_nombre = {_norm(_nombre(x)): x for x in self.articulos if _nombre(x)}

    def _refrescar_stock(self) -> None:
        """Lee el mismo agregado canónico que expone la página de Stock."""
        self.stock = list(self.stock_motor.stock_actual().get("items") or [])
        self.stock_por_id = {_codigo(x).casefold(): x for x in self.stock if _codigo(x)}
        self.stock_por_nombre = {_norm(_nombre(x)): x for x in self.stock if _nombre(x)}

    def _resolver_articulo(self, articulo_id: Optional[str], nombre: str) -> tuple[Optional[Dict[str, Any]], str, float]:
        if articulo_id:
            art = self.articulos_por_id.get(str(articulo_id).casefold())
            if art:
                return art, "ARTICULO_ID_EXACTO", 1.0

        n = _norm(nombre)
        if n and n in self.articulos_por_nombre:
            return self.articulos_por_nombre[n], "ARTICULO_NOMBRE_EXACTO", 1.0

        contenidos = [a for k, a in self.articulos_por_nombre.items() if n and (n in k or k in n)]
        if len(contenidos) == 1:
            return contenidos[0], "ARTICULO_NOMBRE_CONTENIDO", 0.92

        puntuados = sorted(
            ((SequenceMatcher(None, n, k).ratio(), a) for k, a in self.articulos_por_nombre.items() if n and k),
            key=lambda x: x[0], reverse=True,
        )
        if puntuados and puntuados[0][0] >= 0.86:
            segundo = puntuados[1][0] if len(puntuados) > 1 else 0.0
            if puntuados[0][0] - segundo >= 0.08:
                return puntuados[0][1], "ARTICULO_NOMBRE_PARECIDO", round(puntuados[0][0], 4)
        return None, "ARTICULO_NO_LOCALIZADO", 0.0

    def _resolver_stock(self, articulo: Optional[Dict[str, Any]], articulo_id: Optional[str], nombre: str) -> tuple[Optional[Dict[str, Any]], str]:
        ids = []
        for value in (articulo_id, _codigo(articulo or {})):
            if value and str(value).casefold() not in ids:
                ids.append(str(value).casefold())
        for code in ids:
            fila = self.stock_por_id.get(code)
            if fila:
                return fila, "STOCK_ID_EXACTO"

        # Si existe una identidad estable, no se degrada a nombre: dos artículos
        # parecidos nunca deben compartir existencias por accidente.
        if ids:
            return None, "SIN_REGISTRO_INVENTARIO"

        nombres = [_nombre(articulo or {}), nombre]
        for value in nombres:
            n = _norm(value)
            if n and n in self.stock_por_nombre:
                return self.stock_por_nombre[n], "STOCK_NOMBRE_EXACTO"

        for value in nombres:
            n = _norm(value)
            if not n:
                continue
            candidatos = [x for k, x in self.stock_por_nombre.items() if n in k or k in n]
            if len(candidatos) == 1:
                return candidatos[0], "STOCK_NOMBRE_CONTENIDO"
        return None, "SIN_REGISTRO_INVENTARIO"

    def _stock_actual(self, fila: Dict[str, Any]) -> tuple[float, str, Optional[Dict[str, Any]]]:
        return max(_float(fila.get("cantidad")), 0.0), "MotorStock.stock_actual", None

    def cruzar(self, termino: str, objetivo: float, unidad_objetivo: str = "personas") -> Dict[str, Any]:
        self._refrescar_stock()
        explosion = self.motor.explotar(termino, objetivo, unidad_objetivo)
        lineas: List[Dict[str, Any]] = []
        incidencias = 0
        sin_inventario = 0
        sin_articulo = 0

        for ing in explosion["ingredientes_finales"]:
            nombre_ing = str(ing.get("nombre") or "Ingrediente")
            articulo_id_ing = ing.get("articulo_id")
            articulo, metodo_art, confianza_art = self._resolver_articulo(articulo_id_ing, nombre_ing)
            fila, metodo_stock = self._resolver_stock(articulo, articulo_id_ing, nombre_ing)
            requerido = _float(ing.get("cantidad"))
            unidad_req = _canon_unidad(ing.get("unidad") or "u")

            base = {
                "nombre": nombre_ing,
                "articulo_id": _codigo(articulo or {}) or articulo_id_ing,
                "articulo_nombre": _nombre(articulo or {}) or nombre_ing,
                "requerido": round(requerido, 4),
                "unidad": unidad_req,
                "metodo_enlace_articulo": metodo_art,
                "confianza_enlace_articulo": confianza_art,
                "metodo_enlace_stock": metodo_stock,
                "fuente_stock": None,
                "ultimo_movimiento": None,
            }

            if articulo is None:
                base.update({
                    "disponible": 0.0, "faltante": round(requerido, 4), "restante": 0.0,
                    "estado": "ARTICULO_NO_LOCALIZADO", "stock_localizado": False,
                })
                lineas.append(base)
                incidencias += 1
                sin_articulo += 1
                continue

            if fila is None:
                base.update({
                    "disponible": 0.0, "faltante": round(requerido, 4), "restante": 0.0,
                    "estado": "ARTICULO_SIN_INVENTARIO", "stock_localizado": False,
                    "proveedor": articulo.get("proveedor"), "ubicacion": None,
                })
                lineas.append(base)
                incidencias += 1
                sin_inventario += 1
                continue

            unidad_stock = _canon_unidad(fila.get("unidad") or articulo.get("unidad") or unidad_req)
            disponible_stock, fuente_stock, ultimo_movimiento = self._stock_actual(fila)
            convertido = _convertir(disponible_stock, unidad_stock, unidad_req)
            base["fuente_stock"] = fuente_stock
            base["ultimo_movimiento"] = ultimo_movimiento

            if convertido is None:
                base.update({
                    "disponible": round(disponible_stock, 4), "unidad_stock": unidad_stock,
                    "faltante": round(requerido, 4), "restante": 0.0,
                    "estado": "UNIDAD_INCOMPATIBLE", "stock_localizado": True,
                    "proveedor": fila.get("proveedor") or articulo.get("proveedor"),
                    "ubicacion": fila.get("ubicacion"),
                })
                lineas.append(base)
                incidencias += 1
                continue

            faltante = max(requerido - convertido, 0.0)
            restante = max(convertido - requerido, 0.0)
            minimo = _float(fila.get("stock_minimo"), 0.0)
            minimo_conv = _convertir(minimo, unidad_stock, unidad_req) if minimo else 0.0

            if convertido <= 0:
                estado = "SIN_STOCK"
                incidencias += 1
            elif faltante > 0:
                estado = "STOCK_INSUFICIENTE"
                incidencias += 1
            elif minimo_conv and restante < minimo_conv:
                estado = "CUBRE_PERO_BAJO_MINIMO"
            else:
                estado = "STOCK_CORRECTO"

            base.update({
                "disponible": round(convertido, 4), "faltante": round(faltante, 4),
                "restante": round(restante, 4), "stock_minimo_post": round(minimo_conv or 0.0, 4),
                "estado": estado, "stock_localizado": True,
                "proveedor": fila.get("proveedor") or articulo.get("proveedor"),
                "ubicacion": fila.get("ubicacion"),
            })
            lineas.append(base)

        return {
            "version": self.VERSION,
            "receta": explosion["receta"], "objetivo": objetivo, "unidad_objetivo": unidad_objetivo,
            "lineas": lineas, "total_lineas": len(lineas), "total_faltantes": incidencias,
            "total_sin_registro_stock": sin_inventario, "total_articulos_no_localizados": sin_articulo,
            "produccion_viable": incidencias == 0, "explosion": explosion,
            "fuentes": ["DATOS/db/articulos.json", "MotorStock.stock_actual"],
            "solo_lectura": True, "datos_reales_modificados": False,
        }


def formatear_cruce_stock_556c(resultado: Dict[str, Any]) -> str:
    lines = [
        f"CRUCE PRODUCCIÓN–STOCK — {resultado['receta']}",
        f"- Objetivo: {resultado['objetivo']:g} {resultado['unidad_objetivo']}",
        f"- Estado general: {'VIABLE CON STOCK ACTUAL' if resultado['produccion_viable'] else 'FALTAN PRODUCTOS O REGISTROS DE INVENTARIO'}",
        "", "NECESIDADES Y EXISTENCIAS",
    ]
    for x in resultado["lineas"]:
        lines.append(
            f"- {x['nombre']}: necesario {x['requerido']:g} {x['unidad']} | "
            f"disponible {x['disponible']:g} {x.get('unidad', '')} | "
            f"faltante {x['faltante']:g} {x['unidad']} | {x['estado']}"
        )
        lines.append(
            f"  Enlace: {x.get('metodo_enlace_articulo')} / {x.get('metodo_enlace_stock')}"
            + (f" | Fuente: {x.get('fuente_stock')}" if x.get("fuente_stock") else "")
        )
    lines += [
        "", f"- Líneas con faltante o incidencia: {resultado['total_faltantes']}/{resultado['total_lineas']}",
        f"- Artículos existentes sin inventario: {resultado.get('total_sin_registro_stock', 0)}",
        f"- Ingredientes sin artículo localizado: {resultado.get('total_articulos_no_localizados', 0)}",
        "", "LECTURA DE SEGUNDO JEFE",
        "- ARTICULO_SIN_INVENTARIO significa que el artículo existe, pero todavía no tiene una existencia inicial cargada.",
        "- STOCK_INSUFICIENTE significa que existe inventario, pero no cubre la producción solicitada.",
        "", "SEGURIDAD", "- Comparación en modo solo lectura.",
        "- No se ha descontado stock ni creado compras.", "- Datos reales modificados: NO.",
    ]
    return "\n".join(lines)


__all__ = ["CruceStockProduccion556C", "formatear_cruce_stock_556c"]
