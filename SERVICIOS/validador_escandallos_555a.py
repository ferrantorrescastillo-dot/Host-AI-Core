from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
from CORE.entidades.escandallo import Escandallo
from CORE.entidades.menu import Menu
from SERVICIOS.schema_escandallos_555a import normalizar_unidad


@dataclass(slots=True)
class ResultadoValidacion:
    valido: bool
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


def _texto_obligatorio(valor: object, campo: str, errores: list[str]) -> None:
    if not isinstance(valor, str) or not valor.strip():
        errores.append(f"{campo}: obligatorio.")


def validar_ingrediente(ingrediente: Ingrediente) -> ResultadoValidacion:
    errores: list[str] = []
    avisos: list[str] = []
    _texto_obligatorio(ingrediente.codigo, "ingrediente.codigo", errores)
    _texto_obligatorio(ingrediente.nombre, "ingrediente.nombre", errores)
    if ingrediente.cantidad <= 0:
        errores.append("ingrediente.cantidad: debe ser mayor que 0.")
    unidad = normalizar_unidad(ingrediente.unidad)
    if not unidad:
        errores.append("ingrediente.unidad: obligatoria.")
    if not 0 <= ingrediente.merma_pct < 100:
        errores.append("ingrediente.merma_pct: debe estar entre 0 y 99.99.")
    if ingrediente.precio_unitario < 0:
        errores.append("ingrediente.precio_unitario: no puede ser negativo.")
    if not ingrediente.articulo_id:
        avisos.append(f"{ingrediente.nombre}: sin artículo enlazado.")
    return ResultadoValidacion(not errores, errores, avisos)


def validar_receta(receta: Receta) -> ResultadoValidacion:
    errores: list[str] = []
    avisos: list[str] = []
    _texto_obligatorio(receta.codigo, "receta.codigo", errores)
    _texto_obligatorio(receta.nombre, "receta.nombre", errores)
    if receta.rendimiento <= 0:
        errores.append("receta.rendimiento: debe ser mayor que 0.")
    _texto_obligatorio(receta.unidad_rendimiento, "receta.unidad_rendimiento", errores)
    if not receta.ingredientes:
        avisos.append(f"{receta.nombre}: receta sin ingredientes.")
    codigos: set[str] = set()
    for ingrediente in receta.ingredientes:
        resultado = validar_ingrediente(ingrediente)
        errores.extend(resultado.errores)
        avisos.extend(resultado.avisos)
        clave = ingrediente.codigo.strip().casefold()
        if clave in codigos:
            errores.append(f"{receta.nombre}: ingrediente duplicado '{ingrediente.codigo}'.")
        codigos.add(clave)
    return ResultadoValidacion(not errores, errores, avisos)


def validar_escandallo(escandallo: Escandallo) -> ResultadoValidacion:
    resultado = validar_receta(escandallo.receta)
    errores = list(resultado.errores)
    avisos = list(resultado.avisos)
    if escandallo.coste_total < 0:
        errores.append("escandallo.coste_total: no puede ser negativo.")
    coste_calculado = sum(i.cantidad * i.precio_unitario for i in escandallo.receta.ingredientes)
    if escandallo.coste_total and abs(escandallo.coste_total - coste_calculado) > 0.01:
        avisos.append(
            f"{escandallo.receta.nombre}: coste_total ({escandallo.coste_total:.2f}) "
            f"no coincide con ingredientes ({coste_calculado:.2f})."
        )
    return ResultadoValidacion(not errores, errores, avisos)


def validar_menu(menu: Menu) -> ResultadoValidacion:
    errores: list[str] = []
    avisos: list[str] = []
    _texto_obligatorio(menu.nombre, "menu.nombre", errores)
    if not menu.recetas:
        avisos.append(f"{menu.nombre or 'Menú'}: sin recetas asociadas.")
    nombres: set[str] = set()
    for receta in menu.recetas:
        resultado = validar_receta(receta)
        errores.extend(resultado.errores)
        avisos.extend(resultado.avisos)
        clave = receta.nombre.strip().casefold()
        if clave in nombres:
            errores.append(f"{menu.nombre}: receta duplicada '{receta.nombre}'.")
        nombres.add(clave)
    return ResultadoValidacion(not errores, errores, avisos)


def validar_coleccion_escandallos(escandallos: Iterable[Escandallo]) -> ResultadoValidacion:
    errores: list[str] = []
    avisos: list[str] = []
    codigos: set[str] = set()
    for escandallo in escandallos:
        resultado = validar_escandallo(escandallo)
        errores.extend(resultado.errores)
        avisos.extend(resultado.avisos)
        codigo = escandallo.receta.codigo.strip().casefold()
        if codigo in codigos:
            errores.append(f"Código de receta duplicado: '{escandallo.receta.codigo}'.")
        codigos.add(codigo)
    return ResultadoValidacion(not errores, errores, avisos)
