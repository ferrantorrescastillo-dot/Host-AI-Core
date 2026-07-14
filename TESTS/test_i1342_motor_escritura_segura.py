import json
from pathlib import Path
from SERVICIOS.motor_escritura_segura_i1342 import MotorEscrituraSeguraI1342
from SERVICIOS.diagnostico_escritura_segura_i1342 import DiagnosticoEscrituraSeguraI1342

def test_commit_y_backup(tmp_path):
    rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[]',encoding='utf-8')
    m=MotorEscrituraSeguraI1342(tmp_path,[rel]); r=m.ejecutar({rel:[{'id':'1'}]})
    assert r.estado=='COMMIT' and r.integridad_ok and json.loads(p.read_text())==[{'id':'1'}]
    assert Path(r.backup_dir,'manifest.json').exists()

def test_rollback_restaura(tmp_path):
    rel='DATOS/db/menus.json'; p=tmp_path/rel; p.parent.mkdir(parents=True); p.write_text('[{"id":"base"}]',encoding='utf-8')
    m=MotorEscrituraSeguraI1342(tmp_path,[rel]); r=m.ejecutar({rel:[{'id':'nuevo'}]},forzar_fallo=True)
    assert r.estado=='ROLLBACK' and r.integridad_ok
    assert json.loads(p.read_text())==[{'id':'base'}]

def test_ruta_no_autorizada(tmp_path):
    m=MotorEscrituraSeguraI1342(tmp_path,['DATOS/db/menus.json'])
    r=m.ejecutar({'DATOS/db/articulos.json':[]})
    assert r.estado=='ROLLBACK'

def test_diagnostico(tmp_path):
    r=DiagnosticoEscrituraSeguraI1342(tmp_path).ejecutar()
    assert r['diagnostico']=='OK' and not r['datos_reales_modificados']
