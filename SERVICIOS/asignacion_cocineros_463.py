from __future__ import annotations

"""Host AI 4.6.3 - Asignación inteligente de cocineros."""

from typing import Any, Dict, List


class AsignadorCocineros463:
    def asignar(self, elaboraciones: List[Dict[str, Any]] | None, cocineros: int = 3, jornada_horas: float = 7.5) -> Dict[str, Any]:
        nombres = [f"Cocinero {i}" for i in range(1, max(1, int(cocineros)) + 1)]
        capacidad = int(float(jornada_horas) * 60)
        carga = {n: 0 for n in nombres}
        asignaciones: List[Dict[str, Any]] = []

        for item in elaboraciones or []:
            normal = self._normalizar(item)
            candidato = self._elegir_cocinero(normal, nombres, carga)
            inicio = carga[candidato]
            dia = inicio // max(1, capacidad) + 1
            inicio_dia = inicio % max(1, capacidad)
            fin_dia = inicio_dia + normal["tiempo_activo_min"]
            if fin_dia > capacidad and inicio_dia > 0:
                inicio = dia * capacidad
                dia += 1
                inicio_dia = 0
                fin_dia = normal["tiempo_activo_min"]
            asignacion = {
                "cocinero": candidato,
                "dia": dia,
                "inicio_min": inicio_dia,
                "fin_min": fin_dia,
                "duracion_min": normal["tiempo_activo_min"],
                "elaboracion": normal["nombre"],
                "clave": normal["clave"],
                "prioridad": normal["prioridad"],
                "especialidad": normal.get("especialidad") or "general",
                "regla_continuidad": "quien_empieza_intenta_terminar",
            }
            asignaciones.append(asignacion)
            carga[candidato] = inicio + normal["tiempo_activo_min"]

        return {
            "version": "4.6.3",
            "cocineros": len(nombres),
            "total_asignaciones": len(asignaciones),
            "carga_por_cocinero_min": carga,
            "asignaciones": asignaciones,
            "estado_asignacion": self._estado(carga),
            "lectura_host_ai": f"Asignación 4.6.3: {len(asignaciones)} tareas repartidas entre {len(nombres)} cocineros.",
        }

    def _elegir_cocinero(self, item: Dict[str, Any], nombres: List[str], carga: Dict[str, int]) -> str:
        preferido = item.get("cocinero_preferente") or item.get("responsable")
        if preferido in nombres:
            return str(preferido)
        return min(nombres, key=lambda n: carga[n])

    def _normalizar(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        nombre = str(raw.get("nombre") or raw.get("elaboracion") or "Elaboración").strip()
        activo = self._num(raw.get("tiempo_activo_min", raw.get("activo_min", raw.get("duracion_min", 0))))
        return {**dict(raw), "nombre": nombre, "clave": str(raw.get("clave") or nombre.lower().replace(" ", "_")), "tiempo_activo_min": activo, "prioridad": str(raw.get("prioridad") or "normal").lower()}

    def _estado(self, carga: Dict[str, int]) -> str:
        if not carga:
            return "sin_datos"
        valores = list(carga.values())
        return "ajustar" if max(valores) - min(valores) > 120 else "ok"

    def _num(self, valor: Any) -> int:
        try:
            return max(0, int(float(valor or 0)))
        except (TypeError, ValueError):
            return 0
