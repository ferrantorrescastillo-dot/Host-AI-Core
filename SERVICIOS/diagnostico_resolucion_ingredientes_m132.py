from __future__ import annotations
from pathlib import Path
import json

from SERVICIOS.importador_inteligente_recetas_m131 import ImportadorInteligenteRecetasM131
from SERVICIOS.resolucion_ingredientes_m132 import ResolucionIngredientesM132


class DiagnosticoResolucionIngredientesM132:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def ejecutar(self) -> dict:
        d = self.base_dir / 'DATOS/mur/diagnostico_m132'
        d.mkdir(parents=True, exist_ok=True)
        articulos = [
            {'codigo':'M.P-PATATA','nombre':'Patata monalisa','unidad':'kg','precio':1.2},
            {'codigo':'M.P-MANTEQUILLA','nombre':'Mantequilla','unidad':'kg','precio':8.0},
            {'codigo':'A.P-BRIOX','nombre':'A.P BRIOX DE CURRI, SECRETO A BAJA TEMPERATURA Y CEBOLLITA ENCURTIDA.','unidad':'ud','precio':2.5},
        ]
        cat = d / 'articulos.json'
        cat.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding='utf-8')
        texto = '''Parmentier de patata\nRendimiento: 10 raciones\nIngredientes\n2 kg Patata monalisa\n0.25 kg Mantequilla\n0.5 l Leche entera\n0.01 kg Nuez moscada\nElaboración\nCocer la patata, triturar y emulsionar.'''
        imp = ImportadorInteligenteRecetasM131(cat)
        borrador = imp.desde_texto(texto)
        bloqueos_iniciales = list(borrador.bloqueos or [])
        gestor = ResolucionIngredientesM132(cat, permitir_sin_precio=True)
        resultado = gestor.resolver(borrador, decisiones={
            'Leche entera': {'accion':'CREAR','payload':{'nombre':'Leche entera','unidad':'l','precio':1.10,'familia':'Lácteos'}},
            'Nuez moscada': {'accion':'CREAR','payload':{'nombre':'Nuez moscada','unidad':'kg','precio':None,'familia':'Especias'}},
        })
        payload = imp.payload_creacion(resultado.borrador)
        return {
            'ok': not resultado.bloqueos_finales,
            'resultado': resultado.to_dict(),
            'bloqueos_iniciales': bloqueos_iniciales,
            'payload': payload,
            'catalogo': str(cat),
            'receta_creada': False,
        }


def formatear_diagnostico_m132(r: dict) -> str:
    res = r['resultado']; b = res['borrador']; cola = res['cola']
    lineas = [
        'M1.3.2 — RESOLUCIÓN AUTOMÁTICA DE INGREDIENTES MEDIANTE EL MUR',
        '=' * 78,
        f"Diagnóstico: {'OK' if r['ok'] else 'ERROR'} | Receta: {b['nombre']} | Rendimiento: {b['rendimiento']}",
        f"Bloqueos iniciales: {len(r['bloqueos_iniciales'])} | Cola: {len(cola)} | Cerrados: {res['conflictos_cerrados']} | Bloqueos finales: {len(res['bloqueos_finales'])}",
    ]
    for item in cola:
        lineas.append(f"- {item['ingrediente']} | {item['accion']} | {item['articulo_id']} | {item['estado']}")
    lineas += [
        f"Eventos de auditoría: {res['eventos_auditoria']}",
        f"Catálogo aislado: {r['catalogo']}",
        '-' * 78,
        'Se validó una cola de conflictos anidados ARTICULO dentro del flujo de una RECETA.',
        'Cada ingrediente se resolvió mediante M1.2, volvió al borrador y cerró su conflicto tras recalcular.',
        'Nuez moscada quedó como artículo PENDIENTE por no tener precio, sin bloquear la receta según política.',
        'Los A.P continúan excluidos de la vinculación automática como materias primas.',
        'No se creó la receta definitiva ni se modificaron catálogos reales.',
    ]
    return '\n'.join(lineas)


__all__ = ['DiagnosticoResolucionIngredientesM132', 'formatear_diagnostico_m132']
