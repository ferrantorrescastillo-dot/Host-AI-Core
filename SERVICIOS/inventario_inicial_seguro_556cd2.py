from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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


def _codigo(fila: Dict[str, Any]) -> str:
    return str(fila.get("codigo") or fila.get("articulo_id") or fila.get("id") or "").strip()


def _nombre(fila: Dict[str, Any]) -> str:
    return str(fila.get("articulo") or fila.get("nombre") or "").strip()


def _canon_unidad(unidad: Any) -> str:
    u = _norm(unidad)
    mapa = {
        "kg": "kg", "kgs": "kg", "kilo": "kg", "kilos": "kg", "kilogramo": "kg", "kilogramos": "kg",
        "g": "g", "gr": "g", "gramo": "g", "gramos": "g",
        "l": "l", "lt": "l", "litro": "l", "litros": "l",
        "ml": "ml", "mililitro": "ml", "mililitros": "ml",
        "u": "u", "ud": "u", "uds": "u", "unidad": "u", "unidades": "u",
    }
    return mapa.get(u, u or "u")


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _load_list(path: Path) -> List[Dict[str, Any]]:
    data = _load_json(path, [])
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("items", "registros", "articulos", "stock", "movimientos"):
            if isinstance(data.get(key), list):
                return [x for x in data[key] if isinstance(x, dict)]
    return []


def _atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.stem + "_", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _backup(path: Path, backup_dir: Path, etiqueta: str) -> Optional[str]:
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destino = backup_dir / f"{path.stem}_{etiqueta}_{stamp}{path.suffix}.bak"
    shutil.copy2(path, destino)
    return str(destino)


class InventarioInicialSeguro556CD2:
    """Alta segura de inventario inicial sin inventar existencias.

    - Nunca crea cantidades por defecto.
    - El stock mínimo es opcional; si se omite usa una recomendación por unidad.
    - La escritura requiere confirmación explícita.
    - Cada confirmación genera copias de seguridad y un movimiento trazable.
    """

    VERSION = "5.5.6CD.2"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.db_dir = self.base_dir / "DATOS" / "db"
        self.config_dir = self.base_dir / "DATOS" / "config"
        self.backup_dir = self.db_dir / "backups"
        self.articulos_path = self.db_dir / "articulos.json"
        self.stock_path = self.db_dir / "stock_inicial.json"
        self.movimientos_path = self.db_dir / "stock_movimientos.json"
        self.minimos_path = self.config_dir / "stock_minimos_defecto_556cd2.json"

        self.articulos = _load_list(self.articulos_path)
        self.stock = _load_list(self.stock_path)
        self.movimientos = _load_list(self.movimientos_path)
        self.minimos = self._cargar_minimos()

        self.articulos_por_id = {_codigo(x).casefold(): x for x in self.articulos if _codigo(x)}
        self.articulos_por_nombre = {_norm(_nombre(x)): x for x in self.articulos if _nombre(x)}
        self.stock_por_id = {_codigo(x).casefold(): x for x in self.stock if _codigo(x)}
        self.stock_por_nombre = {_norm(_nombre(x)): x for x in self.stock if _nombre(x)}

    def _cargar_minimos(self) -> Dict[str, Any]:
        data = _load_json(self.minimos_path, {})
        if not isinstance(data, dict):
            data = {}
        por_unidad = data.get("por_unidad") if isinstance(data.get("por_unidad"), dict) else {}
        return {
            "por_unidad": {
                "kg": _float(por_unidad.get("kg"), 2.0),
                "l": _float(por_unidad.get("l"), 2.0),
                "u": _float(por_unidad.get("u"), 10.0),
                "g": _float(por_unidad.get("g"), 500.0),
                "ml": _float(por_unidad.get("ml"), 500.0),
            },
            "por_familia": data.get("por_familia") if isinstance(data.get("por_familia"), dict) else {},
        }

    def _resolver_articulo(self, termino: str) -> Tuple[Optional[Dict[str, Any]], str, float, List[Dict[str, Any]]]:
        raw = str(termino or "").strip()
        if not raw:
            return None, "TERMINO_VACIO", 0.0, []
        by_id = self.articulos_por_id.get(raw.casefold())
        if by_id:
            return by_id, "ID_EXACTO", 1.0, []
        n = _norm(raw)
        exact = self.articulos_por_nombre.get(n)
        if exact:
            return exact, "NOMBRE_EXACTO", 1.0, []

        contenidos = [a for k, a in self.articulos_por_nombre.items() if n and (n in k or k in n)]
        if len(contenidos) == 1:
            return contenidos[0], "NOMBRE_CONTENIDO", 0.93, []
        if len(contenidos) > 1:
            return None, "AMBIGUO", 0.0, contenidos[:10]

        scored = sorted(
            ((SequenceMatcher(None, n, k).ratio(), a) for k, a in self.articulos_por_nombre.items() if n and k),
            key=lambda x: x[0], reverse=True,
        )
        if scored and scored[0][0] >= 0.86:
            second = scored[1][0] if len(scored) > 1 else 0.0
            if scored[0][0] - second >= 0.08:
                return scored[0][1], "NOMBRE_PARECIDO", round(scored[0][0], 4), []
            return None, "AMBIGUO", 0.0, [a for _, a in scored[:5]]
        return None, "NO_LOCALIZADO", 0.0, []

    def _registro_stock_existente(self, articulo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        code = _codigo(articulo).casefold()
        if code and code in self.stock_por_id:
            return self.stock_por_id[code]
        return self.stock_por_nombre.get(_norm(_nombre(articulo)))

    def _minimo_recomendado(self, articulo: Dict[str, Any], unidad: str) -> float:
        familia = _norm(articulo.get("familia"))
        por_familia = self.minimos.get("por_familia", {})
        for key, value in por_familia.items():
            if _norm(key) == familia:
                return max(_float(value), 0.0)
        return max(_float(self.minimos.get("por_unidad", {}).get(unidad)), 0.0)

    def proponer(
        self,
        termino: str,
        cantidad: float,
        unidad: Optional[str] = None,
        ubicacion: Optional[str] = None,
        stock_minimo: Optional[float] = None,
    ) -> Dict[str, Any]:
        articulo, metodo, confianza, candidatos = self._resolver_articulo(termino)
        if articulo is None:
            return {
                "version": self.VERSION, "ok": False, "estado": metodo,
                "termino": termino,
                "candidatos": [{"codigo": _codigo(x), "nombre": _nombre(x)} for x in candidatos],
                "datos_reales_modificados": False,
            }

        cantidad = _float(cantidad, -1.0)
        if cantidad < 0:
            return {
                "version": self.VERSION, "ok": False, "estado": "CANTIDAD_INVALIDA",
                "articulo": _nombre(articulo), "datos_reales_modificados": False,
            }

        existing = self._registro_stock_existente(articulo)
        if existing is not None:
            return {
                "version": self.VERSION, "ok": False, "estado": "INVENTARIO_YA_EXISTE",
                "articulo": _nombre(articulo), "codigo": _codigo(articulo),
                "stock_actual": _float(existing.get("stock_actual", existing.get("cantidad", 0))),
                "unidad": _canon_unidad(existing.get("unidad") or articulo.get("unidad")),
                "datos_reales_modificados": False,
            }

        unidad_final = _canon_unidad(unidad or articulo.get("unidad") or "u")
        minimo = self._minimo_recomendado(articulo, unidad_final) if stock_minimo is None else max(_float(stock_minimo), 0.0)
        ubicacion_final = str(ubicacion or articulo.get("ubicacion") or "SIN_UBICACION").strip()
        propuesta = {
            "codigo": _codigo(articulo),
            "articulo_id": _codigo(articulo),
            "articulo": _nombre(articulo),
            "nombre": _nombre(articulo),
            "unidad": unidad_final,
            "stock_actual": round(cantidad, 4),
            "cantidad": round(cantidad, 4),
            "stock_minimo": round(minimo, 4),
            "ubicacion": ubicacion_final,
            "proveedor": articulo.get("proveedor"),
            "origen": "INVENTARIO_INICIAL_5.5.6CD.2",
        }
        return {
            "version": self.VERSION, "ok": True, "estado": "PROPUESTA_LISTA",
            "metodo_enlace": metodo, "confianza_enlace": confianza,
            "propuesta": propuesta,
            "advertencia": "El stock actual procede de la cantidad indicada por el usuario; no se ha inventado.",
            "requiere_confirmacion": True, "datos_reales_modificados": False,
        }

    def confirmar(self, propuesta: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(propuesta, dict) or not propuesta.get("codigo") or not propuesta.get("articulo"):
            return {"version": self.VERSION, "ok": False, "estado": "PROPUESTA_INVALIDA", "datos_reales_modificados": False}

        # Recarga justo antes de escribir para evitar trabajar con una versión obsoleta.
        stock = _load_list(self.stock_path)
        movimientos = _load_list(self.movimientos_path)
        code = str(propuesta.get("codigo")).casefold()
        name = _norm(propuesta.get("articulo"))
        for fila in stock:
            if (_codigo(fila).casefold() == code and code) or (_norm(_nombre(fila)) == name and name):
                return {
                    "version": self.VERSION, "ok": False, "estado": "INVENTARIO_YA_EXISTE",
                    "articulo": propuesta.get("articulo"), "datos_reales_modificados": False,
                }

        backup_stock = _backup(self.stock_path, self.backup_dir, "antes_inventario_inicial")
        backup_mov = _backup(self.movimientos_path, self.backup_dir, "antes_inventario_inicial")
        now = datetime.now(timezone.utc).isoformat()
        registro = dict(propuesta)
        registro["actualizado_en"] = now
        stock.append(registro)
        movimiento = {
            "codigo": propuesta.get("codigo"),
            "articulo_id": propuesta.get("articulo_id") or propuesta.get("codigo"),
            "articulo": propuesta.get("articulo"),
            "tipo": "inventario_inicial",
            "cantidad": propuesta.get("stock_actual"),
            "unidad": propuesta.get("unidad"),
            "stock_antes": 0.0,
            "stock_despues": propuesta.get("stock_actual"),
            "ubicacion": propuesta.get("ubicacion"),
            "fecha_hora": now,
            "origen": "HOST_AI_5.5.6CD.2",
        }
        movimientos.append(movimiento)

        _atomic_write_json(self.stock_path, stock)
        _atomic_write_json(self.movimientos_path, movimientos)
        return {
            "version": self.VERSION, "ok": True, "estado": "INVENTARIO_INICIAL_CREADO",
            "articulo": propuesta.get("articulo"), "codigo": propuesta.get("codigo"),
            "stock_actual": propuesta.get("stock_actual"), "unidad": propuesta.get("unidad"),
            "stock_minimo": propuesta.get("stock_minimo"), "ubicacion": propuesta.get("ubicacion"),
            "copias_seguridad": [x for x in (backup_stock, backup_mov) if x],
            "movimiento_creado": movimiento,
            "datos_reales_modificados": True,
        }

    def listar_sin_inventario(self, limite: int = 100) -> Dict[str, Any]:
        faltantes = []
        for articulo in self.articulos:
            if self._registro_stock_existente(articulo) is None:
                unidad = _canon_unidad(articulo.get("unidad") or "u")
                faltantes.append({
                    "codigo": _codigo(articulo), "nombre": _nombre(articulo), "unidad": unidad,
                    "stock_minimo_recomendado": self._minimo_recomendado(articulo, unidad),
                    "familia": articulo.get("familia"), "proveedor": articulo.get("proveedor"),
                })
        return {
            "version": self.VERSION, "total_articulos": len(self.articulos),
            "con_inventario": len(self.articulos) - len(faltantes), "sin_inventario": len(faltantes),
            "articulos": faltantes[:max(int(limite), 0)],
            "datos_reales_modificados": False,
        }


def formatear_propuesta_556cd2(resultado: Dict[str, Any]) -> str:
    if not resultado.get("ok"):
        estado = resultado.get("estado")
        if estado == "AMBIGUO":
            lines = ["INVENTARIO INICIAL", "- He encontrado varios artículos posibles:"]
            for i, x in enumerate(resultado.get("candidatos", []), 1):
                lines.append(f"  {i}. {x.get('nombre')} [{x.get('codigo')}]")
            lines += ["- Repite la orden con el nombre o código exacto.", "", "SEGURIDAD", "- Datos reales modificados: NO."]
            return "\n".join(lines)
        if estado == "INVENTARIO_YA_EXISTE":
            return (
                "INVENTARIO INICIAL\n"
                f"- {resultado.get('articulo')} ya tiene inventario: {resultado.get('stock_actual', 0):g} {resultado.get('unidad', '')}.\n"
                "- No se ha sobrescrito. Los ajustes posteriores deben registrarse como movimientos.\n\n"
                "SEGURIDAD\n- Datos reales modificados: NO."
            )
        return f"INVENTARIO INICIAL\n- No se puede preparar la propuesta: {estado}.\n\nSEGURIDAD\n- Datos reales modificados: NO."

    p = resultado["propuesta"]
    return "\n".join([
        "PROPUESTA DE INVENTARIO INICIAL",
        f"- Artículo: {p['articulo']} [{p['codigo']}]",
        f"- Stock actual declarado: {p['stock_actual']:g} {p['unidad']}",
        f"- Stock mínimo recomendado: {p['stock_minimo']:g} {p['unidad']}",
        f"- Ubicación: {p['ubicacion']}",
        f"- Proveedor habitual: {p.get('proveedor') or 'NO DEFINIDO'}",
        "",
        "CRITERIO",
        "- La cantidad actual nunca se inventa: procede de la cifra indicada.",
        "- El mínimo es configurable y no se confunde con el stock disponible.",
        "",
        "CONFIRMACIÓN NECESARIA",
        "- Vista previa: todavía no se ha escrito nada.",
        "- Repite el comando con --confirmar para crear el inventario inicial.",
        "- Datos reales modificados: NO.",
    ])


def formatear_confirmacion_556cd2(resultado: Dict[str, Any]) -> str:
    if not resultado.get("ok"):
        return formatear_propuesta_556cd2(resultado)
    return "\n".join([
        "INVENTARIO INICIAL CREADO",
        f"- Artículo: {resultado['articulo']} [{resultado['codigo']}]",
        f"- Stock actual: {resultado['stock_actual']:g} {resultado['unidad']}",
        f"- Stock mínimo: {resultado['stock_minimo']:g} {resultado['unidad']}",
        f"- Ubicación: {resultado['ubicacion']}",
        "- Movimiento inicial registrado: SÍ",
        "",
        "SEGURIDAD",
        f"- Copias de seguridad creadas: {len(resultado.get('copias_seguridad', []))}",
        "- Datos reales modificados: SÍ, con confirmación explícita.",
    ])


def formatear_faltantes_inventario_556cd2(resultado: Dict[str, Any]) -> str:
    lines = [
        "ESTADO DEL INVENTARIO INICIAL",
        f"- Artículos totales: {resultado['total_articulos']}",
        f"- Con inventario: {resultado['con_inventario']}",
        f"- Sin inventario: {resultado['sin_inventario']}",
    ]
    if resultado.get("articulos"):
        lines += ["", "PRIMEROS ARTÍCULOS SIN INVENTARIO"]
        for x in resultado["articulos"]:
            lines.append(
                f"- {x['nombre']} [{x['codigo']}] | unidad {x['unidad']} | mínimo recomendado {x['stock_minimo_recomendado']:g} {x['unidad']}"
            )
    lines += ["", "SEGURIDAD", "- Informe en modo solo lectura.", "- Datos reales modificados: NO."]
    return "\n".join(lines)


__all__ = [
    "InventarioInicialSeguro556CD2",
    "formatear_propuesta_556cd2",
    "formatear_confirmacion_556cd2",
    "formatear_faltantes_inventario_556cd2",
]
