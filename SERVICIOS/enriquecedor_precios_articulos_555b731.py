from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _float(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        parsed = float(value)
        return parsed if parsed >= 0 else None
    except (TypeError, ValueError):
        return None


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _extract_rows(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("articulos", "items", "registros", "datos"):
            rows = data.get(key)
            if isinstance(rows, list):
                return [x for x in rows if isinstance(x, dict)]
    return []


@dataclass(slots=True)
class CoincidenciaPrecio555B731:
    encontrado: bool
    articulo_id: Optional[str]
    articulo_nombre: Optional[str]
    precio_unitario: Optional[float]
    unidad_precio: Optional[str]
    proveedor: Optional[str]
    metodo: str
    confianza: float
    ambiguo: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EnriquecedorPreciosArticulos555B731:
    """Enriquece líneas de escandallo con precios reales del catálogo.

    Prioridades de enlace:
    1. Código/artículo_id exacto.
    2. Nombre normalizado exacto.
    3. Coincidencia aproximada únicamente si es inequívoca y de alta confianza.

    El servicio es estrictamente de solo lectura. No copia precios a la base
    canónica ni modifica ``articulos.json``.
    """

    VERSION = "5.5.5B.7.3.1"

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.ruta_articulos = self.base_dir / "DATOS" / "db" / "articulos.json"
        self.articulos = _extract_rows(_read_json(self.ruta_articulos))
        self._por_codigo: Dict[str, Dict[str, Any]] = {}
        self._por_nombre: Dict[str, List[Dict[str, Any]]] = {}
        for articulo in self.articulos:
            codigo = _norm(articulo.get("codigo") or articulo.get("id") or articulo.get("articulo_id"))
            nombre = _norm(articulo.get("nombre") or articulo.get("articulo"))
            if codigo:
                self._por_codigo[codigo] = articulo
            if nombre:
                self._por_nombre.setdefault(nombre, []).append(articulo)

    @staticmethod
    def _precio(articulo: Dict[str, Any]) -> Optional[float]:
        for key in ("precio", "precio_actual", "precio_unitario", "coste_unitario", "ultimo_precio"):
            value = _float(articulo.get(key))
            if value is not None and value > 0:
                return value
        return None

    @staticmethod
    def _unidad(articulo: Dict[str, Any], unidad_linea: str | None = None) -> str:
        unidad = articulo.get("unidad") or articulo.get("unidad_compra") or articulo.get("unidad_base")
        return str(unidad or unidad_linea or "u").strip().lower()

    def _resultado(self, articulo: Dict[str, Any], metodo: str, confianza: float, *, ambiguo: bool = False, unidad_linea: str | None = None) -> CoincidenciaPrecio555B731:
        return CoincidenciaPrecio555B731(
            encontrado=True,
            articulo_id=str(articulo.get("codigo") or articulo.get("id") or articulo.get("articulo_id") or "") or None,
            articulo_nombre=str(articulo.get("nombre") or articulo.get("articulo") or "") or None,
            precio_unitario=self._precio(articulo),
            unidad_precio=self._unidad(articulo, unidad_linea),
            proveedor=str(articulo.get("proveedor") or articulo.get("proveedor_habitual") or "") or None,
            metodo=metodo,
            confianza=round(confianza, 4),
            ambiguo=ambiguo,
        )

    def resolver(self, linea: Dict[str, Any]) -> Dict[str, Any]:
        articulo_id = _norm(linea.get("articulo_id") or linea.get("codigo"))
        nombre = _norm(linea.get("nombre") or linea.get("ingrediente") or linea.get("articulo"))
        unidad_linea = str(linea.get("unidad") or "u")

        if articulo_id and articulo_id in self._por_codigo:
            return self._resultado(self._por_codigo[articulo_id], "CODIGO_EXACTO", 1.0, unidad_linea=unidad_linea).to_dict()

        exactos = self._por_nombre.get(nombre, []) if nombre else []
        if len(exactos) == 1:
            return self._resultado(exactos[0], "NOMBRE_EXACTO", 1.0, unidad_linea=unidad_linea).to_dict()
        if len(exactos) > 1:
            con_precio = [a for a in exactos if self._precio(a) is not None]
            if len(con_precio) == 1:
                return self._resultado(con_precio[0], "NOMBRE_EXACTO_UNICO_CON_PRECIO", 0.98, unidad_linea=unidad_linea).to_dict()
            return CoincidenciaPrecio555B731(False, None, None, None, None, None, "NOMBRE_AMBIGUO", 1.0, True).to_dict()

        if nombre:
            candidatos: List[Tuple[float, Dict[str, Any]]] = []
            for nombre_catalogo, articulos in self._por_nombre.items():
                ratio = SequenceMatcher(None, nombre, nombre_catalogo).ratio()
                if ratio >= 0.90:
                    for articulo in articulos:
                        candidatos.append((ratio, articulo))
            candidatos.sort(key=lambda x: x[0], reverse=True)
            if candidatos:
                mejor_ratio, mejor = candidatos[0]
                segundo_ratio = candidatos[1][0] if len(candidatos) > 1 else 0.0
                if mejor_ratio >= 0.94 and (mejor_ratio - segundo_ratio >= 0.04 or len(candidatos) == 1):
                    return self._resultado(mejor, "NOMBRE_APROXIMADO_SEGURO", mejor_ratio, unidad_linea=unidad_linea).to_dict()
                return CoincidenciaPrecio555B731(False, None, None, None, None, None, "CANDIDATOS_AMBIGUOS", mejor_ratio, True).to_dict()

        return CoincidenciaPrecio555B731(False, None, None, None, None, None, "SIN_COINCIDENCIA", 0.0).to_dict()

    def enriquecer_linea(self, linea: Dict[str, Any]) -> Dict[str, Any]:
        salida = dict(linea)
        enlace = self.resolver(linea)
        cantidad = _float(linea.get("cantidad")) or 0.0
        precio_original = _float(linea.get("coste_unitario") or linea.get("precio"))
        precio_catalogo = enlace.get("precio_unitario")
        precio = precio_original if precio_original and precio_original > 0 else precio_catalogo

        salida["articulo_id"] = linea.get("articulo_id") or enlace.get("articulo_id")
        salida["articulo_nombre_catalogo"] = enlace.get("articulo_nombre")
        salida["proveedor"] = linea.get("proveedor") or enlace.get("proveedor")
        salida["coste_unitario"] = float(precio or 0.0)
        salida["coste"] = round(cantidad * float(precio or 0.0), 6)
        salida["precio_encontrado"] = bool(precio and precio > 0)
        salida["fuente_precio"] = "ESCANDALLO" if precio_original and precio_original > 0 else ("CATALOGO_ARTICULOS" if precio_catalogo else "SIN_PRECIO")
        salida["metodo_enlace_precio"] = enlace.get("metodo")
        salida["confianza_enlace_precio"] = enlace.get("confianza")
        salida["enlace_ambiguo"] = bool(enlace.get("ambiguo"))
        salida["unidad_precio"] = enlace.get("unidad_precio") or linea.get("unidad") or "u"
        return salida

    def enriquecer(self, lineas: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        enriquecidas = [self.enriquecer_linea(x) for x in lineas if isinstance(x, dict)]
        valoradas = sum(1 for x in enriquecidas if x.get("precio_encontrado"))
        ambiguas = sum(1 for x in enriquecidas if x.get("enlace_ambiguo"))
        sin_precio = [x.get("nombre") for x in enriquecidas if not x.get("precio_encontrado")]
        return {
            "lineas": enriquecidas,
            "total": len(enriquecidas),
            "valoradas": valoradas,
            "sin_precio": len(enriquecidas) - valoradas,
            "ambiguas": ambiguas,
            "nombres_sin_precio": [str(x) for x in sin_precio if x],
            "coste_total": round(sum(float(x.get("coste") or 0.0) for x in enriquecidas), 6),
            "fuente": str(self.ruta_articulos.relative_to(self.base_dir)),
            "solo_lectura": True,
        }


__all__ = ["EnriquecedorPreciosArticulos555B731", "CoincidenciaPrecio555B731"]
