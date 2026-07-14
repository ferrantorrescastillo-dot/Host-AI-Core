from pathlib import Path
from openpyxl import Workbook
from SERVICIOS.importador_seguro_escandallos_i12 import ImportadorSeguroEscandallosI12

class MotorFake:
    def __init__(self): self.d=[]
    def registrar_escandallo(self, **kw): self.d.append(kw); return kw

def crear_excel(path):
    wb=Workbook(); ws=wb.active; ws.title='MP boda'
    ws.append(['FICHA TÉCNICA']); ws.append(['ARTÍCULO','Ceviche de corvina'])
    ws.append(['UNIDADES',10,'COSTE TOTAL',20]); ws.append(['ARTÍCULO','KG','€/UN','€ / RACION'])
    ws.append(['Corvina',2,8,16]); ws.append(['Limón',1,4,4]); wb.save(path)

def test_previa_no_escribe_y_vincula(tmp_path):
    x=tmp_path/'a.xlsx'; crear_excel(x)
    imp=ImportadorSeguroEscandallosI12()
    p=imp.preparar(x, catalogo_articulos=[{'id':'ART-1','nombre':'Corvina'},{'id':'ART-2','nombre':'Limón'}])
    assert p['resumen']['recetas_detectadas']==1
    assert p['resumen']['vinculos_exactos']==2
    assert p['modo']=='vista_previa_sin_escritura'

def test_importacion_exige_confirmacion_y_omite_duplicados(tmp_path):
    x=tmp_path/'a.xlsx'; crear_excel(x); imp=ImportadorSeguroEscandallosI12()
    p=imp.preparar(x, catalogo_articulos=[{'id':'ART-1','nombre':'Corvina'},{'id':'ART-2','nombre':'Limón'}])
    m=MotorFake()
    try: imp.importar(p,m,confirmar=False); assert False
    except ValueError: pass
    r=imp.importar(p,m,confirmar=True)
    assert r['resumen']['importadas']==1 and len(m.d)==1
    p2=imp.preparar(x, catalogo_articulos=[], escandallos_existentes=[{'receta_id':'REC-X','nombre':'Ceviche de corvina'}])
    r2=imp.importar(p2,m,confirmar=True,permitir_sin_resolver=True)
    assert r2['resumen']['omitidas']==1
