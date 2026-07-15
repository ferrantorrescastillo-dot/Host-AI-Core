from __future__ import annotations

"""Host AI 4.6.1 - Planificador diario de producción.

Integra prioridades 4.6.2, asignación de cocineros 4.6.3 y tiempos activos/pasivos 4.6.4.
"""

from pathlib import Path
from typing import Any, Dict, List
import json

from SERVICIOS.tiempos_activos_pasivos_464 import GestorTiemposActivosPasivos464
from SERVICIOS.prioridades_inteligentes_cocina_462 import MotorPrioridadesInteligentesCocina462
from SERVICIOS.asignacion_cocineros_463 import AsignadorCocineros463


class PlanificadorDiarioProduccion461:
    def __init__(self, base_dir: str | Path | None = None, create_output_dir: bool = True):
        self.base_dir = Path(base_dir or Path.cwd())
        self.datos_dir = self.base_dir / "DATOS" / "produccion"
        self.create_output_dir = bool(create_output_dir)
        if self.create_output_dir:
            self.datos_dir.mkdir(parents=True, exist_ok=True)
        self.tiempos = GestorTiemposActivosPasivos464()
        self.prioridades = MotorPrioridadesInteligentesCocina462()
        self.asignador = AsignadorCocineros463()

    def planificar_dia(self, elaboraciones: List[Dict[str, Any]] | None, fecha: str = "", hora_servicio: str = "13:30", cocineros: int = 3, jornada_horas: float = 7.5, hora_inicio: str = "08:00") -> Dict[str, Any]:
        normalizadas = self.tiempos.normalizar_elaboraciones(elaboraciones).get("elaboraciones", [])
        prioridades = self.prioridades.ordenar_prioridades(normalizadas, hora_servicio).get("prioridades", [])
        asignacion = self.asignador.asignar(prioridades, cocineros=cocineros, jornada_horas=jornada_horas)
        bloques = self._crear_bloques(asignacion.get("asignaciones", []), prioridades)
        capacidad = int(float(jornada_horas) * 60 * max(1, int(cocineros)))
        minutos_activos = sum(i.get("tiempo_activo_min", 0) for i in prioridades)
        minutos_pasivos = sum(i.get("tiempo_pasivo_min", 0) for i in prioridades)
        dias = max([b.get("dia", 1) for b in bloques], default=1)
        estado = "ok" if minutos_activos <= capacidad * dias else "ajustar"
        plan = {
            "version": "4.6.1",
            "fecha": fecha,
            "hora_inicio": hora_inicio,
            "hora_servicio": hora_servicio,
            "cocineros": cocineros,
            "jornada_horas": jornada_horas,
            "total_elaboraciones": len(prioridades),
            "minutos_activos": minutos_activos,
            "minutos_pasivos": minutos_pasivos,
            "dias_necesarios": dias,
            "estado_plan": estado,
            "bloques": bloques,
            "asignacion": asignacion,
            "lectura_host_ai": f"Plan diario 4.6.1 preparado: {len(prioridades)} elaboraciones, {dias} día(s), estado {estado}.",
        }
        return plan

    def exportar_plan(self, plan: Dict[str, Any], nombre: str = "plan_diario_produccion_461.json") -> Dict[str, Any]:
        self.datos_dir.mkdir(parents=True, exist_ok=True)
        destino = self.datos_dir / nombre
        destino.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Plan diario de producción exportado: {destino.name}."}

    def _crear_bloques(self, asignaciones: List[Dict[str, Any]], prioridades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        por_clave = {p["clave"]: p for p in prioridades}
        bloques: List[Dict[str, Any]] = []
        for a in asignaciones:
            item = por_clave.get(a["clave"], {})
            bloques.append({**a, "tipo_tiempo": "activo", "requiere_cocinero": True, "recurso": item.get("recurso_principal", "mesa_trabajo")})
            if item.get("tiempo_pasivo_min", 0) > 0:
                bloques.append({
                    "cocinero": a["cocinero"],
                    "dia": a["dia"],
                    "inicio_min": a["fin_min"],
                    "fin_min": a["fin_min"] + item["tiempo_pasivo_min"],
                    "duracion_min": item["tiempo_pasivo_min"],
                    "elaboracion": a["elaboracion"],
                    "clave": a["clave"] + "_pasivo",
                    "tipo_tiempo": "pasivo",
                    "requiere_cocinero": False,
                    "recurso": item.get("recurso_principal", "mesa_trabajo"),
                })
        return sorted(bloques, key=lambda b: (b.get("dia", 1), b.get("inicio_min", 0), 0 if b.get("tipo_tiempo") == "activo" else 1))
