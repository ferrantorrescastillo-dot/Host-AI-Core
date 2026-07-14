from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip(" .")


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _round(value: float, decimals: int = 4) -> float:
    return round(float(value), decimals)


class RecetaAmbigua556AB(LookupError):
    def __init__(self, termino: str, opciones: list[dict[str, Any]]):
        self.termino = termino
        self.opciones = opciones
        nombres = ", ".join(str(x.get("nombre") or "") for x in opciones)
        super().__init__(f"Hay varias recetas para '{termino}': {nombres}")


@dataclass
class LineaEscalada556AB:
    nombre: str
    articulo_id: Optional[str]
    cantidad_base: float
    cantidad_escalada: float
    unidad: str
    factor: float
    es_elaboracion: bool = False
    receta_referenciada_id: Optional[str] = None
    coste_unitario: float = 0.0
    coste_estimado: float = 0.0


class MotorEscaladoExplosion556AB:
    """Escala recetas canónicas y explota elaboraciones internas de forma recursiva.

    Solo lectura. No crea órdenes, no descuenta stock y no modifica la base canónica.
    """

    VERSION = "5.5.6AB"
    MAX_PROFUNDIDAD = 12

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.canonico_path = self.base_dir / "DATOS" / "db" / "escandallos_canonicos.json"
        self.articulos_path = self.base_dir / "DATOS" / "db" / "articulos.json"
        self.preimportacion_path = self.base_dir / "DATOS" / "informes" / "preimportacion_555b.json"
        self.resolucion_path = self.base_dir / "DATOS" / "informes" / "resolucion_variantes_555b.json"
        self.recetas = self._cargar_recetas()
        self.recetas_variantes = self._cargar_variantes_pendientes()
        self.recetas.extend(self.recetas_variantes)
        self.articulos = self._cargar_articulos()
        self.recetas_por_id = {self._id_receta(r): r for r in self.recetas if self._id_receta(r)}
        self.recetas_por_nombre: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for receta in self.recetas:
            if self._nombre_receta(receta):
                self.recetas_por_nombre[_norm(self._nombre_receta(receta))].append(receta)
        self.articulos_por_id = {
            str(a.get("codigo") or a.get("id") or "").casefold(): a
            for a in self.articulos
            if str(a.get("codigo") or a.get("id") or "").strip()
        }

    def _cargar_recetas(self) -> List[Dict[str, Any]]:
        if not self.canonico_path.exists():
            return []
        data = json.loads(self.canonico_path.read_text(encoding="utf-8"))
        raw = data if isinstance(data, list) else data.get("escandallos", []) if isinstance(data, dict) else []
        recetas: List[Dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            receta = item.get("receta") if isinstance(item.get("receta"), dict) else item
            recetas.append(receta)
        return recetas

    def _cargar_variantes_pendientes(self) -> List[Dict[str, Any]]:
        """Carga variantes reales desde los informes de preimportación, sin escribirlas.

        Las variantes siguen pendientes de importación canónica, pero pueden seleccionarse
        explícitamente para cálculos de producción en modo solo lectura.
        """
        if not self.preimportacion_path.exists() or not self.resolucion_path.exists():
            return []
        try:
            pre = json.loads(self.preimportacion_path.read_text(encoding="utf-8"))
            res = json.loads(self.resolucion_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        fichas = [x for x in pre.get("fichas", []) if isinstance(x, dict)]
        por_origen = {
            f"{str(f.get('hoja') or '').strip()}:{int(f.get('fila_inicio') or 0)}": f
            for f in fichas
        }
        variantes: List[Dict[str, Any]] = []
        for decision in res.get("decisiones", []):
            if not isinstance(decision, dict) or decision.get("tipo") != "VARIANTES_REALES":
                continue
            origenes = decision.get("fichas_origen") or []
            nombres = decision.get("nombres_propuestos") or []
            for pos, origen in enumerate(origenes):
                ficha = por_origen.get(str(origen))
                if not ficha:
                    continue
                nombre = str(nombres[pos] if pos < len(nombres) else ficha.get("nombre") or "").strip()
                receta = {
                    "codigo": str(ficha.get("codigo") or f"VAR-{pos+1}"),
                    "nombre": nombre,
                    "nombre_base": str(decision.get("nombre") or ficha.get("nombre") or "").strip(),
                    "rendimiento": _float(ficha.get("rendimiento"), 1.0),
                    "unidad_rendimiento": str(ficha.get("unidad_rendimiento") or "u"),
                    "ingredientes": list(ficha.get("ingredientes") or []),
                    "metadata": {
                        "origen": "variante_pendiente_555b",
                        "hoja": ficha.get("hoja"),
                        "fila_inicio": ficha.get("fila_inicio"),
                        "requiere_seleccion": True,
                    },
                }
                variantes.append(receta)
        return variantes

    def _cargar_articulos(self) -> List[Dict[str, Any]]:
        if not self.articulos_path.exists():
            return []
        data = json.loads(self.articulos_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            for key in ("articulos", "items", "registros"):
                if isinstance(data.get(key), list):
                    return [x for x in data[key] if isinstance(x, dict)]
        return []

    @staticmethod
    def _nombre_receta(receta: Dict[str, Any]) -> str:
        return str(receta.get("nombre") or receta.get("receta") or "").strip()

    @staticmethod
    def _id_receta(receta: Dict[str, Any]) -> str:
        return str(receta.get("codigo") or receta.get("receta_id") or receta.get("id") or "").strip()

    def buscar_receta(self, termino: str) -> Dict[str, Any]:
        t = _norm(termino)
        if not t:
            raise ValueError("Debes indicar el nombre de la receta.")

        exactas = list(self.recetas_por_nombre.get(t, []))
        if len(exactas) == 1:
            return exactas[0]
        if len(exactas) > 1:
            raise RecetaAmbigua556AB(termino, self._opciones(exactas))

        coincidencias = [r for r in self.recetas if t in _norm(self._nombre_receta(r))]
        # Si se busca el nombre base de variantes pendientes, conserva todas las opciones.
        base = [r for r in self.recetas_variantes if _norm(r.get("nombre_base")) == t]
        if base:
            coincidencias = base
        if not coincidencias:
            raise LookupError(f"No existe una receta canónica o variante que coincida con '{termino}'.")
        if len(coincidencias) > 1:
            raise RecetaAmbigua556AB(termino, self._opciones(coincidencias))
        return coincidencias[0]

    def _opciones(self, recetas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        opciones = []
        for r in sorted(recetas, key=lambda x: self._nombre_receta(x).casefold()):
            meta = r.get("metadata") if isinstance(r.get("metadata"), dict) else {}
            opciones.append({
                "receta_id": self._id_receta(r),
                "nombre": self._nombre_receta(r),
                "rendimiento": _float(r.get("rendimiento"), 1.0),
                "unidad_rendimiento": str(r.get("unidad_rendimiento") or "u"),
                "origen": str(meta.get("hoja") or "base_canónica"),
            })
        return opciones

    def escalar(self, termino: str, objetivo: float, unidad_objetivo: str = "personas") -> Dict[str, Any]:
        receta = self.buscar_receta(termino)
        rendimiento = max(_float(receta.get("rendimiento") or receta.get("raciones_base"), 1.0), 1e-9)
        factor = float(objetivo) / rendimiento
        lineas = [self._escalar_linea(ing, factor) for ing in receta.get("ingredientes", []) if isinstance(ing, dict)]
        coste_total = sum(x.coste_estimado for x in lineas)
        return {
            "version": self.VERSION,
            "receta_id": self._id_receta(receta),
            "receta": self._nombre_receta(receta),
            "rendimiento_base": rendimiento,
            "unidad_rendimiento": receta.get("unidad_rendimiento") or "u",
            "objetivo": float(objetivo),
            "unidad_objetivo": unidad_objetivo,
            "factor": factor,
            "ingredientes": [asdict(x) for x in lineas],
            "coste_estimado": _round(coste_total, 2),
            "solo_lectura": True,
            "datos_reales_modificados": False,
            "fuente": str(self.canonico_path.relative_to(self.base_dir)),
        }

    def _escalar_linea(self, ing: Dict[str, Any], factor: float) -> LineaEscalada556AB:
        nombre = str(ing.get("nombre") or ing.get("ingrediente") or ing.get("articulo") or "Ingrediente").strip()
        cantidad_base = _float(ing.get("cantidad"), 0.0)
        cantidad = cantidad_base * factor
        articulo_id = ing.get("articulo_id") or ing.get("codigo_articulo")
        receta_ref = self._resolver_receta_referenciada(ing, nombre)
        precio = _float(ing.get("coste_unitario") or ing.get("precio"), 0.0)
        if precio <= 0 and articulo_id:
            art = self.articulos_por_id.get(str(articulo_id).casefold())
            if art:
                precio = _float(art.get("precio") or art.get("precio_unitario"), 0.0)
        return LineaEscalada556AB(
            nombre=nombre,
            articulo_id=str(articulo_id) if articulo_id else None,
            cantidad_base=_round(cantidad_base),
            cantidad_escalada=_round(cantidad),
            unidad=str(ing.get("unidad") or "u"),
            factor=_round(factor, 6),
            es_elaboracion=receta_ref is not None,
            receta_referenciada_id=self._id_receta(receta_ref) if receta_ref else None,
            coste_unitario=_round(precio, 4),
            coste_estimado=_round(cantidad * precio, 4),
        )

    def _resolver_receta_referenciada(self, ing: Dict[str, Any], nombre: str) -> Optional[Dict[str, Any]]:
        ref = ing.get("receta_id") or ing.get("elaboracion_id") or ing.get("receta_referenciada_id")
        if ref and str(ref) in self.recetas_por_id:
            return self.recetas_por_id[str(ref)]
        coincidencias = self.recetas_por_nombre.get(_norm(nombre), [])
        return coincidencias[0] if len(coincidencias) == 1 else None

    def explotar(self, termino: str, objetivo: float, unidad_objetivo: str = "personas") -> Dict[str, Any]:
        receta = self.buscar_receta(termino)
        rendimiento = max(_float(receta.get("rendimiento") or receta.get("raciones_base"), 1.0), 1e-9)
        factor = float(objetivo) / rendimiento
        agregados: Dict[Tuple[str, str, str], float] = defaultdict(float)
        incidencias: List[Dict[str, Any]] = []
        arbol = self._explotar_receta(receta, factor, 0, set(), agregados, incidencias)
        ingredientes_finales = [
            {"nombre": k[0], "articulo_id": k[1] or None, "unidad": k[2], "cantidad": _round(v)}
            for k, v in sorted(agregados.items(), key=lambda item: item[0][0].casefold())
        ]
        return {
            "version": self.VERSION,
            "receta_id": self._id_receta(receta),
            "receta": self._nombre_receta(receta),
            "rendimiento_base": rendimiento,
            "objetivo": float(objetivo),
            "unidad_objetivo": unidad_objetivo,
            "factor": factor,
            "arbol": arbol,
            "ingredientes_finales": ingredientes_finales,
            "total_ingredientes_finales": len(ingredientes_finales),
            "incidencias": incidencias,
            "solo_lectura": True,
            "datos_reales_modificados": False,
            "fuente": str(self.canonico_path.relative_to(self.base_dir)),
        }

    def _explotar_receta(
        self,
        receta: Dict[str, Any],
        factor: float,
        profundidad: int,
        visitadas: Set[str],
        agregados: Dict[Tuple[str, str, str], float],
        incidencias: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        receta_id = self._id_receta(receta) or _norm(self._nombre_receta(receta))
        if profundidad > self.MAX_PROFUNDIDAD:
            incidencias.append({"tipo": "profundidad_maxima", "receta": self._nombre_receta(receta)})
            return {"tipo": "receta", "nombre": self._nombre_receta(receta), "error": "profundidad_maxima"}
        if receta_id in visitadas:
            incidencias.append({"tipo": "ciclo_detectado", "receta": self._nombre_receta(receta)})
            return {"tipo": "receta", "nombre": self._nombre_receta(receta), "error": "ciclo_detectado"}
        nuevas_visitadas = set(visitadas)
        nuevas_visitadas.add(receta_id)
        nodos: List[Dict[str, Any]] = []
        for ing in receta.get("ingredientes", []):
            if not isinstance(ing, dict):
                continue
            linea = self._escalar_linea(ing, factor)
            ref = self._resolver_receta_referenciada(ing, linea.nombre)
            if ref:
                rendimiento_ref = max(_float(ref.get("rendimiento") or ref.get("raciones_base"), 1.0), 1e-9)
                factor_ref = linea.cantidad_escalada / rendimiento_ref
                hijo = self._explotar_receta(ref, factor_ref, profundidad + 1, nuevas_visitadas, agregados, incidencias)
                nodos.append({
                    "tipo": "elaboracion",
                    "nombre": linea.nombre,
                    "cantidad_necesaria": linea.cantidad_escalada,
                    "unidad": linea.unidad,
                    "receta_referenciada_id": self._id_receta(ref),
                    "factor": _round(factor_ref, 6),
                    "detalle": hijo,
                })
            else:
                key = (linea.nombre, linea.articulo_id or "", linea.unidad)
                agregados[key] += linea.cantidad_escalada
                nodos.append({
                    "tipo": "ingrediente_final",
                    "nombre": linea.nombre,
                    "articulo_id": linea.articulo_id,
                    "cantidad": linea.cantidad_escalada,
                    "unidad": linea.unidad,
                })
        return {
            "tipo": "receta",
            "receta_id": self._id_receta(receta),
            "nombre": self._nombre_receta(receta),
            "factor": _round(factor, 6),
            "nivel": profundidad,
            "componentes": nodos,
        }


def formatear_escalado_556ab(resultado: Dict[str, Any]) -> str:
    lines = [
        f"ESCALADO REAL — {resultado['receta']}",
        f"- Rendimiento base: {resultado['rendimiento_base']:g} {resultado['unidad_rendimiento']}",
        f"- Objetivo: {resultado['objetivo']:g} {resultado['unidad_objetivo']}",
        f"- Factor de multiplicación: x{resultado['factor']:.4g}",
        "",
        "CANTIDADES NECESARIAS",
    ]
    for ing in resultado["ingredientes"]:
        marca = " [ELABORACIÓN]" if ing["es_elaboracion"] else ""
        lines.append(f"- {ing['nombre']}: {ing['cantidad_escalada']:g} {ing['unidad']}{marca}")
    lines += [
        "",
        f"- Coste estimado con precios disponibles: {resultado['coste_estimado']:.2f} €",
        "",
        "SEGURIDAD",
        "- Cálculo en modo solo lectura.",
        "- No se han creado órdenes ni descontado stock.",
        "- Datos reales modificados: NO.",
    ]
    return "\n".join(lines)


def _render_arbol(nodo: Dict[str, Any], nivel: int = 0) -> List[str]:
    pref = "  " * nivel
    lines = [f"{pref}- {nodo.get('nombre')}" ]
    for c in nodo.get("componentes", []):
        if c.get("tipo") == "ingrediente_final":
            lines.append(f"{pref}  · {c.get('nombre')}: {c.get('cantidad'):g} {c.get('unidad')}")
        else:
            lines.append(f"{pref}  ↳ {c.get('nombre')}: {c.get('cantidad_necesaria'):g} {c.get('unidad')}")
            lines.extend(_render_arbol(c.get("detalle", {}), nivel + 2))
    return lines


def formatear_explosion_556ab(resultado: Dict[str, Any]) -> str:
    lines = [
        f"EXPLOSIÓN DE ELABORACIONES — {resultado['receta']}",
        f"- Objetivo: {resultado['objetivo']:g} {resultado['unidad_objetivo']}",
        f"- Factor general: x{resultado['factor']:.4g}",
        "",
        "ÁRBOL DE PRODUCCIÓN",
    ]
    lines.extend(_render_arbol(resultado["arbol"]))
    lines += ["", "INGREDIENTES FINALES CONSOLIDADOS"]
    for ing in resultado["ingredientes_finales"]:
        lines.append(f"- {ing['nombre']}: {ing['cantidad']:g} {ing['unidad']}")
    if resultado.get("incidencias"):
        lines += ["", "INCIDENCIAS"]
        for inc in resultado["incidencias"]:
            lines.append(f"- {inc.get('tipo')}: {inc.get('receta')}")
    lines += [
        "",
        "SEGURIDAD",
        "- Desglose en modo solo lectura.",
        "- No se han creado órdenes ni descontado stock.",
        "- Datos reales modificados: NO.",
    ]
    return "\n".join(lines)


def extraer_consulta_556ab(texto: str) -> Dict[str, Any]:
    t = _norm(texto).replace("?", "")
    explotar = any(x in t for x in ("desglosa", "desglosar", "explota", "explosion", "incluyendo elaboraciones", "elaboraciones internas"))
    objetivo = None
    m = re.search(r"(?:para|de)\s+(\d+(?:[.,]\d+)?)\s*(personas|comensales|pax|raciones|unidades|u|kg|litros|l)?", t)
    if m:
        objetivo = float(m.group(1).replace(",", "."))
        unidad = m.group(2) or "personas"
    else:
        unidad = "personas"
    patrones = (
        r"(?:calcula|escala|prepara)\s+(?:la\s+)?(?:receta|produccion)?\s*(?:de\s+)?(.+?)(?:\s+(?:para|de)\s+\d|$)",
        r"(?:desglosa|explota)\s+(?:toda\s+)?(?:la\s+)?(?:produccion\s+de\s+)?(.+?)(?:\s+(?:para|de)\s+\d|$)",
    )
    termino = ""
    for patron in patrones:
        mm = re.search(patron, t)
        if mm:
            termino = mm.group(1).strip(" .")
            break
    termino = re.sub(r"^(?:una|un|la|el)\s+", "", termino)
    return {"termino": termino, "objetivo": objetivo, "unidad": unidad, "explotar": explotar}


__all__ = [
    "RecetaAmbigua556AB",
    "MotorEscaladoExplosion556AB",
    "formatear_escalado_556ab",
    "formatear_explosion_556ab",
    "extraer_consulta_556ab",
]
