from __future__ import annotations

from pathlib import Path

from SERVICIOS.bandeja_revision_i13413 import BandejaRevisionI13413, formatear_bandeja_i13413
from SERVICIOS.simulador_importacion_menus_i13415 import SimuladorImportacionMenusI13415


class BandejaRevisionI13415(BandejaRevisionI13413):
    VERSION = 'I1.3.4.1.5'

    def __init__(self, base_dir: str | Path):
        super().__init__(base_dir)
        self.simulador = SimuladorImportacionMenusI13415(base_dir)
        self.dir_sesiones = self.base_dir / 'DATOS' / 'mur' / 'revisiones_i13415'

    def _extraer_incidencias(self, plan):
        incidencias = super()._extraer_incidencias(plan)
        # Retira avisos cuya acción quedó clasificada automáticamente con alta confianza.
        acciones = {a.get('accion_id'): a for a in plan.get('acciones', [])}
        salida = []
        for inc in incidencias:
            auto = False
            tipos = []
            confs = []
            motivos = []
            for aid in inc.accion_ids:
                a = acciones.get(aid, {})
                cg = a.get('detalle', {}).get('conocimiento_gastronomico') or {}
                if cg:
                    tipos.append(cg.get('tipo'))
                    confs.append(float(cg.get('confianza') or 0))
                    motivos.append(cg.get('motivo'))
                    if float(cg.get('confianza') or 0) >= .90 and a.get('estado') != 'BLOQUEADA':
                        auto = True
            if inc.nivel == 'AVISO' and auto:
                continue
            if tipos:
                inc.propuesta = str(tipos[0] or inc.propuesta)
                inc.confianza = round(max(confs) * 100)
                inc.motivo = str(motivos[0] or inc.motivo)
            salida.append(inc)
        for idx, inc in enumerate(salida, 1):
            inc.numero = idx
        return salida


def formatear_bandeja_i13415(sesion, solo_pendientes=True):
    texto = formatear_bandeja_i13413(sesion, solo_pendientes)
    texto = texto.replace('I1.3.4.1.3 — BANDEJA', 'I1.3.4.1.5 — CONOCIMIENTO GASTRONÓMICO + BANDEJA')
    cg = sesion.get('plan', {}).get('conocimiento_gastronomico', {})
    resumen = (
        '\n\nRESUMEN DEL MOTOR DE CONOCIMIENTO\n'
        f"Evaluados: {cg.get('evaluados', 0)} | Automatizados alta confianza: {cg.get('automatizados_alta_confianza', 0)} | "
        f"Revisables/bloqueantes: {cg.get('revisables_o_bloqueantes', 0)} | Umbral: {round(float(cg.get('umbral_automatico', .9))*100)}%"
    )
    return texto + resumen
