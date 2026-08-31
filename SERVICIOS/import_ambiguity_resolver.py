from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Protocol

from SERVICIOS.host_ai_engine.models import HostAIEngineResponse


ALLOWED_REGION_TYPES = {"RECETA", "ARTICULOS", "PROVEEDORES", "DESCONOCIDA"}
ALLOWED_MAPPING_TARGETS = {
    "receta", "ingrediente", "cantidad", "unidad", "rendimiento",
    "procedimiento", "proveedor", "formato", "precio_compra", "pvp",
}


class ImportAmbiguityResolver(Protocol):
    """Optional proposal-only resolver. Implementations must not persist data."""

    def resolve(self, region: dict[str, Any]) -> dict[str, Any]: ...


def layout_signature(region: dict[str, Any]) -> str:
    stable = {
        "headers": [str(item).strip().casefold() for item in region.get("headers", [])],
        "options": sorted(str(item) for item in region.get("opciones_permitidas", [])),
        "doubt": str(region.get("duda") or ""),
    }
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()


def sanitize_proposal(raw: Any, region: dict[str, Any]) -> dict[str, Any]:
    """Accept only classification/mapping fields grounded in the extracted region."""
    if not isinstance(raw, dict):
        return {"valid": False, "errors": ["respuesta_no_estructurada"]}
    errors: list[str] = []
    region_type = str(raw.get("tipo_region") or "").upper()
    if region_type not in ALLOWED_REGION_TYPES:
        errors.append("tipo_region_no_permitido")
    headers = {str(item) for item in region.get("headers", [])}
    mapping: dict[str, str] = {}
    for source, target in (raw.get("mapping") or {}).items():
        if str(source) not in headers or str(target) not in ALLOWED_MAPPING_TARGETS:
            errors.append("mapping_no_permitido")
            continue
        mapping[str(source)] = str(target)
    try:
        confidence = max(0.0, min(1.0, float(raw.get("confidence", 0))))
    except (TypeError, ValueError):
        confidence = 0.0
        errors.append("confidence_invalida")
    candidate_name = str(raw.get("nombre") or raw.get("nombre_candidato") or "").strip()
    contextual_name = str(region.get("titulo_contextual") or "").strip()
    if candidate_name and candidate_name.casefold() != contextual_name.casefold():
        errors.append("nombre_no_fundamentado")
        candidate_name = ""
    return {
        "valid": not errors,
        "tipo_region": region_type if region_type in ALLOWED_REGION_TYPES else None,
        "mapping": mapping,
        "nombre_candidato": candidate_name or None,
        "confidence": confidence,
        "origin": "IA",
        "status": "PROPUESTA_PENDIENTE_REVISION",
        "errors": sorted(set(errors)),
    }


def resolve_regions_once(
    regions: list[dict[str, Any]], resolver: ImportAmbiguityResolver
) -> tuple[list[dict[str, Any]], int]:
    cache: dict[str, dict[str, Any]] = {}
    proposals = []
    calls = 0
    for region in regions:
        signature = layout_signature(region)
        if signature not in cache:
            cache[signature] = sanitize_proposal(resolver.resolve(region), region)
            calls += 1
        proposals.append({**cache[signature], "region_id": region.get("region_id"),
                          "layout_signature": signature})
    return proposals, calls


class HostAIEngineImportAmbiguityResolver:
    """Adapter lazy over the canonical engine; never owns a provider or writes domain data."""

    def __init__(
        self, base_dir: Path, *, engine_factory: Callable[[Path], Any] | None = None
    ) -> None:
        self.base_dir = Path(base_dir)
        self._engine_factory = engine_factory
        self._engine: Any = None

    def resolve(self, region: dict[str, Any]) -> dict[str, Any]:
        engine = self._get_engine()
        request = engine.crear_consulta(
            origen="BIBLIOTECA_IMPORTACION", modulo="IMPORTACIONES",
            tipo_peticion="RESOLVER_AMBIGUEDAD_ESTRUCTURAL",
            proveedor_preferido=str(getattr(engine, "default_provider", "SIMULADO")),
            datos_enviados={
                "pregunta": (
                    "Devuelve exclusivamente JSON con tipo_region, nombre_candidato, mapping y confidence. "
                    "No propongas IDs, stock, compras, lotes, proveedores ni precios nuevos."
                ),
                "tool_context": {"solo_lectura": True, "region": region},
            },
        )
        response: HostAIEngineResponse = engine.ejecutar(request)
        if response.errores:
            return {"errors": list(response.errores)}
        raw = dict(response.respuesta or {})
        value: Any = raw.get("resultado") or raw.get("propuesta") or raw.get("mensaje") or raw
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("```"):
                text = text.strip("`").removeprefix("json").strip()
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                return {"errors": ["respuesta_no_estructurada"]}
        return value if isinstance(value, dict) else {"errors": ["respuesta_no_estructurada"]}

    def _get_engine(self) -> Any:
        if self._engine is None:
            if self._engine_factory is None:
                from SERVICIOS.host_ai_engine.service import HostAIEngine
                self._engine = HostAIEngine(self.base_dir)
            else:
                self._engine = self._engine_factory(self.base_dir)
        return self._engine
