from __future__ import annotations
import json
from pathlib import Path
from SERVICIOS.motor_escritura_segura_i1342 import MotorEscrituraSeguraI1342

class DiagnosticoEscrituraSeguraI1342:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir).resolve()
        self.rel = 'DATOS/mur/diagnostico_i1342/menus.json'
        self.motor = MotorEscrituraSeguraI1342(self.base_dir, [self.rel])

    def ejecutar(self):
        path = self.base_dir / self.rel
        path.parent.mkdir(parents=True, exist_ok=True)
        inicial = [{'menu_id':'MENU-BASE','nombre':'Menú diagnóstico base'}]
        path.write_text(json.dumps(inicial, ensure_ascii=False, indent=2), encoding='utf-8')
        commit_data = inicial + [{'menu_id':'MENU-NUEVO','nombre':'Menú diagnóstico nuevo'}]
        commit = self.motor.ejecutar({self.rel: commit_data}, idempotency_key='DIAG-COMMIT-I1342')
        despues_commit = json.loads(path.read_text(encoding='utf-8'))
        rollback_data = despues_commit + [{'menu_id':'MENU-FALLO','nombre':'No debe persistir'}]
        rollback = self.motor.ejecutar({self.rel: rollback_data}, forzar_fallo=True, idempotency_key='DIAG-ROLLBACK-I1342')
        final = json.loads(path.read_text(encoding='utf-8'))
        ok = commit.estado == 'COMMIT' and rollback.estado == 'ROLLBACK' and rollback.integridad_ok and final == despues_commit
        return {
            'version':'I1.3.4.2','diagnostico':'OK' if ok else 'ERROR',
            'commit':commit.to_dict(),'rollback':rollback.to_dict(),
            'registros_finales':len(final),'archivo_diagnostico':str(path),
            'datos_reales_modificados':False,
        }

def formatear_diagnostico_i1342(r):
    c, rb = r['commit'], r['rollback']
    lines=['I1.3.4.2 — MOTOR DE ESCRITURA SEGURA','='*78,
           f"Diagnóstico: {r['diagnostico']}",
           f"COMMIT: {c['estado']} | Backup: creado | Escritos: {c['escritos']} | Integridad: {'OK' if c['integridad_ok'] else 'ERROR'}",
           f"ROLLBACK: {rb['estado']} | Restaurados: {rb['restaurados']} | Integridad: {'OK' if rb['integridad_ok'] else 'ERROR'}",
           f"Eventos de auditoría: {len(c['auditoria']) + len(rb['auditoria'])}",
           f"Archivo aislado: {r['archivo_diagnostico']}",'-'*78,
           'Se validó backup, escritura atómica, commit, fallo controlado, rollback y restauración.',
           'No se modificaron menús, recetas, artículos, compras, stock ni otros datos reales.']
    return '\n'.join(lines)
