from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json
from MODELOS.escandallos_inteligentes_307 import IngredienteEscandallo307, AnalisisEscandallo307, InformeAnalisisEscandallos307

class AnalizadorInteligenteEscandallos:
    """Host AI 3.0.7.1 - Analizador Inteligente de Escandallos.

    Analiza costes, raciones, mermas, tiempos, margen, rentabilidad y costes ocultos de recetas/escandallos.
    La IA queda como interfaz: toda la lógica se ejecuta aquí mediante servicio propio y pipeline registrado.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.dir = self.base_dir / 'DATOS' / 'escandallos_inteligentes'
        self.dir.mkdir(parents=True, exist_ok=True)

    def analizar_escandallos(self, escandallos: List[Dict[str, Any]] | None = None, coste_hora_cocinero: float = 18.0, pct_costes_ocultos: float = 4.0) -> Dict[str, Any]:
        datos = escandallos if escandallos is not None else self._cargar_escandallos_base()
        analizados=[]; coste_total=0.0; venta_total=0.0; beneficio_total=0.0
        recetas_con_perdida=0; recetas_incompletas=0; ingredientes_sin_precio=0
        margenes=[]; foodcosts=[]
        for idx, raw in enumerate(datos or []):
            analisis = self._analizar_uno(raw, idx, coste_hora_cocinero, pct_costes_ocultos)
            d=analisis.to_dict(); analizados.append(d)
            coste_total += analisis.coste_total_estimado
            venta_total += analisis.precio_venta
            beneficio_total += analisis.beneficio_estimado
            if analisis.beneficio_estimado < 0: recetas_con_perdida += 1
            if analisis.incidencias: recetas_incompletas += 1
            ingredientes_sin_precio += sum(1 for ing in analisis.ingredientes if 'sin_precio' in ing.get('incidencias', []))
            margenes.append(analisis.margen_pct); foodcosts.append(analisis.food_cost_pct)
        margen_medio = round(sum(margenes)/len(margenes),2) if margenes else 0.0
        food_medio = round(sum(foodcosts)/len(foodcosts),2) if foodcosts else 0.0
        estado = 'critico' if recetas_con_perdida or ingredientes_sin_precio else ('revisar' if recetas_incompletas or food_medio > 35 else 'ok')
        resumen={
            'estado_general': estado,
            'coste_total_estimado': round(coste_total,2),
            'venta_total': round(venta_total,2),
            'beneficio_total_estimado': round(beneficio_total,2),
            'margen_medio_pct': margen_medio,
            'food_cost_medio_pct': food_medio,
            'recetas_con_perdida': recetas_con_perdida,
            'recetas_incompletas': recetas_incompletas,
            'ingredientes_sin_precio': ingredientes_sin_precio,
        }
        lectura = f"Análisis inteligente de escandallos: {len(analizados)} recetas, food cost medio {food_medio}% y estado {estado}."
        return InformeAnalisisEscandallos307('3.0.7.1', len(analizados), round(coste_total,2), round(venta_total,2), round(beneficio_total,2), margen_medio, food_medio, recetas_con_perdida, recetas_incompletas, ingredientes_sin_precio, analizados, resumen, lectura).to_dict()

    def exportar_analisis(self, analisis: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.dir / (nombre or 'analisis_inteligente_escandallos_3071.json')
        destino.write_text(json.dumps(analisis, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Análisis inteligente de escandallos exportado: {destino.name}.'}

    def _analizar_uno(self, raw: Dict[str, Any], idx:int, coste_hora:float, pct_ocultos:float) -> AnalisisEscandallo307:
        nombre=str(raw.get('nombre') or raw.get('receta') or raw.get('elaboracion') or f'Escandallo {idx+1}').strip()
        clave=str(raw.get('clave') or raw.get('id') or nombre.lower().replace(' ','_')).strip()
        raciones=max(1.0, float(raw.get('raciones', raw.get('pax', raw.get('cantidad_raciones', 1))) or 1))
        precio_venta=float(raw.get('precio_venta', raw.get('venta_total', raw.get('pvp', 0))) or 0)
        if precio_venta and precio_venta < raciones * 1.5 and raw.get('precio_venta_por_racion') is None:
            precio_total=precio_venta
        else:
            precio_total=float(raw.get('precio_venta_total', 0) or 0) or precio_venta
        if raw.get('precio_venta_por_racion') is not None:
            precio_total=float(raw.get('precio_venta_por_racion') or 0)*raciones
        ingredientes_raw = raw.get('ingredientes') or raw.get('articulos') or raw.get('lineas') or []
        ingredientes=[]; coste_ing=0.0; coste_merma=0.0; incidencias=[]; recomendaciones=[]
        if not ingredientes_raw:
            incidencias.append('sin_ingredientes')
            recomendaciones.append('Completar ingredientes antes de validar rentabilidad.')
        for ing_raw in ingredientes_raw:
            ing=self._normalizar_ingrediente(ing_raw)
            ingredientes.append(ing.to_dict())
            coste_ing += ing.coste
            coste_merma += ing.coste_real_con_merma
            if ing.incidencias:
                incidencias.extend([f"{ing.nombre}:{x}" for x in ing.incidencias])
        activo=int(float(raw.get('tiempo_activo_min', raw.get('activo_min', 0)) or 0))
        pasivo=int(float(raw.get('tiempo_pasivo_min', raw.get('pasivo_min', 0)) or 0))
        coste_mo=round((activo/60.0)*float(coste_hora),2)
        coste_oculto=round((coste_merma+coste_mo)*(float(pct_ocultos)/100.0),2)
        coste_total=round(coste_merma+coste_mo+coste_oculto,2)
        coste_racion=round(coste_total/raciones,2) if raciones else 0.0
        venta_racion=round(precio_total/raciones,2) if raciones else 0.0
        margen_total=round(precio_total-coste_merma,2)
        margen_racion=round((precio_total-coste_total)/raciones,2) if raciones else 0.0
        beneficio=round(precio_total-coste_total,2)
        margen_pct=round((beneficio/precio_total)*100,2) if precio_total else 0.0
        food_pct=round((coste_merma/precio_total)*100,2) if precio_total else 0.0
        if precio_total <= 0:
            incidencias.append('sin_precio_venta'); recomendaciones.append('Asignar precio de venta para poder calcular margen.')
        if any('sin_precio' in ing.get('incidencias',[]) for ing in ingredientes):
            recomendaciones.append('Actualizar precios de ingredientes a 0 antes de cerrar escandallo.')
        if beneficio < 0:
            rent='perdida'; recomendaciones.append('Revisar precio de venta, gramajes o proveedor: la receta genera pérdida.')
        elif margen_pct < 15 or food_pct > 40:
            rent='baja'; recomendaciones.append('Optimizar coste o subir precio: margen bajo.')
        elif margen_pct < 30 or food_pct > 32:
            rent='media'; recomendaciones.append('Escandallo aceptable pero mejorable.')
        else:
            rent='alta'; recomendaciones.append('Escandallo rentable según parámetros actuales.')
        return AnalisisEscandallo307(clave,nombre,raciones,round(precio_total,2),round(coste_ing,2),round(coste_merma,2),coste_racion,venta_racion,margen_total,margen_racion,margen_pct,food_pct,activo,pasivo,coste_mo,coste_oculto,coste_total,beneficio,rent,ingredientes,incidencias,recomendaciones,dict(raw))

    def _normalizar_ingrediente(self, raw: Dict[str, Any]) -> IngredienteEscandallo307:
        nombre=str(raw.get('nombre') or raw.get('articulo') or raw.get('ingrediente') or 'Ingrediente sin nombre').strip()
        cantidad=float(raw.get('cantidad', raw.get('qty', 0)) or 0)
        precio=float(raw.get('precio_unitario', raw.get('precio', raw.get('coste_unitario', 0))) or 0)
        merma=float(raw.get('merma_pct', raw.get('merma', 0)) or 0)
        coste=round(cantidad*precio,4)
        coste_real=round(coste/(1-(merma/100.0)),4) if merma < 100 else coste
        incid=[]
        if precio <= 0: incid.append('sin_precio')
        if cantidad <= 0: incid.append('cantidad_no_valida')
        if merma > 35: incid.append('merma_alta')
        alergenos=raw.get('alergenos') or []
        if isinstance(alergenos, str): alergenos=[a.strip() for a in alergenos.split(',') if a.strip()]
        return IngredienteEscandallo307(nombre,cantidad,str(raw.get('unidad','')),precio,merma,coste,coste_real,str(raw.get('proveedor','')),alergenos,incid,dict(raw))

    def _cargar_escandallos_base(self) -> List[Dict[str, Any]]:
        rutas=[self.base_dir/'DATOS'/'db'/'escandallos.json', self.base_dir/'DATOS'/'escandallos.json']
        for ruta in rutas:
            if ruta.exists():
                try:
                    data=json.loads(ruta.read_text(encoding='utf-8'))
                    if isinstance(data, list) and data: return data
                    if isinstance(data, dict):
                        for k in ('escandallos','recetas','items'):
                            if isinstance(data.get(k), list) and data[k]: return data[k]
                except Exception: pass
        return [
            {'nombre':'Paella marisco','raciones':10,'precio_venta_por_racion':18,'tiempo_activo_min':90,'ingredientes':[{'nombre':'Arroz','cantidad':1,'unidad':'kg','precio_unitario':2.4},{'nombre':'Caldo','cantidad':3,'unidad':'l','precio_unitario':1.2},{'nombre':'Gamba','cantidad':1.2,'unidad':'kg','precio_unitario':14,'merma_pct':8}]},
            {'nombre':'Carrillera braseada','raciones':12,'precio_venta_por_racion':16,'tiempo_activo_min':120,'tiempo_pasivo_min':180,'ingredientes':[{'nombre':'Carrillera','cantidad':5,'unidad':'kg','precio_unitario':8.5,'merma_pct':15},{'nombre':'Vino tinto','cantidad':1,'unidad':'l','precio_unitario':3.2},{'nombre':'Bresa','cantidad':2,'unidad':'kg','precio_unitario':1.5}]},
        ]
