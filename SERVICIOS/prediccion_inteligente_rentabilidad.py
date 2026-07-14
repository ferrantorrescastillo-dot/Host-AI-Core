from __future__ import annotations
from typing import Dict, Any, List
import json

class PrediccionInteligenteRentabilidad:
    """Host AI 3.0.7.6 - Predicción Inteligente de Rentabilidad.

    Predice margen y beneficio esperado conectando escandallo actual, histórico de costes,
    simulaciones, compras y tendencia de precios. Motor propio, sin depender de chatbot.
    """
    def __init__(self, core):
        self.core=core
        self.base_dir=core.base_dir
        self.dir=self.base_dir/'DATOS'/'escandallos_inteligentes'
        self.dir.mkdir(parents=True, exist_ok=True)

    def predecir_rentabilidad(self, escandallos: List[Dict[str, Any]]|None=None, analisis: Dict[str, Any]|None=None, historico: List[Dict[str, Any]]|None=None, horizonte_meses:int=3) -> Dict[str, Any]:
        if analisis is None:
            analisis=self.core.analizador_inteligente_escandallos.analizar_escandallos(escandallos)
        items=analisis.get('escandallos',[]) or []
        historico=historico or []
        predicciones=[]; beneficio_actual_total=0.0; beneficio_previsto_total=0.0; riesgo_alto=0
        for item in items:
            pred=self._predecir_uno(item, historico, horizonte_meses)
            predicciones.append(pred)
            beneficio_actual_total += pred['beneficio_actual_estimado']
            beneficio_previsto_total += pred['beneficio_previsto']
            if pred['riesgo_rentabilidad'] in ('alto','critico'): riesgo_alto += 1
        variacion=beneficio_previsto_total-beneficio_actual_total
        resumen={
            'estado_general':'critico' if any(p['riesgo_rentabilidad']=='critico' for p in predicciones) else ('revisar' if riesgo_alto else 'ok'),
            'total_predicciones':len(predicciones),
            'horizonte_meses':horizonte_meses,
            'beneficio_actual_total':round(beneficio_actual_total,2),
            'beneficio_previsto_total':round(beneficio_previsto_total,2),
            'variacion_beneficio_total':round(variacion,2),
            'recetas_riesgo_alto':riesgo_alto,
        }
        lectura=f"Predicción de rentabilidad: {len(predicciones)} escandallos, variación esperada {round(variacion,2)} € a {horizonte_meses} meses y estado {resumen['estado_general']}."
        return {'version':'3.0.7.6','total_predicciones':len(predicciones),'predicciones':predicciones,'resumen':resumen,'lectura_host_ai':lectura}

    def exportar_prediccion(self, prediccion: Dict[str, Any], nombre: str='') -> Dict[str, Any]:
        destino=self.dir/(nombre or 'prediccion_inteligente_rentabilidad_3076.json')
        destino.write_text(json.dumps(prediccion, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo':str(destino),'lectura_host_ai':f'Predicción inteligente de rentabilidad exportada: {destino.name}.'}

    def _predecir_uno(self, item: Dict[str, Any], historico: List[Dict[str, Any]], horizonte:int) -> Dict[str, Any]:
        nombre=item.get('nombre','Escandallo')
        coste=float(item.get('coste_real_con_merma', item.get('coste_total_estimado',0)) or 0)
        venta=float(item.get('precio_venta',0) or 0)
        beneficio=float(item.get('beneficio_estimado', venta-coste) or 0)
        margen=float(item.get('margen_pct',0) or ((beneficio/venta*100) if venta else 0))
        tendencia_coste=self._tendencia_historica(nombre, historico, 'coste_total')
        tendencia_venta=self._tendencia_historica(nombre, historico, 'precio_venta')
        if tendencia_coste is None:
            # heurística conservadora basada en ingredientes caros y mermas altas
            ingredientes=item.get('ingredientes',[]) or []
            merma_media=sum(float(i.get('merma_pct',0) or 0) for i in ingredientes)/len(ingredientes) if ingredientes else 0
            tendencia_coste=0.02 + min(0.04, merma_media/1000.0)
        if tendencia_venta is None:
            tendencia_venta=0.0
        coste_prev=coste*((1+tendencia_coste)**max(1,horizonte))
        venta_prev=venta*((1+tendencia_venta)**max(1,horizonte))
        beneficio_prev=venta_prev-coste_prev
        margen_prev=round((beneficio_prev/venta_prev)*100,2) if venta_prev else 0.0
        food_prev=round((coste_prev/venta_prev)*100,2) if venta_prev else 0.0
        variacion=beneficio_prev-beneficio
        if venta_prev<=0 or beneficio_prev<0: riesgo='critico'
        elif margen_prev<15 or food_prev>45: riesgo='alto'
        elif margen_prev<25 or variacion<0: riesgo='medio'
        else: riesgo='bajo'
        confianza=self._confianza(nombre, historico)
        acciones=[]
        if riesgo in ('critico','alto'):
            acciones.append('Revisar precio de venta, proveedor principal y gramajes antes de mantener el plato en carta.')
        if tendencia_coste>0.03:
            acciones.append('Bloquear proveedor o buscar alternativa: tendencia de coste elevada.')
        if margen_prev<25:
            acciones.append('Simular subida de precio o rediseño de receta para recuperar margen.')
        if not acciones:
            acciones.append('Mantener seguimiento histórico y revisar en el próximo cierre de escandallos.')
        return {'escandallo':nombre,'horizonte_meses':horizonte,'coste_actual':round(coste,2),'coste_previsto':round(coste_prev,2),'precio_venta_actual':round(venta,2),'precio_venta_previsto':round(venta_prev,2),'beneficio_actual_estimado':round(beneficio,2),'beneficio_previsto':round(beneficio_prev,2),'variacion_beneficio':round(variacion,2),'margen_actual_pct':round(margen,2),'margen_previsto_pct':margen_prev,'food_cost_previsto_pct':food_prev,'tendencia_coste_mensual_pct':round(tendencia_coste*100,2),'tendencia_venta_mensual_pct':round(tendencia_venta*100,2),'nivel_confianza':confianza,'riesgo_rentabilidad':riesgo,'acciones_recomendadas':acciones,'lectura_host_ai':f"{nombre}: beneficio previsto {round(beneficio_prev,2)} €, margen previsto {margen_prev}%, riesgo {riesgo}."}

    def _tendencia_historica(self, nombre:str, historico:List[Dict[str,Any]], campo:str):
        vals=[]
        for h in historico:
            if str(h.get('nombre','')).lower()==nombre.lower() or str(h.get('escandallo','')).lower()==nombre.lower():
                if h.get(campo) is not None:
                    try: vals.append(float(h[campo]))
                    except Exception: pass
        if len(vals)<2 or vals[0]==0: return None
        return (vals[-1]/vals[0])**(1/max(1,len(vals)-1))-1

    def _confianza(self, nombre:str, historico:List[Dict[str,Any]]) -> str:
        n=sum(1 for h in historico if str(h.get('nombre','')).lower()==nombre.lower() or str(h.get('escandallo','')).lower()==nombre.lower())
        if n>=6: return 'alta'
        if n>=3: return 'media'
        return 'baja'
