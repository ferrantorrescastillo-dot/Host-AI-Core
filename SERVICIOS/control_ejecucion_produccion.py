from __future__ import annotations

"""
Módulo: control_ejecucion_produccion

Control inteligente de ejecución de producción. Compara planificación y avance
real para detectar bloqueos, retrasos y riesgos operativos. Añadidos comentarios
documentales durante la auditoría sin alterar comportamiento.
"""

from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.ejecucion_produccion_306 import EstadoTareaProduccion, InformeControlEjecucionProduccion

class ControlEjecucionProduccion:
    """Host AI 3.0.6.5 - Control Inteligente de Ejecución de Producción.

    Compara la planificación/asignación prevista con el avance real de cocina. Detecta
    tareas completadas, en curso, pendientes, bloqueadas, retrasos y riesgos operativos.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.produccion_dir = self.base_dir / 'DATOS' / 'produccion'
        self.produccion_dir.mkdir(parents=True, exist_ok=True)

    def controlar_ejecucion(self, planificacion: Dict[str, Any] | None = None, asignacion: Dict[str, Any] | None = None, avance: List[Dict[str, Any]] | None = None, minuto_actual: int = 0) -> Dict[str, Any]:
        if planificacion is None:
            planificacion = self._generar_plan_demo()
        bloques = list((planificacion or {}).get('bloques', []))
        asignaciones = list((asignacion or {}).get('asignaciones', []))
        avance_map = {str(a.get('clave') or a.get('tarea') or a.get('elaboracion','')).lower(): a for a in (avance or [])}
        asign_map = {str(a.get('clave','')).lower(): a for a in asignaciones}
        tareas: List[Dict[str, Any]] = []
        alertas: List[Dict[str, Any]] = []
        for b in bloques:
            if b.get('tipo_tiempo') == 'pasivo':
                continue
            clave = str(b.get('clave') or b.get('nombre','')).lower()
            av = avance_map.get(clave) or avance_map.get(str(b.get('nombre','')).lower()) or {}
            asg = asign_map.get(clave, {})
            avance_pct = float(av.get('avance_pct', av.get('porcentaje', 0)) or 0)
            estado = str(av.get('estado') or self._inferir_estado(b, avance_pct, minuto_actual)).lower()
            fin_previsto = int(b.get('fin_min', 0) or 0)
            retraso = max(0, int(minuto_actual - fin_previsto)) if avance_pct < 100 and minuto_actual > fin_previsto else int(av.get('retraso_min', 0) or 0)
            observaciones: List[str] = []
            if avance_pct >= 100: estado = 'completada'
            if estado in {'bloqueada','parada'}:
                observaciones.append('Tarea bloqueada o parada durante producción.')
            if retraso >= 60:
                riesgo = 'critico'; observaciones.append('Retraso superior a 60 minutos.')
            elif retraso >= 20:
                riesgo = 'aviso'; observaciones.append('Retraso operativo relevante.')
            elif estado in {'bloqueada','parada'}:
                riesgo = 'critico'
            elif estado == 'en_curso':
                riesgo = 'control'
            else:
                riesgo = 'ok'
            item = EstadoTareaProduccion(
                clave=str(b.get('clave','')), elaboracion=str(b.get('nombre','')), estado=estado,
                avance_pct=round(avance_pct,2), retraso_min=retraso, riesgo=riesgo,
                responsable=str(asg.get('cocinero') or av.get('responsable') or 'sin_asignar'),
                recurso=str(b.get('recurso') or asg.get('recurso') or 'mesa_trabajo'), observaciones=observaciones,
                datos={'bloque': b, 'avance': av, 'asignacion': asg}
            ).to_dict()
            tareas.append(item)
            if riesgo in {'aviso','critico'}:
                alertas.append({'gravedad': riesgo, 'clave': item['clave'], 'elaboracion': item['elaboracion'], 'mensaje': '; '.join(observaciones) or 'Riesgo de ejecución detectado.', 'retraso_min': retraso})
        completadas=sum(1 for t in tareas if t['estado']=='completada')
        en_curso=sum(1 for t in tareas if t['estado']=='en_curso')
        bloqueadas=sum(1 for t in tareas if t['estado'] in {'bloqueada','parada'})
        pendientes=max(0, len(tareas)-completadas-en_curso-bloqueadas)
        retraso_total=sum(int(t['retraso_min']) for t in tareas)
        riesgo_global='critico' if any(t['riesgo']=='critico' for t in tareas) else ('aviso' if any(t['riesgo']=='aviso' for t in tareas) else 'ok')
        resumen={'minuto_actual': minuto_actual, 'porcentaje_completado': round((completadas/len(tareas))*100,2) if tareas else 0, 'alertas_por_gravedad': self._contar(alertas,'gravedad')}
        lectura=f"Control inteligente de producción: {len(tareas)} tareas, {completadas} completadas, {len(alertas)} alertas y estado {riesgo_global}."
        return InformeControlEjecucionProduccion('3.0.6.5', len(tareas), completadas, en_curso, pendientes, bloqueadas, retraso_total, riesgo_global, tareas, alertas, resumen, lectura).to_dict()

    def exportar_control(self, control: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.produccion_dir / (nombre or 'control_ejecucion_produccion_3065.json')
        destino.write_text(json.dumps(control, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Control inteligente de ejecución exportado: {destino.name}.'}

    def _inferir_estado(self, b: Dict[str, Any], avance_pct: float, minuto_actual: int) -> str:
        if avance_pct >= 100: return 'completada'
        if avance_pct > 0: return 'en_curso'
        inicio=int(b.get('inicio_min',0) or 0); fin=int(b.get('fin_min',0) or 0)
        if minuto_actual > fin: return 'retrasada'
        if minuto_actual >= inicio: return 'en_curso'
        return 'pendiente'

    def _generar_plan_demo(self) -> Dict[str, Any]:
        elaboraciones = self.core.analizador_inteligente_produccion._cargar_elaboraciones_base() if hasattr(self.core, 'analizador_inteligente_produccion') else []
        if hasattr(self.core, 'planificador_inteligente_produccion'):
            return self.core.planificador_inteligente_produccion.planificar_produccion(elaboraciones)
        return {'bloques': []}

    def _contar(self, items: List[Dict[str, Any]], campo: str) -> Dict[str, int]:
        out: Dict[str,int] = {}
        for i in items:
            k=str(i.get(campo,'sin_dato')); out[k]=out.get(k,0)+1
        return out
