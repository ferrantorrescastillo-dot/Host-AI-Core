"""Asistente integrado Host AI del bloque 3.0.8.7.

Coordina memoria, lenguaje natural, selección de motores, automatización y respuesta.
"""
from __future__ import annotations
from typing import Dict, Any, List
from MODELOS.ia_conversacional_308 import ResultadoAsistenteHostAI308

class AsistenteInteligenteHostAI308:
    VERSION = '3.0.8.7'

    def __init__(self, core=None):
        self.core = core

    def responder(self, texto: str = '', contexto: Dict[str, Any] | None = None, ejecutar: bool = False, confirmado: bool = False) -> Dict[str, Any]:
        contexto = contexto or {}
        pasos: List[str] = []
        texto = texto or ''

        # 1. Memoria: resolver referencias antes de analizar.
        memoria = {}
        contexto_enriquecido = dict(contexto)
        try:
            if self.core and hasattr(self.core, 'memoria_conversacional_308'):
                memoria = self.core.memoria_conversacional_308.resolver_referencias(texto, contexto)
                contexto_enriquecido.update(memoria.get('referencias_resueltas', {}))
                pasos.append('Memoria conversacional consultada y referencias resueltas.')
        except Exception as exc:
            memoria = {'ok': False, 'error': str(exc), 'referencias_resueltas': {}}
            pasos.append('Memoria conversacional no disponible o con error controlado.')

        # 2. Analizador de lenguaje natural.
        analisis = {}
        try:
            if self.core and hasattr(self.core, 'analizador_lenguaje_natural'):
                analisis = self.core.analizador_lenguaje_natural.analizar(texto, contexto_enriquecido)
                pasos.append('Lenguaje natural analizado.')
        except Exception as exc:
            analisis = {'intencion_detectada': 'desconocida', 'pipeline_sugerido': 'motor_conversacional_308', 'accion_sugerida': 'responder', 'confianza': 0.2, 'error': str(exc)}
            pasos.append('Análisis de lenguaje natural degradado por error controlado.')

        # 3. Selector de motores.
        seleccion = {}
        try:
            if self.core and hasattr(self.core, 'selector_inteligente_motores_308'):
                seleccion = self.core.selector_inteligente_motores_308.seleccionar(texto, analisis, contexto_enriquecido)
                pasos.append('Motor operativo seleccionado.')
        except Exception as exc:
            seleccion = {'pipeline_seleccionado': analisis.get('pipeline_sugerido', 'motor_conversacional_308'), 'accion_seleccionada': analisis.get('accion_sugerida', 'responder'), 'confianza': analisis.get('confianza', 0.3), 'disponible': False, 'error': str(exc)}
            pasos.append('Selección de motor degradada por error controlado.')

        # 4. Automatizador: prepara siempre, ejecuta solo si se solicita.
        automatizacion = {}
        try:
            if self.core and hasattr(self.core, 'automatizador_inteligente_308'):
                if ejecutar:
                    automatizacion = self.core.automatizador_inteligente_308.ejecutar(texto, confirmado, analisis, seleccion, contexto_enriquecido)
                    pasos.append('Automatización ejecutada o retenida según confirmación.')
                else:
                    automatizacion = self.core.automatizador_inteligente_308.preparar(texto, analisis, seleccion, contexto_enriquecido)
                    pasos.append('Automatización preparada en modo seguro.')
        except Exception as exc:
            automatizacion = {'requiere_confirmacion': False, 'ejecutada': False, 'error': str(exc), 'lectura_host_ai': 'Automatización no disponible.'}
            pasos.append('Automatizador no disponible o con error controlado.')

        # 5. Generador de respuesta natural.
        respuesta_natural = {}
        try:
            if self.core and hasattr(self.core, 'generador_inteligente_respuestas_308'):
                resultado_fuente = {
                    'ok': True,
                    'mensaje': automatizacion.get('lectura_host_ai') or seleccion.get('motivo') or 'Consulta procesada por Host AI.',
                    'datos': {
                        'analisis': analisis,
                        'seleccion': seleccion,
                        'automatizacion': automatizacion,
                        'memoria': memoria,
                    }
                }
                respuesta_natural = self.core.generador_inteligente_respuestas_308.generar(resultado_fuente, seleccion, contexto_enriquecido)
                pasos.append('Respuesta natural generada.')
        except Exception as exc:
            respuesta_natural = {
                'titulo': 'Host AI',
                'resumen': 'He entendido la solicitud y he preparado la acción más segura disponible.',
                'detalle': [str(exc)],
                'recomendaciones': [],
                'advertencias': [],
                'lectura_host_ai': 'Respuesta generada en modo fallback.'
            }
            pasos.append('Respuesta natural generada en modo fallback.')

        # 6. Aprendizaje de memoria desde turno.
        try:
            if self.core and hasattr(self.core, 'memoria_conversacional_308'):
                turno = {'usuario': texto, 'analisis': analisis, 'seleccion': seleccion, 'automatizacion': automatizacion}
                self.core.memoria_conversacional_308.aprender_desde_turno({'datos': {'analisis': analisis}, 'analisis': analisis, 'turno': turno})
                pasos.append('Memoria actualizada con el turno actual.')
        except Exception:
            pasos.append('Memoria no actualizada por error no crítico.')

        confianza = float(analisis.get('confianza', 0.0) or 0.0)
        confianza_sel = float(seleccion.get('confianza', confianza) or confianza)
        confianza_global = round((confianza + confianza_sel) / 2, 3)
        respuesta_final = respuesta_natural.get('resumen') or respuesta_natural.get('lectura_host_ai') or 'Solicitud procesada por Host AI.'
        requiere = bool(automatizacion.get('requiere_confirmacion'))
        lectura = 'Asistente Inteligente Host AI 3.0.8.7 ha procesado la consulta de extremo a extremo.'
        if requiere and not confirmado:
            lectura += ' La acción queda pendiente de confirmación.'

        return ResultadoAsistenteHostAI308(
            self.VERSION,
            texto,
            respuesta_final,
            analisis.get('intencion_detectada', 'desconocida'),
            seleccion.get('pipeline_seleccionado', analisis.get('pipeline_sugerido', 'motor_conversacional_308')),
            seleccion.get('accion_seleccionada', analisis.get('accion_sugerida', 'responder')),
            memoria,
            seleccion,
            respuesta_natural,
            automatizacion,
            requiere,
            confianza_global,
            pasos,
            lectura,
        ).to_dict()

    def diagnosticar(self) -> Dict[str, Any]:
        componentes = {
            'analizador_lenguaje_natural': hasattr(self.core, 'analizador_lenguaje_natural') if self.core else False,
            'motor_conversacional_308': hasattr(self.core, 'motor_conversacional_308') if self.core else False,
            'selector_inteligente_motores_308': hasattr(self.core, 'selector_inteligente_motores_308') if self.core else False,
            'generador_inteligente_respuestas_308': hasattr(self.core, 'generador_inteligente_respuestas_308') if self.core else False,
            'memoria_conversacional_308': hasattr(self.core, 'memoria_conversacional_308') if self.core else False,
            'automatizador_inteligente_308': hasattr(self.core, 'automatizador_inteligente_308') if self.core else False,
        }
        return {
            'version': self.VERSION,
            'componentes': componentes,
            'ok': all(componentes.values()),
            'lectura_host_ai': f'Diagnóstico asistente 3.0.8.7: {sum(1 for v in componentes.values() if v)}/{len(componentes)} componentes disponibles.'
        }

    def exportar(self, nombre: str = '') -> Dict[str, Any]:
        return {
            'version': self.VERSION,
            'nombre': nombre or 'asistente_inteligente_host_ai_3087',
            'lectura_host_ai': 'Asistente Inteligente Host AI 3.0.8.7 preparado para exportación lógica.'
        }

__all__ = ['AsistenteInteligenteHostAI308']
