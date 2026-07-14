"""
Host AI - Servicio: Motor Conversacional 3.0.8.2.

Servicio de la capa IA Conversacional. Mantiene la lógica de negocio
separada de pipelines y modelos. Este archivo forma parte del proceso de
estabilización RC2 y no modifica el comportamiento funcional del sistema.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List
from MODELOS.ia_conversacional_308 import RespuestaConversacional308, TurnoConversacional308

class MotorConversacional308:
    VERSION = '3.0.8.2'

    def __init__(self, core=None):
        self.core = core
        self.historial: List[Dict[str, Any]] = []
        self.contexto: Dict[str, Any] = {}

    def limpiar(self) -> Dict[str, Any]:
        self.historial.clear(); self.contexto.clear()
        return {'version': self.VERSION, 'historial': [], 'contexto': {}, 'lectura_host_ai': 'Memoria conversacional 3.0.8 limpiada.'}

    def _respuesta_natural(self, analisis: Dict[str, Any], resultado_motor: Dict[str, Any] | None = None) -> str:
        intencion = analisis.get('intencion_detectada', '')
        entidades = analisis.get('entidades', [])
        articulos = [e.get('valor') for e in entidades if e.get('tipo') == 'articulo']
        fechas = [e.get('valor') for e in entidades if e.get('tipo') == 'fecha']
        if analisis.get('requiere_aclaracion'):
            return 'Necesito que me concretes un poco más qué quieres consultar o ejecutar dentro de Host AI.'
        base = {
            'consulta_compras': 'He entendido que quieres revisar compras o pedidos.',
            'consulta_stock': 'He entendido que quieres consultar o analizar stock.',
            'consulta_produccion': 'He entendido que quieres organizar o revisar producción.',
            'consulta_escandallos': 'He entendido que quieres revisar escandallos, costes o rentabilidad.',
            'consulta_anomalias': 'He entendido que quieres detectar anomalías o errores.',
            'consulta_alertas': 'He entendido que quieres generar alertas operativas.',
        }.get(intencion, 'He recibido la consulta y la mantengo en contexto.')
        extras = []
        if articulos: extras.append('Artículos detectados: ' + ', '.join(articulos) + '.')
        if fechas: extras.append('Fecha/contexto temporal: ' + ', '.join(fechas) + '.')
        return ' '.join([base] + extras + [f"Pipeline sugerido: {analisis.get('pipeline_sugerido')}.{analisis.get('accion_sugerida')}."])

    def responder(self, texto: str, contexto: Dict[str, Any] | None = None, ejecutar_motor: bool = False) -> Dict[str, Any]:
        contexto = contexto or {}
        self.contexto.update(contexto)
        analisis = self.core.analizador_lenguaje_natural.analizar(texto, self.contexto) if self.core else {}
        for ent in analisis.get('entidades', []):
            if ent.get('tipo') == 'articulo': self.contexto['ultimo_articulo'] = ent.get('normalizado') or ent.get('valor')
            if ent.get('tipo') == 'fecha': self.contexto['ultima_fecha'] = ent.get('normalizado') or ent.get('valor')
        self.contexto['ultima_intencion'] = analisis.get('intencion_detectada')
        resultado_motor: Dict[str, Any] = {}
        # En 3.0.8.2 la conversación interpreta y enruta. La ejecución automática queda controlada
        # por confirmación en módulos posteriores para no modificar datos sin aprobación.
        respuesta = self._respuesta_natural(analisis, resultado_motor)
        turno = TurnoConversacional308(texto or '', analisis.get('intencion_detectada',''), analisis.get('pipeline_sugerido',''), analisis.get('accion_sugerida',''), respuesta, {'analisis': analisis}).to_dict()
        self.historial.append(turno)
        if len(self.historial) > 25: self.historial = self.historial[-25:]
        lectura = 'Motor conversacional activo: mantiene contexto, intención y entidades para la siguiente pregunta.'
        return RespuestaConversacional308(self.VERSION, texto or '', respuesta, analisis.get('intencion_detectada',''), analisis.get('pipeline_sugerido',''), analisis.get('accion_sugerida',''), analisis.get('confianza',0.0), dict(self.contexto), list(self.historial), resultado_motor, False, ['Validar intención antes de ejecutar acciones con impacto operativo.'], lectura).to_dict()

    def historial_conversacion(self) -> Dict[str, Any]:
        return {'version': self.VERSION, 'total_turnos': len(self.historial), 'historial': list(self.historial), 'contexto': dict(self.contexto), 'lectura_host_ai': f'Historial conversacional con {len(self.historial)} turnos.'}

    def exportar_conversacion(self, conversacion: Dict[str, Any] | None = None, nombre: str = '') -> Dict[str, Any]:
        datos = conversacion or self.historial_conversacion()
        salida = Path('DATOS') / (nombre or 'conversacion_host_ai_3082.json')
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'version': self.VERSION, 'ruta': str(salida), 'lectura_host_ai': f'Conversación exportada en {salida}.'}


__all__ = ['MotorConversacional308']
