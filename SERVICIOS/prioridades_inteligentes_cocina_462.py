from __future__ import annotations

"""Host AI 4.6.2 - Motor de prioridades inteligentes de cocina."""

from typing import Any, Dict, List


class MotorPrioridadesInteligentesCocina462:
    PESO_PRIORIDAD = {"critica": 0, "crítica": 0, "alta": 1, "normal": 2, "baja": 3}

    def ordenar_prioridades(self, elaboraciones: List[Dict[str, Any]] | None, hora_servicio: str = "13:30") -> Dict[str, Any]:
        normalizadas = [self._normalizar(e, i, hora_servicio) for i, e in enumerate(elaboraciones or [])]
        ordenadas = self._ordenar_respetando_dependencias(normalizadas)
        for posicion, item in enumerate(ordenadas, start=1):
            item["orden_prioridad"] = posicion
            item["motivo_prioridad"] = self._motivo(item)
        return {
            "version": "4.6.2",
            "hora_servicio": hora_servicio,
            "total_elaboraciones": len(ordenadas),
            "prioridades": ordenadas,
            "lectura_host_ai": f"Prioridades 4.6.2 calculadas para {len(ordenadas)} elaboraciones antes del servicio de las {hora_servicio}.",
        }

    def _normalizar(self, raw: Dict[str, Any], idx: int, hora_servicio: str) -> Dict[str, Any]:
        raw = dict(raw or {})
        nombre = str(raw.get("nombre") or raw.get("elaboracion") or f"Elaboración {idx + 1}").strip()
        clave = str(raw.get("clave") or raw.get("id") or nombre.lower().replace(" ", "_")).strip()
        prioridad = str(raw.get("prioridad") or "normal").lower()
        activo = self._num(raw.get("tiempo_activo_min", raw.get("activo_min", 0)))
        pasivo = self._num(raw.get("tiempo_pasivo_min", raw.get("pasivo_min", 0)))
        total = self._num(raw.get("tiempo_total_min", raw.get("minutos", activo + pasivo))) or activo + pasivo
        dependencias = self._lista(raw.get("dependencias") or [])
        hora_limite = str(raw.get("hora_servicio") or raw.get("hora_limite") or hora_servicio)
        score = (
            self.PESO_PRIORIDAD.get(prioridad, 2) * 10000
            - pasivo * 12
            - total * 5
            - len(dependencias) * 700
            + idx
        )
        return {**raw, "clave": clave, "nombre": nombre, "prioridad": prioridad, "dependencias": dependencias, "tiempo_activo_min": activo, "tiempo_pasivo_min": pasivo, "tiempo_total_min": total, "hora_limite": hora_limite, "score_prioridad": score}

    def _ordenar_respetando_dependencias(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pendientes = sorted(items, key=lambda x: x["score_prioridad"])
        salida: List[Dict[str, Any]] = []
        guard = 0
        while pendientes and guard < 1000:
            guard += 1
            item = pendientes.pop(0)
            deps = {str(d).lower() for d in item.get("dependencias", [])}
            hechos = {s["nombre"].lower() for s in salida} | {s["clave"].lower() for s in salida}
            pendientes_ids = {p["nombre"].lower() for p in pendientes} | {p["clave"].lower() for p in pendientes}
            if deps and not deps.issubset(hechos) and deps.intersection(pendientes_ids):
                pendientes.append(item)
            else:
                salida.append(item)
        return salida + pendientes

    def _motivo(self, item: Dict[str, Any]) -> str:
        motivos = []
        if item.get("dependencias"):
            motivos.append("tiene dependencias")
        if item.get("tiempo_pasivo_min", 0) >= 60:
            motivos.append("necesita tiempo pasivo largo")
        if item.get("prioridad") in {"critica", "crítica", "alta"}:
            motivos.append(f"prioridad {item.get('prioridad')}")
        return ", ".join(motivos) or "orden operativo normal"

    def _lista(self, valor: Any) -> List[str]:
        if isinstance(valor, str):
            return [x.strip() for x in valor.split(",") if x.strip()]
        return [str(x).strip() for x in valor if str(x).strip()]

    def _num(self, valor: Any) -> int:
        try:
            return max(0, int(float(valor or 0)))
        except (TypeError, ValueError):
            return 0
