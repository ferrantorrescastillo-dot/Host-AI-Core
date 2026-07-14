from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from SERVICIOS.buscador_inteligente_articulos_415 import BuscadorInteligenteArticulos415
from SERVICIOS.interprete_recepcion_texto_441 import InterpreteRecepcionTexto441, LineaRecepcionTexto441


@dataclass
class LineaRecepcionValidada442:
    producto_texto: str
    cantidad: float
    unidad: str
    proveedor_texto: Optional[str]
    precio_unitario: Optional[float]
    codigo_articulo: Optional[str]
    articulo_encontrado: Optional[str]
    proveedor_articulo: Optional[str]
    familia_articulo: Optional[str]
    precio_actual_articulo: Optional[float]
    confianza: float
    accion_sugerida: str
    mensajes: List[str] = field(default_factory=list)


@dataclass
class BorradorRecepcionMercancia442:
    fecha_borrador: str
    texto_original: str
    proveedor_general: Optional[str]
    total_lineas: int
    lineas_validadas: List[LineaRecepcionValidada442] = field(default_factory=list)
    estado: str = "sin_datos"
    mensajes_generales: List[str] = field(default_factory=list)


class ValidadorRecepcionMercancia442:
    """
    Host AI 4.4.2 — Valida una recepción por texto contra el catálogo real.

    Entrada:
    - Texto natural o resultado del intérprete 4.4.1.

    Salida:
    - Borrador de recepción, todavía sin modificar stock.

    Reglas:
    - Si encuentra artículo con confianza alta: accion_sugerida = entrada_stock.
    - Si encuentra artículo con confianza media: accion_sugerida = revisar_coincidencia.
    - Si no encuentra artículo: accion_sugerida = crear_articulo_pendiente.
    - Si viene precio distinto al actual: añade aviso de cambio de precio.
    """

    def __init__(self, ruta_articulos: str = "DATOS/db/articulos.json") -> None:
        self.ruta_articulos = Path(ruta_articulos)
        self.buscador = BuscadorInteligenteArticulos415(str(self.ruta_articulos))

    def validar_texto(self, texto: str) -> BorradorRecepcionMercancia442:
        interprete = InterpreteRecepcionTexto441()
        interpretacion = interprete.interpretar(texto)
        return self.validar_lineas(
            texto_original=interpretacion.texto_original,
            proveedor_general=interpretacion.proveedor_general,
            lineas=interpretacion.lineas,
            mensajes_generales=list(interpretacion.errores),
        )

    def validar_lineas(
        self,
        texto_original: str,
        proveedor_general: Optional[str],
        lineas: List[LineaRecepcionTexto441],
        mensajes_generales: Optional[List[str]] = None,
    ) -> BorradorRecepcionMercancia442:
        validadas: List[LineaRecepcionValidada442] = []
        mensajes = mensajes_generales or []

        for linea in lineas:
            validada = self._validar_linea(linea, proveedor_general)
            validadas.append(validada)

        estado = self._estado(validadas, mensajes)

        return BorradorRecepcionMercancia442(
            fecha_borrador=datetime.now().isoformat(timespec="seconds"),
            texto_original=texto_original,
            proveedor_general=proveedor_general,
            total_lineas=len(validadas),
            lineas_validadas=validadas,
            estado=estado,
            mensajes_generales=mensajes,
        )

    def validar_y_guardar(
        self,
        texto: str,
        ruta_destino: str = "DATOS/db/recepcion_borrador_4_4_2.json",
    ) -> BorradorRecepcionMercancia442:
        borrador = self.validar_texto(texto)
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(asdict(borrador), ensure_ascii=False, indent=2), encoding="utf-8")
        return borrador

    def exportar_txt(
        self,
        borrador: BorradorRecepcionMercancia442,
        ruta_destino: str = "DATOS/db/recepcion_borrador_4_4_2.txt",
    ) -> None:
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.4.2 - BORRADOR RECEPCIÓN MERCANCÍA",
            "=" * 76,
            f"Fecha: {borrador.fecha_borrador}",
            f"Proveedor general: {borrador.proveedor_general or '-'}",
            f"Total líneas: {borrador.total_lineas}",
            f"Estado: {borrador.estado}",
            "",
            "TEXTO ORIGINAL",
            "-" * 76,
            borrador.texto_original,
            "",
            "LÍNEAS",
            "-" * 76,
        ]

        if not borrador.lineas_validadas:
            lineas.append("No hay líneas válidas.")

        for idx, item in enumerate(borrador.lineas_validadas, start=1):
            lineas.append(
                f"{idx}. {item.producto_texto} | {item.cantidad} {item.unidad} | "
                f"Proveedor texto: {item.proveedor_texto or '-'} | "
                f"Artículo: {item.articulo_encontrado or '-'} | Código: {item.codigo_articulo or '-'} | "
                f"Confianza: {round(item.confianza * 100, 1)}% | Acción: {item.accion_sugerida}"
            )
            for mensaje in item.mensajes:
                lineas.append(f"   - {mensaje}")

        if borrador.mensajes_generales:
            lineas.extend(["", "MENSAJES GENERALES", "-" * 76])
            for mensaje in borrador.mensajes_generales:
                lineas.append(f"- {mensaje}")

        ruta.write_text("\n".join(lineas), encoding="utf-8")

    def validar_guardar_y_exportar(
        self,
        texto: str,
        ruta_json: str = "DATOS/db/recepcion_borrador_4_4_2.json",
        ruta_txt: str = "DATOS/db/recepcion_borrador_4_4_2.txt",
    ) -> BorradorRecepcionMercancia442:
        borrador = self.validar_y_guardar(texto, ruta_json)
        self.exportar_txt(borrador, ruta_txt)
        return borrador

    def _validar_linea(self, linea: LineaRecepcionTexto441, proveedor_general: Optional[str]) -> LineaRecepcionValidada442:
        proveedor = linea.proveedor or proveedor_general
        informe = self.buscador.buscar(linea.producto, proveedor=proveedor, limite=3, umbral_minimo=0.40)

        mensajes: List[str] = []

        if informe.resultados:
            mejor = informe.resultados[0]
            confianza = float(mejor.puntuacion)

            if confianza >= 0.80:
                accion = "entrada_stock"
            else:
                accion = "revisar_coincidencia"
                mensajes.append("Coincidencia media. Revisar antes de aplicar.")

            if linea.precio_unitario is not None and mejor.precio is not None:
                if abs(float(linea.precio_unitario) - float(mejor.precio)) > 0.0001:
                    mensajes.append(
                        f"Precio distinto: actual {mejor.precio}, recibido {linea.precio_unitario}. Pendiente de actualizar en 4.4.3."
                    )

            if proveedor and mejor.proveedor and proveedor.lower().strip(". ") not in str(mejor.proveedor).lower():
                mensajes.append(f"Proveedor del texto ({proveedor}) distinto al proveedor del artículo ({mejor.proveedor}).")

            return LineaRecepcionValidada442(
                producto_texto=linea.producto,
                cantidad=linea.cantidad,
                unidad=linea.unidad,
                proveedor_texto=proveedor,
                precio_unitario=linea.precio_unitario,
                codigo_articulo=mejor.codigo,
                articulo_encontrado=mejor.nombre,
                proveedor_articulo=mejor.proveedor,
                familia_articulo=mejor.familia,
                precio_actual_articulo=mejor.precio,
                confianza=confianza,
                accion_sugerida=accion,
                mensajes=mensajes,
            )

        mensajes.append("No existe coincidencia clara en artículos. Crear artículo pendiente en 4.4.3.")
        return LineaRecepcionValidada442(
            producto_texto=linea.producto,
            cantidad=linea.cantidad,
            unidad=linea.unidad,
            proveedor_texto=proveedor,
            precio_unitario=linea.precio_unitario,
            codigo_articulo=None,
            articulo_encontrado=None,
            proveedor_articulo=None,
            familia_articulo=None,
            precio_actual_articulo=None,
            confianza=0.0,
            accion_sugerida="crear_articulo_pendiente",
            mensajes=mensajes,
        )

    def _estado(self, lineas: List[LineaRecepcionValidada442], mensajes: List[str]) -> str:
        if not lineas:
            return "error"
        acciones = {linea.accion_sugerida for linea in lineas}
        if acciones == {"entrada_stock"} and not mensajes:
            return "listo_para_aplicar"
        if "crear_articulo_pendiente" in acciones or "revisar_coincidencia" in acciones:
            return "requiere_revision"
        return "parcial"


__all__ = [
    "ValidadorRecepcionMercancia442",
    "BorradorRecepcionMercancia442",
    "LineaRecepcionValidada442",
]
