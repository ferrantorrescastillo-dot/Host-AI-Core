from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, List, Dict, Any


@dataclass
class Merma:
    articulo: str
    cantidad: float
    unidad: str = "kg"
    coste_unitario: float = 0.0
    motivo: str = "no especificado"
    area: str = "cocina"

    @property
    def coste_total(self) -> float:
        return round(float(self.cantidad) * float(self.coste_unitario), 4)


def registrar_merma(articulo: str, cantidad: float, unidad: str = "kg", coste_unitario: float = 0.0,
                    motivo: str = "no especificado", area: str = "cocina") -> Dict[str, Any]:
    if not articulo or not str(articulo).strip():
        raise ValueError("El artículo de la merma es obligatorio")
    if cantidad < 0:
        raise ValueError("La cantidad de merma no puede ser negativa")
    if coste_unitario < 0:
        raise ValueError("El coste unitario no puede ser negativo")
    merma = Merma(str(articulo).strip(), float(cantidad), unidad, float(coste_unitario), motivo, area)
    data = asdict(merma)
    data["coste_total"] = merma.coste_total
    return data


def calcular_coste_mermas(mermas: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    lineas: List[Dict[str, Any]] = []
    total = 0.0
    por_motivo: Dict[str, float] = {}
    por_area: Dict[str, float] = {}
    for item in mermas:
        linea = registrar_merma(
            item.get("articulo", ""),
            float(item.get("cantidad", 0)),
            item.get("unidad", "kg"),
            float(item.get("coste_unitario", 0)),
            item.get("motivo", "no especificado"),
            item.get("area", "cocina"),
        )
        lineas.append(linea)
        coste = linea["coste_total"]
        total += coste
        por_motivo[linea["motivo"]] = round(por_motivo.get(linea["motivo"], 0.0) + coste, 4)
        por_area[linea["area"]] = round(por_area.get(linea["area"], 0.0) + coste, 4)
    return {
        "total_mermas": round(total, 4),
        "numero_lineas": len(lineas),
        "por_motivo": por_motivo,
        "por_area": por_area,
        "lineas": lineas,
    }


def generar_recomendaciones_mermas(resumen: Dict[str, Any], umbral_alerta: float = 25.0) -> List[str]:
    recomendaciones: List[str] = []
    total = float(resumen.get("total_mermas", 0))
    if total >= umbral_alerta:
        recomendaciones.append(f"Revisar mermas: coste acumulado {total:.2f} € supera el umbral de {umbral_alerta:.2f} €.")
    motivos = resumen.get("por_motivo", {}) or {}
    if motivos:
        motivo_principal = max(motivos, key=motivos.get)
        recomendaciones.append(f"Principal causa de merma: {motivo_principal} ({motivos[motivo_principal]:.2f} €).")
    if not recomendaciones:
        recomendaciones.append("Mermas dentro de control.")
    return recomendaciones
