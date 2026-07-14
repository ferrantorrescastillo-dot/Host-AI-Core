from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from SERVICIOS.motor_movimientos_stock_437 import MotorMovimientosStock437


@dataclass
class AjusteInventarioAplicado:
    codigo: str
    articulo: str
    unidad: str
    stock_sistema: float
    stock_contado: float
    diferencia: float
    estado_comparacion: str
    aplicado: bool
    mensaje: str
    id_movimiento: Optional[str] = None


@dataclass
class ResultadoAplicacionInventario:
    total_lineas: int
    ajustes_aplicados: int
    ajustes_omitidos: int
    errores: int
    lineas: List[AjusteInventarioAplicado] = field(default_factory=list)
    estado: str = "sin_datos"


class AplicadorAjustesInventario43114:
    """
    Aplica ajustes de inventario usando la comparación 4.3.11.3.

    Entrada:
    DATOS/db/comparacion_inventario_4_3_11_3.json

    Actualiza:
    DATOS/db/stock_inicial.json

    Registra movimientos:
    DATOS/db/stock_movimientos.json

    Regla:
    - Aplica solo líneas con estado faltante o sobrante.
    - Omite ok.
    - Omite revisar por seguridad.
    """

    def __init__(
        self,
        ruta_comparacion: str = "DATOS/db/comparacion_inventario_4_3_11_3.json",
        ruta_stock: str = "DATOS/db/stock_inicial.json",
        ruta_movimientos: str = "DATOS/db/stock_movimientos.json",
    ) -> None:
        self.ruta_comparacion = Path(ruta_comparacion)
        self.ruta_stock = Path(ruta_stock)
        self.ruta_movimientos = Path(ruta_movimientos)

    def aplicar(self, motivo: str = "Ajuste por inventario físico") -> ResultadoAplicacionInventario:
        comparacion = self._leer_json_dict(self.ruta_comparacion)
        lineas_comparacion = comparacion.get("lineas", []) if isinstance(comparacion, dict) else []

        motor = MotorMovimientosStock437(
            ruta_stock=str(self.ruta_stock),
            ruta_movimientos=str(self.ruta_movimientos),
        )

        resultados: List[AjusteInventarioAplicado] = []
        aplicados = 0
        omitidos = 0
        errores = 0

        for linea in lineas_comparacion:
            codigo = str(linea.get("codigo", "") or "")
            articulo = str(linea.get("articulo", "") or "")
            unidad = str(linea.get("unidad", "") or "")
            stock_sistema = self._numero(linea.get("stock_sistema")) or 0.0
            stock_contado = self._numero(linea.get("stock_contado")) or 0.0
            diferencia = self._numero(linea.get("diferencia")) or 0.0
            estado = str(linea.get("estado", "") or "")

            if estado == "ok" or diferencia == 0:
                omitidos += 1
                resultados.append(
                    AjusteInventarioAplicado(
                        codigo=codigo,
                        articulo=articulo,
                        unidad=unidad,
                        stock_sistema=stock_sistema,
                        stock_contado=stock_contado,
                        diferencia=diferencia,
                        estado_comparacion=estado,
                        aplicado=False,
                        mensaje="Sin ajuste necesario.",
                    )
                )
                continue

            if estado == "revisar":
                omitidos += 1
                resultados.append(
                    AjusteInventarioAplicado(
                        codigo=codigo,
                        articulo=articulo,
                        unidad=unidad,
                        stock_sistema=stock_sistema,
                        stock_contado=stock_contado,
                        diferencia=diferencia,
                        estado_comparacion=estado,
                        aplicado=False,
                        mensaje="Omitido por seguridad: requiere revisión manual antes de aplicar.",
                    )
                )
                continue

            if estado not in {"faltante", "sobrante"}:
                errores += 1
                resultados.append(
                    AjusteInventarioAplicado(
                        codigo=codigo,
                        articulo=articulo,
                        unidad=unidad,
                        stock_sistema=stock_sistema,
                        stock_contado=stock_contado,
                        diferencia=diferencia,
                        estado_comparacion=estado,
                        aplicado=False,
                        mensaje=f"Estado de comparación no válido: {estado}",
                    )
                )
                continue

            resultado_mov = motor.registrar_movimiento(
                codigo=codigo,
                cantidad=stock_contado,
                tipo="ajuste",
                motivo=motivo,
                usuario="sistema_inventario",
                documento_relacionado="inventario_4_3_11_3",
            )

            if resultado_mov.ok:
                aplicados += 1
                resultados.append(
                    AjusteInventarioAplicado(
                        codigo=codigo,
                        articulo=articulo,
                        unidad=unidad,
                        stock_sistema=stock_sistema,
                        stock_contado=stock_contado,
                        diferencia=diferencia,
                        estado_comparacion=estado,
                        aplicado=True,
                        mensaje="Ajuste aplicado correctamente.",
                        id_movimiento=resultado_mov.id_movimiento,
                    )
                )
            else:
                errores += 1
                resultados.append(
                    AjusteInventarioAplicado(
                        codigo=codigo,
                        articulo=articulo,
                        unidad=unidad,
                        stock_sistema=stock_sistema,
                        stock_contado=stock_contado,
                        diferencia=diferencia,
                        estado_comparacion=estado,
                        aplicado=False,
                        mensaje=resultado_mov.mensaje,
                    )
                )

        estado_general = "ok" if aplicados and errores == 0 else "revisar" if errores or omitidos else "sin_datos"

        return ResultadoAplicacionInventario(
            total_lineas=len(lineas_comparacion),
            ajustes_aplicados=aplicados,
            ajustes_omitidos=omitidos,
            errores=errores,
            lineas=resultados,
            estado=estado_general,
        )

    def exportar_txt(
        self,
        ruta_destino: str = "DATOS/db/ajustes_inventario_4_3_11_4.txt",
        motivo: str = "Ajuste por inventario físico",
    ) -> ResultadoAplicacionInventario:
        resultado = self.aplicar(motivo=motivo)
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.3.11.4 - APLICADOR DE AJUSTES DE INVENTARIO",
            "=" * 78,
            f"Total líneas comparación: {resultado.total_lineas}",
            f"Ajustes aplicados: {resultado.ajustes_aplicados}",
            f"Ajustes omitidos: {resultado.ajustes_omitidos}",
            f"Errores: {resultado.errores}",
            f"Estado: {resultado.estado}",
            "",
            "DETALLE",
            "-" * 78,
        ]

        if not resultado.lineas:
            lineas.append("No hay líneas para aplicar.")

        for item in resultado.lineas:
            estado = "APLICADO" if item.aplicado else "OMITIDO"
            if "no válido" in item.mensaje or "No existe" in item.mensaje:
                estado = "ERROR"

            lineas.append(
                f"[{estado}] {item.codigo} | {item.articulo} | "
                f"Sistema: {item.stock_sistema} {item.unidad} | "
                f"Contado: {item.stock_contado} {item.unidad} | "
                f"Dif: {item.diferencia} {item.unidad} | "
                f"Comparación: {item.estado_comparacion} | "
                f"Mov: {item.id_movimiento or '-'} | {item.mensaje}"
            )

        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return resultado

    def _leer_json_dict(self, ruta: Path) -> Dict[str, Any]:
        if not ruta.exists():
            return {}
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return contenido if isinstance(contenido, dict) else {}

    def _numero(self, valor: Any) -> Optional[float]:
        if valor is None or str(valor).strip() == "":
            return None
        if isinstance(valor, (int, float)):
            return float(valor)
        try:
            return float(str(valor).replace(",", "."))
        except ValueError:
            return None


__all__ = [
    "AplicadorAjustesInventario43114",
    "ResultadoAplicacionInventario",
    "AjusteInventarioAplicado",
]
