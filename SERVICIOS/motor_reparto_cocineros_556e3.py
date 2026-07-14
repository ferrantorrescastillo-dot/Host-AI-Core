from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from SERVICIOS.motor_planificacion_recetas_reales_556e31 import MotorPlanificacionRecetasReales556E31, formatear_plan_real_556e31


class MotorRepartoCocineros556E3:
    """Compatibilidad 5.5.6E.3 corregida por 5.5.6E.3.1.

    Ya no genera tiempos genéricos. Exige ficha de producción validada y reutiliza
    el planificador basado en procesos reales.
    """
    VERSION = "5.5.6E.3.1"

    def __init__(self, base_dir: Path, motor_recursos: Optional[Any] = None):
        self.base_dir = Path(base_dir).resolve()
        self.motor = MotorPlanificacionRecetasReales556E31(self.base_dir)

    def repartir(self, producciones: List[Dict[str, Any]], cocineros: int | Iterable[str] | None = None,
                 inicio_jornada: str = "08:00", fin_jornada: str = "15:30") -> Dict[str, Any]:
        if len(producciones) != 1:
            return {
                "version": self.VERSION,
                "estado": "MULTIPRODUCCION_REQUIERE_5.5.6E.4.1",
                "puede_planificar": False,
                "receta": "varias producciones",
                "motivo": "Primero valida las fichas individuales; la planificación conjunta se hará con el motor de paralelización.",
                "datos_reales_modificados": False,
            }
        p = producciones[0]
        return self.motor.planificar(
            str(p["receta"]), float(p["objetivo"]), str(p.get("unidad", "personas")),
            cocineros=cocineros or 3, inicio_jornada=inicio_jornada, fin_jornada=fin_jornada,
        )


def formatear_reparto_556e3(resultado: Dict[str, Any]) -> str:
    return formatear_plan_real_556e31(resultado)


__all__ = ["MotorRepartoCocineros556E3", "formatear_reparto_556e3"]
