"""
Host AI RC3.1 - Validador de Calidad para Piloto

Capa de validación ligera para detectar entradas problemáticas antes de ejecutar
motores críticos durante pruebas controladas con restaurantes.

No modifica datos ni ejecuta acciones de negocio. Solo devuelve incidencias claras.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class IncidenciaCalidadPiloto:
    """Incidencia detectada durante una validación de calidad para piloto."""

    codigo: str
    mensaje: str
    gravedad: str = "aviso"  # informativa | aviso | critica
    campo: Optional[str] = None


@dataclass
class ResultadoCalidadPiloto:
    """Resultado homogéneo de validación para RC3.1."""

    ok: bool
    contexto: str
    incidencias: List[IncidenciaCalidadPiloto]

    @property
    def total_incidencias(self) -> int:
        return len(self.incidencias)

    @property
    def total_criticas(self) -> int:
        return sum(1 for incidencia in self.incidencias if incidencia.gravedad == "critica")

    def como_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "contexto": self.contexto,
            "total_incidencias": self.total_incidencias,
            "total_criticas": self.total_criticas,
            "incidencias": [incidencia.__dict__ for incidencia in self.incidencias],
        }


class ValidadorCalidadPiloto:
    """Validaciones comunes para preparar Host AI antes de un piloto real."""

    GRAVEDAD_INFORMATIVA = "informativa"
    GRAVEDAD_AVISO = "aviso"
    GRAVEDAD_CRITICA = "critica"

    def validar_articulo(self, articulo: Dict[str, Any]) -> ResultadoCalidadPiloto:
        incidencias: List[IncidenciaCalidadPiloto] = []

        nombre = self._texto(articulo.get("nombre"))
        unidad = self._texto(articulo.get("unidad"))
        proveedor = self._texto(articulo.get("proveedor"))
        precio = self._numero(articulo.get("precio"))
        stock = self._numero(articulo.get("stock"))

        if not nombre:
            incidencias.append(self._incidencia("ART_NOMBRE_VACIO", "El artículo no tiene nombre.", "critica", "nombre"))
        if not unidad:
            incidencias.append(self._incidencia("ART_UNIDAD_VACIA", "El artículo no tiene unidad definida.", "aviso", "unidad"))
        if precio is None:
            incidencias.append(self._incidencia("ART_PRECIO_INVALIDO", "El precio del artículo no es numérico.", "critica", "precio"))
        elif precio <= 0:
            incidencias.append(self._incidencia("ART_PRECIO_CERO", "El artículo tiene precio cero o negativo.", "aviso", "precio"))
        if stock is not None and stock < 0:
            incidencias.append(self._incidencia("ART_STOCK_NEGATIVO", "El artículo tiene stock negativo.", "critica", "stock"))
        if not proveedor:
            incidencias.append(self._incidencia("ART_PROVEEDOR_VACIO", "El artículo no tiene proveedor asignado.", "informativa", "proveedor"))

        return self._resultado("articulo", incidencias)

    def validar_lineas_factura(self, lineas: Iterable[Dict[str, Any]]) -> ResultadoCalidadPiloto:
        incidencias: List[IncidenciaCalidadPiloto] = []
        lineas_lista = list(lineas or [])

        if not lineas_lista:
            incidencias.append(self._incidencia("FAC_SIN_LINEAS", "La factura no contiene líneas.", "critica", "lineas"))
            return self._resultado("factura", incidencias)

        for indice, linea in enumerate(lineas_lista, start=1):
            nombre = self._texto(linea.get("nombre") or linea.get("articulo"))
            cantidad = self._numero(linea.get("cantidad"))
            precio = self._numero(linea.get("precio") or linea.get("precio_unitario"))

            if not nombre:
                incidencias.append(self._incidencia("FAC_LINEA_SIN_ARTICULO", f"La línea {indice} no tiene artículo.", "critica", f"lineas[{indice}].nombre"))
            if cantidad is None or cantidad <= 0:
                incidencias.append(self._incidencia("FAC_CANTIDAD_INVALIDA", f"La línea {indice} tiene cantidad inválida.", "critica", f"lineas[{indice}].cantidad"))
            if precio is None or precio < 0:
                incidencias.append(self._incidencia("FAC_PRECIO_INVALIDO", f"La línea {indice} tiene precio inválido.", "critica", f"lineas[{indice}].precio"))

        return self._resultado("factura", incidencias)

    def validar_receta(self, receta: Dict[str, Any]) -> ResultadoCalidadPiloto:
        incidencias: List[IncidenciaCalidadPiloto] = []

        nombre = self._texto(receta.get("nombre"))
        ingredientes = receta.get("ingredientes") or []
        raciones = self._numero(receta.get("raciones"))
        precio_venta = self._numero(receta.get("precio_venta"))

        if not nombre:
            incidencias.append(self._incidencia("REC_NOMBRE_VACIO", "La receta no tiene nombre.", "critica", "nombre"))
        if not ingredientes:
            incidencias.append(self._incidencia("REC_SIN_INGREDIENTES", "La receta no tiene ingredientes.", "critica", "ingredientes"))
        if raciones is not None and raciones <= 0:
            incidencias.append(self._incidencia("REC_RACIONES_INVALIDAS", "La receta tiene raciones inválidas.", "critica", "raciones"))
        if precio_venta is not None and precio_venta <= 0:
            incidencias.append(self._incidencia("REC_PRECIO_VENTA_INVALIDO", "La receta tiene precio de venta cero o negativo.", "aviso", "precio_venta"))

        for indice, ingrediente in enumerate(ingredientes, start=1):
            cantidad = self._numero(ingrediente.get("cantidad"))
            coste = self._numero(ingrediente.get("coste") or ingrediente.get("precio"))
            if not self._texto(ingrediente.get("nombre")):
                incidencias.append(self._incidencia("REC_INGREDIENTE_SIN_NOMBRE", f"El ingrediente {indice} no tiene nombre.", "critica", f"ingredientes[{indice}].nombre"))
            if cantidad is None or cantidad <= 0:
                incidencias.append(self._incidencia("REC_INGREDIENTE_CANTIDAD_INVALIDA", f"El ingrediente {indice} tiene cantidad inválida.", "critica", f"ingredientes[{indice}].cantidad"))
            if coste is not None and coste < 0:
                incidencias.append(self._incidencia("REC_INGREDIENTE_COSTE_INVALIDO", f"El ingrediente {indice} tiene coste negativo.", "critica", f"ingredientes[{indice}].coste"))

        return self._resultado("receta", incidencias)

    def validar_produccion(self, produccion: Dict[str, Any]) -> ResultadoCalidadPiloto:
        incidencias: List[IncidenciaCalidadPiloto] = []

        elaboracion = self._texto(produccion.get("elaboracion") or produccion.get("nombre"))
        cantidad = self._numero(produccion.get("cantidad"))
        tiempo = self._numero(produccion.get("tiempo_minutos") or produccion.get("tiempo"))

        if not elaboracion:
            incidencias.append(self._incidencia("PROD_SIN_ELABORACION", "La producción no indica elaboración.", "critica", "elaboracion"))
        if cantidad is None or cantidad <= 0:
            incidencias.append(self._incidencia("PROD_CANTIDAD_INVALIDA", "La cantidad de producción es inválida.", "critica", "cantidad"))
        if tiempo is not None and tiempo < 0:
            incidencias.append(self._incidencia("PROD_TIEMPO_INVALIDO", "El tiempo de producción es negativo.", "critica", "tiempo"))

        return self._resultado("produccion", incidencias)

    def validar_paquete_piloto(self, datos: Dict[str, Any]) -> ResultadoCalidadPiloto:
        incidencias: List[IncidenciaCalidadPiloto] = []

        if "articulo" in datos:
            incidencias.extend(self.validar_articulo(datos["articulo"]).incidencias)
        if "lineas_factura" in datos:
            incidencias.extend(self.validar_lineas_factura(datos["lineas_factura"]).incidencias)
        if "receta" in datos:
            incidencias.extend(self.validar_receta(datos["receta"]).incidencias)
        if "produccion" in datos:
            incidencias.extend(self.validar_produccion(datos["produccion"]).incidencias)
        if not datos:
            incidencias.append(self._incidencia("PILOTO_DATOS_VACIOS", "No se han recibido datos para validar.", "critica"))

        return self._resultado("paquete_piloto", incidencias)

    def _resultado(self, contexto: str, incidencias: List[IncidenciaCalidadPiloto]) -> ResultadoCalidadPiloto:
        return ResultadoCalidadPiloto(
            ok=not any(incidencia.gravedad == self.GRAVEDAD_CRITICA for incidencia in incidencias),
            contexto=contexto,
            incidencias=incidencias,
        )

    def _incidencia(self, codigo: str, mensaje: str, gravedad: str, campo: Optional[str] = None) -> IncidenciaCalidadPiloto:
        return IncidenciaCalidadPiloto(codigo=codigo, mensaje=mensaje, gravedad=gravedad, campo=campo)

    @staticmethod
    def _texto(valor: Any) -> str:
        return "" if valor is None else str(valor).strip()

    @staticmethod
    def _numero(valor: Any) -> Optional[float]:
        if valor is None or valor == "":
            return None
        try:
            return float(valor)
        except (TypeError, ValueError):
            return None


__all__ = [
    "IncidenciaCalidadPiloto",
    "ResultadoCalidadPiloto",
    "ValidadorCalidadPiloto",
]
