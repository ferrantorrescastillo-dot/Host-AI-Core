from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from SERVICIOS.host_ai_engine.models import HostAIEngineRequest, HostAIProviderResult


class HostAIProviderBase(ABC):
    provider_name = "BASE"
    model_name = "N/A"

    @property
    def connected(self) -> bool:
        return True

    @abstractmethod
    def ejecutar(self, request: HostAIEngineRequest) -> HostAIProviderResult:
        raise NotImplementedError


class SimulatedProvider(HostAIProviderBase):
    provider_name = "SIMULADO"
    model_name = "host-ai-sim-v1"

    _SCENARIOS = {
        "consulta_simple_receta": {"mensaje": "SIMULACION: consulta simple de receta atendida.", "estado_sugerido": "COMPLETADA"},
        "importacion_compleja": {"mensaje": "SIMULACION: importación compleja dividida en varios pasos.", "estado_sugerido": "PLANIFICADA"},
        "requiere_confirmacion": {"mensaje": "SIMULACION: la acción requiere confirmación explícita.", "estado_sugerido": "ESPERANDO_CONFIRMACION"},
        "confirmacion_aceptada": {"mensaje": "SIMULACION: confirmación aceptada.", "estado_sugerido": "EN_EJECUCION"},
        "confirmacion_rechazada": {"mensaje": "SIMULACION: confirmación rechazada.", "estado_sugerido": "CANCELADA"},
        "confirmacion_parcial": {"mensaje": "SIMULACION: confirmación parcial recibida.", "estado_sugerido": "ESPERANDO_CONFIRMACION"},
        "falta_datos": {"mensaje": "SIMULACION: faltan datos obligatorios.", "estado_sugerido": "BLOQUEADA", "errores": ["Faltan datos obligatorios."]},
        "capacidad_no_disponible": {"mensaje": "SIMULACION: capacidad no disponible todavía.", "estado_sugerido": "BLOQUEADA", "errores": ["Capacidad todavía no implementada."]},
        "error_en_paso": {"mensaje": "SIMULACION: error controlado en un paso.", "estado_sugerido": "ERROR", "errores": ["Error simulado en paso funcional."]},
        "cancelacion_antes_persistir": {"mensaje": "SIMULACION: cancelación antes de persistir.", "estado_sugerido": "CANCELADA"},
    }

    def ejecutar(self, request: HostAIEngineRequest) -> HostAIProviderResult:
        tipo = str(request.tipo_peticion or "").strip().lower()
        modulo = str(request.modulo or "").strip().lower()
        datos = dict(request.datos_enviados or {})
        scenario = str(datos.get("sim_scenario") or "").strip().lower()

        if scenario in self._SCENARIOS:
            meta = dict(self._SCENARIOS[scenario])
            errores = list(meta.pop("errores", []))
            salida = {
                "simulado": True,
                "scenario": scenario,
                "modulo": modulo,
                "tipo_peticion": tipo,
                **meta,
            }
            return HostAIProviderResult(
                ok=not errores,
                proveedor=self.provider_name,
                modelo=self.model_name,
                salida=salida,
                errores=errores,
            )

        salida: dict[str, Any] = {
            "simulado": True,
            "mensaje": "Respuesta simulada del Host AI Engine.",
            "modulo": modulo,
            "tipo_peticion": tipo,
            "resumen_entrada": {
                "campos": sorted(list(datos.keys())),
                "tamano_aproximado": len(str(datos)),
            },
            "siguiente_paso": "Sustituir proveedor SIMULADO por proveedor real cuando se autorice.",
        }

        if "receta" in tipo:
            salida["preview"] = "SIMULACION: propuesta de receta pendiente de proveedor IA real."
        elif "escandallo" in tipo:
            salida["preview"] = "SIMULACION: calculo de escandallo pendiente de proveedor IA real."
        elif "incidencia" in tipo:
            salida["preview"] = "SIMULACION: resolucion de incidencias pendiente de proveedor IA real."
        elif "proveedor" in tipo:
            salida["preview"] = "SIMULACION: ranking de proveedores pendiente de proveedor IA real."
        elif "menu" in tipo:
            salida["preview"] = "SIMULACION: sugerencia de menu pendiente de proveedor IA real."
        elif "produccion" in tipo:
            salida["preview"] = "SIMULACION: plan de produccion pendiente de proveedor IA real."

        return HostAIProviderResult(
            ok=True,
            proveedor=self.provider_name,
            modelo=self.model_name,
            salida=salida,
            errores=[],
        )


class NotConnectedProvider(HostAIProviderBase):
    def __init__(self, provider_name: str, model_name: str = "N/A"):
        self.provider_name = provider_name
        self.model_name = model_name

    @property
    def connected(self) -> bool:
        return False

    def ejecutar(self, request: HostAIEngineRequest) -> HostAIProviderResult:
        return HostAIProviderResult(
            ok=False,
            proveedor=self.provider_name,
            modelo=self.model_name,
            salida={},
            errores=[f"Proveedor no conectado todavia: {self.provider_name}"],
        )
