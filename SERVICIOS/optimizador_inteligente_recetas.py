from __future__ import annotations
from typing import Dict, Any, List, Tuple
from pathlib import Path
import json

class OptimizadorInteligenteRecetas:
    """Host AI 3.0.7.3 - Optimizador Inteligente de Recetas.

    Optimiza recetas/escandallos desde lógica propia: sustituciones, reducción de coste,
    mejora de margen, reducción de mermas y ajuste de cantidades. La IA queda como interfaz.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.dir = self.base_dir / 'DATOS' / 'escandallos_inteligentes'
        self.dir.mkdir(parents=True, exist_ok=True)

    def optimizar_recetas(self, escandallos: List[Dict[str, Any]] | None = None, analisis: Dict[str, Any] | None = None,
                          objetivo_food_cost_pct: float = 30.0, margen_minimo_pct: float = 25.0) -> Dict[str, Any]:
        if analisis is None:
            analisis = self.core.analizador_inteligente_escandallos.analizar_escandallos(escandallos)
        items = analisis.get('escandallos', [])
        optimizaciones=[]; ahorro_total=0.0; margen_mejorado=0
        for item in items:
            opt=self._optimizar_uno(item, objetivo_food_cost_pct, margen_minimo_pct)
            optimizaciones.append(opt)
            ahorro_total += opt['ahorro_estimado']
            if opt['mejora_margen_pct_estimada'] > 0: margen_mejorado += 1
        criticas=sum(1 for o in optimizaciones if o['prioridad']=='critica')
        avisos=sum(1 for o in optimizaciones if o['prioridad']=='aviso')
        resumen={
            'estado_general': 'critico' if criticas else ('revisar' if avisos else 'ok'),
            'recetas_optimizadas': len(optimizaciones),
            'ahorro_total_estimado': round(ahorro_total,2),
            'recetas_con_mejora_margen': margen_mejorado,
            'acciones_criticas': criticas,
            'acciones_aviso': avisos,
            'objetivo_food_cost_pct': objetivo_food_cost_pct,
            'margen_minimo_pct': margen_minimo_pct,
        }
        lectura=f"Optimización inteligente de recetas: {len(optimizaciones)} escandallos revisados, ahorro estimado {round(ahorro_total,2)} € y estado {resumen['estado_general']}."
        return {'version':'3.0.7.3','total_optimizaciones':len(optimizaciones),'ahorro_total_estimado':round(ahorro_total,2),'optimizaciones':optimizaciones,'resumen':resumen,'lectura_host_ai':lectura}

    def exportar_optimizacion(self, optimizacion: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino=self.dir/(nombre or 'optimizacion_inteligente_recetas_3073.json')
        destino.write_text(json.dumps(optimizacion, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo':str(destino),'lectura_host_ai':f'Optimización inteligente de recetas exportada: {destino.name}.'}

    def _optimizar_uno(self, item: Dict[str, Any], objetivo_food: float, margen_min: float) -> Dict[str, Any]:
        nombre=item.get('nombre','Escandallo')
        food=float(item.get('food_cost_pct',0) or 0)
        margen=float(item.get('margen_pct',0) or 0)
        coste=float(item.get('coste_real_con_merma', item.get('coste_total_estimado',0)) or 0)
        venta=float(item.get('precio_venta',0) or 0)
        ingredientes=item.get('ingredientes',[]) or []
        acciones=[]; sustituciones=[]; ajustes=[]; reduccion_mermas=[]; incidencias=[]
        ahorro=0.0; impacto=0.0
        # ingredientes con más peso económico
        caros=sorted(ingredientes, key=lambda x: float(x.get('coste_real_con_merma', x.get('coste',0)) or 0), reverse=True)
        for ing in caros[:3]:
            c=float(ing.get('coste_real_con_merma', ing.get('coste',0)) or 0)
            merma=float(ing.get('merma_pct',0) or 0)
            nombre_ing=ing.get('nombre','ingrediente')
            if c > max(2.0, coste*0.25):
                ahorro_ing=round(c*0.08,2)
                ahorro += ahorro_ing
                sustituciones.append({'ingrediente':nombre_ing,'tipo':'buscar_proveedor_o_formato_alternativo','ahorro_estimado':ahorro_ing,'detalle':'Ingrediente con peso alto en el coste total; comparar formato, proveedor o gramaje.'})
            if merma > 12:
                ahorro_merma=round(c*min(0.12, merma/100.0*0.45),2)
                ahorro += ahorro_merma
                reduccion_mermas.append({'ingrediente':nombre_ing,'merma_pct':merma,'ahorro_estimado':ahorro_merma,'detalle':'Revisar limpieza, porcionado, rendimiento real y aprovechamiento de recortes.'})
            if 'sin_precio' in ing.get('incidencias',[]):
                incidencias.append(f'{nombre_ing}: sin precio actualizado')
        if food > objetivo_food:
            exceso=food-objetivo_food
            acciones.append({'tipo':'reducir_food_cost','prioridad':'alta','detalle':f'Food cost {food}% por encima del objetivo {objetivo_food}%.','accion':'Revisar gramajes, proveedor principal y precio de venta.'})
            ahorro += round(coste*min(0.15, exceso/100.0),2)
        if margen < margen_min:
            acciones.append({'tipo':'mejorar_margen','prioridad':'alta','detalle':f'Margen {margen}% inferior al mínimo {margen_min}%.','accion':'Subir precio, rediseñar guarnición o reducir coste de ingredientes dominantes.'})
        if venta > 0 and margen < margen_min:
            precio_recomendado=round((coste/(1-(margen_min/100.0))),2) if margen_min < 100 else venta
            ajustes.append({'tipo':'precio_venta','precio_actual':venta,'precio_recomendado':precio_recomendado,'detalle':'Precio recomendado para alcanzar margen mínimo objetivo, sin cambiar receta.'})
        if not acciones and not sustituciones and not reduccion_mermas:
            acciones.append({'tipo':'mantener','prioridad':'informativa','detalle':'Receta estable y rentable con los parámetros actuales.','accion':'Mantener seguimiento histórico.'})
        mejora_pct=round((ahorro/venta)*100,2) if venta else 0.0
        if incidencias:
            prioridad='critica'
        elif food > objetivo_food or margen < margen_min:
            prioridad='aviso'
        else:
            prioridad='informativa'
        return {'escandallo':nombre,'prioridad':prioridad,'food_cost_pct_actual':food,'margen_pct_actual':margen,'ahorro_estimado':round(ahorro,2),'mejora_margen_pct_estimada':mejora_pct,'acciones':acciones,'sustituciones':sustituciones,'ajustes':ajustes,'reduccion_mermas':reduccion_mermas,'incidencias':incidencias,'lectura_host_ai':f"{nombre}: prioridad {prioridad}, ahorro estimado {round(ahorro,2)} €."}
