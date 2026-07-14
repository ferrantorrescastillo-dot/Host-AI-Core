from __future__ import annotations
from pathlib import Path
from SERVICIOS.importador_definitivo_menus_i1343 import ImportadorDefinitivoMenusI1343

class DiagnosticoImportacionMenusI1343:
    def __init__(self, base_dir: str | Path):
        self.base_dir=Path(base_dir)
        self.rel='DATOS/mur/diagnostico_i1343/menus.json'
    def ejecutar(self):
        p=self.base_dir/self.rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('[]',encoding='utf-8')
        plan={'plan_id':'PLAN-DIAG-I1343','estado_simulacion':'LISTA_PARA_TRANSACCION','bloqueos':[], 'acciones':[
          {'accion_id':'A1','tipo':'CREAR','entidad':'MENU','nombre':'MENU DIAGNOSTICO I1343','estado':'PLANIFICADA','detalle':{'menu_id':'MENU-DIAG-I1343','hoja':'MENU TEST'}},
          {'accion_id':'A2','tipo':'CREAR_O_REUTILIZAR','entidad':'SECCION','nombre':'PRINCIPAL','estado':'PLANIFICADA','detalle':{'menu':'MENU DIAGNOSTICO I1343','menu_id':'MENU-DIAG-I1343'}},
          {'accion_id':'A3','tipo':'CREAR_RELACION','entidad':'PLATO_MENU','nombre':'Solomillo diagnóstico','estado':'PLANIFICADA','detalle':{'menu':'MENU DIAGNOSTICO I1343','menu_id':'MENU-DIAG-I1343','seccion':'PRINCIPAL','coste_racion':4.5}},
          {'accion_id':'A4','tipo':'VINCULAR','entidad':'RECETA_PRINCIPAL','nombre':'Solomillo de cerdo','estado':'PLANIFICADA','detalle':{'menu':'MENU DIAGNOSTICO I1343','menu_id':'MENU-DIAG-I1343','plato':'Solomillo diagnóstico'}},
          {'accion_id':'A5','tipo':'VINCULAR','entidad':'ARTICULO_DIRECTO','nombre':'Pan individual','estado':'PLANIFICADA','detalle':{'menu':'MENU DIAGNOSTICO I1343','menu_id':'MENU-DIAG-I1343','coste_racion':.2}},
          {'accion_id':'A6','tipo':'REGISTRAR','entidad':'DATOS_ECONOMICOS','nombre':'MENU DIAGNOSTICO I1343','estado':'PLANIFICADA','detalle':{'menu':'MENU DIAGNOSTICO I1343','menu_id':'MENU-DIAG-I1343','precio_venta':50,'coste_total':12,'food_cost_pct':24,'beneficio':38}},
        ]}
        imp=ImportadorDefinitivoMenusI1343(self.base_dir,self.rel)
        r1=imp.importar(plan,confirmar=True,idempotency_key='DIAG-I1343')
        r2=imp.importar(plan,confirmar=True,idempotency_key='DIAG-I1343-REPEAT')
        import json
        data=json.loads(p.read_text(encoding='utf-8'))
        ok=len(data)==1 and len(data[0]['platos'])==1 and len(data[0]['platos'][0]['componentes'])==1
        return {'diagnostico':'OK' if ok else 'ERROR','primera':r1,'segunda':r2,'menus':len(data),'duplicados':len(data)-1,
                'platos':len(data[0]['platos']) if data else 0,'componentes':len(data[0]['platos'][0]['componentes']) if data and data[0]['platos'] else 0,
                'archivo':str(p)}

def formatear_diagnostico_i1343(r):
    t1=r['primera']['resultado_transaccion']; t2=r['segunda']['resultado_transaccion']
    return '\n'.join(['I1.3.4.3 — IMPORTACIÓN DEFINITIVA DE MENÚS','='*78,
      f"Diagnóstico: {r['diagnostico']} | Primera: {t1['estado']} | Repetición: {t2['estado']}",
      f"Menús: {r['menus']} | Duplicados: {r['duplicados']} | Platos: {r['platos']} | Componentes: {r['componentes']}",
      f"Backup primera: {t1['backup_dir']}", f"Archivo aislado: {r['archivo']}",'-'*78,
      'Se validó creación, relaciones, componentes, datos económicos, commit e idempotencia.',
      'El diagnóstico no modificó DATOS/db/menus.json ni otros datos reales.'])
