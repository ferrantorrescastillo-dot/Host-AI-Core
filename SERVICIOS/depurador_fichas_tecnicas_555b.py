from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

from MODELOS.depuracion_fichas_555b import (
    FichaDepurada555B,
    IncidenciaDepuracion555B,
    ResultadoDepuracion555B,
)
from SERVICIOS.extractor_fichas_tecnicas_excel_555b import ExtractorFichasTecnicasExcel555B


def _clave(valor: object) -> str:
    texto = str(valor or "").strip().lower()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", texto).split())


def _nombre_presentable(valor: object) -> str:
    texto = " ".join(str(valor or "").strip().split())
    texto = texto.strip(" .,:;-_")
    return texto


class DepuradorFichasTecnicas555B:
    """Depura la extracción de la Parte 3 sin escribir en la base de datos.

    Reglas conservadoras: corrige únicamente casos inequívocos. Lo dudoso se
    marca para revisión humana, nunca se inventa ni se elimina silenciosamente.
    """

    TITULOS_INVALIDOS = {
        "", "kg", "g", "gr", "l", "lt", "ml", "u", "ud", "uds", "unidad",
        "unidades", "pax", "racion", "raciones", "ficha tecnica", "ficha tecnica plato",
        "articulo", "ingrediente", "producto", "precio", "coste", "menu", "postres",
        "bebidas y varios",
    }
    UNIDADES_VALIDAS = {"kg", "g", "l", "ml", "u", "pax", "ración", "unidad_origen"}
    PALABRAS_UNIDAD = (
        "huevo", "servilleta", "palito", "pan cristal", "gilda", "carquinol",
        "burrata", "pata pulpo", "chuleta lomo", "butifarra", "botifarra",
    )

    def depurar_archivo(self, ruta_archivo: str | Path) -> dict[str, Any]:
        extraido = ExtractorFichasTecnicasExcel555B().extraer(ruta_archivo)
        return self.depurar_resultado(extraido)

    def depurar_resultado(self, resultado_extraccion: dict[str, Any]) -> dict[str, Any]:
        resultado = ResultadoDepuracion555B(archivo=str(resultado_extraccion.get("archivo") or ""))
        if resultado_extraccion.get("errores"):
            resultado.errores.extend(str(e) for e in resultado_extraccion["errores"])
            return resultado.to_dict()

        fichas_origen = list(resultado_extraccion.get("fichas") or [])
        nombres_receta = {_clave(f.get("nombre")): _nombre_presentable(f.get("nombre")) for f in fichas_origen}

        for ficha in fichas_origen:
            depurada = self._depurar_ficha(ficha, nombres_receta)
            resultado.fichas.append(depurada)

        resultado.grupos_duplicados = self._marcar_duplicados(resultado.fichas)
        self._recalcular_estados(resultado.fichas)
        return resultado.to_dict()

    def _depurar_ficha(self, ficha: dict[str, Any], nombres_receta: dict[str, str]) -> FichaDepurada555B:
        nombre_original = _nombre_presentable(ficha.get("nombre"))
        nombre_normalizado = nombre_original
        incidencias: list[IncidenciaDepuracion555B] = []

        clave_nombre = _clave(nombre_original)
        if clave_nombre in self.TITULOS_INVALIDOS or len(clave_nombre) < 3:
            incidencias.append(IncidenciaDepuracion555B(
                codigo="TITULO_INVALIDO",
                nivel="ALTO",
                campo="nombre",
                mensaje=f"'{nombre_original}' no parece un nombre válido de receta.",
                valor_original=nombre_original,
            ))

        rendimiento = ficha.get("rendimiento")
        unidad_rendimiento = str(ficha.get("unidad_rendimiento") or "").strip() or None
        if not isinstance(rendimiento, (int, float)) or rendimiento <= 0:
            incidencias.append(IncidenciaDepuracion555B(
                codigo="RENDIMIENTO_INVALIDO", nivel="ALTO", campo="rendimiento",
                mensaje="El rendimiento no existe o no es mayor que cero.", valor_original=rendimiento,
            ))
        if unidad_rendimiento not in self.UNIDADES_VALIDAS:
            incidencias.append(IncidenciaDepuracion555B(
                codigo="UNIDAD_RENDIMIENTO_REVISAR", nivel="MEDIO", campo="unidad_rendimiento",
                mensaje="La unidad de rendimiento no está normalizada.", valor_original=unidad_rendimiento,
            ))

        ingredientes: list[dict[str, Any]] = []
        elaboraciones: list[str] = []
        for item in ficha.get("ingredientes") or []:
            limpio, avisos, elaboracion = self._depurar_ingrediente(item, nombres_receta, clave_nombre)
            ingredientes.append(limpio)
            incidencias.extend(avisos)
            if elaboracion and elaboracion not in elaboraciones:
                elaboraciones.append(elaboracion)

        if not ingredientes:
            incidencias.append(IncidenciaDepuracion555B(
                codigo="SIN_INGREDIENTES", nivel="CRITICO", campo="ingredientes",
                mensaje="La ficha no contiene ingredientes utilizables.",
            ))

        id_origen = f"excel:{_clave(ficha.get('hoja'))}:{ficha.get('fila_inicio')}"
        confianza_origen = float(ficha.get("confianza") or 0)
        penalizacion = sum({"CRITICO": 35, "ALTO": 20, "MEDIO": 8, "BAJO": 3}.get(i.nivel, 5) for i in incidencias)
        confianza_final = round(max(0.0, min(100.0, confianza_origen - penalizacion)), 2)

        return FichaDepurada555B(
            id_origen=id_origen,
            hoja=str(ficha.get("hoja") or ""),
            fila_inicio=int(ficha.get("fila_inicio") or 0),
            fila_fin=int(ficha.get("fila_fin") or 0),
            nombre_original=nombre_original,
            nombre_normalizado=nombre_normalizado,
            rendimiento=float(rendimiento) if isinstance(rendimiento, (int, float)) else None,
            unidad_rendimiento=unidad_rendimiento,
            ingredientes=ingredientes,
            incidencias=incidencias,
            elaboraciones_referenciadas=elaboraciones,
            confianza_final=confianza_final,
        )

    def _depurar_ingrediente(
        self, item: dict[str, Any], nombres_receta: dict[str, str], clave_ficha: str
    ) -> tuple[dict[str, Any], list[IncidenciaDepuracion555B], str | None]:
        avisos: list[IncidenciaDepuracion555B] = []
        nombre = _nombre_presentable(item.get("nombre"))
        clave_ingrediente = _clave(nombre)
        cantidad = item.get("cantidad")
        unidad_original = str(item.get("unidad") or "unidad_origen").strip()
        unidad = unidad_original

        if not isinstance(cantidad, (int, float)) or cantidad <= 0:
            avisos.append(IncidenciaDepuracion555B(
                codigo="CANTIDAD_INVALIDA", nivel="ALTO", campo="ingrediente.cantidad",
                mensaje=f"Cantidad no válida para '{nombre}'.", valor_original=cantidad,
            ))

        # Solo corrige unidades cuando la evidencia es fuerte: artículo claramente unitario,
        # cantidad entera y origen marcado como kg por una cabecera genérica del Excel.
        if unidad_original == "kg" and isinstance(cantidad, (int, float)) and float(cantidad).is_integer():
            if any(palabra in clave_ingrediente for palabra in self.PALABRAS_UNIDAD):
                unidad = "u"
                avisos.append(IncidenciaDepuracion555B(
                    codigo="UNIDAD_CORREGIDA_A_UNIDAD", nivel="BAJO", campo="ingrediente.unidad",
                    mensaje=f"Se propone tratar '{nombre}' como unidades, no como kg.",
                    valor_original=unidad_original, valor_propuesto="u",
                ))

        if unidad not in self.UNIDADES_VALIDAS:
            avisos.append(IncidenciaDepuracion555B(
                codigo="UNIDAD_INGREDIENTE_REVISAR", nivel="MEDIO", campo="ingrediente.unidad",
                mensaje=f"Unidad no normalizada en '{nombre}'.", valor_original=unidad,
            ))

        elaboracion = None
        if clave_ingrediente and clave_ingrediente != clave_ficha:
            if clave_ingrediente in nombres_receta:
                elaboracion = nombres_receta[clave_ingrediente]

        limpio = {
            "nombre": nombre,
            "cantidad": float(cantidad) if isinstance(cantidad, (int, float)) else cantidad,
            "unidad_original": unidad_original,
            "unidad_normalizada": unidad,
            "precio_unitario": item.get("precio_unitario"),
            "coste_racion": item.get("coste_racion"),
            "fila_origen": item.get("fila_origen"),
            "tipo": "ELABORACION" if elaboracion else "ARTICULO",
            "referencia_elaboracion": elaboracion,
        }
        return limpio, avisos, elaboracion

    def _firma(self, ficha: FichaDepurada555B) -> str:
        partes = [
            f"{_clave(i.get('nombre'))}:{i.get('cantidad')}:{i.get('unidad_normalizada')}"
            for i in ficha.ingredientes
        ]
        base = f"{ficha.rendimiento}|{ficha.unidad_rendimiento}|" + "|".join(sorted(partes))
        return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]

    def _marcar_duplicados(self, fichas: list[FichaDepurada555B]) -> list[dict[str, Any]]:
        por_nombre: dict[str, list[FichaDepurada555B]] = defaultdict(list)
        for ficha in fichas:
            clave = _clave(ficha.nombre_normalizado)
            if clave and clave not in self.TITULOS_INVALIDOS:
                por_nombre[clave].append(ficha)

        grupos: list[dict[str, Any]] = []
        contador = 1
        for clave, grupo in sorted(por_nombre.items()):
            if len(grupo) < 2:
                continue
            id_grupo = f"DUP-{contador:03d}"
            contador += 1
            firmas = {self._firma(f) for f in grupo}
            tipo = "DUPLICADO_EXACTO" if len(firmas) == 1 else "VARIANTES_MISMO_NOMBRE"
            for ficha in grupo:
                ficha.grupo_duplicado = id_grupo
                ficha.tipo_duplicado = tipo
                ficha.incidencias.append(IncidenciaDepuracion555B(
                    codigo=tipo, nivel="MEDIO" if tipo == "VARIANTES_MISMO_NOMBRE" else "BAJO",
                    campo="nombre", mensaje=f"La receta pertenece al grupo {id_grupo}: {tipo}.",
                ))
            grupos.append({
                "id": id_grupo,
                "nombre_normalizado": clave,
                "tipo": tipo,
                "fichas": [f.id_origen for f in grupo],
                "hojas": sorted({f.hoja for f in grupo}),
            })
        return grupos

    def _recalcular_estados(self, fichas: list[FichaDepurada555B]) -> None:
        for ficha in fichas:
            niveles = {i.nivel for i in ficha.incidencias}
            codigos = {i.codigo for i in ficha.incidencias}
            if "CRITICO" in niveles or "SIN_INGREDIENTES" in codigos:
                ficha.estado = "RECHAZADA"
            elif "ALTO" in niveles or "TITULO_INVALIDO" in codigos or ficha.confianza_final < 70:
                ficha.estado = "REVISAR"
            else:
                ficha.estado = "PREPARADA"
