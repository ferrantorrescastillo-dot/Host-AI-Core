from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import difflib
import unicodedata
import re
import json

from MODELOS.relacion_articulos_factura import CandidatoArticuloFactura


class BuscadorArticulosParecidos:
    """
    Host AI 3.0.3.4.2

    Busca artículos internos parecidos a una descripción de factura.
    Usa:
    - artículos importados desde Excel si existen
    - precios/costes registrados si existen
    - similitud por texto
    - palabras importantes
    """

    STOPWORDS = {
        "de", "del", "la", "el", "los", "las", "y", "con", "sin",
        "kg", "g", "l", "ml", "ud", "uds", "unidad", "caja",
    }

    ABREVIATURAS = {
        "carr": "carrillera",
        "tern": "ternera",
        "ter": "ternera",
        "ceb": "cebolla",
        "aceit": "aceite",
        "oliv": "oliva",
        "demi": "demi glace",
        "glace": "glace",
        "bac": "bacalao",
        "pim": "pimiento",
        "tom": "tomate",
        "pat": "patata",
    }

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def buscar(self, descripcion: str, limite: int = 5, proveedor_id: str = "") -> Dict[str, Any]:
        catalogo = self._obtener_catalogo_articulos()
        desc_norm = self._normalizar_expandido(descripcion)

        candidatos = []
        for art in catalogo:
            nombre_norm = self._normalizar_expandido(art.get("nombre", ""))
            score, motivos = self._puntuar(desc_norm, nombre_norm, descripcion, art)
            if score > 0:
                candidatos.append(CandidatoArticuloFactura(
                    articulo_id=art.get("articulo_id", ""),
                    nombre_articulo=art.get("nombre", ""),
                    confianza=round(score, 2),
                    metodo="similitud_texto",
                    motivos=motivos,
                    proveedor_id=proveedor_id,
                    unidad=art.get("unidad", ""),
                    familia=art.get("familia", ""),
                ))

        candidatos.sort(key=lambda c: c.confianza, reverse=True)
        candidatos = candidatos[:limite]

        datos = {
            "descripcion": descripcion,
            "descripcion_normalizada": desc_norm,
            "candidatos": [c.to_dict() for c in candidatos],
            "total_candidatos": len(candidatos),
            "mejor_candidato": candidatos[0].to_dict() if candidatos else None,
            "lectura_host_ai": (
                f"Mejor candidato: {candidatos[0].nombre_articulo} ({candidatos[0].confianza}%)."
                if candidatos else "No se han encontrado artículos parecidos."
            ),
        }
        return datos

    def buscar_lote(self, lineas: List[Dict[str, Any]], limite: int = 5, proveedor_id: str = "") -> Dict[str, Any]:
        resultados = []
        for linea in lineas:
            descripcion = linea.get("descripcion", "")
            resultados.append(self.buscar(descripcion, limite=limite, proveedor_id=proveedor_id))
        return {
            "resultados": resultados,
            "total": len(resultados),
            "con_candidatos": sum(1 for r in resultados if r.get("total_candidatos", 0) > 0),
            "lectura_host_ai": f"Búsqueda realizada para {len(resultados)} líneas.",
        }

    def exportar_busqueda(self, resultado: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "busqueda_articulos_parecidos.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Búsqueda de artículos exportada: {destino.name}.",
        }

    def _obtener_catalogo_articulos(self) -> List[Dict[str, Any]]:
        catalogo = {}

        # Artículos importados desde Excel.
        imp = getattr(self.core, "importador_articulos_excel", None)
        if imp and hasattr(imp, "articulos"):
            for aid, art in imp.articulos.items():
                try:
                    d = art.to_dict()
                except Exception:
                    d = dict(art)
                d.setdefault("articulo_id", aid)
                d.setdefault("nombre", d.get("nombre", aid))
                catalogo[d["articulo_id"]] = d

        # Precios registrados en motor de costes, si existe.
        costes = getattr(self.core, "costes_inteligente", None)
        if costes:
            try:
                precios = costes.listar_precios().get("precios", [])
                for p in precios:
                    aid = p.get("articulo_id") or self._articulo_id(p.get("nombre", ""))
                    if aid not in catalogo:
                        catalogo[aid] = {
                            "articulo_id": aid,
                            "nombre": p.get("nombre", ""),
                            "unidad": p.get("unidad", ""),
                            "familia": p.get("familia", ""),
                            "proveedor": p.get("proveedor", ""),
                        }
            except Exception:
                pass

        return list(catalogo.values())

    def _puntuar(self, desc_norm: str, nombre_norm: str, descripcion_original: str, art: Dict[str, Any]):
        motivos = []
        if not desc_norm or not nombre_norm:
            return 0.0, motivos

        if desc_norm == nombre_norm:
            return 100.0, ["Coincidencia exacta normalizada."]

        if desc_norm in nombre_norm or nombre_norm in desc_norm:
            motivos.append("Una descripción contiene a la otra.")
            return 92.0, motivos

        ratio = difflib.SequenceMatcher(None, desc_norm, nombre_norm).ratio()
        score = ratio * 75

        palabras_desc = set(desc_norm.split()) - self.STOPWORDS
        palabras_nombre = set(nombre_norm.split()) - self.STOPWORDS
        if palabras_desc and palabras_nombre:
            inter = palabras_desc & palabras_nombre
            cobertura = len(inter) / max(1, len(palabras_desc))
            score += cobertura * 25
            if inter:
                motivos.append(f"Palabras coincidentes: {', '.join(sorted(inter))}")

        # Bonus por unidad si coincide.
        unidad = str(art.get("unidad", "") or "").lower()
        if unidad and re.search(rf"\b{re.escape(unidad)}\b", self._normalizar(descripcion_original)):
            score += 5
            motivos.append("Unidad compatible.")

        score = min(100.0, score)
        if score < 35:
            return 0.0, []
        if not motivos:
            motivos.append(f"Similitud de texto: {round(ratio, 2)}.")
        return score, motivos

    def _normalizar_expandido(self, texto: str) -> str:
        texto = self._normalizar(texto)
        palabras = []
        for p in texto.split():
            palabras.extend(self.ABREVIATURAS.get(p, p).split())
        return " ".join(palabras)

    def _normalizar(self, texto: str) -> str:
        texto = str(texto or "").strip().lower()
        texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
        texto = re.sub(r"[^a-z0-9\s]", " ", texto)
        return " ".join(texto.split())

    def _articulo_id(self, nombre: str) -> str:
        slug = self._normalizar(nombre).upper()
        slug = re.sub(r"[^A-Z0-9]+", "-", slug).strip("-")
        return f"ART-{slug[:40] or 'SIN-NOMBRE'}"
