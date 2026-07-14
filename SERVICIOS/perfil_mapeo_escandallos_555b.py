from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


CAMPOS_CANONICOS_555B: dict[str, tuple[str, ...]] = {
    "RECETA": ("receta", "plato", "elaboracion", "preparacion", "nombre receta", "nombre plato"),
    "CODIGO_RECETA": ("codigo receta", "id receta", "cod receta", "referencia receta"),
    "INGREDIENTE": ("ingrediente", "producto", "articulo", "materia prima", "componente"),
    "CODIGO_ARTICULO": ("codigo articulo", "id articulo", "sku", "referencia", "codigo producto"),
    "CANTIDAD": ("cantidad", "cant", "cantidad neta", "peso", "dosis", "qty"),
    "UNIDAD": ("unidad", "ud", "u.m.", "um", "medida", "unidad medida"),
    "RENDIMIENTO": ("rendimiento", "raciones", "porciones", "pax", "comensales", "unidades producidas"),
    "UNIDAD_RENDIMIENTO": ("unidad rendimiento", "tipo rendimiento", "unidad salida"),
    "MERMA": ("merma", "merma %", "porcentaje merma", "% merma"),
    "PRECIO": ("precio", "precio unitario", "coste unitario", "costo unitario", "precio compra"),
    "PROVEEDOR": ("proveedor", "proveedor habitual", "suministrador"),
    "FAMILIA": ("familia", "categoria", "grupo", "tipo"),
    "ALERGENOS": ("alergenos", "alérgenos", "alergias"),
    "OBSERVACIONES": ("observaciones", "notas", "comentarios"),
}

CAMPOS_MINIMOS = ("RECETA", "INGREDIENTE", "CANTIDAD", "UNIDAD")


def normalizar_texto(texto: object) -> str:
    valor = str(texto or "").strip().lower()
    valor = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", valor)
        if unicodedata.category(caracter) != "Mn"
    )
    valor = re.sub(r"[_./\\-]+", " ", valor)
    return " ".join(valor.split())


def sugerir_mapeo(columnas: Iterable[str]) -> tuple[dict[str, str], float, list[str]]:
    resultado: dict[str, str] = {}
    aciertos = 0
    columnas_lista = [str(columna or "").strip() for columna in columnas]

    for columna in columnas_lista:
        normalizada = normalizar_texto(columna)
        mejor_campo = "DESCONOCIDO"
        mejor_puntuacion = 0
        for campo, sinonimos in CAMPOS_CANONICOS_555B.items():
            for sinonimo in sinonimos:
                sinonimo_normalizado = normalizar_texto(sinonimo)
                if normalizada == sinonimo_normalizado:
                    puntuacion = 100
                elif sinonimo_normalizado in normalizada or normalizada in sinonimo_normalizado:
                    puntuacion = 82
                else:
                    palabras_columna = set(normalizada.split())
                    palabras_sinonimo = set(sinonimo_normalizado.split())
                    interseccion = len(palabras_columna & palabras_sinonimo)
                    puntuacion = int((interseccion / max(len(palabras_sinonimo), 1)) * 70)
                if puntuacion > mejor_puntuacion:
                    mejor_puntuacion = puntuacion
                    mejor_campo = campo
        if mejor_puntuacion >= 55:
            resultado[columna] = mejor_campo
            aciertos += 1
        else:
            resultado[columna] = "DESCONOCIDO"

    campos_detectados = set(resultado.values())
    faltantes = [campo for campo in CAMPOS_MINIMOS if campo not in campos_detectados]
    confianza_columnas = (aciertos / max(len(columnas_lista), 1)) * 100
    cobertura_minimos = ((len(CAMPOS_MINIMOS) - len(faltantes)) / len(CAMPOS_MINIMOS)) * 100
    confianza = round((confianza_columnas * 0.4) + (cobertura_minimos * 0.6), 2)
    return resultado, confianza, faltantes


@dataclass(slots=True)
class PerfilMapeoEscandallos555B:
    nombre: str
    hoja: str
    fila_cabecera: int
    mapeo: dict[str, str]
    version: str = "5.5.5B-P1"

    def guardar(self, ruta: str | Path) -> Path:
        destino = Path(ruta)
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_suffix(destino.suffix + ".tmp")
        temporal.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
        temporal.replace(destino)
        return destino

    @classmethod
    def cargar(cls, ruta: str | Path) -> "PerfilMapeoEscandallos555B":
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        return cls(**datos)
