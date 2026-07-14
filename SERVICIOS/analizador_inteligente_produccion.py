from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import json
from MODELOS.analisis_produccion_306 import ItemAnalisisProduccion, InformeAnalisisProduccion

class AnalizadorInteligenteProduccion:
    """Host AI 3.0.6.1 - Analizador Inteligente de Producción.

    Analiza elaboraciones, tiempos activos/pasivos, recursos, prioridades, dependencias y carga
    operativa para empezar el bloque 3.0.6 Producción sobre una base estructurada.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.produccion_dir = self.base_dir / 'DATOS' / 'produccion'
        self.produccion_dir.mkdir(parents=True, exist_ok=True)

    def analizar_produccion(self, elaboraciones: List[Dict[str, Any]] | None = None, jornada_horas: float = 7.5, cocineros: int = 3) -> Dict[str, Any]:
        datos = elaboraciones if elaboraciones is not None else self._cargar_elaboraciones_base()
        items: List[Dict[str, Any]] = []
        recursos=set(); prioridades={'critica':0,'alta':0,'normal':0,'baja':0}; riesgos={'alto':0,'medio':0,'normal':0}
        activo_total=0; pasivo_total=0; total_estimado=0
        for idx, raw in enumerate(datos or []):
            item = self._normalizar_item(raw, idx)
            activo_total += item.tiempo_activo_min
            pasivo_total += item.tiempo_pasivo_min
            total_estimado += item.tiempo_total_min
            for r in item.recursos: recursos.add(r)
            prioridades[item.prioridad] = prioridades.get(item.prioridad,0)+1
            riesgos[item.riesgo] = riesgos.get(item.riesgo,0)+1
            items.append(item.to_dict())
        capacidad_min = max(0, int(float(jornada_horas)*60*max(1,int(cocineros))))
        ocupacion = round((activo_total / capacidad_min) * 100, 2) if capacidad_min else 0
        estado = 'critico' if ocupacion > 115 or riesgos.get('alto',0) else ('ajustar' if ocupacion > 90 or prioridades.get('critica',0) else 'ok')
        resumen = {
            'estado_general': estado,
            'jornada_horas': jornada_horas,
            'cocineros': cocineros,
            'capacidad_activa_min': capacidad_min,
            'ocupacion_activa_pct': ocupacion,
            'elaboraciones_criticas': prioridades.get('critica',0),
            'elaboraciones_riesgo_alto': riesgos.get('alto',0),
            'recursos_clave': sorted(recursos),
        }
        lectura = f"Análisis inteligente de producción: {len(items)} elaboraciones, {activo_total} min activos, {pasivo_total} min pasivos y estado {estado}."
        return InformeAnalisisProduccion('3.0.6.1', len(items), activo_total, pasivo_total, total_estimado, sorted(recursos), prioridades, riesgos, items, resumen, lectura).to_dict()

    def exportar_analisis(self, analisis: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino = self.produccion_dir / (nombre or 'analisis_inteligente_produccion_3061.json')
        destino.write_text(json.dumps(analisis, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo': str(destino), 'lectura_host_ai': f'Análisis inteligente de producción exportado: {destino.name}.'}

    def _normalizar_item(self, raw: Dict[str, Any], idx: int) -> ItemAnalisisProduccion:
        nombre = str(raw.get('nombre') or raw.get('elaboracion') or raw.get('receta') or f'Elaboración {idx+1}').strip()
        clave = str(raw.get('clave') or raw.get('id') or nombre.lower().replace(' ','_')).strip()
        activo = int(float(raw.get('tiempo_activo_min', raw.get('activo_min', raw.get('minutos_activos', 0))) or 0))
        pasivo = int(float(raw.get('tiempo_pasivo_min', raw.get('pasivo_min', raw.get('minutos_pasivos', 0))) or 0))
        total = int(float(raw.get('tiempo_total_min', raw.get('minutos', activo+pasivo)) or (activo+pasivo)))
        if total < activo + pasivo: total = activo + pasivo
        recursos = raw.get('recursos') or raw.get('maquinaria') or []
        if isinstance(recursos, str): recursos = [r.strip() for r in recursos.split(',') if r.strip()]
        dependencias = raw.get('dependencias') or []
        if isinstance(dependencias, str): dependencias = [d.strip() for d in dependencias.split(',') if d.strip()]
        prioridad = str(raw.get('prioridad') or 'normal').lower()
        if prioridad not in {'critica','alta','normal','baja'}: prioridad = 'normal'
        riesgo = self._calcular_riesgo(activo, pasivo, total, recursos, dependencias, prioridad)
        trabajadores = max(1, int(float(raw.get('trabajadores_recomendados', raw.get('cocineros', 1)) or 1)))
        return ItemAnalisisProduccion(
            clave=clave, nombre=nombre, tipo=str(raw.get('tipo','elaboracion')), cantidad=float(raw.get('cantidad',0) or 0), unidad=str(raw.get('unidad','')),
            tiempo_activo_min=activo, tiempo_pasivo_min=pasivo, tiempo_total_min=total, dificultad=str(raw.get('dificultad','media')),
            prioridad=prioridad, recursos=list(recursos), dependencias=list(dependencias), trabajadores_recomendados=trabajadores, riesgo=riesgo, datos=dict(raw)
        )

    def _calcular_riesgo(self, activo:int, pasivo:int, total:int, recursos:List[str], dependencias:List[str], prioridad:str) -> str:
        puntos = 0
        if prioridad == 'critica': puntos += 2
        if activo >= 180: puntos += 2
        elif activo >= 90: puntos += 1
        if total >= 360: puntos += 2
        elif total >= 180: puntos += 1
        if len(recursos) >= 3: puntos += 1
        if dependencias: puntos += 1
        if pasivo >= 180: puntos += 1
        return 'alto' if puntos >= 4 else ('medio' if puntos >= 2 else 'normal')

    def _cargar_elaboraciones_base(self) -> List[Dict[str, Any]]:
        rutas = [self.base_dir/'DATOS'/'db'/'planes_produccion.json', self.base_dir/'DATOS'/'db'/'escandallos.json']
        for ruta in rutas:
            if ruta.exists():
                try:
                    data=json.loads(ruta.read_text(encoding='utf-8'))
                    if isinstance(data, list): return data
                    if isinstance(data, dict):
                        for key in ('elaboraciones','planes','recetas','items'):
                            if isinstance(data.get(key), list): return data[key]
                except Exception:
                    pass
        return [
            {'nombre':'Carrilleras braseadas','cantidad':12,'unidad':'kg','tiempo_activo_min':95,'tiempo_pasivo_min':180,'recursos':['horno','fogón'],'prioridad':'alta','dependencias':['fondo oscuro']},
            {'nombre':'Fondo oscuro','cantidad':20,'unidad':'l','tiempo_activo_min':45,'tiempo_pasivo_min':240,'recursos':['horno','olla'],'prioridad':'critica'},
            {'nombre':'Salsa romesco','cantidad':4,'unidad':'kg','tiempo_activo_min':50,'tiempo_pasivo_min':20,'recursos':['horno','robot'],'prioridad':'normal'},
        ]
