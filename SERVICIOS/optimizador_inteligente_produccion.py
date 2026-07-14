"""Servicio de optimización inteligente de producción para Host AI RC1.

Este módulo pertenece al bloque 3.0.6 Producción.
La revisión RC2 no modifica reglas de planificación ni decisiones; solo
normaliza documentación y contrato público.
"""
from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.optimizacion_produccion_306 import OportunidadOptimizacionProduccion, InformeOptimizacionProduccion

__all__ = ["OptimizadorInteligenteProduccion"]


class OptimizadorInteligenteProduccion:
    """Host AI 3.0.6.7 - Optimizador Inteligente de Producción.

    Optimiza la planificación operativa: secuencia tareas, detecta huecos, agrupa
    recursos compatibles, reduce tiempos muertos y equilibra la carga por cocinero.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.produccion_dir = self.base_dir / 'DATOS' / 'produccion'
        self.produccion_dir.mkdir(parents=True, exist_ok=True)

    def optimizar_produccion(self, planificacion: Dict[str, Any] | None = None, asignacion: Dict[str, Any] | None = None, control: Dict[str, Any] | None = None, replanificacion: Dict[str, Any] | None = None, elaboraciones: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        if planificacion is None:
            planificacion = self._generar_planificacion(elaboraciones)
        if asignacion is None and hasattr(self.core, 'asignador_recursos_produccion'):
            asignacion = self.core.asignador_recursos_produccion.asignar_recursos(elaboraciones, planificacion)
        bloques = list((planificacion or {}).get('bloques', []))
        asignaciones = list((asignacion or {}).get('asignaciones', []))
        oportunidades: List[Dict[str, Any]] = []
        oportunidades.extend(self._optimizar_pasivos(bloques))
        oportunidades.extend(self._optimizar_recursos(bloques))
        oportunidades.extend(self._optimizar_carga_cocineros(asignaciones))
        oportunidades.extend(self._optimizar_retrasos(control or {}, replanificacion or {}))
        oportunidades = self._deduplicar_y_ordenar(oportunidades)
        plan_optimizado = self._crear_plan_optimizado(bloques, oportunidades)
        recursos_optimizados = self._resumen_recursos(plan_optimizado, asignaciones)
        criticas = sum(1 for o in oportunidades if o['prioridad'] == 'critica')
        ahorro = sum(int(o.get('ahorro_min_estimado', 0) or 0) for o in oportunidades)
        estado = 'critico' if criticas else ('mejorable' if oportunidades else 'ok')
        resumen = {
            'bloques_analizados': len(bloques),
            'asignaciones_analizadas': len(asignaciones),
            'oportunidades_por_tipo': self._contar(oportunidades, 'tipo'),
            'oportunidades_por_prioridad': self._contar(oportunidades, 'prioridad'),
            'recursos': recursos_optimizados,
        }
        lectura = f"Optimización inteligente de producción: {len(oportunidades)} oportunidades, ahorro estimado {ahorro} min y estado {estado}."
        return InformeOptimizacionProduccion('3.0.6.7', len(oportunidades), criticas, ahorro, estado, oportunidades, plan_optimizado, recursos_optimizados, resumen, lectura).to_dict()

    def exportar_optimizacion(self, optimizacion: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.produccion_dir / (nombre or 'optimizacion_inteligente_produccion_3067.json')
        destino.write_text(json.dumps(optimizacion, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Optimización inteligente de producción exportada: {destino.name}.'}

    def _generar_planificacion(self, elaboraciones: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        datos = elaboraciones
        if datos is None and hasattr(self.core, 'analizador_inteligente_produccion'):
            datos = self.core.analizador_inteligente_produccion._cargar_elaboraciones_base()
        if hasattr(self.core, 'planificador_inteligente_produccion'):
            return self.core.planificador_inteligente_produccion.planificar_produccion(datos)
        return {'bloques': []}

    def _crear_oportunidad(self, clave: str, elaboracion: str, tipo: str, prioridad: str, ahorro: int, recurso: str, responsable: str, descripcion: str, acciones: List[str], datos: Dict[str, Any]) -> Dict[str, Any]:
        return OportunidadOptimizacionProduccion(clave, elaboracion, tipo, prioridad, int(max(0, ahorro)), recurso, responsable, descripcion, acciones, datos).to_dict()

    def _optimizar_pasivos(self, bloques: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        activos = [b for b in bloques if b.get('tipo_tiempo') == 'activo']
        for b in bloques:
            if b.get('tipo_tiempo') != 'pasivo':
                continue
            dur = int(b.get('duracion_min', b.get('minutos', 0)) or 0)
            if dur >= 120:
                compatibles = [a for a in activos if a.get('clave') != str(b.get('clave','')).replace('_pasivo','') and int(a.get('duracion_min',0) or 0) <= dur]
                if compatibles:
                    out.append(self._crear_oportunidad(
                        str(b.get('clave','')), str(b.get('nombre','')), 'aprovechar_tiempo_pasivo', 'alta' if dur >= 180 else 'normal', min(dur, 90), str(b.get('recurso','')), 'cocinero_disponible',
                        'Tiempo pasivo largo que permite encajar tareas activas sin alargar la jornada.',
                        ['encajar_tareas_activas_durante_pasivo', 'preparar_siguiente_elaboracion', 'validar_recurso_antes_de_iniciar'],
                        {'bloque_pasivo': b, 'compatibles': compatibles[:5]}
                    ))
        return out

    def _optimizar_recursos(self, bloques: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        por_recurso: Dict[str, List[Dict[str, Any]]] = {}
        for b in bloques:
            recurso = str(b.get('recurso') or 'mesa_trabajo')
            por_recurso.setdefault(recurso, []).append(b)
        for recurso, items in por_recurso.items():
            activos = [i for i in items if i.get('tipo_tiempo') == 'activo']
            if len(activos) >= 3:
                ahorro = max(10, min(60, (len(activos)-1)*12))
                out.append(self._crear_oportunidad(
                    f'recurso_{recurso}', f'Recurso {recurso}', 'agrupacion_por_recurso', 'normal', ahorro, recurso, 'jefe_cocina',
                    'Varias tareas usan el mismo recurso; conviene agrupar mise en place, encendidos y limpieza.',
                    ['agrupar_tareas_por_recurso', 'preparar_recurso_en_lote', 'evitar_cambios_innecesarios'],
                    {'recurso': recurso, 'bloques': activos}
                ))
            items_ordenados = sorted(items, key=lambda x: (int(x.get('dia',1) or 1), int(x.get('inicio_min',0) or 0)))
            for prev, nxt in zip(items_ordenados, items_ordenados[1:]):
                if int(prev.get('dia',1) or 1) != int(nxt.get('dia',1) or 1):
                    continue
                hueco = int(nxt.get('inicio_min',0) or 0) - int(prev.get('fin_min',0) or 0)
                if hueco >= 45:
                    out.append(self._crear_oportunidad(
                        f"hueco_{recurso}_{prev.get('clave')}_{nxt.get('clave')}", f'Recurso {recurso}', 'reducir_hueco_recurso', 'normal', min(hueco, 45), recurso, 'jefe_cocina',
                        'Hueco operativo detectado en un recurso crítico.',
                        ['adelantar_bloque_siguiente', 'rellenar_hueco_con_tarea_compatible'],
                        {'bloque_anterior': prev, 'bloque_siguiente': nxt, 'hueco_min': hueco}
                    ))
        return out

    def _optimizar_carga_cocineros(self, asignaciones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cargas: Dict[str, int] = {}
        for a in asignaciones:
            coc = str(a.get('cocinero') or a.get('responsable') or 'sin_asignar')
            cargas[coc] = cargas.get(coc, 0) + int(a.get('duracion_min', a.get('minutos', 0)) or 0)
        if len(cargas) < 2:
            return []
        max_coc = max(cargas, key=cargas.get); min_coc = min(cargas, key=cargas.get)
        diferencia = cargas[max_coc] - cargas[min_coc]
        if diferencia < 90:
            return []
        return [self._crear_oportunidad(
            'equilibrar_cocineros', 'Carga de trabajo', 'equilibrio_carga_cocineros', 'alta' if diferencia >= 180 else 'normal', min(diferencia // 2, 120), 'equipo', min_coc,
            f'Desequilibrio de carga entre {max_coc} y {min_coc}.',
            ['mover_tarea_no_dependiente_al_cocinero_menos_cargado', 'mantener_elaboraciones_críticas_con_responsable_original'],
            {'cargas_min': cargas, 'cocinero_sobrecargado': max_coc, 'cocinero_disponible': min_coc, 'diferencia_min': diferencia}
        )]

    def _optimizar_retrasos(self, control: Dict[str, Any], replanificacion: Dict[str, Any]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for t in control.get('tareas', []) if isinstance(control, dict) else []:
            if str(t.get('riesgo')) in {'critico', 'aviso'} or int(t.get('retraso_min', 0) or 0) > 0:
                out.append(self._crear_oportunidad(
                    str(t.get('clave','')), str(t.get('elaboracion','')), 'recuperacion_retraso', 'critica' if t.get('riesgo') == 'critico' else 'alta', int(t.get('retraso_min', 30) or 30), str(t.get('recurso','')), str(t.get('responsable') or 'cocinero_refuerzo'),
                    'Tarea con riesgo en ejecución que debe optimizarse antes de seguir el plan.',
                    ['priorizar_en_el_siguiente_bloque', 'reasignar_refuerzo_si_hay_cocinero_libre', 'bloquear_nuevas_tareas_dependientes'],
                    {'tarea_control': t}
                ))
        for a in replanificacion.get('acciones', []) if isinstance(replanificacion, dict) else []:
            if str(a.get('prioridad')) in {'critica', 'alta'}:
                out.append(self._crear_oportunidad(
                    str(a.get('clave','')), str(a.get('elaboracion','')), 'aplicar_replanificacion', str(a.get('prioridad','alta')), int(a.get('impacto_min', 30) or 30), str(a.get('recurso','')), str(a.get('responsable_sugerido','')), 
                    'Acción de replanificación que debe incorporarse al plan optimizado.',
                    ['aplicar_accion_replanificacion', 'comunicar_cambio_al_equipo'],
                    {'accion_replanificacion': a}
                ))
        return out

    def _deduplicar_y_ordenar(self, oportunidades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen=set(); out=[]
        for o in oportunidades:
            k=(o.get('clave'), o.get('tipo'))
            if k not in seen:
                seen.add(k); out.append(o)
        peso={'critica':0,'alta':1,'normal':2,'baja':3}
        return sorted(out, key=lambda o: (peso.get(o.get('prioridad','normal'), 2), -int(o.get('ahorro_min_estimado',0)), o.get('tipo','')))

    def _crear_plan_optimizado(self, bloques: List[Dict[str, Any]], oportunidades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        prioridad_claves = {str(o.get('clave','')).replace('_pasivo',''): o for o in oportunidades if o.get('prioridad') in {'critica','alta'}}
        def score(b):
            clave = str(b.get('clave','')).replace('_pasivo','')
            tipo = 1 if b.get('tipo_tiempo') == 'pasivo' else 0
            if clave in prioridad_claves:
                return (0, tipo, int(b.get('inicio_min',0) or 0))
            return (1, int(b.get('dia',1) or 1), int(b.get('inicio_min',0) or 0), tipo)
        plan=[]
        for orden, b in enumerate(sorted(bloques, key=score), start=1):
            nb = dict(b)
            nb['orden_optimizado'] = orden
            nb['motivo_optimizacion'] = prioridad_claves.get(str(b.get('clave','')).replace('_pasivo',''), {}).get('tipo', 'mantener_plan')
            plan.append(nb)
        return plan

    def _resumen_recursos(self, bloques: List[Dict[str, Any]], asignaciones: List[Dict[str, Any]]) -> Dict[str, Any]:
        recursos: Dict[str, int] = {}
        for b in bloques:
            r=str(b.get('recurso') or 'mesa_trabajo')
            recursos[r]=recursos.get(r,0)+int(b.get('duracion_min', b.get('minutos',0)) or 0)
        cocineros: Dict[str, int] = {}
        for a in asignaciones:
            c=str(a.get('cocinero') or a.get('responsable') or 'sin_asignar')
            cocineros[c]=cocineros.get(c,0)+int(a.get('duracion_min', a.get('minutos',0)) or 0)
        return {'minutos_por_recurso': recursos, 'minutos_por_cocinero': cocineros, 'recursos_saturados': [r for r,m in recursos.items() if m >= 360]}

    def _contar(self, items: List[Dict[str, Any]], campo: str) -> Dict[str, int]:
        out: Dict[str,int] = {}
        for i in items:
            k=str(i.get(campo,'sin_dato')); out[k]=out.get(k,0)+1
        return out
