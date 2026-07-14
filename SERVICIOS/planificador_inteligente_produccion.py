from __future__ import annotations

"""
Servicio Host AI 3.0.6.3 - Planificador Inteligente de Producción.

Responsabilidad:
- Normalizar elaboraciones.
- Ordenarlas por prioridad y dependencias.
- Convertirlas en bloques activos/pasivos planificables.
- Devolver un informe estructurado para producción y conversación.
"""

import json
from typing import Any, Dict, List

from MODELOS.planificacion_produccion_306 import (
    BloquePlanProduccion,
    InformePlanificacionProduccion,
)


class PlanificadorInteligenteProduccion:
    """Convierte elaboraciones en un plan operativo de producción."""

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.produccion_dir = self.base_dir / "DATOS" / "produccion"
        self.produccion_dir.mkdir(parents=True, exist_ok=True)

    def planificar_produccion(
        self,
        elaboraciones: List[Dict[str, Any]] | None = None,
        jornada_horas: float = 7.5,
        cocineros: int = 3,
        hora_inicio: str = "08:00",
    ) -> Dict[str, Any]:
        datos = elaboraciones if elaboraciones is not None else self._cargar_elaboraciones_base()
        normalizadas = [self._normalizar(elaboracion, indice) for indice, elaboracion in enumerate(datos or [])]
        ordenadas = self._ordenar_por_dependencias_y_prioridad(normalizadas)
        capacidad_activa_dia = self._calcular_capacidad_activa_dia(jornada_horas, cocineros)

        bloques: List[Dict[str, Any]] = []
        cursor_activo = 0
        minutos_activos = 0
        minutos_pasivos = 0

        for item in ordenadas:
            bloques_item, cursor_activo, activo, pasivo = self._crear_bloques_item(
                item=item,
                cursor_activo=cursor_activo,
                capacidad_activa_dia=capacidad_activa_dia,
            )
            bloques.extend(bloques_item)
            minutos_activos += activo
            minutos_pasivos += pasivo

        dias = max([bloque["dia"] for bloque in bloques], default=0)
        ocupacion = self._calcular_ocupacion(minutos_activos, capacidad_activa_dia, dias)
        estado = self._resolver_estado_ocupacion(ocupacion)
        resumen = self._crear_resumen(
            ordenadas=ordenadas,
            jornada_horas=jornada_horas,
            cocineros=cocineros,
            hora_inicio=hora_inicio,
            capacidad_activa_dia=capacidad_activa_dia,
        )
        lectura = (
            f"Planificación inteligente de producción: {len(ordenadas)} elaboraciones, "
            f"{len(bloques)} bloques, {dias} día(s) y estado {estado}."
        )

        return InformePlanificacionProduccion(
            "3.0.6.3",
            len(ordenadas),
            len(bloques),
            dias,
            minutos_activos,
            minutos_pasivos,
            ocupacion,
            estado,
            bloques,
            resumen,
            lectura,
        ).to_dict()

    def exportar_planificacion(self, planificacion: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        destino = self.produccion_dir / (nombre or "planificacion_inteligente_produccion_3063.json")
        destino.write_text(json.dumps(planificacion, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Planificación inteligente de producción exportada: {destino.name}.",
        }

    def _crear_bloques_item(
        self,
        item: Dict[str, Any],
        cursor_activo: int,
        capacidad_activa_dia: int,
    ) -> tuple[List[Dict[str, Any]], int, int, int]:
        activo = int(item["tiempo_activo_min"])
        pasivo = int(item["tiempo_pasivo_min"])
        dia = cursor_activo // capacidad_activa_dia + 1
        inicio = cursor_activo % capacidad_activa_dia
        fin = inicio + activo

        if fin > capacidad_activa_dia and inicio > 0:
            cursor_activo = dia * capacidad_activa_dia
            dia = cursor_activo // capacidad_activa_dia + 1
            inicio = 0
            fin = activo

        recurso = self._recurso_principal(item.get("recursos", []))
        bloques = [
            BloquePlanProduccion(
                item["clave"],
                item["nombre"],
                dia,
                inicio,
                fin,
                activo,
                "activo",
                recurso,
                item["prioridad"],
                item.get("dependencias", []),
                item,
            ).to_dict()
        ]

        if pasivo > 0:
            bloques.append(
                BloquePlanProduccion(
                    item["clave"] + "_pasivo",
                    item["nombre"],
                    dia,
                    fin,
                    fin + pasivo,
                    pasivo,
                    "pasivo",
                    recurso,
                    item["prioridad"],
                    item.get("dependencias", []),
                    item,
                ).to_dict()
            )

        cursor_activo += activo
        return bloques, cursor_activo, activo, pasivo

    def _normalizar(self, raw: Dict[str, Any], idx: int) -> Dict[str, Any]:
        nombre = str(raw.get("nombre") or raw.get("elaboracion") or raw.get("receta") or f"Elaboración {idx + 1}").strip()
        recursos = self._normalizar_lista(raw.get("recursos") or raw.get("maquinaria") or [])
        dependencias = self._normalizar_lista(raw.get("dependencias") or [])
        prioridad = self._normalizar_prioridad(raw.get("prioridad") or "normal")
        activo = int(float(raw.get("tiempo_activo_min", raw.get("activo_min", raw.get("minutos_activos", 0))) or 0))
        pasivo = int(float(raw.get("tiempo_pasivo_min", raw.get("pasivo_min", raw.get("minutos_pasivos", 0))) or 0))
        total = int(float(raw.get("tiempo_total_min", raw.get("minutos", activo + pasivo)) or (activo + pasivo)))

        return {
            **dict(raw),
            "clave": str(raw.get("clave") or raw.get("id") or nombre.lower().replace(" ", "_")),
            "nombre": nombre,
            "recursos": list(recursos),
            "dependencias": list(dependencias),
            "prioridad": prioridad,
            "tiempo_activo_min": activo,
            "tiempo_pasivo_min": pasivo,
            "tiempo_total_min": max(total, activo + pasivo),
        }

    def _ordenar_por_dependencias_y_prioridad(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        peso = {"critica": 0, "alta": 1, "normal": 2, "baja": 3}

        def score(item: Dict[str, Any]):
            return (
                peso.get(item.get("prioridad", "normal"), 2),
                -len(item.get("dependencias", [])),
                -int(item.get("tiempo_activo_min", 0)),
                item.get("nombre", ""),
            )

        orden = sorted(items, key=score)
        salida: List[Dict[str, Any]] = []
        pendientes = list(orden)
        guard = 0

        while pendientes and guard < 1000:
            guard += 1
            item = pendientes.pop(0)
            deps = {str(dependencia).lower() for dependencia in item.get("dependencias", [])}
            nombres_salida = {s["nombre"].lower() for s in salida} | {s["clave"].lower() for s in salida}
            hay_dependencia_pendiente = any(
                pendiente["nombre"].lower() in deps or pendiente["clave"].lower() in deps
                for pendiente in pendientes
            )
            if deps and not deps.issubset(nombres_salida) and hay_dependencia_pendiente:
                pendientes.append(item)
            else:
                salida.append(item)

        return salida + pendientes

    def _normalizar_lista(self, valor: Any) -> List[str]:
        if isinstance(valor, str):
            return [item.strip() for item in valor.split(",") if item.strip()]
        return list(valor)

    def _normalizar_prioridad(self, valor: Any) -> str:
        prioridad = str(valor or "normal").lower()
        return prioridad if prioridad in {"critica", "alta", "normal", "baja"} else "normal"

    def _calcular_capacidad_activa_dia(self, jornada_horas: float, cocineros: int) -> int:
        return max(1, int(float(jornada_horas) * 60 * max(1, int(cocineros))))

    def _calcular_ocupacion(self, minutos_activos: int, capacidad_activa_dia: int, dias: int) -> float:
        if not dias:
            return 0
        return round((minutos_activos / (capacidad_activa_dia * max(1, dias))) * 100, 2)

    def _resolver_estado_ocupacion(self, ocupacion: float) -> str:
        if ocupacion > 110:
            return "critico"
        if ocupacion > 90:
            return "ajustar"
        return "ok"

    def _crear_resumen(
        self,
        ordenadas: List[Dict[str, Any]],
        jornada_horas: float,
        cocineros: int,
        hora_inicio: str,
        capacidad_activa_dia: int,
    ) -> Dict[str, Any]:
        return {
            "jornada_horas": jornada_horas,
            "cocineros": cocineros,
            "hora_inicio": hora_inicio,
            "capacidad_activa_dia_min": capacidad_activa_dia,
            "prioridades": self._contar(ordenadas, "prioridad"),
            "recursos": sorted({recurso for item in ordenadas for recurso in item.get("recursos", [])}),
            "dependencias_detectadas": sum(1 for item in ordenadas if item.get("dependencias")),
        }

    def _recurso_principal(self, recursos: List[str]) -> str:
        return str(recursos[0]) if recursos else "mesa_trabajo"

    def _contar(self, items: List[Dict[str, Any]], campo: str) -> Dict[str, int]:
        salida: Dict[str, int] = {}
        for item in items:
            clave = str(item.get(campo, "sin_dato"))
            salida[clave] = salida.get(clave, 0) + 1
        return salida

    def _cargar_elaboraciones_base(self) -> List[Dict[str, Any]]:
        if hasattr(self.core, "analizador_inteligente_produccion"):
            return self.core.analizador_inteligente_produccion._cargar_elaboraciones_base()
        return []
