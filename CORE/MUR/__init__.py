"""M1.1 — Núcleo del Motor Universal de Resolución (MUR)."""

from CORE.MUR.modelos import (
    AccionResolucion,
    CheckpointMUR,
    ConflictoMUR,
    EstadoConflicto,
    EventoAuditoriaMUR,
    ResultadoResolucion,
    SesionResolucionMUR,
    SeveridadConflicto,
    TipoConflicto,
    TipoEntidad,
)
from CORE.MUR.orquestador import OrquestadorMUR
from CORE.MUR.registro import IResolutorMUR, RegistroResolutoresMUR
from CORE.MUR.repositorios import RepositorioMURMemoria, RepositorioMURJson

__all__ = [
    'AccionResolucion', 'CheckpointMUR', 'ConflictoMUR', 'EstadoConflicto',
    'EventoAuditoriaMUR', 'ResultadoResolucion', 'SesionResolucionMUR',
    'SeveridadConflicto', 'TipoConflicto', 'TipoEntidad', 'OrquestadorMUR',
    'IResolutorMUR', 'RegistroResolutoresMUR', 'RepositorioMURMemoria',
    'RepositorioMURJson',
]
