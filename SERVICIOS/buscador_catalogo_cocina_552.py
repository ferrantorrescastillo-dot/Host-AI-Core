from __future__ import annotations
import json, re, unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List

from SERVICIOS.lector_modelo_canonico_555b72 import LectorModeloCanonico555B72


def _norm(v: Any)->str:
    t=str(v or '').strip().lower()
    t=''.join(c for c in unicodedata.normalize('NFD',t) if unicodedata.category(c)!='Mn')
    return re.sub(r'\s+',' ',t)

def _cargar_lista(path: Path, keys: Iterable[str]=()) -> List[Dict[str,Any]]:
    if not path.exists(): return []
    try: data=json.loads(path.read_text(encoding='utf-8'))
    except Exception: return []
    if isinstance(data,list): return [x for x in data if isinstance(x,dict)]
    if isinstance(data,dict):
        for k in keys:
            if isinstance(data.get(k),list): return [x for x in data[k] if isinstance(x,dict)]
    return []

class BuscadorCatalogoCocina552:
    def __init__(self, base_dir: Path):
        self.base_dir=Path(base_dir)
        db=self.base_dir/'DATOS'/'db'
        catalogo=LectorModeloCanonico555B72(self.base_dir).cargar()
        self.escandallos=catalogo['escandallos']
        self.fuente_escandallos=catalogo['fuente']
        self.modelo_escandallos=catalogo['modelo']
        self.articulos=_cargar_lista(db/'articulos.json',('articulos','items'))
        self.proveedores=_cargar_lista(db/'proveedores.json',('proveedores','items'))

    def listar(self,tipo: str,limite:int=20)->Dict[str,Any]:
        if tipo in {'menus','recetas','escandallos'}:
            items=self.escandallos
            nombres=[self._nombre(x) for x in items if self._nombre(x)]
            fuente=self.fuente_escandallos
        elif tipo=='articulos':
            items=self.articulos; nombres=[self._nombre(x) for x in items if self._nombre(x)]; fuente='DATOS/db/articulos.json'
        else:
            items=self.proveedores; nombres=[self._nombre(x) for x in items if self._nombre(x)]; fuente='DATOS/db/proveedores.json'
        return {'tipo':tipo,'total':len(nombres),'resultados':nombres[:limite],'solo_lectura':True,'fuente':fuente,'modelo':self.modelo_escandallos if tipo in {'menus','recetas','escandallos'} else 'DATOS_ACTUALES'}

    def buscar(self,termino:str,limite:int=20)->Dict[str,Any]:
        q=_norm(termino)
        grupos=[]
        for tipo,items in [('escandallos_recetas_menus',self.escandallos),('articulos',self.articulos),('proveedores',self.proveedores)]:
            hallados=[]
            for x in items:
                ingredientes=x.get('ingredientes') if isinstance(x.get('ingredientes'),list) else []
                texto_ing=' '.join(_norm(i.get('nombre')) for i in ingredientes if isinstance(i,dict))
                texto=' '.join(_norm(x.get(k)) for k in ('nombre','receta','menu','plato','articulo','codigo','proveedor','familia'))+' '+texto_ing
                if q and q in texto: hallados.append({'nombre':self._nombre(x),'datos':x})
            grupos.append({'tipo':tipo,'total':len(hallados),'resultados':hallados[:limite]})
        return {'termino':termino,'grupos':grupos,'total':sum(g['total'] for g in grupos),'solo_lectura':True,'fuente_escandallos':self.fuente_escandallos,'modelo_escandallos':self.modelo_escandallos}

    @staticmethod
    def _nombre(x:Dict[str,Any])->str:
        return str(x.get('nombre') or x.get('receta') or x.get('menu') or x.get('plato') or x.get('articulo') or '').strip()

def extraer_termino_busqueda_552(texto:str)->str:
    t=(texto or '').strip().rstrip('?.')
    patrones=[r'palabra\s+(.+)$',r'contenga\s+(?:la palabra\s+)?(.+)$',r'(?:receta|menu|escandallo|articulo)\s+(?:llamad[oa]\s+)?(.+)$',r'venden\s+(.+)$',r'uso\s+(.+)$',r'llevan?\s+(.+)$']
    for p in patrones:
        m=re.search(p,t,flags=re.I)
        if m:return m.group(1).strip(' "\'')
    return ''

def formatear_resultado_552(resultado:Dict[str,Any])->str:
    if 'grupos' in resultado:
        lineas=[f"BÚSQUEDA REAL: {resultado.get('termino')}",f"Coincidencias totales: {resultado.get('total',0)}"]
        for g in resultado['grupos']:
            lineas.append(f"\n{g['tipo'].upper()} ({g['total']})")
            for item in g['resultados'][:10]: lineas.append(f"- {item['nombre']}")
        if not resultado.get('total'): lineas.append('\nNo he encontrado coincidencias. No inventaré datos.')
        fuente=resultado.get('fuente_escandallos')
    else:
        lineas=[f"{resultado['tipo'].upper()} DISPONIBLES",f"Total: {resultado['total']}"]+[f"- {n}" for n in resultado['resultados']]
        fuente=resultado.get('fuente')
        if not resultado['total']:
            lineas.append(f"- No hay registros cargados en {fuente or 'la base de datos de escandallos'}.")
    if fuente:
        lineas += ['', 'FUENTE DE DATOS', f'- {fuente}']
    lineas += ['','SEGURIDAD','- Consulta en modo solo lectura.','- Datos reales modificados: NO.']
    return '\n'.join(lineas)
