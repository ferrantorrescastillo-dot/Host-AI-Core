from __future__ import annotations

from typing import Any, Dict

from MODELOS.api_interna import SolicitudPipeline


class DirectorHostAI:
    """Fachada mínima para ejecutar pipelines desde Host AI.

    El Director no contiene lógica de negocio. Su función es transformar una
    petición sencilla (`pipeline`, `accion`, `parametros`) en una
    `SolicitudPipeline` y delegar la ejecución en el Registro de Pipelines.
    """

    def __init__(self, core: Any) -> None:
        self.core = core

    def ejecutar_pipeline(
        self,
        pipeline: str,
        accion: str,
        parametros: Dict[str, Any] | None = None,
    ):
        """Ejecuta un pipeline registrado mediante una solicitud estándar."""
        solicitud = SolicitudPipeline(pipeline, accion, parametros or {})
        return self.core.registro_pipelines.ejecutar(solicitud)
