from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.planificacion_produccion_306 import AsignacionCocineroProduccion, InformeAsignacionProduccion

class AsignadorRecursosProduccion:
    """Host AI 3.0.6.4 - Asignador Inteligente de Recursos y Cocineros.

    Reparte tareas activas entre cocineros respetando jornada, detecta recursos saturados
    y mantiene una lectura operativa para cocina: quién hace qué, cuándo y con qué recurso.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.produccion_dir = self.base_dir / 'DATOS' / 'produccion'
        self.produccion_dir.mkdir(parents=True, exist_ok=True)

    def asignar_recursos(self, elaboraciones: List[Dict[str, Any]] | None = None, planificacion: Dict[str, Any] | None = None, cocineros: int = 3, jornada_horas: float = 7.5) -> Dict[str, Any]:
        if planificacion is None:
            planificacion = self.core.planificador_inteligente_produccion.planificar_produccion(elaboraciones, jornada_horas, cocineros)
        bloques = [b for b in planificacion.get('bloques', []) if b.get('tipo_tiempo') == 'activo']
        nombres = [f'Cocinero {i+1}' for i in range(max(1, int(cocineros)))]
        carga = {n: 0 for n in nombres}
        asignaciones: List[Dict[str, Any]] = []
        ocupacion_recurso: Dict[tuple, List[Dict[str, Any]]] = {}
        conflictos: List[Dict[str, Any]] = []
        capacidad = int(float(jornada_horas) * 60)
        for bloque in sorted(bloques, key=lambda b: (b.get('dia',1), b.get('inicio_min',0), b.get('prioridad','normal'))):
            cocinero = min(nombres, key=lambda n: carga[n])
            dia = int(bloque.get('dia', 1))
            inicio = max(int(bloque.get('inicio_min', 0)), carga[cocinero] % max(1, capacidad))
            fin = inicio + int(bloque.get('duracion_min', 0))
            if fin > capacidad and inicio > 0:
                dia += 1; inicio = 0; fin = int(bloque.get('duracion_min', 0))
            recurso = str(bloque.get('recurso') or 'mesa_trabajo')
            riesgo = self._calcular_riesgo_asignacion(bloque, fin, capacidad)
            asignacion = AsignacionCocineroProduccion(cocinero, dia, inicio, fin, int(bloque.get('duracion_min',0)), str(bloque.get('clave')), str(bloque.get('nombre')), 'produccion_activa', recurso, str(bloque.get('prioridad','normal')), riesgo, bloque.get('datos', {})).to_dict()
            for otra in ocupacion_recurso.get((dia, recurso), []):
                if self._solapa(inicio, fin, otra['inicio_min'], otra['fin_min']):
                    conflictos.append({'tipo':'recurso_saturado','gravedad':'aviso','dia':dia,'recurso':recurso,'elaboraciones':[otra['elaboracion'], asignacion['elaboracion']], 'lectura_host_ai': f'Recurso {recurso} solapado en día {dia}.'})
            ocupacion_recurso.setdefault((dia, recurso), []).append(asignacion)
            asignaciones.append(asignacion)
            carga[cocinero] += int(bloque.get('duracion_min', 0))
        dias = max([a['dia'] for a in asignaciones], default=0)
        estado = 'critico' if any(a['riesgo']=='alto' for a in asignaciones) or len(conflictos) >= 3 else ('ajustar' if conflictos else 'ok')
        resumen = {'jornada_horas': jornada_horas, 'capacidad_por_cocinero_min': capacidad, 'recursos_usados': sorted({a['recurso'] for a in asignaciones}), 'conflictos_detectados': len(conflictos), 'cocinero_mas_cargado_min': max(carga.values()) if carga else 0}
        lectura = f"Asignación inteligente de producción: {len(asignaciones)} tareas activas, {len(conflictos)} conflicto(s), estado {estado}."
        return InformeAsignacionProduccion('3.0.6.4', len(asignaciones), len(nombres), dias, carga, conflictos, estado, asignaciones, resumen, lectura).to_dict()

    def exportar_asignacion(self, asignacion: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.produccion_dir / (nombre or 'asignacion_recursos_produccion_3064.json')
        destino.write_text(json.dumps(asignacion, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Asignación de recursos de producción exportada: {destino.name}.'}

    def _solapa(self, a1:int, a2:int, b1:int, b2:int) -> bool:
        return max(a1, b1) < min(a2, b2)

    def _calcular_riesgo_asignacion(self, bloque: Dict[str, Any], fin: int, capacidad: int) -> str:
        puntos = 0
        if bloque.get('prioridad') == 'critica': puntos += 2
        if int(bloque.get('duracion_min', 0)) >= 120: puntos += 2
        elif int(bloque.get('duracion_min', 0)) >= 75: puntos += 1
        if fin > capacidad: puntos += 2
        if bloque.get('dependencias'): puntos += 1
        return 'alto' if puntos >= 4 else ('medio' if puntos >= 2 else 'normal')
