from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline

class BasePipeline(ABC):
    nombre: str = "base"
    descripcion: str = "Pipeline base"
    acciones_soportadas: List[str] = []
    def __init__(self, core):
        self.core = core
    def validar(self, solicitud: SolicitudPipeline) -> List[str]:
        errores = []
        if solicitud.accion not in self.acciones_soportadas:
            errores.append(f"Acción no soportada por pipeline '{self.nombre}': {solicitud.accion}")
        return errores
    def ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        errores = self.validar(solicitud)
        if errores:
            return ResultadoPipeline(False, self.nombre, solicitud.accion, "Solicitud inválida.", errores=errores)
        return self._ejecutar(solicitud)
    @abstractmethod
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        raise NotImplementedError
    def info(self) -> Dict[str, Any]:
        return {"nombre": self.nombre, "descripcion": self.descripcion, "acciones_soportadas": list(self.acciones_soportadas)}
