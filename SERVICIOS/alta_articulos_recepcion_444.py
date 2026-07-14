from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from SERVICIOS.gestor_articulos_416 import GestorArticulos416


@dataclass
class ArticuloNuevoCreado444:
    producto_texto: str
    codigo_creado: Optional[str]
    nombre_creado: Optional[str]
    proveedor: Optional[str]
    familia: Optional[str]
    precio: Optional[float]
    cantidad_recibida: float
    unidad_recibida: str
    creado: bool
    mensaje: str


@dataclass
class ResultadoAltaArticulosRecepcion444:
    fecha: str
    total_pendientes: int
    creados: int
    no_creados: int
    articulos: List[ArticuloNuevoCreado444] = field(default_factory=list)
    estado: str = "sin_datos"


class AltaArticulosDesdeRecepcion444:
    """
    Host AI 4.4.4 — Alta automática/controlada de artículos nuevos desde recepción.

    Entrada:
    DATOS/db/recepcion_borrador_4_4_2.json

    Acciones:
    - Lee líneas con accion_sugerida == crear_articulo_pendiente.
    - Crea artículo en DATOS/db/articulos.json usando GestorArticulos416.
    - NO suma stock todavía: tras crear, se debe volver a validar/aplicar recepción.

    Motivo:
    Evita sumar stock a un artículo recién creado sin revisar unidad/familia/formato.
    """

    def __init__(
        self,
        ruta_borrador: str = "DATOS/db/recepcion_borrador_4_4_2.json",
        ruta_articulos: str = "DATOS/db/articulos.json",
    ) -> None:
        self.ruta_borrador = Path(ruta_borrador)
        self.ruta_articulos = Path(ruta_articulos)

    def crear_pendientes(self, familia_default: str = "Pendiente clasificar") -> ResultadoAltaArticulosRecepcion444:
        borrador = self._leer_json_dict(self.ruta_borrador)
        lineas = borrador.get("lineas_validadas", []) if isinstance(borrador, dict) else []

        gestor = GestorArticulos416(str(self.ruta_articulos))

        articulos_resultado: List[ArticuloNuevoCreado444] = []
        pendientes = 0
        creados = 0
        no_creados = 0

        for linea in lineas:
            if str(linea.get("accion_sugerida", "") or "") != "crear_articulo_pendiente":
                continue

            pendientes += 1
            producto = str(linea.get("producto_texto", "") or "").strip()
            proveedor = self._texto(linea.get("proveedor_texto"))
            precio = self._numero(linea.get("precio_unitario"))
            cantidad = self._numero(linea.get("cantidad")) or 0.0
            unidad = str(linea.get("unidad", "") or "")

            if not producto:
                no_creados += 1
                articulos_resultado.append(
                    ArticuloNuevoCreado444(
                        producto_texto=producto,
                        codigo_creado=None,
                        nombre_creado=None,
                        proveedor=proveedor,
                        familia=familia_default,
                        precio=precio,
                        cantidad_recibida=cantidad,
                        unidad_recibida=unidad,
                        creado=False,
                        mensaje="No se puede crear artículo sin nombre.",
                    )
                )
                continue

            resultado = gestor.alta_articulo(
                nombre=producto,
                proveedor=proveedor,
                familia=familia_default,
                precio=precio,
                observaciones=f"Creado desde recepción mercancía 4.4.4. Unidad recibida: {unidad}. Cantidad recibida pendiente de aplicar: {cantidad}.",
            )

            creado = resultado.accion == "creado"
            if creado:
                creados += 1
            else:
                no_creados += 1

            articulos_resultado.append(
                ArticuloNuevoCreado444(
                    producto_texto=producto,
                    codigo_creado=resultado.codigo,
                    nombre_creado=resultado.nombre,
                    proveedor=proveedor,
                    familia=familia_default,
                    precio=precio,
                    cantidad_recibida=cantidad,
                    unidad_recibida=unidad,
                    creado=creado,
                    mensaje=resultado.mensaje,
                )
            )

        estado = "sin_pendientes" if pendientes == 0 else "creados" if creados and no_creados == 0 else "creados_con_observaciones" if creados else "no_creados"

        return ResultadoAltaArticulosRecepcion444(
            fecha=datetime.now().isoformat(timespec="seconds"),
            total_pendientes=pendientes,
            creados=creados,
            no_creados=no_creados,
            articulos=articulos_resultado,
            estado=estado,
        )

    def crear_y_exportar(
        self,
        ruta_json: str = "DATOS/db/articulos_nuevos_recepcion_4_4_4.json",
        ruta_txt: str = "DATOS/db/articulos_nuevos_recepcion_4_4_4.txt",
        familia_default: str = "Pendiente clasificar",
    ) -> ResultadoAltaArticulosRecepcion444:
        resultado = self.crear_pendientes(familia_default=familia_default)

        ruta_json_path = Path(ruta_json)
        ruta_json_path.parent.mkdir(parents=True, exist_ok=True)
        ruta_json_path.write_text(json.dumps(asdict(resultado), ensure_ascii=False, indent=2), encoding="utf-8")

        self._exportar_txt(resultado, ruta_txt)
        return resultado

    def _exportar_txt(self, resultado: ResultadoAltaArticulosRecepcion444, ruta_txt: str) -> None:
        ruta = Path(ruta_txt)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.4.4 - ALTA ARTÍCULOS NUEVOS DESDE RECEPCIÓN",
            "=" * 78,
            f"Fecha: {resultado.fecha}",
            f"Pendientes detectados: {resultado.total_pendientes}",
            f"Creados: {resultado.creados}",
            f"No creados: {resultado.no_creados}",
            f"Estado: {resultado.estado}",
            "",
            "DETALLE",
            "-" * 78,
        ]

        if not resultado.articulos:
            lineas.append("No había artículos pendientes de crear.")

        for idx, item in enumerate(resultado.articulos, start=1):
            estado = "CREADO" if item.creado else "NO CREADO"
            lineas.append(
                f"{idx}. [{estado}] {item.producto_texto} | Código: {item.codigo_creado or '-'} | "
                f"Proveedor: {item.proveedor or '-'} | Familia: {item.familia or '-'} | "
                f"Precio: {item.precio} | Recibido: {item.cantidad_recibida} {item.unidad_recibida}"
            )
            lineas.append(f"   - {item.mensaje}")

        lineas.extend([
            "",
            "SIGUIENTE PASO",
            "-" * 78,
            "Vuelve a ejecutar 4.4.2 para validar otra vez la recepción. Si ahora encuentra los artículos, aplica 4.4.3.",
        ])

        ruta.write_text("\n".join(lineas), encoding="utf-8")

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
    "AltaArticulosDesdeRecepcion444",
    "ResultadoAltaArticulosRecepcion444",
    "ArticuloNuevoCreado444",
]
