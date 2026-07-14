"""Cierre técnico del bloque Host AI 3.0.8.8.

Valida la integración final de la capa de IA conversacional.
"""
from __future__ import annotations
from typing import Dict, Any, List
from MODELOS.ia_conversacional_308 import CierreIAConversacional308

class CierreIAConversacional308Servicio:
    VERSION = '3.0.8.8'

    MODULOS = [
        ('3.0.8.1', 'analizador_lenguaje_natural', 'analizar_lenguaje_natural'),
        ('3.0.8.2', 'motor_conversacional_308', 'conversar_host_ai_308'),
        ('3.0.8.3', 'selector_inteligente_motores_308', 'seleccionar_motor_host_ai_308'),
        ('3.0.8.4', 'generador_inteligente_respuestas_308', 'generar_respuesta_host_ai_308'),
        ('3.0.8.5', 'memoria_conversacional_308', 'recordar_memoria_conversacional_308'),
        ('3.0.8.6', 'automatizador_inteligente_308', 'preparar_automatizacion_308'),
        ('3.0.8.7', 'asistente_inteligente_host_ai_308', 'asistente_host_ai_308'),
    ]

    def __init__(self, core=None):
        self.core = core

    def comprobar(self, ejecutar_pruebas: bool = True) -> Dict[str, Any]:
        validados: List[str] = []
        incidencias: List[str] = []
        metricas: Dict[str, Any] = {}
        informe: Dict[str, Any] = {'modulos': []}

        registro = getattr(self.core, 'registro_pipelines', None) if self.core else None
        pipelines = getattr(registro, '_pipelines', getattr(registro, 'pipelines', {})) if registro else {}
        for version, atributo, intencion in self.MODULOS:
            existe_servicio = hasattr(self.core, atributo) if self.core else False
            existe_pipeline = atributo in pipelines
            ok = bool(existe_servicio and existe_pipeline)
            if ok:
                validados.append(version)
            else:
                if not existe_servicio:
                    incidencias.append(f'{version}: servicio no disponible ({atributo}).')
                if not existe_pipeline:
                    incidencias.append(f'{version}: pipeline no registrado ({atributo}).')
            informe['modulos'].append({
                'version': version,
                'servicio': atributo,
                'intencion_principal': intencion,
                'servicio_disponible': existe_servicio,
                'pipeline_registrado': existe_pipeline,
                'ok': ok,
            })

        prueba_conversacional = {}
        if ejecutar_pruebas and self.core:
            try:
                prueba_conversacional = self.core.asistente_inteligente_host_ai_308.responder('qué debo comprar mañana', {}, ejecutar=False)
                if prueba_conversacional.get('respuesta_final'):
                    metricas['prueba_asistente_ok'] = True
                else:
                    metricas['prueba_asistente_ok'] = False
                    incidencias.append('La prueba del asistente no generó respuesta final.')
            except Exception as exc:
                metricas['prueba_asistente_ok'] = False
                incidencias.append(f'Error en prueba conversacional integrada: {exc}')

        metricas.update({
            'modulos_previstos': len(self.MODULOS),
            'modulos_validados': len(validados),
            'pipelines_308_registrados': len([k for k in pipelines.keys() if '308' in k or k in {'analizador_lenguaje_natural'}]),
            'incidencias': len(incidencias),
        })
        informe['prueba_conversacional'] = prueba_conversacional
        ok_global = len(incidencias) == 0 and len(validados) == len(self.MODULOS)
        acciones = []
        if ok_global:
            acciones.append('Bloque 3.0.8 preparado para validación final en PowerShell.')
            acciones.append('Preparar diseño Host AI 4.0 con integración LLM controlada por motores internos.')
        else:
            acciones.append('Revisar incidencias antes de cerrar Host AI 3.0.')

        lectura = 'Cierre IA Conversacional 3.0.8.8 completado correctamente.' if ok_global else 'Cierre IA Conversacional 3.0.8.8 completado con incidencias.'
        return CierreIAConversacional308(self.VERSION, validados, len(self.MODULOS), ok_global, incidencias, metricas, informe, acciones, lectura).to_dict()

    def exportar(self, nombre: str = '') -> Dict[str, Any]:
        datos = self.comprobar(ejecutar_pruebas=False)
        datos['exportacion'] = {'nombre': nombre or 'cierre_ia_conversacional_3088'}
        datos['lectura_host_ai'] = 'Informe de cierre IA Conversacional preparado para exportación lógica.'
        return datos

__all__ = ['CierreIAConversacional308Servicio']
