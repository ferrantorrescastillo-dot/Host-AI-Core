"""Automatizador inteligente del bloque Host AI 3.0.8.6.

Prepara y ejecuta acciones conversacionales con control de confirmación.
"""
from __future__ import annotations
from typing import Dict, Any, List
from MODELOS.ia_conversacional_308 import AccionAutomatizada308
from MODELOS.api_interna import SolicitudPipeline

class AutomatizadorInteligente308:
    VERSION = '3.0.8.6'

    def __init__(self, core=None):
        self.core = core
        self.acciones_impacto = {'crear_pedido','actualizar_escandallo','modificar_articulo','generar_produccion','eliminar','actualizar','crear'}

    def _detectar_accion(self, texto: str, analisis: Dict[str, Any] | None = None) -> str:
        t = (texto or '').lower()
        if any(x in t for x in ['pedido', 'compra esto', 'comprar', 'pide ']): return 'crear_pedido'
        if any(x in t for x in ['actualiza escandallo','cambia escandallo','modifica receta']): return 'actualizar_escandallo'
        if any(x in t for x in ['añade artículo','añadir articulo','nuevo artículo','nuevo articulo']): return 'modificar_articulo'
        if any(x in t for x in ['genera producción','generar produccion','organiza producción','plan de producción']): return 'generar_produccion'
        if any(x in t for x in ['exporta','exportar','informe']): return 'exportar_informe'
        return 'consulta_operativa'

    def preparar(self, texto: str = '', analisis: Dict[str, Any] | None = None, seleccion: Dict[str, Any] | None = None, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
        contexto = contexto or {}
        if analisis is None and self.core:
            analisis = self.core.analizador_lenguaje_natural.analizar(texto, contexto)
        analisis = analisis or {}
        if seleccion is None and self.core:
            seleccion = self.core.selector_inteligente_motores_308.seleccionar(texto, analisis, contexto)
        seleccion = seleccion or {}
        accion = self._detectar_accion(texto, analisis)
        pipeline = seleccion.get('pipeline_seleccionado') or analisis.get('pipeline_sugerido') or 'motor_conversacional_308'
        accion_pipeline = seleccion.get('accion_seleccionada') or analisis.get('accion_sugerida') or 'responder'
        parametros = dict(seleccion.get('parametros') or {})
        parametros.update({'texto': texto, 'analisis': analisis, 'contexto': contexto})
        riesgos: List[str] = []
        requiere = accion in self.acciones_impacto or bool(seleccion.get('requiere_confirmacion'))
        if requiere:
            riesgos.append('La acción puede modificar datos operativos o generar trabajo real; requiere confirmación explícita.')
        if not seleccion.get('disponible', True):
            riesgos.append('El pipeline seleccionado no aparece disponible en el registro actual.')
        pasos = [
            'Interpretar lenguaje natural.',
            f'Seleccionar pipeline {pipeline}.{accion_pipeline}.',
            'Preparar parámetros trazables.',
            'Solicitar confirmación si hay impacto operativo.' if requiere else 'Ejecutar como consulta segura si se solicita.'
        ]
        return AccionAutomatizada308(self.VERSION, texto, accion, pipeline, accion_pipeline, parametros, requiere, True, False, {}, riesgos, pasos, f'Automatizador 3.0.8.6: acción preparada ({accion}).').to_dict()

    def ejecutar(self, texto: str = '', confirmado: bool = False, analisis: Dict[str, Any] | None = None, seleccion: Dict[str, Any] | None = None, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
        plan = self.preparar(texto, analisis, seleccion, contexto)
        if plan['requiere_confirmacion'] and not confirmado:
            plan['puede_ejecutarse'] = False
            plan['lectura_host_ai'] = 'Acción preparada pero pendiente de confirmación explícita.'
            return plan
        resultado: Dict[str, Any] = {}
        try:
            if self.core and plan['pipeline_destino'] in getattr(self.core.registro_pipelines, 'pipelines', {}):
                res = self.core.director.ejecutar_pipeline(plan['pipeline_destino'], plan['accion_pipeline'], plan['parametros'])
                resultado = res.to_dict() if hasattr(res, 'to_dict') else dict(res)
            else:
                resultado = {'ok': True, 'mensaje': 'Ejecución simulada segura: pipeline no ejecutado directamente.', 'datos': {'plan': plan}}
            plan['ejecutada'] = True
            plan['resultado'] = resultado
            plan['lectura_host_ai'] = f'Automatizador 3.0.8.6: acción ejecutada ({plan["accion_detectada"]}).'
        except Exception as exc:
            plan['ejecutada'] = False
            plan['resultado'] = {'ok': False, 'error': str(exc)}
            plan['lectura_host_ai'] = f'Error ejecutando automatización: {exc}'
        return plan

    def validar_confirmacion(self, plan: Dict[str, Any], confirmado: bool = False) -> Dict[str, Any]:
        requiere = bool(plan.get('requiere_confirmacion'))
        return {
            'version': self.VERSION,
            'confirmado': bool(confirmado),
            'requiere_confirmacion': requiere,
            'puede_ejecutarse': (not requiere) or bool(confirmado),
            'lectura_host_ai': 'Confirmación validada.' if ((not requiere) or confirmado) else 'Falta confirmación para ejecutar la acción.'
        }

__all__ = ['AutomatizadorInteligente308']
