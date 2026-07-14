from __future__ import annotations

import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from SERVICIOS.planificador_produccion_556d import PlanificadorProduccion556D


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip(" .")


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


class MotorTiemposProduccion556E1:
    """Descompone y estima tiempos de producción sin crear órdenes ni modificar datos.

    Prioridad de fuentes:
    1. Tiempos explícitos guardados en la receta canónica.
    2. Perfil específico de receta en DATOS/config/tiempos_produccion_556e1.json.
    3. Fases preliminares de 5.5.6D con ajuste por volumen.
    """

    VERSION = "5.5.6E.1"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.planificador = PlanificadorProduccion556D(self.base_dir)
        self.config_path = self.base_dir / "DATOS" / "config" / "tiempos_produccion_556e1.json"
        self.config = _load_json(self.config_path, {"perfiles": {}, "redondeo_min": 5})

    def _perfil(self, receta: str) -> Optional[Dict[str, Any]]:
        perfiles = self.config.get("perfiles", {}) if isinstance(self.config, dict) else {}
        objetivo = _norm(receta)
        for nombre, perfil in perfiles.items():
            if _norm(nombre) == objetivo and isinstance(perfil, dict):
                return perfil
        return None

    @staticmethod
    def _factor_volumen(objetivo: float, rendimiento_base: float) -> float:
        factor = max(float(objetivo) / max(float(rendimiento_base), 1.0), 1.0)
        # El tiempo no crece linealmente: se aplican economías de escala prudentes.
        return max(1.0, factor ** 0.42)

    @staticmethod
    def _redondear(minutos: float, multiplo: int) -> int:
        multiplo = max(int(multiplo or 5), 1)
        return int(math.ceil(max(minutos, 1.0) / multiplo) * multiplo)

    def estimar(self, termino: str, objetivo: float, unidad_objetivo: str = "personas") -> Dict[str, Any]:
        plan = self.planificador.generar(termino, objetivo, unidad_objetivo)
        receta = str(plan.get("receta") or termino)
        explosion = plan.get("cruce", {}).get("explosion", {}) if isinstance(plan.get("cruce"), dict) else {}
        rendimiento_base = float(explosion.get("rendimiento_base") or 1.0)
        factor_volumen = self._factor_volumen(objetivo, rendimiento_base)
        perfil = self._perfil(receta)
        redondeo = int(self.config.get("redondeo_min", 5)) if isinstance(self.config, dict) else 5

        fases: List[Dict[str, Any]] = []
        fuente = "ESTIMACION_5.5.6D"
        confianza = 65.0

        if perfil and isinstance(perfil.get("fases"), list):
            fuente = "PERFIL_REAL_CONFIGURADO"
            confianza = 95.0
            base_fases = perfil["fases"]
        else:
            base_fases = plan.get("tareas", [])

        for idx, fase in enumerate(base_fases, start=1):
            tipo = str(fase.get("tipo_tiempo") or fase.get("tipo") or "activo").lower()
            base_min = float(fase.get("duracion_min") or fase.get("minutos") or 0.0)
            escalable = bool(fase.get("escalable", tipo == "activo"))
            minutos = base_min * factor_volumen if escalable else base_min
            minutos = self._redondear(minutos, redondeo)
            fases.append({
                "orden": idx,
                "fase": str(fase.get("fase") or fase.get("nombre") or f"Fase {idx}"),
                "descripcion": str(fase.get("descripcion") or ""),
                "tipo_tiempo": tipo,
                "duracion_base_min": round(base_min, 2),
                "duracion_estimada_min": minutos,
                "escalable_por_volumen": escalable,
                "requiere_presencia": bool(fase.get("requiere_presencia", tipo == "activo")),
            })

        activos = sum(x["duracion_estimada_min"] for x in fases if x["tipo_tiempo"] == "activo")
        pasivos = sum(x["duracion_estimada_min"] for x in fases if x["tipo_tiempo"] != "activo")
        total_secuencial = activos + pasivos
        return {
            "version": self.VERSION,
            "receta": receta,
            "objetivo": float(objetivo),
            "unidad_objetivo": unidad_objetivo,
            "rendimiento_base": rendimiento_base,
            "factor_volumen": round(factor_volumen, 4),
            "fases": fases,
            "minutos_activos": activos,
            "minutos_pasivos": pasivos,
            "minutos_secuenciales": total_secuencial,
            "horas_activas": round(activos / 60, 2),
            "horas_secuenciales": round(total_secuencial / 60, 2),
            "fuente_tiempos": fuente,
            "confianza_pct": confianza,
            "estado_stock": plan.get("estado"),
            "faltantes": plan.get("faltantes", []),
            "solo_lectura": True,
            "datos_reales_modificados": False,
        }


def formatear_tiempos_556e1(resultado: Dict[str, Any]) -> str:
    lines = [
        f"TIEMPOS DE PRODUCCIÓN — {resultado['receta']}",
        f"- Objetivo: {resultado['objetivo']:g} {resultado['unidad_objetivo']}",
        f"- Fuente: {resultado['fuente_tiempos']}",
        f"- Confianza: {resultado['confianza_pct']:.1f}%",
        "",
        "DESGLOSE DE TIEMPOS",
    ]
    for fase in resultado["fases"]:
        lines.append(
            f"{fase['orden']}. {fase['fase']}: {fase['duracion_estimada_min']} min "
            f"({fase['tipo_tiempo']}{', escalable' if fase['escalable_por_volumen'] else ''})"
        )
    lines += [
        "",
        "RESUMEN",
        f"- Tiempo activo estimado: {resultado['minutos_activos']} min ({resultado['horas_activas']:.2f} h)",
        f"- Tiempo pasivo estimado: {resultado['minutos_pasivos']} min",
        f"- Tiempo secuencial total: {resultado['minutos_secuenciales']} min ({resultado['horas_secuenciales']:.2f} h)",
    ]
    if resultado.get("fuente_tiempos") != "PERFIL_REAL_CONFIGURADO":
        lines += ["", "AVISO", "- Los tiempos son estimaciones iniciales. Podrán sustituirse por tiempos reales aprendidos del restaurante."]
    lines += ["", "SEGURIDAD", "- Cálculo en modo solo lectura.", "- No se han creado órdenes ni modificado datos reales."]
    return "\n".join(lines)


__all__ = ["MotorTiemposProduccion556E1", "formatear_tiempos_556e1"]
