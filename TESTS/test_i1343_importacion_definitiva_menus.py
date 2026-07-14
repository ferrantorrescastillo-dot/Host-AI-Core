import json, pytest
from SERVICIOS.importador_definitivo_menus_i1343 import ImportadorDefinitivoMenusI1343

def plan():
 return {'plan_id':'P1','estado_simulacion':'LISTA_PARA_TRANSACCION','bloqueos':[],'acciones':[
 {'accion_id':'1','tipo':'CREAR','entidad':'MENU','nombre':'M1','estado':'PLANIFICADA','detalle':{'menu_id':'MID1','hoja':'H1'}},
 {'accion_id':'2','tipo':'CREAR_RELACION','entidad':'PLATO_MENU','nombre':'P1','estado':'PLANIFICADA','detalle':{'menu':'M1','menu_id':'MID1','seccion':'S1'}},
 {'accion_id':'3','tipo':'VINCULAR','entidad':'RECETA_PRINCIPAL','nombre':'R1','estado':'PLANIFICADA','detalle':{'menu':'M1','menu_id':'MID1','plato':'P1'}},
 {'accion_id':'4','tipo':'REGISTRAR','entidad':'DATOS_ECONOMICOS','nombre':'M1','estado':'PLANIFICADA','detalle':{'menu':'M1','menu_id':'MID1','precio_venta':10}}]}

def test_importa_e_idempotente(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 imp=ImportadorDefinitivoMenusI1343(tmp_path)
 imp.importar(plan(),confirmar=True); imp.importar(plan(),confirmar=True)
 d=json.loads(p.read_text()); assert len(d)==1 and d[0]['platos'][0]['componentes'][0]['nombre']=='R1'

def test_bloquea_plan_no_listo(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 x=plan(); x['estado_simulacion']='BLOQUEADA'
 with pytest.raises(ValueError): ImportadorDefinitivoMenusI1343(tmp_path).importar(x,confirmar=True)

def test_exige_confirmacion(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 with pytest.raises(PermissionError): ImportadorDefinitivoMenusI1343(tmp_path).importar(plan())

def sesion_lista():
 return {'plan':plan(),'resumen_revision':{'pendientes':0,'bloqueantes':0}}

def test_carga_sesion_revisada_valida_con_ruta_absoluta(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 archivo=tmp_path/'REV TEST.json'; archivo.write_text(json.dumps(sesion_lista()),encoding='utf-8')
 sesion=ImportadorDefinitivoMenusI1343(tmp_path).cargar_sesion_revisada(str(archivo))
 assert sesion['plan']['plan_id']=='P1'
 assert sesion['_ruta_validada']==str(archivo.resolve())

def test_carga_sesion_revisada_admite_ruta_relativa(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 archivo=tmp_path/'DATOS/mur/revisiones_i13415/REV-OK.json'; archivo.parent.mkdir(parents=True)
 archivo.write_text(json.dumps(sesion_lista()),encoding='utf-8')
 sesion=ImportadorDefinitivoMenusI1343(tmp_path).cargar_sesion_revisada('DATOS/mur/revisiones_i13415/REV-OK.json')
 assert sesion['_ruta_validada']==str(archivo.resolve())

def test_carga_sesion_revisada_rechaza_archivo_inexistente(tmp_path):
 with pytest.raises(FileNotFoundError, match='No existe'):
  ImportadorDefinitivoMenusI1343(tmp_path).cargar_sesion_revisada(tmp_path/'no_existe.json')

def test_carga_sesion_revisada_rechaza_json_corrupto(tmp_path):
 archivo=tmp_path/'rota.json'; archivo.write_text('{mal',encoding='utf-8')
 with pytest.raises(ValueError, match='no es válido'):
  ImportadorDefinitivoMenusI1343(tmp_path).cargar_sesion_revisada(archivo)

def test_carga_sesion_revisada_rechaza_pendientes(tmp_path):
 s=sesion_lista(); s['resumen_revision']['pendientes']=1
 archivo=tmp_path/'pendiente.json'; archivo.write_text(json.dumps(s),encoding='utf-8')
 with pytest.raises(ValueError, match='todavía no está lista'):
  ImportadorDefinitivoMenusI1343(tmp_path).cargar_sesion_revisada(archivo)

def test_carga_sesion_revisada_rechaza_plan_bloqueado(tmp_path):
 s=sesion_lista(); s['plan']['estado_simulacion']='BLOQUEADA'
 archivo=tmp_path/'bloqueada.json'; archivo.write_text(json.dumps(s),encoding='utf-8')
 with pytest.raises(ValueError, match='no está listo'):
  ImportadorDefinitivoMenusI1343(tmp_path).cargar_sesion_revisada(archivo)

def plan_componentes_desordenados():
 return {
  'plan_id':'P-COMP','estado_simulacion':'LISTA_PARA_TRANSACCION','bloqueos':[],
  'acciones':[
   {'accion_id':'M','tipo':'CREAR','entidad':'MENU','nombre':'MENU BODA','estado':'PLANIFICADA','detalle':{'menu_id':'MID-BODA','hoja':'MENU BODA 31-1'}},
   # Componentes antes del plato para validar independencia del orden.
   {'accion_id':'SAL','tipo':'VINCULAR','entidad':'SALSA','nombre':'Salsa naranja','estado':'PLANIFICADA','detalle':{'menu':'MENU BODA','menu_id':'MID-BODA','plato':'Solomillo de cerdo con parmentier patata i salsa naranja'}},
   {'accion_id':'GUA','tipo':'VINCULAR','entidad':'GUARNICION','nombre':'Parmentier de patata','estado':'PLANIFICADA','detalle':{'menu':'MENU BODA','menu_id':'MID-BODA','plato':'Solomillo de cerdo con parmentier patata i salsa naranja'}},
   {'accion_id':'PLA','tipo':'CREAR_RELACION','entidad':'PLATO_MENU','nombre':'Solomillo de cerdo con parmentier patata i salsa naranja','estado':'PLANIFICADA','detalle':{'menu':'MENU BODA','menu_id':'MID-BODA','seccion':'Segundo'}},
   {'accion_id':'REC','tipo':'VINCULAR','entidad':'RECETA_PRINCIPAL','nombre':'Solomillo de cerdo','estado':'PLANIFICADA','detalle':{'menu':'MENU BODA','menu_id':'MID-BODA','plato':'Solomillo de cerdo con parmentier patata i salsa naranja'}},
  ]}


def test_componentes_se_enlazan_aunque_aparezcan_antes_del_plato(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 imp=ImportadorDefinitivoMenusI1343(tmp_path)
 catalogo,_=imp.construir_catalogo(plan_componentes_desordenados(),[])
 plato=catalogo[0]['platos'][0]
 assert {c['nombre'] for c in plato['componentes']} == {'Solomillo de cerdo','Parmentier de patata','Salsa naranja'}
 assert all(c['plato_id']==plato['plato_id'] for c in plato['componentes'])


def test_componente_resuelve_por_plato_id_estable_tras_renombrado(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 x=plan_componentes_desordenados()
 plato=next(a for a in x['acciones'] if a['entidad']=='PLATO_MENU')
 plato['nombre']='Solomillo de cerdo, parmentier y salsa de naranja'
 plato['detalle']['plato_id']='PLATO-ESTABLE-001'
 salsa=next(a for a in x['acciones'] if a['nombre']=='Salsa naranja')
 salsa['detalle']={'menu':'MENU BODA','menu_id':'MID-BODA','plato_id':'PLATO-ESTABLE-001','plato':'nombre anterior que ya no coincide'}
 catalogo,_=ImportadorDefinitivoMenusI1343(tmp_path).construir_catalogo(x,[])
 plato_guardado=catalogo[0]['platos'][0]
 assert plato_guardado['plato_id']=='PLATO-ESTABLE-001'
 assert any(c['nombre']=='Salsa naranja' for c in plato_guardado['componentes'])


def test_relaciones_de_componentes_son_idempotentes(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 imp=ImportadorDefinitivoMenusI1343(tmp_path)
 imp.importar(plan_componentes_desordenados(),confirmar=True,idempotency_key='COMP-1')
 imp.importar(plan_componentes_desordenados(),confirmar=True,idempotency_key='COMP-2')
 data=json.loads(p.read_text())
 assert len(data)==1
 assert len(data[0]['platos'])==1
 assert len(data[0]['platos'][0]['componentes'])==3


def test_fallo_de_destino_ocurre_antes_de_escritura(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 x=plan_componentes_desordenados()
 x['acciones']=[a for a in x['acciones'] if a['entidad']!='PLATO_MENU']
 antes=p.read_bytes()
 with pytest.raises(ValueError, match='Componente sin plato destino'):
  ImportadorDefinitivoMenusI1343(tmp_path).importar(x,confirmar=True)
 assert p.read_bytes()==antes

def plan_con_plato_duplicado_misma_identidad():
 x=plan_componentes_desordenados()
 # Duplica la relación PLATO_MENU como ocurre en sesiones antiguas tras revisar/renombrar.
 original=next(a for a in x['acciones'] if a['entidad']=='PLATO_MENU')
 duplicado={
  'accion_id':'PLA-DUP','tipo':'CREAR_RELACION','entidad':'PLATO_MENU',
  'nombre':'Solomillo de cerdo con parmentier patata i salsa naranja',
  'estado':'PLANIFICADA','detalle':{
   'menu':'MENU BODA','menu_id':'MID-BODA','seccion':'Segundo',
   'plato_original':'Solomillo de cerdo con parmentier patata i salsa naranja'
  }
 }
 x['acciones'].insert(x['acciones'].index(original)+1, duplicado)
 return x


def test_deduplica_dos_acciones_del_mismo_plato_logico(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 catalogo,_=ImportadorDefinitivoMenusI1343(tmp_path).construir_catalogo(plan_con_plato_duplicado_misma_identidad(),[])
 assert len(catalogo[0]['platos'])==1
 plato=catalogo[0]['platos'][0]
 assert {c['nombre'] for c in plato['componentes']} == {'Solomillo de cerdo','Parmentier de patata','Salsa naranja'}


def test_alias_duplicados_del_mismo_plato_no_generan_ambiguedad(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 x=plan_con_plato_duplicado_misma_identidad()
 salsa=next(a for a in x['acciones'] if a['nombre']=='Salsa naranja')
 salsa['detalle'].update({
  'plato':'Solomillo de cerdo con parmentier patata i salsa naranja',
  'plato_original':'Solomillo de cerdo con parmentier patata i salsa naranja',
  'plato_destino':'Solomillo de cerdo con parmentier patata i salsa naranja'
 })
 catalogo,_=ImportadorDefinitivoMenusI1343(tmp_path).construir_catalogo(x,[])
 plato=catalogo[0]['platos'][0]
 assert sum(1 for c in plato['componentes'] if c['nombre']=='Salsa naranja')==1


def test_identidad_explicita_con_alias_repetidos_prevalece(tmp_path):
 rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]')
 x=plan_con_plato_duplicado_misma_identidad()
 for a in x['acciones']:
  if a['entidad']=='PLATO_MENU':
   a['detalle']['plato_id']='PLATO-BODA-SOLOMILLO'
 salsa=next(a for a in x['acciones'] if a['nombre']=='Salsa naranja')
 salsa['detalle']['plato_id']='PLATO-BODA-SOLOMILLO'
 catalogo,_=ImportadorDefinitivoMenusI1343(tmp_path).construir_catalogo(x,[])
 assert len(catalogo[0]['platos'])==1
 assert catalogo[0]['platos'][0]['plato_id']=='PLATO-BODA-SOLOMILLO'
