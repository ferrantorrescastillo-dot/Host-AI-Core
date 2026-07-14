from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from SERVICIOS.motor_movimientos_stock_437 import MotorMovimientosStock437
from SERVICIOS.editor_articulos_417 import EditorArticulos417


@dataclass
class LineaRecepcionAplicada443:
    producto_texto: str
    codigo_articulo: Optional[str]
    articulo: Optional[str]
    cantidad: float
    unidad: str
    proveedor: Optional[str]
    precio_unitario: Optional[float]
    accion_origen: str
    aplicada_stock: bool
    precio_actualizado: bool
    id_movimiento: Optional[str]
    mensaje: str


@dataclass
class ResultadoAplicacionRecepcion443:
    fecha_aplicacion: str
    total_lineas: int
    entradas_stock_ok: int
    precios_actualizados: int
    pendientes_articulo_nuevo: int
    omitidas_revision: int
    errores: int
    lineas: List[LineaRecepcionAplicada443] = field(default_factory=list)
    estado: str = "sin_datos"


class AplicadorRecepcionMercancia443:
    """
    Host AI 4.4.3 — Aplicador de recepción validada.

    Entrada:
    DATOS/db/recepcion_borrador_4_4_2.json

    Acciones:
    - Si accion_sugerida == entrada_stock: suma stock usando MotorMovimientosStock437.
    - Si viene precio_unitario distinto: actualiza precio del artículo con EditorArticulos417.
    - Si accion_sugerida == crear_articulo_pendiente: no crea todavía, lo deja para 4.4.4.
    - Si accion_sugerida == revisar_coincidencia: no aplica por seguridad.

    Salidas:
    DATOS/db/recepcion_aplicada_4_4_3.json
    DATOS/db/recepcion_aplicada_4_4_3.txt
    """

    def __init__(
        self,
        ruta_borrador: str = "DATOS/db/recepcion_borrador_4_4_2.json",
        ruta_stock: str = "DATOS/db/stock_inicial.json",
        ruta_movimientos: str = "DATOS/db/stock_movimientos.json",
        ruta_articulos: str = "DATOS/db/articulos.json",
    ) -> None:
        self.ruta_borrador = Path(ruta_borrador)
        self.ruta_stock = Path(ruta_stock)
        self.ruta_movimientos = Path(ruta_movimientos)
        self.ruta_articulos = Path(ruta_articulos)

    def aplicar(self) -> ResultadoAplicacionRecepcion443:
        borrador = self._leer_json_dict(self.ruta_borrador)
        lineas_borrador = borrador.get("lineas_validadas", []) if isinstance(borrador, dict) else []

        motor = MotorMovimientosStock437(str(self.ruta_stock), str(self.ruta_movimientos))
        editor = EditorArticulos417(str(self.ruta_articulos))

        lineas_resultado: List[LineaRecepcionAplicada443] = []
        entradas_ok = 0
        precios_actualizados = 0
        pendientes_nuevo = 0
        omitidas_revision = 0
        errores = 0

        for linea in lineas_borrador:
            accion = str(linea.get("accion_sugerida", "") or "")
            codigo = self._texto(linea.get("codigo_articulo"))
            articulo = self._texto(linea.get("articulo_encontrado"))
            producto_texto = str(linea.get("producto_texto", "") or "")
            cantidad = self._numero(linea.get("cantidad")) or 0.0
            unidad = str(linea.get("unidad", "") or "")
            proveedor = self._texto(linea.get("proveedor_texto")) or self._texto(linea.get("proveedor_articulo"))
            precio_unitario = self._numero(linea.get("precio_unitario"))
            precio_actual = self._numero(linea.get("precio_actual_articulo"))

            if accion == "crear_articulo_pendiente":
                pendientes_nuevo += 1
                lineas_resultado.append(
                    LineaRecepcionAplicada443(
                        producto_texto=producto_texto,
                        codigo_articulo=None,
                        articulo=None,
                        cantidad=cantidad,
                        unidad=unidad,
                        proveedor=proveedor,
                        precio_unitario=precio_unitario,
                        accion_origen=accion,
                        aplicada_stock=False,
                        precio_actualizado=False,
                        id_movimiento=None,
                        mensaje="Pendiente de crear artículo en 4.4.4.",
                    )
                )
                continue

            if accion == "revisar_coincidencia":
                omitidas_revision += 1
                lineas_resultado.append(
                    LineaRecepcionAplicada443(
                        producto_texto=producto_texto,
                        codigo_articulo=codigo,
                        articulo=articulo,
                        cantidad=cantidad,
                        unidad=unidad,
                        proveedor=proveedor,
                        precio_unitario=precio_unitario,
                        accion_origen=accion,
                        aplicada_stock=False,
                        precio_actualizado=False,
                        id_movimiento=None,
                        mensaje="Omitida por seguridad: coincidencia pendiente de revisar.",
                    )
                )
                continue

            if accion != "entrada_stock":
                omitidas_revision += 1
                lineas_resultado.append(
                    LineaRecepcionAplicada443(
                        producto_texto=producto_texto,
                        codigo_articulo=codigo,
                        articulo=articulo,
                        cantidad=cantidad,
                        unidad=unidad,
                        proveedor=proveedor,
                        precio_unitario=precio_unitario,
                        accion_origen=accion,
                        aplicada_stock=False,
                        precio_actualizado=False,
                        id_movimiento=None,
                        mensaje=f"Acción no aplicable automáticamente: {accion}",
                    )
                )
                continue

            if not codigo:
                errores += 1
                lineas_resultado.append(
                    LineaRecepcionAplicada443(
                        producto_texto=producto_texto,
                        codigo_articulo=None,
                        articulo=articulo,
                        cantidad=cantidad,
                        unidad=unidad,
                        proveedor=proveedor,
                        precio_unitario=precio_unitario,
                        accion_origen=accion,
                        aplicada_stock=False,
                        precio_actualizado=False,
                        id_movimiento=None,
                        mensaje="No hay código de artículo para aplicar entrada.",
                    )
                )
                continue

            resultado_mov = motor.registrar_movimiento(
                codigo=codigo,
                cantidad=cantidad,
                tipo="entrada",
                motivo=f"Recepción mercancía por texto 4.4.3: {producto_texto}",
                usuario="recepcion_texto",
                documento_relacionado="recepcion_borrador_4_4_2",
            )

            aplicada_stock = bool(resultado_mov.ok)
            id_movimiento = resultado_mov.id_movimiento if resultado_mov.ok else None
            if aplicada_stock:
                entradas_ok += 1
            else:
                errores += 1

            precio_actualizado = False
            if aplicada_stock and precio_unitario is not None:
                if precio_actual is None or abs(precio_unitario - precio_actual) > 0.0001:
                    resultado_edicion = editor.editar_por_codigo(codigo, precio=precio_unitario, proveedor=proveedor)
                    precio_actualizado = bool(resultado_edicion.actualizado)
                    if precio_actualizado:
                        precios_actualizados += 1

            lineas_resultado.append(
                LineaRecepcionAplicada443(
                    producto_texto=producto_texto,
                    codigo_articulo=codigo,
                    articulo=articulo or resultado_mov.articulo,
                    cantidad=cantidad,
                    unidad=unidad,
                    proveedor=proveedor,
                    precio_unitario=precio_unitario,
                    accion_origen=accion,
                    aplicada_stock=aplicada_stock,
                    precio_actualizado=precio_actualizado,
                    id_movimiento=id_movimiento,
                    mensaje=resultado_mov.mensaje,
                )
            )

        estado = self._estado(entradas_ok, pendientes_nuevo, omitidas_revision, errores, len(lineas_borrador))
        return ResultadoAplicacionRecepcion443(
            fecha_aplicacion=datetime.now().isoformat(timespec="seconds"),
            total_lineas=len(lineas_borrador),
            entradas_stock_ok=entradas_ok,
            precios_actualizados=precios_actualizados,
            pendientes_articulo_nuevo=pendientes_nuevo,
            omitidas_revision=omitidas_revision,
            errores=errores,
            lineas=lineas_resultado,
            estado=estado,
        )

    def aplicar_y_exportar(
        self,
        ruta_json: str = "DATOS/db/recepcion_aplicada_4_4_3.json",
        ruta_txt: str = "DATOS/db/recepcion_aplicada_4_4_3.txt",
    ) -> ResultadoAplicacionRecepcion443:
        resultado = self.aplicar()

        ruta_json_path = Path(ruta_json)
        ruta_json_path.parent.mkdir(parents=True, exist_ok=True)
        ruta_json_path.write_text(json.dumps(asdict(resultado), ensure_ascii=False, indent=2), encoding="utf-8")

        self._exportar_txt(resultado, ruta_txt)
        return resultado

    def _exportar_txt(self, resultado: ResultadoAplicacionRecepcion443, ruta_txt: str) -> None:
        ruta = Path(ruta_txt)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.4.3 - RECEPCIÓN APLICADA A STOCK/PRECIOS",
            "=" * 78,
            f"Fecha: {resultado.fecha_aplicacion}",
            f"Total líneas: {resultado.total_lineas}",
            f"Entradas stock OK: {resultado.entradas_stock_ok}",
            f"Precios actualizados: {resultado.precios_actualizados}",
            f"Pendientes artículo nuevo: {resultado.pendientes_articulo_nuevo}",
            f"Omitidas revisión: {resultado.omitidas_revision}",
            f"Errores: {resultado.errores}",
            f"Estado: {resultado.estado}",
            "",
            "DETALLE",
            "-" * 78,
        ]

        if not resultado.lineas:
            lineas.append("No hay líneas aplicadas.")

        for idx, linea in enumerate(resultado.lineas, start=1):
            estado = "OK" if linea.aplicada_stock else "PENDIENTE"
            if "No hay" in linea.mensaje or "No existe" in linea.mensaje:
                estado = "ERROR"
            lineas.append(
                f"{idx}. [{estado}] {linea.producto_texto} | {linea.cantidad} {linea.unidad} | "
                f"Código: {linea.codigo_articulo or '-'} | Stock: {linea.aplicada_stock} | "
                f"Precio actualizado: {linea.precio_actualizado} | Movimiento: {linea.id_movimiento or '-'}"
            )
            lineas.append(f"   - {linea.mensaje}")

        ruta.write_text("\n".join(lineas), encoding="utf-8")

    def _estado(self, entradas_ok: int, pendientes: int, omitidas: int, errores: int, total: int) -> str:
        if total == 0:
            return "sin_datos"
        if errores:
            return "aplicado_con_errores"
        if pendientes or omitidas:
            return "aplicado_con_pendientes" if entradas_ok else "pendiente_revision"
        return "aplicado"

    def _leer_json_dict(self, ruta: Path) -> Dict[str, Any]:
        if not ruta.exists():
            return {}
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return contenido if isinstance(contenido, dict) else {}

    def _texto(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None
        texto = str(valor).strip()
        return texto if texto else None

    def _numero(self, valor: Any) -> Optional[float]:
        if valor is None or str(valor).strip() == "":
            return None
        if isinstance(valor, (int, float)):
            return float(valor)
        limpio = str(valor).replace(" ", "").replace("€", "").replace(",", ".")
        try:
            return float(limpio)
        except ValueError:
            return None


__all__ = [
    "AplicadorRecepcionMercancia443",
    "ResultadoAplicacionRecepcion443",
    "LineaRecepcionAplicada443",
]
