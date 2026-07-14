from __future__ import annotations

from pathlib import Path
from typing import Any

from SERVICIOS.motor_conocimiento_gastronomico_i13415 import MotorConocimientoGastronomicoI13415
from SERVICIOS.simulador_importacion_menus_i13414 import SimuladorImportacionMenusI13414
from SERVICIOS.simulador_importacion_menus_i13411 import _stable_id, _norm


class SimuladorImportacionMenusI13415(SimuladorImportacionMenusI13414):
    VERSION = 'I1.3.4.1.5'

    def __init__(self, base_dir: str | Path):
        super().__init__(base_dir)
        self.conocimiento = MotorConocimientoGastronomicoI13415(base_dir)

    @staticmethod
    def _aplicar_destino(accion: dict[str, Any], tipo: str, destino: str) -> None:
        mapa = {
            'APERITIVO_PREPARADO': ('VINCULAR', 'APERITIVO_PREPARADO'),
            'ARTICULO_DIRECTO': ('VINCULAR', 'ARTICULO_DIRECTO'),
            'SALSA_MENU': ('CREAR_RELACION', 'SALSA_MENU'),
            'POSTRE_MENU': ('CREAR_RELACION', 'POSTRE_MENU'),
            'ELABORACION_MENU': ('CREAR_RELACION', 'ELABORACION_MENU'),
            'PLATO_MENU': ('CREAR_RELACION', 'PLATO_MENU'),
        }
        if destino in mapa:
            accion['tipo'], accion['entidad'] = mapa[destino]
            accion['estado'] = 'PLANIFICADA'
        accion.setdefault('detalle', {})['tipo_conocimiento_gastronomico'] = tipo

    def construir_plan(self, pre: dict[str, Any], menus_existentes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        plan = super().construir_plan(pre, menus_existentes)
        resultados = []
        automatizadas = 0
        revisables = 0

        for accion in plan.get('acciones', []):
            nombre = str(accion.get('nombre') or '')
            if not nombre or accion.get('tipo') in {'CREAR', 'CREAR_O_REUTILIZAR', 'REGISTRAR'}:
                continue
            detalle = accion.get('detalle', {})
            rol = accion.get('entidad') if accion.get('tipo') == 'RESOLVER_ANTES_DE_IMPORTAR' else detalle.get('rol')
            cg = self.conocimiento.clasificar(nombre, {'rol': rol, 'menu': detalle.get('menu'), 'plato': detalle.get('plato')})
            accion.setdefault('detalle', {})['conocimiento_gastronomico'] = cg.to_dict()
            if self.conocimiento.es_alta_confianza(cg):
                # Los bloqueos de conceptos reales no se cierran por una mera clasificación:
                # solo se mejora su tipo. Las advertencias no bloqueantes sí se automatizan.
                if accion.get('estado') != 'BLOQUEADA':
                    self._aplicar_destino(accion, cg.tipo, cg.destino_importacion)
                    automatizadas += 1
                else:
                    accion['entidad'] = cg.tipo if cg.tipo != 'DESCONOCIDO' else accion.get('entidad')
                    revisables += 1
            else:
                revisables += 1
            resultados.append({
                'accion_id': accion.get('accion_id'), 'nombre': nombre,
                'tipo': cg.tipo, 'confianza': cg.confianza, 'motivo': cg.motivo,
                'aprendido': cg.aprendido, 'automatizada': cg.confianza >= .90 and accion.get('estado') != 'BLOQUEADA',
            })

        # Recalcula resumen y ids tras aplicar conocimiento.
        acciones = plan.get('acciones', [])
        plan['resumen'].update({
            'acciones': len(acciones),
            'ejecutables': sum(a.get('estado') == 'PLANIFICADA' for a in acciones),
            'bloqueadas': sum(a.get('estado') == 'BLOQUEADA' for a in acciones),
            'vincular': sum(a.get('tipo') == 'VINCULAR' for a in acciones),
            'relaciones': sum(a.get('tipo') in {'CREAR_RELACION', 'CREAR_O_REUTILIZAR'} for a in acciones),
        })
        plan['conocimiento_gastronomico'] = {
            'version': self.VERSION,
            'evaluados': len(resultados),
            'automatizados_alta_confianza': automatizadas,
            'revisables_o_bloqueantes': revisables,
            'resultados': resultados,
            'umbral_automatico': .90,
        }
        plan['version'] = self.VERSION
        for idx, a in enumerate(acciones, 1):
            d = a.get('detalle', {})
            a['accion_id'] = _stable_id('ACT', self.VERSION, idx, a.get('tipo'), a.get('entidad'), a.get('nombre'), d.get('menu_id'), d.get('plato'))
        plan['plan_id'] = _stable_id('PLAN', self.VERSION, *(a['accion_id'] for a in acciones))
        return plan
