from pathlib import Path
from SERVICIOS.motor_interpretacion_culinaria_i13414 import MotorInterpretacionCulinariaI13414
from SERVICIOS.simulador_importacion_menus_i13414 import SimuladorImportacionMenusI13414


def pendientes(nombres):
    return [{'nombre': x, 'catalogado': False} for x in nombres]


def test_crema_agrupa_conceptos():
    m=MotorInterpretacionCulinariaI13414()
    r=m.interpretar('Crema de marisco, vieras con bombon de coco y curri.', pendientes(['crema','marisco vieras','bombon','coco','curri']))
    assert r['aplicada']
    assert [x['nombre'] for x in r['conceptos']] == ['Crema de marisco','vieras','bombon de coco y curri']


def test_lenguado_no_rompe_tecnica():
    m=MotorInterpretacionCulinariaI13414()
    r=m.interpretar('Lenguado a la menier de yondu con hinojo y avellanas', pendientes(['lenguado','menier','yondu','hinojo','avellanas']))
    assert r['conceptos'][0]['nombre']=='Lenguado a la menier'
    assert r['conceptos'][1]['rol']=='CONDIMENTO'
    assert r['conceptos'][-1]['rol']=='ACABADO'


def test_tournedo_dos_conceptos():
    m=MotorInterpretacionCulinariaI13414()
    r=m.interpretar('Tournedo de solomillo Rossini con chalotas glaseadas.', pendientes(['tournedo','solomillo rossini','chalotas glaseadas']))
    assert len(r['conceptos'])==2
    assert r['conceptos'][1]['rol']=='GUARNICION'


def test_no_interpreta_un_solo_pendiente():
    m=MotorInterpretacionCulinariaI13414()
    assert not m.interpretar('Parmentier de patata', pendientes(['Parmentier de patata']))['aplicada']


def test_simulacion_real_reduce_fragmentos():
    base=Path(__file__).resolve().parents[1]
    x=base/'Documentos'/'Escandallos Boronat.xlsx'
    if not x.exists():
        return
    s=SimuladorImportacionMenusI13414(base)
    plan=s.simular(x, hojas=['MENU FIN DE AÑO'])
    ic=plan['interpretacion_culinaria']
    assert ic['platos_interpretados'] >= 3
    assert ic['reduccion'] > 0
    assert plan['integridad']['sin_escrituras']
