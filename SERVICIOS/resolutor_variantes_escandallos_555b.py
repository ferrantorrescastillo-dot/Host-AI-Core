from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from MODELOS.resolucion_inteligente_555b import DecisionResolucion555B, ResultadoResolucion555B
from SERVICIOS.preimportador_escandallos_555b import PreimportadorEscandallosExcel555B


def _clave(valor: object) -> str:
    texto = str(valor or "").strip().lower()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", texto).split())


def _firma_ingredientes(ficha: dict[str, Any]) -> set[str]:
    resultado: set[str] = set()
    for ing in ficha.get("ingredientes") or []:
        nombre = _clave(ing.get("nombre"))
        if not nombre:
            continue
        cantidad = ing.get("cantidad")
        unidad = _clave(ing.get("unidad") or ing.get("unidad_normalizada"))
        try:
            cantidad_n = round(float(cantidad), 6)
        except (TypeError, ValueError):
            cantidad_n = 0.0
        resultado.add(f"{nombre}|{cantidad_n}|{unidad}")
    return resultado


def _nombres_ingredientes(ficha: dict[str, Any]) -> set[str]:
    return {
        _clave(ing.get("nombre"))
        for ing in ficha.get("ingredientes") or []
        if _clave(ing.get("nombre"))
    }


def _similitud_conjuntos(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _similitud_nombres(a: str, b: str) -> float:
    return SequenceMatcher(None, _clave(a), _clave(b)).ratio()


def _id_grupo(nombre: str, fichas: list[dict[str, Any]]) -> str:
    base = nombre + "|" + "|".join(sorted(str(f.get("codigo") or f.get("hoja") or "") for f in fichas))
    return "RES-" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:8].upper()


class ResolutorInteligenteEscandallos555B:
    """Analiza duplicados y variantes antes de importar escandallos.

    No escribe en la base canónica. Genera propuestas conservadoras y marca
    explícitamente cuándo hace falta una decisión humana.
    """

    TITULOS_INVALIDOS = {
        "", "kg", "g", "gr", "l", "lt", "ml", "u", "ud", "uds", "unidad",
        "pax", "racion", "raciones", "ficha tecnica", "ficha tecnica plato",
        "articulo", "ingrediente", "producto", "precio", "coste", "menu",
    }

    def __init__(
        self,
        ruta_articulos: str | Path = "DATOS/db/articulos.json",
        ruta_destino: str | Path = "DATOS/db/escandallos_canonicos.json",
    ) -> None:
        self.ruta_articulos = Path(ruta_articulos)
        self.ruta_destino = Path(ruta_destino)

    def ejecutar(
        self,
        ruta_excel: str | Path,
        *,
        informe_preimportacion: str | Path | None = None,
    ) -> dict[str, Any]:
        resultado = ResultadoResolucion555B(
            archivo_excel=str(Path(ruta_excel)),
            informe_preimportacion=str(informe_preimportacion) if informe_preimportacion else None,
        )
        try:
            previo = self._cargar_preimportacion(ruta_excel, informe_preimportacion)
        except Exception as exc:
            resultado.errores.append(f"No se pudo preparar la resolución: {exc}")
            return resultado.to_dict()

        fichas = list(previo.get("fichas") or [])
        por_nombre: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for ficha in fichas:
            nombre = str(ficha.get("nombre") or "").strip()
            clave = _clave(nombre)
            if clave in self.TITULOS_INVALIDOS or len(clave) < 3:
                resultado.fichas_individuales.append({
                    "codigo": ficha.get("codigo"),
                    "nombre": nombre,
                    "hoja": ficha.get("hoja"),
                    "fila_inicio": ficha.get("fila_inicio"),
                    "accion_propuesta": "REVISAR_TITULO",
                    "motivo": "El valor detectado no parece un nombre de receta. No se propone un nombre inventado.",
                    "requiere_confirmacion": True,
                })
                continue
            por_nombre[clave].append(ficha)

        for clave, grupo in sorted(por_nombre.items()):
            if len(grupo) < 2:
                continue
            resultado.decisiones.append(self._resolver_grupo(clave, grupo))

        # Conserva también incidencias individuales no agrupadas.
        for ficha in fichas:
            if ficha.get("estado") == "REVISAR" and _clave(ficha.get("nombre")) not in self.TITULOS_INVALIDOS:
                if not any(f.get("codigo") == ficha.get("codigo") for f in resultado.fichas_individuales):
                    resultado.fichas_individuales.append({
                        "codigo": ficha.get("codigo"),
                        "nombre": ficha.get("nombre"),
                        "hoja": ficha.get("hoja"),
                        "fila_inicio": ficha.get("fila_inicio"),
                        "accion_propuesta": "REVISAR_FICHA",
                        "motivo": ficha.get("motivo") or "La preimportación dejó esta ficha pendiente de revisión.",
                        "requiere_confirmacion": True,
                    })

        return resultado.to_dict()

    def _cargar_preimportacion(
        self,
        ruta_excel: str | Path,
        informe_preimportacion: str | Path | None,
    ) -> dict[str, Any]:
        if informe_preimportacion:
            ruta = Path(informe_preimportacion)
            if ruta.exists():
                data = json.loads(ruta.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("fichas"), list):
                    return data
        servicio = PreimportadorEscandallosExcel555B(self.ruta_articulos, self.ruta_destino)
        return servicio.ejecutar(ruta_excel, confirmar=False)

    def _resolver_grupo(self, clave: str, grupo: list[dict[str, Any]]) -> DecisionResolucion555B:
        nombre_muestra = str(grupo[0].get("nombre") or clave)
        comparaciones: list[float] = []
        comparaciones_nombres: list[float] = []
        firmas = [_firma_ingredientes(f) for f in grupo]
        nombres_sets = [_nombres_ingredientes(f) for f in grupo]
        for i in range(len(firmas)):
            for j in range(i + 1, len(firmas)):
                comparaciones.append(_similitud_conjuntos(firmas[i], firmas[j]))
                comparaciones_nombres.append(_similitud_conjuntos(nombres_sets[i], nombres_sets[j]))
        similitud_media = sum(comparaciones) / len(comparaciones) if comparaciones else 1.0
        similitud_nombres = (
            sum(comparaciones_nombres) / len(comparaciones_nombres) if comparaciones_nombres else 1.0
        )
        rendimientos = {round(float(f.get("rendimiento") or 0), 6) for f in grupo}
        unidades = {_clave(f.get("unidad_rendimiento")) for f in grupo}

        recomendada = self._elegir_mejor(grupo)
        id_grupo = _id_grupo(clave, grupo)
        origenes = [f"{f.get('hoja')}:{f.get('fila_inicio')}" for f in grupo]

        # Duplicados prácticamente idénticos: se puede conservar la mejor ficha.
        if similitud_media >= 0.98 and len(rendimientos) == 1 and len(unidades) == 1:
            return DecisionResolucion555B(
                grupo=id_grupo,
                nombre=nombre_muestra,
                tipo="DUPLICADO_EQUIVALENTE",
                accion_propuesta="SELECCIONAR_MEJOR_FICHA",
                confianza=round(similitud_media * 100, 2),
                motivo="Las fichas tienen el mismo rendimiento y una composición equivalente.",
                fichas_origen=origenes,
                ficha_recomendada=str(recomendada.get("codigo") or ""),
                requiere_confirmacion=False,
                detalles={"similitud_ingredientes": round(similitud_media * 100, 2)},
            )

        # Muy parecidas, con pequeñas diferencias: propuesta de fusión manual.
        if similitud_nombres >= 0.82:
            return DecisionResolucion555B(
                grupo=id_grupo,
                nombre=nombre_muestra,
                tipo="DUPLICADOS_CON_DIFERENCIAS_MENORES",
                accion_propuesta="FUSIONAR_DUPLICADOS",
                confianza=round(similitud_nombres * 100, 2),
                motivo="Las fichas comparten casi todos los ingredientes, pero difieren en cantidades, rendimiento o algún detalle.",
                fichas_origen=origenes,
                ficha_recomendada=str(recomendada.get("codigo") or ""),
                requiere_confirmacion=True,
                detalles={
                    "similitud_composicion_exacta": round(similitud_media * 100, 2),
                    "similitud_nombres_ingredientes": round(similitud_nombres * 100, 2),
                    "rendimientos": sorted(rendimientos),
                    "unidades_rendimiento": sorted(unidades),
                },
            )

        # Diferencias reales: conservar como versiones claramente diferenciadas.
        nombres = [self._nombre_variante(nombre_muestra, f, pos) for pos, f in enumerate(grupo, start=1)]
        return DecisionResolucion555B(
            grupo=id_grupo,
            nombre=nombre_muestra,
            tipo="VARIANTES_REALES",
            accion_propuesta="MANTENER_COMO_VARIANTES",
            confianza=round((1.0 - similitud_media) * 100, 2),
            motivo="La composición difiere suficientemente como para no fusionar automáticamente.",
            fichas_origen=origenes,
            ficha_recomendada=None,
            nombres_propuestos=nombres,
            requiere_confirmacion=True,
            detalles={
                "similitud_ingredientes": round(similitud_media * 100, 2),
                "rendimientos": sorted(rendimientos),
                "unidades_rendimiento": sorted(unidades),
            },
        )

    @staticmethod
    def _elegir_mejor(grupo: list[dict[str, Any]]) -> dict[str, Any]:
        def puntuacion(f: dict[str, Any]) -> tuple[float, int, int]:
            confianza = float(f.get("confianza") or 0)
            enlazados = sum(1 for r in f.get("relaciones_articulos") or [] if r.get("estado") == "ENLAZADO")
            ingredientes = len(f.get("ingredientes") or [])
            return (confianza, enlazados, ingredientes)
        return max(grupo, key=puntuacion)

    @staticmethod
    def _nombre_variante(nombre: str, ficha: dict[str, Any], posicion: int) -> str:
        hoja = " ".join(str(ficha.get("hoja") or "").split())
        sufijo = re.sub(r"\b(m\.?p\.?|menu|menú|ficha tecnica|ficha técnica)\b", "", hoja, flags=re.I)
        sufijo = " ".join(sufijo.split()).strip(" .-_()")
        if not sufijo:
            sufijo = f"variante {posicion}"
        return f"{nombre} — {sufijo}"
