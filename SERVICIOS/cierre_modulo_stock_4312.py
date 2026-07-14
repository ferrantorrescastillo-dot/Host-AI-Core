from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
import json


@dataclass
class ResultadoChequeoStock:
    nombre: str
    ok: bool
    detalle: str


@dataclass
class InformeCierreModuloStock:
    articulos_stock: int
    movimientos_stock: int
    pedidos_confirmados: int
    registros_inventario: int
    ajustes_inventario: int
    chequeos: List[ResultadoChequeoStock] = field(default_factory=list)
    estado_final: str = "sin_datos"
    bloque_siguiente: str = "Host AI 4.4 - Recepción inteligente de mercancía"
    recomendaciones: List[str] = field(default_factory=list)


class CierreModuloStock4312:
    """
    Cierre del módulo Host AI 4.3 Stock.

    Valida:
    - stock inicial
    - movimientos
    - pedidos confirmados
    - inventario
    - ajustes de inventario
    - informes clave

    No modifica datos.
    """

    def __init__(self, ruta_db: str = "DATOS/db") -> None:
        self.ruta_db = Path(ruta_db)

    def cerrar(self) -> InformeCierreModuloStock:
        stock = self._leer_json_lista(self.ruta_db / "stock_inicial.json")
        movimientos = self._leer_json_lista(self.ruta_db / "stock_movimientos.json")
        pedidos = self._leer_json_lista(self.ruta_db / "pedidos_confirmados.json")
        inventario = self._leer_json_lista(self.ruta_db / "inventario_contado_4_3_11_2.json")

        ajustes_inventario = [
            m for m in movimientos
            if str(m.get("tipo", "")).lower() == "ajuste"
            and "inventario" in str(m.get("motivo", "")).lower()
        ]

        chequeos: List[ResultadoChequeoStock] = []

        chequeos.append(self._chequear_archivo_json("Stock inicial", self.ruta_db / "stock_inicial.json", stock))
        chequeos.append(self._chequear_movimientos(movimientos))
        chequeos.append(self._chequear_archivo_opcional("Pedidos confirmados", self.ruta_db / "pedidos_confirmados.json", pedidos))
        chequeos.append(self._chequear_archivo_opcional("Inventario contado", self.ruta_db / "inventario_contado_4_3_11_2.json", inventario))
        chequeos.append(self._chequear_txt("Informe stock inicial", self.ruta_db / "informe_stock_inicial_4_3_3.txt"))
        chequeos.append(self._chequear_txt("Alertas stock bajo", self.ruta_db / "alertas_stock_bajo_4_3_4.txt"))
        chequeos.append(self._chequear_txt("Historial movimientos", self.ruta_db / "historial_movimientos_stock_4_3_10.txt"))
        chequeos.append(self._chequear_txt("Informe final inventario", self.ruta_db / "informe_final_inventario_4_3_11_5.txt"))

        estado_final = self._estado_final(chequeos, stock)
        recomendaciones = self._recomendaciones(chequeos, stock, movimientos, inventario)

        return InformeCierreModuloStock(
            articulos_stock=len(stock),
            movimientos_stock=len(movimientos),
            pedidos_confirmados=len(pedidos),
            registros_inventario=len(inventario),
            ajustes_inventario=len(ajustes_inventario),
            chequeos=chequeos,
            estado_final=estado_final,
            recomendaciones=recomendaciones,
        )

    def exportar_txt(self, ruta_destino: str = "DATOS/db/cierre_modulo_stock_4_3_12.txt") -> InformeCierreModuloStock:
        informe = self.cerrar()
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.3.12 - CIERRE MÓDULO STOCK",
            "=" * 76,
            f"Artículos con stock cargado: {informe.articulos_stock}",
            f"Movimientos de stock: {informe.movimientos_stock}",
            f"Pedidos confirmados: {informe.pedidos_confirmados}",
            f"Registros inventario contado: {informe.registros_inventario}",
            f"Ajustes de inventario detectados: {informe.ajustes_inventario}",
            "",
            "CHEQUEOS",
            "-" * 76,
        ]

        for chequeo in informe.chequeos:
            estado = "OK" if chequeo.ok else "OBSERVACIÓN"
            lineas.append(f"[{estado}] {chequeo.nombre}: {chequeo.detalle}")

        lineas.extend(["", "RECOMENDACIONES", "-" * 76])
        for recomendacion in informe.recomendaciones:
            lineas.append(f"- {recomendacion}")

        lineas.extend([
            "",
            f"ESTADO FINAL: {informe.estado_final}",
            f"BLOQUE SIGUIENTE: {informe.bloque_siguiente}",
        ])

        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return informe

    def _chequear_archivo_json(self, nombre: str, ruta: Path, datos: List[Dict[str, Any]]) -> ResultadoChequeoStock:
        if not ruta.exists():
            return ResultadoChequeoStock(nombre, False, f"No existe {ruta.name}.")
        if not datos:
            return ResultadoChequeoStock(nombre, False, f"{ruta.name} existe pero está vacío.")
        return ResultadoChequeoStock(nombre, True, f"{len(datos)} registros.")

    def _chequear_archivo_opcional(self, nombre: str, ruta: Path, datos: List[Dict[str, Any]]) -> ResultadoChequeoStock:
        if not ruta.exists():
            return ResultadoChequeoStock(nombre, False, f"No existe todavía {ruta.name}. Puede ser normal si no se ha usado este flujo.")
        return ResultadoChequeoStock(nombre, True, f"{len(datos)} registros.")

    def _chequear_txt(self, nombre: str, ruta: Path) -> ResultadoChequeoStock:
        if not ruta.exists():
            return ResultadoChequeoStock(nombre, False, f"No existe {ruta.name}.")
        if ruta.stat().st_size == 0:
            return ResultadoChequeoStock(nombre, False, f"{ruta.name} está vacío.")
        return ResultadoChequeoStock(nombre, True, f"Archivo generado correctamente.")

    def _chequear_movimientos(self, movimientos: List[Dict[str, Any]]) -> ResultadoChequeoStock:
        if not movimientos:
            return ResultadoChequeoStock(
                "Movimientos de stock",
                False,
                "No hay movimientos registrados todavía. El motor existe, pero falta uso real.",
            )

        tipos = {str(m.get("tipo", "")).lower() for m in movimientos}
        return ResultadoChequeoStock(
            "Movimientos de stock",
            True,
            f"{len(movimientos)} movimientos. Tipos detectados: {', '.join(sorted(tipos))}.",
        )

    def _estado_final(self, chequeos: List[ResultadoChequeoStock], stock: List[Dict[str, Any]]) -> str:
        if not stock:
            return "no_apto"
        fallos = [c for c in chequeos if not c.ok]
        if fallos:
            return "cerrado_con_observaciones"
        return "cerrado"

    def _recomendaciones(
        self,
        chequeos: List[ResultadoChequeoStock],
        stock: List[Dict[str, Any]],
        movimientos: List[Dict[str, Any]],
        inventario: List[Dict[str, Any]],
    ) -> List[str]:
        recomendaciones: List[str] = []

        if not stock:
            recomendaciones.append("Cargar stock inicial antes de avanzar.")
        if not movimientos:
            recomendaciones.append("Probar al menos una entrada, salida o ajuste para validar historial real.")
        if not inventario:
            recomendaciones.append("Hacer una prueba de inventario físico cuando sea posible.")
        for chequeo in chequeos:
            if not chequeo.ok:
                recomendaciones.append(f"Revisar: {chequeo.nombre} -> {chequeo.detalle}")

        if not recomendaciones:
            recomendaciones.append("Módulo Stock cerrado correctamente. Se puede avanzar a recepción inteligente de mercancía.")

        return recomendaciones

    def _leer_json_lista(self, ruta: Path) -> List[Dict[str, Any]]:
        if not ruta.exists():
            return []
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return contenido if isinstance(contenido, list) else []


__all__ = [
    "CierreModuloStock4312",
    "InformeCierreModuloStock",
    "ResultadoChequeoStock",
]
