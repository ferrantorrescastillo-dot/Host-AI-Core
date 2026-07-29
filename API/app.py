from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from API.contracts.http_models import ApiRequest, ApiResponse
from API.facade.core_public_api02 import CorePublicApi02Facade
from API.router import ApiRouter


class HostAIPlatformAPI:
    """Composicion base de la capa API (API-01).

    En API-01 no hay framework HTTP ni logica de negocio.
    Solo se define la fachada, contratos y enrutado.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self.facade = CorePublicApi02Facade(base_dir=base_dir)
        self.router = ApiRouter(self.facade)

    def handle(self, request: ApiRequest) -> ApiResponse:
        if not str(request.request_id or "").strip():
            request.request_id = str(uuid4())
        return self.router.dispatch(request)
