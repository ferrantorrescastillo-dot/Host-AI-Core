from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from CORE.MUR.modelos import ConflictoMUR, ResultadoResolucion


class IResolutorMUR(ABC):
    resolutor_id: str = 'RESOLUTOR-BASE'
    version: str = '1.0'

    @abstractmethod
    def soporta(self, conflicto: ConflictoMUR) -> bool:
        raise NotImplementedError

    @abstractmethod
    def preparar(self, conflicto: ConflictoMUR) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def ejecutar(self, conflicto: ConflictoMUR, accion: str, payload: dict[str, Any]) -> ResultadoResolucion:
        raise NotImplementedError

    def validar(self, conflicto: ConflictoMUR, resultado: ResultadoResolucion) -> tuple[bool, str]:
        return resultado.ok, resultado.mensaje

    def compensar(self, conflicto: ConflictoMUR, resultado: ResultadoResolucion) -> ResultadoResolucion:
        return ResultadoResolucion(True, 'SIN_COMPENSACION', 'El resolutor no requiere compensación.', requiere_recalculo=False)


class RegistroResolutoresMUR:
    def __init__(self) -> None:
        self._resolutores: dict[str, IResolutorMUR] = {}

    def registrar(self, resolutor: IResolutorMUR) -> None:
        rid = str(resolutor.resolutor_id).strip()
        if not rid:
            raise ValueError('El resolutor debe tener resolutor_id.')
        if rid in self._resolutores:
            raise ValueError(f'Ya existe un resolutor registrado con id {rid}.')
        self._resolutores[rid] = resolutor

    def desregistrar(self, resolutor_id: str) -> None:
        self._resolutores.pop(resolutor_id, None)

    def obtener(self, resolutor_id: str) -> IResolutorMUR:
        try:
            return self._resolutores[resolutor_id]
        except KeyError as exc:
            raise LookupError(f'No existe el resolutor {resolutor_id}.') from exc

    def seleccionar(self, conflicto: ConflictoMUR) -> IResolutorMUR:
        compatibles = [r for r in self._resolutores.values() if r.soporta(conflicto)]
        if not compatibles:
            raise LookupError(f'No hay resolutor para {conflicto.tipo_entidad.value}/{conflicto.tipo_conflicto.value}.')
        if len(compatibles) > 1:
            compatibles.sort(key=lambda r: (getattr(r, 'prioridad', 100), r.resolutor_id))
        return compatibles[0]

    def listar(self) -> list[dict[str, str]]:
        return [{'resolutor_id': r.resolutor_id, 'version': str(r.version)} for r in self._resolutores.values()]
