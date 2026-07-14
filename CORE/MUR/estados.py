from __future__ import annotations

from CORE.MUR.modelos import EstadoConflicto


class TransicionEstadoInvalida(ValueError):
    pass


TRANSICIONES: dict[EstadoConflicto, set[EstadoConflicto]] = {
    EstadoConflicto.DETECTADO: {EstadoConflicto.CLASIFICADO, EstadoConflicto.CANCELADO},
    EstadoConflicto.CLASIFICADO: {EstadoConflicto.EN_RESOLUCION, EstadoConflicto.PENDIENTE, EstadoConflicto.CANCELADO},
    EstadoConflicto.EN_RESOLUCION: {EstadoConflicto.RESUELTO, EstadoConflicto.PENDIENTE, EstadoConflicto.FALLIDO, EstadoConflicto.CANCELADO},
    EstadoConflicto.PENDIENTE: {EstadoConflicto.EN_RESOLUCION, EstadoConflicto.CANCELADO},
    EstadoConflicto.RESUELTO: {EstadoConflicto.APLICADO, EstadoConflicto.REABIERTO},
    EstadoConflicto.APLICADO: {EstadoConflicto.CERRADO, EstadoConflicto.REABIERTO},
    EstadoConflicto.CERRADO: {EstadoConflicto.REABIERTO},
    EstadoConflicto.FALLIDO: {EstadoConflicto.EN_RESOLUCION, EstadoConflicto.CANCELADO},
    EstadoConflicto.CANCELADO: {EstadoConflicto.REABIERTO},
    EstadoConflicto.REABIERTO: {EstadoConflicto.EN_RESOLUCION, EstadoConflicto.CANCELADO},
}


def validar_transicion(actual: EstadoConflicto, nuevo: EstadoConflicto) -> None:
    if nuevo == actual:
        return
    if nuevo not in TRANSICIONES.get(actual, set()):
        raise TransicionEstadoInvalida(f'Transición MUR no válida: {actual.value} -> {nuevo.value}')
