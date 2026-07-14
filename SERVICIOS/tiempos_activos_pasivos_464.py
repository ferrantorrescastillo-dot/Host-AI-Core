from __future__ import annotations

"""
Host AI 4.6.4 - Gestión de tiempos activos y pasivos.

Este servicio normaliza elaboraciones de cocina distinguiendo:
- tiempo activo: trabajo real del cocinero.
- tiempo pasivo: horno, reposo, fermentación, abatimiento, cocción sin atención continua.
- tiempo total: suma operativa para ordenar la jornada.

No sustituye los motores 3.0.6 ya existentes; prepara una capa 4.x más operativa
para que el planificador diario pueda aprovechar huecos reales de cocina.
"""

from typing import Any, Dict, List


class GestorTiemposActivosPasivos464:
    TIPOS_PASIVOS = {"horno", "reposo", "fermentacion", "fermentación", "abatimiento", "coccion", "cocción", "enfriado", "marinado"}

    def normalizar_elaboraciones(self, elaboraciones: List[Dict[str, Any]] | None) -> Dict[str, Any]:
        items = [self._normalizar_item(e, i) for i, e in enumerate(elaboraciones or [])]
        total_activo = sum(i["tiempo_activo_min"] for i in items)
        total_pasivo = sum(i["tiempo_pasivo_min"] for i in items)
        aprovechables = [i for i in items if i["tiempo_pasivo_min"] > 0]
        return {
            "version": "4.6.4",
            "total_elaboraciones": len(items),
            "minutos_activos": total_activo,
            "minutos_pasivos": total_pasivo,
            "elaboraciones_con_pasivo": len(aprovechables),
            "elaboraciones": items,
            "lectura_host_ai": (
                f"Gestión de tiempos 4.6.4: {len(items)} elaboraciones, "
                f"{total_activo} min activos y {total_pasivo} min pasivos aprovechables."
            ),
        }

    def generar_bloques_tiempo(self, elaboracion: Dict[str, Any]) -> List[Dict[str, Any]]:
        item = self._normalizar_item(elaboracion, 0)
        bloques = []
        if item["tiempo_activo_min"]:
            bloques.append({
                "clave": item["clave"] + "_activo",
                "elaboracion": item["nombre"],
                "tipo_tiempo": "activo",
                "duracion_min": item["tiempo_activo_min"],
                "requiere_cocinero": True,
                "recurso": item["recurso_principal"],
            })
        if item["tiempo_pasivo_min"]:
            bloques.append({
                "clave": item["clave"] + "_pasivo",
                "elaboracion": item["nombre"],
                "tipo_tiempo": "pasivo",
                "duracion_min": item["tiempo_pasivo_min"],
                "requiere_cocinero": False,
                "recurso": item["recurso_principal"],
            })
        return bloques

    def _normalizar_item(self, raw: Dict[str, Any], idx: int) -> Dict[str, Any]:
        raw = dict(raw or {})
        nombre = str(raw.get("nombre") or raw.get("elaboracion") or raw.get("receta") or f"Elaboración {idx + 1}").strip()
        clave = str(raw.get("clave") or raw.get("id") or nombre.lower().replace(" ", "_")).strip()
        recursos = self._lista(raw.get("recursos") or raw.get("maquinaria") or raw.get("recurso") or [])
        pasos = raw.get("pasos") or raw.get("fases") or []

        activo = self._numero(raw.get("tiempo_activo_min", raw.get("activo_min", raw.get("minutos_activos", 0))))
        pasivo = self._numero(raw.get("tiempo_pasivo_min", raw.get("pasivo_min", raw.get("minutos_pasivos", 0))))

        if (activo == 0 and pasivo == 0) and isinstance(pasos, list):
            for paso in pasos:
                duracion = self._numero((paso or {}).get("duracion_min", (paso or {}).get("minutos", 0)))
                tipo = str((paso or {}).get("tipo") or (paso or {}).get("fase") or "activo").lower()
                if tipo in self.TIPOS_PASIVOS or (paso or {}).get("requiere_cocinero") is False:
                    pasivo += duracion
                else:
                    activo += duracion

        total = self._numero(raw.get("tiempo_total_min", raw.get("minutos", activo + pasivo))) or (activo + pasivo)
        return {
            **raw,
            "clave": clave,
            "nombre": nombre,
            "recursos": recursos,
            "recurso_principal": str(recursos[0]) if recursos else "mesa_trabajo",
            "tiempo_activo_min": activo,
            "tiempo_pasivo_min": pasivo,
            "tiempo_total_min": max(total, activo + pasivo),
            "pasivo_aprovechable": pasivo > 0,
        }

    def _lista(self, valor: Any) -> List[str]:
        if not valor:
            return []
        if isinstance(valor, str):
            return [v.strip() for v in valor.split(",") if v.strip()]
        return [str(v).strip() for v in valor if str(v).strip()]

    def _numero(self, valor: Any) -> int:
        try:
            return max(0, int(float(valor or 0)))
        except (TypeError, ValueError):
            return 0
