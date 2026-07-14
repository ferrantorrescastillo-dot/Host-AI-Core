"""
Host AI - RC3.2 Rendimiento para Piloto

Servicio ligero para medir tiempos de ejecución de funciones críticas
sin modificar los motores existentes.

Objetivo:
- Detectar operaciones lentas.
- Preparar Host AI para pruebas reales en restaurante.
- Mantener mediciones simples, trazables y sin dependencias externas.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ResultadoMedicionRendimiento:
    nombre: str
    tiempo_ms: float
    estado: str
    mensaje: str
    resultado: Optional[Any] = None


class MedidorRendimientoPiloto:
    """
    Mide tiempos de ejecución de funciones o procesos de Host AI.

    No decide lógica de negocio.
    No modifica datos.
    Solo mide y clasifica tiempos.
    """

    def __init__(self, limite_ok_ms: float = 500.0, limite_aviso_ms: float = 1500.0) -> None:
        self.limite_ok_ms = limite_ok_ms
        self.limite_aviso_ms = limite_aviso_ms
        self.mediciones: List[ResultadoMedicionRendimiento] = []

    def medir(self, nombre: str, funcion: Callable[..., Any], *args: Any, **kwargs: Any) -> ResultadoMedicionRendimiento:
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la medición no puede estar vacío.")

        inicio = perf_counter()

        try:
            resultado = funcion(*args, **kwargs)
            estado_error = None
        except Exception as exc:  # pragma: no cover - se valida en test específico
            resultado = None
            estado_error = exc

        fin = perf_counter()
        tiempo_ms = round((fin - inicio) * 1000, 3)

        if estado_error is not None:
            medicion = ResultadoMedicionRendimiento(
                nombre=nombre,
                tiempo_ms=tiempo_ms,
                estado="error",
                mensaje=f"Error durante la ejecución: {estado_error}",
                resultado=None,
            )
        else:
            estado = self._clasificar(tiempo_ms)
            medicion = ResultadoMedicionRendimiento(
                nombre=nombre,
                tiempo_ms=tiempo_ms,
                estado=estado,
                mensaje=self._mensaje_estado(estado, tiempo_ms),
                resultado=resultado,
            )

        self.mediciones.append(medicion)
        return medicion

    def resumen(self) -> Dict[str, Any]:
        total = len(self.mediciones)
        por_estado: Dict[str, int] = {}

        for medicion in self.mediciones:
            por_estado[medicion.estado] = por_estado.get(medicion.estado, 0) + 1

        tiempo_total_ms = round(sum(m.tiempo_ms for m in self.mediciones), 3)
        tiempo_medio_ms = round(tiempo_total_ms / total, 3) if total else 0.0

        return {
            "total_mediciones": total,
            "por_estado": por_estado,
            "tiempo_total_ms": tiempo_total_ms,
            "tiempo_medio_ms": tiempo_medio_ms,
            "estado_general": self._estado_general(por_estado),
        }

    def _clasificar(self, tiempo_ms: float) -> str:
        if tiempo_ms <= self.limite_ok_ms:
            return "ok"
        if tiempo_ms <= self.limite_aviso_ms:
            return "aviso"
        return "lento"

    def _mensaje_estado(self, estado: str, tiempo_ms: float) -> str:
        if estado == "ok":
            return f"Ejecución correcta en {tiempo_ms} ms."
        if estado == "aviso":
            return f"Ejecución aceptable pero revisable en {tiempo_ms} ms."
        return f"Ejecución lenta para piloto: {tiempo_ms} ms."

    def _estado_general(self, por_estado: Dict[str, int]) -> str:
        if por_estado.get("error", 0):
            return "error"
        if por_estado.get("lento", 0):
            return "revisar"
        if por_estado.get("aviso", 0):
            return "aceptable"
        return "ok"


__all__ = [
    "MedidorRendimientoPiloto",
    "ResultadoMedicionRendimiento",
]
