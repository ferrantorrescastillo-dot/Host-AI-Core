"""Servicio de simulación de costes de escandallos.

Módulo revisado en RC2.5. No altera comportamiento: documenta el contrato
público del servicio y mantiene compatibilidad con los pipelines existentes.
"""

from __future__ import annotations
from typing import Dict, Any, List
import json

class SimuladorCostesEscandallos:
    """Host AI 3.0.7.5 - Simulador de Costes.

    Simula cambios de proveedor, precios de ingredientes, gramajes, mermas y precio de venta
    sobre escandallos reales. La lógica es determinista y propia: la IA solo será la interfaz.
    """
    def __init__(self, core):
        self.core=core
        self.base_dir=core.base_dir
        self.dir=self.base_dir/'DATOS'/'escandallos_inteligentes'
        self.dir.mkdir(parents=True, exist_ok=True)

    def simular_costes(self, escandallos: List[Dict[str, Any]]|None=None, analisis: Dict[str, Any]|None=None, escenarios: List[Dict[str, Any]]|None=None) -> Dict[str, Any]:
        if analisis is None:
            analisis=self.core.analizador_inteligente_escandallos.analizar_escandallos(escandallos)
        base_items=analisis.get('escandallos', []) or []
        escenarios=escenarios or self._escenarios_base()
        simulaciones=[]
        impacto_total=0.0; mejoras=0; empeoran=0; criticos=0
        for item in base_items:
            for escenario in escenarios:
                sim=self._simular_uno(item, escenario)
                simulaciones.append(sim)
                impacto_total += sim['impacto_beneficio_total']
                if sim['impacto_beneficio_total'] > 0: mejoras += 1
                if sim['impacto_beneficio_total'] < 0: empeoran += 1
                if sim['riesgo']=='critico': criticos += 1
        resumen={
            'estado_general':'critico' if criticos else ('revisar' if empeoran else 'ok'),
            'escandallos_analizados':len(base_items),
            'escenarios_aplicados':len(escenarios),
            'simulaciones_generadas':len(simulaciones),
            'impacto_total_beneficio':round(impacto_total,2),
            'simulaciones_mejoran':mejoras,
            'simulaciones_empeoran':empeoran,
            'simulaciones_criticas':criticos,
        }
        lectura=f"Simulación de costes completada: {len(simulaciones)} escenarios evaluados, impacto total estimado {round(impacto_total,2)} € y estado {resumen['estado_general']}."
        return {'version':'3.0.7.5','total_escandallos':len(base_items),'total_escenarios':len(escenarios),'simulaciones':simulaciones,'resumen':resumen,'lectura_host_ai':lectura}

    def exportar_simulacion(self, simulacion: Dict[str, Any], nombre: str='') -> Dict[str, Any]:
        destino=self.dir/(nombre or 'simulacion_costes_escandallos_3075.json')
        destino.write_text(json.dumps(simulacion, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo':str(destino),'lectura_host_ai':f'Simulación de costes exportada: {destino.name}.'}

    def _escenarios_base(self) -> List[Dict[str, Any]]:
        return [
            {'nombre':'subida_ingredientes_10','tipo':'precio_ingredientes_pct','valor_pct':10,'detalle':'Subida general del 10% en ingredientes.'},
            {'nombre':'bajada_ingredientes_5','tipo':'precio_ingredientes_pct','valor_pct':-5,'detalle':'Mejora de compra o proveedor con -5% en ingredientes.'},
            {'nombre':'subida_precio_venta_5','tipo':'precio_venta_pct','valor_pct':5,'detalle':'Subida comercial del precio de venta en 5%.'},
            {'nombre':'reduccion_merma_20','tipo':'merma_pct_relativa','valor_pct':-20,'detalle':'Reducción relativa del 20% sobre mermas actuales.'},
        ]

    def _simular_uno(self, item: Dict[str, Any], escenario: Dict[str, Any]) -> Dict[str, Any]:
        nombre=item.get('nombre','Escandallo')
        raciones=float(item.get('raciones',1) or 1)
        coste_base=float(item.get('coste_real_con_merma', item.get('coste_total_estimado',0)) or 0)
        venta_base=float(item.get('precio_venta',0) or item.get('venta_total',0) or 0)
        beneficio_base=float(item.get('beneficio_estimado', venta_base-coste_base) or 0)
        ingredientes=item.get('ingredientes',[]) or []
        coste_sim=coste_base; venta_sim=venta_base; cambios=[]
        tipo=escenario.get('tipo','precio_ingredientes_pct'); val=float(escenario.get('valor_pct',0) or 0)
        if tipo=='precio_ingredientes_pct':
            factor=1+(val/100.0)
            coste_sim=0.0
            for ing in ingredientes:
                c=float(ing.get('coste_real_con_merma', ing.get('coste',0)) or 0)
                nuevo=c*factor
                coste_sim += nuevo
                cambios.append({'ingrediente':ing.get('nombre','ingrediente'),'coste_base':round(c,2),'coste_simulado':round(nuevo,2)})
            if coste_sim <= 0: coste_sim=coste_base*factor
        elif tipo=='precio_venta_pct':
            venta_sim=venta_base*(1+(val/100.0))
        elif tipo=='merma_pct_relativa':
            # aproxima impacto reduciendo solo la parte de merma dentro del coste real
            ahorro=0.0
            for ing in ingredientes:
                c=float(ing.get('coste_real_con_merma', ing.get('coste',0)) or 0)
                merma=float(ing.get('merma_pct',0) or 0)
                if merma>0:
                    ahorro += c*(merma/100.0)*abs(val/100.0)
            coste_sim=max(0.0, coste_base-ahorro)
        elif tipo=='gramaje_pct':
            coste_sim=coste_base*(1+(val/100.0))
        beneficio_sim=venta_sim-coste_sim
        margen_sim=round((beneficio_sim/venta_sim)*100,2) if venta_sim else 0.0
        food_sim=round((coste_sim/venta_sim)*100,2) if venta_sim else 0.0
        impacto=beneficio_sim-beneficio_base
        if venta_sim<=0 or margen_sim<0: riesgo='critico'
        elif margen_sim<20 or food_sim>40: riesgo='aviso'
        else: riesgo='informativo'
        decision='potenciar' if impacto>0 and riesgo!='critico' else ('evitar' if riesgo=='critico' or impacto<0 else 'neutral')
        return {'escandallo':nombre,'escenario':escenario.get('nombre','escenario'),'tipo_escenario':tipo,'coste_base':round(coste_base,2),'coste_simulado':round(coste_sim,2),'venta_base':round(venta_base,2),'venta_simulada':round(venta_sim,2),'beneficio_base':round(beneficio_base,2),'beneficio_simulado':round(beneficio_sim,2),'impacto_beneficio_total':round(impacto,2),'impacto_beneficio_por_racion':round(impacto/raciones,2) if raciones else round(impacto,2),'margen_simulado_pct':margen_sim,'food_cost_simulado_pct':food_sim,'riesgo':riesgo,'decision_recomendada':decision,'cambios_ingredientes':cambios[:10],'lectura_host_ai':f"{nombre} / {escenario.get('nombre','escenario')}: impacto {round(impacto,2)} €, riesgo {riesgo}, decisión {decision}."}


__all__ = ["SimuladorCostesEscandallos"]
