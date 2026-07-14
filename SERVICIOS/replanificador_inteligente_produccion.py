from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.ejecucion_produccion_306 import AccionReplanificacionProduccion, InformeReplanificacionProduccion

class ReplanificadorInteligenteProduccion:
    """Host AI 3.0.6.6 - Replanificador Inteligente de Producción.

    Toma el control de ejecución y propone cómo reorganizar el día: reforzar cocinero,
    adelantar tareas críticas, posponer tareas no urgentes, cambiar recursos y recuperar minutos.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.produccion_dir = self.base_dir / 'DATOS' / 'produccion'
        self.produccion_dir.mkdir(parents=True, exist_ok=True)

    def replanificar_produccion(self, control: Dict[str, Any] | None = None, planificacion: Dict[str, Any] | None = None, incidencias: List[Dict[str, Any]] | None = None, cocineros_disponibles: int = 3) -> Dict[str, Any]:
        if control is None:
            if planificacion is None and hasattr(self.core, 'planificador_inteligente_produccion'):
                planificacion = self.core.planificador_inteligente_produccion.planificar_produccion()
            control = self.core.control_ejecucion_produccion.controlar_ejecucion(planificacion, None, [], 0) if hasattr(self.core, 'control_ejecucion_produccion') else {'tareas': []}
        tareas = list((control or {}).get('tareas', []))
        incidencias = incidencias or []
        acciones: List[Dict[str, Any]] = []
        for t in tareas:
            riesgo = str(t.get('riesgo','ok'))
            estado = str(t.get('estado','pendiente'))
            retraso = int(t.get('retraso_min',0) or 0)
            if riesgo == 'critico' or estado in {'bloqueada','parada'}:
                acciones.append(self._accion(t, 'reforzar_o_reasignar', 'Tarea crítica, bloqueada o con retraso alto.', 'critica', max(30, retraso), cocineros_disponibles))
            elif riesgo == 'aviso' or retraso > 0:
                acciones.append(self._accion(t, 'adelantar_y_controlar', 'Tarea con desviación respecto al plan.', 'alta', max(15, retraso), cocineros_disponibles))
            elif estado == 'pendiente' and str(t.get('datos',{}).get('bloque',{}).get('prioridad','normal')) in {'critica','alta'}:
                acciones.append(self._accion(t, 'mantener_prioridad', 'Tarea pendiente prioritaria que no debe caer del plan.', 'alta', 0, cocineros_disponibles))
        for inc in incidencias:
            pseudo={'clave': str(inc.get('clave','incidencia')), 'elaboracion': str(inc.get('elaboracion') or inc.get('descripcion') or 'Incidencia de producción'), 'recurso': str(inc.get('recurso','sin_recurso')), 'responsable': str(inc.get('responsable','jefe_cocina'))}
            gravedad=str(inc.get('gravedad','aviso'))
            acciones.append(self._accion(pseudo, 'resolver_incidencia', str(inc.get('mensaje') or 'Incidencia manual añadida.'), 'critica' if gravedad=='critico' else 'alta', int(inc.get('impacto_min',30) or 30), cocineros_disponibles))
        acciones = self._deduplicar_acciones(acciones)
        nuevo_orden = self._generar_nuevo_orden(tareas, acciones)
        criticas=sum(1 for a in acciones if a['prioridad']=='critica')
        recuperables=sum(int(a.get('impacto_min',0)) for a in acciones if a.get('accion') in {'reforzar_o_reasignar','adelantar_y_controlar','resolver_incidencia'})
        estado='critico' if criticas else ('ajustar' if acciones else 'ok')
        resumen={'cocineros_disponibles': cocineros_disponibles, 'acciones_por_tipo': self._contar(acciones,'accion'), 'control_origen': {'riesgo_global': (control or {}).get('riesgo_global'), 'retraso_total_min': (control or {}).get('retraso_total_min')}}
        lectura=f"Replanificación inteligente de producción: {len(acciones)} acciones, {criticas} críticas y estado {estado}."
        return InformeReplanificacionProduccion('3.0.6.6', len(acciones), criticas, recuperables, estado, acciones, nuevo_orden, resumen, lectura).to_dict()

    def exportar_replanificacion(self, replanificacion: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.produccion_dir / (nombre or 'replanificacion_inteligente_produccion_3066.json')
        destino.write_text(json.dumps(replanificacion, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Replanificación inteligente de producción exportada: {destino.name}.'}

    def _accion(self, t: Dict[str, Any], accion: str, motivo: str, prioridad: str, impacto_min: int, cocineros: int) -> Dict[str, Any]:
        responsable = str(t.get('responsable') or 'cocinero_1')
        if accion == 'reforzar_o_reasignar' and cocineros > 1:
            responsable = 'cocinero_refuerzo'
        return AccionReplanificacionProduccion(
            clave=str(t.get('clave','')), elaboracion=str(t.get('elaboracion','')), accion=accion, motivo=motivo,
            prioridad=prioridad, impacto_min=int(impacto_min), responsable_sugerido=responsable,
            recurso=str(t.get('recurso','mesa_trabajo')), datos={'tarea_origen': t}
        ).to_dict()

    def _deduplicar_acciones(self, acciones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen=set(); out=[]
        for a in acciones:
            k=(a.get('clave'), a.get('accion'))
            if k not in seen:
                seen.add(k); out.append(a)
        peso={'critica':0,'alta':1,'normal':2,'baja':3}
        return sorted(out, key=lambda a: (peso.get(a.get('prioridad','normal'),2), -int(a.get('impacto_min',0)), a.get('elaboracion','')))

    def _generar_nuevo_orden(self, tareas: List[Dict[str, Any]], acciones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        claves_accion={a['clave']: a for a in acciones}
        def score(t):
            a=claves_accion.get(t.get('clave'))
            if a and a.get('prioridad')=='critica': return (0, -int(a.get('impacto_min',0)))
            if a: return (1, -int(a.get('impacto_min',0)))
            if t.get('estado')=='en_curso': return (2,0)
            return (3,0)
        return [{'clave': t.get('clave'), 'elaboracion': t.get('elaboracion'), 'estado': t.get('estado'), 'accion_sugerida': claves_accion.get(t.get('clave'),{}).get('accion','mantener_plan')} for t in sorted(tareas, key=score)]

    def _contar(self, items: List[Dict[str, Any]], campo: str) -> Dict[str, int]:
        out: Dict[str,int] = {}
        for i in items:
            k=str(i.get(campo,'sin_dato')); out[k]=out.get(k,0)+1
        return out
