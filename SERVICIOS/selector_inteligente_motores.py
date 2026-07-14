from __future__ import annotations
from typing import Dict, Any, List, Tuple
from MODELOS.ia_conversacional_308 import SeleccionMotor308

class SelectorInteligenteMotores308:
    VERSION = '3.0.8.3'

    def __init__(self, core=None):
        self.core = core
        self.rutas = {
            'consulta_compras': ('motor_inteligente_pedidos', 'generar', 'Consulta relacionada con compras o pedidos.'),
            'consulta_stock': ('analizador_inteligente_stock', 'analizar', 'Consulta relacionada con stock.'),
            'consulta_produccion': ('planificador_inteligente_produccion', 'planificar', 'Consulta relacionada con producción.'),
            'consulta_escandallos': ('analizador_inteligente_escandallos', 'analizar', 'Consulta relacionada con escandallos o rentabilidad.'),
            'consulta_anomalias': ('detector_anomalias_compras', 'detectar', 'Consulta relacionada con anomalías.'),
            'consulta_alertas': ('motor_alertas_stock', 'generar', 'Consulta relacionada con alertas operativas.'),
            'conversacion_general': ('motor_conversacional_308', 'responder', 'Consulta conversacional general.'),
        }
        self.acciones_con_confirmacion = {'crear', 'actualizar', 'eliminar', 'generar_pedido', 'ejecutar'}

    def _pipelines_disponibles(self) -> set[str]:
        try:
            registro = getattr(self.core, 'registro_pipelines', None)
            if registro and hasattr(registro, 'pipelines'):
                return set(registro.pipelines.keys())
            if registro and hasattr(registro, '_pipelines'):
                return set(registro._pipelines.keys())
        except Exception:
            pass
        return set()

    def _alternativas(self, intencion: str) -> List[Dict[str, Any]]:
        orden = ['consulta_compras','consulta_stock','consulta_produccion','consulta_escandallos','consulta_anomalias','consulta_alertas']
        alts = []
        for k in orden:
            if k == intencion or k not in self.rutas: continue
            pipeline, accion, motivo = self.rutas[k]
            alts.append({'intencion': k, 'pipeline': pipeline, 'accion': accion, 'motivo': motivo})
        return alts[:3]

    def seleccionar(self, texto: str = '', analisis: Dict[str, Any] | None = None, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
        contexto = contexto or {}
        if analisis is None:
            analisis = self.core.analizador_lenguaje_natural.analizar(texto, contexto) if self.core else {}
        intencion = analisis.get('intencion_detectada') or 'conversacion_general'
        pipeline, accion, motivo = self.rutas.get(intencion, self.rutas['conversacion_general'])
        # respetar si el analizador ya trae una sugerencia concreta válida
        pipeline = analisis.get('pipeline_sugerido') or pipeline
        accion = analisis.get('accion_sugerida') or accion
        disponibles = self._pipelines_disponibles()
        disponible = True if not disponibles else pipeline in disponibles
        parametros = {
            'texto': texto or analisis.get('texto_original',''),
            'analisis': analisis,
            'entidades': analisis.get('entidades', []),
            'contexto': contexto,
        }
        requiere_confirmacion = accion in self.acciones_con_confirmacion or intencion in {'consulta_compras'} and 'pedido' in pipeline
        solicitud = {'pipeline': pipeline, 'accion': accion, 'parametros': parametros}
        lectura = f'Selector 3.0.8.3: intención {intencion}; motor seleccionado {pipeline}.{accion}.'
        if not disponible:
            lectura += ' Aviso: el pipeline no aparece registrado en el proyecto actual.'
        return SeleccionMotor308(
            self.VERSION, texto or analisis.get('texto_original',''), intencion, pipeline, accion,
            parametros, float(analisis.get('confianza', 0.0)), self._alternativas(intencion),
            disponible, requiere_confirmacion, motivo, solicitud, lectura
        ).to_dict()

    def seleccionar_desde_conversacion(self, conversacion: Dict[str, Any]) -> Dict[str, Any]:
        analisis = conversacion.get('datos', {}).get('analisis') or conversacion.get('analisis') or {}
        texto = conversacion.get('usuario') or conversacion.get('texto_usuario') or analisis.get('texto_original','')
        contexto = conversacion.get('contexto_actualizado') or {}
        return self.seleccionar(texto, analisis, contexto)
