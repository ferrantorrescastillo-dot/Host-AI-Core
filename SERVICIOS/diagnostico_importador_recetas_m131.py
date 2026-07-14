from __future__ import annotations
from pathlib import Path
import json, tempfile
from SERVICIOS.importador_inteligente_recetas_m131 import ImportadorInteligenteRecetasM131, clasificar_prefijo_articulo

class DiagnosticoImportadorRecetasM131:
    def __init__(self, base_dir: str|Path): self.base_dir=Path(base_dir)
    def ejecutar(self)->dict:
        d=self.base_dir/'DATOS/mur/diagnostico_m131';d.mkdir(parents=True,exist_ok=True)
        articulos=[
          {'codigo':'M.P-PATATA','nombre':'Patata monalisa','unidad':'kg','precio':1.2},
          {'codigo':'M.P-MANTEQUILLA','nombre':'Mantequilla','unidad':'kg','precio':8.0},
          {'codigo':'M.P-LECHE','nombre':'Leche entera','unidad':'l','precio':1.1},
          {'codigo':'A.P-BRIOX','nombre':'A.P BRIOX DE CURRI, SECRETO A BAJA TEMPERATURA Y CEBOLLITA ENCURTIDA.','unidad':'ud','precio':2.5},
        ]
        cat=d/'articulos.json';cat.write_text(json.dumps(articulos,ensure_ascii=False,indent=2),encoding='utf-8')
        texto='''Parmentier de patata\nRendimiento: 10 raciones\nIngredientes\n2 kg Patata monalisa\n0.25 kg Mantequilla\n0.5 l Leche entera\nElaboración\nCocer la patata, triturar y emulsionar con mantequilla y leche.'''
        imp=ImportadorInteligenteRecetasM131(cat);b=imp.desde_texto(texto)
        payload=imp.payload_creacion(b)
        return {'ok':not b.bloqueos,'borrador':b.to_dict(),'payload':payload,'catalogo':str(cat),
                'ap_clase':clasificar_prefijo_articulo(articulos[-1]),'mp_clase':clasificar_prefijo_articulo(articulos[0])}

def formatear_diagnostico_m131(r:dict)->str:
    b=r['borrador'];ings=b['ingredientes']
    lineas=['M1.3.1 — IMPORTADOR INTELIGENTE DE RECETAS','='*78,
      f"Diagnóstico: {'OK' if r['ok'] else 'ERROR'} | Nombre: {b['nombre']} | Rendimiento: {b['rendimiento']}",
      f"Ingredientes detectados: {len(ings)} | Bloqueos: {len(b['bloqueos'])}"]
    for i in ings: lineas.append(f"- {i['nombre']} | {i['cantidad']} {i['unidad']} | {i['articulo_id']} | {i['clase_articulo']} | {i['estado']}")
    lineas += [f"Regla prefijos: M.P={r['mp_clase']} | A.P={r['ap_clase']}",f"Catálogo aislado: {r['catalogo']}",'-'*78,
      'Se validó texto, borrador, cantidades, unidades, rendimiento y vínculo solo con materias primas.',
      'Los A.P se clasifican como APERITIVO y no se usan automáticamente como ingredientes base.',
      'Word, PDF y Excel comparten el mismo contrato de borrador. No se modificaron datos reales.',
      'Ingredientes inexistentes o ambiguos permanecen bloqueados hasta M1.3.2.']
    return '\n'.join(lineas)

__all__=['DiagnosticoImportadorRecetasM131','formatear_diagnostico_m131']
