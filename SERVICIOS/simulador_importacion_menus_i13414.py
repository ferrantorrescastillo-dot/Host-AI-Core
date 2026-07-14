from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from SERVICIOS.motor_interpretacion_culinaria_i13414 import MotorInterpretacionCulinariaI13414
from SERVICIOS.simulador_importacion_menus_i13412 import SimuladorImportacionMenusI13412, formatear_simulacion_i13412
from SERVICIOS.simulador_importacion_menus_i13411 import _stable_id, _norm


class SimuladorImportacionMenusI13414(SimuladorImportacionMenusI13412):
    VERSION = 'I1.3.4.1.4'

    def __init__(self, base_dir: str | Path):
        super().__init__(base_dir)
        self.interprete = MotorInterpretacionCulinariaI13414()

    def _interpretar_preimportacion(self, pre: dict[str, Any]) -> dict[str, Any]:
        r = deepcopy(pre)
        aplicadas = 0
        antes = despues = 0
        interpretaciones = []
        nuevos_bloqueos = []
        claves_interpretadas = set()

        for menu in r.get('menus', []):
            for plato in menu.get('platos', []):
                comps = list(plato.get('componentes', []))
                antes += sum(1 for c in comps if not c.get('catalogado'))
                inter = self.interprete.interpretar(str(plato.get('nombre_original') or ''), comps)
                if inter.get('aplicada'):
                    catalogados = [c for c in comps if c.get('catalogado')]
                    nuevos = self.interprete.convertir_componentes(inter)
                    plato['componentes'] = catalogados + nuevos
                    plato['interpretacion_culinaria'] = inter
                    plato['estado_semantico'] = 'PARCIAL' if catalogados or nuevos else plato.get('estado_semantico')
                    aplicadas += 1
                    interpretaciones.append({'menu': menu.get('nombre'), 'plato': plato.get('nombre_original'), **inter})
                    claves_interpretadas.add((_norm(menu.get('nombre')), _norm(plato.get('nombre_original'))))
                despues += sum(1 for c in plato.get('componentes', []) if not c.get('catalogado'))

        # Reconstruye bloqueos de platos interpretados por concepto, conserva los demás.
        for b in r.get('bloqueos', []):
            clave = (_norm(b.get('menu')), _norm(b.get('plato')))
            if clave not in claves_interpretadas:
                nuevos_bloqueos.append(b)
        for menu in r.get('menus', []):
            for plato in menu.get('platos', []):
                if (_norm(menu.get('nombre')), _norm(plato.get('nombre_original'))) not in claves_interpretadas:
                    continue
                for c in plato.get('componentes', []):
                    if c.get('catalogado'):
                        continue
                    nuevos_bloqueos.append({
                        'codigo': 'CONCEPTO_CULINARIO_NO_RESUELTO', 'nivel': 'BLOQUEO',
                        'menu': menu.get('nombre'), 'plato': plato.get('nombre_original'),
                        'componente': c.get('nombre'), 'rol': c.get('rol'),
                        'mensaje': 'Concepto culinario agrupado pendiente de vínculo definitivo.',
                        'acciones': ['Vincular con receta', 'Vincular con artículo', 'Crear receta y completar ficha'],
                    })
        r['bloqueos'] = nuevos_bloqueos
        r['estado_preimportacion'] = 'LISTA' if not nuevos_bloqueos else 'BLOQUEADA'
        r['interpretacion_culinaria'] = {
            'version': self.VERSION, 'platos_interpretados': aplicadas,
            'fragmentos_pendientes_antes': antes, 'conceptos_pendientes_despues': despues,
            'reduccion': max(0, antes-despues), 'interpretaciones': interpretaciones,
        }
        return r

    def construir_plan(self, pre: dict[str, Any], menus_existentes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        pre2 = self._interpretar_preimportacion(pre)
        plan = super().construir_plan(pre2, menus_existentes)
        plan['version'] = self.VERSION
        plan['interpretacion_culinaria'] = pre2.get('interpretacion_culinaria', {})
        for idx, a in enumerate(plan.get('acciones', []), 1):
            d=a.get('detalle', {})
            a['accion_id'] = _stable_id('ACT', self.VERSION, idx, a.get('tipo'), a.get('entidad'), a.get('nombre'), d.get('menu_id'), d.get('plato'))
        plan['plan_id'] = _stable_id('PLAN', self.VERSION, *(a['accion_id'] for a in plan.get('acciones', [])))
        return plan


def formatear_simulacion_i13414(resultado: dict[str, Any]) -> str:
    ic = resultado.get('interpretacion_culinaria', {})
    base = formatear_simulacion_i13412(resultado).splitlines()
    base[0] = 'I1.3.4.1.4 — MOTOR DE INTERPRETACIÓN CULINARIA Y SIMULACIÓN'
    cab = [
        '='*78,
        'INTERPRETACIÓN CULINARIA',
        f"Platos reinterpretados: {ic.get('platos_interpretados',0)} | Fragmentos antes: {ic.get('fragmentos_pendientes_antes',0)} | Conceptos después: {ic.get('conceptos_pendientes_despues',0)} | Reducción: {ic.get('reduccion',0)}",
    ]
    for x in ic.get('interpretaciones', []):
        cab.append(f"- {x.get('plato')}")
        for c in x.get('conceptos', []):
            cab.append(f"    {c.get('rol')}: {c.get('nombre')} | confianza {round(float(c.get('confianza',0))*100)}%")
    # Inserta tras el primer separador.
    return '\n'.join(base[:2] + cab[1:] + base[2:] + ['I1.3.4.1.4 sigue siendo solo simulación: 0 escrituras.'])
