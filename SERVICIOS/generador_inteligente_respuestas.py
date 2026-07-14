"""
Host AI - Servicio: Generador Inteligente de Respuestas 3.0.8.4.

Servicio de la capa IA Conversacional. Mantiene la lógica de negocio
separada de pipelines y modelos. Este archivo forma parte del proceso de
estabilización RC2 y no modifica el comportamiento funcional del sistema.
"""
from __future__ import annotations
from typing import Dict, Any, List
from MODELOS.ia_conversacional_308 import RespuestaNatural308

class GeneradorInteligenteRespuestas308:
    VERSION = '3.0.8.4'

    def __init__(self, core=None):
        self.core = core

    def _contar(self, valor: Any) -> int:
        if isinstance(valor, list): return len(valor)
        if isinstance(valor, dict): return len(valor)
        return 0 if valor in (None, '') else 1

    def _extraer_metricas(self, datos: Dict[str, Any]) -> List[str]:
        detalle: List[str] = []
        claves_interes = [
            'analisis','recomendaciones','anomalias','predicciones','alertas','incidencias',
            'articulos','proveedores','movimientos','ubicaciones','escandallos','recetas','resultados'
        ]
        for k in claves_interes:
            if k in datos:
                detalle.append(f'{k.capitalize()}: {self._contar(datos[k])}')
        for k, v in datos.items():
            if isinstance(v, (int, float)) and k not in {'version'}:
                detalle.append(f'{k}: {v}')
        return detalle[:12]

    def generar(self, resultado: Dict[str, Any] | None = None, seleccion: Dict[str, Any] | None = None, tono: str = 'profesional') -> Dict[str, Any]:
        resultado = resultado or {}
        seleccion = seleccion or {}
        ok = resultado.get('ok', True)
        datos = resultado.get('datos') if isinstance(resultado.get('datos'), dict) else resultado
        if not isinstance(datos, dict): datos = {'resultado': datos}
        pipeline = seleccion.get('pipeline_seleccionado') or resultado.get('pipeline') or datos.get('pipeline') or 'Host AI'
        accion = seleccion.get('accion_seleccionada') or resultado.get('accion') or datos.get('accion') or 'consulta'
        tipo = 'error' if not ok else 'respuesta_operativa'
        titulo = 'No he podido completar la operación' if not ok else f'Resultado de {pipeline}'
        resumen_base = resultado.get('mensaje') or datos.get('lectura_host_ai') or seleccion.get('lectura_host_ai')
        if not resumen_base:
            resumen_base = f'He procesado la acción {accion} usando el motor {pipeline}.'
        detalle = self._extraer_metricas(datos)
        advertencias: List[str] = []
        if seleccion.get('requiere_confirmacion'):
            advertencias.append('Esta acción puede tener impacto operativo; conviene pedir confirmación antes de ejecutarla.')
        if not seleccion.get('disponible', True):
            advertencias.append('El pipeline seleccionado no aparece disponible en el registro actual.')
        if not ok:
            errores = resultado.get('errores') or datos.get('errores') or []
            advertencias.extend([str(e) for e in errores[:5]])
        recomendaciones = []
        if tipo != 'error':
            recomendaciones.append('Revisar el resultado antes de aplicar cambios sobre compras, stock, producción o escandallos.')
            if detalle:
                recomendaciones.append('Usar el detalle como resumen ejecutivo y consultar el JSON si necesitas trazabilidad completa.')
        lectura = 'Generador 3.0.8.4: respuesta natural creada a partir de resultado técnico Host AI.'
        return RespuestaNatural308(self.VERSION, tipo, titulo, str(resumen_base), detalle, recomendaciones, advertencias, datos, lectura).to_dict()

    def generar_desde_texto(self, texto: str, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
        contexto = contexto or {}
        analisis = self.core.analizador_lenguaje_natural.analizar(texto, contexto) if self.core else {}
        seleccion = self.core.selector_inteligente_motores_308.seleccionar(texto, analisis, contexto) if self.core else {}
        resultado_simulado = {'ok': True, 'mensaje': seleccion.get('lectura_host_ai','Consulta procesada.'), 'datos': {'analisis': analisis, 'seleccion': seleccion}}
        return self.generar(resultado_simulado, seleccion)


__all__ = ['GeneradorInteligenteRespuestas308']
