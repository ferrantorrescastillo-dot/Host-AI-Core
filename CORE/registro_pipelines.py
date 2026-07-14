from __future__ import annotations

from typing import Any, Dict, List

from MODELOS.api_interna import ResultadoPipeline, SolicitudPipeline


class RegistroPipelines:
    """Registro central de pipelines de Host AI.

    Responsabilidad única:
    - guardar pipelines disponibles,
    - listar información pública,
    - ejecutar una solicitud contra el pipeline indicado.

    Esta clase no conoce servicios, modelos de negocio ni lógica del restaurante.
    Solo actúa como índice técnico de pipelines.
    """

    def __init__(self) -> None:
        self._pipelines: Dict[str, Any] = {}

    def registrar(self, pipeline: Any) -> None:
        """Registra un pipeline usando su atributo público `nombre`."""
        nombre = getattr(pipeline, "nombre", None)
        if not nombre:
            raise ValueError("No se puede registrar un pipeline sin nombre.")
        self._pipelines[nombre] = pipeline

    def existe(self, nombre: str) -> bool:
        """Indica si existe un pipeline registrado con ese nombre."""
        return nombre in self._pipelines

    def obtener(self, nombre: str) -> Any | None:
        """Devuelve el pipeline registrado o None si no existe.

        Método añadido para evitar accesos directos futuros a `_pipelines`.
        No cambia el comportamiento actual del sistema.
        """
        return self._pipelines.get(nombre)

    def nombres(self) -> List[str]:
        """Devuelve los nombres de los pipelines registrados."""
        return list(self._pipelines.keys())

    def contar(self) -> int:
        """Devuelve el número total de pipelines registrados."""
        return len(self._pipelines)

    def listar(self) -> List[Dict[str, Any]]:
        """Devuelve la información pública de todos los pipelines."""
        return [pipeline.info() for pipeline in self._pipelines.values()]

    def ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        """Ejecuta una solicitud contra el pipeline indicado."""
        pipeline = self.obtener(solicitud.pipeline)
        if pipeline is None:
            return ResultadoPipeline(
                False,
                solicitud.pipeline,
                solicitud.accion,
                f"Pipeline no registrado: {solicitud.pipeline}",
                errores=[f"No existe pipeline '{solicitud.pipeline}'."],
            )
        return pipeline.ejecutar(solicitud)
