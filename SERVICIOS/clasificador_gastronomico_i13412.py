from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import Any


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower().strip()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


@dataclass(frozen=True)
class ClasificacionGastronomica:
    tipo: str
    familia: str
    confianza: float
    razon: str
    activa_arbol_semantico: bool
    destino_importacion: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ClasificadorGastronomicoI13412:
    """Clasifica una línea de menú antes de activar reconocimiento/árbol semántico."""

    VERSION = "I1.3.4.1.2"

    RUIDO_COMERCIAL = {
        "por pax", "precio pax", "precio por pax", "precio kg", "precio kilo",
        "kg", "unid", "unidad", "unidades", "caja", "bote", "botella", "lata",
        "sin cargo", "ojo cambiar", "menu calcotada", "menu bbq", "menu infantil",
    }
    PALABRAS_BEBIDA = {
        "cerveza", "refresco", "vermouth", "vermut", "aquarius", "coca cola", "cocacola",
        "fanta", "sprite", "zumo", "kombucha", "sidra", "caña", "cana",
    }
    PALABRAS_VINO = {
        "vino", "tinto", "blanco", "rosado", "bag in box", "clos pinell", "mas cabellut",
        "terra alta", "celler", "rioja", "priorat", "penedes",
    }
    PALABRAS_CAVA = {"cava", "champagne", "prosecco", "espumoso", "roger de flor", "petit instant"}
    PALABRAS_AGUA = {"agua", "font vella", "fon vella", "mineral"}
    PALABRAS_CAFE = {"cafe", "cafes", "descafeinado", "infusion", "te"}
    PALABRAS_PAN = {"pan", "cesta de pan", "pan de pages", "panecillo"}
    PALABRAS_SERVICIO = {"cotillon", "servicio", "menaje", "camarero", "transporte", "montaje"}
    PALABRAS_COMPLEMENTO = {
        "bodega", "seleccion de vinos", "turrones", "neulas", "pan agua", "cafes",
    }
    INDICIOS_COMERCIALES = {
        "caja", "bote", "botella", "lata", "kg", "lt", "litro", "unid", "unidad",
        "precio pax", "precio kg", "sin cargo", "bag in box", "sobre de",
    }
    INDICIOS_CULINARIOS = {
        "ensalada", "ensaladilla", "tartar", "croqueta", "calçots", "calcots", "tempura",
        "parrillada", "crema", "salsa", "carpaccio", "huevos", "pulpo", "chuleta",
        "solomillo", "lenguado", "tournedo", "lingote", "sorbete", "postre", "hamburguesa",
        "bravas", "gazpacho", "salmorejo", "ostra", "brocheta", "arroz", "fideos",
    }

    @staticmethod
    def _prefijo_mp(n: str) -> bool:
        return bool(re.match(r"^(m\s*p|mp)\b", n))

    @staticmethod
    def _prefijo_ap(n: str) -> bool:
        return bool(re.match(r"^(a\s*p|ap)\b", n))

    @staticmethod
    def _contiene(n: str, palabras: set[str]) -> bool:
        return any(p in n for p in palabras)

    def clasificar(self, nombre: str, componentes: list[dict[str, Any]] | None = None) -> ClasificacionGastronomica:
        n = _norm(nombre)
        comps = componentes or []
        receta_completa = any(
            c.get("catalogado") and c.get("grupo") == "RECETA_PRINCIPAL" and
            str(c.get("estado", "")).endswith("COMPLETA")
            for c in comps
        )
        receta_catalogada = any(c.get("catalogado") and c.get("tipo_entidad") == "RECETA" for c in comps)
        articulo_catalogado = any(c.get("catalogado") and c.get("tipo_entidad") == "ARTICULO" for c in comps)

        # La receta conocida prevalece sobre palabras como pan, agua o salsa dentro del nombre.
        if receta_completa:
            return ClasificacionGastronomica(
                "PLATO_RECETA", "PLATO", 1.0,
                "Existe una receta principal completa en el catálogo.", True, "PLATO_MENU"
            )
        if self._prefijo_ap(n):
            return ClasificacionGastronomica(
                "APERITIVO_PREPARADO", "A.P", 1.0,
                "El prefijo A.P identifica un aperitivo preparado.", False, "ARTICULO_DIRECTO"
            )
        if self._prefijo_mp(n):
            return ClasificacionGastronomica(
                "MATERIA_PRIMA", "M.P", 1.0,
                "El prefijo M.P identifica una materia prima o producto base.", False, "ARTICULO_DIRECTO"
            )
        if self._contiene(n, self.PALABRAS_CAVA):
            return ClasificacionGastronomica("CAVA", "BEBIDA", .99, "Contiene una denominación inequívoca de cava/espumoso.", False, "BEBIDA_MENU")
        if self._contiene(n, self.PALABRAS_VINO):
            return ClasificacionGastronomica("VINO", "BEBIDA", .97, "Contiene una denominación o marca de vino.", False, "BEBIDA_MENU")
        if self._contiene(n, self.PALABRAS_AGUA):
            return ClasificacionGastronomica("AGUA", "BEBIDA", .98, "La línea corresponde a agua/mineral.", False, "BEBIDA_MENU")
        if self._contiene(n, self.PALABRAS_CAFE):
            return ClasificacionGastronomica("CAFE_INFUSION", "BEBIDA", .95, "La línea corresponde a café o infusión.", False, "COMPLEMENTO_MENU")
        if self._contiene(n, self.PALABRAS_BEBIDA):
            return ClasificacionGastronomica("BEBIDA", "BEBIDA", .95, "La línea corresponde a una bebida comercial.", False, "BEBIDA_MENU")
        if self._contiene(n, self.PALABRAS_SERVICIO):
            return ClasificacionGastronomica("SERVICIO", "SERVICIO", .95, "La línea corresponde a un servicio o elemento no culinario.", False, "COMPLEMENTO_MENU")
        if self._contiene(n, self.PALABRAS_COMPLEMENTO):
            return ClasificacionGastronomica("COMPLEMENTO", "COMPLEMENTO", .92, "La línea agrupa complementos del menú.", False, "COMPLEMENTO_MENU")
        # Pan solo se clasifica como pan si no es una receta conocida.
        if self._contiene(n, self.PALABRAS_PAN):
            return ClasificacionGastronomica("PAN", "COMPLEMENTO", .90, "La línea corresponde a pan o cesta de pan.", False, "COMPLEMENTO_MENU")

        indicio_comercial = self._contiene(n, self.INDICIOS_COMERCIALES)
        indicio_culinario = self._contiene(n, self.INDICIOS_CULINARIOS)
        if articulo_catalogado and indicio_comercial:
            return ClasificacionGastronomica("ARTICULO_COMERCIAL", "ARTICULO", .96, "Artículo catalogado con envase, precio o formato comercial.", False, "ARTICULO_DIRECTO")
        if articulo_catalogado:
            tipo = "APERITIVO_PREPARADO" if indicio_culinario else "ARTICULO_COMERCIAL"
            familia = "A.P" if indicio_culinario else "ARTICULO"
            return ClasificacionGastronomica(tipo, familia, .90, "Existe como artículo y no como receta principal completa.", False, "ARTICULO_DIRECTO")
        if receta_catalogada:
            return ClasificacionGastronomica("PLATO_COMPUESTO", "PLATO", .90, "Contiene una o más recetas catalogadas y componentes adicionales.", True, "PLATO_MENU")
        if indicio_culinario:
            return ClasificacionGastronomica("PLATO_PENDIENTE", "PLATO", .78, "El nombre presenta estructura culinaria y requiere resolución.", True, "PLATO_MENU")
        if indicio_comercial:
            return ClasificacionGastronomica("ARTICULO_COMERCIAL", "ARTICULO", .78, "La línea presenta formato comercial, envase o unidad de compra.", False, "ARTICULO_DIRECTO")
        return ClasificacionGastronomica("ELEMENTO_PENDIENTE", "PENDIENTE", .45, "No hay evidencia suficiente para clasificar automáticamente.", True, "PLATO_MENU")

    def es_ruido_semantico(self, texto: str, nombre_menu: str | None = None) -> bool:
        n = _norm(texto)
        if not n:
            return True
        if nombre_menu:
            mn = _norm(nombre_menu)
            if n == mn or (len(n) >= 5 and n in mn) or (len(mn) >= 5 and mn in n):
                return True
        if n in self.RUIDO_COMERCIAL:
            return True
        if any(n == x or n.startswith(x + " ") for x in {"por pax", "precio pax", "precio kg"}):
            return True
        return False
