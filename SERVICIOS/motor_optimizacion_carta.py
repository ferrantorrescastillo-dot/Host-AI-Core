"""Servicio de optimización inteligente de carta para Host AI RC1.

Este módulo pertenece al bloque 3.0.7 Escandallos Inteligentes.
La revisión RC2 mantiene la lógica existente y deja explícito el servicio
principal exportado por el módulo.
"""
from __future__ import annotations
from typing import Dict, Any, List
import json

__all__ = ["MotorOptimizacionCarta"]


class MotorOptimizacionCarta:
    """Host AI 3.0.7.7 - Motor Inteligente de Optimización de Carta.

    Analiza los escandallos como una carta completa y recomienda qué platos potenciar,
    revisar, rediseñar o retirar. Conecta coste, margen, riesgo, rentabilidad prevista,
    histórico, ventas y complejidad de producción. Motor determinista propio: la IA será
    únicamente la interfaz conversacional.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.dir = self.base_dir / 'DATOS' / 'escandallos_inteligentes'
        self.dir.mkdir(parents=True, exist_ok=True)

    def optimizar_carta(
        self,
        escandallos: List[Dict[str, Any]] | None = None,
        analisis: Dict[str, Any] | None = None,
        prediccion: Dict[str, Any] | None = None,
        ventas: List[Dict[str, Any]] | None = None,
        objetivos: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        objetivos = objetivos or {}
        margen_objetivo = float(objetivos.get('margen_objetivo_pct', 65) or 65)
        food_cost_max = float(objetivos.get('food_cost_max_pct', 35) or 35)

        if analisis is None:
            analisis = self.core.analizador_inteligente_escandallos.analizar_escandallos(escandallos)
        if prediccion is None:
            try:
                prediccion = self.core.prediccion_inteligente_rentabilidad.predecir_rentabilidad(analisis=analisis)
            except Exception:
                prediccion = {'predicciones': []}

        items = analisis.get('escandallos', []) or []
        ventas_index = self._indexar_ventas(ventas or [])
        pred_index = {str(p.get('escandallo', '')).lower(): p for p in prediccion.get('predicciones', []) or []}

        optimizaciones = []
        recomendaciones_carta = []
        contadores = {'estrella': 0, 'potenciar': 0, 'revisar': 0, 'retirar': 0}
        beneficio_total = 0.0
        beneficio_previsto_total = 0.0

        for item in items:
            opt = self._optimizar_plato(item, ventas_index, pred_index, margen_objetivo, food_cost_max)
            optimizaciones.append(opt)
            contadores[opt['clasificacion']] = contadores.get(opt['clasificacion'], 0) + 1
            beneficio_total += float(opt.get('beneficio_actual_estimado', 0) or 0)
            beneficio_previsto_total += float(opt.get('beneficio_previsto_estimado', opt.get('beneficio_actual_estimado', 0)) or 0)

        recomendaciones_carta.extend(self._recomendaciones_globales(optimizaciones, margen_objetivo, food_cost_max))
        estado = 'critico' if contadores.get('retirar', 0) else ('revisar' if contadores.get('revisar', 0) else 'ok')
        resumen = {
            'estado_general': estado,
            'total_platos': len(optimizaciones),
            'platos_estrella': contadores.get('estrella', 0),
            'platos_a_potenciar': contadores.get('potenciar', 0),
            'platos_a_revisar': contadores.get('revisar', 0),
            'platos_a_retirar': contadores.get('retirar', 0),
            'beneficio_actual_estimado_total': round(beneficio_total, 2),
            'beneficio_previsto_estimado_total': round(beneficio_previsto_total, 2),
            'impacto_previsto_total': round(beneficio_previsto_total - beneficio_total, 2),
            'margen_objetivo_pct': margen_objetivo,
            'food_cost_max_pct': food_cost_max,
        }
        lectura = (
            f"Optimización de carta completada: {len(optimizaciones)} platos analizados, "
            f"{contadores.get('estrella',0)} estrella, {contadores.get('potenciar',0)} a potenciar, "
            f"{contadores.get('revisar',0)} a revisar y {contadores.get('retirar',0)} a retirar."
        )
        return {
            'version': '3.0.7.7',
            'total_platos': len(optimizaciones),
            'platos_estrella': contadores.get('estrella', 0),
            'platos_a_potenciar': contadores.get('potenciar', 0),
            'platos_a_revisar': contadores.get('revisar', 0),
            'platos_a_retirar': contadores.get('retirar', 0),
            'optimizaciones': optimizaciones,
            'recomendaciones_carta': recomendaciones_carta,
            'resumen': resumen,
            'lectura_host_ai': lectura,
        }

    def exportar_optimizacion(self, optimizacion: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.dir / (nombre or 'optimizacion_carta_3077.json')
        destino.write_text(json.dumps(optimizacion, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Optimización inteligente de carta exportada: {destino.name}.'}

    def _indexar_ventas(self, ventas: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        idx = {}
        for v in ventas:
            nombre = str(v.get('nombre', v.get('escandallo', v.get('plato', '')))).lower()
            if nombre:
                idx[nombre] = v
        return idx

    def _optimizar_plato(self, item: Dict[str, Any], ventas_index: Dict[str, Dict[str, Any]], pred_index: Dict[str, Dict[str, Any]], margen_objetivo: float, food_cost_max: float) -> Dict[str, Any]:
        nombre = item.get('nombre', 'Escandallo')
        clave = str(nombre).lower()
        venta = float(item.get('precio_venta', 0) or item.get('venta_total', 0) or 0)
        coste = float(item.get('coste_total_estimado', item.get('coste_real_con_merma', 0)) or 0)
        beneficio = float(item.get('beneficio_estimado', venta - coste) or 0)
        margen = float(item.get('margen_pct', ((beneficio / venta) * 100 if venta else 0)) or 0)
        food = float(item.get('food_cost_pct', ((coste / venta) * 100 if venta else 0)) or 0)
        rentabilidad = item.get('rentabilidad', '')
        incidencias = item.get('incidencias', []) or []
        tiempo = int(item.get('tiempo_activo_min', 0) or 0) + int(item.get('tiempo_pasivo_min', 0) or 0)
        pred = pred_index.get(clave, {})
        venta_hist = ventas_index.get(clave, {})
        unidades = float(venta_hist.get('unidades_vendidas', venta_hist.get('ventas', 0)) or 0)
        popularidad = self._popularidad(unidades)
        beneficio_previsto = float(pred.get('beneficio_previsto', beneficio) or beneficio)
        margen_previsto = float(pred.get('margen_previsto_pct', margen) or margen)
        riesgo_pred = pred.get('riesgo_rentabilidad', 'bajo')

        puntuacion = 0
        motivos = []
        if margen >= margen_objetivo:
            puntuacion += 3; motivos.append('Margen por encima del objetivo.')
        elif margen >= margen_objetivo - 10:
            puntuacion += 1; motivos.append('Margen cercano al objetivo.')
        else:
            puntuacion -= 2; motivos.append('Margen por debajo del objetivo.')
        if food <= food_cost_max:
            puntuacion += 2; motivos.append('Food cost controlado.')
        else:
            puntuacion -= 2; motivos.append('Food cost por encima del máximo recomendado.')
        if beneficio_previsto >= beneficio:
            puntuacion += 1; motivos.append('Rentabilidad prevista estable o positiva.')
        else:
            puntuacion -= 1; motivos.append('Rentabilidad prevista negativa.')
        if popularidad == 'alta': puntuacion += 2; motivos.append('Alta demanda histórica.')
        elif popularidad == 'baja': puntuacion -= 1; motivos.append('Baja demanda histórica.')
        if tiempo > 240: puntuacion -= 1; motivos.append('Alta carga productiva.')
        if incidencias: puntuacion -= min(3, len(incidencias)); motivos.append('Tiene incidencias técnicas en escandallo.')
        if riesgo_pred in ('alto', 'critico'):
            puntuacion -= 2; motivos.append('Riesgo de rentabilidad futura elevado.')
        if venta <= 0 or beneficio < 0:
            puntuacion -= 5; motivos.append('Precio de venta ausente o beneficio negativo.')

        if puntuacion >= 6:
            clasificacion = 'estrella'
            decision = 'Mantener visible en carta y usar como plato tractor.'
        elif puntuacion >= 3:
            clasificacion = 'potenciar'
            decision = 'Potenciar en menús, sugerencias y ventas dirigidas.'
        elif puntuacion >= 0:
            clasificacion = 'revisar'
            decision = 'Revisar precio, gramajes, proveedor o método de producción.'
        else:
            clasificacion = 'retirar'
            decision = 'Retirar temporalmente o rediseñar antes de seguir vendiendo.'

        acciones = self._acciones_plato(clasificacion, margen, food, margen_objetivo, food_cost_max, incidencias, tiempo)
        return {
            'plato': nombre,
            'clasificacion': clasificacion,
            'puntuacion': puntuacion,
            'decision_recomendada': decision,
            'precio_venta': round(venta, 2),
            'coste_total_estimado': round(coste, 2),
            'beneficio_actual_estimado': round(beneficio, 2),
            'beneficio_previsto_estimado': round(beneficio_previsto, 2),
            'margen_actual_pct': round(margen, 2),
            'margen_previsto_pct': round(margen_previsto, 2),
            'food_cost_pct': round(food, 2),
            'popularidad': popularidad,
            'unidades_vendidas': unidades,
            'tiempo_total_min': tiempo,
            'riesgo_rentabilidad': riesgo_pred,
            'motivos': motivos,
            'acciones_recomendadas': acciones,
            'lectura_host_ai': f"{nombre}: {clasificacion}, puntuación {puntuacion}, margen {round(margen,2)}%."
        }

    def _popularidad(self, unidades: float) -> str:
        if unidades >= 80: return 'alta'
        if unidades >= 25: return 'media'
        if unidades > 0: return 'baja'
        return 'sin_datos'

    def _acciones_plato(self, clasificacion: str, margen: float, food: float, margen_obj: float, food_max: float, incidencias: List[str], tiempo: int) -> List[str]:
        acciones = []
        if margen < margen_obj:
            acciones.append('Simular subida de precio o reducción de coste para acercar el margen al objetivo.')
        if food > food_max:
            acciones.append('Revisar ingredientes principales y proveedores: food cost por encima del límite.')
        if incidencias:
            acciones.append('Completar o corregir el escandallo antes de tomar decisiones comerciales.')
        if tiempo > 240:
            acciones.append('Revisar mise en place y producción anticipada para reducir carga operativa.')
        if clasificacion in ('estrella', 'potenciar'):
            acciones.append('Dar visibilidad en carta, menús cerrados y recomendaciones de sala.')
        if clasificacion == 'retirar':
            acciones.append('Rediseñar receta o retirar temporalmente hasta recuperar rentabilidad.')
        return acciones or ['Mantener seguimiento en cierre mensual de escandallos.']

    def _recomendaciones_globales(self, opts: List[Dict[str, Any]], margen_obj: float, food_max: float) -> List[Dict[str, Any]]:
        recs = []
        estrellas = [o for o in opts if o['clasificacion'] == 'estrella']
        retirar = [o for o in opts if o['clasificacion'] == 'retirar']
        revisar = [o for o in opts if o['clasificacion'] == 'revisar']
        if estrellas:
            recs.append({'tipo': 'potenciacion', 'prioridad': 'alta', 'mensaje': f"Potenciar {len(estrellas)} platos estrella como base de carta y menús.", 'platos': [o['plato'] for o in estrellas[:8]]})
        if retirar:
            recs.append({'tipo': 'retirada_redisenyo', 'prioridad': 'critica', 'mensaje': f"Revisar o retirar {len(retirar)} platos con mala rentabilidad o riesgo.", 'platos': [o['plato'] for o in retirar[:8]]})
        if revisar:
            recs.append({'tipo': 'ajuste_coste', 'prioridad': 'media', 'mensaje': f"Ajustar {len(revisar)} platos con margen o food cost mejorable.", 'platos': [o['plato'] for o in revisar[:8]]})
        media_margen = sum(float(o.get('margen_actual_pct', 0) or 0) for o in opts) / len(opts) if opts else 0
        if media_margen < margen_obj:
            recs.append({'tipo': 'estrategia_carta', 'prioridad': 'alta', 'mensaje': f"La carta queda por debajo del margen objetivo ({round(media_margen,2)}% vs {margen_obj}%).", 'accion': 'Subir precios selectivamente y renegociar ingredientes de alto impacto.'})
        return recs
