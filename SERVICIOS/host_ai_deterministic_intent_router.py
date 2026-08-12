from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import re
import unicodedata


INTENT_BUSCAR_RECETA = "BUSCAR_RECETA"
INTENT_LISTAR_RECETAS_PENDIENTES = "LISTAR_RECETAS_PENDIENTES"
INTENT_LISTAR_ESCANDALLOS_DESACTUALIZADOS = "LISTAR_ESCANDALLOS_DESACTUALIZADOS"
INTENT_LISTAR_INCIDENCIAS = "LISTAR_INCIDENCIAS"
INTENT_MOSTRAR_EVENTOS_PROXIMOS = "MOSTRAR_EVENTOS_PROXIMOS"
INTENT_ABRIR_MODULO = "ABRIR_MODULO"
INTENT_ABRIR_REFERENCIA_RESULTADO = "ABRIR_REFERENCIA_RESULTADO"
INTENT_MOSTRAR_ESCANDALLO_ACTUAL = "MOSTRAR_ESCANDALLO_ACTUAL"
INTENT_MOSTRAR_MENU_ACTUAL = "MOSTRAR_MENU_ACTUAL"
INTENT_CONSULTAR_MARGEN_ACTUAL = "CONSULTAR_MARGEN_ACTUAL"
INTENT_MOSTRAR_ESTADO_GENERAL = "MOSTRAR_ESTADO_GENERAL"
INTENT_CONSULTAR_ESTADO_STOCK = "CONSULTAR_ESTADO_STOCK"
INTENT_AYUDA = "AYUDA"
INTENT_DESCONOCIDA = "DESCONOCIDA"


@dataclass
class IntentMatch:
    intent: str
    score: float
    terms: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"intent": self.intent, "score": self.score, "terms": dict(self.terms or {})}


class HostAIDeterministicIntentRouter:
    """Router determinista de intenciones para APP-01.5."""

    MOD_KEYWORDS = {
        "eventos": "2",
        "evento": "2",
        "produccion": "3",
        "compras": "4",
        "stock": "5",
        "escandallos": "6",
        "recetas": "6",
        "menus": "7",
        "menu": "7",
        "catalogo": "8",
        "importaciones": "9",
        "importacion": "9",
        "incidencias": "10",
        "estadisticas": "11",
        "configuracion": "12",
    }

    def detectar(self, texto: str) -> IntentMatch:
        raw = str(texto or "")
        norm = self._norm(raw)

        if not norm:
            return IntentMatch(INTENT_AYUDA, 0.6, {})

        if norm in {"ayuda", "help", "que puedes hacer", "que haces"}:
            return IntentMatch(INTENT_AYUDA, 1.0, {})

        if "estado" in norm and ("sistema" in norm or "general" in norm or "como" in norm):
            return IntentMatch(INTENT_MOSTRAR_ESTADO_GENERAL, 0.95, {})

        stock = self._extract_stock_query(norm)
        if stock is not None:
            return IntentMatch(INTENT_CONSULTAR_ESTADO_STOCK, 0.98, stock)

        if self._contains_any(norm, ["recetas pendientes", "recetas incompletas", "pendientes de completar"]):
            return IntentMatch(INTENT_LISTAR_RECETAS_PENDIENTES, 0.95, {})

        if (
            self._contains_any(norm, ["escandallos desactualizados", "escandallos pendientes", "escandallos con incidencias"])
            or ("escandallos" in norm and "desactualizados" in norm)
        ):
            return IntentMatch(INTENT_LISTAR_ESCANDALLOS_DESACTUALIZADOS, 0.95, {})

        if self._contains_any(norm, ["incidencias", "incidencia abierta", "incidencias abiertas"]):
            return IntentMatch(INTENT_LISTAR_INCIDENCIAS, 0.9, {})

        if self._contains_any(norm, ["eventos proximos", "proximos eventos", "que eventos hay", "eventos hay proximos"]) or ("eventos" in norm and "proximos" in norm):
            return IntentMatch(INTENT_MOSTRAR_EVENTOS_PROXIMOS, 0.92, {})

        ref = self._extract_result_reference_open(norm)
        if ref:
            return IntentMatch(INTENT_ABRIR_REFERENCIA_RESULTADO, 0.96, {"referencia": ref})

        if self._contains_any(norm, ["muestra el escandallo", "muestrame el escandallo", "ver escandallo", "este escandallo"]):
            return IntentMatch(INTENT_MOSTRAR_ESCANDALLO_ACTUAL, 0.95, {})

        if self._contains_any(norm, ["muestra el menu", "muestrame el menu", "ver menu", "este menu"]):
            return IntentMatch(INTENT_MOSTRAR_MENU_ACTUAL, 0.95, {})

        if self._contains_any(norm, ["que margen tiene", "que margen", "margen de esta receta", "margen del menu"]):
            return IntentMatch(INTENT_CONSULTAR_MARGEN_ACTUAL, 0.93, {})

        abrir = self._extract_module_open(norm)
        if abrir:
            return IntentMatch(INTENT_ABRIR_MODULO, 0.95, {"modulo_sidebar": abrir})

        receta = self._extract_recipe_query(raw)
        if receta:
            return IntentMatch(INTENT_BUSCAR_RECETA, 0.97, {"termino": receta})

        return IntentMatch(INTENT_DESCONOCIDA, 0.0, {})

    def detectar_referencia_resultado(self, texto: str) -> int | None:
        norm = self._norm(texto)
        m = re.search(r"\b(primer[ao]|1|uno)\b", norm)
        if m:
            return 0
        m = re.search(r"\b(segund[ao]|2|dos)\b", norm)
        if m:
            return 1
        m = re.search(r"\b(ultim[ao]|ultima|ultimo)\b", norm)
        if m:
            return -1
        m = re.search(r"\b(tercer[ao]?|3|tres)\b", norm)
        if m:
            return 2
        return None

    def _extract_result_reference_open(self, norm: str) -> str:
        if not self._contains_any(norm, ["abre", "abrir", "abreme", "muestra", "ver", "llevame"]):
            return ""
        if self._contains_any(norm, ["la primera", "el primero", "primer resultado", "la 1", "la uno", "el actual", "esta receta", "este evento", "este escandallo", "este menu"]):
            return "primera"
        if self._contains_any(norm, ["la segunda", "el segundo", "segundo resultado", "la 2", "la dos"]):
            return "segunda"
        if self._contains_any(norm, ["la ultima", "el ultimo", "la última", "el último", "ultimo resultado", "anterior"]):
            return "ultima"
        return ""

    @staticmethod
    def _contains_any(texto: str, opciones: list[str]) -> bool:
        return any(op in texto for op in opciones)

    def _extract_module_open(self, norm: str) -> str:
        if not self._contains_any(norm, ["abre", "abrir", "llevame", "ir a", "ve a"]):
            return ""
        for key, value in self.MOD_KEYWORDS.items():
            if key in norm:
                return value
        return ""

    @staticmethod
    def _extract_recipe_query(raw: str) -> str:
        text = " ".join(str(raw or "").strip().split())
        low = text.lower()
        if "receta" not in low and "recetas" not in low:
            return ""
        patterns = [
            r"buscar\s+receta\s+de\s+(.+)$",
            r"buscar\s+receta\s+(.+)$",
            r"busca\s+la\s+receta\s+de\s+(.+)$",
            r"busca\s+la\s+receta\s+(.+)$",
            r"busca\s+receta\s+(.+)$",
            r"receta\s+de\s+(.+)$",
        ]
        for pat in patterns:
            m = re.search(pat, low)
            if m:
                termino = re.sub(r"[^a-zA-Z0-9áéíóúüñÁÉÍÓÚÜÑ\s-]", " ", m.group(1)).strip()
                return " ".join(termino.split())
        return ""

    @classmethod
    def _extract_stock_query(cls, norm: str) -> dict[str, Any] | None:
        if "stock" in norm and cls._contains_any(
            norm,
            ["alerta", "alertas", "bajo de stock", "bajos de stock", "stock bajo"],
        ):
            return {"consulta": "alertas", "termino": ""}

        for pattern in [
            r"(?:cuanto stock tengo de|cuanto stock hay de|tengo stock de|dime el stock de|stock de)\s+(.+)$",
            r"^tengo\s+(.+)$",
        ]:
            match = re.search(pattern, norm)
            if match:
                termino = cls._clean_stock_term(match.group(1))
                if termino and termino not in {"stock", "alertas", "productos"}:
                    return {"consulta": "articulo", "termino": termino}

        if "stock" in norm and cls._contains_any(
            norm,
            ["como esta", "estado del", "estado de", "resumen", "situacion", "que tal"],
        ):
            return {"consulta": "resumen", "termino": ""}
        return None

    @staticmethod
    def _clean_stock_term(value: str) -> str:
        value = re.sub(r"\b(ahora|actualmente|por favor)\b", " ", str(value or ""))
        return " ".join(value.split()).strip()

    @staticmethod
    def _norm(texto: str) -> str:
        t = unicodedata.normalize("NFKD", str(texto or "").lower().strip())
        t = "".join(char for char in t if not unicodedata.combining(char))
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        return " ".join(t.split())


__all__ = [
    "HostAIDeterministicIntentRouter",
    "IntentMatch",
    "INTENT_BUSCAR_RECETA",
    "INTENT_LISTAR_RECETAS_PENDIENTES",
    "INTENT_LISTAR_ESCANDALLOS_DESACTUALIZADOS",
    "INTENT_LISTAR_INCIDENCIAS",
    "INTENT_MOSTRAR_EVENTOS_PROXIMOS",
    "INTENT_ABRIR_MODULO",
    "INTENT_ABRIR_REFERENCIA_RESULTADO",
    "INTENT_MOSTRAR_ESCANDALLO_ACTUAL",
    "INTENT_MOSTRAR_MENU_ACTUAL",
    "INTENT_CONSULTAR_MARGEN_ACTUAL",
    "INTENT_MOSTRAR_ESTADO_GENERAL",
    "INTENT_CONSULTAR_ESTADO_STOCK",
    "INTENT_AYUDA",
    "INTENT_DESCONOCIDA",
]
