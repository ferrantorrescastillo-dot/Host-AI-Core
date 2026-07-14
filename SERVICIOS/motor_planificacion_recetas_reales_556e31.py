from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from SERVICIOS.fichas_produccion_reales_556e31 import RepositorioFichasProduccion556E31


def _minutos_hora(valor: str) -> int:
    h, m = str(valor).split(":", 1)
    return int(h) * 60 + int(m)


def _hora(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def _norm(value: Any) -> str:
    import re
    import unicodedata

    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip(" .")


class MotorPlanificacionRecetasReales556E31:
    """Planificador real de recetas validado por rendimiento, lotes y jornadas.

    Revisión 5.5.6E.3.4:
    - toma el rendimiento del escandallo canónico cuando existe;
    - interpreta la duración escalada como carga de trabajo (persona-minutos);
    - divide fases paralelizables entre cocineros;
    - ningún cocinero supera la jornada configurada;
    - corta el planning a fin de jornada y continúa por días reales;
    - los tiempos pasivos liberan al equipo;
    - divide internamente pelado, corte, porcionado, envasado y etiquetado;
    - usa todo el equipo disponible antes de abrir una segunda jornada.
    """

    VERSION = "5.5.6E.3.4.1"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.repo = RepositorioFichasProduccion556E31(self.base_dir)
        self.canonico_path = self.base_dir / "DATOS" / "db" / "escandallos_canonicos.json"

    @staticmethod
    def _factor(objetivo: float, rendimiento: float) -> float:
        return max(float(objetivo) / max(float(rendimiento), 0.0001), 0.0001)

    def _buscar_rendimiento_canonico(self, receta: str) -> Optional[Dict[str, Any]]:
        if not self.canonico_path.exists():
            return None
        try:
            data = json.loads(self.canonico_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        items = data if isinstance(data, list) else data.get("escandallos", []) if isinstance(data, dict) else []
        objetivo = _norm(receta)
        candidatos: List[Dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            r = item.get("receta") if isinstance(item.get("receta"), dict) else item
            nombre = str(r.get("nombre") or r.get("receta") or "").strip()
            if _norm(nombre) == objetivo:
                candidatos = [r]
                break
            if objetivo and (objetivo in _norm(nombre) or _norm(nombre) in objetivo):
                candidatos.append(r)
        if len(candidatos) != 1:
            return None
        r = candidatos[0]
        rendimiento = r.get("rendimiento") or r.get("raciones_base") or r.get("rendimiento_base")
        try:
            rendimiento = float(rendimiento)
        except (TypeError, ValueError):
            return None
        if rendimiento <= 0:
            return None
        return {
            "rendimiento": rendimiento,
            "unidad": str(r.get("unidad_rendimiento") or "u"),
            "fuente": str(self.canonico_path.relative_to(self.base_dir)),
        }

    @staticmethod
    def _carga_fase(fase: Dict[str, Any], factor: float) -> int:
        """Devuelve persona-minutos, no tiempo transcurrido.

        El escalado sublineal conserva las eficiencias de lote. Después la carga se
        reparte entre cocineros cuando la fase admite paralelización.
        """
        base = float(fase.get("duracion_base_min") or 0)
        if bool(fase.get("escalable_por_volumen", False)):
            base *= max(1.0, factor ** 0.42)
        return max(1, int(math.ceil(base / 5.0) * 5))

    @staticmethod
    def _es_paralelizable(fase: Dict[str, Any]) -> bool:
        """Decide si una fase puede repartirse entre varias personas.

        Prioriza el dato explícito de la ficha. Cuando una ficha antigua no lo
        contiene, aplica una heurística conservadora basada en el nombre y el
        recurso. Nunca paraleliza cocciones, reposos o controles que requieran
        una única secuencia técnica.
        """
        # Las fichas antiguas guardaban `puede_paralelizar=False` por defecto,
        # aunque el usuario nunca hubiera tomado esa decisión. Solo tratamos
        # como bloqueo explícito el nuevo campo `bloquear_paralelizacion`.
        if bool(fase.get("bloquear_paralelizacion", False)):
            return False
        if bool(fase.get("puede_paralelizar", False)):
            return True

        nombre = _norm(fase.get("nombre"))
        recursos = {_norm(x) for x in (fase.get("recursos") or [])}
        no_divisibles = (
            "cocer", "cocinar", "hornear", "freir", "abatir", "enfriar",
            "reposar", "fermentar", "reducir", "control final", "mezclar",
        )
        if any(token in nombre for token in no_divisibles):
            # Mezclar puede dividirse por lotes solo si la ficha lo declara.
            return False

        divisibles = (
            "pelar", "cortar", "limpiar", "porcionar", "envasar",
            "etiquetar", "pesar", "preparar", "montar", "emplatar",
        )
        if any(token in nombre for token in divisibles):
            return True
        if "mesa_trabajo" in recursos and bool(fase.get("escalable_por_volumen", False)):
            return True
        return bool(fase.get("escalable_por_volumen", False))

    @staticmethod
    def _equipo(cocineros: int | Iterable[str]) -> List[str]:
        if isinstance(cocineros, int):
            if cocineros <= 0:
                raise ValueError("Debe existir al menos un cocinero.")
            return [f"Cocinero {i}" for i in range(1, cocineros + 1)]
        equipo = [str(x).strip() for x in cocineros if str(x).strip()]
        if not equipo:
            raise ValueError("Debe existir al menos un cocinero.")
        return equipo

    @staticmethod
    def _nuevo_dia(cargas_dia: Dict[int, Dict[str, int]], dia: int, equipo: List[str]) -> None:
        cargas_dia.setdefault(dia, {c: 0 for c in equipo})

    def _programar_activa(
        self,
        *,
        fase: Dict[str, Any],
        orden: int,
        carga_total: int,
        paralelizable: bool,
        equipo: List[str],
        dia: int,
        cursor: int,
        inicio: int,
        fin: int,
        cargas_dia: Dict[int, Dict[str, int]],
        cargas_total: Dict[str, int],
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        pendientes = int(carga_total)
        segmentos: List[Dict[str, Any]] = []
        segmento_n = 1
        while pendientes > 0:
            if cursor >= fin:
                dia += 1
                cursor = inicio
            self._nuevo_dia(cargas_dia, dia, equipo)
            disponibles = sorted(
                equipo,
                key=lambda c: (cargas_dia[dia][c], cargas_total[c], c),
            )
            max_trabajadores = len(equipo) if paralelizable else 1
            trabajadores = disponibles[:max_trabajadores]
            ventana = fin - cursor
            if ventana <= 0:
                dia += 1
                cursor = inicio
                continue

            # Capacidad restante real de cada cocinero en esta jornada.
            capacidades = {c: max(0, (fin - inicio) - cargas_dia[dia][c]) for c in trabajadores}
            trabajadores = [c for c in trabajadores if capacidades[c] > 0]
            if not trabajadores:
                dia += 1
                cursor = inicio
                continue

            # Nadie puede trabajar más minutos que la ventana horaria disponible.
            capacidad_segmento = sum(min(ventana, capacidades[c]) for c in trabajadores)
            if capacidad_segmento <= 0:
                dia += 1
                cursor = inicio
                continue
            trabajo_segmento = min(pendientes, capacidad_segmento)

            # Reparto equilibrado de persona-minutos.
            asignado: Dict[str, int] = {c: 0 for c in trabajadores}
            restante = trabajo_segmento
            while restante > 0:
                progreso = False
                for c in trabajadores:
                    limite = min(ventana, capacidades[c])
                    if asignado[c] < limite and restante > 0:
                        asignado[c] += 1
                        restante -= 1
                        progreso = True
                if not progreso:
                    break
            usados = [c for c in trabajadores if asignado[c] > 0]
            duracion_elapsed = max(asignado.values()) if usados else 0
            fin_segmento = cursor + duracion_elapsed
            for c in usados:
                cargas_dia[dia][c] += asignado[c]
                cargas_total[c] += asignado[c]

            segmentos.append({
                "orden": orden,
                "segmento": segmento_n,
                "fase": fase.get("nombre") or "Fase",
                "descripcion": fase.get("descripcion") or "",
                "tipo_tiempo": str(fase.get("tipo_tiempo") or "activo"),
                "dia": dia,
                "inicio_min": cursor,
                "fin_min": fin_segmento,
                "inicio": _hora(cursor),
                "fin": _hora(fin_segmento),
                "duracion_min": duracion_elapsed,
                "carga_persona_min": sum(asignado.values()),
                "responsable": ", ".join(usados),
                "responsables": usados,
                "reparto_minutos": asignado,
                "libera_cocinero": False,
                "recursos": fase.get("recursos", []),
                "punto_control": fase.get("punto_control", ""),
                "paralelizada": len(usados) > 1,
            })
            pendientes -= sum(asignado.values())
            cursor = fin_segmento
            segmento_n += 1
            if pendientes > 0:
                dia += 1
                cursor = inicio
        return segmentos, dia, cursor

    def _programar_pasiva(
        self,
        *,
        fase: Dict[str, Any],
        orden: int,
        duracion: int,
        dia: int,
        cursor: int,
        inicio: int,
        fin: int,
        responsable: str,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        pendientes = int(duracion)
        segmentos: List[Dict[str, Any]] = []
        segmento_n = 1
        while pendientes > 0:
            if cursor >= fin:
                dia += 1
                cursor = inicio
            ventana = fin - cursor
            tramo = min(pendientes, ventana)
            fin_segmento = cursor + tramo
            segmentos.append({
                "orden": orden,
                "segmento": segmento_n,
                "fase": fase.get("nombre") or "Fase",
                "descripcion": fase.get("descripcion") or "",
                "tipo_tiempo": str(fase.get("tipo_tiempo") or "pasivo"),
                "dia": dia,
                "inicio_min": cursor,
                "fin_min": fin_segmento,
                "inicio": _hora(cursor),
                "fin": _hora(fin_segmento),
                "duracion_min": tramo,
                "carga_persona_min": 0,
                "responsable": responsable,
                "responsables": [],
                "reparto_minutos": {},
                "libera_cocinero": True,
                "recursos": fase.get("recursos", []),
                "punto_control": fase.get("punto_control", ""),
                "paralelizada": False,
            })
            pendientes -= tramo
            cursor = fin_segmento
            segmento_n += 1
            if pendientes > 0:
                dia += 1
                cursor = inicio
        return segmentos, dia, cursor

    def planificar(
        self,
        receta: str,
        objetivo: float,
        unidad: str = "personas",
        cocineros: int | Iterable[str] = 3,
        inicio_jornada: str = "08:00",
        fin_jornada: str = "15:30",
    ) -> Dict[str, Any]:
        ficha = self.repo.buscar(receta)
        if not ficha or ficha.get("estado") != "VALIDADA":
            return {
                "version": self.VERSION,
                "estado": "NECESITA_FICHA_PRODUCCION",
                "receta": receta,
                "objetivo": float(objetivo),
                "unidad": unidad,
                "puede_planificar": False,
                "motivo": "No existe una ficha de producción real validada.",
                "datos_reales_modificados": False,
            }

        equipo = self._equipo(cocineros)
        inicio = _minutos_hora(inicio_jornada)
        fin = _minutos_hora(fin_jornada)
        jornada = fin - inicio
        if jornada <= 0:
            raise ValueError("La jornada debe tener una duración positiva.")

        incidencias: List[Dict[str, Any]] = []
        rendimiento_ficha = float(ficha.get("rendimiento_base") or 1)
        unidad_rendimiento = str(ficha.get("unidad_rendimiento") or "u")
        rendimiento_canonico = self._buscar_rendimiento_canonico(receta)
        fuente_rendimiento = "FICHA_PRODUCCION_REAL"
        rendimiento = rendimiento_ficha
        if rendimiento_canonico:
            rendimiento = float(rendimiento_canonico["rendimiento"])
            unidad_rendimiento = str(rendimiento_canonico["unidad"])
            fuente_rendimiento = "ESCANDALLO_CANONICO"
            if abs(rendimiento_ficha - rendimiento) > 1e-9:
                incidencias.append({
                    "gravedad": "INFO",
                    "motivo": (
                        f"El rendimiento de la ficha ({rendimiento_ficha:g}) no coincidía con el escandallo "
                        f"({rendimiento:g}); se ha usado el escandallo canónico."
                    ),
                })

        factor = self._factor(objetivo, rendimiento)
        cargas_total = {c: 0 for c in equipo}
        cargas_dia: Dict[int, Dict[str, int]] = {}
        dia = 1
        cursor = inicio
        tareas: List[Dict[str, Any]] = []
        responsable_principal = equipo[0]

        for idx, fase in enumerate(ficha.get("fases", []), start=1):
            carga = self._carga_fase(fase, factor)
            tipo = str(fase.get("tipo_tiempo") or "activo").lower()
            requiere = bool(fase.get("requiere_presencia", tipo == "activo"))
            activa = tipo == "activo" or requiere or tipo == "mixto"
            if activa:
                paralelizable = self._es_paralelizable(fase)
                segmentos, dia, cursor = self._programar_activa(
                    fase=fase,
                    orden=int(fase.get("orden") or idx),
                    carga_total=carga,
                    paralelizable=paralelizable,
                    equipo=equipo,
                    dia=dia,
                    cursor=cursor,
                    inicio=inicio,
                    fin=fin,
                    cargas_dia=cargas_dia,
                    cargas_total=cargas_total,
                )
                tareas.extend(segmentos)
                if segmentos and segmentos[0].get("responsables"):
                    responsable_principal = segmentos[0]["responsables"][0]
            else:
                segmentos, dia, cursor = self._programar_pasiva(
                    fase=fase,
                    orden=int(fase.get("orden") or idx),
                    duracion=carga,
                    dia=dia,
                    cursor=cursor,
                    inicio=inicio,
                    fin=fin,
                    responsable=responsable_principal,
                )
                tareas.extend(segmentos)

        dias_estimados = max((t["dia"] for t in tareas), default=1)
        capacidad_dia = jornada * len(equipo)
        total_activo = sum(cargas_total.values())
        cargas_por_dia = []
        for d in range(1, dias_estimados + 1):
            self._nuevo_dia(cargas_dia, d, equipo)
            cargas_por_dia.append({
                "dia": d,
                "capacidad_equipo_min": capacidad_dia,
                "minutos_activos": sum(cargas_dia[d].values()),
                "cocineros": [
                    {
                        "nombre": c,
                        "minutos_activos": cargas_dia[d][c],
                        "minutos_libres": jornada - cargas_dia[d][c],
                        "horas_activas": round(cargas_dia[d][c] / 60, 2),
                    }
                    for c in equipo
                ],
            })

        if dias_estimados > 1:
            incidencias.append({
                "gravedad": "MEDIO",
                "motivo": f"La secuencia validada requiere {dias_estimados} jornadas reales; ninguna tarea supera las {fin_jornada}.",
            })

        return {
            "version": self.VERSION,
            "estado": "PLAN_REAL_OK" if dias_estimados == 1 else "PLAN_REAL_MULTIDIA",
            "puede_planificar": True,
            "receta": ficha["receta"],
            "objetivo": float(objetivo),
            "unidad": unidad,
            "rendimiento_base": rendimiento,
            "unidad_rendimiento": unidad_rendimiento,
            "rendimiento_ficha": rendimiento_ficha,
            "fuente_rendimiento": fuente_rendimiento,
            "factor": round(factor, 4),
            "fuente": "FICHA_PRODUCCION_REAL_VALIDADA",
            "inicio_jornada": inicio_jornada,
            "fin_jornada": fin_jornada,
            "minutos_jornada_por_cocinero": jornada,
            "capacidad_diaria_equipo_min": capacidad_dia,
            "dias_estimados": dias_estimados,
            "tareas": tareas,
            "cocineros": [
                {
                    "nombre": c,
                    "minutos_activos": cargas_total[c],
                    "horas_activas": round(cargas_total[c] / 60, 2),
                }
                for c in equipo
            ],
            "cargas_por_dia": cargas_por_dia,
            "minutos_activos": total_activo,
            "minutos_pasivos": sum(t["duracion_min"] for t in tareas if t["libera_cocinero"]),
            "fin_estimado": f"Día {dia} {_hora(cursor)}",
            "incidencias": incidencias,
            "solo_lectura": True,
            "datos_reales_modificados": False,
        }


def formatear_plan_real_556e31(resultado: Dict[str, Any]) -> str:
    if not resultado.get("puede_planificar"):
        from SERVICIOS.fichas_produccion_reales_556e31 import mensaje_falta_ficha_556e31

        return mensaje_falta_ficha_556e31(resultado.get("receta", "receta"))

    lines = [
        f"PLANIFICACIÓN REAL — {resultado['receta']}",
        f"- Objetivo: {resultado['objetivo']:g} {resultado['unidad']}",
        f"- Rendimiento usado: {resultado['rendimiento_base']:g} {resultado['unidad_rendimiento']} ({resultado['fuente_rendimiento']})",
        f"- Factor de producción: x{resultado['factor']:g}",
        f"- Estado: {resultado['estado']}",
        f"- Jornada por cocinero: {resultado['inicio_jornada']}–{resultado['fin_jornada']} ({resultado['minutos_jornada_por_cocinero']} min)",
        f"- Capacidad diaria del equipo: {resultado['capacidad_diaria_equipo_min']} min activos",
        f"- Días estimados: {resultado['dias_estimados']}",
    ]

    tareas_por_dia: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for tarea in resultado["tareas"]:
        tareas_por_dia[int(tarea.get("dia") or 1)].append(tarea)

    for dia in sorted(tareas_por_dia):
        lines += ["", f"DÍA {dia}", "SECUENCIA VALIDADA"]
        for t in tareas_por_dia[dia]:
            libera = " (libera al equipo)" if t["libera_cocinero"] else ""
            recursos = f" | Recursos: {', '.join(t['recursos'])}" if t.get("recursos") else ""
            reparto = ""
            if t.get("reparto_minutos"):
                reparto = " | Reparto: " + ", ".join(f"{c} {m} min" for c, m in t["reparto_minutos"].items() if m)
            lines.append(
                f"{t['orden']}.{t.get('segmento', 1)} {t['inicio']}–{t['fin']} {t['fase']} — "
                f"{t['responsable'] or 'sin presencia'} [{t['tipo_tiempo']}]{libera}{recursos}{reparto}"
            )

        carga_dia = next(x for x in resultado["cargas_por_dia"] if x["dia"] == dia)
        lines += ["", "CARGA DEL EQUIPO"]
        for c in carga_dia["cocineros"]:
            lines.append(
                f"- {c['nombre']}: {c['minutos_activos']} min activos ({c['horas_activas']:.2f} h) | "
                f"libres: {c['minutos_libres']} min"
            )

    if resultado["incidencias"]:
        lines += ["", "OBSERVACIONES"] + [f"- [{x['gravedad']}] {x['motivo']}" for x in resultado["incidencias"]]
    lines += [
        "",
        "SEGURIDAD",
        "- Planning basado únicamente en una ficha validada y el rendimiento canónico disponible.",
        "- Ningún cocinero supera su jornada y ninguna tarea continúa después del fin de turno.",
        "- No se han creado órdenes ni modificado datos reales.",
    ]
    return "\n".join(lines)


__all__ = ["MotorPlanificacionRecetasReales556E31", "formatear_plan_real_556e31"]
