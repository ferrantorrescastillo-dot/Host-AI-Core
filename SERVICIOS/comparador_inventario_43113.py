from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import Counter, defaultdict
import json


@dataclass
class LineaComparacionInventario:
    codigo: str
    articulo: str
    unidad: str
    stock_sistema: float
    stock_contado: float
    diferencia: float
    ubicacion: Optional[str]
    proveedor: Optional[str]
    familia: Optional[str]
    estado: str
    prioridad: str
    mensaje: str


@dataclass
class InformeComparacionInventario:
    total_contados: int
    ok: int
    faltantes: int
    sobrantes: int
    revisar: int
    diferencia_por_unidad: Dict[str, float]
    estados: Dict[str, int]
    prioridades: Dict[str, int]
    lineas: List[LineaComparacionInventario] = field(default_factory=list)
    estado_general: str = "sin_datos"


class ComparadorInventario43113:
    """
    Compara inventario contado contra stock sistema.

    Entrada:
    DATOS/db/inventario_contado_4_3_11_2.json

    Salidas:
    DATOS/db/comparacion_inventario_4_3_11_3.json
    DATOS/db/comparacion_inventario_4_3_11_3.txt

    No modifica stock_inicial.json.
    """

    def __init__(self, ruta_inventario: str = "DATOS/db/inventario_contado_4_3_11_2.json") -> None:
        self.ruta_inventario = Path(ruta_inventario)

    def comparar(self) -> InformeComparacionInventario:
        registros = self._leer_json_lista(self.ruta_inventario)
        lineas: List[LineaComparacionInventario] = []
        diferencias_unidad: Dict[str, float] = defaultdict(float)

        for registro in registros:
            codigo = str(registro.get("codigo", "") or "")
            articulo = str(registro.get("articulo", "") or "")
            unidad = str(registro.get("unidad", "") or "")
            stock_sistema = self._numero(registro.get("stock_sistema")) or 0.0
            stock_contado = self._numero(registro.get("stock_contado")) or 0.0
            diferencia = round(stock_contado - stock_sistema, 4)

            estado, prioridad, mensaje = self._clasificar_diferencia(
                stock_sistema=stock_sistema,
                stock_contado=stock_contado,
                diferencia=diferencia,
                unidad=unidad,
            )

            diferencias_unidad[unidad or "SIN_UNIDAD"] += diferencia

            lineas.append(
                LineaComparacionInventario(
                    codigo=codigo,
                    articulo=articulo,
                    unidad=unidad,
                    stock_sistema=stock_sistema,
                    stock_contado=stock_contado,
                    diferencia=diferencia,
                    ubicacion=self._texto(registro.get("ubicacion")),
                    proveedor=self._texto(registro.get("proveedor")),
                    familia=self._texto(registro.get("familia")),
                    estado=estado,
                    prioridad=prioridad,
                    mensaje=mensaje,
                )
            )

        # Orden: revisar alta primero, luego faltantes/sobrantes, luego OK.
        orden_prioridad = {"alta": 0, "media": 1, "baja": 2}
        orden_estado = {"revisar": 0, "faltante": 1, "sobrante": 2, "ok": 3}
        lineas.sort(key=lambda x: (orden_prioridad.get(x.prioridad, 9), orden_estado.get(x.estado, 9), x.codigo))

        estados = Counter(linea.estado for linea in lineas)
        prioridades = Counter(linea.prioridad for linea in lineas)

        estado_general = self._estado_general(estados, len(lineas))

        return InformeComparacionInventario(
            total_contados=len(lineas),
            ok=estados.get("ok", 0),
            faltantes=estados.get("faltante", 0),
            sobrantes=estados.get("sobrante", 0),
            revisar=estados.get("revisar", 0),
            diferencia_por_unidad={unidad: round(cantidad, 4) for unidad, cantidad in diferencias_unidad.items()},
            estados=dict(estados),
            prioridades=dict(prioridades),
            lineas=lineas,
            estado_general=estado_general,
        )

    def exportar(
        self,
        ruta_json: str = "DATOS/db/comparacion_inventario_4_3_11_3.json",
        ruta_txt: str = "DATOS/db/comparacion_inventario_4_3_11_3.txt",
    ) -> InformeComparacionInventario:
        informe = self.comparar()

        ruta_json_path = Path(ruta_json)
        ruta_json_path.parent.mkdir(parents=True, exist_ok=True)
        ruta_json_path.write_text(json.dumps(asdict(informe), ensure_ascii=False, indent=2), encoding="utf-8")

        ruta_txt_path = Path(ruta_txt)
        ruta_txt_path.parent.mkdir(parents=True, exist_ok=True)

        lineas = [
            "HOST AI 4.3.11.3 - COMPARADOR INTELIGENTE DE INVENTARIO",
            "=" * 78,
            f"Artículos contados: {informe.total_contados}",
            f"OK: {informe.ok}",
            f"Faltantes: {informe.faltantes}",
            f"Sobrantes: {informe.sobrantes}",
            f"Revisar: {informe.revisar}",
            f"Estado general: {informe.estado_general}",
            "",
            "DIFERENCIA TOTAL POR UNIDAD",
            "-" * 78,
        ]

        if not informe.diferencia_por_unidad:
            lineas.append("Sin diferencias registradas.")

        for unidad, diferencia in informe.diferencia_por_unidad.items():
            lineas.append(f"{unidad}: {diferencia}")

        lineas.extend(["", "DETALLE", "-" * 78])

        if not informe.lineas:
            lineas.append("No hay inventario contado para comparar.")

        for item in informe.lineas:
            lineas.append(
                f"[{item.prioridad.upper()}] {item.estado.upper()} | {item.codigo} | {item.articulo} | "
                f"Sistema: {item.stock_sistema} {item.unidad} | "
                f"Contado: {item.stock_contado} {item.unidad} | "
                f"Dif: {item.diferencia} {item.unidad} | "
                f"Ubicación: {item.ubicacion or '-'} | {item.mensaje}"
            )

        ruta_txt_path.write_text("\n".join(lineas), encoding="utf-8")
        return informe

    def _clasificar_diferencia(self, stock_sistema: float, stock_contado: float, diferencia: float, unidad: str) -> tuple[str, str, str]:
        if diferencia == 0:
            return "ok", "baja", "Coincide con el stock del sistema."

        abs_diff = abs(diferencia)

        # Porcentaje de diferencia respecto al sistema.
        if stock_sistema > 0:
            ratio = abs_diff / stock_sistema
        else:
            ratio = 1.0 if stock_contado > 0 else 0.0

        if ratio >= 0.5 and abs_diff >= 2:
            prioridad = "alta"
            estado = "revisar"
            mensaje = "Diferencia grande. Revisar antes de aplicar ajuste."
        elif diferencia < 0:
            prioridad = "media" if abs_diff >= 1 else "baja"
            estado = "faltante"
            mensaje = "Hay menos stock real que en el sistema."
        else:
            prioridad = "media" if abs_diff >= 1 else "baja"
            estado = "sobrante"
            mensaje = "Hay más stock real que en el sistema."

        return estado, prioridad, mensaje

    def _estado_general(self, estados: Counter, total: int) -> str:
        if total == 0:
            return "sin_datos"
        if estados.get("revisar", 0):
            return "revisar_antes_de_aplicar"
        if estados.get("faltante", 0) or estados.get("sobrante", 0):
            return "pendiente_de_aplicar"
        return "ok"

    def _leer_json_lista(self, ruta: Path) -> List[Dict[str, Any]]:
        if not ruta.exists():
            return []
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return contenido if isinstance(contenido, list) else []

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
        try:
            return float(str(valor).replace(",", "."))
        except ValueError:
            return None


__all__ = [
    "ComparadorInventario43113",
    "InformeComparacionInventario",
    "LineaComparacionInventario",
]
