from __future__ import annotations
from typing import Dict, Any, List
import json

class CierreEscandallosInteligentes:
    """Host AI 3.0.7.8 - Cierre Escandallos Inteligentes.

    Ejecuta y consolida el bloque 3.0.7 completo: análisis, alertas, optimización,
    comparativa histórica, simulación, predicción de rentabilidad y optimización de carta.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.dir = self.base_dir / 'DATOS' / 'escandallos_inteligentes'
        self.dir.mkdir(parents=True, exist_ok=True)

    def comprobar_cierre(
        self,
        escandallos: List[Dict[str, Any]] | None = None,
        historico: List[Dict[str, Any]] | None = None,
        ventas: List[Dict[str, Any]] | None = None,
        objetivos: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        modulos_validados = []
        incidencias = []
        acciones = []
        informe: Dict[str, Any] = {}

        analisis = self._ejecutar('3.0.7.1', 'analisis', lambda: self.core.analizador_inteligente_escandallos.analizar_escandallos(escandallos), modulos_validados, incidencias)
        informe['analisis'] = analisis
        alertas = self._ejecutar('3.0.7.2', 'alertas', lambda: self.core.motor_alertas_escandallos.generar_alertas(analisis=analisis), modulos_validados, incidencias)
        informe['alertas'] = alertas
        optimizacion_recetas = self._ejecutar('3.0.7.3', 'optimizacion_recetas', lambda: self.core.optimizador_inteligente_recetas.optimizar_recetas(analisis=analisis), modulos_validados, incidencias)
        informe['optimizacion_recetas'] = optimizacion_recetas
        comparativa = self._ejecutar('3.0.7.4', 'comparativa_historica', lambda: self.core.comparador_historico_escandallos.comparar_historico(escandallos_anteriores=historico or escandallos or [], escandallos_actuales=escandallos), modulos_validados, incidencias)
        informe['comparativa_historica'] = comparativa
        simulacion = self._ejecutar('3.0.7.5', 'simulacion_costes', lambda: self.core.simulador_costes_escandallos.simular_costes(analisis=analisis), modulos_validados, incidencias)
        informe['simulacion_costes'] = simulacion
        prediccion = self._ejecutar('3.0.7.6', 'prediccion_rentabilidad', lambda: self.core.prediccion_inteligente_rentabilidad.predecir_rentabilidad(analisis=analisis, historico=historico or []), modulos_validados, incidencias)
        informe['prediccion_rentabilidad'] = prediccion
        carta = self._ejecutar('3.0.7.7', 'optimizacion_carta', lambda: self.core.motor_optimizacion_carta.optimizar_carta(analisis=analisis, prediccion=prediccion, ventas=ventas or [], objetivos=objetivos or {}), modulos_validados, incidencias)
        informe['optimizacion_carta'] = carta

        metricas = self._metricas(informe)
        estado = self._estado(metricas, incidencias)
        acciones.extend(self._acciones(metricas, informe, incidencias))
        lectura = (
            f"Cierre Escandallos Inteligentes completado: {len(modulos_validados)}/8 módulos validados, "
            f"{metricas.get('total_escandallos',0)} escandallos y estado {estado}."
        )
        return {
            'version': '3.0.7.8',
            'bloque': 'Escandallos Inteligentes',
            'modulos_validados': modulos_validados,
            'total_escandallos': metricas.get('total_escandallos', 0),
            'estado_general': estado,
            'metricas': metricas,
            'incidencias': incidencias,
            'acciones_recomendadas': acciones,
            'informe_final': informe,
            'lectura_host_ai': lectura,
        }

    def exportar_cierre(self, cierre: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.dir / (nombre or 'cierre_escandallos_inteligentes_3078.json')
        destino.write_text(json.dumps(cierre, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Cierre Escandallos Inteligentes exportado: {destino.name}.'}

    def _ejecutar(self, version: str, nombre: str, fn, modulos: List[str], incidencias: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            datos = fn()
            modulos.append(version)
            return datos
        except Exception as exc:
            incidencias.append({'modulo': version, 'nombre': nombre, 'gravedad': 'critica', 'mensaje': str(exc)})
            return {'version': version, 'error': str(exc), 'resumen': {'estado_general': 'critico'}}

    def _metricas(self, informe: Dict[str, Any]) -> Dict[str, Any]:
        analisis = informe.get('analisis', {}) or {}
        alertas = informe.get('alertas', {}) or {}
        opt = informe.get('optimizacion_recetas', {}) or {}
        sim = informe.get('simulacion_costes', {}) or {}
        pred = informe.get('prediccion_rentabilidad', {}) or {}
        carta = informe.get('optimizacion_carta', {}) or {}
        return {
            'total_escandallos': analisis.get('total_escandallos', 0),
            'beneficio_total_estimado': round(float(analisis.get('beneficio_total_estimado', 0) or 0), 2),
            'margen_medio_pct': round(float(analisis.get('margen_medio_pct', 0) or 0), 2),
            'food_cost_medio_pct': round(float(analisis.get('food_cost_medio_pct', 0) or 0), 2),
            'alertas_totales': alertas.get('total_alertas', 0),
            'alertas_criticas': alertas.get('criticas', 0),
            'optimizaciones_receta': opt.get('total_optimizaciones', 0),
            'simulaciones_costes': sim.get('resumen', {}).get('simulaciones_generadas', 0),
            'predicciones_rentabilidad': pred.get('total_predicciones', 0),
            'platos_estrella': carta.get('platos_estrella', 0),
            'platos_a_potenciar': carta.get('platos_a_potenciar', 0),
            'platos_a_revisar': carta.get('platos_a_revisar', 0),
            'platos_a_retirar': carta.get('platos_a_retirar', 0),
            'estado_analisis': analisis.get('resumen', {}).get('estado_general', 'desconocido'),
            'estado_alertas': alertas.get('resumen', {}).get('estado_general', 'desconocido'),
            'estado_carta': carta.get('resumen', {}).get('estado_general', 'desconocido'),
        }

    def _estado(self, metricas: Dict[str, Any], incidencias: List[Dict[str, Any]]) -> str:
        if incidencias or metricas.get('alertas_criticas', 0) > 0 or metricas.get('platos_a_retirar', 0) > 0:
            return 'critico'
        if metricas.get('platos_a_revisar', 0) > 0 or metricas.get('alertas_totales', 0) > 0:
            return 'revisar'
        return 'ok'

    def _acciones(self, metricas: Dict[str, Any], informe: Dict[str, Any], incidencias: List[Dict[str, Any]]) -> List[str]:
        acciones = []
        if incidencias:
            acciones.append('Corregir incidencias técnicas antes de cerrar el bloque de escandallos.')
        if metricas.get('alertas_criticas', 0) > 0:
            acciones.append('Resolver alertas críticas de escandallos antes de validar la carta.')
        if metricas.get('platos_a_retirar', 0) > 0:
            acciones.append('Retirar o rediseñar platos clasificados como no rentables.')
        if metricas.get('platos_a_potenciar', 0) > 0 or metricas.get('platos_estrella', 0) > 0:
            acciones.append('Construir menús y sugerencias comerciales alrededor de platos estrella o a potenciar.')
        if metricas.get('food_cost_medio_pct', 0) > 35:
            acciones.append('Revisar food cost medio del bloque y renegociar ingredientes principales.')
        return acciones or ['Bloque 3.0.7 validado: mantener seguimiento histórico y preparar IA conversacional.']
