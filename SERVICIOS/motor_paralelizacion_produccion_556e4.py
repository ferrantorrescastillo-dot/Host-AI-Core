from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from SERVICIOS.motor_reparto_cocineros_556e3 import MotorRepartoCocineros556E3, _hora, _minutos_hora


class MotorParalelizacionProduccion556E4:
    """Construye un cronograma multi-producción respetando personas, precedencias y recursos.

    - Las fases de una receta mantienen su orden.
    - Las fases pasivas liberan al cocinero.
    - Se conserva el cocinero principal de cada elaboración.
    - Los recursos se reservan solo durante la fase que los necesita.
    """

    VERSION = "5.5.6E.4"

    def __init__(self, base_dir: Path, motor_reparto: Optional[MotorRepartoCocineros556E3] = None):
        self.base_dir = Path(base_dir).resolve()
        self.motor_reparto = motor_reparto or MotorRepartoCocineros556E3(self.base_dir)

    @staticmethod
    def _capacidad_recursos(reparto: Dict[str, Any]) -> Dict[str, int]:
        config = getattr(getattr(reparto, "motor_recursos", None), "config", {})
        recursos = config.get("recursos", {}) if isinstance(config, dict) else {}
        return {str(k): max(int(v or 0), 1) for k, v in recursos.items()}

    @staticmethod
    def _primer_hueco(
        desde: int,
        duracion: int,
        reservas: List[Tuple[int, int]],
        capacidad: int,
    ) -> int:
        candidato = desde
        while True:
            puntos = sorted({candidato, candidato + duracion} | {x for r in reservas for x in r})
            conflicto = False
            for a, b in zip(puntos, puntos[1:]):
                if a >= candidato + duracion or b <= candidato:
                    continue
                activos = sum(1 for ini, fin in reservas if ini < b and fin > a)
                if activos >= capacidad:
                    candidato = max(fin for ini, fin in reservas if ini < b and fin > a)
                    conflicto = True
                    break
            if not conflicto:
                return candidato

    def planificar(
        self,
        producciones: List[Dict[str, Any]],
        cocineros: int | Iterable[str | Dict[str, Any]] | None = None,
        inicio_jornada: str = "08:00",
        fin_jornada: str = "15:30",
    ) -> Dict[str, Any]:
        reparto = self.motor_reparto.repartir(producciones, cocineros, inicio_jornada, fin_jornada)
        inicio = _minutos_hora(inicio_jornada)
        fin = _minutos_hora(fin_jornada)
        capacidad_recursos = self._capacidad_recursos(self.motor_reparto)
        reservas_recursos: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
        disponibilidad_cocinero: Dict[str, int] = {c["nombre"]: inicio for c in reparto["cocineros"]}
        cronograma: List[Dict[str, Any]] = []
        incidencias: List[Dict[str, Any]] = []

        # Se intercalan elaboraciones por carga activa para aprovechar tiempos pasivos.
        asignaciones = sorted(reparto["asignaciones"], key=lambda a: (-a["minutos_activos"], a["receta"]))
        estado_receta = {a["receta"]: inicio for a in asignaciones}

        pendientes = []
        for a in asignaciones:
            for tarea in a["tareas"]:
                pendientes.append({"asignacion": a, "tarea": tarea})

        # Procesamiento por rondas de fase conserva la precedencia y permite alternar recetas.
        max_fases = max((len(a["tareas"]) for a in asignaciones), default=0)
        for indice_fase in range(max_fases):
            for a in asignaciones:
                if indice_fase >= len(a["tareas"]):
                    continue
                t = a["tareas"][indice_fase]
                responsable = a["cocinero_principal"]
                duracion = int(t["duracion_min"])
                tipo = t["tipo_tiempo"]
                desde = estado_receta[a["receta"]]
                if tipo == "activo":
                    desde = max(desde, disponibilidad_cocinero[responsable])

                recursos = [str(r.get("recurso")) for r in t.get("recursos", []) if r.get("recurso")]
                comienzo = desde
                cambiado = True
                while cambiado:
                    cambiado = False
                    for recurso in recursos:
                        nuevo = self._primer_hueco(
                            comienzo,
                            duracion,
                            reservas_recursos[recurso],
                            capacidad_recursos.get(recurso, 1),
                        )
                        if nuevo > comienzo:
                            comienzo = nuevo
                            cambiado = True
                final = comienzo + duracion
                for recurso in recursos:
                    reservas_recursos[recurso].append((comienzo, final))
                if tipo == "activo":
                    disponibilidad_cocinero[responsable] = final
                estado_receta[a["receta"]] = final
                cronograma.append({
                    "receta": a["receta"],
                    "fase": t["fase"],
                    "tipo_tiempo": tipo,
                    "responsable": responsable,
                    "inicio_min": comienzo,
                    "fin_min": final,
                    "inicio": _hora(comienzo),
                    "fin": _hora(final),
                    "duracion_min": duracion,
                    "recursos": recursos,
                    "libera_cocinero": tipo != "activo",
                })

        cronograma.sort(key=lambda x: (x["inicio_min"], x["responsable"], x["receta"]))
        final_global = max((x["fin_min"] for x in cronograma), default=inicio)
        for receta, termina in estado_receta.items():
            if termina > fin:
                incidencias.append({
                    "gravedad": "ALTO",
                    "receta": receta,
                    "motivo": f"Termina a las {_hora(termina)}, fuera de la jornada.",
                    "exceso_min": termina - fin,
                })

        # Conflictos residuales: deben ser cero si la planificación ha respetado capacidades.
        conflictos_residuales = []
        for recurso, reservas in reservas_recursos.items():
            capacidad = capacidad_recursos.get(recurso, 1)
            puntos = sorted({x for r in reservas for x in r})
            for a, b in zip(puntos, puntos[1:]):
                demanda = sum(1 for ini, finr in reservas if ini < b and finr > a)
                if demanda > capacidad:
                    conflictos_residuales.append({"recurso": recurso, "inicio": a, "fin": b, "demanda": demanda, "capacidad": capacidad})

        return {
            "version": self.VERSION,
            "inicio_jornada": inicio_jornada,
            "fin_jornada": fin_jornada,
            "cronograma": cronograma,
            "reparto_base": reparto,
            "incidencias": incidencias,
            "conflictos_residuales": conflictos_residuales,
            "inicio_global": _hora(inicio),
            "fin_global": _hora(final_global),
            "duracion_total_min": final_global - inicio,
            "estado": "PLAN_PARALELO_OK" if not incidencias and not conflictos_residuales else "PLAN_PARALELO_A_REVISAR",
            "solo_lectura": True,
            "datos_reales_modificados": False,
        }


def formatear_paralelizacion_556e4(resultado: Dict[str, Any]) -> str:
    lines = [
        "CRONOGRAMA PARALELO DE PRODUCCIÓN",
        f"- Jornada: {resultado['inicio_jornada']}–{resultado['fin_jornada']}",
        f"- Plan resultante: {resultado['inicio_global']}–{resultado['fin_global']}",
        f"- Estado: {resultado['estado']}",
        "",
        "CRONOGRAMA",
    ]
    for t in resultado["cronograma"]:
        recursos = f" | recursos: {', '.join(t['recursos'])}" if t["recursos"] else ""
        libre = " | libera cocinero" if t["libera_cocinero"] else ""
        lines.append(f"- {t['inicio']}–{t['fin']} | {t['responsable']} | {t['receta']} → {t['fase']}{recursos}{libre}")
    if resultado["incidencias"]:
        lines += ["", "INCIDENCIAS"]
        for i in resultado["incidencias"]:
            lines.append(f"- [{i['gravedad']}] {i['receta']}: {i['motivo']}")
    lines += [
        "",
        "CONTROL",
        f"- Conflictos de recursos sin resolver: {len(resultado['conflictos_residuales'])}",
        "",
        "SEGURIDAD",
        "- Cronograma calculado en modo solo lectura.",
        "- No se han reservado recursos, cambiado turnos ni creado órdenes.",
    ]
    return "\n".join(lines)


__all__ = ["MotorParalelizacionProduccion556E4", "formatear_paralelizacion_556e4"]
