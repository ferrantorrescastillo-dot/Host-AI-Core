from __future__ import annotations

from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import re
import unicodedata

from SERVICIOS.detector_limpio_menus_i131 import DetectorLimpioMenusI131


PALABRAS_VACIAS = {
    "a", "al", "amb", "con", "de", "del", "el", "en", "i", "la", "las",
    "los", "sobre", "y", "una", "un", "para", "por", "servido", "servida",
    "acompanado", "acompanada",
}


def normalizar(texto: Any) -> str:
    valor = str(texto or "").strip().lower()
    valor = "".join(
        c for c in unicodedata.normalize("NFD", valor)
        if unicodedata.category(c) != "Mn"
    )
    valor = re.sub(r"[^a-z0-9]+", " ", valor)
    return re.sub(r"\s+", " ", valor).strip()


def _tokens(texto: Any) -> list[str]:
    return normalizar(texto).split()


def _tokens_significativos(texto: Any) -> list[str]:
    return [t for t in _tokens(texto) if t not in PALABRAS_VACIAS and len(t) > 1]


def _cargar_lista_json(ruta: Path, claves: Iterable[str]) -> list[dict[str, Any]]:
    if not ruta.exists():
        return []
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict):
        raw = []
        for clave in claves:
            if isinstance(data.get(clave), list):
                raw = data[clave]
                break
    else:
        raw = []
    return [x for x in raw if isinstance(x, dict)]


def _hash_archivo(ruta: Path) -> str | None:
    if not ruta.exists():
        return None
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


@dataclass(frozen=True)
class EntidadCatalogoI1321:
    tipo: str
    entidad_id: str
    nombre: str
    nombre_normalizado: str
    origen: str


@dataclass(frozen=True)
class CoincidenciaI1321:
    tipo: str
    entidad_id: str
    nombre: str
    estado: str
    confianza: float
    inicio_token: int
    fin_token: int
    texto_reconocido: str
    origen: str

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


class MotorReconocimientoMenusI1321:
    """I1.3.2.1 — reconocimiento de entidades culinarias en platos de menú.

    Responsabilidad exclusiva:
    - cargar recetas y artículos existentes;
    - reconocer coincidencias completas y parciales;
    - devolver un mapa de entidades sobre cada texto.

    No decide receta principal, guarnición o salsa. No importa ni escribe datos.
    """

    VERSION = "I1.3.2.1.1"

    def __init__(self, base_dir: str | Path, recetas: Iterable[dict[str, Any]] | None = None,
                 articulos: Iterable[dict[str, Any]] | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.ruta_recetas_canonicas = self.base_dir / "DATOS" / "db" / "escandallos_canonicos.json"
        self.ruta_recetas_operativas = self.base_dir / "DATOS" / "db" / "escandallos.json"
        self.ruta_recetas = self.ruta_recetas_canonicas
        self.ruta_articulos = self.base_dir / "DATOS" / "db" / "articulos.json"
        self._recetas_raw = list(recetas) if recetas is not None else self._cargar_recetas()
        self._articulos_raw = list(articulos) if articulos is not None else _cargar_lista_json(
            self.ruta_articulos, ("articulos", "items", "registros")
        )
        self.recetas = self._preparar_recetas(self._recetas_raw)
        self.articulos = self._preparar_articulos(self._articulos_raw)

    def _cargar_recetas(self) -> list[dict[str, Any]]:
        """Carga el catálogo completo sin escribir ni migrar datos.

        Prioridad:
        1. escandallos.json (recetas operativas/importadas);
        2. escandallos_canonicos.json (catálogo canónico histórico).
        
        Los duplicados se eliminan por nombre normalizado conservando la fuente
        operativa, que es la que contiene las recetas importadas por I1.2.x.
        """
        fuentes = [
            (self.ruta_recetas_operativas, "escandallos_operativos"),
            (self.ruta_recetas_canonicas, "escandallos_canonicos"),
        ]
        resultado: list[dict[str, Any]] = []
        vistos: set[str] = set()
        for ruta, origen in fuentes:
            raw = _cargar_lista_json(ruta, ("escandallos", "recetas", "items", "registros"))
            for item in raw:
                receta = item.get("receta") if isinstance(item.get("receta"), dict) else item
                if not isinstance(receta, dict):
                    continue
                nombre = str(receta.get("nombre") or receta.get("receta") or "").strip()
                clave = normalizar(nombre)
                if not clave or clave in vistos:
                    continue
                vistos.add(clave)
                copia = dict(receta)
                copia["_origen_catalogo_i13211"] = origen
                resultado.append(copia)
        return resultado

    @staticmethod
    def _preparar_recetas(items: Iterable[dict[str, Any]]) -> list[EntidadCatalogoI1321]:
        entidades = []
        vistos = set()
        for item in items:
            receta = item.get("receta") if isinstance(item.get("receta"), dict) else item
            nombre = str(receta.get("nombre") or receta.get("receta") or "").strip()
            normal = normalizar(nombre)
            if not normal or normal in vistos:
                continue
            vistos.add(normal)
            entidades.append(EntidadCatalogoI1321(
                "RECETA",
                str(receta.get("codigo") or receta.get("receta_id") or receta.get("id") or "").strip(),
                nombre,
                normal,
                str(receta.get("_origen_catalogo_i13211") or "catalogo_recetas"),
            ))
        return sorted(entidades, key=lambda x: (-len(x.nombre_normalizado), x.nombre_normalizado))

    @staticmethod
    def _preparar_articulos(items: Iterable[dict[str, Any]]) -> list[EntidadCatalogoI1321]:
        entidades = []
        vistos = set()
        for item in items:
            nombre = str(item.get("nombre") or item.get("articulo") or item.get("Artículo") or "").strip()
            normal = normalizar(nombre)
            if not normal or normal in vistos:
                continue
            vistos.add(normal)
            entidades.append(EntidadCatalogoI1321(
                "ARTICULO",
                str(item.get("codigo") or item.get("articulo_id") or item.get("id") or "").strip(),
                nombre,
                normal,
                "articulos",
            ))
        return sorted(entidades, key=lambda x: (-len(x.nombre_normalizado), x.nombre_normalizado))

    @staticmethod
    def _buscar_secuencia(tokens_texto: list[str], tokens_entidad: list[str]) -> list[tuple[int, int]]:
        if not tokens_entidad or len(tokens_entidad) > len(tokens_texto):
            return []
        return [
            (i, i + len(tokens_entidad))
            for i in range(len(tokens_texto) - len(tokens_entidad) + 1)
            if tokens_texto[i:i + len(tokens_entidad)] == tokens_entidad
        ]

    def _coincidencias_contenidas(self, texto: str, entidades: Iterable[EntidadCatalogoI1321]) -> list[CoincidenciaI1321]:
        tokens_texto = _tokens(texto)
        coincidencias: list[CoincidenciaI1321] = []
        for entidad in entidades:
            tokens_entidad = _tokens(entidad.nombre_normalizado)
            significativos = _tokens_significativos(entidad.nombre_normalizado)
            # Evita inundar el mapa con artículos genéricos de una sola palabra.
            if entidad.tipo == "ARTICULO" and len(significativos) < 2 and entidad.nombre_normalizado != normalizar(texto):
                continue
            for inicio, fin in self._buscar_secuencia(tokens_texto, tokens_entidad):
                estado = "EXACTA_COMPLETA" if inicio == 0 and fin == len(tokens_texto) else "EXACTA_PARCIAL"
                confianza = 1.0 if estado == "EXACTA_COMPLETA" else 0.98
                coincidencias.append(CoincidenciaI1321(
                    entidad.tipo, entidad.entidad_id, entidad.nombre, estado, confianza,
                    inicio, fin, " ".join(tokens_texto[inicio:fin]), entidad.origen,
                ))
        return coincidencias

    @staticmethod
    def _eliminar_solapes(coincidencias: list[CoincidenciaI1321]) -> list[CoincidenciaI1321]:
        # Conserva primero coincidencias completas y luego las más largas/confiables.
        ordenadas = sorted(
            coincidencias,
            key=lambda c: (
                c.estado != "EXACTA_COMPLETA",
                -(c.fin_token - c.inicio_token),
                -c.confianza,
                c.tipo != "RECETA",
                c.nombre.casefold(),
            ),
        )
        elegidas: list[CoincidenciaI1321] = []
        ocupados: set[int] = set()
        for c in ordenadas:
            rango = set(range(c.inicio_token, c.fin_token))
            if rango & ocupados:
                continue
            elegidas.append(c)
            ocupados |= rango
        return sorted(elegidas, key=lambda c: (c.inicio_token, c.fin_token, c.tipo))

    def _candidatos_probables(self, texto: str, limite: int = 5) -> list[dict[str, Any]]:
        normal_texto = normalizar(texto)
        tokens_texto = set(_tokens_significativos(texto))
        candidatos = []
        for entidad in self.recetas:
            tokens_entidad = set(_tokens_significativos(entidad.nombre_normalizado))
            if not tokens_entidad:
                continue
            inter = len(tokens_texto & tokens_entidad)
            cobertura = inter / len(tokens_entidad)
            similitud = SequenceMatcher(None, normal_texto, entidad.nombre_normalizado).ratio()
            confianza = max(similitud, cobertura * 0.94)
            if inter >= 1 and confianza >= 0.62:
                candidatos.append({
                    "tipo": entidad.tipo,
                    "entidad_id": entidad.entidad_id,
                    "nombre": entidad.nombre,
                    "estado": "PROBABLE",
                    "confianza": round(confianza, 4),
                    "origen": entidad.origen,
                })
        candidatos.sort(key=lambda x: (-x["confianza"], x["nombre"].casefold()))
        return candidatos[:limite]

    @staticmethod
    def _es_equivalencia_completa(texto: str, entidad: EntidadCatalogoI1321) -> bool:
        """Acepta variaciones mínimas del mismo nombre culinario.

        Ejemplos reales: y/i, de omitido, sufijos de servicio como "boda" o
        aclaraciones de proteína como "porc". No acepta platos compuestos con
        varias elaboraciones adicionales.
        """
        texto_sig = _tokens_significativos(texto)
        entidad_sig = _tokens_significativos(entidad.nombre_normalizado)
        if len(entidad_sig) < 2:
            return False
        faltan = [t for t in entidad_sig if t not in texto_sig]
        extras = [t for t in texto_sig if t not in entidad_sig]
        if faltan:
            return False
        # Una única aclaración adicional sigue siendo el mismo plato; dos o más
        # indican normalmente un plato compuesto y deben pasar al mapa parcial.
        return len(extras) <= 1

    def _receta_equivalente_completa(self, texto: str) -> CoincidenciaI1321 | None:
        candidatos = [r for r in self.recetas if self._es_equivalencia_completa(texto, r)]
        if not candidatos:
            return None
        candidatos.sort(key=lambda r: (-len(_tokens_significativos(r.nombre_normalizado)), -len(r.nombre_normalizado)))
        mejor = candidatos[0]
        # Si hay empate real entre nombres distintos, evitamos decidir.
        if len(candidatos) > 1:
            n0 = len(_tokens_significativos(candidatos[0].nombre_normalizado))
            n1 = len(_tokens_significativos(candidatos[1].nombre_normalizado))
            if n0 == n1 and candidatos[0].nombre_normalizado != candidatos[1].nombre_normalizado:
                return None
        tokens_texto = _tokens(texto)
        return CoincidenciaI1321(
            "RECETA", mejor.entidad_id, mejor.nombre, "EQUIVALENTE_COMPLETA", 0.97,
            0, len(tokens_texto), normalizar(texto), mejor.origen,
        )

    def reconocer_texto(self, texto: str) -> dict[str, Any]:
        texto = str(texto or "").strip()
        if not texto:
            raise ValueError("El texto del plato no puede estar vacío.")
        tokens_texto = _tokens(texto)
        completas_receta = [
            c for c in self._coincidencias_contenidas(texto, self.recetas)
            if c.estado == "EXACTA_COMPLETA"
        ]
        # Una receta completa conocida se preserva como unidad y no se fragmenta.
        if completas_receta:
            mapa = self._eliminar_solapes(completas_receta)
            modo = "RECETA_COMPLETA"
        else:
            equivalente = self._receta_equivalente_completa(texto)
            if equivalente is not None:
                mapa = [equivalente]
                modo = "RECETA_COMPLETA"
            else:
                coincidencias_receta = self._coincidencias_contenidas(texto, self.recetas)
                coincidencias_articulo = self._coincidencias_contenidas(texto, self.articulos)
                # Un artículo histórico con el nombre comercial del plato no debe
                # ocultar recetas reales contenidas en un plato compuesto.
                if coincidencias_receta:
                    coincidencias_articulo = [
                        c for c in coincidencias_articulo
                        if c.estado != "EXACTA_COMPLETA"
                    ]
                mapa = self._eliminar_solapes(coincidencias_receta + coincidencias_articulo)
                completas_articulo = [c for c in mapa if c.tipo == "ARTICULO" and c.estado == "EXACTA_COMPLETA"]
                modo = "ARTICULO_COMPLETO" if completas_articulo else (
                    "MAPA_PARCIAL" if mapa else "SIN_COINCIDENCIAS_EXACTAS"
                )
        cubiertos = {i for c in mapa for i in range(c.inicio_token, c.fin_token)}
        sin_resolver = [token for i, token in enumerate(tokens_texto) if i not in cubiertos]
        return {
            "version": self.VERSION,
            "texto_original": texto,
            "texto_normalizado": normalizar(texto),
            "modo": modo,
            "coincidencias": [c.a_dict() for c in mapa],
            "tokens_sin_resolver": sin_resolver,
            "candidatos_probables": [] if mapa else self._candidatos_probables(texto),
            "solo_reconocimiento": True,
            "interpretacion_semantica": False,
            "datos_modificados": False,
        }

    def reconocer_previa(self, previa_i131: dict[str, Any]) -> dict[str, Any]:
        menus = []
        total_platos = total_recetas_completas = total_articulos_completos = total_parciales = total_sin_exacta = 0
        for menu in previa_i131.get("menus", []):
            platos = []
            for plato in menu.get("platos", []):
                reconocimiento = self.reconocer_texto(plato.get("nombre") or "")
                platos.append({**plato, "reconocimiento": reconocimiento})
                total_platos += 1
                completas = [c for c in reconocimiento["coincidencias"] if c["estado"] in {"EXACTA_COMPLETA", "EQUIVALENTE_COMPLETA"}]
                if any(c["tipo"] == "RECETA" for c in completas):
                    total_recetas_completas += 1
                elif any(c["tipo"] == "ARTICULO" for c in completas):
                    total_articulos_completos += 1
                elif reconocimiento["coincidencias"]:
                    total_parciales += 1
                else:
                    total_sin_exacta += 1
            menus.append({
                "hoja": menu.get("hoja"),
                "nombre": menu.get("nombre"),
                "platos": platos,
                "articulos_directos": menu.get("articulos_directos", []),
                "complementos": menu.get("complementos", []),
            })
        return {
            "version": self.VERSION,
            "modo": "vista_previa_reconocimiento_sin_escritura",
            "catalogo": {"recetas": len(self.recetas), "articulos": len(self.articulos)},
            "resumen": {
                "menus": len(menus), "platos": total_platos,
                "recetas_completas": total_recetas_completas,
                "articulos_completos": total_articulos_completos,
                "mapas_parciales": total_parciales,
                "sin_coincidencia_exacta": total_sin_exacta,
            },
            "menus": menus,
            "solo_reconocimiento": True,
            "interpretacion_semantica": False,
            "datos_modificados": False,
        }

    def preparar_desde_excel(self, ruta_excel: str | Path, hojas: list[str] | None = None) -> dict[str, Any]:
        previa = DetectorLimpioMenusI131().preparar(ruta_excel, hojas=hojas)
        return self.reconocer_previa(previa)

    def huellas_fuentes(self) -> dict[str, str | None]:
        return {
            "recetas_canonicas": _hash_archivo(self.ruta_recetas_canonicas),
            "recetas_operativas": _hash_archivo(self.ruta_recetas_operativas),
            "articulos": _hash_archivo(self.ruta_articulos),
        }


def formatear_reconocimiento_i1321(resultado: dict[str, Any]) -> str:
    r = resultado.get("resumen", {})
    cat = resultado.get("catalogo", {})
    lineas = [
        "I1.3.2.1.1 — CATÁLOGO DE RECONOCIMIENTO CORREGIDO",
        "=" * 78,
        f"Catálogo: {cat.get('recetas', 0)} recetas | {cat.get('articulos', 0)} artículos",
        f"Menús: {r.get('menus', 0)} | Platos: {r.get('platos', 0)} | "
        f"Receta completa: {r.get('recetas_completas', 0)} | "
        f"Artículo completo: {r.get('articulos_completos', 0)} | "
        f"Mapa parcial: {r.get('mapas_parciales', 0)} | "
        f"Sin exacta: {r.get('sin_coincidencia_exacta', 0)}",
    ]
    for menu in resultado.get("menus", []):
        lineas.append(f"\n{menu.get('nombre')} | Hoja: {menu.get('hoja')}")
        for plato in menu.get("platos", []):
            rec = plato.get("reconocimiento", {})
            lineas.append(f"- {plato.get('nombre')} [{rec.get('modo')}]")
            for c in rec.get("coincidencias", []):
                lineas.append(
                    f"    ✔ {c.get('tipo')}: {c.get('nombre')} | {c.get('estado')} | {c.get('confianza', 0):.0%}"
                )
            if not rec.get("coincidencias"):
                probs = rec.get("candidatos_probables", [])
                if probs:
                    lineas.append("    ? Probables: " + ", ".join(
                        f"{x.get('nombre')} ({x.get('confianza', 0):.0%})" for x in probs[:3]
                    ))
                else:
                    lineas.append("    — Sin entidades conocidas")
            if rec.get("tokens_sin_resolver"):
                lineas.append("    · Sin resolver: " + " ".join(rec["tokens_sin_resolver"]))
    lineas.extend([
        "=" * 78,
        "SOLO RECONOCIMIENTO: no se asignó receta principal, salsa o guarnición.",
        "No se importó ningún menú y no se modificó la base de datos.",
    ])
    return "\n".join(lineas)
