from __future__ import annotations
from typing import Dict, Any, List
import json
from MODELOS.escandallos_inteligentes_307 import AlertaEscandallo307, InformeAlertasEscandallos307

class MotorAlertasEscandallos:
    """Host AI 3.0.7.2 - Motor de Alertas de Escandallos.

    Detecta recetas con pérdidas, ingredientes sin precio, duplicados, mermas excesivas, costes fuera de rango
    y escandallos incompletos a partir del análisis 3.0.7.1 o de escandallos en bruto.
    """
    def __init__(self, core):
        self.core=core
        self.base_dir=core.base_dir
        self.dir=self.base_dir/'DATOS'/'escandallos_inteligentes'
        self.dir.mkdir(parents=True, exist_ok=True)

    def generar_alertas(self, analisis: Dict[str, Any] | None = None, escandallos: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        if analisis is None:
            analisis = self.core.analizador_inteligente_escandallos.analizar_escandallos(escandallos)
        alertas=[]
        for esc in analisis.get('escandallos', []):
            self._alertas_escandallo(esc, alertas)
        crit=sum(1 for a in alertas if a.gravedad=='critica')
        avis=sum(1 for a in alertas if a.gravedad=='aviso')
        info=sum(1 for a in alertas if a.gravedad=='informativa')
        estado='critico' if crit else ('revisar' if avis else 'ok')
        resumen={'estado_general':estado,'criticas':crit,'avisos':avis,'informativas':info,'escandallos_revisados':analisis.get('total_escandallos',0)}
        lectura=f"Alertas de escandallos: {len(alertas)} alertas detectadas ({crit} críticas, {avis} avisos). Estado {estado}."
        return InformeAlertasEscandallos307('3.0.7.2',len(alertas),crit,avis,info,[a.to_dict() for a in alertas],resumen,lectura).to_dict()

    def exportar_alertas(self, alertas: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino=self.dir/(nombre or 'alertas_escandallos_3072.json')
        destino.write_text(json.dumps(alertas, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo':str(destino),'lectura_host_ai':f'Alertas de escandallos exportadas: {destino.name}.'}

    def _alertas_escandallo(self, esc: Dict[str, Any], alertas: List[AlertaEscandallo307]) -> None:
        nombre=esc.get('nombre','Escandallo')
        if esc.get('beneficio_estimado',0) < 0:
            alertas.append(AlertaEscandallo307('critica','receta_con_perdida',nombre,mensaje=f"{nombre} genera pérdida estimada.",accion_recomendada='Revisar precio de venta, gramajes, proveedor o costes ocultos.',datos={'beneficio_estimado':esc.get('beneficio_estimado')}))
        if esc.get('precio_venta',0) <= 0:
            alertas.append(AlertaEscandallo307('critica','sin_precio_venta',nombre,mensaje=f"{nombre} no tiene precio de venta.",accion_recomendada='Añadir PVP antes de validar rentabilidad.'))
        if esc.get('food_cost_pct',0) > 45:
            alertas.append(AlertaEscandallo307('aviso','food_cost_alto',nombre,mensaje=f"Food cost de {nombre} por encima del rango recomendado.",accion_recomendada='Optimizar compra o ajustar precio.',datos={'food_cost_pct':esc.get('food_cost_pct')}))
        if esc.get('margen_pct',0) < 15 and esc.get('precio_venta',0) > 0:
            alertas.append(AlertaEscandallo307('aviso','margen_bajo',nombre,mensaje=f"Margen bajo en {nombre}.",accion_recomendada='Revisar rentabilidad de la receta.',datos={'margen_pct':esc.get('margen_pct')}))
        if 'sin_ingredientes' in esc.get('incidencias',[]):
            alertas.append(AlertaEscandallo307('critica','receta_sin_ingredientes',nombre,mensaje=f"{nombre} no tiene ingredientes.",accion_recomendada='Completar ficha técnica y escandallo.'))
        vistos={}
        for ing in esc.get('ingredientes',[]):
            n=str(ing.get('nombre','')).lower().strip()
            if n:
                vistos[n]=vistos.get(n,0)+1
            if 'sin_precio' in ing.get('incidencias',[]):
                alertas.append(AlertaEscandallo307('critica','ingrediente_sin_precio',nombre,ing.get('nombre',''),f"Ingrediente sin precio en {nombre}: {ing.get('nombre','')}.",'Actualizar precio y proveedor antes de cerrar el escandallo.',{'precio_unitario':ing.get('precio_unitario')}))
            if 'cantidad_no_valida' in ing.get('incidencias',[]):
                alertas.append(AlertaEscandallo307('aviso','cantidad_no_valida',nombre,ing.get('nombre',''),f"Cantidad no válida en {ing.get('nombre','')}.",'Corregir cantidad o unidad del ingrediente.'))
            if 'merma_alta' in ing.get('incidencias',[]):
                alertas.append(AlertaEscandallo307('aviso','merma_excesiva',nombre,ing.get('nombre',''),f"Merma alta en {ing.get('nombre','')}.",'Revisar rendimiento real, proveedor o proceso de limpieza.',{'merma_pct':ing.get('merma_pct')}))
        for ing, count in vistos.items():
            if count > 1:
                alertas.append(AlertaEscandallo307('informativa','ingrediente_duplicado',nombre,ing,f"Ingrediente duplicado en {nombre}: {ing}.",'Unificar líneas si corresponden al mismo artículo.',{'repeticiones':count}))
