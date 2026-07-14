"""
Host AI - Servicio: Analizador de Lenguaje Natural 3.0.8.1.

Servicio de la capa IA Conversacional. Mantiene la lógica de negocio
separada de pipelines y modelos. Este archivo forma parte del proceso de
estabilización RC2 y no modifica el comportamiento funcional del sistema.
"""
from __future__ import annotations
import json, re, unicodedata
from pathlib import Path
from typing import Dict, Any, List, Tuple
from MODELOS.ia_conversacional_308 import AnalisisLenguajeNatural308, EntidadConversacional308

class AnalizadorLenguajeNatural:
    VERSION = '3.0.8.1'

    def __init__(self, core=None):
        self.core = core

    def _normalizar(self, texto: str) -> str:
        t = (texto or '').strip().lower()
        t = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
        t = re.sub(r'\s+', ' ', t)
        return t

    def _extraer_entidades(self, texto_norm: str) -> List[Dict[str, Any]]:
        entidades: List[EntidadConversacional308] = []
        unidades = re.findall(r'(\d+(?:[\.,]\d+)?)\s*(kg|kilos|g|gr|l|litros|uds|unidades|raciones)', texto_norm)
        for num, unidad in unidades:
            entidades.append(EntidadConversacional308('cantidad', f'{num} {unidad}', num.replace(',', '.') + ' ' + unidad, 0.92))
        for fecha in ['hoy','mañana','manana','ayer','esta semana','semana que viene','proxima semana']:
            if fecha in texto_norm:
                entidades.append(EntidadConversacional308('fecha', fecha, 'mañana' if fecha=='manana' else fecha, 0.9))
        articulos = ['aceite','arroz','gamba','carne','pollo','merluza','bacalao','tomate','harina','leche','huevo','caldo','sepia','patata','cebolla']
        for art in articulos:
            if re.search(rf'\b{re.escape(art)}\b', texto_norm):
                entidades.append(EntidadConversacional308('articulo', art, art, 0.82))
        proveedores = re.findall(r'proveedor(?:es)?\s+([a-z0-9 _\-]+)', texto_norm)
        for p in proveedores:
            valor = p.strip()[:40]
            if valor:
                entidades.append(EntidadConversacional308('proveedor', valor, valor, 0.72))
        return [e.to_dict() for e in entidades]

    def _detectar_intencion(self, texto_norm: str) -> Tuple[str, str, str, float, List[str]]:
        reglas = [
            (['comprar','pedido','pido','compra','proveedor','precio mejor'], 'consulta_compras', 'motor_inteligente_pedidos', 'generar', 0.88),
            (['stock','queda','tengo','rotura','faltara','faltará'], 'consulta_stock', 'analizador_inteligente_stock', 'analizar', 0.86),
            (['produccion','producción','elaborar','cocinar','preparar','partida'], 'consulta_produccion', 'planificador_inteligente_produccion', 'planificar', 0.86),
            (['escandallo','receta','margen','rentabilidad','coste','food cost','carta'], 'consulta_escandallos', 'analizador_inteligente_escandallos', 'analizar', 0.86),
            (['anomalia','anomalía','raro','error','duplicada','sospechosa'], 'consulta_anomalias', 'detector_anomalias_compras', 'detectar', 0.84),
            (['alerta','avisame','avísame','problema','critico','crítico'], 'consulta_alertas', 'motor_alertas_stock', 'generar', 0.80),
        ]
        for palabras, intencion, pipeline, accion, confianza in reglas:
            if any(p in texto_norm for p in palabras):
                return intencion, pipeline, accion, confianza, []
        return 'conversacion_general', 'motor_conversacional', 'responder', 0.45, ['No se ha detectado una intención operativa clara.']

    def analizar(self, texto: str, contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
        contexto = contexto or {}
        texto_norm = self._normalizar(texto)
        entidades = self._extraer_entidades(texto_norm)
        intencion, pipeline, accion, confianza, aclaraciones = self._detectar_intencion(texto_norm)
        requiere_aclaracion = confianza < 0.55
        solicitud = {
            'pipeline': pipeline,
            'accion': accion,
            'parametros': {
                'texto': texto,
                'texto_normalizado': texto_norm,
                'entidades': entidades,
                'contexto': contexto,
            }
        }
        lectura = f"Host AI ha interpretado la consulta como {intencion} y sugiere ejecutar {pipeline}.{accion}."
        return AnalisisLenguajeNatural308(self.VERSION, texto or '', texto_norm, intencion, pipeline, accion, confianza, entidades, contexto, requiere_aclaracion, aclaraciones, solicitud, lectura).to_dict()

    def exportar_analisis(self, analisis: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        salida = Path('DATOS') / (nombre or 'analisis_lenguaje_natural_3081.json')
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(json.dumps(analisis, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'version': self.VERSION, 'ruta': str(salida), 'lectura_host_ai': f'Análisis de lenguaje natural exportado en {salida}.'}


__all__ = ['AnalizadorLenguajeNatural']
