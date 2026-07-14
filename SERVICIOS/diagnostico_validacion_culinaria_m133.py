from __future__ import annotations
from pathlib import Path
import json

from SERVICIOS.importador_inteligente_recetas_m131 import ImportadorInteligenteRecetasM131
from SERVICIOS.validacion_culinaria_m133 import ValidadorCulinarioM133


class DiagnosticoValidacionCulinariaM133:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def ejecutar(self) -> dict:
        d = self.base_dir / 'DATOS/mur/diagnostico_m133'
        d.mkdir(parents=True, exist_ok=True)
        articulos = [
            {'codigo':'M.P-PATATA','nombre':'Patata monalisa','unidad':'kg','precio':1.20},
            {'codigo':'M.P-MANTEQUILLA','nombre':'Mantequilla','unidad':'kg','precio':8.00},
            {'codigo':'M.P-LECHE','nombre':'Leche entera','unidad':'l','precio':1.10},
            {'codigo':'M.P-NUEZ','nombre':'Nuez moscada','unidad':'kg','precio':None,'estado_calidad':'PENDIENTE'},
            {'codigo':'A.P-BRIOX','nombre':'A.P BRIOX DE CURRI, SECRETO A BAJA TEMPERATURA Y CEBOLLITA ENCURTIDA.','unidad':'ud','precio':2.50},
        ]
        cat = d / 'articulos.json'
        cat.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding='utf-8')
        texto = '''Parmentier de patata
Rendimiento: 10 raciones
Ingredientes
2 kg Patata monalisa
0.25 kg Mantequilla
0.5 l Leche entera
0.01 kg Nuez moscada
Elaboración
Cocer la patata durante 25 min. Escurrir, triturar y emulsionar con mantequilla y leche. Conservar refrigerada un máximo de 48 h.'''
        borrador = ImportadorInteligenteRecetasM131(cat).desde_texto(texto)
        resultado = ValidadorCulinarioM133(cat).validar(
            borrador,
            metadatos={'alergenos':['LECHE'], 'conservacion':'0-4 ºC / 48 h', 'tiempos':'25 min'},
        )
        # Caso adverso para certificar errores y avisos sin escribir datos.
        texto_malo = '''Parmentier incoherente
Rendimiento: 10
Ingredientes
2 l Mantequilla
0 kg Patata monalisa
1 ud A.P BRIOX DE CURRI, SECRETO A BAJA TEMPERATURA Y CEBOLLITA ENCURTIDA.
Elaboración
Mezclar.'''
        malo = ImportadorInteligenteRecetasM131(cat).desde_texto(texto_malo)
        # El importador excluye A.P: se fuerza el vínculo solo para comprobar que el validador lo bloquea.
        ap = malo.ingredientes[2]
        ap.articulo_id='A.P-BRIOX'; ap.articulo_nombre=articulos[-1]['nombre']; ap.clase_articulo='APERITIVO'; ap.estado='VINCULADO'
        adverso = ValidadorCulinarioM133(cat).validar(malo)
        return {
            'ok': resultado.estado in {'VALIDADA','REVISAR'} and resultado.errores == 0 and adverso.errores >= 2,
            'resultado': resultado.to_dict(),
            'adverso': adverso.to_dict(),
            'catalogo': str(cat),
            'datos_reales_modificados': False,
        }


def formatear_diagnostico_m133(r: dict) -> str:
    v=r['resultado']; a=r['adverso']
    lineas=[
        'M1.3.3 — VALIDACIÓN CULINARIA INTELIGENTE',
        '='*78,
        f"Diagnóstico: {'OK' if r['ok'] else 'ERROR'} | Receta: {v['receta']} | Estado: {v['estado']}",
        f"Ingredientes: {v['ingredientes']} | Errores: {v['errores']} | Avisos: {v['avisos']} | Informativos: {v['informativos']}",
        f"Coste total conocido: {v['coste_total']} € | Coste/ración conocido: {v['coste_por_racion']} €",
    ]
    for h in v['hallazgos']:
        simbolo='✖' if h['severidad']=='ERROR' else ('!' if h['severidad']=='AVISO' else '·')
        lineas.append(f"{simbolo} [{h['severidad']}] {h['codigo']}: {h['mensaje']}")
    lineas += [
        '-'*78,
        f"Caso adverso: {a['estado']} | Errores: {a['errores']} | Avisos: {a['avisos']}",
    ]
    for h in a['hallazgos']:
        if h['severidad']=='ERROR':
            lineas.append(f"✖ {h['codigo']}: {h['mensaje']}")
    lineas += [
        f"Catálogo aislado: {r['catalogo']}",
        '-'*78,
        'Se validaron rendimiento, cantidades, unidades, duplicados, costes, elaboración, tiempos, conservación y alérgenos.',
        'Los A.P se bloquean como materia prima automática. Las sospechas culinarias se muestran como avisos explicables.',
        'Un artículo sin precio deja el coste incompleto, pero no convierte automáticamente la receta en inválida.',
        'No se creó ninguna receta ni se modificaron catálogos reales.',
    ]
    return '\n'.join(lineas)


__all__=['DiagnosticoValidacionCulinariaM133','formatear_diagnostico_m133']
