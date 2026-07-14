from __future__ import annotations
import re, unicodedata
from typing import Any, Dict


def _norm(texto: str) -> str:
    t=(texto or '').strip().lower()
    t=''.join(c for c in unicodedata.normalize('NFD',t) if unicodedata.category(c)!='Mn')
    return re.sub(r'\s+',' ',t.replace('¿','').replace('?','')).strip()


def clasificar_consulta_datos_551(texto: str) -> Dict[str, Any]:
    t=_norm(texto)
    mapa=(
        ('consultar_menus', ('que menus','menus disponibles','lista de menus','mostrar menus','ensename los menus')),
        ('consultar_recetas', ('que recetas','recetas registradas','lista de recetas','mostrar recetas','ensename las recetas')),
        ('consultar_escandallos', ('que escandallos','escandallos disponibles','lista de escandallos','mostrar escandallos')),
        ('buscar_catalogo_cocina', ('busca cualquier receta','busca una receta','buscar receta','buscar menu','busca el menu','que contenga la palabra','relacionado con')),
        ('consultar_articulos', ('que articulos','articulos disponibles','buscar articulo','busca el articulo')),
        ('consultar_proveedores', ('que proveedores','proveedores disponibles','quien vende','que proveedor vende')),
    )
    for intencion, frases in mapa:
        if any(f in t for f in frases):
            return {'gestionado':True,'intencion':intencion,'confianza':0.98,'texto_normalizado':t}
    return {'gestionado':False,'intencion':'desconocida','confianza':0.0,'texto_normalizado':t}
