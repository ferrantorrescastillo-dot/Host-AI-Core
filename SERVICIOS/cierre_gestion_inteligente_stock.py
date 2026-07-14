from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.cierre_gestion_stock import InformeCierreGestionStock

class CierreGestionInteligenteStock:
    """Host AI 3.0.5.8 - Cierre Gestión Inteligente del Stock.

    Ejecuta el bloque 3.0.5 como un único sistema y genera un informe ejecutivo final.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.stock_dir = self.base_dir / 'DATOS' / 'stock'
        self.stock_dir.mkdir(parents=True, exist_ok=True)

    def generar_cierre(self, horizonte_dias: int = 14) -> Dict[str, Any]:
        modulos=[]; incidencias=[]; acciones=[]; metricas={}
        def ejecutar(nombre, fn):
            try:
                dato = fn(); modulos.append(nombre); return dato
            except Exception as exc:
                incidencias.append({'modulo': nombre, 'gravedad':'critica', 'mensaje': str(exc)}); return {}
        analisis = ejecutar('3.0.5.1 Analizador Inteligente de Stock', lambda: self.core.analizador_inteligente_stock.analizar_stock())
        alertas = ejecutar('3.0.5.2 Motor de Alertas de Stock', lambda: self.core.motor_alertas_stock.generar_alertas())
        control = ejecutar('3.0.5.3 Control Entradas y Salidas', lambda: self.core.control_inteligente_movimientos_stock.analizar_movimientos())
        reconciliacion = ejecutar('3.0.5.4 Reconciliador Inteligente de Stock', lambda: self.core.reconciliador_inteligente_stock.reconciliar_stock())
        prediccion = ejecutar('3.0.5.5 Predicción Necesidades Stock', lambda: self.core.prediccion_necesidades_stock.predecir_necesidades(horizonte_dias=horizonte_dias))
        optimizacion = ejecutar('3.0.5.6 Optimizador de Stock', lambda: self.core.optimizador_stock.optimizar_stock(horizonte_dias=horizonte_dias))
        ubicaciones = ejecutar('3.0.5.7 Stock por Ubicaciones', lambda: self.core.stock_por_ubicaciones.analizar_ubicaciones())

        metricas = {
            'total_articulos': analisis.get('total_articulos', 0),
            'total_lotes': analisis.get('total_lotes', 0),
            'valor_total_estimado': analisis.get('valor_total_estimado', 0),
            'alertas_stock': alertas.get('total_alertas', alertas.get('total_avisos', 0)),
            'movimientos_analizados': control.get('total_movimientos', 0),
            'descuadres': reconciliacion.get('total_diferencias', reconciliacion.get('diferencias_detectadas', 0)),
            'necesidades_previstas': prediccion.get('total_necesidades', prediccion.get('total_items', 0)),
            'acciones_optimizacion': optimizacion.get('total_recomendaciones', 0),
            'ubicaciones': ubicaciones.get('total_ubicaciones', 0),
            'lotes_sin_ubicacion': len(ubicaciones.get('sin_ubicacion', []) or []),
        }
        for a in alertas.get('alertas', []) or alertas.get('avisos', []) or []:
            if a.get('gravedad') == 'critica' or a.get('nivel') == 'alto': incidencias.append({'modulo':'alertas_stock','gravedad':'critica','mensaje':a.get('mensaje','Alerta crítica de stock.'), 'datos':a})
        for u in ubicaciones.get('alertas', []) or []: incidencias.append({'modulo':'stock_por_ubicaciones','gravedad':u.get('gravedad','aviso'), 'mensaje':u.get('mensaje','Revisar ubicación.'), 'datos':u})
        acciones.extend(optimizacion.get('acciones', [])[:20])
        if metricas['lotes_sin_ubicacion']:
            acciones.append({'tipo':'ubicaciones','prioridad':'aviso','accion':'asignar_ubicaciones','motivo':'Hay lotes sin ubicación operativa.'})
        estado = 'critico' if any(i.get('gravedad')=='critica' for i in incidencias) else ('revisar' if incidencias or acciones else 'ok')
        ejecutivo = self._informe_ejecutivo(metricas, incidencias, acciones, estado)
        lectura = f"Cierre Gestión Inteligente del Stock 3.0.5: estado {estado}, {len(modulos)} módulos validados, {len(incidencias)} incidencias y {len(acciones)} acciones."
        return InformeCierreGestionStock('3.0.5', estado, modulos, metricas, incidencias, acciones, ejecutivo, lectura).to_dict()

    def exportar_cierre(self, cierre: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.stock_dir / (nombre or 'cierre_gestion_inteligente_stock_305.json')
        destino.write_text(json.dumps(cierre, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Cierre de Gestión Inteligente del Stock exportado: {destino.name}.'}

    def _informe_ejecutivo(self, m: Dict[str, Any], incidencias: List[Dict[str, Any]], acciones: List[Dict[str, Any]], estado: str) -> str:
        return '\n'.join([
            'HOST AI 3.0.5 - CIERRE GESTIÓN INTELIGENTE DEL STOCK',
            f'Estado general: {estado}',
            f"Artículos: {m.get('total_articulos',0)} | Lotes: {m.get('total_lotes',0)} | Valor estimado: {m.get('valor_total_estimado',0)} €",
            f"Alertas: {m.get('alertas_stock',0)} | Descuadres: {m.get('descuadres',0)} | Ubicaciones: {m.get('ubicaciones',0)}",
            f'Incidencias detectadas: {len(incidencias)}',
            f'Acciones recomendadas: {len(acciones)}',
        ])
