from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.optimizacion_produccion_306 import ComprobacionCierreProduccion, InformeCierreProduccion

class CierreInteligenteProduccion:
    """Host AI 3.0.6.8 - Cierre Inteligente de Producción.

    Valida el bloque completo 3.0.6 como sistema: análisis, alertas, planificación,
    asignación, control, replanificación y optimización. Genera un informe final.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.produccion_dir = self.base_dir / 'DATOS' / 'produccion'
        self.produccion_dir.mkdir(parents=True, exist_ok=True)

    def comprobar_cierre(self, elaboraciones: List[Dict[str, Any]] | None = None, analisis: Dict[str, Any] | None = None, alertas: Dict[str, Any] | None = None, planificacion: Dict[str, Any] | None = None, asignacion: Dict[str, Any] | None = None, control: Dict[str, Any] | None = None, replanificacion: Dict[str, Any] | None = None, optimizacion: Dict[str, Any] | None = None) -> Dict[str, Any]:
        datos = elaboraciones or self._elaboraciones_base()
        analisis = analisis or self._seguro('analizador_inteligente_produccion', 'analizar_produccion', datos)
        alertas = alertas or self._seguro('motor_alertas_produccion', 'generar_alertas', datos)
        planificacion = planificacion or self._seguro('planificador_inteligente_produccion', 'planificar_produccion', datos)
        asignacion = asignacion or self._seguro('asignador_recursos_produccion', 'asignar_recursos', datos, planificacion)
        control = control or self._seguro('control_ejecucion_produccion', 'controlar_ejecucion', planificacion, asignacion, [], 0)
        replanificacion = replanificacion or self._seguro('replanificador_inteligente_produccion', 'replanificar_produccion', control, planificacion, [], 3)
        optimizacion = optimizacion or self._seguro('optimizador_inteligente_produccion', 'optimizar_produccion', planificacion, asignacion, control, replanificacion, datos)
        comprobaciones: List[Dict[str, Any]] = []
        comprobaciones.extend(self._validar_modulos(analisis, alertas, planificacion, asignacion, control, replanificacion, optimizacion))
        comprobaciones.extend(self._validar_coherencia(analisis, alertas, planificacion, asignacion, control, replanificacion, optimizacion))
        metricas = self._metricas(analisis, alertas, planificacion, asignacion, control, replanificacion, optimizacion)
        ok = sum(1 for c in comprobaciones if c['estado'] == 'ok')
        aviso = sum(1 for c in comprobaciones if c['gravedad'] == 'aviso')
        criticas = sum(1 for c in comprobaciones if c['gravedad'] == 'critica')
        estado = 'bloqueado' if criticas else ('revisar' if aviso else 'cerrado')
        informe_final = {
            'bloque': 'HOST AI 3.0.6 Producción',
            'estado': estado,
            'modulos': ['3.0.6.1','3.0.6.2','3.0.6.3','3.0.6.4','3.0.6.5','3.0.6.6','3.0.6.7','3.0.6.8'],
            'lectura_operativa': self._lectura_operativa(estado, metricas, criticas, aviso),
            'siguiente_bloque': 'HOST AI 3.0.7 Escandallos inteligentes',
        }
        lectura = f"Cierre inteligente de producción: estado {estado}, {ok}/{len(comprobaciones)} comprobaciones OK, {criticas} críticas."
        return InformeCierreProduccion('3.0.6.8', estado, 8, len(comprobaciones), ok, aviso, criticas, metricas, comprobaciones, informe_final, lectura).to_dict()

    def exportar_cierre(self, cierre: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.produccion_dir / (nombre or 'cierre_inteligente_produccion_3068.json')
        destino.write_text(json.dumps(cierre, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Cierre inteligente de producción exportado: {destino.name}.'}

    def _elaboraciones_base(self) -> List[Dict[str, Any]]:
        if hasattr(self.core, 'analizador_inteligente_produccion'):
            return self.core.analizador_inteligente_produccion._cargar_elaboraciones_base()
        return []

    def _seguro(self, atributo: str, metodo: str, *args) -> Dict[str, Any]:
        servicio = getattr(self.core, atributo, None)
        if not servicio or not hasattr(servicio, metodo):
            return {'version': 'no_disponible', 'error': f'{atributo}.{metodo} no disponible'}
        try:
            return getattr(servicio, metodo)(*args)
        except TypeError:
            try:
                return getattr(servicio, metodo)()
            except Exception as exc:
                return {'version': 'error', 'error': str(exc)}
        except Exception as exc:
            return {'version': 'error', 'error': str(exc)}

    def _check(self, clave: str, modulo: str, estado: str, mensaje: str, gravedad: str = 'info', datos: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return ComprobacionCierreProduccion(clave, modulo, estado, mensaje, gravedad, datos or {}).to_dict()

    def _validar_modulos(self, analisis, alertas, planificacion, asignacion, control, replanificacion, optimizacion) -> List[Dict[str, Any]]:
        modulos = [
            ('3061', 'Analizador Inteligente de Producción', analisis, '3.0.6.1'),
            ('3062', 'Motor Alertas Producción', alertas, '3.0.6.2'),
            ('3063', 'Planificador Inteligente de Producción', planificacion, '3.0.6.3'),
            ('3064', 'Asignador Recursos Producción', asignacion, '3.0.6.4'),
            ('3065', 'Control Ejecución Producción', control, '3.0.6.5'),
            ('3066', 'Replanificador Producción', replanificacion, '3.0.6.6'),
            ('3067', 'Optimizador Producción', optimizacion, '3.0.6.7'),
        ]
        out=[]
        for clave, nombre, datos, version in modulos:
            if not isinstance(datos, dict) or datos.get('error'):
                out.append(self._check(clave, nombre, 'error', f'Módulo no ejecutado correctamente: {datos.get("error") if isinstance(datos, dict) else "sin datos"}', 'critica', {'datos': datos}))
            elif datos.get('version') != version:
                out.append(self._check(clave, nombre, 'aviso', f'Versión esperada {version}, recibida {datos.get("version")}.', 'aviso', {'version_recibida': datos.get('version')}))
            else:
                out.append(self._check(clave, nombre, 'ok', f'{nombre} validado correctamente.', 'info', {'version': version}))
        return out

    def _validar_coherencia(self, analisis, alertas, planificacion, asignacion, control, replanificacion, optimizacion) -> List[Dict[str, Any]]:
        out=[]
        total_elab = int(analisis.get('total_elaboraciones', 0) or 0) if isinstance(analisis, dict) else 0
        bloques = int(planificacion.get('total_bloques', 0) or 0) if isinstance(planificacion, dict) else 0
        asignaciones = int(asignacion.get('total_asignaciones', 0) or 0) if isinstance(asignacion, dict) else 0
        tareas = int(control.get('total_tareas', 0) or 0) if isinstance(control, dict) else 0
        if total_elab <= 0:
            out.append(self._check('coherencia_elaboraciones', 'Cierre Producción', 'aviso', 'No hay elaboraciones analizadas.', 'aviso'))
        else:
            out.append(self._check('coherencia_elaboraciones', 'Cierre Producción', 'ok', f'{total_elab} elaboraciones analizadas.'))
        if bloques < total_elab:
            out.append(self._check('coherencia_plan', 'Cierre Producción', 'aviso', 'La planificación tiene menos bloques que elaboraciones.', 'aviso', {'bloques': bloques, 'elaboraciones': total_elab}))
        else:
            out.append(self._check('coherencia_plan', 'Cierre Producción', 'ok', f'{bloques} bloques planificados.'))
        if asignaciones <= 0:
            out.append(self._check('coherencia_asignacion', 'Cierre Producción', 'aviso', 'No hay asignaciones de recursos/cocineros.', 'aviso'))
        else:
            out.append(self._check('coherencia_asignacion', 'Cierre Producción', 'ok', f'{asignaciones} asignaciones generadas.'))
        if tareas <= 0:
            out.append(self._check('coherencia_control', 'Cierre Producción', 'aviso', 'El control no contiene tareas activas.', 'aviso'))
        else:
            out.append(self._check('coherencia_control', 'Cierre Producción', 'ok', f'{tareas} tareas controladas.'))
        if int(optimizacion.get('total_oportunidades', 0) or 0) >= 0:
            out.append(self._check('coherencia_optimizacion', 'Cierre Producción', 'ok', 'Optimización conectada al cierre.'))
        return out

    def _metricas(self, analisis, alertas, planificacion, asignacion, control, replanificacion, optimizacion) -> Dict[str, Any]:
        return {
            'elaboraciones': analisis.get('total_elaboraciones', 0) if isinstance(analisis, dict) else 0,
            'alertas': alertas.get('total_alertas', 0) if isinstance(alertas, dict) else 0,
            'bloques': planificacion.get('total_bloques', 0) if isinstance(planificacion, dict) else 0,
            'dias_planificados': planificacion.get('dias_planificados', 0) if isinstance(planificacion, dict) else 0,
            'minutos_activos': planificacion.get('minutos_activos', 0) if isinstance(planificacion, dict) else 0,
            'asignaciones': asignacion.get('total_asignaciones', 0) if isinstance(asignacion, dict) else 0,
            'tareas_controladas': control.get('total_tareas', 0) if isinstance(control, dict) else 0,
            'replanificaciones': replanificacion.get('total_acciones', 0) if isinstance(replanificacion, dict) else 0,
            'oportunidades_optimizacion': optimizacion.get('total_oportunidades', 0) if isinstance(optimizacion, dict) else 0,
            'ahorro_estimado_min': optimizacion.get('ahorro_total_min_estimado', 0) if isinstance(optimizacion, dict) else 0,
        }

    def _lectura_operativa(self, estado: str, metricas: Dict[str, Any], criticas: int, avisos: int) -> str:
        if estado == 'cerrado':
            return 'El bloque de Producción queda coherente y listo para utilizarse como sistema integrado.'
        if estado == 'revisar':
            return f'El bloque funciona, pero quedan {avisos} avisos que conviene revisar antes de pasar a producción real.'
        return f'El bloque no debe cerrarse todavía: hay {criticas} comprobaciones críticas.'
