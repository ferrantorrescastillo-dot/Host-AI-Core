from pathlib import Path
from typing import Any,Dict
from SERVICIOS.clasificador_consultas_datos_551 import clasificar_consulta_datos_551
from SERVICIOS.buscador_catalogo_cocina_552 import BuscadorCatalogoCocina552,extraer_termino_busqueda_552,formatear_resultado_552

def procesar_consulta_datos_552(texto:str,base_dir:Path)->Dict[str,Any]:
    c=clasificar_consulta_datos_551(texto)
    if not c['gestionado']: return {'gestionado':False}
    b=BuscadorCatalogoCocina552(base_dir)
    i=c['intencion']
    if i=='consultar_menus': r=b.listar('menus')
    elif i=='consultar_recetas': r=b.listar('recetas')
    elif i=='consultar_escandallos': r=b.listar('escandallos')
    elif i=='consultar_articulos': r=b.listar('articulos')
    elif i=='consultar_proveedores':
        term=extraer_termino_busqueda_552(texto); r=b.buscar(term) if term else b.listar('proveedores')
    else: r=b.buscar(extraer_termino_busqueda_552(texto))
    return {'gestionado':True,'ok':True,'version':'5.5.2','intencion':i,'estado':'consulta_datos_resuelta','mensaje':formatear_resultado_552(r),'datos':r,'pasos':[]}
