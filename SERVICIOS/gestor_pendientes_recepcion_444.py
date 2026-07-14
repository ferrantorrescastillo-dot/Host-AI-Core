from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from SERVICIOS.gestor_articulos_416 import GestorArticulos416


@dataclass
class ArticuloPendienteRecepcion:
    articulo_original: str
    proveedor: Optional[str]
    cantidad: float
    unidad: str
    precio_unitario: Optional[float]
    familia_sugerida: Optional[str]
    codigo_creado: Optional[str]
    creado: bool
    mensaje: str


@dataclass
class ResultadoGestionPendientesRecepcion:
    total_pendientes: int
    creados: int
    no_creados: int
    pendientes: List[ArticuloPendienteRecepcion] = field(default_factory=list)
    estado: str = "sin_datos"


class GestorPendientesRecepcion444:
    """
    4.4.4 - Gestiona artículos no encontrados en una recepción.

    Entrada:
    DATOS/db/recepcion_mercancia_validada_4_4_2.json

    Crea artículos opcionalmente en:
    DATOS/db/articulos.json

    Seguridad:
    - Por defecto NO crea artículos automáticamente.
    - Para crear, usar crear=True.
    """

    def __init__(
        self,
        ruta_recepcion: str = "DATOS/db/recepcion_mercancia_validada_4_4_2.json",
        ruta_articulos: str = "DATOS/db/articulos.json",
    ) -> None:
        self.ruta_recepcion = Path(ruta_recepcion)
        self.ruta_articulos = Path(ruta_articulos)

    def procesar(self, crear: bool = False) -> ResultadoGestionPendientesRecepcion:
        recepcion = self._leer_json_dict(self.ruta_recepcion)
        proveedor_general = self._texto(recepcion.get("proveedor"))
        lineas = self._extraer_lineas(recepcion)

        pendientes_raw = []
        for linea in lineas:
            codigo = self._texto(linea.get("codigo")) or self._texto(linea.get("codigo_articulo"))
            if codigo:
                continue
            pendientes_raw.append(linea)

        gestor = GestorArticulos416(str(self.ruta_articulos))
        resultados: List[ArticuloPendienteRecepcion] = []
        creados = 0
        no_creados = 0

        for linea in pendientes_raw:
            articulo = self._texto(linea.get("articulo")) or self._texto(linea.get("nombre")) or self._texto(linea.get("articulo_original")) or ""
            proveedor = self._texto(linea.get("proveedor")) or proveedor_general
            cantidad = self._numero(linea.get("cantidad")) or 0.0
            unidad = self._texto(linea.get("unidad")) or ""
            precio = self._numero(linea.get("precio_unitario"))
            familia = self._sugerir_familia(articulo)

            codigo_creado = None
            creado = False
            mensaje = "Pendiente de revisión. No creado automáticamente."

            if crear and articulo:
                alta = gestor.alta_articulo(
                    nombre=articulo,
                    proveedor=proveedor,
                    familia=familia,
                    precio=precio,
                    observaciones=f"Creado desde recepción 4.4.4. Unidad recibida: {unidad}.",
                )
                creado = alta.accion == "creado"
                codigo_creado = alta.codigo
                mensaje = alta.mensaje
                if creado:
                    creados += 1
                else:
                    no_creados += 1
            else:
                no_creados += 1

            resultados.append(
                ArticuloPendienteRecepcion(
                    articulo_original=articulo,
                    proveedor=proveedor,
                    cantidad=cantidad,
                    unidad=unidad,
                    precio_unitario=precio,
                    familia_sugerida=familia,
                    codigo_creado=codigo_creado,
                    creado=creado,
                    mensaje=mensaje,
                )
            )

        estado = "creados" if creados and no_creados == 0 else "pendientes" if no_creados else "sin_pendientes"

        return ResultadoGestionPendientesRecepcion(
            total_pendientes=len(pendientes_raw),
            creados=creados,
            no_creados=no_creados,
            pendientes=resultados,
            estado=estado,
        )

    def exportar(
        self,
        crear: bool = False,
        ruta_json: str = "DATOS/db/pendientes_recepcion_4_4_4.json",
        ruta_txt: str = "DATOS/db/pendientes_recepcion_4_4_4.txt",
    ) -> ResultadoGestionPendientesRecepcion:
        resultado = self.procesar(crear=crear)

        ruta_json_path = Path(ruta_json)
        ruta_json_path.parent.mkdir(parents=True, exist_ok=True)
        ruta_json_path.write_text(json.dumps(asdict(resultado), ensure_ascii=False, indent=2), encoding="utf-8")

        ruta_txt_path = Path(ruta_txt)
        ruta_txt_path.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.4.4 - ARTÍCULOS PENDIENTES DE RECEPCIÓN",
            "=" * 74,
            f"Pendientes: {resultado.total_pendientes}",
            f"Creados: {resultado.creados}",
            f"No creados: {resultado.no_creados}",
            f"Estado: {resultado.estado}",
            f"Modo creación: {'ACTIVO' if crear else 'REVISIÓN'}",
            "",
            "DETALLE",
            "-" * 74,
        ]

        if not resultado.pendientes:
            lineas.append("No hay artículos pendientes.")

        for item in resultado.pendientes:
            estado = "CREADO" if item.creado else "PENDIENTE"
            lineas.append(
                f"[{estado}] {item.articulo_original} | Proveedor: {item.proveedor or '-'} | "
                f"{item.cantidad} {item.unidad} | Precio: {item.precio_unitario if item.precio_unitario is not None else '-'} | "
                f"Familia sugerida: {item.familia_sugerida or '-'} | Código: {item.codigo_creado or '-'} | {item.mensaje}"
            )

        ruta_txt_path.write_text("\n".join(lineas), encoding="utf-8")
        return resultado

    def _extraer_lineas(self, recepcion: Dict[str, Any]) -> List[Dict[str, Any]]:
        for key in ["lineas_validadas", "lineas", "items", "productos"]:
            value = recepcion.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        return []

    def _sugerir_familia(self, nombre: str) -> Optional[str]:
        n = (nombre or "").lower()
        reglas = [
            ("Arroces y cereales", ["arroz", "pasta", "fideo"]),
            ("Aceites", ["aceite", "aove"]),
            ("Verduras", ["tomate", "cebolla", "puerro", "patata", "pimiento", "lechuga"]),
            ("Frutas", ["naranja", "limon", "limón", "manzana", "pera"]),
            ("Carnes", ["pollo", "ternera", "cerdo", "butifarra", "hamburguesa"]),
            ("Pescados", ["bacalao", "merluza", "salmón", "salmon", "atun", "atún"]),
            ("Mariscos", ["gamba", "langostino", "pulpo", "sepia", "calamar"]),
            ("Lácteos", ["leche", "queso", "nata", "mantequilla"]),
            ("Bebidas", ["agua", "vino", "coca cola", "fanta", "cerveza"]),
            ("Panadería", ["pan", "brioche", "baguette"]),
            ("Varios", []),
        ]
        for familia, palabras in reglas:
            if any(p in n for p in palabras):
                return familia
        return "Varios"

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
        limpio = str(valor).replace("€", "").replace(" ", "")
        if "," in limpio and "." in limpio:
            limpio = limpio.replace(".", "").replace(",", ".")
        else:
            limpio = limpio.replace(",", ".")
        try:
            return float(limpio)
        except ValueError:
            return None


__all__ = ["GestorPendientesRecepcion444", "ResultadoGestionPendientesRecepcion", "ArticuloPendienteRecepcion"]
