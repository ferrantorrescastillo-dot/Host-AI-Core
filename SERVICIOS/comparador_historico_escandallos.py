from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json

class ComparadorHistoricoEscandallos:
    """Host AI 3.0.7.4 - Comparador Histórico de Escandallos.

    Compara versiones antiguas/nuevas de recetas: coste, margen, proveedores,
    ingredientes y evolución económica del escandallo.
    """
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.dir = self.base_dir / 'DATOS' / 'escandallos_inteligentes'
        self.dir.mkdir(parents=True, exist_ok=True)

    def comparar_historico(self, escandallos_anteriores: List[Dict[str, Any]] | None = None,
                           escandallos_actuales: List[Dict[str, Any]] | None = None,
                           analisis_anterior: Dict[str, Any] | None = None,
                           analisis_actual: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if analisis_anterior is None:
            analisis_anterior=self.core.analizador_inteligente_escandallos.analizar_escandallos(escandallos_anteriores or self._cargar_version('anterior'))
        if analisis_actual is None:
            analisis_actual=self.core.analizador_inteligente_escandallos.analizar_escandallos(escandallos_actuales or self._cargar_version('actual'))
        prev={self._clave(x):x for x in analisis_anterior.get('escandallos',[])}
        curr={self._clave(x):x for x in analisis_actual.get('escandallos',[])}
        claves=sorted(set(prev)|set(curr))
        comparaciones=[]; subidas=0; bajadas=0; nuevos=0; eliminados=0; impacto_total=0.0
        for c in claves:
            comp=self._comparar_uno(c, prev.get(c), curr.get(c))
            comparaciones.append(comp)
            impacto_total += comp.get('impacto_coste_total',0.0)
            if comp['estado']=='nuevo': nuevos += 1
            elif comp['estado']=='eliminado': eliminados += 1
            elif comp.get('variacion_coste_pct',0) > 5: subidas += 1
            elif comp.get('variacion_coste_pct',0) < -5: bajadas += 1
        resumen={'estado_general':'critico' if subidas else ('revisar' if nuevos or eliminados else 'ok'),'total_comparaciones':len(comparaciones),'escandallos_nuevos':nuevos,'escandallos_eliminados':eliminados,'subidas_coste':subidas,'bajadas_coste':bajadas,'impacto_coste_total':round(impacto_total,2)}
        lectura=f"Comparador histórico de escandallos: {len(comparaciones)} comparaciones, {subidas} subidas de coste y {nuevos} recetas nuevas."
        return {'version':'3.0.7.4','total_comparaciones':len(comparaciones),'comparaciones':comparaciones,'resumen':resumen,'lectura_host_ai':lectura}

    def exportar_comparativa(self, comparativa: Dict[str, Any], nombre: str = '') -> Dict[str, Any]:
        destino=self.dir/(nombre or 'comparador_historico_escandallos_3074.json')
        destino.write_text(json.dumps(comparativa, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'archivo':str(destino),'lectura_host_ai':f'Comparativa histórica de escandallos exportada: {destino.name}.'}

    def _clave(self, x: Dict[str, Any]) -> str:
        return str(x.get('clave') or x.get('nombre') or '').strip().lower().replace(' ','_')

    def _comparar_uno(self, clave: str, anterior: Dict[str, Any] | None, actual: Dict[str, Any] | None) -> Dict[str, Any]:
        if anterior is None:
            return {'clave':clave,'escandallo':actual.get('nombre',clave),'estado':'nuevo','variacion_coste_pct':0.0,'variacion_margen_pct':0.0,'impacto_coste_total':float(actual.get('coste_total_estimado',0) or 0),'lectura_host_ai':'Escandallo nuevo incorporado al histórico.'}
        if actual is None:
            return {'clave':clave,'escandallo':anterior.get('nombre',clave),'estado':'eliminado','variacion_coste_pct':0.0,'variacion_margen_pct':0.0,'impacto_coste_total':-float(anterior.get('coste_total_estimado',0) or 0),'lectura_host_ai':'Escandallo eliminado o no presente en la versión actual.'}
        coste_ant=float(anterior.get('coste_total_estimado',0) or 0)
        coste_act=float(actual.get('coste_total_estimado',0) or 0)
        margen_ant=float(anterior.get('margen_pct',0) or 0)
        margen_act=float(actual.get('margen_pct',0) or 0)
        var_coste=round(((coste_act-coste_ant)/coste_ant)*100,2) if coste_ant else 0.0
        var_margen=round(margen_act-margen_ant,2)
        proveedores_ant=self._proveedores(anterior); proveedores_act=self._proveedores(actual)
        cambios_prov=sorted(list(proveedores_ant.symmetric_difference(proveedores_act)))
        ingredientes=self._comparar_ingredientes(anterior.get('ingredientes',[]), actual.get('ingredientes',[]))
        if var_coste > 8 or var_margen < -8: estado='empeora'
        elif var_coste < -5 or var_margen > 5: estado='mejora'
        else: estado='estable'
        return {'clave':clave,'escandallo':actual.get('nombre', anterior.get('nombre',clave)),'estado':estado,'coste_anterior':round(coste_ant,2),'coste_actual':round(coste_act,2),'variacion_coste_pct':var_coste,'margen_anterior_pct':margen_ant,'margen_actual_pct':margen_act,'variacion_margen_pct':var_margen,'impacto_coste_total':round(coste_act-coste_ant,2),'cambios_proveedor':cambios_prov,'comparativa_ingredientes':ingredientes,'lectura_host_ai':f"{actual.get('nombre',clave)}: {estado}, variación coste {var_coste}% y margen {var_margen} puntos."}

    def _proveedores(self, x: Dict[str, Any]) -> set:
        return {str(i.get('proveedor','')).strip().lower() for i in x.get('ingredientes',[]) if str(i.get('proveedor','')).strip()}

    def _comparar_ingredientes(self, ant: List[Dict[str, Any]], act: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        a={str(i.get('nombre','')).lower():i for i in ant}
        b={str(i.get('nombre','')).lower():i for i in act}
        out=[]
        for k in sorted(set(a)|set(b)):
            if not k: continue
            if k not in a: out.append({'ingrediente':k,'estado':'nuevo'})
            elif k not in b: out.append({'ingrediente':k,'estado':'eliminado'})
            else:
                ca=float(a[k].get('coste_real_con_merma',a[k].get('coste',0)) or 0); cb=float(b[k].get('coste_real_con_merma',b[k].get('coste',0)) or 0)
                if abs(cb-ca) > 0.01:
                    out.append({'ingrediente':k,'estado':'modificado','coste_anterior':round(ca,2),'coste_actual':round(cb,2),'variacion':round(cb-ca,2)})
        return out

    def _cargar_version(self, sufijo: str) -> List[Dict[str, Any]]:
        ruta=self.base_dir/'DATOS'/'db'/f'escandallos_{sufijo}.json'
        if ruta.exists():
            try:
                data=json.loads(ruta.read_text(encoding='utf-8'))
                return data if isinstance(data,list) else []
            except Exception: return []
        return []
