from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from SERVICIOS.fichas_produccion_reales_556e31 import RepositorioFichasProduccion556E31


def _norm(texto: Any) -> str:
    value = str(texto or "").strip().lower()
    value = "".join(c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", value).strip(" .")


def _minutos(texto: str) -> Optional[int]:
    t = _norm(texto)
    total = 0
    encontrado = False
    for patron, factor in (
        (r"(\d+(?:[.,]\d+)?)\s*(?:h|hora|horas)\b", 60),
        (r"(\d+(?:[.,]\d+)?)\s*(?:min|minuto|minutos)\b", 1),
    ):
        for m in re.finditer(patron, t):
            total += round(float(m.group(1).replace(",", ".")) * factor)
            encontrado = True
    if encontrado:
        return max(1, int(total))
    return None


def _limpiar_nombre_fase(texto: str) -> str:
    """Devuelve un nombre operativo corto, sin duración ni conectores colgantes."""
    nombre = str(texto or "").strip()
    nombre = re.sub(r"\b\d+(?:[.,]\d+)?\s*(?:h|hora|horas|min|minuto|minutos)\b", "", nombre, flags=re.I)
    nombre = re.sub(r"\b(?:durante|por|unos?|aproximadamente|aprox\.?)\s*$", "", nombre, flags=re.I)
    nombre = re.sub(r"\s+", " ", nombre).strip(" .,-:;")
    # Evita artículos iniciales innecesarios sin destruir nombres naturales.
    nombre = re.sub(r"^(cocer|cocinar|enfriar|pelar|cortar|mezclar|reposar|porcionar|etiquetar|preparar)\s+(?:el|la|los|las)\s+", r"\1 ", nombre, flags=re.I)
    return nombre[:1].upper() + nombre[1:] if nombre else "Fase sin nombre"


RECURSOS = {
    "fogones": ("cocer", "hervir", "saltear", "sofreir", "sarten", "olla", "cazo", "fogón", "fogon"),
    "horno": ("hornear", "horno", "asar"),
    "abatidor": ("abatir", "abatidor", "enfriar rapidamente", "enfriamiento rapido"),
    "camara_fria": ("camara", "cámara", "refrigerar", "reposar en frio", "reposar en frío"),
    "freidora": ("freir", "freír", "freidora"),
    "plancha": ("plancha",),
    "mesa_trabajo": ("cortar", "pelar", "mezclar", "porcionar", "envasar", "etiquetar", "preparar", "picar"),
    "envasadora": ("envasar al vacio", "envasar al vacío", "vacío", "vacio"),
}

PASIVOS = ("reposar", "enfriar", "abatir", "marinar", "fermentar", "congelar", "refrigerar", "dejar", "cocer", "hornear", "hervir")
ACTIVOS = ("cortar", "pelar", "picar", "mezclar", "porcionar", "envasar", "etiquetar", "saltear", "sofreir", "batir", "triturar", "preparar", "limpiar")


@dataclass
class FaseDetectada556E32:
    nombre: str
    descripcion: str
    duracion_base_min: int
    tipo_tiempo: str
    requiere_presencia: bool
    escalable_por_volumen: bool
    recursos: List[str]
    puede_paralelizar: bool
    punto_control: str = ""
    confianza: float = 0.0


class AnalizadorRecetasLenguajeNatural556E32:
    VERSION = "5.5.6E.3.3"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.repo = RepositorioFichasProduccion556E31(self.base_dir)

    @staticmethod
    def es_inicio_ingesta(texto: str) -> bool:
        t = _norm(texto)
        patrones = (
            "registra esta receta", "registra la receta", "te paso la receta",
            "pego la receta", "analiza esta receta", "extrae las fases",
            "guardar proceso de", "registrar proceso de",
        )
        return any(p in t for p in patrones)

    @staticmethod
    def extraer_nombre_objetivo(texto: str) -> Optional[str]:
        limpio = str(texto or "").strip()
        patrones = [
            r"(?:para|de)\s+(.+?)(?:\s*:\s*|\s*$)",
            r"receta\s+(.+?)(?:\s*:\s*|\s*$)",
        ]
        for patron in patrones:
            m = re.search(patron, limpio, re.I)
            if m:
                candidato = m.group(1).strip(" .:-")
                candidato = re.sub(r"^(?:la|el)\s+", "", candidato, flags=re.I)
                if candidato and len(candidato) < 120:
                    return candidato
        return None

    @staticmethod
    def extraer_texto_inline(texto: str) -> str:
        if ":" not in texto:
            return ""
        return texto.split(":", 1)[1].strip()

    def analizar(
        self,
        receta: str,
        texto_receta: str,
        rendimiento_base: float = 1,
        unidad_rendimiento: str = "u",
    ) -> Dict[str, Any]:
        segmentos = self._segmentar(texto_receta)
        fases: List[FaseDetectada556E32] = []
        avisos: List[str] = []

        for segmento in segmentos:
            fase = self._analizar_segmento(segmento)
            if fase:
                fases.append(fase)

        if not fases:
            return {
                "ok": False,
                "estado": "SIN_FASES_DETECTADAS",
                "mensaje": "No he podido detectar fases operativas. Añade acciones y tiempos, por ejemplo: 'Cocer patatas 35 minutos'.",
                "datos_reales_modificados": False,
            }

        sin_tiempo = [f.nombre for f in fases if f.duracion_base_min <= 0]
        if sin_tiempo:
            avisos.append("Fases sin duración real: " + ", ".join(sin_tiempo))

        ficha = {
            "receta": receta.strip(),
            "rendimiento_base": float(rendimiento_base or 1),
            "unidad_rendimiento": str(unidad_rendimiento or "u").strip(),
            "origen": "TEXTO_LENGUAJE_NATURAL",
            "validada_por": "pendiente_confirmacion_jefe_cocina",
            "fases": [asdict(f) for f in fases],
            "observaciones": "Ficha generada automáticamente desde texto. Requiere confirmación humana antes de guardarse.",
        }
        validacion = self.repo.validar(ficha)
        return {
            "ok": True,
            "estado": "FICHA_PROPUESTA",
            "ficha": ficha,
            "avisos": avisos + validacion.get("avisos", []),
            "errores": validacion.get("errores", []),
            "datos_reales_modificados": False,
            "mensaje": self.formatear_vista_previa(ficha, avisos + validacion.get("avisos", [])),
        }

    def guardar_confirmado(self, ficha: Dict[str, Any]) -> Dict[str, Any]:
        ficha = dict(ficha)
        ficha["validada_por"] = "jefe_cocina"
        resultado = self.repo.guardar(ficha, confirmar=True)
        resultado["mensaje"] = self.formatear_guardado(resultado)
        return resultado

    def _segmentar(self, texto: str) -> List[str]:
        t = str(texto or "").replace("\r", "\n")
        t = re.sub(r"(?m)^\s*[-•*]\s*", "", t)
        t = re.sub(r"(?m)^\s*\d+[.)-]\s*", "", t)
        partes = re.split(r"\n+|(?<=[.!?;])\s+|\s+(?:después|despues|luego|a continuación|finalmente)\s+", t, flags=re.I)
        return [p.strip(" .;-\t") for p in partes if len(p.strip(" .;-\t")) >= 3]

    def _analizar_segmento(self, segmento: str) -> Optional[FaseDetectada556E32]:
        t = _norm(segmento)
        if not t:
            return None
        minutos = _minutos(segmento)
        recursos = [nombre for nombre, palabras in RECURSOS.items() if any(_norm(p) in t for p in palabras)]
        if not recursos:
            recursos = ["mesa_trabajo"]

        pasivo = any(p in t for p in PASIVOS)
        activo = any(p in t for p in ACTIVOS)
        if pasivo and activo:
            tipo = "mixto"
            requiere = True
        elif pasivo:
            tipo = "pasivo"
            requiere = False
        else:
            tipo = "activo"
            requiere = True

        nombre = _limpiar_nombre_fase(segmento)

        confianza = 0.45
        if minutos is not None:
            confianza += 0.30
        if recursos:
            confianza += 0.15
        if activo or pasivo:
            confianza += 0.10

        return FaseDetectada556E32(
            nombre=nombre,
            descripcion=segmento.strip(),
            duracion_base_min=int(minutos or 0),
            tipo_tiempo=tipo,
            requiere_presencia=requiere,
            escalable_por_volumen=(tipo != "pasivo"),
            recursos=list(dict.fromkeys(recursos)),
            puede_paralelizar=(tipo == "pasivo"),
            confianza=round(min(confianza, 1.0), 2),
        )

    @staticmethod
    def formatear_vista_previa(ficha: Dict[str, Any], avisos: List[str]) -> str:
        lineas = [
            "FICHA DE PRODUCCIÓN DETECTADA",
            f"- Receta: {ficha.get('receta')}",
            f"- Rendimiento base: {ficha.get('rendimiento_base')} {ficha.get('unidad_rendimiento')}",
            f"- Fases detectadas: {len(ficha.get('fases', []))}",
            "",
            "FASES PROPUESTAS",
        ]
        for i, fase in enumerate(ficha.get("fases", []), start=1):
            duracion = fase.get("duracion_base_min") or 0
            dur_txt = f"{duracion} min" if duracion else "TIEMPO PENDIENTE"
            lineas.extend([
                f"{i}. {fase.get('nombre')}",
                f"   - Duración: {dur_txt}",
                f"   - Tipo: {str(fase.get('tipo_tiempo')).upper()}",
                f"   - Recursos: {', '.join(fase.get('recursos') or ['sin definir'])}",
                f"   - Requiere presencia: {'sí' if fase.get('requiere_presencia') else 'no'}",
            ])
        if avisos:
            lineas += ["", "AVISOS"] + [f"- {a}" for a in avisos]
        lineas += [
            "",
            "CONFIRMACIÓN NECESARIA",
            "- Revisa fases, tiempos y recursos.",
            "- Escribe 'confirma la ficha de producción' para guardarla.",
            "- Escribe 'cancela la ficha de producción' para descartarla.",
            "- No se ha modificado ningún dato real.",
        ]
        return "\n".join(lineas)

    @staticmethod
    def formatear_guardado(resultado: Dict[str, Any]) -> str:
        ficha = resultado.get("ficha", {})
        return "\n".join([
            "FICHA DE PRODUCCIÓN GUARDADA",
            f"- Receta: {ficha.get('receta')}",
            f"- Versión: {ficha.get('version', 1)}",
            f"- Fases: {len(ficha.get('fases', []))}",
            "- Estado: VALIDADA",
            "",
            "SIGUIENTE PASO",
            f"- Ya puedes planificar '{ficha.get('receta')}' con tiempos y recursos reales.",
            "",
            "SEGURIDAD",
            "- Datos reales modificados: SÍ, con confirmación explícita.",
        ])


__all__ = ["AnalizadorRecetasLenguajeNatural556E32", "FaseDetectada556E32"]
